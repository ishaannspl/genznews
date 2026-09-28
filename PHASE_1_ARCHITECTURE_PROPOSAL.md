# GenZNews Automated Content Aggregation & AI Publishing Engine

## Phase 1 Architecture Proposal & Phased Technical Report

**Target Platform:** `genznews.site` | **CMS:** WordPress (Astra Theme / Elementor)  
**Assigned Role:** AI Developer Intern  
**Project Status:** Phase 1 – Architecture & Proposal (Complete with Phase 2 & 3 Production Prototypes)  
**Editorial Tagline:** *"Truth First. News Always."*  

---

## 1. Executive Summary & End-to-End Pipeline Architecture

GenZNews (`genznews.site`) requires an automated, high-throughput content curation engine that monitors trending news across 5 target PRD niches, extracts core facts, deduplicates stories, rewrites content in an authentic, razor-sharp Gen Z editorial persona, and prepares structured payloads for publication.

```mermaid
flowchart TD
    A[Curated RSS Feeds in sources.json\n15-20 Verified Feeds Across 5 Niches] -->|Every 30 Mins| B[Ingestion & URL Normalization]
    B --> C{SHA-256 Canonical\nURL Hash Exists?}
    C -->|Yes: Already Processed| D[Skip / Cache Hit]
    C -->|No: New Story| E[Trafilatura Headless Scraper\nMetadata + Clean Content Extraction]
    E --> F[Gemini 2.0 Flash Engine\nPersona Rewriting + Anti-Slop Guardrails]
    F --> G[Structured JSON Synthesis:\nHook, TL;DR, Breakdown, Why It Matters, SEO Bundle]
    G --> H[Dual Persistence Layer:\nSQLite articles.db + Supabase]
    G --> I[Markdown Output Generation\nOrganized by niche in /output/]
    G --> J[WordPress REST API POST\n/wp-json/wp/v2/posts as 'draft'\n(Optional Phase 4 Target)]
```

## End-to-End Workflow Breakdown

1. **Ingestion:** Polling 15 curated RSS feeds across the 5 niches every 30 minutes.
2. **Deduplication:** Canonical URL normalization (query param scrubbing: UTM, fbclid, ref) + SHA-256 hash lookup in database.
3. **Extraction:** Fast HTML/text extraction with Trafilatura, stripping boilerplate, ads, and navigation.
4. **Persona & Anti-Slop Synthesis:** Gemini 2.0 Flash prompt enforcing 5 core editorial sections and banning generic AI filler words.
5. **SEO & Media Bundle:** 3 CTR headline variants (for A/B testing), meta description (<155 chars), kebab-case URL slug, and 3–5 tags.
6. **Persistence & Export:** Local SQLite relational storage (`articles.db`) with full schema + Markdown export to niche folders + Supabase synchronization.

---

## 2. Low-Code (n8n + Supabase) vs. Code-First (Python + FastAPI)

| Evaluation Dimension | Option A: Low-Code (`n8n` + Supabase) | Option B: Code-First (`Python` + `FastAPI` / Celery) | Recommended Decision & Rationale |
| :--- | :--- | :--- | :--- |
| **Speed of Implementation** | **Very High** (Drag-and-drop nodes for RSS polling, HTTP requests, and Supabase inserts). | **Moderate** (Requires writing boilerplate code, route handlers, models, and CLI runners). | **Hybrid / Code-First Prototype:** Python script written with zero friction; code can easily be packaged into an n8n custom node or run standalone as a Docker container. |
| **Visual Debugging & Monitoring** | **Superior** (Visual canvas displays every execution step, variable state, and failed nodes with instant retries). | **CLI / Logs** (Requires logging frameworks like Loguru, Grafana Loki, or terminal stdout). | **n8n shines for non-dev operations**; however, Python CLI with structured logging gives developers full debugging depth. |
| **Custom Persona & Prompt Flexibility** | **Moderate** (Limited to prompt node configuration; complex token trimming or fallbacks requires JavaScript snippets). | **Maximum** (Full control over Pydantic validation, regex cleaning, retry decorators, and token budget throttling). | **Python Wins:** Essential for enforcing strict JSON schemas and anti-hallucination guardrails before saving. |
| **Long-Term Maintainability** | **Medium** (Complex workflows become spaghetti diagrams; version control of JSON workflows is clunky). | **High** (Pure modular Python: version-controlled with Git, unit-tested with Pytest, Dockerized). | **Python Wins:** Production-grade maintainability, clean separation of concerns (`scraper`, `ai_writer`, `database`, `schemas`). |
| **Operational Cost** | Cloud n8n costs $20–$50/mo. Self-hosted n8n requires VPS (~$5–$10/mo). | Runs anywhere (serverless AWS Lambda / Google Cloud Run / lightweight $5 VPS). | **Python Wins on cost efficiency and portability.** |

**Strategic Architecture Recommendation:**  

Use **Python (FastAPI + standalone daemon)** for core ingestion, deduplication, and LLM synthesis. Expose standard REST endpoints (`POST /generate`, `GET /articles`). If the editorial team later requires visual workflow automation, `n8n` can simply call the FastAPI webhook endpoints.

---

## 3. LLM Cost & Token Benchmark

**Sizing Baseline:** 100 articles/day  

- Average Input: ~2,500 tokens per scraped article (~250,000 input tokens/day)  
- Average Output: ~750 tokens per synthesized Gen Z draft (~75,000–300,000 output tokens/day)  

| Model | Input Price (per 1M tokens) | Output Price (per 1M tokens) | Daily Cost (100 articles) | Monthly Cost (~3,000 articles) | Latency & Speed | Recommendation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 2.0 Flash** *(Selected)* | **$0.10** | **$0.40** | **~$0.055 / day** | **~$1.65 / month** | **Sub-second (400–800ms)**; generous rate limits; excellent JSON adherence. | **RECOMMENDED PRIMARY** |
| **GPT-4o-mini** | $0.15 | $0.60 | ~$0.082 / day | ~$2.47 / month | Fast (1–2s); reliable instruction following. | Strong secondary fallback |
| **Claude 3.5 Haiku** | $0.80 | $4.00 | ~$0.500 / day | ~$15.00 / month | High stylistic flair, but 9x more expensive than Gemini Flash. | Tertiary / Premium testing only |

> [!TIP]
> **Cost Verdict:** **Gemini 2.0 Flash** delivers the highest throughput, lowest latency, and superior economics. At **under $2.00 per month** for 3,000 published articles, the operational cost is effectively negligible.

---

## 4. Prompt Engineering & Anti-Slop Editorial Persona

### Mandatory Editorial Structure

1. **The Hook:** 1–2 punchy sentences answering *"Why should you care right now?"*
2. **TL;DR (Quick Hits):** Exactly 3 crisp bullet points summarizing the key facts.
3. **The Breakdown:** Short, digestible paragraphs (2–3 sentences max each) with zero corporate jargon.
4. **Why It Matters:** Practical cultural, financial, lifestyle, or industry takeaway for youth.
5. **Source Footnote:** `Sources: {source_domain}. Synthesized and curated by GenZNews.`

### Forbidden AI Slop (Strictly Banned)

The system prompt explicitly bans corporate cliché markers that trigger audience drop-off and search engine algorithmic downgrades:

- ❌ *"In today's fast-paced world"*
- ❌ *"Delve"* / *"Delving"*
- ❌ *"Tapestry"*
- ❌ *"Testament to"*
- ❌ *"In conclusion"*
- ❌ *"Moreover"* / *"Furthermore"*
- ❌ *"Beacon"* / *"Landscape"* / *"Realm"* / *"Symphony"*
- ❌ *"It is important to remember"*

---

## 5. Live Production Samples Across All 5 PRD Niches

The pipeline has processed verified real-world news articles across each of the 5 PRD content niches:

| # | Niche | Article Title | Slug | Source Domain | Output Path |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Health & Wellness** | NHS Slaps Instant Suspensions on Medical Record Snoopers | `nhs-instant-suspension-medical-record-snoopers` | `bbc.co.uk` | `output/health_wellness/` |
| **2** | **Education & Career** | How One Principal Uses AI to Stop Burnout and Actually Lead | `ai-made-me-better-principal-edsurge` | `edsurge.com` | `output/education_career/` |
| **3** | **Entertainment & Pop Culture** | YouTube's New AI Agent Wants to Run Your Entire Channel | `youtube-new-ai-creator-tools-2026` | `theverge.com` | `output/entertainment_pop_culture/` |
| **4** | **Biogas & Clean Energy** | How to Be a Low-Key Clean Energy Advocate Without Making It Your Entire Personality | `realistic-clean-energy-ev-ebike-guide` | `cleantechnica.com` | `output/biogas_clean_energy/` |
| **5** | **Digital Marketing & Social Media** | Meta Ditches Cameras on New Ray-Ban AI Glasses to Escape the 'Creep' Factor | `meta-camera-free-ray-ban-ai-glasses` | `techcrunch.com` | `output/digital_marketing_social_media/` |

### Sample Showcase: Entertainment & Pop Culture

> **Headline:** YouTube's New AI Agent Wants to Run Your Entire Channel  
>
> **A/B Headline Options:**
>
> 1. *YouTube's New AI Agent Wants to Run Your Entire Channel*
> 2. *Inside YouTube's Massive AI Push for Creators*
> 3. *Can YouTube's New AI Tools Save Creators From Burnout?*  
>
> **The Hook:**  
> YouTube is rolling out automated AI agents that practically run your channel for you, handling everything from retrofitting old videos to drafting brand sponsorships. If you've ever wanted to outsource the most exhausting parts of content creation, the platform is now handing you the keys.  
>
> **TL;DR (Quick Hits):**  
>
> - YouTube introduced a new AI 'agent' at its annual Made on YouTube event to monitor back catalogs and suggest title or thumbnail tweaks for trending topics.  
> - Creators can now test three different versions of a video or thumbnail to see which one gets the highest watch time before locking it in.  
> - Execs insist these behind-the-scenes efficiency tools cross the line only when AI starts writing the actual scripts and shooting the content.  
>
> **Why It Matters:**  
> Burnout is the silent killer of the creator economy, forcing many internet personalities to rethink how they work. While relying on tech tools carries some reputational risk among audiences, offloading boring administrative tasks like brand pitches and thumbnail testing frees up actual hours for genuine creativity.  
>
> **Source Footnote:** *Sources: theverge.com. Synthesized and curated by GenZNews.*

---

## 6. How to Run the Automated Engine

### 1. Run Pipeline Once (Batch Ingestion Across 5 Niches)

```powershell
python run_pipeline.py --per-niche 1
```

### 2. Run Pipeline Continuously (Automated Daemon Polling Every 30 Minutes)

```powershell
python run_pipeline.py --per-niche 1 --interval 30
```

### 3. Run Pipeline for a Specific Niche Only

```powershell
python run_pipeline.py --niches entertainment_pop_culture digital_marketing_social_media
```

### 4. Run the FastAPI REST Server

```powershell
uvicorn app.main:app --reload --port 8000
```

- Interactive Swagger documentation: `http://localhost:8000/docs`
- Query by niche: `GET /articles?niche=entertainment_pop_culture`
- Get full article payload: `GET /articles/{id}`

### 5. Run Automated Tests

```powershell
python -m pytest -q tests/test_scraper.py
```
