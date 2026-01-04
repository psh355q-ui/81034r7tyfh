-- Database Optimization Phase 1: 복합 인덱스 추가
-- 목표: War Room MVP DB 쿼리 시간 0.5-1.0s → 0.3-0.5s 단축
-- 날짜: 2026-01-02
-- 예상 효과: 티커별 조회, 최신 데이터 조회 최적화

-- ============================================================================
-- NewsArticle 복합 인덱스
-- ============================================================================

-- 티커별 최신 뉴스 조회 최적화 (War Room News Agent용)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_ticker_date ON news_articles USING btree (tickers, published_date);

-- 처리된 뉴스만 조회 (부분 인덱스)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_processed ON news_articles (published_date)
WHERE
    processed_at IS NOT NULL;

COMMENT ON INDEX idx_news_ticker_date IS '티커별 뉴스 시계열 조회 최적화 (Phase 1)';

COMMENT ON INDEX idx_news_processed IS '처리 완료된 뉴스만 필터링 (Phase 1)';

-- ============================================================================
-- TradingSignal 복합 인덱스
-- ============================================================================

-- 티커별 최신 신호 조회 (시간 역순)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_ticker_date ON trading_signals (ticker, created_at DESC);

-- 알림 미전송 신호만 조회 (부분 인덱스)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signal_pending_alert ON trading_signals (ticker)
WHERE
    alert_sent = FALSE;

COMMENT ON INDEX idx_signal_ticker_date IS '티커별 최신 신호 조회 최적화 (Phase 1)';

COMMENT ON INDEX idx_signal_pending_alert IS '알림 대기 중 신호만 조회 (Phase 1)';

-- ============================================================================
-- StockPrice 최적화 인덱스
-- ============================================================================

-- 최신 가격 조회용 DESC 인덱스
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stock_ticker_time_desc ON stock_prices (ticker, time DESC);

COMMENT ON INDEX idx_stock_ticker_time_desc IS '최신 가격 조회 최적화 (Phase 1)';

-- ============================================================================
-- 통계 갱신 (쿼리 플래너 최적화)
-- ============================================================================

ANALYZE news_articles;

ANALYZE trading_signals;

ANALYZE stock_prices;

-- ============================================================================
-- 검증 쿼리
-- ============================================================================

-- 인덱스 크기 확인
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(
        pg_relation_size(indexname::regclass)
    ) as index_size
FROM pg_indexes
WHERE
    schemaname = 'public'
    AND indexname IN (
        'idx_news_ticker_date',
        'idx_news_processed',
        'idx_signal_ticker_date',
        'idx_signal_pending_alert',
        'idx_stock_ticker_time_desc'
    )
ORDER BY tablename, indexname;

-- 인덱스 생성 확인
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE
    schemaname = 'public'
    AND indexname LIKE '%ticker%date%'
    OR indexname LIKE '%processed%'
    OR indexname LIKE '%pending%'
    OR indexname LIKE '%desc%';

-- 예상 효과 측정 (EXPLAIN ANALYZE 권장)
-- War Room MVP에서 자주 사용되는 쿼리 패턴:
--
-- 1. 티커별 최신 뉴스
--    SELECT * FROM news_articles
--    WHERE tickers @> ARRAY['NVDA']
--    ORDER BY published_date DESC LIMIT 10;
--
-- 2. 처리된 뉴스만
--    SELECT * FROM news_articles
--    WHERE processed_at IS NOT NULL
--    ORDER BY published_date DESC;
--
-- 3. 티커별 최신 신호
--    SELECT * FROM trading_signals
--    WHERE ticker = 'NVDA'
--    ORDER BY created_at DESC LIMIT 5;
--
-- 4. 최신 가격
--    SELECT * FROM stock_prices
--    WHERE ticker = 'NVDA'
--    ORDER BY time DESC LIMIT 1;

COMMIT;