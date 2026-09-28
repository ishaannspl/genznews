"""Rewrite a news article in Gen-Z style according to PRD Phase 3 specifications using Gemini Flash."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from .schemas import GenZArticle, ScrapedData

load_dotenv()

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are GenZNewsAI — the lead editorial voice of GenZNews (genznews.site).
Tagline: "Truth First. News Always."

Your mission is to synthesize news into an engaging, razor-sharp, authentic Gen Z editorial voice.

EDITORIAL STANDARDS & MANDATORY STRUCTURE:
1. The Hook: 1–2 punchy sentences answering "Why should you care right now?"
2. TL;DR (Quick Hits): Exactly 3 crisp bullet points summarizing the gist.
3. The Breakdown: Short, digestible paragraphs (2–3 sentences max each) explaining what happened without corporate jargon or fluff.
4. Why It Matters: Practical cultural, financial, lifestyle, or industry takeaway for youth.
5. Source Footnote: "Sources: {source_domain}. Synthesized and curated by GenZNews."

FORBIDDEN AI SLOP (STRICTLY BANNED):
Do NOT use ANY of these words or phrases:
- "In today's fast-paced world"
- "Delve" or "Delving"
- "Tapestry"
- "Testament to"
- "In conclusion"
- "Moreover"
- "Furthermore"
- "Beacon"
- "Landscape"
- "Realm"
- "Symphony"
- "It is important to remember"
- Any robotic corporate transitions.
- Em-dashes ("—", "–", or "--") anywhere in your output. NEVER use em-dashes. Use colons, commas, periods, or standard hyphens instead.

TONE:
- Direct, smart, culturally clued-in, slightly witty, but 100% factually accurate.
- NOT cringe slang overload — speak like an intelligent Gen Z creator / journalist on Substack or Twitter/X.
- Zero hallucination of facts: rewrite only verified points from the source.

SEO BUNDLE:
- 3 high-CTR headline options (Punchy, intriguing, honest)
- 1 selected primary headline
- Meta description (STRICTLY under 155 characters)
- Clean kebab-case URL slug (e.g. "clean-energy-biogas-2026-bet")
- 3 to 5 relevant lowercase tags

CRITICAL OUTPUT FORMAT:
You MUST respond with a single valid JSON object with NO markdown code fences (no ```json).
Start your response with { and end with }.

JSON schema:
{
  "selected_headline": "string",
  "headline_options": ["string", "string", "string"],
  "meta_description": "string under 155 chars",
  "slug": "kebab-case-slug",
  "tags": ["tag1", "tag2", "tag3"],
  "hook": "1-2 punchy sentences",
  "tldr": ["point 1", "point 2", "point 3"],
  "breakdown": "Paragraph 1 (2-3 sentences).\\n\\nParagraph 2 (2-3 sentences).",
  "why_it_matters": "Practical takeaway paragraph.",
  "source_attribution": "Sources: [Domain/Outlet]. Synthesized and curated by GenZNews."
}"""


def _build_user_prompt(article: ScrapedData) -> str:
    lines = []
    if article.niche:
        lines.append(f"TARGET NICHE: {article.niche}")
    if article.original_title:
        lines.append(f"ORIGINAL HEADLINE: {article.original_title}")
    if article.original_author:
        lines.append(f"AUTHOR: {article.original_author}")
    if article.published_at:
        lines.append(f"DATE: {article.published_at}")
    lines.append(f"SOURCE OUTLET / DOMAIN: {article.domain}")
    lines.append("")
    lines.append("SOURCE ARTICLE CONTENT:")
    lines.append(article.original_content[:8000])
    return "\n".join(lines)


def _parse_json(raw: str) -> dict[str, Any]:
    """Extract a JSON object from model output robustly."""
    raw = raw.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    # Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Regex search for JSON block
    match = re.search(r"(\{.*\})", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find candidate block with selected_headline or genz_title
    for candidate in re.finditer(r"\{[^{}]*\}", raw, re.DOTALL):
        try:
            data = json.loads(candidate.group())
            if "selected_headline" in data or "genz_title" in data:
                return data
        except json.JSONDecodeError:
            continue

    raise RuntimeError(f"Could not parse valid JSON from model output: {raw[:400]}")


def remove_em_dashes(text: str) -> str:
    """Replace em-dashes, en-dashes, and double hyphens with clean punctuation."""
    if not text:
        return text
    text = re.sub(r"(?<=\w)[—–](?=[A-Z])", ": ", text)
    text = re.sub(r"(?<=\w)[—–](?=[a-z])", ", ", text)
    text = re.sub(r"\s*[—–]\s*", " - ", text)
    text = text.replace("—", " - ").replace("–", "-").replace(" -- ", " - ")
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


# ── Core caller with retry ────────────────────────────────────────────────────

def _call_gemini(client: genai.Client, model_name: str, prompt: str) -> str:
    """Call Gemini with retries on temporary overloads."""
    wait = 4
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
            )
            text = response.text
            if not text or not text.strip():
                raise RuntimeError("Gemini returned an empty response")
            return text.strip()

        except genai_errors.ServerError as exc:
            if "503" in str(exc) or "UNAVAILABLE" in str(exc):
                if attempt < 3:
                    print(f"    [Gemini] Overloaded, retrying in {wait}s... ({attempt+1}/4)")
                    time.sleep(wait)
                    wait *= 2
                else:
                    raise
            else:
                raise

    raise RuntimeError("Gemini request failed after maximum retries.")


# ── Public API ────────────────────────────────────────────────────────────────

def generate_genz_article(article: ScrapedData) -> GenZArticle:
    """
    Send the scraped article to Gemini and return a fully structured
    GenZArticle adhering strictly to PRD Phase 3 editorial guidelines.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")

    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    client = genai.Client(api_key=api_key)
    full_prompt = f"{_SYSTEM_PROMPT}\n\n{_build_user_prompt(article)}"

    try:
        raw = _call_gemini(client, primary_model, full_prompt)
    except Exception as exc:
        print(f"    [Gemini] Primary model ({primary_model}) failed: {exc}. Trying fallback...")
        raw = _call_gemini(client, "gemini-3.5-flash-lite", full_prompt)

    data = _parse_json(raw)

    headline = remove_em_dashes(
        data.get("selected_headline")
        or data.get("genz_title")
        or (data.get("headline_options", [""])[0] if data.get("headline_options") else "")
        or "GenZNews Update"
    )
    raw_headlines = data.get("headline_options") or [headline]
    headlines = [remove_em_dashes(str(h)) for h in raw_headlines]
    meta_desc = remove_em_dashes(data.get("meta_description") or "")
    slug = data.get("slug") or re.sub(r"[^a-z0-9]+", "-", headline.lower()).strip("-")
    slug = re.sub(r"[—–]+", "-", slug).strip("-")
    raw_tags = data.get("tags") or data.get("genz_tags") or []
    tags = [remove_em_dashes(str(t)) for t in raw_tags]
    hook = remove_em_dashes(data.get("hook") or "")
    raw_tldr = data.get("tldr") or []
    tldr = [remove_em_dashes(str(item)) for item in raw_tldr] if isinstance(raw_tldr, list) else [remove_em_dashes(str(raw_tldr))]
    breakdown = remove_em_dashes(data.get("breakdown") or "")
    why_it_matters = remove_em_dashes(data.get("why_it_matters") or "")
    attribution = remove_em_dashes(data.get("source_attribution") or f"Sources: {article.domain}. Synthesized and curated by GenZNews.")

    # Format full readable piece
    tldr_formatted = "\n".join([f"- {item}" for item in tldr]) if isinstance(tldr, list) else str(tldr)
    full_content = f"""**The Hook**
{hook}

**TL;DR (Quick Hits)**
{tldr_formatted}

**The Breakdown**
{breakdown}

**Why It Matters**
{why_it_matters}

---
*{attribution}*"""

    return GenZArticle(
        genz_title=headline,
        headlines=headlines,
        meta_description=meta_desc,
        slug=slug,
        genz_tags=tags,
        hook=hook,
        tldr=tldr if isinstance(tldr, list) else [str(tldr)],
        breakdown=breakdown,
        why_it_matters=why_it_matters,
        source_attribution=attribution,
        genz_content=full_content,
        niche=article.niche,
    )
