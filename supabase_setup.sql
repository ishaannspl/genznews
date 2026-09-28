-- Run this ONCE in your Supabase project's SQL Editor
-- Dashboard → SQL Editor → New Query → paste this → Run

CREATE TABLE IF NOT EXISTS articles (
  id                BIGSERIAL PRIMARY KEY,
  source_url        TEXT NOT NULL UNIQUE,   -- deduplication key
  domain            TEXT NOT NULL,
  original_title    TEXT,
  original_author   TEXT,
  published_at      TEXT,
  original_content  TEXT NOT NULL,
  genz_title        TEXT,
  genz_content      TEXT,
  genz_tags         TEXT[],
  status            TEXT DEFAULT 'done',
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- This is a backend-only API (no per-user auth), so disable RLS
ALTER TABLE articles DISABLE ROW LEVEL SECURITY;

-- Optional: index for fast lookups by domain or date
CREATE INDEX IF NOT EXISTS idx_articles_domain     ON articles (domain);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles (created_at DESC);

-- Verify the table was created
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'articles'
ORDER BY ordinal_position;
