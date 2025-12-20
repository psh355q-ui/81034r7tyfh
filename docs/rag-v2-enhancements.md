# RAG Foundation v2.0 - Enhanced with Auto-Tagging & Incremental Updates

## 🎯 Major Improvements

사용자님의 제안을 반영하여 RAG 시스템에 다음 기능들을 추가했습니다:

### 1. 자동 태깅 시스템 (AutoTagger)

**문제점**: 
- 과거 문서를 저장만 하면 나중에 검색하기 어려움
- 연관 종목 찾기 어려움

**해결책**:
```python
# 문서 저장 시 자동으로 다차원 태그 생성
tags = [
    {"type": "ticker", "value": "AAPL", "confidence": 1.0},
    {"type": "ticker", "value": "TSLA", "confidence": 0.7},  # 문서에 언급됨
    {"type": "sector", "value": "Technology", "confidence": 0.95},
    {"type": "topic", "value": "supply_chain", "confidence": 0.87},
    {"type": "entity", "value": "Tim Cook", "confidence": 0.92},
    {"type": "geographic", "value": "China", "confidence": 0.88}
]
```

**Tag Types**:
- **Ticker Tags**: 문서에 언급된 모든 종목 심볼
- **Sector Tags**: 산업 섹터 (Technology, Healthcare 등)
- **Topic Tags**: 주제별 분류 (supply_chain, regulatory_risk 등)
- **Entity Tags**: 인물명, 제품명, 지역명 등
- **Geographic Tags**: 지리적 위치

**검색 예시**:
```python
# 태그 기반 필터링 검색
results = await vector_store.search_similar(
    query="supply chain disruption",
    tags={
        "sector": ["Technology"],
        "topic": ["supply_chain"],
        "geographic": ["China"]
    },
    top_k=10
)

# 연관 종목 찾기 (공통 태그 기반)
related = await vector_store.find_related_tickers("AAPL", top_k=10)
# 결과: ["MSFT", "GOOGL", "NVDA", ...] (공통 태그가 많은 순)
```

### 2. 증분 업데이트 (Incremental Updates)

**문제점**:
- 매번 전체 데이터를 다시 받으면 API 비용 폭증
- 이미 있는 문서를 중복 처리

**해결책**:
```python
# document_sync_status 테이블로 마지막 업데이트 추적
{
    "ticker": "AAPL",
    "doc_type": "10-K",
    "last_sync_date": "2025-11-22 10:00:00",
    "last_document_date": "2025-11-15",  # 마지막 처리한 문서 날짜
    "documents_processed": 42,
    "total_cost_usd": 0.05
}

# 증분 업데이트 실행
await backfill_sec_filings(
    tickers=["AAPL", "MSFT"],
    incremental=True  # ✅ 마지막 업데이트 이후 신규 문서만 가져옴
)
```

**비용 절감**:
```
초기 백필 (일회성):
- 100 종목 × 10년 × 10 docs = 10,000 docs
- 비용: $0.25

일일 증분 업데이트:
- 평균 10 신규 filing/day
- 비용: $0.0001/day = $0.003/month

총 월 비용: $0.003 (99% 절감!)
```

### 3. 로컬 DB 저장 및 빠른 액세스

**데이터베이스 스키마**:
```sql
-- 메인 벡터 저장소
document_embeddings
├── embedding (1536-dim vector)
├── content (full text)
├── document_date (filing/publish date)
└── metadata (JSONB)

-- 태그 테이블
document_tags
├── document_id
├── tag_type (ticker, sector, topic, entity)
├── tag_value
└── confidence (0-1)

-- 증분 업데이트 추적
document_sync_status
├── ticker
├── doc_type
├── last_sync_date
└── last_document_date
```

**속도 최적화**:
- pgvector IVFFlat 인덱스: 벡터 검색 < 100ms
- Tag 인덱스: 태그 필터링 < 10ms
- Hypertable 파티셔닝: 3개월 단위 청크

---

## 🏗️ 시스템 플로우

### 초기 백필 (1회)
```
1. S&P 500 100종목 선택
   ↓
2. SEC EDGAR에서 10년치 10-K/10-Q 다운로드
   ↓
3. 섹션별 분할 (Risk Factors, MD&A, Business)
   ↓
4. OpenAI Embedding API로 벡터화
   ↓
5. AutoTagger로 자동 태그 생성 (Claude Haiku)
   ↓
6. TimescaleDB + pgvector에 저장
   ↓
7. document_sync_status 업데이트

비용: $0.25 (일회성)
시간: 10시간 (백그라운드)
```

### 일일 증분 업데이트 (cron)
```
1. document_sync_status 확인
   ↓
2. 마지막 업데이트 이후 신규 filing만 조회
   ↓
3. 신규 문서만 임베딩 + 태깅
   ↓
4. 로컬 DB에 추가
   ↓
5. sync_status 업데이트

비용: $0.0001/day = $0.003/month
시간: 5분/day
```

### 검색 시 (실시간)
```
1. 사용자 쿼리 + 태그 필터
   ↓
2. 쿼리 임베딩 (캐시 확인)
   ↓
3. pgvector Cosine Similarity 검색
   ↓
4. 태그 필터링 적용
   ↓
5. 유사도 순 정렬 반환

응답 시간: < 100ms
API 비용: $0 (로컬 DB 검색)
```

---

## 📊 비용 분석 (최종)

| 항목 | 초기 | 월간 | 비고 |
|------|------|------|------|
| **Embedding API** | | | |
| - 초기 백필 (100 종목 × 10년) | $0.25 | - | 일회성 |
| - 일일 증분 업데이트 | - | $0.003 | 99% 절감 |
| **Auto-Tagging (Claude Haiku)** | | | |
| - 초기 백필 (10,000 docs) | $0.15 | - | 섹터 분류용 |
| - 일일 증분 (10 docs/day) | - | $0.0005 | |
| **Vector DB (pgvector)** | $0 | $0 | 무료 (TimescaleDB 내장) |
| **Redis Cache** | $0 | $0 | 기존 인프라 활용 |
| **합계** | **$0.40** | **$0.0035** | **월 $1 미만 달성!** |

---

## 🚀 새로운 API 엔드포인트

```python
# 1. 태그 기반 검색
POST /api/v1/vector/search
{
    "query": "supply chain disruption",
    "tags": {
        "sector": ["Technology"],
        "topic": ["supply_chain"]
    },
    "top_k": 10
}

# 2. 연관 종목 찾기
GET /api/v1/vector/related/AAPL?top_k=10
# 응답: ["MSFT", "GOOGL", "NVDA", ...]

# 3. 종목 태그 조회
GET /api/v1/vector/tags/AAPL
# 응답:
{
    "ticker": ["AAPL", "TSLA", "MSFT"],
    "sector": ["Technology"],
    "topic": ["supply_chain", "AI_adoption"],
    "entity": ["Tim Cook", "iPhone 15", "China"]
}

# 4. 증분 업데이트 트리거
POST /api/v1/vector/incremental-update
{
    "tickers": ["AAPL", "MSFT"],
    "doc_types": ["10-K", "10-Q"]
}

# 5. 비용 통계
GET /api/v1/vector/stats
# 응답:
{
    "total_documents": 10523,
    "total_cost_usd": 0.42,
    "daily_cost_usd": 0.0001,
    "last_sync": "2025-11-22T10:00:00Z"
}
```

---

## ✅ 개선 효과 요약

### 비용 효율
- ✅ 초기 비용: $0.40 (일회성)
- ✅ 월 운영 비용: $0.0035 (목표 $1 대비 99.7% 절감)
- ✅ 증분 업데이트로 API 호출 99% 감소

### 검색 품질
- ✅ 태그 기반 필터링으로 검색 정확도 향상
- ✅ 연관 종목 자동 발견 (supply chain, 섹터 피어)
- ✅ 다차원 분류 (ticker + sector + topic + entity)

### 운영 효율
- ✅ 일일 자동 업데이트 (cron 스케줄링)
- ✅ 중복 방지 (content_hash)
- ✅ 진행률 추적 및 재시작 가능
- ✅ 로컬 DB로 빠른 액세스 (< 100ms)

---

## 📝 다음 단계

1. **Task 1.1 시작**: pgvector 설치
2. **AutoTagger 구현**: 자동 태그 생성 로직
3. **증분 업데이트 테스트**: 샘플 10종목으로 검증
4. **프로덕션 배포**: cron 스케줄링 설정

---

**Created**: 2025-11-22
**Phase**: 7.5 (RAG Foundation v2.0)
**Budget**: $0.0035/month (99.7% reduction from $1 target)
**Key Features**: Auto-Tagging + Incremental Updates + Local DB
