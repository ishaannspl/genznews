# 📰 The GenZNews White Paper
### *How Our Autonomous AI News Engine Works (Explained for a 5-Year-Old)*

---

```
       +--------------------------------------------------------------+
       |   "Truth First. News Always." — The Autonomous News Robot    |
       +--------------------------------------------------------------+
                                      |
              [ 1. THE MAILBOX: Predefined News Feeds ]
              (Times of India, The Hindu, Dainik Jagran, etc.)
                                      |
                                      v
              [ 2. THE FINGERPRINT: SHA-256 Deduplication ]
              (Have I seen this story before? Skip if yes!)
                                      |
                                      v
              [ 3. THE FRUIT PEELER: Trafilatura Scraper ]
              (Throw away ads, popups, and banners; keep pure news)
                                      |
                                      v
              [ 4. THE STORYTELLER: Gemini Flash AI ]
              (Rewrite like a sharp, witty Gen Z creator; NO em-dashes!)
                                      |
                                      v
              [ 5. THE TOY CHEST: SQLite + Supabase + Markdown ]
              (Safe storage, organized by niche, ready for WordPress)
```

---

## 🧸 Table of Contents
1. [The Big Idea (Why We Built This)](#1-the-big-idea-why-we-built-this)
2. [Meet the Cast of Characters (The 5 Parts of Our Robot)](#2-meet-the-cast-of-characters-the-5-parts-of-our-robot)
3. [The Magical 5-Step Journey of a News Story](#3-the-magical-5-step-journey-of-a-news-story)
4. [The 5 Playgrounds (The 5 News Niches)](#4-the-5-playgrounds-the-5-news-niches)
5. [The Secret Rulebook (Anti-Slop & Zero Em-Dashes)](#5-the-secret-rulebook-anti-slop--zero-em-dashes)
6. [How the Robot Runs Every Day (The 24-Hour Alarm Clock)](#6-how-the-robot-runs-every-day-the-24-hour-alarm-clock)
7. [The Grown-Up Tech Specs (For Engineers)](#7-the-grown-up-tech-specs-for-engineers)
8. [How to Put This Project on GitHub](#8-how-to-put-this-project-on-github)

---

## 1. The Big Idea (Why We Built This)

Imagine your parents give you a newspaper. It is as big as a blanket, covered in tiny black words, full of boring adult talk (*"henceforth"*, *"furthermore"*), and covered in 50 noisy ads trying to sell you car insurance. You would probably put it down in 5 seconds.

**GenZNews is a smart robot friend.**
It wakes up, reads those giant, boring newspapers across India, throws away all the advertisements, finds the coolest true facts, and rewrites the stories like an exciting, witty friend telling you what happened in plain English!

---

## 2. Meet the Cast of Characters (The 5 Parts of Our Robot)

| Character | Real Tech Name | What It Does (ELI5) |
| :--- | :--- | :--- |
| 📬 **The Mailbox Peeker** | `feedparser` (RSS) | Knocks on the doors of *The Hindu*, *Times of India*, and *Dainik Jagran* to see if they wrote any new stories today. |
| 🔍 **The Detective's Stamp** | `hashlib` (SHA-256) | Stamps a secret fingerprint on every story so the robot never wastes time reading the same story twice. |
| 🍌 **The Banana Peeler** | `trafilatura` (Scraper) | Peels away the ugly wrapper (cookie banners, sidebars, video popups) and keeps only the sweet fruit (the real story). |
| 🧠 **The Cool Storyteller** | `Gemini 2.0 Flash` (AI) | Takes the facts and tells them in a punchy Gen-Z voice with zero boring corporate jargon and **zero em-dashes**. |
| 🗄️ **The Toy Chest** | SQLite (`articles.db`) & Supabase | Neatly stacks the finished stories into folders so the world can read them on the website. |

---

## 3. The Magical 5-Step Journey of a News Story

### Step 1: The Magic Mailbox (`sources.json`)
Every morning, newspapers like **The Times of India**, **The Indian Express**, **The Hindu**, **Dainik Jagran**, and **Hindustan Times** drop their newest letters into a digital mailbox called an **RSS Feed**. 
Our robot doesn't wander around aimlessly; it checks this exact mailbox every time.

### Step 2: The Fingerprint Check (Deduplication)
Before reading, the robot calculates a special mathematical fingerprint (called a **SHA-256 hash**) from the story link. 
* *Did we read this yesterday?* **Yes** -> Skip it! Save time and brainpower!
* *Is it brand new?* **No** -> Let's read it!

### Step 3: Peeling the Banana (Scraping)
When you open a news website, 90% of the page is noisy junk: blinking banner ads, autoplaying videos, and popups asking for your email.
Our scraper uses **Trafilatura** to act like a fruit peeler: it slices off all the ads and leaves **pure, clean article sentences**, the author's name, and the date.

### Step 4: The Storyteller Makeover (Gemini AI)
Even if the story was written in Hindi (like in *Dainik Jagran*), our AI reads it, understands the facts, and rewrites it into 4 punchy parts:
1. **The Hook**: 1–2 sentences telling you *"Why should you care right now?"*
2. **TL;DR (Quick Hits)**: Exactly 3 bullet points giving you the summary in 10 seconds.
3. **The Breakdown**: Short, snappy paragraphs (2–3 sentences each). No walls of text!
4. **Why It Matters**: How this affects your life, job, wallet, or future.

### Step 5: Tucking It into the Toy Chest
The robot saves the finished story as a beautiful Markdown file in `output/` and syncs it to our cloud database (Supabase), ready to be pushed to WordPress!

---

## 4. The 5 Playgrounds (The 5 News Niches)

The robot only cares about 5 specific topics that matter to young people:

1. 🧘 **Health & Wellness**: Mental health, biohacking, simple natural remedies, fitness.
2. 🎓 **Education & Career**: Tech careers, AI learning tools, student inventors, jobs of the future.
3. 🎮 **Entertainment & Pop Culture**: Gaming tournaments, YouTube/creators, movies, viral trends.
4. ⚡ **Biogas & Clean Energy**: Electric vehicles, green innovations, solar power, fighting pollution.
5. 📱 **Digital Marketing & Social Media**: Instagram/TikTok algorithms, creator economy, gadgets.

---

## 5. The Secret Rulebook (Anti-Slop & Zero Em-Dashes)

Our robot follows very strict rules so it never sounds like a boring corporate bot:

### 🚫 The Banned Word List
If the AI tries to say any of these words, it gets a penalty:
* ❌ *"In today's fast-paced world"*
* ❌ *"Delve"* or *"Delving"*
* ❌ *"Tapestry"*
* ❌ *"Testament to"*
* ❌ *"In conclusion"*
* ❌ *"Moreover"* / *"Furthermore"*

### 🚫 The Absolute Zero Em-Dash Rule
AI models love using long dashes (`—`). Real young creators don't talk like that.
Our robot has an **automatic em-dash ban**:
* Every em-dash is strictly forbidden in the prompt.
* If one slips in, a code cleaner turns it into a natural comma, colon, or hyphen.
* Result: **0 em-dashes in every article.**

---

## 6. How the Robot Runs Every Day (The 24-Hour Alarm Clock)

You can choose how your robot works:

* **Want it to run just once right now?**
  ```bash
  python run_pipeline.py --per-niche 1
  ```
  *(Takes ~30 seconds, makes 5 fresh stories, and goes to sleep).*

* **Want it to run automatically every day (24 hours)?**
  ```bash
  python run_pipeline.py --interval 1440 --per-niche 1
  ```
  *(1440 minutes = 24 hours. It wakes up every day, checks the mailbox, writes 5 stories, and goes back to sleep).*

---

## 7. The Grown-Up Tech Specs (For Engineers)

For developers who want the architectural details:

* **Language**: Python 3.11+
* **Feed Ingestion**: `feedparser` with reverse-chronological parsing.
* **Extraction Engine**: `trafilatura` for heuristic boiler-plate removal.
* **Deduplication**: Canonical URL normalization (query scrubbing) + SHA-256 hash collision checks.
* **Language Model**: Google `gemini-2.0-flash` (via official `google-genai` SDK) with JSON mode (`response_mime_type="application/json"`).
* **Storage**: Local SQLite (`articles.db`) with WAL mode + cloud synchronization to Supabase PostgreSQL.
* **Type Safety**: Pyright verified with 0 errors, 0 warnings.
* **Publishing Target**: WordPress REST API (`/wp-json/wp/v2/posts`) with `status: "draft"`.

---

## 8. How to Put This Project on GitHub

Follow these simple steps in your terminal to safely publish this code to GitHub:

### Step 1: Initialize Git
```bash
git init
```

### Step 2: Ensure Secrets Are Ignored
Check that your `.gitignore` has `.env` and `articles.db` (we already set this up for you so your Gemini API keys will never leak).

### Step 3: Add and Commit Your Code
```bash
git add .
git commit -m "feat: complete autonomous GenZNews aggregation and publishing pipeline"
```

### Step 4: Create a New Repo on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Name your repository (e.g., `genznews-ai-publisher`).
3. Keep it **Public** or **Private**, and leave "Initialize with README" unchecked.

### Step 5: Push Your Code
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/genznews-ai-publisher.git
git push -u origin main
```

🎉 **Congratulations! Your autonomous news engine is now live and open-source on GitHub!**
