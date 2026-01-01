-- Migration for table: deep_reasoning_analyses
-- Generated: 2026-01-01 21:00:24
-- Description: Deep Reasoning 분석 이력 저장 (3-Step CoT 추론 결과)

-- ====================================
-- Create Table
-- ====================================

CREATE TABLE IF NOT EXISTS deep_reasoning_analyses (
    id SERIAL NOT NULL,
    news_text TEXT NOT NULL,
    theme VARCHAR(500) NOT NULL,
    primary_beneficiary_ticker VARCHAR(20),
    primary_beneficiary_action VARCHAR(10),
    primary_beneficiary_confidence FLOAT,
    primary_beneficiary_reasoning TEXT,
    hidden_beneficiary_ticker VARCHAR(20),
    hidden_beneficiary_action VARCHAR(10),
    hidden_beneficiary_confidence FLOAT,
    hidden_beneficiary_reasoning TEXT,
    loser_ticker VARCHAR(20),
    loser_action VARCHAR(10),
    loser_confidence FLOAT,
    loser_reasoning TEXT,
    bull_case TEXT NOT NULL,
    bear_case TEXT NOT NULL,
    reasoning_trace JSONB NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- ====================================
-- Create Indexes
-- ====================================

CREATE INDEX IF NOT EXISTS idx_deep_reasoning_created_at ON deep_reasoning_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_deep_reasoning_primary_ticker ON deep_reasoning_analyses(primary_beneficiary_ticker);
CREATE INDEX IF NOT EXISTS idx_deep_reasoning_hidden_ticker ON deep_reasoning_analyses(hidden_beneficiary_ticker);
CREATE INDEX IF NOT EXISTS idx_deep_reasoning_model ON deep_reasoning_analyses(model_used);

-- ====================================
-- Column Comments
-- ====================================

COMMENT ON COLUMN deep_reasoning_analyses.id IS '고유 ID';
COMMENT ON COLUMN deep_reasoning_analyses.news_text IS '분석 대상 뉴스 텍스트';
COMMENT ON COLUMN deep_reasoning_analyses.theme IS '투자 테마';
COMMENT ON COLUMN deep_reasoning_analyses.primary_beneficiary_ticker IS '주 수혜주 티커';
COMMENT ON COLUMN deep_reasoning_analyses.primary_beneficiary_action IS '주 수혜주 액션';
COMMENT ON COLUMN deep_reasoning_analyses.primary_beneficiary_confidence IS '주 수혜주 신뢰도 (0~1)';
COMMENT ON COLUMN deep_reasoning_analyses.primary_beneficiary_reasoning IS '주 수혜주 근거';
COMMENT ON COLUMN deep_reasoning_analyses.hidden_beneficiary_ticker IS '숨은 수혜주 티커';
COMMENT ON COLUMN deep_reasoning_analyses.hidden_beneficiary_action IS '숨은 수혜주 액션';
COMMENT ON COLUMN deep_reasoning_analyses.hidden_beneficiary_confidence IS '숨은 수혜주 신뢰도 (0~1)';
COMMENT ON COLUMN deep_reasoning_analyses.hidden_beneficiary_reasoning IS '숨은 수혜주 근거';
COMMENT ON COLUMN deep_reasoning_analyses.loser_ticker IS '피해주 티커';
COMMENT ON COLUMN deep_reasoning_analyses.loser_action IS '피해주 액션';
COMMENT ON COLUMN deep_reasoning_analyses.loser_confidence IS '피해주 신뢰도 (0~1)';
COMMENT ON COLUMN deep_reasoning_analyses.loser_reasoning IS '피해주 근거';
COMMENT ON COLUMN deep_reasoning_analyses.bull_case IS '낙관 시나리오';
COMMENT ON COLUMN deep_reasoning_analyses.bear_case IS '비관 시나리오';
COMMENT ON COLUMN deep_reasoning_analyses.reasoning_trace IS '추론 과정 단계 배열';
COMMENT ON COLUMN deep_reasoning_analyses.model_used IS '사용된 AI 모델';
COMMENT ON COLUMN deep_reasoning_analyses.processing_time_ms IS '처리 시간 (밀리초)';
COMMENT ON COLUMN deep_reasoning_analyses.created_at IS '분석 생성 시각';

-- Migration complete for deep_reasoning_analyses
