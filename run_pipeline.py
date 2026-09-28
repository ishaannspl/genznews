# -*- coding: utf-8 -*-
"""
GenZNews Automated Content Aggregation & AI Publishing Engine
Executes end-to-end ingestion, SHA-256 deduplication, scraping,
Gemini Gen-Z synthesis, database persistence, and formatted output generation
across the 5 target PRD niches.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow local imports
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import feedparser
from dotenv import load_dotenv

from app.ai_writer import generate_genz_article
from app.database import article_exists, compute_url_hash, insert_article
from app.schemas import ScrapedData
from app.scraper import ArticleExtractionError, ScraperError, scrape_article

load_dotenv()

OUTPUT_DIR = ROOT_DIR / "output"
SOURCES_FILE = ROOT_DIR / "sources.json"


def load_sources() -> dict[str, Any]:
    """Load curated RSS sources categorized by the 5 PRD niches."""
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(f"Sources file missing: {SOURCES_FILE}")
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("niches", {})


def save_markdown_article(niche_key: str, article_data: dict[str, Any], genz_obj: Any) -> Path:
    """Save formatted article markdown file organized by niche directory."""
    niche_dir = OUTPUT_DIR / niche_key
    niche_dir.mkdir(parents=True, exist_ok=True)

    slug = genz_obj.slug or f"article-{int(time.time())}"
    filepath = niche_dir / f"{slug}.md"

    tags_formatted = ", ".join([f"#{t}" for t in genz_obj.genz_tags])
    headline_options_str = "\n".join([f"- Option {idx+1}: {hl}" for idx, hl in enumerate(genz_obj.headlines)])

    tldr_bullets = "\n".join([f"- {bullet}" for bullet in genz_obj.tldr])

    clean_attribution = genz_obj.source_attribution.replace("Sources: www.", "Sources: ").replace("Sources: https://", "Sources: ")

    md_content = f"""# {genz_obj.genz_title}

**Niche:** {niche_key.replace('_', ' ').title()}  
**Slug:** `{genz_obj.slug}`  
**Meta Description:** *{genz_obj.meta_description}*  
**Tags:** {tags_formatted}  
**Source URL:** [{article_data['domain']}]({article_data['source_url']})  
**Date Processed:** {article_data['created_at']}  

---

## Alternative Headline Options (A/B Testing)

{headline_options_str}

---

## The Hook

{genz_obj.hook}

## TL;DR (Quick Hits)

{tldr_bullets}

## The Breakdown

{genz_obj.breakdown}

## Why It Matters

{genz_obj.why_it_matters}

---

*{clean_attribution}*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    return filepath


def process_feed_article(entry: Any, niche_key: str, niche_name: str) -> dict[str, Any] | None:
    """Download, deduplicate, scrape, and rewrite a single article entry."""
    url = getattr(entry, "link", None)
    if not url:
        return None

    # Step 1: SHA-256 Deduplication check
    url_hash = compute_url_hash(url)
    if article_exists(url):
        print(f"  [-] Already processed (Hash: {url_hash[:10]}...): {url[:60]}...")
        return None

    print(f"\n  [+] New story discovered in [{niche_name}]:")
    print(f"      URL:  {url}")
    print(f"      Hash: {url_hash[:12]}...")

    # Step 2: Scrape raw content & parse metadata
    try:
        raw = scrape_article(url)
    except (ScraperError, ArticleExtractionError) as exc:
        print(f"      [x] Scraping skipped: {exc}")
        return None
    except Exception as exc:
        print(f"      [x] Unexpected scrape error: {exc}")
        return None

    print(f"      [>] Scraped {len(raw['content'])} characters from {raw['domain']}")

    scraped_data = ScrapedData(
        url=raw["url"],
        domain=raw["domain"],
        original_title=raw.get("title") or getattr(entry, "title", None),
        original_author=raw.get("author") or getattr(entry, "author", None),
        published_at=raw.get("published_at") or getattr(entry, "published", None),
        original_content=raw["content"],
        niche=niche_key,
        url_hash=url_hash,
    )

    # Step 3: Persona & Humanization (Gemini Gen Z Rewrite)
    print(f"      [>] Synthesizing Gen Z article with Gemini...")
    try:
        genz = generate_genz_article(scraped_data)
    except Exception as exc:
        print(f"      [x] AI Synthesis failed: {exc}")
        return None

    # Step 4: Persist to Database (SQLite + Supabase)
    print(f"      [>] Storing in database...")
    saved_row = insert_article(
        source_url=scraped_data.url,
        domain=scraped_data.domain,
        original_title=scraped_data.original_title,
        original_author=scraped_data.original_author,
        published_at=scraped_data.published_at,
        original_content=scraped_data.original_content,
        genz_title=genz.genz_title,
        genz_content=genz.genz_content,
        genz_tags=genz.genz_tags,
        niche=niche_key,
        headlines=genz.headlines,
        meta_description=genz.meta_description,
        slug=genz.slug,
        hook=genz.hook,
        tldr=genz.tldr,
        breakdown=genz.breakdown,
        why_it_matters=genz.why_it_matters,
        source_attribution=genz.source_attribution,
        status="done",
    )

    # Step 5: Save Markdown and Structured Output
    md_file = save_markdown_article(niche_key, saved_row, genz)
    print(f"      [v] Saved markdown: {md_file.relative_to(ROOT_DIR)}")

    return {
        "niche": niche_key,
        "niche_name": niche_name,
        "title": genz.genz_title,
        "slug": genz.slug,
        "hook": genz.hook,
        "tldr": genz.tldr,
        "breakdown": genz.breakdown,
        "why_it_matters": genz.why_it_matters,
        "meta_description": genz.meta_description,
        "tags": genz.genz_tags,
        "attribution": genz.source_attribution,
        "source_url": scraped_data.url,
        "markdown_file": str(md_file),
    }


def run_pipeline(articles_per_niche: int = 1, target_niches: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Run automated content ingestion and synthesis across the 5 niches.
    Produces target count of articles per niche.
    """
    niches = load_sources()
    selected_niches = target_niches or list(niches.keys())
    completed_articles: list[dict[str, Any]] = []

    print("=" * 70)
    print("  GENZNEWS AUTOMATED CONTENT AGGREGATION & AI REWRITING ENGINE")
    print("  Tagline: 'Truth First. News Always.'")
    print("=" * 70)

    for niche_key in selected_niches:
        if niche_key not in niches:
            print(f"[!] Unknown niche: {niche_key}, skipping.")
            continue

        niche_info = niches[niche_key]
        niche_name = niche_info["display_name"]
        feeds = niche_info.get("feeds", [])

        print(f"\n{'='*70}")
        print(f"NICHE: {niche_name.upper()} ({niche_key})")
        print(f"Focus: {niche_info['description']}")
        print(f"{'='*70}")

        niche_done = 0

        for feed_url in feeds:
            if niche_done >= articles_per_niche:
                break

            print(f"\n  Checking RSS: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
            except Exception as e:
                print(f"  [x] Failed to read feed {feed_url}: {e}")
                continue

            entries = feed.entries or []
            print(f"  Discovered {len(entries)} entries in feed.")

            for entry in entries:
                if niche_done >= articles_per_niche:
                    break

                result = process_feed_article(entry, niche_key, niche_name)
                if result:
                    completed_articles.append(result)
                    niche_done += 1
                    # Polite delay between LLM calls
                    time.sleep(2)

        if niche_done == 0:
            print(f"  [!] Note: No new articles could be processed for {niche_name} (all cached or scrapers blocked).")

    # Save summary manifest
    manifest_path = OUTPUT_DIR / "latest_batch.json"
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(completed_articles, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"PIPELINE RUN FINISHED: {len(completed_articles)} total articles generated.")
    print(f"Output directory : {OUTPUT_DIR}")
    print(f"Latest batch JSON: {manifest_path.relative_to(ROOT_DIR)}")
    print("=" * 70)

    return completed_articles


def main():
    parser = argparse.ArgumentParser(description="GenZNews Automated Content Aggregator")
    parser.add_argument(
        "--per-niche",
        type=int,
        default=1,
        help="Number of articles to generate per niche (default: 1, yields 5 articles across 5 niches)",
    )
    parser.add_argument(
        "--niches",
        nargs="*",
        help="Specific niches to run (options: health_wellness, education_career, entertainment_pop_culture, biogas_clean_energy, digital_marketing_social_media)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Continuous polling interval in minutes (default: 0 = run once). Set to e.g. 30 to continuously poll every 30 minutes.",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        run_pipeline(articles_per_niche=args.per_niche, target_niches=args.niches)
    else:
        print(f"[*] Starting continuous pipeline daemon: polling every {args.interval} minutes. Press Ctrl+C to stop.")
        cycle = 1
        try:
            while True:
                print(f"\n>>> [Cycle #{cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}] <<<")
                try:
                    run_pipeline(articles_per_niche=args.per_niche, target_niches=args.niches)
                except Exception as exc:
                    print(f"[!] Cycle #{cycle} encountered error: {exc}")
                print(f"\n[*] Cycle #{cycle} complete. Sleeping for {args.interval} minutes...")
                time.sleep(args.interval * 60)
                cycle += 1
        except KeyboardInterrupt:
            print("\n[!] Pipeline daemon stopped by user.")


if __name__ == "__main__":
    main()
