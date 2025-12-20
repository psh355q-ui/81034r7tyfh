# Tasks: Feature Store

**Input**: Design documents from `.specify/specs/001-feature-store/`
**Prerequisites**: spec.md, plan.md
**Estimated Total Time**: 2 weeks (80 hours)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- File paths follow plan.md structure: `backend/data/feature_store/`, `backend/tests/`

---

## Phase 1: Setup (4 hours)

**Purpose**: Project initialization and dependencies

- [ ] T001 Create backend directory structure per plan.md: `backend/data/feature_store/`, `backend/data/collectors/`, `backend/data/models/`, `backend/tests/`
- [ ] T002 Initialize Python project with `pyproject.toml` (Poetry or uv) with dependencies: redis>=5.0, asyncpg>=0.29, pandas>=2.0, yfinance>=0.2, pydantic>=2.0, pytest>=7.4
- [ ] T003 [P] Create `.env.example` with: `REDIS_URL=redis://localhost:6379`, `TIMESCALE_URL=postgresql://postgres:postgres@localhost:5432/ai_trading`
- [ ] T004 [P] Create `pytest.ini` with async markers and coverage config (target 80%+)

---

## Phase 2: Foundational (12 hours) ⚠️ BLOCKS ALL USER STORIES

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Docker & Database

- [ ] T005 Create `docker-compose.yml` with Redis 7 (redis:7-alpine, 512MB memory, maxmemory-policy=allkeys-lru) and TimescaleDB (timescale/timescaledb:latest-pg15)
- [ ] T006 Start Docker Compose, verify Redis and TimescaleDB are healthy (use `docker-compose ps`)
- [ ] T007 Create Alembic migration `001_create_features_table.py` with hypertable schema from plan.md data-model section
- [ ] T008 Run Alembic migration, verify hypertable created: `SELECT * FROM timescaledb_information.hypertables`

### Base Classes & Models

- [ ] T009 [P] Create Pydantic models in `backend/data/models/feature.py`: Feature, FeatureRequest, FeatureResponse (exact schemas from plan.md data-model section)
- [ ] T010 [P] Create abstract `CacheLayer` interface in `backend/data/feature_store/cache_layer.py` with async methods: get(), set(), exists(), delete()
- [ ] T011 Implement `RedisCache` class (inherits CacheLayer) with connection pooling (max_connections=50), key schema: `feature:{ticker}:{feature_name}:{as_of_date}`
- [ ] T012 Implement `TimescaleCache` class (inherits CacheLayer) with asyncpg connection pool (min_size=5, max_size=20)

### Connection Testing

- [ ] T013 Write unit test `tests/unit/test_cache_layer.py::test_redis_connection` - verify Redis get/set with TTL
- [ ] T014 Write unit test `tests/unit/test_cache_layer.py::test_timescale_connection` - verify TimescaleDB insert/query
- [ ] T015 Run tests T013-T014, ensure they PASS before proceeding

**Checkpoint**: Foundation ready - Docker running, DB schema created, cache layers working ✅

---

## Phase 3: User Story 1 - Fast Feature Retrieval (Priority: P1) 🎯 MVP

**Goal**: Retrieve cached features in < 5ms (Redis) or < 100ms (TimescaleDB)

**Independent Test**: Call `get_features('AAPL', ['ret_5d'])` with pre-cached data, verify response time < 5ms

### Tests for US1

- [ ] T016 [P] [US1] Write contract test `tests/contract/test_feature_store.py::test_get_features_interface` - verify function signature matches plan.md contracts
- [ ] T017 [P] [US1] Write integration test `tests/integration/test_feature_store.py::test_redis_cache_hit` - pre-seed Redis, request feature, verify < 5ms
- [ ] T018 [P] [US1] Write integration test `tests/integration/test_feature_store.py::test_timescale_cache_hit` - seed DB (no Redis), request feature, verify < 100ms
- [ ] T019 Run tests T016-T018, ensure they FAIL (not implemented yet)

### Implementation for US1

- [ ] T020 [US1] Create `FeatureStore` class in `backend/data/feature_store/store.py` with `__init__(redis_cache, timescale_cache)`
- [ ] T021 [US1] Implement `FeatureStore.get_features()` - 2-layer cache retrieval: check Redis → fallback TimescaleDB → return None if not found
- [ ] T022 [US1] Add Prometheus metrics in `backend/data/feature_store/metrics.py`: `feature_requests_total`, `feature_latency_seconds`
- [ ] T023 [US1] Add logging for cache hits/misses with context: ticker, feature_name, cache_layer
- [ ] T024 [US1] Run tests T016-T018 again, ensure they PASS

**Checkpoint**: US1 complete - can retrieve cached features in < 5ms (Redis) or < 100ms (DB) ✅

---

## Phase 4: User Story 2 - Automatic Feature Computation (Priority: P1)

**Goal**: Automatically compute missing features from raw data

**Independent Test**: Request feature not in cache, verify it's computed, saved to both layers, and returned

### Tests for US2

- [ ] T025 [P] [US2] Write unit test `tests/unit/test_features.py::test_calculate_return_5d` - mock OHLCV data, verify ret_5d calculation (compare against spreadsheet)
- [ ] T026 [P] [US2] Write unit test `tests/unit/test_features.py::test_calculate_volatility_20d` - verify vol_20d calculation
- [ ] T027 [P] [US2] Write unit test `tests/unit/test_features.py::test_calculate_momentum_20d` - verify mom_20d calculation
- [ ] T028 [US2] Write integration test `tests/integration/test_feature_store.py::test_compute_on_cache_miss` - request missing feature, verify it's computed and saved
- [ ] T029 Run tests T025-T028, ensure they FAIL

### Implementation for US2

- [ ] T030 [P] [US2] Implement `calculate_return()` in `backend/data/feature_store/features.py` - fetch OHLCV via yfinance, calculate (price_now - price_N_days_ago) / price_N_days_ago
- [ ] T031 [P] [US2] Implement `calculate_volatility()` in `backend/data/feature_store/features.py` - rolling std of daily returns
- [ ] T032 [P] [US2] Implement `calculate_momentum()` in `backend/data/feature_store/features.py` - rate of change over window
- [ ] T033 [US2] Add Yahoo Finance collector in `backend/data/collectors/yahoo_collector.py` with caching (24h TTL) and rate limiting
- [ ] T034 [US2] Update `FeatureStore.get_features()` to call `compute_feature()` on cache miss
- [ ] T035 [US2] Implement `FeatureStore.compute_feature()` - route to correct calculation function (ret_5d → calculate_return(5))
- [ ] T036 [US2] Implement `FeatureStore._save_feature()` - save to both Redis (with TTL) and TimescaleDB
- [ ] T037 [US2] Add error handling: if computation fails, return None and log warning (don't crash)
- [ ] T038 [US2] Run tests T025-T028 again, ensure they PASS

**Checkpoint**: US2 complete - features are auto-computed on cache miss ✅

---

## Phase 5: User Story 3 - Point-in-Time Feature Access (Priority: P2)

**Goal**: Retrieve features as they existed at a historical timestamp (avoid look-ahead bias)

**Independent Test**: Request `as_of=2024-06-15`, verify only data before that date is used

### Tests for US3

- [ ] T039 [US3] Write integration test `tests/integration/test_point_in_time.py::test_historical_feature` - seed DB with dates 2024-01-01 to 2024-12-31, query as_of=2024-06-15, verify no future data used
- [ ] T040 [US3] Write integration test `tests/integration/test_point_in_time.py::test_backtest_no_lookahead` - run mock backtest over date range, verify sequential queries don't leak future data
- [ ] T041 Run tests T039-T040, ensure they FAIL

### Implementation for US3

- [ ] T042 [US3] Update `FeatureStore.get_features()` to accept `as_of` parameter (default=None means latest)
- [ ] T043 [US3] Update Redis key schema to include date: `feature:{ticker}:{feature_name}:{as_of_date}` (use date string YYYY-MM-DD)
- [ ] T044 [US3] Update TimescaleDB query to filter `as_of_timestamp <= user_provided_as_of`
- [ ] T045 [US3] Update feature calculation functions to accept `as_of` parameter and only fetch data before that date
- [ ] T046 [US3] Update `yahoo_collector.py` to support historical date queries: `yf.download(ticker, start=as_of-60days, end=as_of)`
- [ ] T047 [US3] Run tests T039-T040 again, ensure they PASS

**Checkpoint**: US3 complete - point-in-time queries work for backtesting ✅

---

## Phase 6: User Story 4 - High Cache Hit Rate (Priority: P1)

**Goal**: Achieve > 95% cache hit rate to minimize costs

**Independent Test**: Run system for 100 requests, measure (cache hits / total requests) > 0.95

### Tests for US4

- [ ] T048 [US4] Write performance test `tests/performance/test_cache_hit_rate.py::test_95_percent_hit_rate` - simulate 1000 requests (80% repeated tickers), measure hit rate > 95%
- [ ] T049 [US4] Write integration test `tests/integration/test_warm_up.py::test_cache_warm_up` - call warm_cache(['AAPL', 'MSFT']), verify features exist in Redis
- [ ] T050 Run tests T048-T049, ensure they FAIL

### Implementation for US4

- [ ] T051 [US4] Implement `FeatureStore.warm_cache(tickers)` - pre-load features for given tickers into Redis (call at market open)
- [ ] T052 [US4] Add LRU eviction monitoring: track evicted keys, alert if eviction rate > 5%
- [ ] T053 [US4] Add cache hit rate metric to Prometheus: `cache_hit_rate{cache_layer="redis"}`, `cache_hit_rate{cache_layer="timescale"}`
- [ ] T054 [US4] Implement distributed lock for cache stampede prevention: use Redis SETNX to ensure only one process computes same feature
- [ ] T055 [US4] Run tests T048-T049 again, ensure they PASS (hit rate > 95%)

**Checkpoint**: US4 complete - cache hit rate > 95% achieved ✅

---

## Phase 7: User Story 5 - Feature Versioning (Priority: P3) 🔵 Optional

**Goal**: Track feature calculation logic versions for reproducibility

**Independent Test**: Change calculation logic, verify old and new versions coexist

### Tests for US5

- [ ] T056 [US5] Write integration test `tests/integration/test_versioning.py::test_multiple_versions` - save feature v1, change logic, save v2, verify both retrievable
- [ ] T057 [US5] Write integration test `tests/integration/test_versioning.py::test_default_latest_version` - request feature without version, verify latest returned
- [ ] T058 Run tests T056-T057, ensure they FAIL

### Implementation for US5

- [ ] T059 [US5] Add `version` parameter to `FeatureStore.get_features()` (default=None means latest)
- [ ] T060 [US5] Update Redis key schema: `feature:{ticker}:{feature_name}:{as_of_date}:v{version}`
- [ ] T061 [US5] Update TimescaleDB query to filter by version: `WHERE version = ? OR (version IS NULL AND ? IS NULL)`
- [ ] T062 [US5] Add version metadata to feature calculation functions (hardcode version=1 for now)
- [ ] T063 [US5] Run tests T056-T057 again, ensure they PASS

**Checkpoint**: US5 complete - feature versioning works ✅

---

## Phase 8: Performance & Monitoring (8 hours)

**Purpose**: Optimize and add observability

- [ ] T064 [P] Write load test `tests/performance/test_benchmarks.py::test_1000_req_per_sec` - use pytest-benchmark, measure p50/p95/p99 latencies
- [ ] T065 [P] Write cost test `tests/performance/test_cost_tracking.py::test_monthly_cost` - simulate 24h operation, count API calls, calculate cost < $0.02/day
- [ ] T066 Run performance tests T064-T065, document results in `quickstart.md`
- [ ] T067 Create Grafana dashboard JSON in `monitoring/grafana/feature_store_dashboard.json` with panels from plan.md
- [ ] T068 Add Prometheus scrape endpoint in `backend/data/feature_store/metrics.py` (use prometheus_client)
- [ ] T069 Optimize TimescaleDB queries: run EXPLAIN ANALYZE, add indexes if p99 > 100ms
- [ ] T070 Optimize Redis memory: tune `maxmemory-policy`, monitor memory usage with `INFO memory`

---

## Phase 9: Documentation & Polish (4 hours)

**Purpose**: Finalize documentation and code quality

- [ ] T071 [P] Create `quickstart.md` in `.specify/specs/001-feature-store/` with: Docker setup, sample data population, example queries
- [ ] T072 [P] Create `data-model.md` with SQL schema, Redis key patterns, Pydantic models
- [ ] T073 [P] Update `README.md` with Feature Store section: purpose, usage, performance metrics
- [ ] T074 [P] Add docstrings to all public methods in `store.py`, `features.py`, `cache_layer.py`
- [ ] T075 Run linter (ruff or black) and fix all formatting issues
- [ ] T076 Run type checker (mypy) and fix type errors
- [ ] T077 Generate code coverage report: `pytest --cov=backend/data/feature_store --cov-report=html`, verify > 80%
- [ ] T078 Review and validate quickstart.md - follow steps manually, ensure it works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational ✅
- **User Story 2 (Phase 4)**: Depends on Foundational ✅ (can run parallel with US1 if different developers)
- **User Story 3 (Phase 5)**: Depends on US1 + US2 (modifies their implementations)
- **User Story 4 (Phase 6)**: Depends on US1 + US2 (builds on top)
- **User Story 5 (Phase 7)**: Optional - depends on US1 + US2
- **Performance (Phase 8)**: Depends on US1-US4 complete
- **Documentation (Phase 9)**: Can start anytime, finalize at end

### Critical Path (MVP)

Minimum viable product requires:
1. Phase 1 (Setup) → 2 (Foundational) → 3 (US1) → 4 (US2) → 8 (Performance tests)

US3, US4, US5 are enhancements (can defer to later).

### Parallel Opportunities

**After Foundational phase completes:**
- US1 (Phase 3) and US2 (Phase 4) can run in parallel (different files):
  - Developer A: T020-T024 (US1 - retrieval logic)
  - Developer B: T030-T038 (US2 - computation logic)
  - They integrate in T034 (update get_features to call compute_feature)

**Within each User Story:**
- All tests marked [P] can run in parallel (write tests concurrently)
- All models/functions marked [P] can run in parallel (implement independently)

**Documentation (Phase 9):**
- All T071-T074 can run in parallel (different files)

---

## Implementation Strategy

### MVP First (2 days)

1. Day 1 AM: T001-T015 (Setup + Foundational) → Foundation ready
2. Day 1 PM: T016-T024 (US1 - retrieval) → Can retrieve cached features
3. Day 2 AM: T025-T038 (US2 - computation) → Auto-compute on cache miss
4. Day 2 PM: T064-T066 (Performance tests) → Validate speed/cost
5. **STOP and DEMO**: Show working MVP - request feature, get result in < 10ms

### Full Feature (2 weeks)

- Week 1: Phases 1-4 (Setup + Foundational + US1 + US2) = MVP
- Week 2: Phases 5-9 (US3-US5 + Performance + Documentation)

### Parallel Team Strategy (if 2 developers)

- Developer A: Setup → Foundational → US1 → US3 → US5 (optional)
- Developer B: Setup → Foundational → US2 → US4 → Performance

Both work on Documentation (Phase 9) in parallel at end.

---

## Time Estimates

| Phase | Hours | Tasks | Can Parallelize? |
|-------|-------|-------|------------------|
| 1. Setup | 4h | T001-T004 | Yes (T003-T004) |
| 2. Foundational | 12h | T005-T015 | Partial (T009-T012) |
| 3. US1 | 8h | T016-T024 | Yes (T016-T018) |
| 4. US2 | 12h | T025-T038 | Yes (T025-T032) |
| 5. US3 | 8h | T039-T047 | No |
| 6. US4 | 6h | T048-T055 | Partial (T048-T049) |
| 7. US5 | 6h | T056-T063 | No (optional) |
| 8. Performance | 8h | T064-T070 | Yes (T064-T065) |
| 9. Documentation | 4h | T071-T078 | Yes (T071-T074) |
| **Total** | **68h** | 78 tasks | ~20h parallelizable |

**With 1 developer**: 68 hours = 8.5 days = **2 weeks**
**With 2 developers**: (68 - 20) / 2 + 20 = 44 hours = 5.5 days = **1.5 weeks**

---

## Success Criteria Checklist

From spec.md, verify:

- [ ] **SC-001**: Redis cache hit rate > 95% (T048)
- [ ] **SC-002**: Average latency < 10ms (T064)
- [ ] **SC-003**: Cost reduction 99.96% (T065)
- [ ] **SC-004**: Serve 700k queries/month (T064 - 1000 req/sec)
- [ ] **SC-005**: Zero data corruption (T039-T040 - backtest determinism)
- [ ] **SC-006**: Graceful degradation (T017-T018 - fallback to DB)
- [ ] **SC-007**: Cache warm-up < 5 minutes (T049)
- [ ] **SC-008**: Cost tracking dashboard (T067)

---

## Notes

- **TDD**: Write tests FIRST (ensure they FAIL), then implement, then verify PASS
- **Commit strategy**: Commit after each user story checkpoint (T024, T038, T047, etc.)
- **Stop points**: After US1 (T024) or US2 (T038), system is usable - can pause and demo
- **Skip US5**: Feature versioning (Phase 7) is optional - can defer to Phase 2 of project
- **Docker required**: All integration tests require Docker Compose running (T006)

---

**Next Steps**:
1. Review this task list with team
2. Clarify any ambiguities via `/speckit.clarify`
3. Start implementation via `/speckit.implement` or manually execute tasks in order
4. Update task checkboxes as you complete them
5. Celebrate after each checkpoint! 🎉
