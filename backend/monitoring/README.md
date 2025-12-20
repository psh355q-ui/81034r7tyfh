# Prometheus Monitoring Metrics

## Overview

Comprehensive Prometheus metrics collection for real-time monitoring via Grafana dashboards.

**Integration Status**: ✅ **Tier 1 Complete** (Gemini Code Review: 3.5/5)

## Metrics Categories

### 1. AI Agent Metrics (6 metrics)

Track AI model performance, costs, and decisions:

| Metric | Type | Description |
|--------|------|-------------|
| `agent_analyses_total` | Counter | Total stock analyses performed |
| `agent_decisions_total` | Counter | Trading decisions (labels: `ticker`, `action`) |
| `ai_api_requests_total` | Counter | Claude API calls (label: `model_name`) |
| `ai_api_cost_usd_total` | Counter | Total AI cost in USD |
| `ai_api_latency_seconds` | Histogram | API response time distribution |
| `agent_conviction_score` | Histogram | Conviction score distribution (0.0-1.0) |

**Usage**:
```python
from monitoring import track_ai_request, AGENT_DECISIONS_TOTAL

# Track API request with cost
with track_ai_request('claude-3-haiku-20240307', cost_usd=0.0007):
    decision = await agent.analyze(ticker)

# Record decision
AGENT_DECISIONS_TOTAL.labels(ticker='AAPL', action='BUY').inc()
```

---

### 2. Feature Store Metrics (5 metrics)

Monitor cache performance and feature calculations:

| Metric | Type | Description |
|--------|------|-------------|
| `cache_hits_total` | Counter | Cache hits (label: `layer` = L1_Redis, L2_TimescaleDB) |
| `cache_misses_total` | Counter | Cache misses requiring calculation |
| `cache_hit_rate` | Gauge | Current hit rate (0.0-1.0) |
| `feature_calculation_latency_seconds` | Histogram | Time to calculate features |
| `feature_store_query_latency_seconds` | Histogram | Total query time |

**Usage**:
```python
from monitoring import CACHE_HITS_TOTAL, track_feature_calculation, update_cache_metrics

# Track cache hit
CACHE_HITS_TOTAL.labels(layer='L1_Redis').inc()

# Track feature calculation
with track_feature_calculation('mom_20d'):
    momentum = calculate_momentum(prices)

# Update hit rate gauge
update_cache_metrics(hits=950, misses=50)  # 95% hit rate
```

---

### 3. Trading & Portfolio Metrics (6 metrics)

Monitor trading activity and portfolio performance:

| Metric | Type | Description |
|--------|------|-------------|
| `trades_total` | Counter | Executed trades (labels: `ticker`, `side`) |
| `current_positions_count` | Gauge | Number of open positions |
| `portfolio_total_value` | Gauge | Total value (cash + holdings) |
| `portfolio_cash` | Gauge | Current cash balance |
| `daily_pnl` | Gauge | Daily profit/loss |
| `total_return_pct` | Gauge | Total portfolio return % |

**Usage**:
```python
from monitoring import track_trade, update_portfolio_metrics

# Track trade execution
track_trade(ticker='AAPL', side='BUY', quantity=10, fill_price=150.25)

# Update portfolio metrics (all at once)
update_portfolio_metrics(
    total_value=105000.00,
    cash=50000.00,
    num_positions=7,
    daily_pnl=1250.50,
    total_return_pct=5.0,
    max_drawdown_pct=-3.5
)
```

---

### 4. Constitution Rules & Risk Metrics (4 metrics)

Monitor rule enforcement and risk management:

| Metric | Type | Description |
|--------|------|-------------|
| `kill_switch_status` | Gauge | 1 = ACTIVE/Halted, 0 = Running |
| `constitution_violations_total` | Counter | Rule violations (label: `rule_name`) |
| `constitution_checks_total` | Counter | Rule checks (labels: `rule_name`, `result`) |
| `max_drawdown_pct` | Gauge | Maximum drawdown from peak |

**Usage**:
```python
from monitoring import track_constitution_check, KILL_SWITCH_STATUS

# Track rule check
passed = conviction >= 0.7
track_constitution_check('conviction_threshold_buy', passed=passed)

# Update kill switch
KILL_SWITCH_STATUS.set(1 if halted else 0)
```

---

### 5. System Health Metrics (3 metrics)

Monitor system infrastructure status:

| Metric | Type | Description |
|--------|------|-------------|
| `system_uptime_seconds` | Gauge | Application uptime |
| `timescale_connection_status` | Gauge | 1 = Connected, 0 = Disconnected |
| `redis_connection_status` | Gauge | 1 = Connected, 0 = Disconnected |

**Usage**:
```python
from monitoring import update_system_health

update_system_health(
    uptime_seconds=time.time() - start_time,
    timescale_connected=True,
    redis_connected=True,
    kill_switch_active=False
)
```

---

## Deployment

### 1. Start Metrics Server

**Standalone** (default for Phase 4-6):
```python
from monitoring import start_monitoring_server

start_monitoring_server(port=8001)
# Metrics at: http://localhost:8001/metrics
```

**FastAPI Integration** (Phase 7):
```python
from prometheus_client import make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### 2. Configure Prometheus

Already configured in [docker-compose.yml](../../docker-compose.yml):

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

**prometheus.yml**:
```yaml
scrape_configs:
  - job_name: 'ai-trading-system'
    scrape_interval: 15s
    static_configs:
      - targets: ['host.docker.internal:8001']
```

### 3. Access Grafana

Already configured in [docker-compose.yml](../../docker-compose.yml):

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
```

**Access**: http://localhost:3001
**Credentials**: admin / (from [config.py](../config.py))

---

## Grafana Dashboard Examples

### Dashboard 1: AI Trading Overview

**Panels**:
1. **Total AI Cost** (today): `sum(ai_api_cost_usd_total)`
2. **AI Requests/min**: `rate(ai_api_requests_total[1m])`
3. **Avg API Latency**: `histogram_quantile(0.95, ai_api_latency_seconds_bucket)`
4. **Cache Hit Rate**: `cache_hit_rate`
5. **Decisions by Action**: `agent_decisions_total` (grouped by action)

### Dashboard 2: Portfolio Performance

**Panels**:
1. **Portfolio Value**: `portfolio_total_value`
2. **Daily PnL**: `daily_pnl`
3. **Total Return %**: `total_return_pct`
4. **Max Drawdown**: `max_drawdown_pct`
5. **Open Positions**: `current_positions_count`
6. **Trades Today**: `increase(trades_total[1d])`

### Dashboard 3: System Health

**Panels**:
1. **Kill Switch Status**: `kill_switch_status` (red alert if 1)
2. **System Uptime**: `system_uptime_seconds`
3. **Database Status**: `timescale_connection_status`, `redis_connection_status`
4. **Constitution Violations**: `rate(constitution_violations_total[1h])`
5. **Feature Store Latency**: `feature_store_query_latency_seconds`

---

## Alerting Rules

### prometheus-alerts.yml

```yaml
groups:
  - name: trading_alerts
    rules:
      # Kill Switch Activated
      - alert: KillSwitchActivated
        expr: kill_switch_status == 1
        for: 1m
        annotations:
          summary: "Kill switch is ACTIVE - Trading halted"
          severity: critical

      # High AI Cost
      - alert: HighAICost
        expr: rate(ai_api_cost_usd_total[1h]) > 0.50
        for: 5m
        annotations:
          summary: "AI cost exceeding $0.50/hour"
          severity: warning

      # Low Cache Hit Rate
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.8
        for: 10m
        annotations:
          summary: "Cache hit rate below 80%"
          severity: warning

      # Database Disconnected
      - alert: DatabaseDisconnected
        expr: timescale_connection_status == 0 or redis_connection_status == 0
        for: 2m
        annotations:
          summary: "Database connection lost"
          severity: critical

      # Large Drawdown
      - alert: LargeDrawdown
        expr: max_drawdown_pct < -8.0
        for: 5m
        annotations:
          summary: "Max drawdown exceeds -8%"
          severity: warning
```

---

## Integration Examples

### With TradingAgent

```python
from ai.trading_agent import TradingAgent
from monitoring import track_ai_request, AGENT_ANALYSES_TOTAL, AGENT_DECISIONS_TOTAL

class MonitoredTradingAgent(TradingAgent):
    async def analyze(self, ticker: str):
        AGENT_ANALYSES_TOTAL.inc()

        # Track API request
        with track_ai_request(self.model_name, cost_usd=0.0007):
            decision = await super().analyze(ticker)

        # Record decision
        AGENT_DECISIONS_TOTAL.labels(
            ticker=ticker,
            action=decision.action
        ).inc()

        return decision
```

### With FeatureStore

```python
from data.feature_store import FeatureStore
from monitoring import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL, track_feature_calculation

class MonitoredFeatureStore(FeatureStore):
    async def get_features(self, ticker: str, date):
        # Check L1 cache
        cached = await self.redis.get(key)
        if cached:
            CACHE_HITS_TOTAL.labels(layer='L1_Redis').inc()
            return cached

        # Check L2 cache
        cached = await self.timescale.query(ticker, date)
        if cached:
            CACHE_HITS_TOTAL.labels(layer='L2_TimescaleDB').inc()
            return cached

        # Calculate (cache miss)
        CACHE_MISSES_TOTAL.inc()

        with track_feature_calculation('all_features'):
            features = await self.calculate_features(ticker, date)

        return features
```

### With BacktestEngine

```python
from backtesting import BacktestEngine
from monitoring import update_portfolio_metrics

class MonitoredBacktest(BacktestEngine):
    async def run(self):
        results = await super().run()

        # Update metrics after backtest
        update_portfolio_metrics(
            total_value=results['final_value'],
            cash=results.get('final_cash', 0),
            num_positions=0,  # Backtest ended
            daily_pnl=0,
            total_return_pct=results['total_return_pct'],
            max_drawdown_pct=results['max_drawdown_pct']
        )

        return results
```

---

## Testing

### Run Demo Server

```bash
cd backend
python -m monitoring.metrics
```

**Visit**: http://localhost:8001/metrics

**Output**:
```
# HELP agent_analyses_total Total number of stock analyses performed by AI agent
# TYPE agent_analyses_total counter
agent_analyses_total 42.0

# HELP ai_api_cost_usd_total Total cost of Claude API calls in USD
# TYPE ai_api_cost_usd_total counter
ai_api_cost_usd_total{model_name="claude-3-haiku-20240307"} 0.0294

# HELP cache_hit_rate Current cache hit rate (0.0 - 1.0)
# TYPE cache_hit_rate gauge
cache_hit_rate 0.95
```

---

## Files

- [metrics.py](metrics.py) - All Prometheus metrics (460 lines)
- [__init__.py](__init__.py) - Module exports
- [README.md](README.md) - This file

---

## Improvements from Gemini Version

Gemini's original version (3.5/5 rating) had these issues, now fixed:

1. ✅ **Missing context managers** - Added `track_ai_request()`, `track_feature_calculation()`
2. ✅ **No batch update functions** - Added `update_portfolio_metrics()`, `update_system_health()`
3. ✅ **Missing Constitution metrics** - Added violation tracking
4. ✅ **No integration examples** - Added TradingAgent/FeatureStore examples
5. ✅ **Missing buckets configuration** - Added proper histogram buckets
6. ✅ **No alerting rules** - Created comprehensive alert examples

---

## Next Steps

1. **Phase 4-5**: Use metrics for A/B testing (Haiku vs Sonnet)
2. **Phase 6**: Monitor production trading in real-time
3. **Phase 7**: Create Grafana dashboards
4. **Phase 7**: Set up Slack/email alerts via Alertmanager

---

## References

- **MASTER_GUIDE.md**: Section 7 (Monitoring), Section 8 (Observability)
- **GEMINI_CODE_REVIEW.md**: Tier 1 File Review (Score: 3.5/5)
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Dashboards**: https://grafana.com/docs/

---

**Status**: ✅ Production-ready
**AI Cost**: $0 (infrastructure monitoring only)
**Added**: 2025-11-09 (Gemini Tier 1 Integration)
**Total Metrics**: 24 (6 AI + 5 Cache + 6 Portfolio + 4 Risk + 3 System)
