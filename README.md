# ⚡ GenZNews: Autonomous Content Aggregation & AI Publishing Engine

> **Editorial Tagline**: *"Truth First. News Always."*  
> An automated, high-throughput intelligence engine that continuously monitors top Indian and global news outlets, extracts core facts, and synthesizes reporting into a razor-sharp, authentic Gen Z editorial voice.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%20Flash-4285F4.svg)](https://ai.google.dev)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20Supabase-green.svg)](https://supabase.com)
[![Type Checked](https://img.shields.io/badge/Type%20Safety-Pyright%200%20Errors-success.svg)](https://github.com/microsoft/pyright)

📖 **Looking for the child-friendly explanation? Read our [White Paper (ELI5)](./WHITE_PAPER_ELI5.md)**

---

## 🚀 Key Features

* 📰 **Predefined High-Authority Sources**: Ingests breaking news across 5 niches from **The Times of India**, **The Hindu**, **Dainik Jagran (Hindi)**, **The Indian Express**, and **Hindustan Times**.
* 🔍 **Canonical SHA-256 Deduplication**: Automatically normalizes URLs (scrubbing UTM and tracking tokens) to prevent duplicate processing.
* 🍌 **Ad-Free Extraction**: Uses **Trafilatura** to strip 90% of page bloat, cookie banners, navigation menus, and video popups.
* 🧠 **Gen Z Persona Rewriting**: Enforces strict journalistic structures (The Hook, TL;DR 3 Bullets, The Breakdown, Why It Matters, SEO Bundle).
* 🚫 **Anti-Slop Guardrails & Zero Em-Dashes**: Strictly bans AI corporate clichés (*"in today's fast-paced world"*, *"delve"*, *"tapestry"*) and automatically sanitizes all em-dashes (`—`).
* 🌐 **Cross-Lingual Support**: Automatically translates and modernizes Hindi Devanagari reports into punchy English news.
* ⏰ **Automated 24/7 Scheduling**: Run on-demand or schedule daily 24-hour cycles via `--interval 1440`.
* 🗄️ **Dual Persistence**: Saves to local SQLite (`articles.db`) and real-time cloud Supabase PostgreSQL.

---

## 🛠️ Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/genznews-ai-publisher.git
cd genznews-ai-publisher

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your `GEMINI_API_KEY` (get one free at [aistudio.google.dev](https://aistudio.google.dev)) and optional Supabase credentials.

---

## 🏃 Execution Commands

### Run Standard Pipeline (1 article per niche)
```bash
python run_pipeline.py --per-niche 1
```

### Run Continuously Every 24 Hours
```bash
python run_pipeline.py --interval 1440 --per-niche 1
```

### Run Specifically for the 5 Top Indian Outlets
```bash
python run_specific_indian_batch.py
```

### Launch Real-Time REST API
```bash
uvicorn app.main:app --reload
```
Open interactive docs at `http://127.0.0.1:8000/docs`.

---

## 📂 Project Architecture

```
GENZNWS/
├── app/
│   ├── ai_writer.py       # Gemini Flash prompt, persona, anti-slop, em-dash sanitizer
│   ├── config.py          # Environment settings and timeout controls
│   ├── database.py        # SQLite persistence & Supabase cloud sync
│   ├── main.py            # FastAPI production REST API
│   ├── schemas.py         # Pydantic data models & typing
│   └── scraper.py         # Trafilatura cleaner & requests engine
├── output/                # Markdown articles sorted by niche
├── sources.json           # Predefined curated RSS feeds
├── run_pipeline.py        # Autonomous CLI pipeline runner with scheduler
├── run_specific_indian_batch.py # Dedicated runner for the 5 major Indian outlets
├── WHITE_PAPER_ELI5.md    # Complete White Paper explained for 5-year-olds
├── requirements.txt       # Dependencies
└── .env.example           # Safe configuration template
```

---

## 📄 License
MIT License. Built for GenZNews.site.
