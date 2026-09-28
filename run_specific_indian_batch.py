# -*- coding: utf-8 -*-
"""
Generate Gen-Z synthesized news specifically from the 5 requested Indian news outlets:
1. The Indian Express
2. The Hindu
3. Dainik Jagran (Hindi source)
4. The Times of India
5. Hindustan Times
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import feedparser
from dotenv import load_dotenv

from app.ai_writer import generate_genz_article
from app.database import article_exists, compute_url_hash, insert_article
from app.schemas import ScrapedData
from app.scraper import ArticleExtractionError, ScraperError, scrape_article
from run_pipeline import save_markdown_article

load_dotenv()

TARGET_OUTLETS = [
    {
        "outlet_name": "The Indian Express",
        "niche": "digital_marketing_social_media",
        "feed_url": "https://indianexpress.com/section/technology/feed/",
    },
    {
        "outlet_name": "The Hindu",
        "niche": "education_career",
        "feed_url": "https://www.thehindu.com/sci-tech/feeder/default.rss",
    },
    {
        "outlet_name": "Dainik Jagran",
        "niche": "entertainment_pop_culture",
        "feed_url": "https://rss.jagran.com/rss/technology/tech-news.xml",
    },
    {
        "outlet_name": "The Times of India",
        "niche": "health_wellness",
        "feed_url": "https://timesofindia.indiatimes.com/rssfeeds/3908999.cms",
    },
    {
        "outlet_name": "Hindustan Times",
        "niche": "education_career",
        "feed_url": "https://www.hindustantimes.com/feeds/rss/education/rssfeed.xml",
    },
]


def run_5_outlets():
    print("=" * 70)
    print("PROCESSING 1 LATEST ARTICLE FROM EACH OF THE 5 REQUESTED INDIAN OUTLETS:")
    print("1. The Indian Express")
    print("2. The Hindu")
    print("3. Dainik Jagran (Hindi)")
    print("4. The Times of India")
    print("5. Hindustan Times")
    print("=" * 70)

    results = []

    for item in TARGET_OUTLETS:
        outlet = item["outlet_name"]
        feed_url = item["feed_url"]
        niche = item["niche"]

        print(f"\n[{outlet}] Fetching latest feed from: {feed_url}")
        feed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
        if not feed.entries:
            print(f"  [x] No entries found for {outlet}")
            continue

        # Look for the first un-processed entry
        selected_entry = None
        for entry in feed.entries:
            link = getattr(entry, "link", None)
            if not link:
                continue
            selected_entry = entry
            break

        if not selected_entry:
            print(f"  [x] No valid links in feed for {outlet}")
            continue

        url = selected_entry.link
        title = getattr(selected_entry, "title", "No Title")
        pub_date = getattr(selected_entry, "published", getattr(selected_entry, "updated", "Today"))
        print(f"  [+] Latest Story: {title}")
        print(f"      Published : {pub_date}")
        print(f"      URL       : {url}")

        # Scrape
        print(f"      [>] Scraping article text...")
        try:
            raw = scrape_article(url)
            print(f"      [v] Scraped {len(raw['content'])} characters from {raw['domain']}")
        except Exception as exc:
            print(f"      [x] Scraping failed: {exc}")
            continue

        scraped_data = ScrapedData(
            url=raw["url"],
            domain=raw["domain"],
            original_title=raw.get("title") or title,
            original_author=raw.get("author") or getattr(selected_entry, "author", None),
            published_at=raw.get("published_at") or pub_date,
            original_content=raw["content"],
            niche=niche,
            url_hash=compute_url_hash(raw["url"]),
        )

        # AI Rewrite with Gemini
        print(f"      [>] Synthesizing Gen Z article with Gemini...")
        try:
            genz = generate_genz_article(scraped_data)
        except Exception as exc:
            print(f"      [x] AI Synthesis failed: {exc}")
            continue

        # Save to DB
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
            niche=niche,
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

        # Save to Markdown
        md_file = save_markdown_article(niche, saved_row, genz)
        print(f"      [v] Saved Markdown: {md_file.relative_to(ROOT_DIR)}")

        results.append({
            "outlet": outlet,
            "niche": niche,
            "title": genz.genz_title,
            "source_url": url,
            "markdown_path": str(md_file),
            "hook": genz.hook,
            "tldr": genz.tldr,
        })

        time.sleep(2)

    print("\n" + "=" * 70)
    print(f"COMPLETED: Generated {len(results)} articles across the 5 Indian outlets!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_5_outlets()
