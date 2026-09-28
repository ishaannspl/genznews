# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Full pipeline test:
  URL -> scraper -> Gemini rewrite -> Supabase save -> print result
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from app.scraper import scrape_article
from app.schemas import ScrapedData
from app.ai_writer import generate_genz_article
from app.database import insert_article, article_exists

# Use TOI article from earlier test
TEST_URL = "https://timesofindia.indiatimes.com/education/news/sbi-offers-free-online-courses-on-ai-banking-finance-marketing-and-more-check-details/articleshow/134482593.cms"

print("=" * 60)
print("GENZNWS -- Full Pipeline Test")
print("=" * 60)

# ── Step 1: Check dedup ───────────────────────────────────────
print("\n[0] Deduplication check...")
if article_exists(TEST_URL):
    print("    Already processed! Skipping. Check Supabase for existing row.")
    sys.exit(0)
print("    Not yet processed. Continuing...")

# ── Step 1: Scrape ────────────────────────────────────────────
print("\n[1] Scraping article...")
raw = scrape_article(TEST_URL)
print(f"    Title   : {raw['title']}")
print(f"    Author  : {raw['author']}")
print(f"    Date    : {raw['published_at']}")
print(f"    Chars   : {len(raw['content'])}")

scraped = ScrapedData(
    url=raw["url"],
    domain=raw["domain"],
    original_title=raw["title"],
    original_author=raw["author"],
    published_at=raw["published_at"],
    original_content=raw["content"],
)

# ── Step 2: AI rewrite ────────────────────────────────────────
print("\n[2] Generating Gen-Z rewrite via Gemini...")
genz = generate_genz_article(scraped)
print(f"    GenZ Title   : {genz.genz_title}")
print(f"    GenZ Tags    : {genz.genz_tags}")
print(f"    Content (200): {genz.genz_content[:200]}...")

# ── Step 3: Save to Supabase ──────────────────────────────────
print("\n[3] Saving to Supabase...")
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
)
print(f"    Saved! Row ID  : {saved['id']}")
print(f"    Created at     : {saved['created_at']}")

print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print("=" * 60)
print(f"\nFINAL OUTPUT:")
print(f"  ID             : {saved['id']}")
print(f"  Source         : {saved['domain']}")
print(f"  Original Title : {saved['original_title']}")
print(f"  Gen-Z Title    : {saved['genz_title']}")
print(f"  Tags           : {saved['genz_tags']}")
print(f"\nFULL GEN-Z ARTICLE:")
print("-" * 60)
print(genz.genz_content)
print("-" * 60)
