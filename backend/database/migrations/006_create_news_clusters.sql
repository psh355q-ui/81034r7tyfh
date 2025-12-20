-- Migration: 006_create_news_clusters.sql
-- Description: Create tables for 4-Signal Consensus Framework (Phase 18)
-- Date: 2025-12-19
-- Author: AI Trading System Team

-- =============================================================================
-- News Clusters Table
-- =============================================================================
-- Stores clustered news articles with 4-Signal scores and verdicts

CREATE TABLE IF NOT EXISTS news_clusters (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(32) UNIQUE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    theme VARCHAR(200),

    -- Timestamps
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 4-Signal Scores
    di_score FLOAT DEFAULT 0.5,              -- Diversity Integrity (0-1)
    tn_score FLOAT DEFAULT 0.0,              -- Temporal Naturalness (-1 to +1)
    ni_score FLOAT DEFAULT 0.5,              -- Narrative Independence (0-1)
    el_matched BOOLEAN DEFAULT FALSE,        -- Event Legitimacy (matched)
    el_confidence FLOAT DEFAULT 0.0,         -- Event Legitimacy confidence (0-1)
    el_event_name VARCHAR(200),              -- Matched event name

    -- Verdict Classification
    verdict VARCHAR(30) DEFAULT 'PENDING',   -- EMBARGO_EVENT, ORGANIC_CONSENSUS, MANIPULATION_ATTACK, etc.
    verdict_reason TEXT,                     -- Explanation of verdict
    confidence_multiplier FLOAT DEFAULT 1.0, -- Applied to trading signals (0.0-2.0)

    -- Cooling Period (quarantine for suspicious news)
    cooling_intensity FLOAT DEFAULT 0.0,     -- 0 = no cooling, 1 = full block
    cooling_until TIMESTAMPTZ,               -- When cooling expires

    -- Metrics
    article_count INT DEFAULT 0,             -- Number of articles in cluster
    nfpi_score FLOAT,                        -- News Fraud Probability Index (0-100)

    -- Indexing
    CONSTRAINT valid_di_score CHECK (di_score >= 0 AND di_score <= 1),
    CONSTRAINT valid_tn_score CHECK (tn_score >= -1 AND tn_score <= 1),
    CONSTRAINT valid_ni_score CHECK (ni_score >= 0 AND ni_score <= 1),
    CONSTRAINT valid_el_confidence CHECK (el_confidence >= 0 AND el_confidence <= 1),
    CONSTRAINT valid_cooling CHECK (cooling_intensity >= 0 AND cooling_intensity <= 1)
);

-- Indexes for performance
CREATE INDEX idx_news_clusters_ticker ON news_clusters(ticker);
CREATE INDEX idx_news_clusters_last_seen ON news_clusters(last_seen);
CREATE INDEX idx_news_clusters_verdict ON news_clusters(verdict);
CREATE INDEX idx_news_clusters_fingerprint ON news_clusters(fingerprint);
CREATE INDEX idx_news_clusters_cooling ON news_clusters(cooling_until) WHERE cooling_until IS NOT NULL;

-- =============================================================================
-- Cluster Articles Table
-- =============================================================================
-- Individual articles within each cluster (for detailed analysis)

CREATE TABLE IF NOT EXISTS cluster_articles (
    id SERIAL PRIMARY KEY,
    cluster_id INT NOT NULL REFERENCES news_clusters(id) ON DELETE CASCADE,

    -- Article metadata
    article_id VARCHAR(100) UNIQUE NOT NULL,  -- External article ID
    ticker VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,

    -- Source information
    source VARCHAR(200) NOT NULL,
    source_tier VARCHAR(20),                   -- MAJOR, MINOR, SOCIAL, UNKNOWN

    -- Timestamps
    published_at TIMESTAMPTZ NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),

    -- Sentiment (optional)
    sentiment FLOAT,                           -- -1 to +1

    CONSTRAINT valid_sentiment CHECK (sentiment >= -1 AND sentiment <= 1)
);

-- Indexes
CREATE INDEX idx_cluster_articles_cluster_id ON cluster_articles(cluster_id);
CREATE INDEX idx_cluster_articles_ticker ON cluster_articles(ticker);
CREATE INDEX idx_cluster_articles_published ON cluster_articles(published_at);
CREATE INDEX idx_cluster_articles_source ON cluster_articles(source);

-- =============================================================================
-- Economic Calendar Table (for Event Legitimacy detection)
-- =============================================================================
-- Scheduled events (earnings, FOMC, economic data releases)

CREATE TABLE IF NOT EXISTS economic_calendar (
    id SERIAL PRIMARY KEY,

    -- Event details
    event_type VARCHAR(50) NOT NULL,           -- EARNINGS, FOMC, CPI, NFP, etc.
    event_name VARCHAR(200) NOT NULL,
    ticker VARCHAR(20),                        -- NULL for macro events

    -- Timing
    scheduled_time TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(50) DEFAULT 'America/New_York',

    -- Metadata
    importance VARCHAR(20),                    -- HIGH, MEDIUM, LOW
    description TEXT,
    source VARCHAR(100),                       -- Where this event was sourced from

    -- Status
    is_confirmed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_economic_calendar_time ON economic_calendar(scheduled_time);
CREATE INDEX idx_economic_calendar_ticker ON economic_calendar(ticker);
CREATE INDEX idx_economic_calendar_type ON economic_calendar(event_type);

-- =============================================================================
-- Cluster Signal History Table (for analysis and debugging)
-- =============================================================================
-- Tracks how signals changed over time as articles were added

CREATE TABLE IF NOT EXISTS cluster_signal_history (
    id SERIAL PRIMARY KEY,
    cluster_id INT NOT NULL REFERENCES news_clusters(id) ON DELETE CASCADE,

    -- Snapshot of signals at this point in time
    article_count INT NOT NULL,
    di_score FLOAT NOT NULL,
    tn_score FLOAT NOT NULL,
    ni_score FLOAT NOT NULL,
    el_matched BOOLEAN NOT NULL,
    el_confidence FLOAT NOT NULL,
    verdict VARCHAR(30) NOT NULL,
    confidence_multiplier FLOAT NOT NULL,
    nfpi_score FLOAT,

    -- When this snapshot was taken
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX idx_signal_history_cluster ON cluster_signal_history(cluster_id);

-- =============================================================================
-- Views for Easy Querying
-- =============================================================================

-- Active clusters (within last 24 hours)
CREATE OR REPLACE VIEW active_news_clusters AS
SELECT
    nc.*,
    COUNT(ca.id) as actual_article_count
FROM news_clusters nc
LEFT JOIN cluster_articles ca ON nc.id = ca.cluster_id
WHERE nc.last_seen >= NOW() - INTERVAL '24 hours'
  AND nc.article_count >= 2
GROUP BY nc.id;

-- Suspicious clusters (manipulation or burst)
CREATE OR REPLACE VIEW suspicious_clusters AS
SELECT
    nc.*,
    COUNT(ca.id) as actual_article_count
FROM news_clusters nc
LEFT JOIN cluster_articles ca ON nc.id = ca.cluster_id
WHERE nc.verdict IN ('MANIPULATION_ATTACK', 'SUSPICIOUS_BURST')
  AND (nc.cooling_until IS NULL OR nc.cooling_until > NOW())
GROUP BY nc.id
ORDER BY nc.last_seen DESC;

-- High confidence clusters (for trading signals)
CREATE OR REPLACE VIEW high_confidence_clusters AS
SELECT
    nc.*,
    COUNT(ca.id) as actual_article_count
FROM news_clusters nc
LEFT JOIN cluster_articles ca ON nc.id = ca.cluster_id
WHERE nc.verdict IN ('EMBARGO_EVENT', 'ORGANIC_CONSENSUS')
  AND nc.confidence_multiplier >= 1.0
  AND nc.last_seen >= NOW() - INTERVAL '6 hours'
GROUP BY nc.id
ORDER BY nc.confidence_multiplier DESC, nc.last_seen DESC;

-- =============================================================================
-- Functions
-- =============================================================================

-- Function to update cluster metrics
CREATE OR REPLACE FUNCTION update_cluster_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update article count
    UPDATE news_clusters
    SET article_count = (
        SELECT COUNT(*)
        FROM cluster_articles
        WHERE cluster_id = NEW.cluster_id
    ),
    updated_at = NOW()
    WHERE id = NEW.cluster_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update metrics when articles are added
CREATE TRIGGER trigger_update_cluster_metrics
AFTER INSERT ON cluster_articles
FOR EACH ROW
EXECUTE FUNCTION update_cluster_metrics();

-- Function to clean up old clusters
CREATE OR REPLACE FUNCTION cleanup_old_clusters(days_old INT DEFAULT 7)
RETURNS INT AS $$
DECLARE
    deleted_count INT;
BEGIN
    -- Delete clusters older than N days
    WITH deleted AS (
        DELETE FROM news_clusters
        WHERE last_seen < NOW() - (days_old || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Sample Data (for testing)
-- =============================================================================

-- Insert sample economic calendar events
INSERT INTO economic_calendar (event_type, event_name, ticker, scheduled_time, importance, description) VALUES
('EARNINGS', 'Apple Q4 2024 Earnings', 'AAPL', '2024-10-31 16:00:00-04', 'HIGH', 'Apple quarterly earnings report'),
('FOMC', 'Federal Reserve FOMC Meeting Decision', NULL, '2024-11-07 14:00:00-05', 'HIGH', 'Federal Reserve interest rate decision'),
('CPI', 'Consumer Price Index (CPI) Release', NULL, '2024-11-13 08:30:00-05', 'HIGH', 'Monthly inflation data'),
('NFP', 'Non-Farm Payrolls Report', NULL, '2024-12-06 08:30:00-05', 'HIGH', 'Monthly jobs report');

-- =============================================================================
-- Permissions
-- =============================================================================

-- Grant permissions to app user (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON news_clusters TO kis_trading_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON cluster_articles TO kis_trading_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON economic_calendar TO kis_trading_user;
GRANT SELECT, INSERT ON cluster_signal_history TO kis_trading_user;

GRANT USAGE, SELECT ON SEQUENCE news_clusters_id_seq TO kis_trading_user;
GRANT USAGE, SELECT ON SEQUENCE cluster_articles_id_seq TO kis_trading_user;
GRANT USAGE, SELECT ON SEQUENCE economic_calendar_id_seq TO kis_trading_user;
GRANT USAGE, SELECT ON SEQUENCE cluster_signal_history_id_seq TO kis_trading_user;

-- =============================================================================
-- Migration Complete
-- =============================================================================

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 006_create_news_clusters.sql completed successfully';
    RAISE NOTICE 'Tables created: news_clusters, cluster_articles, economic_calendar, cluster_signal_history';
    RAISE NOTICE 'Views created: active_news_clusters, suspicious_clusters, high_confidence_clusters';
END $$;
