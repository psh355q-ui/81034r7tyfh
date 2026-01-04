-- Migration for table: agent_weights_history
-- Generated: 2026-01-03 16:06:38
-- Description: Agent 가중치 조정 이력 (Failure Learning)

-- ====================================
-- Create Table
-- ====================================

CREATE TABLE IF NOT EXISTS agent_weights_history (
    id SERIAL NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    trader_agent NUMERIC(5,4) NOT NULL,
    risk_agent NUMERIC(5,4) NOT NULL,
    analyst_agent NUMERIC(5,4) NOT NULL,
    macro_agent NUMERIC(5,4) NOT NULL,
    institutional_agent NUMERIC(5,4) NOT NULL,
    news_agent NUMERIC(5,4) NOT NULL,
    chip_war_agent NUMERIC(5,4) NOT NULL,
    dividend_risk_agent NUMERIC(5,4) NOT NULL,
    pm_agent NUMERIC(5,4) NOT NULL
);

-- ====================================
-- Create Indexes
-- ====================================

CREATE INDEX IF NOT EXISTS idx_agent_weights_changed_at ON agent_weights_history(changed_at DESC);

-- ====================================
-- Column Comments
-- ====================================

COMMENT ON COLUMN agent_weights_history.id IS 'Primary key';
COMMENT ON COLUMN agent_weights_history.changed_at IS '가중치 변경 시각';
COMMENT ON COLUMN agent_weights_history.changed_by IS '변경 주체 (system/manual/scheduler)';
COMMENT ON COLUMN agent_weights_history.reason IS '변경 사유';
COMMENT ON COLUMN agent_weights_history.trader_agent IS 'Trader Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.risk_agent IS 'Risk Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.analyst_agent IS 'Analyst Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.macro_agent IS 'Macro Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.institutional_agent IS 'Institutional Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.news_agent IS 'News Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.chip_war_agent IS 'ChipWar Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.dividend_risk_agent IS 'Dividend Risk Agent 가중치 (0.0000-1.0000)';
COMMENT ON COLUMN agent_weights_history.pm_agent IS 'PM Agent 가중치 (0.0000-1.0000)';

-- Migration complete for agent_weights_history
