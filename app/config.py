"""Environment-backed configuration for the scraper."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


@dataclass(frozen=True)
class Settings:
    user_agent: str
    request_timeout_seconds: int
    max_article_chars: int
    min_article_chars: int


def get_settings() -> Settings:
    user_agent = os.getenv(
        "USER_AGENT",
        "GenZNewsAI/0.1 (article extraction; +https://localhost)",
    ).strip()
    if not user_agent:
        raise ValueError("USER_AGENT must not be empty")

    min_article_chars = _positive_int("MIN_ARTICLE_CHARS", 200)
    max_article_chars = _positive_int("MAX_ARTICLE_CHARS", 30000)
    if min_article_chars > max_article_chars:
        raise ValueError("MIN_ARTICLE_CHARS cannot exceed MAX_ARTICLE_CHARS")

    return Settings(
        user_agent=user_agent,
        request_timeout_seconds=_positive_int("REQUEST_TIMEOUT_SECONDS", 15),
        max_article_chars=max_article_chars,
        min_article_chars=min_article_chars,
    )
