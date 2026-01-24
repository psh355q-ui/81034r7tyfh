-- MacroSnapshots 테이블 생성 마이그레이션
-- 작성일: 2026-01-23

CREATE TABLE IF NOT EXISTS macro_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date TIMESTAMP NOT NULL UNIQUE,
    regime VARCHAR(50),
    fed_stance VARCHAR(50),
    vix_level FLOAT,
    vix_category VARCHAR(20),
    market_sentiment VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_macro_snapshot_date ON macro_snapshots(snapshot_date);

-- 테이블 설명 추가
COMMENT ON TABLE macro_snapshots IS '거시경제 스냅샷';
COMMENT ON COLUMN macro_snapshots.regime IS '시장 레짐 (GOLDILOCKS, STAGFLATION, RECOVERY, etc.)';
COMMENT ON COLUMN macro_snapshots.fed_stance IS 'Fed 스탠스 (HAWKISH, DOVISH, NEUTRAL)';
COMMENT ON COLUMN macro_snapshots.vix_level IS 'VIX 지수';
COMMENT ON COLUMN macro_snapshots.vix_category IS 'VIX 카테고리 (LOW, NORMAL, ELEVATED, HIGH)';
COMMENT ON COLUMN macro_snapshots.market_sentiment IS '시장 심리 (RISK_ON, RISK_OFF, NEUTRAL)';
