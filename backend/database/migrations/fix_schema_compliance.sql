-- Schema Compliance Fix Migration
-- Generated: 2025-12-27
-- Purpose: Fix schema mismatches found in compliance audit

-- =============================================================================
-- Phase 1: news_articles - Add missing columns
-- =============================================================================

-- Add missing columns
ALTER TABLE news_articles
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_analyzed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS published_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20),
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

-- Update NULL values in source before setting NOT NULL
UPDATE news_articles SET source = 'legacy' WHERE source IS NULL;

-- Set source to NOT NULL
ALTER TABLE news_articles ALTER COLUMN source SET NOT NULL;

-- Update url to NOT NULL (if needed)
UPDATE news_articles
SET
    url = CONCAT('legacy_', id::text)
WHERE
    url IS NULL
    OR url = '';

ALTER TABLE news_articles ALTER COLUMN url SET NOT NULL;

-- =============================================================================
-- Phase 2: trading_signals - Add missing columns
-- =============================================================================

-- Add missing columns
ALTER TABLE trading_signals
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS executed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS metadata JSONB,
ADD COLUMN IF NOT EXISTS exit_price FLOAT,
ADD COLUMN IF NOT EXISTS outcome_recorded_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP;

-- Update NULL values in source before setting NOT NULL
UPDATE trading_signals SET source = 'legacy' WHERE source IS NULL;

-- Set source to NOT NULL
ALTER TABLE trading_signals ALTER COLUMN source SET NOT NULL;

-- =============================================================================
-- Phase 3: Verification Queries
-- =============================================================================

-- Verify news_articles
SELECT
    'news_articles' as table_name,
    COUNT(*) as total_rows,
    COUNT(created_at) as has_created_at,
    COUNT(source) as has_source,
    COUNT(is_analyzed) as has_is_analyzed
FROM news_articles;

-- Verify trading_signals
SELECT
    'trading_signals' as table_name,
    COUNT(*) as total_rows,
    COUNT(created_at) as has_created_at,
    COUNT(source) as has_source,
    COUNT(metadata) as has_metadata
FROM trading_signals;

-- =============================================================================
-- Rollback (if needed)
-- =============================================================================
/*
-- news_articles rollback
ALTER TABLE news_articles DROP COLUMN IF EXISTS created_at;
ALTER TABLE news_articles DROP COLUMN IF EXISTS is_analyzed;
ALTER TABLE news_articles DROP COLUMN IF EXISTS published_date;
ALTER TABLE news_articles DROP COLUMN IF EXISTS sentiment_label;
ALTER TABLE news_articles ALTER COLUMN source DROP NOT NULL;
ALTER TABLE news_articles ALTER COLUMN url DROP NOT NULL;

-- trading_signals rollback
ALTER TABLE trading_signals DROP COLUMN IF EXISTS created_at;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS executed_at;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS metadata;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS exit_price;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS outcome_recorded_at;
ALTER TABLE trading_signals DROP COLUMN IF EXISTS generated_at;
ALTER TABLE trading_signals ALTER COLUMN source DROP NOT NULL;
*/