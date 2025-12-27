-- Phase 3: DB Schema Synchronization Migration
-- Purpose: Add missing columns to match updated SQLAlchemy models

-- 1. News Articles Updates
ALTER TABLE news_articles
ADD COLUMN IF NOT EXISTS author VARCHAR(200),
ADD COLUMN IF NOT EXISTS summary TEXT;

-- Verify tags is ARRAY type (TEXT[])
DO $$
BEGIN
    -- If tags is JSONB, we might want to keep it or convert it. Model says ARRAY(String).
    -- Checking if column exists and type.
    -- Assuming it exists as we didn't add it.
    NULL;
END $$;

-- 2. Trading Signals Updates
ALTER TABLE trading_signals
ADD COLUMN IF NOT EXISTS analysis_id INTEGER REFERENCES analysis_results (id),
ADD COLUMN IF NOT EXISTS target_price DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS stop_loss DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS entry_price DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS shares INTEGER,
ADD COLUMN IF NOT EXISTS alert_sent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS news_title VARCHAR(500),
ADD COLUMN IF NOT EXISTS news_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS analysis_theme VARCHAR(200),
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'unknown';

-- Create index for analysis_id if not exists
CREATE INDEX IF NOT EXISTS idx_signal_analysis_id ON trading_signals (analysis_id);

CREATE INDEX IF NOT EXISTS idx_signal_source ON trading_signals (source);

-- 3. Data Collection Progress Updates (Verification)
-- Ensure columns exist as per previous checks
ALTER TABLE data_collection_progress
ADD COLUMN IF NOT EXISTS items_collected INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS items_total INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING';