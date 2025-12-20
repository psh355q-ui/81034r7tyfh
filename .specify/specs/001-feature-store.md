# Feature Specification: Feature Store

**Feature Branch**: `001-feature-store`
**Created**: 2025-11-08
**Status**: Draft
**Priority**: P1 (Foundation)

## Overview

2-Layer Feature Store (Redis + TimescaleDB) for caching and reusing calculated stock features. This is the foundation infrastructure that enables 99.95% API cost reduction and 299x speed improvement (3 seconds → 10ms).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast Feature Retrieval (Priority: P1)

As a trading algorithm, I need to retrieve pre-calculated stock features in under 5ms so that I can make real-time trading decisions without delays.

**Why this priority**: Real-time trading requires sub-second response times. This is the core value proposition of the Feature Store - speed and cost efficiency.

**Independent Test**: Can be fully tested by calling `get_features(ticker='AAPL', as_of=datetime.now(), feature_names=['ret_5d'])` and measuring response time < 5ms for cached features.

**Acceptance Scenarios**:

1. **Given** feature exists in Redis cache, **When** system requests feature, **Then** feature is returned in < 5ms
2. **Given** feature exists in TimescaleDB but not Redis, **When** system requests feature, **Then** feature is returned in < 100ms and cached to Redis
3. **Given** multiple features requested for same ticker, **When** batch request made, **Then** all features returned in single round-trip

---

### User Story 2 - Automatic Feature Computation (Priority: P1)

As a trading system, I need the Feature Store to automatically compute missing features so that I don't have to implement calculation logic in multiple places.

**Why this priority**: DRY principle - feature calculation should happen once and be reused. Critical for consistency and maintainability.

**Independent Test**: Request a feature that doesn't exist in cache, verify it's computed from raw data, saved to both layers, and returned correctly.

**Acceptance Scenarios**:

1. **Given** feature not in cache or DB, **When** system requests feature, **Then** feature is computed from raw data, saved to both layers, and returned
2. **Given** raw data is updated, **When** TTL expires, **Then** feature is recomputed with fresh data
3. **Given** computation fails, **When** retry attempted, **Then** system falls back to stale cached value or returns error gracefully

---

### User Story 3 - Point-in-Time Feature Access (Priority: P2)

As a backtesting engine, I need to retrieve features as they existed at a specific historical timestamp so that I can avoid look-ahead bias and get accurate backtest results.

**Why this priority**: Essential for reliable backtesting. Without this, backtest results will be misleading and unreliable.

**Independent Test**: Request features with `as_of=datetime(2024, 1, 1)` and verify that only data available before that date is used in calculations.

**Acceptance Scenarios**:

1. **Given** historical date specified, **When** feature requested, **Then** only data available before that date is used
2. **Given** feature was updated after as_of date, **When** feature requested, **Then** old version is returned from TimescaleDB
3. **Given** backtest runs over date range, **When** features requested sequentially, **Then** no look-ahead bias occurs

---

### User Story 4 - High Cache Hit Rate (Priority: P1)

As a cost-conscious developer, I need cache hit rate > 95% so that I minimize expensive AI API calls and database queries.

**Why this priority**: This is the primary cost-saving mechanism. Without high cache hit rate, the system loses its cost advantage.

**Independent Test**: Run system for 24 hours, measure (cache hits / total requests) > 0.95.

**Acceptance Scenarios**:

1. **Given** same ticker queried multiple times within TTL, **When** features requested, **Then** cache returns result without recomputation
2. **Given** popular tickers (top 100), **When** market opens, **Then** cache is pre-warmed with their features
3. **Given** cache eviction occurs, **When** feature re-requested, **Then** it's reloaded from TimescaleDB (not recomputed)

---

### User Story 5 - Feature Versioning (Priority: P3)

As a data scientist, I need to track which version of feature calculation logic was used so that I can reproduce past analyses and compare model performance across versions.

**Why this priority**: Important for ML governance and debugging, but not critical for MVP.

**Independent Test**: Change feature calculation logic, verify old and new versions coexist, and can be queried separately.

**Acceptance Scenarios**:

1. **Given** feature calculation logic changed, **When** new version deployed, **Then** old cached values remain valid until TTL
2. **Given** multiple versions exist, **When** specific version requested, **Then** correct version is returned
3. **Given** version not specified, **When** feature requested, **Then** latest version is returned by default

---

### Edge Cases

- What happens when Redis is down? (Fallback to TimescaleDB, slower but functional)
- What happens when both Redis and TimescaleDB are down? (Return error, trigger alert)
- What happens when feature computation times out? (Return cached stale value if available, otherwise error)
- What happens when TTL=0 (disable cache)? (Always recompute from DB)
- What happens when ticker doesn't exist? (Return empty result with clear error message)
- What happens with concurrent requests for same missing feature? (Use lock to ensure only one computation happens)
- What happens when cache is full? (LRU eviction policy, evict least recently used)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support 2-layer caching: Redis (online, < 5ms) and TimescaleDB (offline, < 100ms)
- **FR-002**: System MUST compute these standard features: ret_5d, ret_20d, ret_60d, vol_20d, vol_60d, mom_20d, mom_60d
- **FR-003**: System MUST support point-in-time queries (as_of parameter) to avoid look-ahead bias in backtesting
- **FR-004**: System MUST batch-retrieve multiple features in a single call to minimize network round-trips
- **FR-005**: System MUST track cache hit/miss metrics for monitoring cost efficiency
- **FR-006**: System MUST support configurable TTL per feature type (default 5 minutes for intraday, 24 hours for daily)
- **FR-007**: System MUST automatically refresh expired cache entries on next access
- **FR-008**: System MUST support concurrent access from multiple processes/threads safely
- **FR-009**: System MUST log all cache misses and computation costs for cost tracking
- **FR-010**: System MUST gracefully handle missing raw data by returning null and logging warning

### Non-Functional Requirements

- **NFR-001**: Latency - Redis retrieval MUST complete in < 5ms (p99)
- **NFR-002**: Latency - TimescaleDB retrieval MUST complete in < 100ms (p99)
- **NFR-003**: Throughput - System MUST handle 1000 feature requests per second
- **NFR-004**: Cache Hit Rate - System MUST achieve > 95% cache hit rate in production
- **NFR-005**: Reliability - System MUST have 99.9% uptime (allow Redis restarts)
- **NFR-006**: Cost Efficiency - System MUST reduce API calls by 97.5% (20,000 → 500 calls/month)
- **NFR-007**: Scalability - System MUST support 100-500 tickers without performance degradation
- **NFR-008**: Observability - System MUST expose Prometheus metrics for cache hit rate, latency, cost tracking

### Key Entities

- **Feature**: A calculated metric for a ticker at a specific timestamp (e.g., "AAPL ret_5d on 2024-01-15 = 0.05")
  - Attributes: ticker, feature_name, value, as_of_timestamp, calculated_at, version, ttl

- **FeatureDefinition**: Metadata about how to compute a feature
  - Attributes: name, description, calculation_logic, dependencies (raw data required), ttl, version

- **CacheLayer**: Abstract interface for Redis and TimescaleDB
  - Methods: get(key), set(key, value, ttl), exists(key), delete(key)

- **RawDataSource**: Yahoo Finance, KIS API, etc.
  - Provides: OHLCV data, fundamentals, news/events

### Data Model (TimescaleDB)

```sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    feature_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION,
    as_of_timestamp TIMESTAMPTZ NOT NULL,  -- Point-in-time
    calculated_at TIMESTAMPTZ NOT NULL,    -- When computed
    version INTEGER DEFAULT 1,
    metadata JSONB,  -- Extra context
    UNIQUE(ticker, feature_name, as_of_timestamp, version)
);

-- Hypertable for time-series optimization
SELECT create_hypertable('features', 'as_of_timestamp');

-- Index for fast lookups
CREATE INDEX idx_features_lookup ON features(ticker, feature_name, as_of_timestamp DESC);
```

### Redis Key Schema

```
feature:{ticker}:{feature_name}:{as_of_date} = {value}
Example: feature:AAPL:ret_5d:2024-11-08 = 0.0523

TTL: 300 seconds (5 minutes) for intraday, 86400 seconds (24 hours) for daily
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Redis cache hit rate > 95% in production after 24 hours of operation
- **SC-002**: Average feature retrieval latency < 10ms (including cache misses that hit DB)
- **SC-003**: API cost reduction from $50/day (without cache) to $0.02/day (with cache) = 99.96% reduction
- **SC-004**: System successfully serves 100 tickers with 7 features each, 1000 queries/day = 700,000 queries/month
- **SC-005**: Zero data corruption - backtests produce identical results when re-run with same parameters
- **SC-006**: Graceful degradation - if Redis fails, system continues working with TimescaleDB (slower but functional)
- **SC-007**: Cache warm-up completes in < 5 minutes for top 100 tickers at market open
- **SC-008**: Cost tracking dashboard shows live cumulative costs and cost-per-query metrics

### Performance Benchmarks (target vs baseline)

| Metric | Baseline (No Cache) | Target (With Cache) | Improvement |
|--------|---------------------|---------------------|-------------|
| Feature retrieval latency | 3 seconds (AI API) | 10ms | 299x faster |
| Monthly API calls | 20,000 | 500 | 97.5% reduction |
| Monthly cost | $1,000 | $0.51 | 99.95% reduction |
| Queries per second | 10 | 1,000 | 100x throughput |

## Out of Scope (Phase 1)

- Feature engineering / discovery (manual definitions only)
- Real-time streaming features (batch only)
- Distributed Redis cluster (single instance OK for 100 tickers)
- Feature drift detection
- Automated feature backfilling (manual backfill only)
- Multi-region replication

## Dependencies

### External Services

- **Redis 7+**: In-memory cache (docker: redis:7-alpine)
- **TimescaleDB**: Time-series PostgreSQL extension (docker: timescale/timescaledb:latest-pg15)
- **Yahoo Finance API**: Raw OHLCV data (free tier, no API key needed)

### Internal Dependencies

- Data ingestion pipeline must populate TimescaleDB with OHLCV data
- Feature calculation functions must be implemented (ret_5d, vol_20d, etc.)

## Implementation Notes

### Technology Stack

- Python 3.11+
- Redis client: `redis-py`
- PostgreSQL client: `asyncpg` or `psycopg3`
- Data processing: `pandas`, `numpy`

### Code Structure

```
backend/
├── data/
│   ├── feature_store/
│   │   ├── __init__.py
│   │   ├── store.py              # Main FeatureStore class
│   │   ├── cache_layer.py        # Redis + TimescaleDB abstraction
│   │   ├── features.py           # Feature calculation logic
│   │   └── metrics.py            # Prometheus metrics
│   └── collectors/
│       └── yahoo_collector.py    # Fetch raw OHLCV data
└── tests/
    └── test_feature_store.py     # Unit + integration tests
```

### Key Classes

```python
class FeatureStore:
    async def get_features(
        self,
        ticker: str,
        as_of: datetime,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Retrieve features with 2-layer caching."""

    async def compute_feature(
        self,
        ticker: str,
        feature_name: str,
        as_of: datetime
    ) -> float:
        """Compute feature from raw data."""

    async def warm_cache(self, tickers: List[str]):
        """Pre-load popular tickers into Redis."""
```

## Testing Strategy

### Unit Tests

- Test each feature calculation function in isolation
- Test cache hit/miss logic
- Test TTL expiration and refresh
- Test error handling (missing data, timeout, etc.)

### Integration Tests

- Test full flow: cache miss → DB lookup → compute → cache save → return
- Test point-in-time queries with historical data
- Test concurrent access (use pytest-asyncio with multiple tasks)
- Test graceful degradation (Redis down, DB down)

### Performance Tests

- Load test: 1000 requests/sec for 60 seconds
- Measure p50, p95, p99 latencies
- Verify cache hit rate > 95% after warm-up

### Cost Tests

- Run for 24 hours
- Count total API calls, DB queries, cache hits
- Calculate cost-per-query
- Verify < $0.02/day for 100 tickers

## Rollout Plan

1. **Week 1**: Redis + TimescaleDB setup, basic get/set operations
2. **Week 2**: Feature calculation logic (7 standard features), unit tests
3. **Week 3**: Point-in-time queries, cache warm-up, integration tests
4. **Week 4**: Performance optimization, monitoring dashboard, production deployment

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis OOM (out of memory) | Cache evictions, lower hit rate | Monitor memory, tune maxmemory-policy, add more RAM |
| TimescaleDB slow queries | Latency spike > 100ms | Add indexes, use EXPLAIN ANALYZE, consider partitioning |
| Stale cache after data correction | Incorrect features returned | Add manual cache invalidation API endpoint |
| Feature calculation bug | Wrong trading decisions | Thorough unit tests, compare against known-good values |
| Concurrent cache stampede | Multiple processes compute same feature | Use distributed lock (Redis SETNX) |

## References

- MASTER_GUIDE.md (lines 113-147): Feature Store architecture
- COST_OPTIMIZATION_GUIDE.md: Caching strategy (99.95% cost reduction)
- TimescaleDB Best Practices: https://docs.timescale.com/
- Redis Best Practices: https://redis.io/docs/manual/patterns/

---

**Next Steps**: Review this spec, clarify any ambiguities, then proceed to `/speckit.plan` for technical implementation planning.
