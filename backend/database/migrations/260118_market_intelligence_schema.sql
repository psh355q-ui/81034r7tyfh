-- ====================================
-- Market Intelligence v2.0 Schema Extension
-- Migration: 260118_market_intelligence_schema
-- Date: 2026-01-18
-- Reference: docs/planning/260118_market_intelligence_roadmap.md
-- ====================================
--
-- This migration adds tables and columns for the Market Intelligence v2.0 system
-- based on AI trio (Claude, ChatGPT, Gemini) discussions.
--
-- Changes:
-- 1. Extend news_articles table with narrative/fact/market confirmation fields
-- 2. Create 9 new tables for intelligence components
--
-- ====================================

-- ====================================
-- 1. EXTEND news_articles TABLE
-- ====================================

-- Narrative tracking (ChatGPT P0)
ALTER TABLE news_articles
    ADD COLUMN IF NOT EXISTS narrative_phase VARCHAR(20),
    ADD COLUMN IF NOT EXISTS narrative_strength FLOAT,
    ADD COLUMN IF NOT EXISTS narrative_consensus FLOAT;

COMMENT ON COLUMN news_articles.narrative_phase IS 'Narrative phase: EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING';
COMMENT ON COLUMN news_articles.narrative_strength IS 'Narrative strength: 0.0 ~ 1.0';
COMMENT ON COLUMN news_articles.narrative_consensus IS 'Narrative consensus: 0.0 ~ 1.0';

-- Fact verification (Gemini P0)
ALTER TABLE news_articles
    ADD COLUMN IF NOT EXISTS fact_verification_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS fact_confidence_adjustment FLOAT DEFAULT 0.0;

COMMENT ON COLUMN news_articles.fact_verification_status IS 'Fact verification status: VERIFIED, PARTIAL, MISMATCH, UNVERIFIED';
COMMENT ON COLUMN news_articles.fact_confidence_adjustment IS 'Confidence adjustment: -0.2 ~ +0.1';

-- Market confirmation (ChatGPT P0)
ALTER TABLE news_articles
    ADD COLUMN IF NOT EXISTS price_correlation_score FLOAT,
    ADD COLUMN IF NOT EXISTS confirmation_status VARCHAR(20);

COMMENT ON COLUMN news_articles.price_correlation_score IS 'Price correlation score: -1.0 ~ 1.0';
COMMENT ON COLUMN news_articles.confirmation_status IS 'Market confirmation status: CONFIRMED, DIVERGENT, LEADING, NOISE';

-- Enhanced tagging
ALTER TABLE news_articles
    ADD COLUMN IF NOT EXISTS narrative_tags TEXT[],
    ADD COLUMN IF NOT EXISTS horizon_tags TEXT[];

COMMENT ON COLUMN news_articles.narrative_tags IS 'Fact vs Narrative tags';
COMMENT ON COLUMN news_articles.horizon_tags IS 'Time horizon tags: SHORT, MEDIUM, LONG';

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_news_narrative_phase ON news_articles(narrative_phase) WHERE narrative_phase IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_news_fact_status ON news_articles(fact_verification_status) WHERE fact_verification_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_news_confirmation_status ON news_articles(confirmation_status) WHERE confirmation_status IS NOT NULL;

-- ====================================
-- 2. CREATE NEW TABLES
-- ====================================

-- 2.1 Narrative States (ChatGPT P0)
CREATE TABLE IF NOT EXISTS narrative_states (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(50) NOT NULL,
    fact_layer TEXT,
    narrative_layer TEXT,
    market_expectation TEXT,
    expectation_gap FLOAT,
    phase VARCHAR(20),
    change_velocity FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE narrative_states IS 'Narrative state tracking - separates fact from narrative layer';
COMMENT ON COLUMN narrative_states.phase IS 'Narrative phase: EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING';
COMMENT ON COLUMN narrative_states.expectation_gap IS 'Gap between market expectation and reality';

CREATE INDEX idx_narrative_states_topic ON narrative_states(topic);
CREATE INDEX idx_narrative_states_phase ON narrative_states(phase);
CREATE INDEX idx_narrative_states_created_at ON narrative_states(created_at);

-- 2.2 Market Confirmations (ChatGPT P0)
CREATE TABLE IF NOT EXISTS market_confirmations (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    news_intensity FLOAT,
    price_momentum FLOAT,
    volume_anomaly FLOAT,
    signal VARCHAR(20),
    divergence_score FLOAT,
    proxy_tickers VARCHAR(50)[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE market_confirmations IS 'Market confirmation - cross-verifies news intensity with price action';
COMMENT ON COLUMN market_confirmations.signal IS 'Signal: CONFIRMED, DIVERGENT, LEADING, NOISE';
COMMENT ON COLUMN market_confirmations.divergence_score IS 'Divergence between news and price (-1.0 to 1.0)';

CREATE INDEX idx_market_confirmations_theme ON market_confirmations(theme);
CREATE INDEX idx_market_confirmations_signal ON market_confirmations(signal);
CREATE INDEX idx_market_confirmations_created_at ON market_confirmations(created_at);

-- 2.3 Narrative Fatigue (ChatGPT P1)
CREATE TABLE IF NOT EXISTS narrative_fatigue (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    fatigue_score FLOAT,
    signal VARCHAR(20),
    mention_growth FLOAT,
    price_response FLOAT,
    new_info_ratio FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE narrative_fatigue IS 'Narrative fatigue detection - identifies overheating themes';
COMMENT ON COLUMN narrative_fatigue.fatigue_score IS 'Fatigue score: mention_growth - price_response - new_info_ratio';

CREATE INDEX idx_narrative_fatigue_theme ON narrative_fatigue(theme);
CREATE INDEX idx_narrative_fatigue_signal ON narrative_fatigue(signal);
CREATE INDEX idx_narrative_fatigue_created_at ON narrative_fatigue(created_at);

-- 2.4 Contrary Signals (ChatGPT P1)
CREATE TABLE IF NOT EXISTS contrary_signals (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    crowding_level VARCHAR(20),
    contrarian_signal VARCHAR(30),
    indicators JSONB DEFAULT '{}'::jsonb,
    reasoning TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE contrary_signals IS 'Contrary signal detection - warns against crowded trades';
COMMENT ON COLUMN contrary_signals.crowding_level IS 'Crowding level: LOW, MEDIUM, HIGH, EXTREME';

CREATE INDEX idx_contrary_signals_theme ON contrary_signals(theme);
CREATE INDEX idx_contrary_signals_crowding ON contrary_signals(crowding_level);
CREATE INDEX idx_contrary_signals_created_at ON contrary_signals(created_at);

-- 2.5 Horizon Tags (ChatGPT P1)
CREATE TABLE IF NOT EXISTS horizon_tags (
    id SERIAL PRIMARY KEY,
    news_article_id INTEGER REFERENCES news_articles(id) ON DELETE SET NULL,
    short_term TEXT,
    mid_term TEXT,
    long_term TEXT,
    recommended_horizon VARCHAR(10),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE horizon_tags IS 'Time horizon classification - separates insights by investment horizon';
COMMENT ON COLUMN horizon_tags.recommended_horizon IS 'Recommended horizon: SHORT, MEDIUM, LONG';

CREATE INDEX idx_horizon_tags_article_id ON horizon_tags(news_article_id);
CREATE INDEX idx_horizon_tags_horizon ON horizon_tags(recommended_horizon);
CREATE INDEX idx_horizon_tags_created_at ON horizon_tags(created_at);

-- 2.6 Policy Feasibility (ChatGPT P2)
CREATE TABLE IF NOT EXISTS policy_feasibility (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    feasibility_score FLOAT,
    factors JSONB DEFAULT '{}'::jsonb,
    risks TEXT[],
    reasoning TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE policy_feasibility IS 'Policy feasibility analysis - calculates realization probability';
COMMENT ON COLUMN policy_feasibility.feasibility_score IS 'Feasibility: 0.0 ~ 1.0';

CREATE INDEX idx_policy_feasibility_name ON policy_feasibility(policy_name);
CREATE INDEX idx_policy_feasibility_score ON policy_feasibility(feasibility_score);
CREATE INDEX idx_policy_feasibility_created_at ON policy_feasibility(created_at);

-- 2.7 Insight Reviews (ChatGPT+Gemini P2)
CREATE TABLE IF NOT EXISTS insight_reviews (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER NOT NULL,
    insight_type VARCHAR(50),
    predicted_direction VARCHAR(20),
    actual_outcome_7d FLOAT,
    actual_outcome_30d FLOAT,
    success BOOLEAN,
    accuracy_score FLOAT,
    failure_reason TEXT,
    lesson_learned TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    reviewed_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE insight_reviews IS 'Insight post-mortem - tracks prediction accuracy and learns from mistakes';
COMMENT ON COLUMN insight_reviews.predicted_direction IS 'Predicted direction: UP, DOWN, SIDEWAYS';

CREATE INDEX idx_insight_reviews_insight_id ON insight_reviews(insight_id);
CREATE INDEX idx_insight_reviews_success ON insight_reviews(success);
CREATE INDEX idx_insight_reviews_reviewed_at ON insight_reviews(reviewed_at);

-- 2.8 User Feedback Intelligence (Gemini P2)
CREATE TABLE IF NOT EXISTS user_feedback_intelligence (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER,
    insight_type VARCHAR(50),
    feedback_type VARCHAR(20),
    user_comment TEXT,
    corrected_data JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE user_feedback_intelligence IS 'User feedback for active learning - improves system accuracy';
COMMENT ON COLUMN user_feedback_intelligence.feedback_type IS 'Feedback type: WRONG_THEME, BAD_SUMMARY, GOOD';

CREATE INDEX idx_user_feedback_intelligence_insight_id ON user_feedback_intelligence(insight_id);
CREATE INDEX idx_user_feedback_intelligence_type ON user_feedback_intelligence(feedback_type);
CREATE INDEX idx_user_feedback_intelligence_created_at ON user_feedback_intelligence(created_at);

-- 2.9 Prompt Versions (Gemini P2)
CREATE TABLE IF NOT EXISTS prompt_versions (
    id SERIAL PRIMARY KEY,
    prompt_name VARCHAR(100) NOT NULL,
    version INTEGER DEFAULT 1,
    prompt_text TEXT NOT NULL,
    performance_score FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE prompt_versions IS 'Prompt version management - A/B tests prompts for optimal performance';

CREATE INDEX idx_prompt_versions_name ON prompt_versions(prompt_name);
CREATE INDEX idx_prompt_versions_active ON prompt_versions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_prompt_versions_created_at ON prompt_versions(created_at);

-- 2.10 Generated Charts (Gemini P1)
CREATE TABLE IF NOT EXISTS generated_charts (
    id SERIAL PRIMARY KEY,
    chart_type VARCHAR(50),
    chart_title VARCHAR(255),
    parameters JSONB DEFAULT '{}'::jsonb,
    file_path TEXT,
    thumbnail_path TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE generated_charts IS 'Generated charts log - tracks visualization auto-generation';

CREATE INDEX idx_generated_charts_type ON generated_charts(chart_type);
CREATE INDEX idx_generated_charts_created_at ON generated_charts(created_at);

-- ====================================
-- 3. TRIGGERS FOR UPDATED_AT
-- ====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_narrative_states_updated_at
    BEFORE UPDATE ON narrative_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policy_feasibility_updated_at
    BEFORE UPDATE ON policy_feasibility
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- 4. GRANT PERMISSIONS
-- ====================================

-- Grant permissions to the application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ====================================
-- MIGRATION COMPLETE
-- ====================================

-- Verification query
SELECT
    'Migration 260118_market_intelligence_schema completed' as status,
    COUNT(*) as new_tables_added
FROM information_schema.tables
WHERE table_name IN (
    'narrative_states',
    'market_confirmations',
    'narrative_fatigue',
    'contrary_signals',
    'horizon_tags',
    'policy_feasibility',
    'insight_reviews',
    'user_feedback_intelligence',
    'prompt_versions',
    'generated_charts'
);

-- ====================================
-- ROLLBACK SCRIPT (for manual rollback if needed)
-- ====================================
--
-- DROP TABLE IF EXISTS generated_charts CASCADE;
-- DROP TABLE IF EXISTS prompt_versions CASCADE;
-- DROP TABLE IF EXISTS user_feedback_intelligence CASCADE;
-- DROP TABLE IF EXISTS insight_reviews CASCADE;
-- DROP TABLE IF EXISTS policy_feasibility CASCADE;
-- DROP TABLE IF EXISTS horizon_tags CASCADE;
-- DROP TABLE IF EXISTS contrary_signals CASCADE;
-- DROP TABLE IF EXISTS narrative_fatigue CASCADE;
-- DROP TABLE IF EXISTS market_confirmations CASCADE;
-- DROP TABLE IF EXISTS narrative_states CASCADE;
--
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS narrative_phase;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS narrative_strength;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS narrative_consensus;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS fact_verification_status;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS fact_confidence_adjustment;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS price_correlation_score;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS confirmation_status;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS narrative_tags;
-- ALTER TABLE news_articles DROP COLUMN IF EXISTS horizon_tags;
--
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
