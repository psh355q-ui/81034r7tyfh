-- Migration for table: shadow_trading_sessions
-- Generated: 2026-01-03 14:56:54
-- Description: Shadow Trading 세션 추적 (MVP 검증용 가상 트레이딩)

-- ====================================
-- Create Table
-- ====================================

CREATE TABLE IF NOT EXISTS shadow_trading_sessions (
    id SERIAL NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    initial_capital NUMERIC(15,2) NOT NULL,
    current_capital NUMERIC(15,2) NOT NULL,
    available_cash NUMERIC(15,2) NOT NULL,
    reason VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- ====================================
-- Create Indexes
-- ====================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_shadow_sessions_session_id ON shadow_trading_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_shadow_sessions_status ON shadow_trading_sessions(status);
CREATE INDEX IF NOT EXISTS idx_shadow_sessions_start_date ON shadow_trading_sessions(start_date);

-- ====================================
-- Column Comments
-- ====================================

COMMENT ON COLUMN shadow_trading_sessions.id IS 'Primary Key';
COMMENT ON COLUMN shadow_trading_sessions.session_id IS '세션 고유 ID (shadow_YYYY-MM-DDTHH:MM:SS)';
COMMENT ON COLUMN shadow_trading_sessions.status IS '세션 상태 (active/paused/completed/failed)';
COMMENT ON COLUMN shadow_trading_sessions.start_date IS '시작 일시';
COMMENT ON COLUMN shadow_trading_sessions.end_date IS '종료 일시';
COMMENT ON COLUMN shadow_trading_sessions.initial_capital IS '초기 자본금';
COMMENT ON COLUMN shadow_trading_sessions.current_capital IS '현재 자본금';
COMMENT ON COLUMN shadow_trading_sessions.available_cash IS '가용 현금';
COMMENT ON COLUMN shadow_trading_sessions.reason IS '세션 시작 이유';
COMMENT ON COLUMN shadow_trading_sessions.created_at IS '생성 시각';
COMMENT ON COLUMN shadow_trading_sessions.updated_at IS '수정 시각';

-- Migration complete for shadow_trading_sessions
