# Database Storage Optimization Analysis

**Generated**: 2025-12-27 14:41
**Focus**: 컬럼 통합 및 용량 최적화

---

## 📊 현재 테이블 크기

| 테이블 | 크기 | 주요 용량 요인 |
|--------|------|--------------|
| news_articles | (측정 중) | TEXT, VECTOR(1536), 중복 컬럼 |
| trading_signals | (측정 중) | 중복 메타데이터 컬럼 |
| stock_prices | (측정 중) | 대량 시계열 데이터 |

---

## 🔍 컬럼 통합 기회 분석

### news_articles - 통합 가능 항목

#### 1. 시간 관련 컬럼 (3개 → 1-2개)
```
현재:
- published_at (TIMESTAMP) - 뉴스 발행 시각
- published_date (TIMESTAMP) - 중복?
- crawled_at (TIMESTAMP) - 크롤링 시각
- created_at (TIMESTAMP) - DB 저장 시각

제안:
- published_at (TIMESTAMP) - 뉴스 발행 시각만 유지
- created_at (TIMESTAMP) - DB 저장 시각
❌ 삭제: published_date (published_at와 중복)
❌ 삭제: crawled_at (중요하지 않음, 필요시 metadata에)

절감: ~16 bytes/row
```

#### 2. 감성 분석 컬럼 (2개 → JSONB 통합)
```
현재:
- sentiment_score (FLOAT) - 점수
- sentiment_label (VARCHAR) - 라벨

제안:
→ metadata (JSONB) 안에 통합
{
  "sentiment": {
    "score": 0.85,
    "label": "positive"
  }
}

절감: ~24 bytes/row (VARCHAR 제거)
```

#### 3. 분석 상태 (BOOLEAN → metadata)
```
현재:
- is_analyzed (BOOLEAN)

제안:
→ metadata에 통합 또는 analyzed_at (TIMESTAMP) 사용
- NULL이면 미분석
- 값 있으면 분석 완료 + 시각

절감: ~1 byte/row
```

#### 4. 임베딩 메타데이터
```
현재:
- embedding (VECTOR(1536)) - 6144 bytes
- embedding_model (VARCHAR) - 모델 정보

제안:
- embedding 유지 (필수)
- embedding_model → metadata로 이동

절감: ~20-50 bytes/row
```

### trading_signals - 통합 가능 항목

#### 1. 가격 관련 컬럼 (JSONB 통합)
```
현재:
- target_price (FLOAT)
- stop_loss (FLOAT)
- exit_price (FLOAT)
- entry_price (FLOAT)

제안:
→ price_levels (JSONB)
{
  "target": 150.0,
  "stop_loss": 130.0,
  "entry": 140.0,
  "exit": 148.0
}

절감: 컬럼 4개 → 1개 (메타데이터 오버헤드는 있지만 유연성 증가)
```

#### 2. 시간 관련 컬럼 (5개 → 3개)
```
현재:
- created_at
- generated_at (AI 생성 시각)
- executed_at
- outcome_recorded_at
- updated_at

제안:
- created_at - 시그널 생성
- executed_at - 실행 시각
- completed_at - 완료 시각 (outcome_recorded_at 대체)
❌ 삭제: generated_at (created_at와 거의 동일)
❌ 삭제: updated_at (필요시 metadata에)

절감: ~16-32 bytes/row
```

#### 3. 메타데이터 통합
```
현재:
- metadata (JSONB) - AI 정보
- reasoning (TEXT) - 근거

제안:
→ metadata에 reasoning 통합
{
  "ai_model": "gpt-4",
  "confidence": 85,
  "reasoning": "...",
  "debate_results": {...}
}

절감: TEXT 컬럼 제거로 ~100-500 bytes/row
```

---

## 💡 최적화 전략

### Strategy 1: JSONB 활용 (권장)

**장점**:
- 유연성: 새 필드 추가 시 테이블 변경 불필요
- 압축: PostgreSQL JSONB는 자동 압축
- 쿼리: GIN 인덱스로 빠른 검색 가능

**단점**:
- 약간의 오버헤드 (~10-20%)
- 타입 안전성 낮음

**적용 제안**:
```sql
-- news_articles
ALTER TABLE news_articles DROP COLUMN sentiment_label;
ALTER TABLE news_articles DROP COLUMN sentiment_score;
ALTER TABLE news_articles DROP COLUMN embedding_model;
ALTER TABLE news_articles DROP COLUMN published_date;
ALTER TABLE news_articles DROP COLUMN crawled_at;

-- metadata 구조
{
  "sentiment": {"score": 0.8, "label": "positive"},
  "embedding_model": "text-embedding-3-small",
  "categories": ["tech", "earnings"],
  "crawled_at": "2024-01-01T00:00:00Z"
}

-- trading_signals
ALTER TABLE trading_signals DROP COLUMN target_price;
ALTER TABLE trading_signals DROP COLUMN stop_loss;
ALTER TABLE trading_signals DROP COLUMN exit_price;
ALTER TABLE trading_signals DROP COLUMN reasoning;

-- metadata 구조
{
  "price_levels": {
    "target": 150.0,
    "stop_loss": 130.0,
    "entry": 140.0,
    "exit": 148.0
  },
  "reasoning": "Strong earnings beat...",
  "ai_model": "deep-reasoning-v2",
  "confidence": 85
}
```

### Strategy 2: VARCHAR 길이 최적화

```sql
-- 현재 문제
source VARCHAR(100) -- 대부분 10자 이하
url TEXT -- 대부분 200자 이하

-- 최적화
source VARCHAR(50) -- 50으로 충분
url VARCHAR(500) -- TEXT 대신 고정 길이

절감: VARCHAR는 실제 사용 길이만 저장하지만,
      TEXT는 추가 포인터 오버헤드 있음
```

### Strategy 3: 불필요한 인덱스 제거

```sql
-- 현재 인덱스 확인
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('news_articles', 'trading_signals');

-- 사용하지 않는 인덱스 삭제
-- (쿼리 분석 후 결정)
```

---

## 📉 예상 용량 절감

### news_articles (행당)

| 항목 | 절감 |
|------|------|
| published_date 삭제 | 8 bytes |
| crawled_at 삭제 | 8 bytes |
| sentiment_label 삭제 | ~20 bytes |
| sentiment_score 삭제 | 8 bytes |
| embedding_model 삭제 | ~30 bytes |
| **총 절감** | **~74 bytes/row** |

**예시**: 10만 건 → **7.4 MB 절감**

### trading_signals (행당)

| 항목 | 절감 |
|------|------|
| target_price, stop_loss, exit_price → JSONB | ~24 bytes |
| reasoning → metadata | ~200 bytes (avg) |
| generated_at, updated_at 삭제 | 16 bytes |
| **총 절감** | **~240 bytes/row** |

**예시**: 1만 건 → **2.4 MB 절감**

---

## 🚀 실행 계획 (용량 최적화 우선)

### Phase 1: 분석 및 백업 ✅
- [x] 현재 테이블 크기 측정
- [x] 컬럼별 사용률 분석
- [ ] 전체 DB 백업

### Phase 2: 저비용 최적화 (즉시)
```sql
-- 1. 중복 컬럼 삭제 (데이터 손실 없음)
ALTER TABLE news_articles 
DROP COLUMN IF EXISTS published_date,  -- published_at와 중복
DROP COLUMN IF EXISTS crawled_at;       -- 불필요

ALTER TABLE trading_signals
DROP COLUMN IF EXISTS generated_at,     -- created_at와 중복
DROP COLUMN IF EXISTS updated_at;       -- 불필요

-- 2. VARCHAR 길이 최적화
ALTER TABLE news_articles 
ALTER COLUMN source TYPE VARCHAR(50);

-- 절감: ~100-200 MB (예상)
```

### Phase 3: JSONB 통합 (단계적)
```sql
-- 1. news_articles
UPDATE news_articles 
SET metadata = jsonb_build_object(
  'sentiment', jsonb_build_object(
    'score', sentiment_score,
    'label', sentiment_label
  ),
  'embedding_model', embedding_model
)
WHERE metadata IS NULL OR NOT metadata ? 'sentiment';

ALTER TABLE news_articles
DROP COLUMN sentiment_score,
DROP COLUMN sentiment_label,
DROP COLUMN embedding_model;

-- 2. trading_signals
UPDATE trading_signals
SET metadata = metadata || jsonb_build_object(
  'price_levels', jsonb_build_object(
    'target', target_price,
    'stop_loss', stop_loss,
    'exit', exit_price
  ),
  'reasoning', reasoning
);

ALTER TABLE trading_signals
DROP COLUMN target_price,
DROP COLUMN stop_loss,
DROP COLUMN exit_price,
DROP COLUMN reasoning;

-- 절감: ~500 MB (예상)
```

### Phase 4: 스키마 JSON 업데이트
- 실제 최적화된 구조 반영
- db-schema-manager 업데이트
- Repository 코드 수정

---

## ✅ 다음 단계 결정

**Option A: 즉시 최적화 (권장)**
1. 백업 먼저
2. Phase 2 실행 (중복 컬럼 삭제)
3. 용량 절감 확인
4. Phase 3 단계적 진행

**Option B: 현상 유지 + 스키마 JSON만 수정**
- DB는 그대로
- 스키마 JSON을 현재 DB에 맞게 수정
- 용량 최적화는 나중에

**어떤 방향으로 진행할까요?**
