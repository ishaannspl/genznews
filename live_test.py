# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
Live scraper test - runs scrape_article() against real URLs
and prints a compact report for each source.
Run from the project root: python live_test.py
"""

import sys
import os

# Allow running from root without installing the package
sys.path.insert(0, os.path.dirname(__file__))

from app.scraper import scrape_article, ScraperError

ARTICLES = {
    "TOI": "https://timesofindia.indiatimes.com/education/news/sbi-offers-free-online-courses-on-ai-banking-finance-marketing-and-more-check-details/articleshow/134482593.cms",
    "Jagran": "https://www.jagran.com/news/education-bseb-stet-dummy-admit-card-2026-will-be-released-today-and-candidates-opportunity-to-make-corrections-until-september-30-40384505.html",
    "HT": "https://www.hindustantimes.com/education/news/ayodhya-declares-holiday-for-all-schools-on-september-25-amid-heavy-rainfall-forecast-101790307598021.html",
    "Indian Express": "https://indianexpress.com/article/cities/mumbai/campus-vote-maharashtra-moves-to-revive-student-elections-10892864/",
    "Guardian": "https://www.theguardian.com/global-development/2026/sep/25/africa-young-talent-decolonise-universities-public-health-expert-john-nkengasong-higher-education",
}

print("=" * 65)
print("GENZNWS — Live Scraper Test  |  25 Sep 2026")
print("=" * 65)

results = {}

for source, url in ARTICLES.items():
    print(f"\n>>> {source}")
    print(f"   URL: {url[:80]}...")
    try:
        art = scrape_article(url)
        chars = len(art["content"])
        preview = art["content"][:200].replace("\n", " ")
        results[source] = "[PASS]"
        print(f"   HTTP:         200 OK")
        print(f"   TITLE:        {art['title']}")
        print(f"   AUTHOR:       {art['author']}")
        print(f"   PUBLISHED_AT: {art['published_at']}")
        print(f"   CONTENT_CHARS:{chars}")
        print(f"   PREVIEW:      {preview}...")
        print(f"   STATUS:       [PASS]")
    except ScraperError as exc:
        results[source] = f"[FAIL] {exc}"
        print(f"   STATUS:       [FAIL]")
        print(f"   ERROR:        {exc}")
    except Exception as exc:
        results[source] = f"[ERROR] {exc}"
        print(f"   STATUS:       [ERROR] UNEXPECTED")
        print(f"   ERROR:        {exc}")

print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
for source, status in results.items():
    print(f"  {source:<16} {status}")
print("=" * 65)
