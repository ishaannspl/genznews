"""Database storage helpers — SQLite local persistence + Supabase integration."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

try:
    from postgrest.types import CountMethod
except ImportError:
    CountMethod = None  # type: ignore

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "articles.db")


# ── Canonical URL SHA-256 Hashing ─────────────────────────────────────────────

def get_canonical_url(url: str) -> str:
    """Normalize a URL to prevent duplicate processing due to tracking tags."""
    parsed = urlparse(url.strip())
    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    # Strip analytics and tracking query params
    filtered_queries = []
    if parsed.query:
        for k, v in parse_qsl(parsed.query, keep_blank_values=False):
            k_lower = k.lower()
            if k_lower.startswith("utm_") or k_lower in {
                "ref", "source", "fbclid", "gclid", "at_medium", "at_campaign", "mc_cid"
            }:
                continue
            filtered_queries.append((k, v))
        filtered_queries.sort()

    clean_query = urlencode(filtered_queries)
    return urlunparse((scheme, netloc, path, "", clean_query, ""))


def compute_url_hash(url: str) -> str:
    """Return SHA-256 hash of canonical URL."""
    canonical = get_canonical_url(url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── SQLite Setup ──────────────────────────────────────────────────────────────

def init_sqlite_db() -> None:
    """Initialize local SQLite database schema for Phase 2 deduplication & storage."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT NOT NULL UNIQUE,
                    source_url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    niche TEXT,
                    original_title TEXT,
                    original_author TEXT,
                    published_at TEXT,
                    original_content TEXT,
                    genz_title TEXT,
                    headlines_json TEXT,
                    meta_description TEXT,
                    slug TEXT,
                    genz_tags_json TEXT,
                    hook TEXT,
                    tldr_json TEXT,
                    breakdown TEXT,
                    why_it_matters TEXT,
                    source_attribution TEXT,
                    genz_content TEXT,
                    status TEXT DEFAULT 'done',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles (url_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_niche ON articles (niche)")
    finally:
        conn.close()


# Call on import
init_sqlite_db()


# ── Supabase Client (Optional / Fallback) ──────────────────────────────────────

def _get_supabase_client():
    url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") or "").strip()
    if not url or url.startswith("http") is False or "PASTE_YOUR" in url:
        return None
    if not key:
        return None
    try:
        from supabase import create_client  # type: ignore
        return create_client(url, key)
    except Exception as exc:
        print(f"    [Supabase] Could not create client: {exc}")
        return None


# ── Storage Operations ────────────────────────────────────────────────────────

def article_exists(source_url: str) -> bool:
    """
    Check if canonical URL hash exists in local SQLite or Supabase.
    """
    url_hash = compute_url_hash(source_url)

    # 1. Check local SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM articles WHERE url_hash = ? OR source_url = ? LIMIT 1", (url_hash, source_url))
        if cur.fetchone() is not None:
            return True
    finally:
        conn.close()

    # 2. Check Supabase
    client = _get_supabase_client()
    if client:
        try:
            count_arg = CountMethod.exact if CountMethod is not None else None
            resp = client.table("articles").select("id", count=count_arg).eq("source_url", source_url).execute()
            if (resp.count or 0) > 0:
                return True
        except Exception:
            pass

    return False


def insert_article(
    *,
    source_url: str,
    domain: str,
    original_title: Optional[str] = None,
    original_author: Optional[str] = None,
    published_at: Optional[str] = None,
    original_content: str = "",
    genz_title: str = "",
    genz_content: str = "",
    genz_tags: Optional[list[str]] = None,
    niche: Optional[str] = None,
    headlines: Optional[list[str]] = None,
    meta_description: str = "",
    slug: str = "",
    hook: str = "",
    tldr: Optional[list[str]] = None,
    breakdown: str = "",
    why_it_matters: str = "",
    source_attribution: str = "",
    status: str = "done",
) -> dict[str, Any]:
    """
    Save the synthesized article into local SQLite and Supabase.
    """
    url_hash = compute_url_hash(source_url)
    tags_list = genz_tags or []
    headlines_list = headlines or [genz_title]
    tldr_list = tldr or []
    created_at = datetime.now(timezone.utc).isoformat()

    # 1. Insert into SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    row_id = None
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO articles (
                    url_hash, source_url, domain, niche, original_title, original_author,
                    published_at, original_content, genz_title, headlines_json,
                    meta_description, slug, genz_tags_json, hook, tldr_json,
                    breakdown, why_it_matters, source_attribution, genz_content,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url_hash, source_url, domain, niche, original_title, original_author,
                published_at, original_content, genz_title, json.dumps(headlines_list),
                meta_description, slug, json.dumps(tags_list), hook, json.dumps(tldr_list),
                breakdown, why_it_matters, source_attribution, genz_content,
                status, created_at
            ))
            row_id = cur.lastrowid
    finally:
        conn.close()

    result_data: dict[str, Any] = {
        "id": row_id or 1,
        "url_hash": url_hash,
        "source_url": source_url,
        "domain": domain,
        "niche": niche,
        "original_title": original_title,
        "original_author": original_author,
        "published_at": published_at,
        "genz_title": genz_title,
        "genz_content": genz_content,
        "genz_tags": tags_list,
        "meta_description": meta_description,
        "slug": slug,
        "status": status,
        "created_at": created_at,
    }

    # 2. Sync to Supabase
    client = _get_supabase_client()
    if client:
        try:
            payload = {
                "source_url": source_url,
                "domain": domain,
                "original_title": original_title,
                "original_author": original_author,
                "published_at": published_at,
                "original_content": original_content,
                "genz_title": genz_title,
                "genz_content": genz_content,
                "genz_tags": tags_list,
                "status": status,
            }
            sb_resp = client.table("articles").insert(payload).execute()
            if sb_resp.data:
                first_row = sb_resp.data[0]
                if isinstance(first_row, dict):
                    result_data["supabase_id"] = first_row.get("id")
        except Exception as exc:
            print(f"    [Supabase Note] Local SQLite saved; Supabase sync skipped: {exc}")

    return result_data


def get_article_by_id(article_id: int) -> Optional[dict[str, Any]]:
    """Fetch article by local ID."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["genz_tags"] = json.loads(d["genz_tags_json"]) if d.get("genz_tags_json") else []
        d["headlines"] = json.loads(d["headlines_json"]) if d.get("headlines_json") else []
        d["tldr"] = json.loads(d["tldr_json"]) if d.get("tldr_json") else []
        return d
    finally:
        conn.close()


def get_recent_articles(limit: int = 20, niche: Optional[str] = None) -> list[dict[str, Any]]:
    """Fetch the most recently generated articles."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        if niche:
            cur.execute(
                "SELECT id, domain, niche, genz_title, genz_tags_json, status, created_at FROM articles WHERE niche = ? ORDER BY id DESC LIMIT ?",
                (niche, limit)
            )
        else:
            cur.execute(
                "SELECT id, domain, niche, genz_title, genz_tags_json, status, created_at FROM articles ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        rows = cur.fetchall()
        result = []
        for r in rows:
            item = dict(r)
            item["genz_tags"] = json.loads(item["genz_tags_json"]) if item.get("genz_tags_json") else []
            result.append(item)
        return result
    finally:
        conn.close()
