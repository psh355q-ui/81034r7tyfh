-- GLM-4.7 뉴스 해석 서비스: news_articles 테이블에 glm_analysis 컬럼 추가
-- Date: 2026-01-15
-- Phase: Phase 0, T0.2

-- 1. glm_analysis JSONB 컬럼 추가
ALTER TABLE news_articles
ADD COLUMN IF NOT EXISTS glm_analysis JSONB;

-- 2. GIN 인덱스 생성 (JSONB 쿼리 최적화)
CREATE INDEX IF NOT EXISTS idx_news_articles_glm_analysis
ON news_articles USING GIN (glm_analysis);

-- 3. 부분 인덱스 생성 (분석 완료된 뉴스만)
CREATE INDEX IF NOT EXISTS idx_news_articles_glm_analyzed
ON news_articles (id)
WHERE glm_analysis IS NOT NULL;

-- 4. 코멘트 추가
COMMENT ON COLUMN news_articles.glm_analysis IS 'GLM-4.7 뉴스 분석 결과 (종목/섹터 식별)';
