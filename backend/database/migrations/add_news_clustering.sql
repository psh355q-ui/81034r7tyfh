-- ═══════════════════════════════════════════════════════════════
-- 뉴스 클러스터링 & 경제 캘린더 시스템
-- Migration: Phase 1 - News Clustering Enhancement
-- Created: 2025-12-17
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- 1. 뉴스 클러스터 테이블 (4-Signal 프레임워크)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_clusters (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(32) UNIQUE NOT NULL,  -- 티커 + 주제 해시
    ticker VARCHAR(20),
    theme VARCHAR(200),

-- 기본 정보
hit_count INT DEFAULT 1, -- 중복 횟수
first_seen_at TIMESTAMPTZ NOT NULL, -- 첫 발견 시각
last_seen_at TIMESTAMPTZ NOT NULL, -- 마지막 발견 시각
source_list JSONB DEFAULT '[]', -- 출처 목록
article_ids JSONB DEFAULT '[]', -- 기사 ID 목록

-- ═══ 4가지 핵심 신호 ═══
di_score FLOAT DEFAULT 0.5, -- 출처 다양성 무결성 (0~1)
tn_score FLOAT DEFAULT 0.0, -- 시간 자연스러움 (-1~+1)
ni_score FLOAT DEFAULT 0.5, -- 내용 독립성 (0~1)
el_matched BOOLEAN DEFAULT FALSE, -- 이벤트 정당성 (매칭 여부)
el_confidence FLOAT DEFAULT 0.0, -- 이벤트 신뢰도
el_event_name VARCHAR(200), -- 매칭된 이벤트명

-- ═══ 판정 결과 ═══
verdict VARCHAR(30) DEFAULT 'PENDING',
-- 'EMBARGO_EVENT': 엠바고 해제 (신뢰)
-- 'ORGANIC_CONSENSUS': 진짜 합의 (강화)
-- 'MANIPULATION_ATTACK': 작전 공격 (차단)
-- 'PR_CAMPAIGN': PR 캠페인 (강화 금지)
-- 'NOISE': 노이즈 (무시)
-- 'WATCH': 관망 (냉각기간)
verdict_reason TEXT,
confidence_multiplier FLOAT DEFAULT 1.0,

-- ═══ 냉각 기간 ═══
cooling_intensity FLOAT DEFAULT 0.0,
    cooling_until TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cluster_ticker ON news_clusters (ticker);

CREATE INDEX IF NOT EXISTS idx_cluster_verdict ON news_clusters (verdict);

CREATE INDEX IF NOT EXISTS idx_cluster_time ON news_clusters (first_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_cluster_fingerprint ON news_clusters (fingerprint);

-- ═══════════════════════════════════════════════════════════════
-- 2. 출처 신뢰도 테이블
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS source_credibility (
    source VARCHAR(100) PRIMARY KEY,
    tier INT DEFAULT 3, -- 1(최상) ~ 5(최하)
    total_signals INT DEFAULT 0, -- 전체 시그널 수
    correct_signals INT DEFAULT 0, -- 정확한 시그널 수
    accuracy_rate FLOAT, -- 정확도
    manipulation_flags INT DEFAULT 0, -- 조작 연루 횟수
    last_manipulation_at TIMESTAMPTZ,
    credibility_weight FLOAT DEFAULT 1.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tier 1 출처 (초기 데이터)
INSERT INTO
    source_credibility (
        source,
        tier,
        credibility_weight
    )
VALUES ('Bloomberg', 1, 2.0),
    ('Reuters', 1, 2.0),
    ('WSJ', 1, 2.0),
    ('Wall Street Journal', 1, 2.0),
    ('Financial Times', 1, 2.0),
    ('SEC Filing', 1, 2.5),
    ('CNBC', 2, 1.5),
    ('Yahoo Finance', 2, 1.3),
    ('MarketWatch', 2, 1.3),
    ('연합뉴스', 2, 1.4),
    ('Yonhap News', 2, 1.4),
    ('한국경제', 2, 1.3),
    ('매일경제', 2, 1.3)
ON CONFLICT (source) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 3. 중앙은행 의원 정보 (연준 등)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS central_bank_officials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(100),  -- 'Chair', 'Vice Chair', 'Governor', 'President'
    institution VARCHAR(50) DEFAULT 'Federal Reserve',
    bank_location VARCHAR(50),  -- 'Federal Reserve Board', 'New York Fed', etc.

-- 의결권
has_voting_rights BOOLEAN DEFAULT FALSE,
voting_year INT, -- FOMC 투표권은 순환제

-- 성향
stance VARCHAR(20) DEFAULT 'NEUTRAL', -- 'HAWKISH', 'DOVISH', 'NEUTRAL'
stance_confidence FLOAT DEFAULT 0.5, -- 0.0~1.0

-- 약력
bio TEXT, wikipedia_url VARCHAR(500),

-- 임기
term_start DATE,
    term_end DATE,
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_official_active ON central_bank_officials (active);

CREATE INDEX IF NOT EXISTS idx_official_voting ON central_bank_officials (has_voting_rights);

-- ═══════════════════════════════════════════════════════════════
-- 4. 경제 캘린더 이벤트 (자동 수집)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS economic_calendar_events (
    id SERIAL PRIMARY KEY,

-- 기본 정보
event_name VARCHAR(200) NOT NULL,
event_type VARCHAR(50) NOT NULL,
-- 'FOMC', 'CPI', 'GDP', 'NFP', 'EARNINGS', 
-- 'FED_SPEECH', 'FOMC_TESTIMONY', 'FOMC_PRESS_CONFERENCE'
ticker VARCHAR(20), -- 실적발표의 경우 티커

-- 일정
scheduled_at TIMESTAMPTZ NOT NULL,
embargo_lift_time TIMESTAMPTZ, -- 엠바고 해제 예상 시각
fiscal_quarter VARCHAR(10), -- 예: '2025Q1'

-- 연준 발언 관련
speaker_id INT REFERENCES central_bank_officials (id),
speech_topic VARCHAR(500),
speech_location VARCHAR(200),
expected_stance VARCHAR(20), -- 'HAWKISH', 'DOVISH', 'NEUTRAL'
live_stream_url VARCHAR(500),
transcript_url VARCHAR(500),

-- 중요도
importance INT DEFAULT 3, -- 1(최고)~5(낮음)
expected_volatility FLOAT, -- 예상 변동성

-- 예측값 (있는 경우)
consensus_estimate JSONB,
-- 예: {"eps": 1.25, "revenue": 5000000000}

-- 수집 정보
data_source VARCHAR(50), -- 'FMP', 'FRED', 'Finnhub', 'Yahoo', 'FederalReserve'
source_event_id VARCHAR(100), -- 원본 API의 이벤트 ID
expected_news_burst BOOLEAN DEFAULT TRUE,

-- 메타
created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_scheduled ON economic_calendar_events (scheduled_at);

CREATE INDEX IF NOT EXISTS idx_event_ticker ON economic_calendar_events (ticker);

CREATE INDEX IF NOT EXISTS idx_event_type ON economic_calendar_events (event_type);

CREATE INDEX IF NOT EXISTS idx_event_speaker ON economic_calendar_events (speaker_id);

-- ═══════════════════════════════════════════════════════════════
-- 5. 이벤트 결과 (자동 기록)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS economic_event_results (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES economic_calendar_events(id),

-- 실제 결과
actual_value JSONB,
-- 예: {"eps": 1.32, "revenue": 5200000000, "guidance": "positive"}

-- 예측 대비
beat_consensus BOOLEAN, -- 예상치 상회 여부
surprise_percent FLOAT, -- 서프라이즈 %

-- 시장 반응
price_change_1h FLOAT, -- 발표 후 1시간 가격 변동
price_change_1d FLOAT, -- 발표 후 1일 가격 변동
volume_change FLOAT, -- 거래량 변화
vix_change_1h FLOAT, -- VIX 변동 (연준 발언 등)
dollar_index_change_1h FLOAT, -- 달러 인덱스 변동

-- 뉴스 반응
news_cluster_id INT REFERENCES news_clusters (id),
news_count_1h INT, -- 발표 후 1시간 내 뉴스 수

-- 연준 발언 관련
actual_stance VARCHAR(20), -- 실제 발언 성향
key_quotes JSONB, -- 주요 발언 인용
market_interpretation VARCHAR(20), -- 시장 해석

-- 수집 정보
result_announced_at TIMESTAMPTZ,
    data_collected_at TIMESTAMPTZ DEFAULT NOW(),
    data_source VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_result_event ON economic_event_results (event_id);

CREATE INDEX IF NOT EXISTS idx_result_announced ON economic_event_results (result_announced_at);

CREATE INDEX IF NOT EXISTS idx_result_cluster ON economic_event_results (news_cluster_id);

-- ═══════════════════════════════════════════════════════════════
-- 6. 수집 작업 로그 (모니터링용)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS calendar_collection_logs (
    id SERIAL PRIMARY KEY,
    collection_type VARCHAR(50),  -- 'scheduled_update', 'result_collection', 'officials_update'
    data_source VARCHAR(50),

-- 통계
events_collected INT DEFAULT 0,
events_updated INT DEFAULT 0,
results_collected INT DEFAULT 0,

-- 상태
status VARCHAR(20), -- 'success', 'partial', 'failed'
error_message TEXT,

-- 타이밍
started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds FLOAT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_log_type ON calendar_collection_logs (collection_type);

CREATE INDEX IF NOT EXISTS idx_log_created ON calendar_collection_logs (created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 7. 의원 성향 분석 히스토리
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS official_stance_history (
    id SERIAL PRIMARY KEY,
    official_id INT REFERENCES central_bank_officials(id),
    
    stance VARCHAR(20),  -- HAWKISH, DOVISH, NEUTRAL
    confidence FLOAT,
    reasoning TEXT,

-- 분석 정보
analysis_method VARCHAR(50),  -- 'AI_ANALYSIS', 'VOTING_PATTERN', 'SPEECH_ANALYSIS'
    data_sources JSONB,  -- Wikipedia, speeches, etc.
    
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stance_official ON official_stance_history (official_id);

CREATE INDEX IF NOT EXISTS idx_stance_analyzed ON official_stance_history (analyzed_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 8. 투표권 변경 히스토리
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS voting_rights_history (
    id SERIAL PRIMARY KEY,
    official_id INT REFERENCES central_bank_officials (id),
    year INT NOT NULL,
    has_voting_rights BOOLEAN,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voting_official ON voting_rights_history (official_id);

CREATE INDEX IF NOT EXISTS idx_voting_year ON voting_rights_history (year DESC);

-- ═══════════════════════════════════════════════════════════════
-- 9. 자동 업데이트 로그
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS officials_update_logs (
    id SERIAL PRIMARY KEY,
    update_type VARCHAR(50), -- 'MONTHLY', 'VOTING_ANNUAL', 'TERM_CHECK', 'STANCE_ANALYSIS'
    stats JSONB, -- {"board_updated": 7, "new_members": 1, ...}
    status VARCHAR(20),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_officials_log_type ON officials_update_logs (update_type);

CREATE INDEX IF NOT EXISTS idx_officials_log_created ON officials_update_logs (created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 완료 메시지
-- ═══════════════════════════════════════════════════════════════
DO $$
BEGIN
    RAISE NOTICE '✅ 뉴스 클러스터링 & 경제 캘린더 마이그레이션 완료';
    RAISE NOTICE '   - 9개 테이블 생성됨';
    RAISE NOTICE '   - 초기 출처 신뢰도 데이터 시드됨';
END $$;