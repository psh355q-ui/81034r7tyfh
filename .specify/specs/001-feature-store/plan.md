# Implementation Plan: Feature Store

**Branch**: `001-feature-store` | **Date**: 2025-11-08 | **Spec**: [001-feature-store.md](../001-feature-store.md)

## Summary

Build a 2-layer Feature Store (Redis + TimescaleDB) to cache and reuse calculated stock features, achieving 99.95% API cost reduction and 299x speed improvement. This is the foundation infrastructure for all trading strategies and AI analysis.

**Primary Requirement**: Retrieve pre-calculated features in < 5ms (Redis) or < 100ms (TimescaleDB) with > 95% cache hit rate.

**Technical Approach**:
1. Redis as L1 cache (in-memory, 5-minute TTL for real-time, 24-hour for daily)
2. TimescaleDB as L2 cache (persistent, point-in-time queries for backtesting)
3. Lazy computation: calculate only on cache miss
4. Cache warm-up: pre-load top tickers at market open

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `redis>=5.0.0` (async Redis client)
- `asyncpg>=0.29.0` (async PostgreSQL client)
- `pandas>=2.0.0`, `numpy>=1.24.0` (feature calculations)
- `yfinance>=0.2.0` (raw OHLCV data)
- `pydantic>=2.0.0` (data validation)
- `prometheus-client>=0.19.0` (metrics)

**Storage**:
- Redis 7+ (docker: `redis:7-alpine`, 512MB memory limit, maxmemory-policy=allkeys-lru)
- TimescaleDB (docker: `timescale/timescaledb:latest-pg15`, hypertable on `as_of_timestamp`)

**Testing**:
- `pytest>=7.4.0`, `pytest-asyncio>=0.21.0` (async tests)
- `pytest-benchmark>=4.0.0` (performance tests)
- `pytest-redis>=3.0.0` (Redis fixtures)
- `testcontainers>=3.7.0` (Docker-based integration tests)

**Target Platform**: Linux server (Docker Compose), Synology NAS (Docker)

**Project Type**: Single backend service (FastAPI monolith)

**Performance Goals**:
- 1000 feature requests/second
- < 5ms Redis latency (p99)
- < 100ms TimescaleDB latency (p99)
- > 95% cache hit rate after 24h

**Constraints**:
- Must work on Synology DS423+ (4GB RAM, 2 CPU cores)
- Must handle 100-500 tickers without degradation
- Must reduce monthly API cost from $1,000 to < $1

**Scale/Scope**:
- 100 tickers × 7 features × 1000 queries/day = 700k queries/month
- 12 months historical data for backtesting (365 days × 100 tickers)
- 5-year data retention policy

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on `.specify/memory/constitution.md`:

### ✅ Cost Efficiency
- **Requirement**: API cost < $1/month per 100 tickers
- **This Plan**: Feature Store reduces AI API calls from 20,000 → 500/month = $1,000 → $0.51/month ✅
- **Caching Strategy**: 3-layer (Redis → TimescaleDB → AI API) ✅

### ✅ Performance
- **Requirement**: Sub-second analysis latency
- **This Plan**: < 5ms for cached features, < 100ms for DB queries ✅
- **Throughput**: 1000 req/sec (sufficient for real-time trading) ✅

### ✅ Testing Standards
- **Requirement**: TDD, unit tests + integration tests
- **This Plan**: pytest with 80%+ coverage, Docker-based integration tests ✅

### ✅ Simplicity
- **Requirement**: Avoid over-engineering, prefer simple solutions
- **This Plan**:
  - Single monolith (no microservices) ✅
  - File-based async (no complex queues) ✅
  - Built-in Redis/PostgreSQL (no Kafka, no external message broker) ✅

### ⚠️ Risk Management Gates (N/A for infrastructure feature)
- Kill Switch, Stop Loss: Not applicable (this is data layer, not trading logic)
- Monitoring: Prometheus metrics for cache hit rate, latency, cost tracking ✅

**Status**: All gates passed ✅

## Project Structure

### Documentation (this feature)

```text
.specify/specs/001-feature-store/
├── spec.md              # Feature specification (DONE)
├── plan.md              # This file - Implementation plan
├── research.md          # Phase 0: Research existing solutions
├── data-model.md        # Phase 1: Database schema & Redis keys
├── quickstart.md        # Phase 1: Developer getting started guide
├── contracts/           # Phase 1: API contracts (async function signatures)
│   ├── feature_store.py
│   ├── cache_layer.py
│   └── features.py
└── tasks.md             # Phase 2: Breakdown into executable tasks
```

### Source Code (repository root)

```text
ai-trading-system/
├── backend/
│   ├── data/
│   │   ├── feature_store/
│   │   │   ├── __init__.py
│   │   │   ├── store.py              # FeatureStore main class
│   │   │   ├── cache_layer.py        # RedisCache + TimescaleCache
│   │   │   ├── features.py           # Feature calculation (ret_5d, vol_20d, etc.)
│   │   │   ├── warm_up.py            # Cache pre-warming at market open
│   │   │   └── metrics.py            # Prometheus metrics
│   │   ├── collectors/
│   │   │   ├── __init__.py
│   │   │   └── yahoo_collector.py    # Fetch raw OHLCV from Yahoo Finance
│   │   └── models/
│   │       ├── __init__.py
│   │       └── feature.py            # Pydantic models (Feature, FeatureRequest)
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_features.py      # Test feature calculations
│   │   │   ├── test_cache_layer.py   # Test Redis/DB operations
│   │   │   └── test_store.py         # Test FeatureStore logic
│   │   ├── integration/
│   │   │   ├── test_feature_store_integration.py  # Full flow with Docker
│   │   │   └── test_point_in_time.py  # Backtest scenarios
│   │   └── performance/
│   │       └── test_benchmarks.py    # Load tests (1000 req/sec)
│   ├── alembic/                      # Database migrations
│   │   ├── versions/
│   │   │   └── 001_create_features_table.py
│   │   └── env.py
│   ├── pyproject.toml                # Dependencies (Poetry/uv)
│   └── pytest.ini                    # Pytest config
├── docker-compose.yml                # Redis + TimescaleDB services
├── .env.example                      # Environment variables template
└── README.md
```

**Structure Decision**: Single backend project (Option 1) because this is a monolithic API service. Frontend will be added in later phase. No need for separate mobile/API split.

## Complexity Tracking

No Constitution violations. All design choices align with project principles:
- Single monolith (not multiple services)
- Direct Redis/PostgreSQL access (no abstraction layers beyond cache_layer.py)
- Standard Python patterns (no custom frameworks)

## Phase 0: Research

### Questions to Answer

1. **Redis Best Practices**:
   - What's the optimal `maxmemory-policy` for feature caching? (LRU vs LFU)
   - Should we use Redis Hashes or Strings for feature storage?
   - What's the memory overhead per key-value pair?
   - How to handle Redis connection pooling in async Python?

2. **TimescaleDB Optimization**:
   - How to create hypertables for time-series data?
   - What indexes are needed for point-in-time queries?
   - How to partition data (by ticker vs by time)?
   - Compression settings for historical data?

3. **Feature Calculation Patterns**:
   - Should features be calculated in Python (pandas) or SQL (window functions)?
   - How to handle missing data (forward-fill, interpolate, or NaN)?
   - How to vectorize calculations for performance?

4. **Concurrency & Race Conditions**:
   - How to prevent cache stampede (multiple processes computing same feature)?
   - Redis distributed locks (SETNX) vs asyncio locks?
   - How to handle stale reads during cache refresh?

5. **Cost Tracking**:
   - How to attribute API costs to specific features/tickers?
   - What Prometheus metrics to expose?
   - How to estimate monthly costs in real-time?

### Research Plan

1. **Redis Investigation** (2 hours)
   - Read: Redis Patterns documentation (https://redis.io/docs/manual/patterns/)
   - Read: redis-py async API docs
   - Experiment: Benchmark String vs Hash storage with 1M keys
   - Deliverable: Decision on key schema and maxmemory-policy

2. **TimescaleDB Investigation** (2 hours)
   - Read: TimescaleDB Best Practices (https://docs.timescale.com/)
   - Read: asyncpg documentation
   - Experiment: Create hypertable, test query performance with 1M rows
   - Deliverable: SQL schema with indexes

3. **Python Async Patterns** (1 hour)
   - Read: asyncio best practices for database pooling
   - Experiment: Test connection pool sizes (10, 50, 100 connections)
   - Deliverable: Recommended pool size

4. **Distributed Lock Research** (1 hour)
   - Read: Redlock algorithm (https://redis.io/topics/distlock)
   - Alternative: asyncio.Lock (in-process only, simpler)
   - Deliverable: Decision on lock strategy

5. **Benchmark Existing Systems** (optional)
   - Look at: Feast (feature store), Tecton (feature platform)
   - Goal: Learn from their API design, not copy implementation

**Total Research Time**: ~6 hours

### Output: research.md

Document findings, decisions, and code snippets from experiments.

## Phase 1: Design

### Data Model Design

**Output**: `data-model.md` containing:

1. **TimescaleDB Schema**:
```sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    feature_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION,
    as_of_timestamp TIMESTAMPTZ NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL,
    version INTEGER DEFAULT 1,
    metadata JSONB,
    UNIQUE(ticker, feature_name, as_of_timestamp, version)
);

SELECT create_hypertable('features', 'as_of_timestamp');
CREATE INDEX idx_features_lookup ON features(ticker, feature_name, as_of_timestamp DESC);
```

2. **Redis Key Schema**:
```
feature:{ticker}:{feature_name}:{as_of_date} = {value}
TTL: 300 seconds (5 min) for intraday, 86400 (24h) for daily
```

3. **Pydantic Models**:
```python
class Feature(BaseModel):
    ticker: str
    feature_name: str
    value: float | None
    as_of_timestamp: datetime
    calculated_at: datetime
    version: int = 1

class FeatureRequest(BaseModel):
    ticker: str
    feature_names: list[str]
    as_of: datetime | None = None  # None = latest
```

### API Contracts

**Output**: `contracts/*.py` containing function signatures:

```python
# contracts/feature_store.py
class FeatureStore:
    async def get_features(
        self,
        ticker: str,
        feature_names: list[str],
        as_of: datetime | None = None
    ) -> dict[str, float | None]:
        """Retrieve features with 2-layer caching."""
        ...

    async def compute_feature(
        self,
        ticker: str,
        feature_name: str,
        as_of: datetime
    ) -> float:
        """Compute feature from raw data."""
        ...

    async def warm_cache(self, tickers: list[str]) -> None:
        """Pre-load features into Redis."""
        ...

# contracts/cache_layer.py
class CacheLayer(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        ...

# contracts/features.py
async def calculate_return(
    ticker: str,
    period_days: int,
    as_of: datetime
) -> float:
    """Calculate return over N days."""
    ...

async def calculate_volatility(
    ticker: str,
    window_days: int,
    as_of: datetime
) -> float:
    """Calculate rolling volatility."""
    ...
```

### Quickstart Guide

**Output**: `quickstart.md` containing:
- How to run Feature Store locally (Docker Compose)
- How to populate sample data
- How to query features via Python REPL
- Example: "Get AAPL features in < 5ms"

## Phase 2: Task Breakdown

**Output**: `tasks.md` (created by `/speckit.tasks` command)

Tasks will be prioritized as:
1. **Critical Path** (blocks everything else):
   - Docker Compose setup (Redis + TimescaleDB)
   - Database schema creation (Alembic migration)
   - Redis connection pool setup
   - Basic get/set operations

2. **Feature Calculation** (can develop in parallel):
   - Implement `calculate_return()`
   - Implement `calculate_volatility()`
   - Implement `calculate_momentum()`
   - Unit tests for each

3. **FeatureStore Logic** (depends on #1 and #2):
   - 2-layer cache retrieval
   - Lazy computation on cache miss
   - Point-in-time queries
   - Integration tests

4. **Optimization** (last):
   - Cache warm-up at market open
   - Distributed lock for cache stampede
   - Prometheus metrics
   - Performance benchmarks

**Estimated Total Time**: 2 weeks (10 working days)

## Testing Strategy

### Unit Tests (test/unit/)

**Coverage Target**: 80%+

- `test_features.py`: Test each feature calculation function
  - Input: Historical OHLCV data (mock)
  - Output: Expected feature value (compare against spreadsheet)
  - Edge cases: Missing data, zero volume, negative prices

- `test_cache_layer.py`: Test Redis and TimescaleDB operations
  - Mock Redis/PostgreSQL connections
  - Test TTL expiration
  - Test concurrent access (asyncio.gather)

- `test_store.py`: Test FeatureStore logic
  - Mock CacheLayer and feature calculations
  - Test cache hit/miss paths
  - Test error handling (DB down, timeout)

### Integration Tests (test/integration/)

**Dependencies**: Docker Compose must be running (Redis + TimescaleDB)

- `test_feature_store_integration.py`: Full flow
  - Start: Empty cache
  - Action: Request feature (cache miss → compute → save → return)
  - Verify: Feature exists in Redis and TimescaleDB
  - Action: Request same feature (cache hit)
  - Verify: Response time < 5ms

- `test_point_in_time.py`: Backtest scenarios
  - Populate DB with historical features (2024-01-01 to 2024-12-31)
  - Query: `get_features('AAPL', ['ret_5d'], as_of=datetime(2024, 6, 15))`
  - Verify: Only data before 2024-06-15 used in calculation

### Performance Tests (test/performance/)

- `test_benchmarks.py`: Load testing
  - Scenario: 1000 requests/sec for 60 seconds
  - Measure: p50, p95, p99 latencies
  - Verify: p99 < 10ms (cache hit), p99 < 200ms (cache miss)
  - Verify: No errors, no timeouts

**Tools**: `pytest-benchmark`, `locust` (optional)

### Cost Tests

- Run for 24 hours in staging
- Mock: 100 tickers, 7 features each, 1000 queries/hour
- Measure: Total API calls, DB queries, cache hits
- Calculate: Cost per query
- Verify: < $0.02/day

## Monitoring & Observability

### Prometheus Metrics

```python
# Counters
feature_requests_total{ticker, feature_name, cache_layer}
feature_computation_total{feature_name}
feature_errors_total{error_type}

# Histograms
feature_latency_seconds{operation}  # get, compute, save
cache_hit_rate{cache_layer}  # redis, timescaledb

# Gauges
cache_size_bytes{cache_layer}
active_tickers_count
monthly_cost_usd
```

### Grafana Dashboard

**Panels**:
1. Cache hit rate over time (target: > 95%)
2. Latency distribution (p50, p95, p99)
3. Cost tracking (cumulative monthly cost, cost per query)
4. Error rate (alerts if > 1%)
5. Top 10 most requested features
6. Cache memory usage (Redis)

## Deployment Plan

### Week 1: Foundation
- Day 1-2: Docker Compose setup, database schema, Redis connection pool
- Day 3-4: Feature calculation functions (ret_5d, vol_20d, mom_20d)
- Day 5: Unit tests for feature calculations

### Week 2: Integration
- Day 6-7: FeatureStore class with 2-layer caching
- Day 8: Point-in-time queries for backtesting
- Day 9: Integration tests, cache warm-up
- Day 10: Performance optimization, monitoring dashboard

### Rollout to Production
1. **Staging**: Run for 24 hours with synthetic load
2. **Canary**: Enable for 10 tickers (top liquid stocks)
3. **Full**: Enable for all 100 tickers
4. **Monitor**: Grafana dashboard for 7 days

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Redis OOM crash | High (system down) | Medium | Monitor memory, tune maxmemory-policy, add alerts |
| TimescaleDB slow queries | Medium (latency spike) | Low | Add indexes, use EXPLAIN ANALYZE, consider partitioning |
| Cache stampede | Medium (CPU spike) | Medium | Use Redis distributed lock (SETNX) |
| Data corruption | High (wrong trades) | Low | Thorough unit tests, compare against known-good values |
| Feature calculation bug | High (wrong trades) | Medium | TDD, compare against spreadsheet, add integration tests |

## Success Criteria (from Spec)

- **SC-001**: Redis cache hit rate > 95% in production ✅ (monitor via Prometheus)
- **SC-002**: Average latency < 10ms ✅ (pytest-benchmark)
- **SC-003**: Cost reduction 99.96% ✅ (cost tracking dashboard)
- **SC-004**: Serve 700k queries/month ✅ (load test 1000 req/sec)
- **SC-005**: Zero data corruption ✅ (deterministic backtest results)
- **SC-006**: Graceful degradation ✅ (fallback to TimescaleDB if Redis down)

## Dependencies & Blockers

### External Dependencies
- ✅ Redis 7+ (available via Docker)
- ✅ TimescaleDB (available via Docker)
- ✅ Yahoo Finance API (free, no API key)

### Internal Dependencies
- ⏳ Data ingestion pipeline (out of scope for this feature, can mock for now)
- ⏳ OHLCV data in TimescaleDB (can use yfinance to backfill manually)

### Blockers
- None (feature is self-contained)

## Next Steps

1. ✅ Review this plan with stakeholders
2. ⏳ Run Phase 0 research (6 hours)
3. ⏳ Complete Phase 1 design (data-model.md, contracts/, quickstart.md)
4. ⏳ Generate tasks.md via `/speckit.tasks`
5. ⏳ Start implementation via `/speckit.implement`

---

**Ready for Review** 🚀

Questions? Clarifications needed? Use `/speckit.clarify` to ask.
