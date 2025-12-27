-- Database Schema Sync Migration
-- Date: 2025-12-27
-- Purpose: Add missing columns to match SQLAlchemy models

BEGIN;

-- =============================================================================
-- Phase 1: news_articles - Add missing columns from model
-- =============================================================================

-- Based on models.py NewsArticle class
-- Missing columns identified by schema comparison

ALTER TABLE news_articles
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Note: Other columns from schema comparison are already present
-- The validation script showed ARRAY type notation differences but columns exist

-- =============================================================================
-- Phase 2: trading_signals - Add missing columns from model
-- =============================================================================

-- Based on models.py TradingSignal class
-- These columns exist in model but not in DB

ALTER TABLE trading_signals
ADD COLUMN IF NOT EXISTS news_title VARCHAR(500),
ADD COLUMN IF NOT EXISTS news_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS analysis_theme VARCHAR(200);

-- Fix nullable constraints to match model
ALTER TABLE trading_signals
ALTER COLUMN signal_type
SET NOT NULL,
ALTER COLUMN confidence
SET NOT NULL,
ALTER COLUMN reasoning
SET NOT NULL;

-- Set defaults for existing NULL values before adding constraints
UPDATE trading_signals
SET
    signal_type = 'manual'
WHERE
    signal_type IS NULL;

UPDATE trading_signals
SET
    confidence = 50.0
WHERE
    confidence IS NULL;

UPDATE trading_signals
SET
    reasoning = 'No reasoning provided'
WHERE
    reasoning IS NULL;

-- =============================================================================
-- Phase 3: Verification
-- =============================================================================

-- Count columns
SELECT 'news_articles' as table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE
    table_name = 'news_articles';

SELECT 'trading_signals' as table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE
    table_name = 'trading_signals';

COMMIT;

-- =============================================================================
-- Rollback script (if needed)
-- =============================================================================
/*
BEGIN;

ALTER TABLE news_articles DROP COLUMN IF EXISTS created_at;

ALTER TABLE trading_signals 
DROP COLUMN IF EXISTS news_title,
DROP COLUMN IF EXISTS news_source,
DROP COLUMN IF EXISTS analysis_theme;

ALTER TABLE trading_signals
ALTER COLUMN signal_type DROP NOT NULL,
ALTER COLUMN confidence DROP NOT NULL,
ALTER COLUMN reasoning DROP NOT NULL;

COMMIT;
*/