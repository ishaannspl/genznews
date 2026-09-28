"""Download and extract the main content and metadata from one article URL."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import requests
import trafilatura

from .config import get_settings


class ScraperError(Exception):
    """Base error for expected article scraping failures."""


class InvalidURLError(ScraperError):
    """Raised when the supplied URL is not an HTTP(S) URL."""


class ArticleExtractionError(ScraperError):
    """Raised when an article cannot be extracted or is too short."""


@dataclass(frozen=True)
class ScrapedArticle:
    url: str
    domain: str
    title: str | None
    author: str | None
    published_at: str | None
    content: str


def _validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise InvalidURLError("URL is required")

    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidURLError("URL must include an http:// or https:// scheme and a host")
    if parsed.username or parsed.password:
        raise InvalidURLError("URLs containing credentials are not supported")
    return normalized


def _clean_text(text: str, max_chars: int) -> str:
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", text):
        cleaned = re.sub(r"[ \t\r\f\v]+", " ", paragraph).strip()
        if cleaned:
            paragraphs.append(cleaned)

    normalized = "\n\n".join(paragraphs)
    if len(normalized) <= max_chars:
        return normalized

    truncated = normalized[:max_chars]
    last_break = truncated.rfind("\n\n")
    if last_break >= max_chars // 2:
        truncated = truncated[:last_break]
    return f"{truncated.rstrip()} [Article truncated for length safety.]"


def _metadata_value(metadata: Any, name: str) -> str | None:
    value = getattr(metadata, name, None) if metadata is not None else None
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def scrape_article(url: str) -> dict[str, Any]:
    """Download one article and return cleaned text plus available metadata."""
    settings = get_settings()
    normalized_url = _validate_url(url)
    domain = urlparse(normalized_url).netloc.lower()

    try:
        response = requests.get(
            normalized_url,
            headers={"User-Agent": settings.user_agent},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise ScraperError("The article request timed out") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == 403:
            raise ScraperError("The website denied access to the article (HTTP 403)") from exc
        if status_code == 404:
            raise ScraperError("The article was not found (HTTP 404)") from exc
        raise ScraperError(f"The article request failed with HTTP {status_code}") from exc
    except requests.RequestException as exc:
        raise ScraperError(f"Could not reach the article website: {exc}") from exc

    extracted = trafilatura.extract(
        response.text,
        include_comments=False,
        include_tables=False,
        output_format="txt",
        favor_precision=True,
    )
    content = _clean_text(extracted or "", settings.max_article_chars)
    if len(content) < settings.min_article_chars:
        raise ArticleExtractionError(
            f"Article extraction produced too little text ({len(content)} characters)"
        )

    metadata = trafilatura.extract_metadata(response.text)
    result = ScrapedArticle(
        url=normalized_url,
        domain=domain,
        title=_metadata_value(metadata, "title"),
        author=_metadata_value(metadata, "author"),
        published_at=_metadata_value(metadata, "date"),
        content=content,
    )
    return asdict(result)
