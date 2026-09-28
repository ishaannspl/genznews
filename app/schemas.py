"""Pydantic schemas for API request/response and internal data transfer."""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator


# ── Request ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Body sent to POST /generate."""
    url: HttpUrl
    niche: Optional[str] = None

    @field_validator("url", mode="before")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return str(v).strip()


# ── Internal ──────────────────────────────────────────────────────────────────

class ScrapedData(BaseModel):
    """Cleaned article from the scraper, before AI processing."""
    url: str
    domain: str
    original_title: Optional[str] = None
    original_author: Optional[str] = None
    published_at: Optional[str] = None
    original_content: str
    niche: Optional[str] = None
    url_hash: Optional[str] = None


class GenZArticle(BaseModel):
    """AI-generated Gen-Z rewrite matching the PRD Phase 3 specification."""
    # Headings and SEO
    genz_title: str
    headlines: List[str] = []
    meta_description: str = ""
    slug: str = ""
    genz_tags: List[str] = []

    # Structured article sections
    hook: str = ""
    tldr: List[str] = []
    breakdown: str = ""
    why_it_matters: str = ""
    source_attribution: str = ""

    # Assembled complete markdown / HTML content
    genz_content: str = ""
    niche: Optional[str] = None


# ── Response ──────────────────────────────────────────────────────────────────

class ArticleOut(BaseModel):
    """Response returned by API endpoints."""
    id: int
    url: str
    domain: str
    original_title: Optional[str] = None
    original_author: Optional[str] = None
    published_at: Optional[str] = None
    genz_title: str
    headlines: List[str] = []
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    hook: Optional[str] = None
    tldr: List[str] = []
    breakdown: Optional[str] = None
    why_it_matters: Optional[str] = None
    source_attribution: Optional[str] = None
    genz_content: str
    genz_tags: List[str] = []
    niche: Optional[str] = None
    status: str = "done"
    created_at: str

    class Config:
        from_attributes = True
