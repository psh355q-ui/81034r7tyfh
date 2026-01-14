# Production Monitoring Guide

**Version**: 1.0
**Last Updated**: 2025-11-24
**Author**: AI Trading System Team

---

## 📋 Overview

This guide covers the advanced monitoring and alerting system for production operations of the AI Trading System.

### Key Features

- **🔍 Real-time Monitoring**: Prometheus metrics for all system components
- **🚨 Smart Alerts**: Intelligent alert filtering and prioritization
- **💔 Circuit Breakers**: Automatic failure protection for external APIs
- **🛑 Kill Switch**: Emergency trading halt mechanism
- **📊 Health Checks**: Comprehensive component health monitoring
- **⚡ Performance Metrics**: Track trading execution and AI costs

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Monitoring Layer                         │
├──────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Prometheus │  │   Grafana  │  │  Alerting  │        │
│  │  Metrics   │  │ Dashboard  │  │  Manager   │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│              Protection Mechanisms                        │
├──────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Circuit   │  │    Kill    │  │   Health   │        │
│  │  Breakers  │  │   Switch   │  │  Monitor   │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                Trading System                             │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Prometheus Metrics

### 2.1 Available Metrics

#### Trading Metrics
- `trades_total` - Total trades executed (by ticker, side, status)
- `trade_slippage_bps` - Trade slippage in basis points
- `trade_execution_duration_seconds` - Trade execution time
- `signals_generated_total` - Trading signals generated
- `signal_confidence` - Signal confidence distribution

#### Portfolio Metrics
- `portfolio_value_usd` - Current portfolio value
- `portfolio_daily_pnl_usd` - Daily P&L
- `portfolio_sharpe_ratio` - Rolling Sharpe ratio
- `portfolio_max_drawdown_pct` - Maximum drawdown

#### AI Cost Metrics
- `ai_api_calls_total` - Total AI API calls
- `ai_cost_usd_total` - Total AI cost
- `ai_tokens_used_total` - Tokens consumed
- `ai_monthly_cost_usd` - Projected monthly cost

#### System Metrics
- `api_requests_total` - API requests
- `api_request_duration_seconds` - API latency
- `cache_hit_rate` - Cache hit percentage
- `circuit_breaker_state` - Circuit breaker states

#### Risk Metrics
- `risk_score` - Risk scores by type
- `kill_switch_activations_total` - Kill switch activations
- `volatility_breach_total` - Volatility limit breaches

### 2.2 Accessing Metrics

```bash
# Prometheus endpoint
curl http://localhost:8000/metrics

# Metrics summary API
curl http://localhost:8000/monitoring/metrics/summary
```

### 2.3 Example Queries

```promql
# Average trade slippage in last hour
rate(trade_slippage_bps_sum[1h]) / rate(trade_slippage_bps_count[1h])

# AI cost per day
increase(ai_cost_usd_total[1d])

# 95th percentile API latency
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# Cache hit rate
avg(cache_hit_rate{cache_type="redis"})
```

---

## 3. Smart Alert System

### 3.1 Alert Categories

| Category | Description | Default Priority |
|----------|-------------|------------------|
| `SYSTEM_ERROR` | Critical system errors | HIGH |
| `TRADING_SIGNAL` | Buy/Sell signals | MEDIUM |
| `RISK_WARNING` | Risk threshold breaches | HIGH |
| `PORTFOLIO_UPDATE` | Portfolio changes | LOW |
| `DATA_QUALITY` | Data issues | MEDIUM |
| `COST_ALERT` | High AI/API costs | MEDIUM |
| `PERFORMANCE` | Performance degradation | LOW |

### 3.2 Alert Priorities

1. **CRITICAL**: Immediate action required (bypasses quiet hours)
2. **HIGH**: Action needed soon
3. **MEDIUM**: Informational, action optional
4. **LOW**: Nice to know

### 3.3 Smart Filtering

Alerts are automatically filtered based on:

- **Deduplication**: Prevents duplicate alerts within time window
- **Rate Limiting**: Limits alerts per category per hour
- **Quiet Hours**: Suppresses low-priority alerts (10 PM - 7 AM)
- **Priority Threshold**: Only sends alerts above minimum priority

### 3.4 Configuration

```python
# In main.py or configuration file
from backend.monitoring.smart_alerts import SmartAlertManager, AlertRule

alert_manager = SmartAlertManager(
    telegram_bot=telegram_bot,
    slack_client=slack_client,
    quiet_hours_start=22,  # 10 PM
    quiet_hours_end=7,     # 7 AM
)

# Customize alert rules
alert_manager.update_rule(AlertRule(
    category=AlertCategory.TRADING_SIGNAL,
    min_priority=AlertPriority.HIGH,  # Only high+ priority
    max_per_hour=10,                   # Max 10 per hour
    dedupe_window_minutes=30,          # 30 min dedupe window
))
```

### 3.5 Sending Alerts

```python
# Critical error (force send)
await alert_manager.alert_critical_error(
    error="Database connection lost",
    details={"database": "timescaledb", "retry_count": 3}
)

# Trading signal
await alert_manager.alert_trading_signal(
    ticker="AAPL",
    signal="BUY",
    confidence=0.85,
    details={"target_price": 195.00}
)

# Risk warning
await alert_manager.alert_risk_warning(
    ticker="TSLA",
    risk_type="volatility",
    risk_score=0.9,
    message="Volatility exceeded 50% threshold"
)
```

### 3.6 Alert APIs

```bash
# Get alert statistics
curl http://localhost:8000/monitoring/alerts/statistics

# Get recent alerts
curl http://localhost:8000/monitoring/alerts/recent?limit=50

# Send test alert
curl -X POST "http://localhost:8000/monitoring/alerts/test" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "TRADING_SIGNAL",
    "priority": "HIGH",
    "message": "Test alert from API"
  }'
```

---

## 4. Circuit Breakers

### 4.1 Purpose

Circuit breakers protect against cascading failures when external services fail:

- **Yahoo Finance API**: Stock price data
- **SEC EDGAR**: Filing downloads
- **Claude API**: AI analysis
- **Database**: TimescaleDB, PostgreSQL

### 4.2 States

- **CLOSED**: Normal operation ✅
- **OPEN**: Service failed, requests blocked ⛔
- **HALF_OPEN**: Testing recovery 🔄

### 4.3 Configuration

```python
from backend.monitoring.circuit_breaker import (
    CircuitBreakerManager,
    CircuitConfig,
)

cb_manager = CircuitBreakerManager(alert_manager=alert_manager)

# Create circuit breaker for Yahoo Finance
yahoo_breaker = cb_manager.create_breaker(
    name="yahoo_finance",
    config=CircuitConfig(
        failure_threshold=5,      # Open after 5 failures
        success_threshold=2,       # Close after 2 successes
        timeout_seconds=60,        # Try half-open after 60s
    )
)
```

### 4.4 Usage

```python
# Wrap external API calls
try:
    result = await yahoo_breaker.call(
        fetch_stock_data,
        ticker="AAPL"
    )
except CircuitBreakerOpenError:
    # Handle circuit open
    logger.warning("Yahoo Finance circuit is open")
    # Use cached data or return error
```

### 4.5 Monitoring

```bash
# Get all circuit breaker statuses
curl http://localhost:8000/monitoring/circuit-breakers

# Get specific breaker
curl http://localhost:8000/monitoring/circuit-breakers/yahoo_finance

# Reset circuit breaker
curl -X POST http://localhost:8000/monitoring/circuit-breakers/yahoo_finance/reset

# Reset all breakers
curl -X POST http://localhost:8000/monitoring/circuit-breakers/reset-all
```

---

## 5. Kill Switch

### 5.1 Purpose

Emergency mechanism to halt all trading operations when:

- Daily loss limit reached
- Critical system error
- Data quality issues
- Excessive market volatility
- Manual intervention needed

### 5.2 Activation Reasons

- `MANUAL`: User activated
- `DAILY_LOSS_LIMIT`: Hit daily loss limit
- `SYSTEM_ERROR`: Critical system error
- `DATA_QUALITY`: Bad data detected
- `VOLATILITY`: Market too volatile
- `API_FAILURE`: External API failure
- `RISK_THRESHOLD`: Risk limits breached

### 5.3 Configuration

```python
from backend.monitoring.circuit_breaker import KillSwitch, KillSwitchReason

kill_switch = KillSwitch(
    alert_manager=alert_manager,
    auto_cancel_orders=False,   # Manually cancel orders
    auto_close_positions=False, # Manually close positions
)

# Register callbacks
async def on_kill_switch_activate(reason, message, metadata):
    logger.critical(f"Kill switch activated: {reason}")
    # Cancel all pending orders
    await cancel_all_orders()

kill_switch.register_on_activate(on_kill_switch_activate)
```

### 5.4 Usage

```python
# Activate kill switch
await kill_switch.activate(
    reason=KillSwitchReason.DAILY_LOSS_LIMIT,
    message="Daily loss exceeded -5%",
    metadata={"daily_pnl": -5234.56, "limit": -5000.00}
)

# Check if trading allowed
if not kill_switch.is_trading_allowed():
    raise HTTPException(400, "Trading halted by kill switch")

# Deactivate
await kill_switch.deactivate(
    message="Manual recovery after fixing data issue"
)
```

### 5.5 Kill Switch APIs

```bash
# Get kill switch status
curl http://localhost:8000/monitoring/kill-switch

# Activate kill switch
curl -X POST "http://localhost:8000/monitoring/kill-switch/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "MANUAL",
    "message": "Emergency halt for system maintenance",
    "metadata": {"operator": "admin"}
  }'

# Deactivate kill switch
curl -X POST "http://localhost:8000/monitoring/kill-switch/deactivate" \
  -d "message=System maintenance complete"
```

---

## 6. Health Monitoring

### 6.1 Health Check Components

The health monitor tracks:

- **Redis**: Cache availability
- **Database**: TimescaleDB/PostgreSQL
- **Disk Space**: Storage capacity
- **Memory**: RAM usage
- **CPU**: Processor load

### 6.2 Health Status Levels

- `HEALTHY`: All systems operational ✅
- `DEGRADED`: Some issues, reduced performance ⚠️
- `UNHEALTHY`: Critical failures ❌
- `UNKNOWN`: Component not monitored ❓

### 6.3 Health Check APIs

```bash
# Detailed health check
curl http://localhost:8000/monitoring/health

# Health summary
curl http://localhost:8000/monitoring/health/summary

# Specific component
curl http://localhost:8000/monitoring/health/component/redis

# Quick system status
curl http://localhost:8000/monitoring/system/status
```

### 6.4 Example Response

```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T10:30:00Z",
  "components": [
    {
      "name": "Redis",
      "status": "healthy",
      "message": "Redis is operational",
      "response_time_ms": 1.23,
      "last_check": "2025-11-24T10:30:00Z"
    },
    {
      "name": "Disk Space",
      "status": "healthy",
      "message": "Disk usage normal: 45.2%",
      "metadata": {
        "total_gb": 512.0,
        "used_gb": 231.4,
        "free_gb": 280.6,
        "used_pct": 45.2
      }
    }
  ],
  "system_resources": {
    "cpu_percent": 23.5,
    "memory_percent": 58.2,
    "disk_free_gb": 280.6
  }
}
```

---

## 7. Grafana Dashboards

### 7.1 Setup

```bash
# Start Grafana (if using Docker Compose)
docker-compose up -d grafana

# Access Grafana
http://localhost:3000
# Default: admin / admin
```

### 7.2 Recommended Dashboards

#### System Overview Dashboard

Panels:
- API Request Rate (req/s)
- API Latency (p50, p95, p99)
- Cache Hit Rate
- System Resources (CPU, Memory, Disk)
- Circuit Breaker States
- Kill Switch Status

#### Trading Dashboard

Panels:
- Total Trades Today
- Trade Slippage Distribution
- Signals Generated (by type)
- Portfolio Value Over Time
- Daily P&L
- Sharpe Ratio (30d rolling)

#### Cost Dashboard

Panels:
- AI Cost Today
- AI Cost by Model
- Token Usage
- Projected Monthly Cost
- Cost per Analysis
- Cache Savings

#### Risk Dashboard

Panels:
- Risk Scores by Ticker
- Volatility Breaches
- Position Concentration
- Daily Loss Limit Usage
- Kill Switch Activations

---

## 8. Operational Procedures

### 8.1 Daily Checklist

- [ ] Check system health (`/monitoring/health`)
- [ ] Review overnight alerts
- [ ] Verify cache hit rate > 90%
- [ ] Check AI cost < daily budget
- [ ] Verify all circuit breakers CLOSED
- [ ] Confirm kill switch inactive

### 8.2 Emergency Procedures

#### Scenario: High API Costs

```bash
# 1. Check current costs
curl http://localhost:8000/monitoring/metrics/trading

# 2. If over budget, activate kill switch
curl -X POST http://localhost:8000/monitoring/kill-switch/activate \
  -H "Content-Type: application/json" \
  -d '{"reason":"COST_ALERT","message":"Daily AI cost exceeded $10"}'

# 3. Investigate and fix
# 4. Resume trading
curl -X POST http://localhost:8000/monitoring/kill-switch/deactivate
```

#### Scenario: Circuit Breaker Open

```bash
# 1. Check breaker status
curl http://localhost:8000/monitoring/circuit-breakers/yahoo_finance

# 2. Verify external service is back
curl https://query1.finance.yahoo.com/v8/finance/chart/AAPL

# 3. Reset circuit breaker
curl -X POST http://localhost:8000/monitoring/circuit-breakers/yahoo_finance/reset
```

#### Scenario: System Degraded

```bash
# 1. Get detailed health
curl http://localhost:8000/monitoring/health

# 2. Check unhealthy components
# 3. If critical, activate kill switch
# 4. Fix issue (restart service, clear disk, etc.)
# 5. Verify health restored
# 6. Deactivate kill switch
```

### 8.3 Alert Response Times

| Priority | Response Time | Action |
|----------|---------------|--------|
| CRITICAL | Immediate | Drop everything, fix now |
| HIGH | < 15 minutes | Investigate and resolve |
| MEDIUM | < 1 hour | Review and address |
| LOW | Next business day | Monitor and log |

---

## 9. Best Practices

### 9.1 Monitoring

1. **Set Up Dashboards**: Create Grafana dashboards for quick status checks
2. **Configure Alerts**: Tune alert thresholds to avoid noise
3. **Review Daily**: Check metrics every morning
4. **Track Trends**: Monitor weekly/monthly trends
5. **Document Incidents**: Keep runbook of past issues

### 9.2 Circuit Breakers

1. **Tune Thresholds**: Adjust based on service reliability
2. **Monitor State**: Track time in OPEN state
3. **Test Recovery**: Verify HALF_OPEN → CLOSED transitions
4. **Log Failures**: Understand root causes

### 9.3 Kill Switch

1. **Test Regularly**: Monthly kill switch drills
2. **Document Procedures**: Clear activation/deactivation steps
3. **Set Limits**: Define clear thresholds (loss %, volatility)
4. **Communicate**: Notify team when activated

### 9.4 Alerts

1. **Reduce Noise**: Set appropriate thresholds
2. **Use Quiet Hours**: Don't wake up for low-priority alerts
3. **Deduplicate**: Prevent alert storms
4. **Actionable Only**: Only alert if action needed

---

## 10. Troubleshooting

### Problem: Too Many Alerts

**Solution**:
```python
# Increase rate limits
alert_manager.update_rule(AlertRule(
    category=AlertCategory.TRADING_SIGNAL,
    max_per_hour=5,  # Reduce from 20
    dedupe_window_minutes=60,  # Increase from 15
))
```

### Problem: Circuit Breaker Stuck OPEN

**Solution**:
```bash
# 1. Check service health
curl https://api.external-service.com/health

# 2. Manually reset if service is healthy
curl -X POST http://localhost:8000/monitoring/circuit-breakers/service_name/reset
```

### Problem: Kill Switch Won't Deactivate

**Solution**:
```python
# Check kill switch status
status = kill_switch.get_status()
print(status)

# Force deactivate
kill_switch.is_active = False  # Emergency override
```

### Problem: Metrics Not Updating

**Solution**:
```bash
# 1. Check Prometheus scraping
curl http://localhost:8000/metrics | grep -A 5 "trades_total"

# 2. Restart metrics collector
# 3. Verify metrics_collector is initialized in main.py
```

---

## 11. API Reference

### Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/monitoring/health` | GET | Detailed health check |
| `/monitoring/health/summary` | GET | Health summary |
| `/monitoring/health/component/{name}` | GET | Component health |
| `/monitoring/metrics/summary` | GET | Metrics summary |
| `/monitoring/alerts/statistics` | GET | Alert statistics |
| `/monitoring/alerts/recent` | GET | Recent alerts |
| `/monitoring/alerts/test` | POST | Send test alert |
| `/monitoring/circuit-breakers` | GET | All circuit breakers |
| `/monitoring/circuit-breakers/{name}` | GET | Specific breaker |
| `/monitoring/circuit-breakers/{name}/reset` | POST | Reset breaker |
| `/monitoring/kill-switch` | GET | Kill switch status |
| `/monitoring/kill-switch/activate` | POST | Activate kill switch |
| `/monitoring/kill-switch/deactivate` | POST | Deactivate kill switch |
| `/monitoring/system/info` | GET | System information |
| `/monitoring/system/status` | GET | Quick system status |

---

## 12. Conclusion

This production monitoring system provides comprehensive visibility and control over the AI Trading System. Key benefits:

- **Proactive**: Detect issues before they impact trading
- **Automated**: Circuit breakers and smart alerts reduce manual intervention
- **Safe**: Kill switch provides emergency stop
- **Transparent**: Full visibility into system health and performance
- **Cost-Effective**: Track and optimize AI/API costs

For questions or issues, refer to the main documentation or create an issue on GitHub.

---

**Last Updated**: 2025-11-24
**Version**: 1.0
**Maintainer**: AI Trading System Team
