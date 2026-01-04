-- Migration for table: shadow_trading_positions
-- Generated: 2026-01-03 14:56:57
-- Description: Shadow Trading 포지션/거래 내역 (실제 돈 없이 가상 트레이딩)

-- ====================================
-- Create Table
-- ====================================

CREATE TABLE IF NOT EXISTS shadow_trading_positions (
    id SERIAL NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    trade_id VARCHAR(150) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(15,4) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    exit_price NUMERIC(15,4),
    exit_date TIMESTAMP,
    pnl NUMERIC(15,2),
    pnl_pct NUMERIC(10,4),
    stop_loss_price NUMERIC(15,4) NOT NULL,
    reason VARCHAR(200),
    agent_decision TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- ====================================
-- Create Indexes
-- ====================================

CREATE INDEX IF NOT EXISTS idx_shadow_positions_session_id ON shadow_trading_positions(session_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_shadow_positions_trade_id ON shadow_trading_positions(trade_id);
CREATE INDEX IF NOT EXISTS idx_shadow_positions_symbol ON shadow_trading_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_shadow_positions_entry_date ON shadow_trading_positions(entry_date);
CREATE INDEX IF NOT EXISTS idx_shadow_positions_exit_date ON shadow_trading_positions(exit_date);

-- ====================================
-- Column Comments
-- ====================================

COMMENT ON COLUMN shadow_trading_positions.id IS 'Primary Key';
COMMENT ON COLUMN shadow_trading_positions.session_id IS '세션 ID (foreign key to shadow_trading_sessions)';
COMMENT ON COLUMN shadow_trading_positions.trade_id IS '거래 고유 ID';
COMMENT ON COLUMN shadow_trading_positions.symbol IS '종목 심볼';
COMMENT ON COLUMN shadow_trading_positions.action IS '거래 행위 (buy/sell)';
COMMENT ON COLUMN shadow_trading_positions.quantity IS '수량';
COMMENT ON COLUMN shadow_trading_positions.entry_price IS '진입 가격';
COMMENT ON COLUMN shadow_trading_positions.entry_date IS '진입 일시';
COMMENT ON COLUMN shadow_trading_positions.exit_price IS '청산 가격';
COMMENT ON COLUMN shadow_trading_positions.exit_date IS '청산 일시';
COMMENT ON COLUMN shadow_trading_positions.pnl IS '손익 ($)';
COMMENT ON COLUMN shadow_trading_positions.pnl_pct IS '손익률 (0.0-1.0)';
COMMENT ON COLUMN shadow_trading_positions.stop_loss_price IS 'Stop Loss 가격';
COMMENT ON COLUMN shadow_trading_positions.reason IS '거래 이유';
COMMENT ON COLUMN shadow_trading_positions.agent_decision IS 'Agent 결정 상세 (JSON string)';
COMMENT ON COLUMN shadow_trading_positions.created_at IS '생성 시각';

-- Migration complete for shadow_trading_positions
