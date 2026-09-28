# -*- coding: utf-8 -*-
"""Quick connection test for Gemini + Supabase before starting the server."""

import io
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("GENZNEWS -- System & Database Connection Check")
print("=" * 60)

# ── 1. Gemini AI Engine ─────────────────────────────────────
print("\n[1] Testing Gemini AI Connection...")
api_key = os.getenv("GEMINI_API_KEY", "")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

connected = False
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model_name,
        contents="Reply with exactly: OK",
    )
    print("   Status : CONNECTED (google.genai SDK)")
    print(f"   Model  : {model_name}")
    print(f"   Reply  : {resp.text.strip()[:60]}")
    connected = True
except Exception as e:
    pass

if not connected:
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel(model_name)
        resp = model.generate_content("Reply with exactly: OK")
        print("   Status : CONNECTED (legacy genai SDK)")
        print(f"   Model  : {model_name}")
        print(f"   Reply  : {resp.text.strip()[:60]}")
    except Exception as exc:
        print("   Status : FAILED")
        print(f"   Error  : {exc}")

# ── 2. Supabase Cloud Database ──────────────────────────────
print("\n[2] Testing Supabase Connection...")
url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").strip()
key = (os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") or "").strip()

try:
    from supabase import create_client
    sb = create_client(url, key)
    resp = sb.table("articles").select("id, domain, genz_title").limit(5).execute()
    print("   Status : CONNECTED")
    print(f"   URL    : {url}")
    print(f"   Table  : 'articles' exists! Rows retrieved: {len(resp.data)}")
    for item in resp.data:
        print(f"            - [ID: {item['id']}] {item['domain']}: {item['genz_title'][:40]}...")
except Exception as exc:
    print("   Status : FAILED")
    print(f"   Error  : {exc}")

print("\n" + "=" * 60)
