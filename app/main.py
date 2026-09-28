"""FastAPI application — GenZNews AI article generation pipeline."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .ai_writer import generate_genz_article
from .database import article_exists, get_article_by_id, get_recent_articles, insert_article
from .schemas import ArticleOut, GenerateRequest, ScrapedData
from .scraper import ArticleExtractionError, ScraperError, scrape_article

app = FastAPI(
    title="GenZNews AI",
    description="Scrape a news article → rewrite it in Gen-Z style → save to Supabase.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}


# ── Generate ──────────────────────────────────────────────────────────────────

@app.post("/generate", response_model=ArticleOut, tags=["articles"])
def generate(body: GenerateRequest) -> ArticleOut:
    """
    Full pipeline:
    1. Validate & scrape URL
    2. Generate Gen-Z rewrite via Gemini
    3. Save to Supabase
    4. Return saved article
    """
    url = str(body.url)

    # Deduplication — skip if already processed
    if article_exists(url):
        raise HTTPException(
            status_code=409,
            detail="This article has already been processed. Use GET /articles to find it.",
        )

    # Step 1 — Scrape
    try:
        raw = scrape_article(url)
    except ScraperError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    scraped = ScrapedData(
        url=raw["url"],
        domain=raw["domain"],
        original_title=raw["title"],
        original_author=raw["author"],
        published_at=raw["published_at"],
        original_content=raw["content"],
    )

    # Step 2 — AI rewrite
    try:
        genz = generate_genz_article(scraped)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}")

    # Step 3 — Save to database (SQLite + Supabase)
    try:
        saved = insert_article(
            source_url=scraped.url,
            domain=scraped.domain,
            original_title=scraped.original_title,
            original_author=scraped.original_author,
            published_at=scraped.published_at,
            original_content=scraped.original_content,
            genz_title=genz.genz_title,
            genz_content=genz.genz_content,
            genz_tags=genz.genz_tags,
            niche=body.niche,
            headlines=genz.headlines,
            meta_description=genz.meta_description,
            slug=genz.slug,
            hook=genz.hook,
            tldr=genz.tldr,
            breakdown=genz.breakdown,
            why_it_matters=genz.why_it_matters,
            source_attribution=genz.source_attribution,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database save failed: {exc}")

    return ArticleOut(
        id=saved["id"],
        url=saved["source_url"],
        domain=saved["domain"],
        original_title=saved["original_title"],
        original_author=saved["original_author"],
        published_at=saved["published_at"],
        genz_title=saved["genz_title"],
        headlines=genz.headlines,
        meta_description=genz.meta_description,
        slug=genz.slug,
        hook=genz.hook,
        tldr=genz.tldr,
        breakdown=genz.breakdown,
        why_it_matters=genz.why_it_matters,
        source_attribution=genz.source_attribution,
        genz_content=saved["genz_content"],
        genz_tags=saved["genz_tags"] or [],
        niche=saved.get("niche"),
        status=saved["status"],
        created_at=str(saved["created_at"]),
    )


# ── List articles ─────────────────────────────────────────────────────────────

@app.get("/articles", tags=["articles"])
def list_articles(limit: int = 20, niche: str | None = None) -> list[dict]:
    """Return the most recently generated articles (summary view), optionally filtered by niche."""
    try:
        return get_recent_articles(limit=min(limit, 100), niche=niche)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/articles/{article_id}", response_model=ArticleOut, tags=["articles"])
def get_article(article_id: int) -> ArticleOut:
    """Fetch one article by ID with full structured fields."""
    try:
        row = get_article_by_id(article_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleOut(
        id=row["id"],
        url=row["source_url"],
        domain=row["domain"],
        original_title=row.get("original_title"),
        original_author=row.get("original_author"),
        published_at=row.get("published_at"),
        genz_title=row.get("genz_title", ""),
        headlines=row.get("headlines") or [],
        meta_description=row.get("meta_description"),
        slug=row.get("slug"),
        hook=row.get("hook"),
        tldr=row.get("tldr") or [],
        breakdown=row.get("breakdown"),
        why_it_matters=row.get("why_it_matters"),
        source_attribution=row.get("source_attribution"),
        genz_content=row.get("genz_content", ""),
        genz_tags=row.get("genz_tags") or [],
        niche=row.get("niche"),
        status=row.get("status", "done"),
        created_at=str(row.get("created_at", "")),
    )
