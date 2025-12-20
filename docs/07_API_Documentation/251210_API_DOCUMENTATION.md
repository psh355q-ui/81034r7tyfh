# AI Trading System - API Documentation

Complete API reference for all endpoints in the AI Trading System.

**Base URL**: `http://localhost:8001`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Monitoring](#health--monitoring)
3. [News & RSS](#news--rss)
4. [AI Analysis](#ai-analysis)
5. [Trading Signals](#trading-signals)
6. [Backtesting](#backtesting)
7. [Reports & Analytics](#reports--analytics)
8. [Advanced Analytics](#advanced-analytics)
9. [CEO Analysis](#ceo-analysis)
10. [Notifications](#notifications)
11. [Logs](#logs)
12. [Incremental Cost Savings](#incremental-cost-savings)
13. [Global Macro](#global-macro)
14. [Auto Trade](#auto-trade)
15. [Consensus Backtest](#consensus-backtest)
16. [Portfolio Management](#portfolio-management)

---

## Authentication

All protected endpoints require authentication via API key.

### Methods
- **Header**: `X-API-Key: your_api_key`
- **Query Parameter**: `?api_key=your_api_key`

### Permission Levels
- **READONLY**: View data, stats, monitoring
- **TRADING**: Execute trades, approve signals
- **MASTER**: Full system access

### Endpoints

#### `GET /auth/status`
Get authentication system status.

**Auth Required**: READONLY

**Response**:
```json
{
  "total_keys": 4,
  "enabled_keys": 2,
  "recent_failed_attempts": 5,
  "audit_log_size": 150
}
```

#### `GET /auth/me`
Get current API key information.

**Auth Required**: Valid API key

**Response**:
```json
{
  "name": "TRADING",
  "permissions": ["READ", "TRADE"],
  "rate_limit_per_hour": 3600,
  "enabled": true,
  "created_at": "N/A",
  "last_used": null,
  "remaining_requests": 60
}
```

#### `GET /auth/audit-logs?limit=100`
Get recent audit logs.

**Auth Required**: TRADING

**Parameters**:
- `limit` (int, optional): Number of logs to return (1-1000, default: 100)

#### `GET /auth/failed-attempts?hours=24`
Get failed authentication attempts.

**Auth Required**: TRADING

**Parameters**:
- `hours` (int, optional): Time window in hours (1-168, default: 24)

#### `GET /auth/test/read`
Test READONLY permission.

#### `GET /auth/test/write`
Test TRADING permission.

#### `GET /auth/test/execute`
Test MASTER permission.

#### `GET /auth/health`
Public health check (no auth required).

---

## Health & Monitoring

#### `GET /health`
System health check.

**Auth Required**: None

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-26T14:23:31.704970",
  "components": [
    {
      "name": "Disk Space",
      "status": "healthy",
      "message": "Disk usage normal: 45.2%",
      "last_check": "2025-11-26T14:23:31.602325",
      "response_time_ms": 0.583,
      "metadata": {
        "total_gb": 1863.02,
        "used_gb": 842.15,
        "free_gb": 1020.87,
        "used_pct": 45.2
      }
    },
    {
      "name": "Memory",
      "status": "healthy",
      "message": "Memory usage normal: 55.4%",
      "metadata": {
        "total_gb": 31.93,
        "used_gb": 17.68,
        "available_gb": 14.25,
        "used_pct": 55.4
      }
    }
  ],
  "system_resources": {
    "cpu_percent": 11.3,
    "memory_percent": 55.4,
    "memory_available_gb": 14.25,
    "disk_used_percent": 45.2,
    "disk_free_gb": 1020.87
  }
}
```

---

## News & RSS

### RSS Feed Management

#### `GET /feeds`
List all RSS feeds.

**Response**:
```json
[
  {
    "id": 1,
    "name": "Bloomberg Markets",
    "url": "https://feeds.bloomberg.com/markets/news.rss",
    "category": "us",
    "enabled": true,
    "last_fetched": "2025-11-26T10:30:00",
    "article_count": 1523
  }
]
```

#### `POST /feeds`
Add new RSS feed.

**Request Body**:
```json
{
  "name": "Reuters Business",
  "url": "https://www.reuters.com/business/rss",
  "category": "us",
  "enabled": true
}
```

#### `PUT /feeds/{feed_id}`
Update RSS feed.

#### `DELETE /feeds/{feed_id}`
Delete RSS feed.

### News Articles

#### `GET /news/articles`
Get news articles with filtering.

**Parameters**:
- `limit` (int): Number of articles (default: 50)
- `offset` (int): Pagination offset (default: 0)
- `category` (str): Filter by category
- `analyzed` (bool): Only analyzed articles
- `high_impact` (bool): Only high-impact news

**Response**:
```json
{
  "articles": [
    {
      "id": 1234,
      "url": "https://example.com/article",
      "title": "Fed Raises Interest Rates",
      "content": "The Federal Reserve...",
      "published_at": "2025-11-26T09:00:00",
      "source": "Bloomberg",
      "category": "us",
      "analyzed": true,
      "sentiment": 0.65,
      "impact_score": 8.5,
      "tickers": ["SPY", "TLT"]
    }
  ],
  "total": 1523,
  "has_more": true
}
```

#### `POST /news/crawl`
Trigger RSS crawling.

**Response**:
```json
{
  "status": "started",
  "message": "Crawling 12 RSS feeds...",
  "feeds": 12
}
```

#### `POST /news/analyze`
Trigger AI analysis of unanalyzed articles.

**Parameters**:
- `batch_size` (int): Articles to analyze (default: 10, max: 50)

#### `GET /news/ticker/{ticker}`
Get news for specific ticker.

**Response**:
```json
{
  "ticker": "AAPL",
  "articles": [...],
  "total": 45,
  "avg_sentiment": 0.72,
  "avg_impact": 6.8
}
```

#### `GET /news/stats`
Get news statistics.

**Response**:
```json
{
  "total_articles": 15234,
  "analyzed_articles": 12456,
  "analysis_rate": 81.7,
  "feeds_active": 12,
  "feeds_total": 15,
  "last_crawl": "2025-11-26T10:30:00",
  "daily_usage": {
    "gemini_api_calls": 245,
    "limit": 1500,
    "usage_pct": 16.3
  }
}
```

---

## AI Analysis

### AI Chat

#### `POST /ai-chat`
Chat with AI assistant.

**Request Body**:
```json
{
  "message": "Analyze AAPL stock",
  "context": {
    "ticker": "AAPL",
    "user_portfolio": ["AAPL", "MSFT"]
  }
}
```

**Response**:
```json
{
  "response": "Apple Inc. (AAPL) is currently...",
  "sources": ["Bloomberg", "Reuters"],
  "confidence": 0.85
}
```

### Gemini Free Chat

#### `POST /gemini-free/chat`
Chat using Gemini free tier.

**Request Body**:
```json
{
  "message": "What are the top tech stocks?",
  "stream": false
}
```

### AI Review

#### `POST /ai-review/analyze`
Deep analysis with multi-AI ensemble.

**Request Body**:
```json
{
  "ticker": "TSLA",
  "analysis_type": "fundamental",
  "include_news": true,
  "include_technicals": true
}
```

**Response**:
```json
{
  "ticker": "TSLA",
  "claude_analysis": {...},
  "gpt4_analysis": {...},
  "gemini_analysis": {...},
  "ensemble_recommendation": "BUY",
  "confidence": 0.78,
  "reasoning": "Strong fundamentals, positive sentiment..."
}
```

---

## Trading Signals

#### `GET /signals`
Get all trading signals.

**Parameters**:
- `status` (str): Filter by status (pending/approved/rejected/executed)
- `ticker` (str): Filter by ticker
- `limit` (int): Number of signals

**Response**:
```json
{
  "signals": [
    {
      "id": 1,
      "ticker": "AAPL",
      "action": "BUY",
      "confidence": 0.85,
      "target_price": 185.50,
      "stop_loss": 175.00,
      "position_size": 5.0,
      "status": "pending",
      "created_at": "2025-11-26T09:15:00",
      "reasoning": "Strong earnings beat, positive sentiment",
      "ai_sources": ["claude", "gpt4", "gemini"]
    }
  ],
  "total": 45
}
```

#### `POST /signals/generate`
Generate trading signal from news.

**Request Body**:
```json
{
  "article_id": 1234,
  "force_regenerate": false
}
```

#### `POST /signals/{signal_id}/approve`
Approve a trading signal.

**Auth Required**: TRADING

#### `POST /signals/{signal_id}/reject`
Reject a trading signal.

**Auth Required**: TRADING

#### `POST /signals/{signal_id}/execute`
Execute approved signal.

**Auth Required**: TRADING

**Request Body**:
```json
{
  "execution_algorithm": "TWAP",
  "duration_minutes": 30,
  "max_slippage_bps": 10
}
```

---

## Backtesting

#### `POST /backtest/run`
Run backtest on historical signals.

**Request Body**:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000,
  "strategy": "news_trading",
  "parameters": {
    "min_confidence": 0.7,
    "max_position_size": 10.0,
    "use_stop_loss": true
  }
}
```

**Response**:
```json
{
  "backtest_id": "bt_20241126_001",
  "status": "completed",
  "results": {
    "total_return": 23.5,
    "sharpe_ratio": 1.85,
    "max_drawdown": -8.3,
    "win_rate": 62.5,
    "total_trades": 143,
    "winning_trades": 89,
    "losing_trades": 54,
    "avg_win": 2.8,
    "avg_loss": -1.5,
    "profit_factor": 1.73
  },
  "equity_curve": [...],
  "trades": [...]
}
```

#### `GET /backtest/results/{backtest_id}`
Get backtest results.

#### `GET /backtest/list`
List all backtests.

---

## Reports & Analytics

### Basic Reports

#### `GET /reports/performance`
Get performance metrics.

**Parameters**:
- `start_date` (date): Start date (YYYY-MM-DD)
- `end_date` (date): End date (YYYY-MM-DD)
- `ticker` (str, optional): Filter by ticker

**Response**:
```json
{
  "total_return": 15.3,
  "total_return_pct": 15.3,
  "sharpe_ratio": 1.65,
  "sortino_ratio": 2.12,
  "max_drawdown": -6.8,
  "win_rate": 58.5,
  "avg_win": 2.5,
  "avg_loss": -1.3,
  "profit_factor": 1.92,
  "total_trades": 87,
  "winning_trades": 51,
  "losing_trades": 36
}
```

#### `GET /reports/risk`
Get risk metrics.

**Response**:
```json
{
  "var_95": -2500.00,
  "var_99": -4200.00,
  "cvar_95": -3100.00,
  "current_drawdown": -2.3,
  "max_drawdown": -6.8,
  "portfolio_volatility": 12.5,
  "beta": 0.85,
  "correlation_to_spy": 0.72
}
```

---

## Advanced Analytics

New in Phase 15.5 - Deep performance analysis and attribution.

### Performance Attribution

#### `GET /reports/advanced/performance-attribution`
Analyze performance contribution by various dimensions.

**Parameters**:
- `start_date` (date, required): Start date (YYYY-MM-DD)
- `end_date` (date, required): End date (YYYY-MM-DD)
- `dimension` (str): Dimension to analyze
  - `all`: All dimensions
  - `strategy`: By trading strategy
  - `sector`: By sector
  - `ai_source`: By AI model (Claude/GPT/Gemini)
  - `position`: By long/short positions
  - `time`: By time periods

**Response**:
```json
{
  "strategy_attribution": {
    "news_trading": {
      "pnl": 12500.00,
      "pnl_pct": 12.5,
      "trades": 45,
      "win_rate": 62.2,
      "sharpe": 1.85
    },
    "mean_reversion": {
      "pnl": 3200.00,
      "pnl_pct": 3.2,
      "trades": 23,
      "win_rate": 52.2,
      "sharpe": 1.12
    }
  },
  "sector_attribution": {
    "Technology": {
      "pnl": 8900.00,
      "pnl_pct": 8.9,
      "exposure_pct": 35.0,
      "contribution": 56.8
    },
    "Healthcare": {
      "pnl": 4200.00,
      "pnl_pct": 4.2,
      "exposure_pct": 20.0,
      "contribution": 26.8
    }
  },
  "ai_source_attribution": {
    "claude": {
      "pnl": 9500.00,
      "trades": 32,
      "win_rate": 65.6,
      "avg_confidence": 0.78
    },
    "gpt4": {
      "pnl": 4800.00,
      "trades": 28,
      "win_rate": 57.1,
      "avg_confidence": 0.72
    },
    "gemini": {
      "pnl": 1400.00,
      "trades": 27,
      "win_rate": 51.9,
      "avg_confidence": 0.68
    }
  }
}
```

### Risk Analytics

#### `GET /reports/advanced/risk-metrics`
Advanced risk analysis including VaR, drawdowns, and concentration.

**Parameters**:
- `start_date` (date, required)
- `end_date` (date, required)
- `metric` (str): Risk metric type
  - `all`: All metrics
  - `var`: Value at Risk
  - `drawdown`: Drawdown analysis
  - `concentration`: Concentration risk
  - `correlation`: Correlation analysis
  - `stress_test`: Stress testing

**Response**:
```json
{
  "var_metrics": {
    "var_95_usd": -2500.00,
    "var_95_pct": -2.5,
    "var_99_usd": -4200.00,
    "var_99_pct": -4.2,
    "cvar_95_usd": -3100.00,
    "cvar_99_usd": -5800.00,
    "portfolio_value": 100000.00,
    "sample_size": 252
  },
  "drawdown_metrics": {
    "max_drawdown_pct": -6.8,
    "max_drawdown_usd": -6800.00,
    "current_drawdown_pct": -2.3,
    "current_drawdown_usd": -2300.00,
    "recovery_days": 15,
    "is_recovered": false,
    "drawdown_periods": [
      {
        "start_date": "2024-03-15",
        "end_date": "2024-04-02",
        "drawdown_pct": -6.8,
        "duration_days": 18,
        "recovery_days": 12
      }
    ]
  },
  "concentration_metrics": {
    "hhi_index": 1250.5,
    "top_5_concentration_pct": 45.2,
    "top_holdings": [
      {
        "symbol": "AAPL",
        "exposure_usd": 15000.00,
        "concentration_pct": 15.0
      },
      {
        "symbol": "MSFT",
        "exposure_usd": 12000.00,
        "concentration_pct": 12.0
      }
    ]
  },
  "correlation_analysis": {
    "spy_correlation": 0.72,
    "intra_portfolio_correlation": 0.58,
    "correlation_matrix": {...}
  }
}
```

### Trade Analytics

#### `GET /reports/advanced/trade-analytics`
Detailed trade pattern analysis.

**Parameters**:
- `start_date` (date, required)
- `end_date` (date, required)
- `analysis_type` (str): Analysis type
  - `all`: All analyses
  - `win_loss`: Win/loss patterns
  - `execution`: Execution quality
  - `holding`: Holding period analysis
  - `confidence`: Confidence impact

**Response**:
```json
{
  "win_loss_patterns": {
    "by_day_of_week": {
      "Monday": {"win_rate": 62.5, "avg_pnl": 125.50},
      "Tuesday": {"win_rate": 55.0, "avg_pnl": 98.20}
    },
    "by_hour": {
      "09:00": {"win_rate": 58.3, "avg_pnl": 110.30},
      "10:00": {"win_rate": 65.2, "avg_pnl": 145.80}
    }
  },
  "execution_quality": {
    "avg_slippage_bps": 2.5,
    "fill_rate": 98.5,
    "avg_execution_time_sec": 45.2,
    "best_execution_algo": "TWAP",
    "worst_execution_algo": "MARKET"
  },
  "holding_period": {
    "avg_holding_hours": 18.5,
    "optimal_holding_hours": 24.0,
    "by_holding_period": {
      "0-6h": {"count": 15, "win_rate": 45.0, "avg_pnl": -50.20},
      "6-24h": {"count": 42, "win_rate": 65.5, "avg_pnl": 180.50},
      "24-72h": {"count": 30, "win_rate": 58.0, "avg_pnl": 120.30}
    }
  },
  "confidence_impact": {
    "high_confidence": {
      "threshold": 0.8,
      "count": 25,
      "win_rate": 72.0,
      "avg_pnl": 225.50
    },
    "medium_confidence": {
      "threshold": 0.6,
      "count": 45,
      "win_rate": 55.6,
      "avg_pnl": 105.20
    },
    "low_confidence": {
      "threshold": 0.4,
      "count": 17,
      "win_rate": 41.2,
      "avg_pnl": -25.80
    }
  }
}
```

---

## CEO Analysis

Phase 15 - CEO speech and statement analysis from SEC filings.

#### `GET /ceo-analysis/quotes/{ticker}`
Get CEO quotes from SEC filings.

**Parameters**:
- `ticker` (str, required): Stock ticker
- `filing_type` (str, optional): 10-K, 10-Q, 8-K
- `limit` (int): Number of quotes (default: 10)

**Response**:
```json
{
  "ticker": "AAPL",
  "quotes": [
    {
      "text": "We are very excited about our services business...",
      "quote_type": "forward_looking",
      "source": "sec_filing",
      "filing_type": "10-K",
      "fiscal_period": "FY2024",
      "sentiment": 0.85,
      "published_at": "2024-11-02T00:00:00"
    }
  ],
  "total": 45
}
```

#### `POST /ceo-analysis/similar-statements`
Find similar CEO statements across companies.

**Request Body**:
```json
{
  "ticker": "AAPL",
  "statement": "We are investing heavily in AI",
  "top_k": 5
}
```

---

## Notifications

#### `POST /notifications/telegram/test`
Test Telegram bot connection.

**Response**:
```json
{
  "status": "success",
  "message": "Test message sent successfully"
}
```

#### `POST /notifications/slack/test`
Test Slack webhook.

#### `GET /notifications/history`
Get notification history.

---

## Logs

#### `GET /logs`
Get system logs with filtering.

**Parameters**:
- `level` (str): Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `category` (str): Log category
- `start_date` (datetime): Filter from date
- `end_date` (datetime): Filter to date
- `limit` (int): Number of logs (default: 100)
- `offset` (int): Pagination offset

**Response**:
```json
{
  "logs": [
    {
      "timestamp": "2025-11-26T10:30:15",
      "level": "INFO",
      "category": "trading",
      "message": "Signal generated for AAPL",
      "metadata": {
        "ticker": "AAPL",
        "action": "BUY",
        "confidence": 0.85
      }
    }
  ],
  "total": 1523,
  "has_more": true
}
```

#### `POST /logs`
Create new log entry.

---

## Incremental Cost Savings

Phase 14 - Track and optimize AI API costs.

#### `GET /incremental/dashboard`
Get cost savings dashboard.

**Response**:
```json
{
  "total_savings_usd": 1250.50,
  "total_baseline_cost_usd": 3500.00,
  "total_actual_cost_usd": 2249.50,
  "savings_rate_pct": 35.7,
  "optimizations": [
    {
      "name": "Gemini Free Tier Usage",
      "savings_usd": 450.00,
      "impact_pct": 36.0
    },
    {
      "name": "Prompt Caching",
      "savings_usd": 380.50,
      "impact_pct": 30.4
    },
    {
      "name": "Batch Processing",
      "savings_usd": 420.00,
      "impact_pct": 33.6
    }
  ],
  "monthly_trend": [...]
}
```

#### `GET /incremental/usage`
Get detailed API usage statistics.

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message here",
  "error_code": "INVALID_PARAMETER",
  "timestamp": "2025-11-26T10:30:15"
}
```

### Common HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limits

Default rate limits by permission level:
- **READONLY**: 60 requests/minute
- **TRADING**: 60 requests/minute
- **MASTER**: Unlimited

Rate limit info is returned in response headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

## Webhooks

The system can send webhooks for important events:

### Event Types
- `signal.generated`: New trading signal created
- `signal.approved`: Signal approved for execution
- `signal.executed`: Signal executed successfully
- `risk.alert`: Risk threshold exceeded
- `system.error`: Critical system error

### Webhook Payload
```json
{
  "event_type": "signal.generated",
  "timestamp": "2025-11-26T10:30:15",
  "data": {
    "signal_id": 123,
    "ticker": "AAPL",
    "action": "BUY",
    "confidence": 0.85
  }
}
```

---

## WebSocket Support

Real-time updates via WebSocket:

### Connect
```
ws://localhost:5000/ws
```

### Subscribe to Events
```json
{
  "action": "subscribe",
  "channels": ["signals", "news", "alerts"]
}
```

### Message Format
```json
{
  "channel": "signals",
  "event": "signal.generated",
  "data": {...}
}
```

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store API keys securely** (environment variables, secret managers)
3. **Implement retry logic** with exponential backoff
4. **Cache responses** where appropriate
5. **Monitor rate limits** and adjust request frequency
6. **Log all trading operations** for audit trail
7. **Test with paper trading** before live execution
8. **Set up webhooks** for critical events
9. **Use batch endpoints** when processing multiple items
10. **Implement circuit breakers** for external API calls

---

## SDK Examples

### Python
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:5000"

headers = {"X-API-Key": API_KEY}

# Get trading signals
response = requests.get(
    f"{BASE_URL}/signals",
    headers=headers,
    params={"status": "pending", "limit": 10}
)
signals = response.json()

# Generate signal from news
response = requests.post(
    f"{BASE_URL}/signals/generate",
    headers=headers,
    json={"article_id": 1234}
)
```

### JavaScript/TypeScript
```typescript
const API_KEY = "your_api_key";
const BASE_URL = "http://localhost:5000";

// Get performance metrics
const response = await fetch(
  `${BASE_URL}/reports/performance?start_date=2024-01-01&end_date=2024-12-31`,
  {
    headers: {
      "X-API-Key": API_KEY
    }
  }
);
const metrics = await response.json();
```

---

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check API key is correct
- Verify key has required permissions
- Check key hasn't expired

**429 Rate Limited**
- Reduce request frequency
- Implement request queuing
- Upgrade API key tier

**500 Internal Server Error**
- Check server logs
- Verify database connectivity
- Check external API availability

**Database Connection Errors**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database migrations are applied

---

## Global Macro

### Global Assessment

#### `GET /api/global-macro/market-map`
Get comprehensive market heatmap and status.

#### `GET /api/global-macro/country-risks`
Get country risk analysis (Geo-political, economic).

#### `GET /api/global-macro/analyze-event?event_text=...`
Analyze a specific global event text for impact.

#### `GET /api/global-macro/theme-risks/{ticker}`
Get thematic risks associated with a specific ticker.

---

## Auto Trade

### Control

#### `POST /api/auto-trade/start`
Start the automatic trading engine.

**Parameters**:
- `mode` (str): "real" or "paper"

#### `POST /api/auto-trade/stop`
Stop the automatic trading engine.

#### `GET /api/auto-trade/status`
Get current status of the auto-trading engine (running/stopped).

#### `GET /api/auto-trade/stats`
Get session statistics (uptime, trades executed, errors).

#### `POST /api/auto-trade/execute`
Manually trigger a trade execution cycle.

---

## Consensus Backtest

#### `POST /backtest/consensus`
Run a consensus-based backtest strategy.

**Request Body**:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "tickers": ["AAPL", "NVDA"],
  "strategies": ["news", "technical", "macro"]
}
```

#### `GET /backtest/consensus/list`
List all consensus backtest results.

#### `GET /backtest/consensus/{id}`
Get details of a specific consensus backtest.

---

## Portfolio Management

#### `GET /api/reports/portfolio`
Get real-time portfolio summary (supports KIS integration).

**Response**:
```json
{
  "active_positions": [
    {
       "ticker": "INTC",
       "signal_type": "KIS_REAL",
       "quantity": 10,
       "current_price": 25.50
    }
  ],
  "total_positions": 1,
  "avg_return": 1.25
}
```

#### `POST /api/reports/portfolio/analyze`
Run deep analysis on current portfolio (VaR, Concentration).

#### `POST /api/reports/portfolio/rebalance`
Generate rebalancing suggestions.

---

## Consensus System (Phase E1)

### Consensus Voting

#### `POST /api/consensus/vote`
Initiate a 3-AI consensus vote for a trading decision.

**Request Body**:
```json
{
  "ticker": "NVDA",
  "action": "BUY",
  "context": {
    "price": 495.50,
    "news_summary": "Strong Q4 earnings beat",
    "market_regime": "BULL"
  }
}
```

**Response**:
```json
{
  "approved": true,
  "votes": [
    {"ai": "claude", "vote": "approve", "confidence": 0.85},
    {"ai": "chatgpt", "vote": "approve", "confidence": 0.78},
    {"ai": "gemini", "vote": "approve", "confidence": 0.92}
  ],
  "consensus_strength": 0.85,
  "decision": "APPROVED"
}
```

#### `GET /api/consensus/history?limit=50`
Get consensus voting history.

#### `GET /api/consensus/stats`
Get consensus system statistics.

---

## Position Management (Phase E3)

#### `GET /api/positions`
Get all active positions.

**Response**:
```json
{
  "positions": [
    {
      "ticker": "NVDA",
      "entry_price": 450.00,
      "current_price": 495.50,
      "quantity": 10,
      "dca_count": 2,
      "unrealized_pnl": 455.00,
      "status": "active"
    }
  ]
}
```

#### `POST /api/positions`
Create a new position.

#### `PUT /api/positions/{ticker}`
Update position (DCA, trim, exit).

#### `GET /api/positions/{ticker}`
Get specific position details.

---

## Deep Reasoning (Phase 14)

#### `POST /api/reasoning/analyze`
Perform 3-step CoT (Chain-of-Thought) analysis.

**Request Body**:
```json
{
  "news_text": "Google announces TPU v6 with 4x performance",
  "enable_web_verification": true
}
```

**Response**:
```json
{
  "primary_impact": {
    "ticker": "GOOGL",
    "impact": "Strong positive",
    "reasoning": "Direct beneficiary of new chip..."
  },
  "hidden_beneficiary": {
    "ticker": "AVGO",
    "reasoning": "Broadcom designs interconnects for TPUs..."
  },
  "verification_sources": [
    "https://example.com/broadcom-google-partnership"
  ]
}
```

---

## AI Quality Monitoring (Phase C)

#### `GET /api/ai-quality/bias-check`
Check for AI bias in recent decisions.

#### `POST /api/ai-quality/debate`
Initiate AI debate on a controversial decision.

#### `GET /api/ai-quality/model-comparison`
Compare performance of different AI models.

---

## Cost Monitoring

#### `GET /api/cost/summary`
Get AI API cost summary.

**Response**:
```json
{
  "total_cost_this_month": 2.45,
  "breakdown": {
    "claude": 0.85,
    "gemini": 0.95,
    "chatgpt": 0.65
  },
  "projected_monthly": 2.89
}
```

#### `GET /api/cost/history?months=3`
Get cost history.

---

## Tax Loss Harvesting (Option 10)

#### `GET /api/tax/opportunities`
Find tax loss harvesting opportunities.

#### `POST /api/tax/execute`
Execute tax loss harvesting trade.

#### `GET /api/tax/report?year=2025`
Generate annual tax report.

---

## SEC Analysis (Phase 15)

#### `POST /api/sec/analyze-filing`
Analyze SEC filing (10-K, 10-Q).

**Request Body**:
```json
{
  "ticker": "AAPL",
  "filing_type": "10-K",
  "year": 2024
}
```

#### `GET /api/ceo-analysis/search?query=AI+strategy`
Search CEO statements from earnings calls.

---

## Incremental Updates (Phase 16)

#### `POST /api/incremental/update`
Trigger incremental data update.

#### `GET /api/incremental/status`
Get incremental update status.

---

## KIS Integration (Phase 11)

#### `POST /api/kis/login`
Login to KIS (Korea Investment & Securities) API.

#### `GET /api/kis/balance`
Get account balance.

#### `POST /api/kis/order`
Place order via KIS.

#### `POST /api/kis-sync/start`
Start real-time KIS synchronization.

---

**Last Updated**: 2025-12-12
**API Version**: 1.2.0
**Documentation Version**: Phase E Complete (36 API Routers)
**Total Endpoints**: 100+

---

## API Router List (완전)

| Router | Prefix | Phase | 설명 |
|--------|--------|-------|------|
| `consensus_router.py` | `/api/consensus` | E1 | 3-AI 투표 시스템 |
| `position_router.py` | `/api/positions` | E3 | 포지션 관리 |
| `reasoning_api.py` | `/api/reasoning` | 14 | Deep Reasoning |
| `signals_router.py` | `/api/signals` | 9 | 트레이딩 시그널 |
| `ai_signals_router.py` | `/api/ai-signals` | E | AI 시그널 |
| `news_router.py` | `/api/news` | 8 | 뉴스 분석 |
| `backtest_router.py` | `/api/backtest` | 10 | 백테스팅 |
| `kis_integration_router.py` | `/api/kis` | 11 | KIS API |
| `kis_sync_router.py` | `/api/kis-sync` | 11 | KIS 동기화 |
| `auto_trade_router.py` | `/api/auto-trade` | B | 자동매매 |
| `reports_router.py` | `/api/reports` | 15 | 리포트 생성 |
| `monitoring_router.py` | `/api/monitoring` | 7 | 모니터링 |
| `ai_review_router.py` | `/api/ai-review` | 12 | AI 검토 |
| `ai_chat_router.py` | `/api/ai-chat` | 14 | AI 채팅 |
| `ai_quality_router.py` | `/api/ai-quality` | C | AI 품질 |
| `ceo_analysis_router.py` | `/api/ceo-analysis` | 15 | CEO 분석 |
| `sec_router.py` | `/api/sec` | 15 | SEC 문서 |
| `sec_semantic_search.py` | `/api/sec-search` | 15 | SEC 검색 |
| `feeds_router.py` | `/api/feeds` | 16 | RSS 피드 |
| `incremental_router.py` | `/api/incremental` | 16 | 증분 업데이트 |
| `forensics_router.py` | `/api/forensics` | 15 | Forensic 회계 |
| `options_flow_router.py` | `/api/options-flow` | 15 | 옵션 플로우 |
| `global_macro_router.py` | `/api/global-macro` | C | 글로벌 매크로 |
| `tax_routes.py` | `/api/tax` | Option 10 | 세금 최적화 |
| `notifications_router.py` | `/api/notifications` | 9 | 알림 관리 |
| `logs_router.py` | `/api/logs` | 7 | 로그 조회 |
| `auth_router.py` | `/api/auth` | 7 | 인증 |
| `phase_integration_router.py` | `/api/phase` | E | Phase 통합 |
| `cost_monitoring.py` | `/api/cost` | B | 비용 모니터링 |
| `news_filter.py` | `/api/news-filter` | 8 | 뉴스 필터 |
| `simple_news_router.py` | `/api/simple-news` | 8 | 간단 뉴스 |
| `gemini_free_router.py` | `/api/gemini-free` | 14 | Gemini 무료 |
| `mock_router.py` | `/api/mock` | - | 테스트용 Mock |
