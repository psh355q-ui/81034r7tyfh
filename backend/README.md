# AI Trading System - Backend

## Feature Store Implementation

2-Layer caching system (Redis + TimescaleDB) for high-performance feature retrieval.

### Quick Start

#### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv or pip for package management

#### 2. Installation

```bash
# Install dependencies
pip install -e .

# Or with uv (recommended)
uv pip install -e .
```

#### 3. Start Infrastructure

```bash
# Start Redis + TimescaleDB + Monitoring
docker compose up -d

# Check containers are healthy
docker compose ps

# You should see:
# - redis (healthy)
# - timescaledb (healthy)
# - prometheus (healthy)
# - grafana (healthy)
```

#### 4. Run Database Migration

```bash
# Apply Alembic migration to create features table
cd backend
alembic upgrade head

# Verify hypertable created
docker compose exec timescaledb psql -U postgres -d ai_trading -c "SELECT * FROM timescaledb_information.hypertables;"
```

#### 5. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set your API keys
# At minimum, you need:
# - REDIS_URL (default: redis://localhost:6379/0)
# - TIMESCALE_* (default: localhost:5432/ai_trading)
```

#### 6. Test Feature Store

```python
import asyncio
from data.feature_store import FeatureStore

async def main():
    # Initialize Feature Store
    store = FeatureStore()
    await store.initialize()

    # Get features for AAPL
    response = await store.get_features(
        ticker="AAPL",
        feature_names=["ret_5d", "vol_20d", "mom_20d"]
    )

    print(f"Features: {response.features}")
    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"Cache hits: {response.cache_hits}, Cache misses: {response.cache_misses}")

    # Close connections
    await store.close()

asyncio.run(main())
```

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Feature Store                        │
│                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Request   │ →  │ Redis (L1)  │ →  │TimescaleDB  │ │
│  │             │    │   < 5ms     │    │  (L2)       │ │
│  │             │    │             │    │  < 100ms    │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                  │                   │         │
│         │                  │ cache miss        │         │
│         ↓                  ↓                   ↓         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Feature Calculation                    │   │
│  │  (Yahoo Finance + Pandas/Numpy)                  │   │
│  │           ~2-5 seconds                           │   │
│  └──────────────────────────────────────────────────┘   │
│         │                                                │
│         ↓                                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │    Save to both Redis + TimescaleDB              │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Available Features

| Feature Name | Description | Window |
|--------------|-------------|--------|
| `ret_5d` | 5-day return | 5 days |
| `ret_20d` | 20-day return | 20 days |
| `ret_60d` | 60-day return | 60 days |
| `vol_20d` | 20-day volatility (annualized) | 20 days |
| `vol_60d` | 60-day volatility (annualized) | 60 days |
| `mom_20d` | 20-day momentum | 20 days |
| `mom_60d` | 60-day momentum | 60 days |
| `rsi_14` | Relative Strength Index | 14 days |
| `macd` | MACD indicator | 12/26/9 |

### Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Redis latency (p99) | < 5ms | 2-4ms |
| TimescaleDB latency (p99) | < 100ms | 30-80ms |
| Cache hit rate (after warmup) | > 95% | ~98% |
| Monthly cost (100 tickers) | < $1 | ~$0.51 |

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only (fast, no Docker required)
pytest -m unit

# Run integration tests (requires Docker)
pytest -m integration

# Run with coverage report
pytest --cov=data --cov-report=html
open htmlcov/index.html
```

### Monitoring

#### Grafana Dashboard

Open http://localhost:3001 (admin/admin)

- Feature Store Performance Dashboard
- Cache hit rate over time
- Latency distribution (p50, p95, p99)
- Cost tracking

#### Prometheus Metrics

Open http://localhost:9090

Available metrics:
- `feature_requests_total{ticker, feature_name, cache_layer}`
- `feature_latency_seconds{operation}`
- `cache_hit_rate{cache_layer}`
- `monthly_cost_usd`

### Cache Warm-up

Pre-load popular tickers at market open:

```python
store = FeatureStore()
await store.initialize()

# Warm cache for top 10 tickers
tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "AMZN", "META", "SPY", "QQQ", "DIA"]
stats = await store.warm_cache(tickers)

print(f"Warmed {stats['tickers_warmed']} tickers in {stats['time_taken_seconds']:.2f}s")
```

### Troubleshooting

#### Redis connection failed

```bash
# Check Redis is running
docker compose ps redis

# Check Redis logs
docker compose logs redis

# Test connection manually
docker compose exec redis redis-cli ping
# Should return: PONG
```

#### TimescaleDB connection failed

```bash
# Check TimescaleDB is running
docker compose ps timescaledb

# Check logs
docker compose logs timescaledb

# Test connection manually
docker compose exec timescaledb psql -U postgres -d ai_trading -c "SELECT 1"
```

#### Cache hit rate is low

Possible causes:
1. Cache not warmed up yet (wait 24h or run `warm_cache()`)
2. TTL too short (increase `ttl_daily` parameter)
3. Redis memory full (check `docker stats`, increase maxmemory)

#### Features returning None

Possible causes:
1. Insufficient historical data (need N+buffer days)
2. Yahoo Finance rate limit hit (wait 1 hour)
3. Invalid ticker symbol (check spelling)

### Next Steps

See [MASTER_GUIDE.md](../MASTER_GUIDE.md) for:
- Phase 3: AI integration (Claude API)
- Phase 4: Trading strategies
- Phase 5: Automatic execution
- Phase 6: Deployment to Synology NAS

### Support

For issues or questions:
- Check [tasks.md](.specify/specs/001-feature-store/tasks.md) for implementation status
- Review [spec.md](.specify/specs/001-feature-store/spec.md) for requirements
- See [plan.md](.specify/specs/001-feature-store/plan.md) for architecture details
