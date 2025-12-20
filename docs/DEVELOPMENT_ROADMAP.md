# Development Roadmap - AI Trading System

## 현재 시스템 상태 (2025-12-17)

### ✅ 완료된 주요 기능

1. **Trading Dashboard** - 실시간 거래 모니터링
2. **Portfolio Management** - 한국투자증권 API 연동
3. **News Analysis** - AI 뉴스 분석 시스템
4. **Backtest System** - 시그널 백테스트 엔진
5. **Deep Reasoning** - AI 심층 분석
6. **War Room** - 멀티 티커 전략 회의
7. **Constitutional AI** - 헌법 기반 거래 시스템
8. **Ticker Autocomplete** - 500+ 티커 자동완성

---

## 🚧 진행 중인 작업

### 1. Historical Data Seeding System (우선순위: 높음)

**목표:** 시스템 시작 시 역사적 데이터 자동 수집

**구성 요소:**

#### A. Multi-Source News Crawler
- [ ] NewsAPI 통합 (100건/일)
- [ ] Google News RSS 크롤러
- [ ] Yahoo Finance News 크롤러
- [ ] 중복 제거 시스템
- [ ] 크롤링 스케쥴러 (매일 자동 실행)

**예상 시간:** 3-4시간

#### B. Comprehensive News Processing Pipeline
- [ ] AI 분석 파이프라인 구축
  - [ ] 티커 추출 (NER)
  - [ ] 감정 분석 (Gemini API)
  - [ ] 주제 추출
  - [ ] 핵심 주장/요약 생성
- [ ] 임베딩 생성 (OpenAI 1536-dim)
- [ ] 자동 태깅 시스템
- [ ] 메타데이터 구조화
  - 출처, 기자 이름
  - YYMMDDHHMMSS 타임스탬프
  - 중요도 점수
  - Breaking news 플래그

**예상 시간:** 4-5시간

#### C. Stock Price Data (yfinance)
- [ ] yfinance 서비스 구현
- [ ] Historical OHLCV 다운로드
- [ ] 데이터 검증 로직
- [ ] DB 저장 최적화

**예상 시간:** 1-2시간

#### D. Backfill API + Progress Tracking
- [ ] POST /api/data/backfill/start
- [ ] GET /api/data/backfill/status/{job_id}
- [ ] POST /api/data/backfill/cancel/{job_id}
- [ ] GET /api/data/stats
- [ ] Celery/Background job 설정
- [ ] 진행률 추적 시스템

**예상 시간:** 2-3시간

#### E. Frontend UI
- [ ] Data Management 페이지 확장
- [ ] 백필 컨트롤 UI
- [ ] 진행 상황 표시
- [ ] 데이터베이스 통계 대시보드

**예상 시간:** 2-3시간

**총 예상 시간:** 12-17시간

**데이터베이스 스키마 변경:**
```sql
-- news_articles 테이블 확장
ALTER TABLE news_articles ADD COLUMN embedding VECTOR(1536);
ALTER TABLE news_articles ADD COLUMN tags TEXT[];
ALTER TABLE news_articles ADD COLUMN tickers TEXT[];
ALTER TABLE news_articles ADD COLUMN sentiment VARCHAR(20);
ALTER TABLE news_articles ADD COLUMN sentiment_score FLOAT;
ALTER TABLE news_articles ADD COLUMN key_topics TEXT[];
ALTER TABLE news_articles ADD COLUMN main_claim TEXT;
ALTER TABLE news_articles ADD COLUMN summary_short TEXT;
ALTER TABLE news_articles ADD COLUMN summary_detailed TEXT;
ALTER TABLE news_articles ADD COLUMN importance_score FLOAT;
ALTER TABLE news_articles ADD COLUMN is_breaking_news BOOLEAN;
ALTER TABLE news_articles ADD COLUMN author VARCHAR(200);
ALTER TABLE news_articles ADD COLUMN source VARCHAR(50);

-- Vector similarity search index
CREATE INDEX idx_embedding ON news_articles USING ivfflat(embedding);
CREATE INDEX idx_tickers ON news_articles USING GIN(tickers);
CREATE INDEX idx_importance ON news_articles(importance_score DESC);
```

---

### 2. Trading System 실환경 연결

**미완료 항목:**

#### A. Trading Dashboard
- [ ] START ENGINE → 시황조사 트리거 연결
- [ ] START ENGINE → 뉴스 조회 트리거 연결
- [ ] 호재/경고 시그널 생성 검증
- [ ] 장 중 시간대 테스트

**예상 시간:** 2-3시간

#### B. Portfolio Management
- [ ] Portfolio Analysis N/A 값 수정
- [ ] Rebalancing 데이터 연결
- [ ] KIS API /api/kis/balance 검증

**예상 시간:** 1-2시간

#### C. News Crawling
- [ ] RSS Crawling "Connection error" 수정
- [ ] RSS feed URL 검증
- [ ] 백엔드 RSS crawler 디버깅

**예상 시간:** 2-3시간

---

### 3. War Room API 연결

**현재 상태:** Mock 데이터로 UI 완성

**필요 작업:**
- [ ] 백엔드 API 엔드포인트 구현
- [ ] 프론트엔드 API 호출 연결
- [ ] 실시간 토론 진행 상태 업데이트
- [ ] 투표 결과 저장/조회

**예상 시간:** 3-4시간

---

### 4. Deep Reasoning 실데이터 연동

**현재 상태:** Mock 모드로 기능 구현 완료

**필요 작업:**
- [ ] 실제 뉴스 데이터 연동
- [ ] 매크로 정합성 체크 실구현
- [ ] Skeptic Challenge 실구현
- [ ] 분석 결과 DB 저장

**예상 시간:** 2-3시간

---

## 📋 개선 필요 사항

### 1. 성능 최적화

#### A. Database
- [ ] PostgreSQL 인덱스 최적화
- [ ] pgvector extension 설치 (임베딩 검색)
- [ ] Connection pooling 설정
- [ ] Query 성능 튜닝

#### B. API
- [ ] Rate limiting 구현
- [ ] Caching 전략 (Redis)
- [ ] Batch processing 최적화

#### C. Frontend
- [ ] Lazy loading 구현
- [ ] Virtual scrolling (대량 데이터)
- [ ] Image optimization

**예상 시간:** 5-8시간

---

### 2. 모니터링 & 로깅

- [ ] Prometheus + Grafana 설정
- [ ] 에러 추적 (Sentry)
- [ ] 성능 메트릭 수집
- [ ] Alert 시스템 구축

**예상 시간:** 4-6시간

---

### 3. 테스트 커버리지

- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] E2E tests (Playwright)
- [ ] API tests (Postman/Newman)

**예상 시간:** 8-12시간

---

### 4. 문서화

- [ ] API 문서 업데이트
- [ ] 사용자 매뉴얼 작성
- [ ] 개발자 가이드
- [ ] Troubleshooting 가이드

**예상 시간:** 4-6시간

---

## 🔮 향후 기능 (장기 계획)

### 1. AI 고도화

- [ ] Fine-tuned model (도메인 특화)
- [ ] Multi-modal analysis (이미지 + 텍스트)
- [ ] Real-time sentiment tracking
- [ ] Predictive analytics

### 2. 확장 기능

- [ ] Mobile app (React Native)
- [ ] Telegram bot
- [ ] Slack integration
- [ ] Email alerts

### 3. 고급 분석

- [ ] Factor analysis
- [ ] Attribution analysis
- [ ] Risk decomposition
- [ ] Portfolio optimization (MVO)

---

## 📊 작업 우선순위

### High Priority (즉시 시작)
1. **Historical Data Seeding** - 시스템 운영 필수
2. **News Processing Pipeline** - RAG/AI 기능 필수
3. **Trading Dashboard 연결** - 실거래 필수

### Medium Priority (1-2주 내)
1. War Room API 연결
2. Deep Reasoning 실데이터
3. Performance Optimization

### Low Priority (장기)
1. Testing
2. Documentation
3. 확장 기능

---

## 💰 예상 비용 (API)

### 현재 사용 중
- **Gemini API:** Free tier (~$0/월)
- **NewsAPI:** Free tier (100건/일)
- **KIS API:** 무료

### 추가 필요 (Historical Data Seeding)
- **OpenAI Embeddings:** $0.0001/1K tokens
  - 예상: 10,000 articles × 평균 500 tokens = 5M tokens = **$0.50**
- **Gemini Pro (분석):** 현재 무료
- **yfinance:** 무료

**월 예상 비용:** ~$10-20 (대량 백필 시)  
**일상 운영:** ~$2-5/월

---

## 📝 다음 단계

1. **즉시:** Historical Data Seeding 구현 시작
2. **이번 주:** News Processing Pipeline 완성
3. **다음 주:** Trading System 실환경 연결 완료
4. **다다음 주:** 성능 최적화 및 모니터링

---

## 참조 문서

- [Implementation Plan](./implementation_plan.md) - Historical Data Seeding 상세 계획
- [Backtest Improvements](./251217_Backtest_Improvements.md) - 백테스트 개선 사항
- [Task Checklist](../brain/task.md) - 전체 작업 체크리스트
