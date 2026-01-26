-- ====================================
-- Persona-based Trading Migration Script
-- Phase 3: Persona-based Trading
-- Date: 2026-01-25
-- ====================================
-- 
-- This migration creates the database tables and initial data for the Persona-based Trading system.
--
-- Tables:
--   - personas: Persona definitions (CONSERVATIVE, AGGRESSIVE, GROWTH, BALANCED)
--   - portfolio_allocations: Portfolio allocation tracking per persona
--   - user_persona_preferences: User persona preferences
--
-- ====================================

-- ====================================
-- Table: personas
-- ====================================
CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Investment characteristics
    risk_tolerance VARCHAR(20) NOT NULL CHECK (risk_tolerance IN ('VERY_LOW', 'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH')),
    investment_horizon VARCHAR(20) NOT NULL CHECK (investment_horizon IN ('SHORT', 'MEDIUM', 'LONG')),
    return_expectation VARCHAR(20) NOT NULL CHECK (return_expectation IN ('LOW', 'MODERATE', 'HIGH', 'VERY_HIGH')),
    
    -- Agent weights (War Room MVP)
    trader_weight NUMERIC(4, 3) NOT NULL CHECK (trader_weight >= 0 AND trader_weight <= 1),
    risk_weight NUMERIC(4, 3) NOT NULL CHECK (risk_weight >= 0 AND risk_weight <= 1),
    analyst_weight NUMERIC(4, 3) NOT NULL CHECK (analyst_weight >= 0 AND analyst_weight <= 1),
    
    -- Asset allocation ratios (default)
    stock_allocation NUMERIC(5, 4) NOT NULL DEFAULT 0.60 CHECK (stock_allocation >= 0 AND stock_allocation <= 1),
    bond_allocation NUMERIC(5, 4) NOT NULL DEFAULT 0.30 CHECK (bond_allocation >= 0 AND bond_allocation <= 1),
    cash_allocation NUMERIC(5, 4) NOT NULL DEFAULT 0.10 CHECK (cash_allocation >= 0 AND cash_allocation <= 1),
    
    -- Risk management settings
    max_position_size NUMERIC(5, 4) NOT NULL DEFAULT 0.10 CHECK (max_position_size >= 0 AND max_position_size <= 1),
    max_sector_exposure NUMERIC(5, 4) NOT NULL DEFAULT 0.30 CHECK (max_sector_exposure >= 0 AND max_sector_exposure <= 1),
    stop_loss_pct NUMERIC(5, 4) NOT NULL DEFAULT 0.05 CHECK (stop_loss_pct >= 0 AND stop_loss_pct <= 1),
    
    -- Leverage settings
    leverage_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    max_leverage_pct NUMERIC(5, 4) NOT NULL DEFAULT 0.0 CHECK (max_leverage_pct >= 0 AND max_leverage_pct <= 1),
    
    -- Feature activation
    yield_trap_detector BOOLEAN NOT NULL DEFAULT FALSE,
    dividend_calendar BOOLEAN NOT NULL DEFAULT FALSE,
    noise_filter BOOLEAN NOT NULL DEFAULT FALSE,
    thesis_violation BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Hard Rules
    max_agent_disagreement NUMERIC(4, 3) NOT NULL DEFAULT 0.67 CHECK (max_agent_disagreement >= 0 AND max_agent_disagreement <= 1),
    min_avg_confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.50 CHECK (min_avg_confidence >= 0 AND min_avg_confidence <= 1),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for personas table
CREATE INDEX idx_personas_name ON personas(name);
CREATE INDEX idx_personas_active ON personas(is_active);
CREATE INDEX idx_personas_default ON personas(is_default);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_personas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_personas_updated_at
    BEFORE UPDATE ON personas
    FOR EACH ROW
    EXECUTE FUNCTION update_personas_updated_at();


-- ====================================
-- Table: portfolio_allocations
-- ====================================
CREATE TABLE IF NOT EXISTS portfolio_allocations (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    
    -- Allocation info
    asset_class VARCHAR(20) NOT NULL CHECK (asset_class IN ('STOCK', 'BOND', 'CASH', 'CRYPTO', 'COMMODITY', 'ETF', 'REIT')),
    target_allocation NUMERIC(5, 4) NOT NULL CHECK (target_allocation >= 0 AND target_allocation <= 1),
    current_allocation NUMERIC(5, 4) CHECK (current_allocation >= 0 AND current_allocation <= 1),
    deviation NUMERIC(5, 4) CHECK (deviation >= 0),
    
    -- Rebalancing settings
    rebalance_threshold NUMERIC(5, 4) NOT NULL DEFAULT 0.05 CHECK (rebalance_threshold >= 0 AND rebalance_threshold <= 1),
    last_rebalanced TIMESTAMP,
    next_rebalance_date TIMESTAMP,
    
    -- Metadata
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for portfolio_allocations table
CREATE INDEX idx_allocations_persona ON portfolio_allocations(persona_id);
CREATE INDEX idx_allocations_asset_class ON portfolio_allocations(asset_class);
CREATE INDEX idx_allocations_rebalance ON portfolio_allocations(next_rebalance_date);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_portfolio_allocations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_portfolio_allocations_updated_at
    BEFORE UPDATE ON portfolio_allocations
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolio_allocations_updated_at();


-- ====================================
-- Table: user_persona_preferences
-- ====================================
CREATE TABLE IF NOT EXISTS user_persona_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL UNIQUE,
    persona_id INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    
    -- Personalized settings (override default persona settings)
    custom_weights JSONB,
    custom_allocations JSONB,
    custom_risk_settings JSONB,
    
    -- Activity tracking
    last_switched_at TIMESTAMP,
    switch_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for user_persona_preferences table
CREATE INDEX idx_user_persona_user ON user_persona_preferences(user_id);
CREATE INDEX idx_user_persona_persona ON user_persona_preferences(persona_id);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_user_persona_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_persona_preferences_updated_at
    BEFORE UPDATE ON user_persona_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_persona_preferences_updated_at();


-- ====================================
-- Initial Data: Personas
-- ====================================

-- CONSERVATIVE (보수형) - 안정성 우선, 배당/채권 중심
INSERT INTO personas (
    name, display_name, description,
    risk_tolerance, investment_horizon, return_expectation,
    trader_weight, risk_weight, analyst_weight,
    stock_allocation, bond_allocation, cash_allocation,
    max_position_size, max_sector_exposure, stop_loss_pct,
    leverage_allowed, max_leverage_pct,
    yield_trap_detector, dividend_calendar, noise_filter, thesis_violation,
    max_agent_disagreement, min_avg_confidence,
    is_active, is_default
) VALUES (
    'CONSERVATIVE', '보수형', '배당/안정 추구: 현금흐름 최적화, Yield Trap 방지',
    'LOW', 'LONG', 'MODERATE',
    0.10, 0.40, 0.50,
    0.50, 0.40, 0.10,
    0.08, 0.25, 0.03,
    FALSE, 0.0,
    TRUE, TRUE, TRUE, FALSE,
    0.40, 0.60,
    TRUE, FALSE
);

-- AGGRESSIVE (공격형) - 고수익 추구, 성장주/레버리지 허용
INSERT INTO personas (
    name, display_name, description,
    risk_tolerance, investment_horizon, return_expectation,
    trader_weight, risk_weight, analyst_weight,
    stock_allocation, bond_allocation, cash_allocation,
    max_position_size, max_sector_exposure, stop_loss_pct,
    leverage_allowed, max_leverage_pct,
    yield_trap_detector, dividend_calendar, noise_filter, thesis_violation,
    max_agent_disagreement, min_avg_confidence,
    is_active, is_default
) VALUES (
    'AGGRESSIVE', '공격형', '공격적 투자: 레버리지 허용 (10% 제한), FOMO 제어',
    'VERY_HIGH', 'SHORT', 'VERY_HIGH',
    0.50, 0.30, 0.20,
    0.80, 0.10, 0.10,
    0.15, 0.40, 0.08,
    TRUE, 0.10,
    FALSE, FALSE, FALSE, FALSE,
    0.80, 0.45,
    TRUE, FALSE
);

-- GROWTH (성장형) - 가치/성장 추구, 펀더멘털 중심
INSERT INTO personas (
    name, display_name, description,
    risk_tolerance, investment_horizon, return_expectation,
    trader_weight, risk_weight, analyst_weight,
    stock_allocation, bond_allocation, cash_allocation,
    max_position_size, max_sector_exposure, stop_loss_pct,
    leverage_allowed, max_leverage_pct,
    yield_trap_detector, dividend_calendar, noise_filter, thesis_violation,
    max_agent_disagreement, min_avg_confidence,
    is_active, is_default
) VALUES (
    'GROWTH', '성장형', '가치/성장 투자: 펀더멘털 중심, 노이즈 필터링',
    'HIGH', 'LONG', 'HIGH',
    0.15, 0.25, 0.60,
    0.70, 0.20, 0.10,
    0.12, 0.35, 0.05,
    FALSE, 0.0,
    FALSE, FALSE, TRUE, TRUE,
    0.50, 0.55,
    TRUE, FALSE
);

-- BALANCED (밸런스형) - 균형 잡힌 포트폴리오, 기본값
INSERT INTO personas (
    name, display_name, description,
    risk_tolerance, investment_horizon, return_expectation,
    trader_weight, risk_weight, analyst_weight,
    stock_allocation, bond_allocation, cash_allocation,
    max_position_size, max_sector_exposure, stop_loss_pct,
    leverage_allowed, max_leverage_pct,
    yield_trap_detector, dividend_calendar, noise_filter, thesis_violation,
    max_agent_disagreement, min_avg_confidence,
    is_active, is_default
) VALUES (
    'BALANCED', '밸런스형', '단기 트레이딩: 모멘텀/뉴스 기반 빠른 의사결정',
    'MEDIUM', 'MEDIUM', 'MODERATE',
    0.35, 0.35, 0.30,
    0.60, 0.30, 0.10,
    0.10, 0.30, 0.05,
    FALSE, 0.0,
    FALSE, FALSE, FALSE, FALSE,
    0.67, 0.50,
    TRUE, TRUE
);


-- ====================================
-- Initial Data: Portfolio Allocations
-- ====================================

-- CONSERVATIVE allocations
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'STOCK', 0.50, 0.05 FROM personas WHERE name = 'CONSERVATIVE';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'BOND', 0.40, 0.05 FROM personas WHERE name = 'CONSERVATIVE';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'CASH', 0.10, 0.05 FROM personas WHERE name = 'CONSERVATIVE';

-- AGGRESSIVE allocations
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'STOCK', 0.80, 0.05 FROM personas WHERE name = 'AGGRESSIVE';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'BOND', 0.10, 0.05 FROM personas WHERE name = 'AGGRESSIVE';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'CASH', 0.10, 0.05 FROM personas WHERE name = 'AGGRESSIVE';

-- GROWTH allocations
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'STOCK', 0.70, 0.05 FROM personas WHERE name = 'GROWTH';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'BOND', 0.20, 0.05 FROM personas WHERE name = 'GROWTH';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'CASH', 0.10, 0.05 FROM personas WHERE name = 'GROWTH';

-- BALANCED allocations
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'STOCK', 0.60, 0.05 FROM personas WHERE name = 'BALANCED';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'BOND', 0.30, 0.05 FROM personas WHERE name = 'BALANCED';
INSERT INTO portfolio_allocations (persona_id, asset_class, target_allocation, rebalance_threshold)
SELECT id, 'CASH', 0.10, 0.05 FROM personas WHERE name = 'BALANCED';


-- ====================================
-- Migration Complete
-- ====================================

-- Log migration completion
INSERT INTO data_collection_progress (
    task_name, source, collection_type, status,
    progress_pct, items_processed, items_total,
    started_at, completed_at, job_metadata
) VALUES (
    'Persona Tables Migration', 'persona_migration', 'schema', 'completed',
    100.0, 3, 3,
    NOW(), NOW(),
    '{"migration_version": "1.0", "migration_date": "2026-01-25", "tables_created": ["personas", "portfolio_allocations", "user_persona_preferences"]}'::jsonb
) ON CONFLICT DO NOTHING;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Persona-based Trading Migration Complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: personas, portfolio_allocations, user_persona_preferences';
    RAISE NOTICE 'Initial personas: CONSERVATIVE, AGGRESSIVE, GROWTH, BALANCED';
    RAISE NOTICE 'Default persona: BALANCED';
    RAISE NOTICE '========================================';
END $$;
