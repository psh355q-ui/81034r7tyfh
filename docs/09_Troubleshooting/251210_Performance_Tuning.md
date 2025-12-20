# Performance Tuning Guide - AI Trading System

**작성일**: 2025-12-10
**문서 버전**: 1.0
**옵션**: Option 5 - 문서화 보완

---

## 📋 목차

1. [개요](#개요)
2. [Redis 캐시 최적화](#redis-캐시-최적화)
3. [TimescaleDB 최적화](#timescaledb-최적화)
4. [PostgreSQL 성능 튜닝](#postgresql-성능-튜닝)
5. [API 응답 속도 개선](#api-응답-속도-개선)
6. [AI 모델 최적화](#ai-모델-최적화)
7. [네트워크 최적화](#네트워크-최적화)
8. [모니터링 및 측정](#모니터링-및-측정)

---

## 개요

### 현재 성능 지표

| 지표 | 목표 | 현재 달성 | 상태 |
|------|------|-----------|------|
| 캐시 히트율 | > 95% | 96.4% | ✅ |
| API 응답 속도 | < 10ms | 3.93ms | ✅ |
| DB 쿼리 속도 | < 50ms | 12ms | ✅ |
| AI 응답 속도 | < 2s | 1.2s | ✅ |
| 메모리 사용량 | < 2GB | 1.5GB | ✅ |

### 성과

- **2-Layer Cache 시스템**: 725배 속도 향상
- **Incremental Update**: 86% 비용 절감
- **Connection Pooling**: 10배 동시 연결 처리
- **Batch Processing**: 5배 처리량 증가

---

## Redis 캐시 최적화

### 1. 2-Layer Cache 아키텍처

```
Layer 1: In-Memory Cache (Python dict)
    ↓ (Miss)
Layer 2: Redis Cache
    ↓ (Miss)
Database/API
```

**코드 위치**: `backend/data/feature_store.py`

### 2. 캐시 설정 최적화

```python
# redis.conf 최적화
maxmemory 2gb
maxmemory-policy allkeys-lru  # LRU 제거 정책
save ""  # 디스크 저장 비활성화 (속도 우선)

# 연결 풀 설정
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)
```

### 3. TTL (Time To Live) 전략

```python
# 데이터 유형별 TTL 설정
CACHE_TTL = {
    "price": 60,           # 1분 (실시간 가격)
    "news": 300,           # 5분 (뉴스)
    "fundamentals": 3600,  # 1시간 (재무 데이터)
    "features": 1800,      # 30분 (AI 특징)
}

# 사용 예시
redis_client.setex(
    f"price:{ticker}",
    CACHE_TTL["price"],
    json.dumps(price_data)
)
```

### 4. 캐시 키 네이밍 전략

```python
# 계층적 키 구조
# 형식: {카테고리}:{서브카테고리}:{식별자}

# 좋은 예
"price:realtime:AAPL:2024-12-10"
"news:chip:NVDA:latest"
"feature:technical:TSLA:1d"

# 나쁜 예
"AAPL_price_data"
"news123"
```

### 5. Pipeline 사용 (대량 작업)

```python
import redis

# ❌ 비효율적: 여러 번 왕복
for ticker in tickers:
    redis_client.get(f"price:{ticker}")

# ✅ 효율적: 한 번에 처리
pipe = redis_client.pipeline()
for ticker in tickers:
    pipe.get(f"price:{ticker}")
results = pipe.execute()
```

### 6. 캐시 Warming (사전 로딩)

```python
async def warm_cache():
    """서버 시작 시 자주 사용하는 데이터 미리 로딩"""
    popular_tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]

    for ticker in popular_tickers:
        # 가격 데이터 캐시
        price = await fetch_price(ticker)
        redis_client.setex(f"price:{ticker}", 60, json.dumps(price))

        # 뉴스 데이터 캐시
        news = await fetch_news(ticker)
        redis_client.setex(f"news:{ticker}", 300, json.dumps(news))

# 서버 시작 시 실행
@app.on_event("startup")
async def startup():
    await warm_cache()
```

---

## TimescaleDB 최적화

### 1. Hypertable 생성

```sql
-- 시계열 테이블을 Hypertable로 변환
CREATE TABLE stock_prices (
    time TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
);

-- Hypertable 활성화 (자동 파티셔닝)
SELECT create_hypertable('stock_prices', 'time');
```

### 2. 인덱스 최적화

```sql
-- 복합 인덱스 생성
CREATE INDEX idx_ticker_time ON stock_prices (ticker, time DESC);

-- 부분 인덱스 (최근 데이터만)
CREATE INDEX idx_recent_prices
ON stock_prices (ticker, time DESC)
WHERE time > NOW() - INTERVAL '30 days';
```

### 3. Continuous Aggregates (자동 집계)

```sql
-- 1시간 캔들 자동 계산
CREATE MATERIALIZED VIEW stock_prices_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    ticker,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume
FROM stock_prices
GROUP BY bucket, ticker;

-- 자동 갱신 정책
SELECT add_continuous_aggregate_policy('stock_prices_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

### 4. Data Retention 정책

```sql
-- 1년 이상 된 데이터 자동 삭제
SELECT add_retention_policy('stock_prices', INTERVAL '1 year');

-- 압축 정책 (오래된 데이터 압축)
ALTER TABLE stock_prices SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker'
);

SELECT add_compression_policy('stock_prices', INTERVAL '30 days');
```

---

## PostgreSQL 성능 튜닝

### 1. Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 연결 풀 설정
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 최대 연결 수
    max_overflow=10,       # 추가 연결 수
    pool_pre_ping=True,    # 연결 확인
    pool_recycle=3600,     # 1시간마다 재연결
)
```

### 2. Query 최적화

```sql
-- ❌ 비효율적: 전체 테이블 스캔
SELECT * FROM stocks WHERE ticker LIKE '%AAPL%';

-- ✅ 효율적: 인덱스 사용
SELECT * FROM stocks WHERE ticker = 'AAPL';

-- ❌ 비효율적: N+1 문제
SELECT * FROM trades;  -- 1000개 조회
for each trade:
    SELECT * FROM stocks WHERE id = trade.stock_id;  -- 1000번 실행

-- ✅ 효율적: JOIN 사용
SELECT t.*, s.*
FROM trades t
JOIN stocks s ON t.stock_id = s.id;  -- 1번 실행
```

### 3. EXPLAIN ANALYZE 사용

```sql
-- 쿼리 성능 분석
EXPLAIN ANALYZE
SELECT * FROM stock_prices
WHERE ticker = 'AAPL'
AND time > NOW() - INTERVAL '1 day'
ORDER BY time DESC
LIMIT 100;

-- 결과 해석:
-- Seq Scan → 인덱스 필요
-- Index Scan → 최적화됨
-- Execution Time: 12ms → 목표 달성
```

### 4. 배치 Insert

```python
# ❌ 비효율적: 개별 Insert
for price in prices:
    db.execute("INSERT INTO stock_prices VALUES (...)", price)

# ✅ 효율적: 배치 Insert
db.execute_many(
    "INSERT INTO stock_prices VALUES (...)",
    prices
)
```

---

## API 응답 속도 개선

### 1. 비동기 처리 (Async/Await)

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

# ❌ 동기: 순차 실행 (3초)
@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    price = fetch_price(ticker)        # 1초
    news = fetch_news(ticker)          # 1초
    fundamentals = fetch_fundamentals(ticker)  # 1초
    return {"price": price, "news": news, "fundamentals": fundamentals}

# ✅ 비동기: 병렬 실행 (1초)
@app.get("/stock/{ticker}")
async def get_stock(ticker: str):
    price, news, fundamentals = await asyncio.gather(
        fetch_price_async(ticker),
        fetch_news_async(ticker),
        fetch_fundamentals_async(ticker)
    )
    return {"price": price, "news": news, "fundamentals": fundamentals}
```

### 2. Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# 캐시 설정
@app.on_event("startup")
async def startup():
    FastAPICache.init(RedisBackend(redis_client), prefix="api-cache")

# 캐시 적용
@app.get("/stock/{ticker}")
@cache(expire=60)  # 1분간 캐시
async def get_stock(ticker: str):
    return await fetch_stock_data(ticker)
```

### 3. Response Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

# Gzip 압축 활성화
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. Pagination

```python
# ❌ 전체 데이터 반환 (느림)
@app.get("/stocks")
async def get_stocks():
    return db.query("SELECT * FROM stocks")

# ✅ 페이지네이션 (빠름)
@app.get("/stocks")
async def get_stocks(skip: int = 0, limit: int = 100):
    return db.query(f"SELECT * FROM stocks LIMIT {limit} OFFSET {skip}")
```

---

## AI 모델 최적화

### 1. Prompt 최적화 (토큰 절감)

```python
# ❌ 비효율적: 긴 프롬프트 (1000 토큰)
prompt = f"""
Analyze the following news article in great detail:
{long_article}
Please provide a comprehensive analysis including...
[많은 지시사항]
"""

# ✅ 효율적: 간결한 프롬프트 (200 토큰)
prompt = f"""
News: {article[:500]}
Sentiment (positive/negative/neutral) & confidence (0-1):
"""
```

### 2. Incremental Update (86% 비용 절감)

```python
# ❌ 전체 재계산
features = await ai.analyze_full_context(ticker, all_news)

# ✅ 증분 업데이트 (새 뉴스만)
new_features = await ai.analyze_incremental(ticker, new_news_only)
```

### 3. Batch Processing

```python
# ❌ 개별 요청 (10개 → 10번 API 호출)
for ticker in tickers:
    await ai.analyze(ticker)

# ✅ 배치 요청 (10개 → 1번 API 호출)
await ai.analyze_batch(tickers)
```

### 4. 모델 선택 최적화

```python
# 간단한 작업: GPT-3.5-turbo ($0.001/1K tokens)
simple_tasks = ["sentiment", "classification"]

# 복잡한 작업: GPT-4 ($0.03/1K tokens)
complex_tasks = ["deep_reasoning", "multi_step_analysis"]
```

---

## 네트워크 최적화

### 1. CDN 사용 (프론트엔드)

```javascript
// CloudFlare CDN 설정
// - 정적 파일 캐싱
// - Global 배포
// - DDoS 방어
```

### 2. Keep-Alive 연결

```python
import httpx

# ❌ 매번 새 연결
for url in urls:
    response = httpx.get(url)

# ✅ 연결 재사용
async with httpx.AsyncClient() as client:
    for url in urls:
        response = await client.get(url)
```

### 3. HTTP/2 활성화

```python
import uvicorn

# HTTP/2 지원
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=443,
    http="h2",
    ssl_keyfile="key.pem",
    ssl_certfile="cert.pem"
)
```

---

## 모니터링 및 측정

### 1. Prometheus 메트릭

```python
from prometheus_client import Counter, Histogram

# API 호출 횟수
api_calls = Counter('api_calls_total', 'Total API calls', ['endpoint'])

# 응답 시간
api_latency = Histogram('api_latency_seconds', 'API latency')

@app.get("/stock/{ticker}")
async def get_stock(ticker: str):
    with api_latency.time():
        api_calls.labels(endpoint="/stock").inc()
        return await fetch_stock_data(ticker)
```

### 2. Grafana 대시보드

```yaml
# grafana/dashboards/performance.json
panels:
  - title: "API Response Time"
    metric: "api_latency_seconds"
    target: "< 10ms"

  - title: "Cache Hit Rate"
    metric: "cache_hits / (cache_hits + cache_misses)"
    target: "> 95%"

  - title: "Database Query Time"
    metric: "db_query_seconds"
    target: "< 50ms"
```

### 3. Slow Query 로그

```sql
-- postgresql.conf
log_min_duration_statement = 1000  # 1초 이상 쿼리 로깅

-- 느린 쿼리 조회
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 성능 벤치마크

### Before Optimization

| 작업 | 시간 | 비용 |
|------|------|------|
| Feature 계산 | 5s | $0.10 |
| API 응답 | 50ms | - |
| DB 쿼리 | 200ms | - |

### After Optimization

| 작업 | 시간 | 비용 | 개선율 |
|------|------|------|--------|
| Feature 계산 | 0.007s | $0.014 | **725배 ↑**, **86% ↓** |
| API 응답 | 3.93ms | - | **12배 ↑** |
| DB 쿼리 | 12ms | - | **16배 ↑** |

---

## 체크리스트

### 일일 점검
- [ ] 캐시 히트율 > 95%
- [ ] API 응답 속도 < 10ms
- [ ] 에러율 < 0.1%

### 주간 점검
- [ ] Slow Query 로그 검토
- [ ] Redis 메모리 사용량 확인
- [ ] AI 비용 트렌드 분석

### 월간 점검
- [ ] 성능 벤치마크 테스트
- [ ] 인덱스 최적화 검토
- [ ] 캐시 전략 재평가

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team
