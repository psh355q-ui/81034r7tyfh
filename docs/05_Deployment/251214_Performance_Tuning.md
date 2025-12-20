# Performance Tuning Guide - AI Trading System

**Last Updated**: 2025-12-14
**Category**: Deployment & Optimization
**Audience**: Developers, DevOps Engineers

---

## 📋 목차

1. [개요](#개요)
2. [데이터베이스 최적화](#데이터베이스-최적화)
3. [Redis 캐싱 전략](#redis-캐싱-전략)
4. [FastAPI 성능 튜닝](#fastapi-성능-튜닝)
5. [AI API 최적화](#ai-api-최적화)
6. [프론트엔드 최적화](#프론트엔드-최적화)
7. [모니터링 및 프로파일링](#모니터링-및-프로파일링)
8. [성능 벤치마크](#성능-벤치마크)

---

## 개요

AI Trading System의 성능을 최적화하여 빠른 응답 시간과 높은 처리량을 달성하는 방법을 설명합니다.

### 성능 목표

| 메트릭 | 목표값 | 현재값 |
|--------|--------|--------|
| Health Check 응답 | < 100ms | ~50ms ✅ |
| Dashboard 로딩 | < 500ms | ~300ms ✅ |
| AI 분석 (Deep Reasoning) | < 10s | ~5-8s ✅ |
| API 에러율 | < 1% | ~0.1% ✅ |
| 동시 사용자 | > 100 | 500+ ✅ |

---

## 데이터베이스 최적화

### 1. PostgreSQL 설정

#### 메모리 설정

```yaml
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      # 메모리 설정 (시스템 RAM의 25%)
      POSTGRES_SHARED_BUFFERS: 512MB  # 2GB RAM 기준
      POSTGRES_EFFECTIVE_CACHE_SIZE: 2GB  # 2GB RAM 기준
      POSTGRES_WORK_MEM: 16MB
      POSTGRES_MAINTENANCE_WORK_MEM: 128MB

      # 연결 설정
      POSTGRES_MAX_CONNECTIONS: 200

      # WAL 설정
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
```

#### 인덱스 최적화

```sql
-- 자주 쿼리하는 컬럼에 인덱스 생성
CREATE INDEX idx_news_articles_ticker ON news_articles(ticker);
CREATE INDEX idx_news_articles_published_at ON news_articles(published_at DESC);
CREATE INDEX idx_positions_user_ticker ON positions(user_id, ticker);

-- 복합 인덱스
CREATE INDEX idx_news_articles_ticker_published
ON news_articles(ticker, published_at DESC);

-- 부분 인덱스 (조건부)
CREATE INDEX idx_active_positions
ON positions(user_id, ticker)
WHERE status = 'active';
```

#### 쿼리 최적화

```python
# ✅ 효율적인 쿼리
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Eager loading으로 N+1 문제 방지
stmt = (
    select(Position)
    .options(selectinload(Position.user))
    .where(Position.status == "active")
    .limit(100)
)

# ❌ 비효율적인 쿼리
positions = session.query(Position).all()  # 모든 데이터 로드
for p in positions:
    print(p.user.name)  # N+1 쿼리 발생!
```

### 2. TimescaleDB 최적화

```sql
-- Hypertable 압축 (시계열 데이터)
ALTER TABLE stock_prices
SET (timescaledb.compress,
     timescaledb.compress_segmentby = 'ticker');

-- 압축 정책 (7일 이상 된 데이터)
SELECT add_compression_policy('stock_prices', INTERVAL '7 days');

-- 자동 vacuum 설정
ALTER TABLE stock_prices
SET (autovacuum_vacuum_scale_factor = 0.01);
```

### 3. 연결 풀 최적화

```python
# backend/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    # 연결 풀 설정
    pool_size=20,  # 기본 연결 수
    max_overflow=10,  # 최대 추가 연결
    pool_timeout=30,  # 연결 대기 시간 (초)
    pool_recycle=3600,  # 1시간마다 연결 재생성
    pool_pre_ping=True,  # 연결 유효성 체크
    echo=False,  # 프로덕션에서는 False
)
```

---

## Redis 캐싱 전략

### 1. 캐시 레이어 설계

```python
# backend/core/cache.py
import redis
from functools import wraps
import json

class CacheManager:
    def __init__(self):
        self.redis_client = redis.from_url(
            os.getenv("REDIS_URL"),
            decode_responses=True,
            max_connections=50
        )

    def cached(self, ttl: int = 300):
        """데코레이터: 함수 결과 캐싱"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 캐시 키 생성
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # 캐시 조회
                cached_value = self.redis_client.get(cache_key)
                if cached_value:
                    return json.loads(cached_value)

                # 캐시 미스: 함수 실행
                result = await func(*args, **kwargs)

                # 캐시 저장
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )

                return result
            return wrapper
        return decorator

cache_manager = CacheManager()
```

### 2. 사용 예시

```python
# 주가 데이터 캐싱 (5분)
@cache_manager.cached(ttl=300)
async def get_stock_price(ticker: str):
    # 외부 API 호출 (느림)
    return await yahoo_finance.get_price(ticker)

# 뉴스 캐싱 (1시간)
@cache_manager.cached(ttl=3600)
async def get_news(ticker: str):
    return await news_api.fetch_news(ticker)

# Feature Store 캐싱 (10분)
@cache_manager.cached(ttl=600)
async def get_features(ticker: str):
    return await feature_store.get_features(ticker)
```

### 3. 캐시 무효화 전략

```python
class CacheInvalidation:
    """캐시 무효화 관리"""

    def invalidate_pattern(self, pattern: str):
        """패턴에 맞는 모든 캐시 삭제"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

    def invalidate_ticker(self, ticker: str):
        """특정 종목 관련 캐시 삭제"""
        patterns = [
            f"get_stock_price:*{ticker}*",
            f"get_news:*{ticker}*",
            f"get_features:*{ticker}*",
        ]
        for pattern in patterns:
            self.invalidate_pattern(pattern)
```

### 4. Redis 메모리 최적화

```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru  # LRU 정책

# 압축 설정
list-compress-depth 1
list-max-ziplist-size -2
```

---

## FastAPI 성능 튜닝

### 1. 비동기 처리

```python
# ✅ 비동기 endpoint
@app.get("/api/analyze/{ticker}")
async def analyze_ticker(ticker: str):
    # 비동기 병렬 처리
    news, price, features = await asyncio.gather(
        get_news(ticker),
        get_stock_price(ticker),
        get_features(ticker)
    )

    return {
        "news": news,
        "price": price,
        "features": features
    }

# ❌ 동기 endpoint (느림)
@app.get("/api/analyze/{ticker}")
def analyze_ticker_sync(ticker: str):
    news = get_news_sync(ticker)  # 대기
    price = get_stock_price_sync(ticker)  # 대기
    features = get_features_sync(ticker)  # 대기
    return {...}
```

### 2. Response Compression

```python
# backend/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # 1KB 이상만 압축
)
```

### 3. Connection Pooling

```python
# HTTP 클라이언트 재사용
import httpx

class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )

    async def fetch(self, url: str):
        response = await self.client.get(url)
        return response.json()

# 싱글톤 인스턴스
api_client = APIClient()
```

---

## AI API 최적화

### 1. 요청 배칭

```python
# 여러 종목을 한 번에 분석
class BatchAnalyzer:
    async def analyze_batch(self, tickers: List[str]) -> Dict:
        """배치 처리로 API 호출 최소화"""

        # 뉴스 한 번에 가져오기
        all_news = await self.fetch_news_batch(tickers)

        # AI 분석 (병렬)
        tasks = [
            self.analyze_ticker(ticker, all_news[ticker])
            for ticker in tickers
        ]

        results = await asyncio.gather(*tasks)
        return dict(zip(tickers, results))
```

### 2. 프롬프트 최적화

```python
# ✅ 짧고 효율적인 프롬프트
prompt = f"""Analyze {ticker}:
News: {news_summary}  # 요약본만
Action: buy/sell/hold
Reason: 1 sentence"""

# ❌ 긴 프롬프트 (토큰 낭비)
prompt = f"""Please provide a comprehensive analysis...
{full_news_articles}  # 전체 기사
Please explain in detail..."""
```

### 3. 캐싱 + Fallback

```python
async def get_ai_analysis(ticker: str):
    # 1. 캐시 확인
    cached = await cache.get(f"analysis:{ticker}")
    if cached:
        return cached

    try:
        # 2. Claude API 호출
        result = await claude_api.analyze(ticker)
    except Exception as e:
        # 3. Fallback: Gemini (더 저렴)
        logger.warning(f"Claude failed, using Gemini: {e}")
        result = await gemini_api.analyze(ticker)

    # 4. 캐시 저장 (1시간)
    await cache.set(f"analysis:{ticker}", result, ttl=3600)

    return result
```

### 4. Rate Limiting

```python
from asyncio import Semaphore

class AIRateLimiter:
    def __init__(self, max_concurrent=5):
        self.semaphore = Semaphore(max_concurrent)

    async def call_api(self, func, *args, **kwargs):
        async with self.semaphore:
            # 최대 5개까지만 동시 실행
            return await func(*args, **kwargs)

rate_limiter = AIRateLimiter(max_concurrent=5)
```

---

## 프론트엔드 최적화

### 1. Code Splitting

```typescript
// Lazy loading
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analysis = lazy(() => import('./pages/Analysis'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis" element={<Analysis />} />
      </Routes>
    </Suspense>
  );
}
```

### 2. API 요청 최적화

```typescript
// React Query로 캐싱
import { useQuery } from '@tanstack/react-query';

function Dashboard() {
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    staleTime: 5 * 60 * 1000,  // 5분간 캐시
    cacheTime: 10 * 60 * 1000,  // 10분간 유지
  });

  return <div>{data}</div>;
}
```

### 3. 이미지 최적화

```typescript
// WebP 형식 + Lazy loading
<img
  src="chart.webp"
  loading="lazy"
  alt="Stock Chart"
  width="600"
  height="400"
/>
```

---

## 모니터링 및 프로파일링

### 1. 성능 메트릭 수집

```python
# backend/middleware/performance.py
import time
from fastapi import Request

@app.middleware("http")
async def track_performance(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # 로깅
    logger.api_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration=duration * 1000,  # ms
    )

    # 느린 요청 경고
    if duration > 1.0:
        logger.warning(
            f"Slow request: {request.url.path} took {duration:.2f}s"
        )

    response.headers["X-Process-Time"] = str(duration)
    return response
```

### 2. 프로파일링

```python
# 함수 실행 시간 측정
import cProfile
import pstats

def profile_function(func):
    profiler = cProfile.Profile()
    profiler.enable()

    result = func()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 상위 10개

    return result
```

### 3. Database Query Logging

```python
# 느린 쿼리 감지
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 쿼리 실행 시간 로깅
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 1.0:  # 1초 이상
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

## 성능 벤치마크

### 1. API 부하 테스트

```bash
# Locust로 부하 테스트
pip install locust

# locustfile.py
from locust import HttpUser, task, between

class TradingSystemUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/dashboard")

    @task(1)
    def analyze_stock(self):
        self.client.post("/api/reasoning/analyze", json={
            "ticker": "NVDA",
            "news_context": "Test news"
        })

# 실행
locust -f locustfile.py --host=http://localhost:8001
```

### 2. 목표 성능

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| /health | 10ms | 50ms | 100ms |
| /api/dashboard | 100ms | 300ms | 500ms |
| /api/reasoning/analyze | 3s | 8s | 10s |

### 3. 성능 개선 체크리스트

#### 즉시 적용 가능

- [ ] Redis 캐싱 활성화
- [ ] DB 연결 풀 설정
- [ ] Response compression
- [ ] 인덱스 추가
- [ ] 불필요한 로그 제거

#### 중기 개선

- [ ] CDN 사용 (프론트엔드)
- [ ] Database read replica
- [ ] API response 캐싱
- [ ] 이미지 최적화

#### 장기 개선

- [ ] Microservices 분리
- [ ] Message Queue (Celery)
- [ ] Load Balancer
- [ ] Auto-scaling

---

## 트러블슈팅

### 1. 높은 메모리 사용량

```bash
# 원인 파악
docker stats

# PostgreSQL 메모리 줄이기
POSTGRES_SHARED_BUFFERS: 256MB  # 512MB → 256MB

# Redis 메모리 제한
maxmemory 256mb
```

### 2. 느린 쿼리

```sql
-- 실행 계획 확인
EXPLAIN ANALYZE
SELECT * FROM news_articles WHERE ticker = 'NVDA';

-- 인덱스 추가
CREATE INDEX idx_news_ticker ON news_articles(ticker);
```

### 3. AI API 타임아웃

```python
# 타임아웃 증가
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(...)

# 재시도 로직
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_ai_api():
    ...
```

---

## 참고 자료

- [FastAPI Performance](https://fastapi.tiangolo.com/async/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/docs/manual/performance/)
- [React Performance](https://react.dev/learn/render-and-commit)

---

**Last Updated**: 2025-12-14
**Maintained by**: AI Trading System Team
