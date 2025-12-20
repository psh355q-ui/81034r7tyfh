# Paper Trading Guide

## Overview

The Paper Trading system allows you to test your AI trading strategy with **real-time market data** but without risking real money. It's the perfect way to validate your strategy before going live.

## Features

- **Real-time Market Data**: Fetches live quotes using Yahoo Finance API
- **Live Portfolio Tracking**: Track positions, P&L, and cash in real-time
- **AI Decision Making**: Integrates Phase 5 Ensemble Strategy for intelligent decisions
- **Execution Simulation**: Simulates order execution with realistic slippage
- **Metrics & Alerts**: Full monitoring with Prometheus metrics and alerts
- **Flexible Configuration**: Customize capital, tickers, intervals, and more

## Quick Start

### 1. Quick Test (5 minutes)

```bash
cd backend
python run_paper_trading.py --quick
```

This runs a 5-minute simulation with 3 tickers (AAPL, NVDA, MSFT).

### 2. Full Trading Session (1 hour)

```bash
python run_paper_trading.py --duration 1h --capital 100000
```

### 3. Continuous Trading

```bash
python run_paper_trading.py --continuous
```

Press `Ctrl+C` to stop when ready.

## Command-Line Options

```
Options:
  --duration DURATION       Trading duration (e.g., 5m, 1h, 30s)
  --capital CAPITAL         Initial capital (default: 100000)
  --tickers TICKER [...]    Tickers to trade (default: AAPL NVDA MSFT GOOGL AMZN)
  --interval SECONDS        Decision interval in seconds (default: 60)
  --max-positions N         Maximum number of positions (default: 10)
  --quick                   Quick test (5 minutes, 3 tickers)
  --continuous              Run until manual stop (Ctrl+C)
  --verbose                 Enable debug logging
  --no-ai                   Disable AI (use mock strategy)
  --no-monitoring           Disable metrics/alerting
```

## Examples

### Example 1: Tech Stocks Portfolio

```bash
python run_paper_trading.py \
  --tickers AAPL NVDA MSFT GOOGL AMZN TSLA META \
  --capital 200000 \
  --duration 2h \
  --max-positions 15
```

### Example 2: Quick Day Trading Test

```bash
python run_paper_trading.py \
  --tickers AAPL TSLA \
  --capital 50000 \
  --interval 15 \
  --duration 30m
```

### Example 3: Overnight Trading Simulation

```bash
python run_paper_trading.py \
  --tickers AAPL NVDA MSFT GOOGL AMZN \
  --duration 8h \
  --interval 300 \
  --verbose
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Paper Trading Engine                       │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────┐      ┌──────────────────┐    │
│  │ Market Data      │      │  Live Portfolio   │    │
│  │ Fetcher          │      │  Tracker          │    │
│  │                  │      │                   │    │
│  │ - Real-time      │      │ - Positions       │    │
│  │   quotes         │      │ - Orders          │    │
│  │ - Price caching  │      │ - P&L tracking    │    │
│  │ - Batch fetching │      │ - Trade history   │    │
│  └──────────────────┘      └──────────────────┘    │
│           │                         │                │
│           └─────────┬───────────────┘                │
│                     ▼                                │
│        ┌─────────────────────────┐                  │
│        │  Trading Loop           │                  │
│        │                         │                  │
│        │  1. Fetch market data   │                  │
│        │  2. Update prices       │                  │
│        │  3. Make decisions      │                  │
│        │  4. Execute orders      │                  │
│        │  5. Record metrics      │                  │
│        └─────────────────────────┘                  │
│                     │                                │
│         ┌───────────┴───────────┐                   │
│         ▼                       ▼                    │
│  ┌─────────────┐       ┌────────────────┐          │
│  │   AI        │       │  Metrics &     │          │
│  │   Strategy  │       │  Alerting      │          │
│  │   (Phase 5) │       │  (Phase 7)     │          │
│  └─────────────┘       └────────────────┘          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Components

### 1. MarketDataFetcher

Fetches real-time market data from Yahoo Finance:

```python
from paper_trading import MarketDataFetcher

fetcher = MarketDataFetcher(cache_ttl_seconds=15)

# Get single quote
quote = await fetcher.get_quote("AAPL")
print(f"AAPL: ${quote.price:.2f}")

# Get multiple quotes
quotes = await fetcher.get_quotes_batch(["AAPL", "NVDA", "MSFT"])
```

**Features:**
- Real-time price fetching
- 15-second cache TTL
- Batch fetching support
- Graceful fallback to cached prices

### 2. LivePortfolio

Tracks portfolio state in real-time:

```python
from paper_trading import LivePortfolio

portfolio = LivePortfolio(
    initial_cash=100000.0,
    commission_rate=0.001,  # 0.1%
    max_positions=10,
)

# Create and fill order
order = portfolio.create_order("AAPL", "BUY", 10, 150.0)
portfolio.fill_order(order, fill_price=150.50, slippage_bps=2.0)

# Check position
position = portfolio.get_position("AAPL")
print(f"P&L: ${position.unrealized_pnl:.2f}")
```

**Features:**
- Position tracking with live P&L
- Order management (pending, filled, rejected)
- Transaction history
- Real-time valuation
- Commission and slippage tracking

### 3. PaperTradingEngine

Main engine orchestrating everything:

```python
from paper_trading import PaperTradingEngine, PaperTradingConfig

config = PaperTradingConfig(
    initial_cash=100000.0,
    tickers=["AAPL", "NVDA", "MSFT"],
    decision_interval_seconds=60,
    max_positions=10,
    enable_ai=True,
    enable_monitoring=True,
)

engine = PaperTradingEngine(config)

# Run for 30 minutes
await engine.run_for_duration(1800)

# Print results
engine.print_summary()
```

## Trading Strategy

The paper trading engine supports multiple strategy modes:

### 1. AI Strategy (Default)

Uses Phase 5 Ensemble Strategy:
- ChatGPT for regime detection
- Gemini for stock screening
- Claude for final analysis
- Risk management integration

### 2. Custom Strategy

Provide your own strategy function:

```python
async def my_strategy(engine, market_data):
    """Custom trading strategy."""
    decisions = []

    for ticker, quote in market_data.items():
        # Your logic here
        if should_buy(ticker, quote):
            decisions.append({
                "ticker": ticker,
                "action": "BUY",
                "position_size": 5.0,  # 5% of portfolio
                "conviction": 0.8,
                "reason": "Custom signal",
            })

    return decisions

engine.set_custom_strategy(my_strategy)
```

### 3. Mock Strategy

Simple momentum-based strategy for testing:
- 15% chance to trade each ticker
- Buy if no position and cash available
- Sell if position has >5% gain or <-3% loss

## Performance Metrics

The system tracks comprehensive metrics:

### Portfolio Metrics
- Total value (cash + positions)
- Realized P&L
- Unrealized P&L
- Total return percentage
- Exposure percentage

### Trading Metrics
- Number of trades
- Total commissions paid
- Win rate
- Average trade P&L

### Execution Metrics
- Decision count
- Execution count
- Average slippage

## Output Example

```
======================================================================
PAPER TRADING SUMMARY
======================================================================
Duration: 1800 seconds

Initial Capital: $100,000.00
Final Value:     $102,450.00
Total Return:    $+2,450.00 (+2.45%)

Realized P&L:    $+1,200.00
Unrealized P&L:  $+1,250.00

Current Cash:    $45,300.00
Positions:       5
Exposure:        55.6%

Total Trades:    12
Commissions:     $65.43
Decisions Made:  45
======================================================================

Current Positions:
----------------------------------------------------------------------
AAPL   |  100 shares @ $ 145.20 | Current: $ 148.50 | P&L: $  +330.00 ( +2.27%)
NVDA   |   50 shares @ $ 182.00 | Current: $ 186.30 | P&L: $  +215.00 ( +2.36%)
MSFT   |   80 shares @ $ 398.50 | Current: $ 405.20 | P&L: $  +536.00 ( +1.68%)
GOOGL  |   40 shares @ $ 165.80 | Current: $ 168.90 | P&L: $  +124.00 ( +1.87%)
AMZN   |   25 shares @ $ 201.30 | Current: $ 203.50 | P&L: $   +55.00 ( +1.09%)
----------------------------------------------------------------------
```

## Integration with AI System

### Phase 5 Integration (Ensemble Strategy)

When AI is enabled, the paper trading engine uses the full ensemble:

```python
# In paper_trading_engine.py
from strategies import EnsembleStrategy

ai_strategy = EnsembleStrategy()

# Make decision
decision_result = await ai_strategy.make_decision(
    ticker=ticker,
    market_context=context,
)
```

### Phase 6 Integration (Smart Execution)

Orders are executed using smart algorithms:

```python
from execution import SmartExecutor

executor = SmartExecutor()

# Execute with optimal algorithm
result = await executor.execute_with_smart_routing(
    trading_decision=decision,
    current_price=price,
    urgency=urgency_level,
)
```

### Phase 7 Integration (Monitoring)

Full monitoring and alerting:

```python
# Record metrics
metrics_collector.record_trading_decision(
    ticker=ticker,
    action=action,
    conviction=conviction,
    latency_seconds=latency,
)

# Send alerts
await alert_manager.alert_trade_executed(
    ticker=ticker,
    action=action,
    shares=shares,
    price=price,
)
```

## Best Practices

### 1. Start Small

Begin with quick tests before long sessions:

```bash
# 5-minute test
python run_paper_trading.py --quick

# 30-minute test
python run_paper_trading.py --duration 30m
```

### 2. Monitor Performance

Use verbose logging to understand decisions:

```bash
python run_paper_trading.py --verbose --duration 1h
```

### 3. Test Different Configurations

Try various setups to find optimal parameters:

```bash
# Conservative (fewer positions, longer intervals)
python run_paper_trading.py --max-positions 5 --interval 300

# Aggressive (more positions, shorter intervals)
python run_paper_trading.py --max-positions 20 --interval 30
```

### 4. Compare Strategies

Test with and without AI:

```bash
# With AI
python run_paper_trading.py --duration 1h

# Without AI (mock strategy)
python run_paper_trading.py --duration 1h --no-ai
```

### 5. Respect Market Hours

While the system works 24/7, consider market hours for realistic testing:
- **Regular hours**: 9:30 AM - 4:00 PM ET (Monday-Friday)
- **Pre-market**: 4:00 AM - 9:30 AM ET
- **After-hours**: 4:00 PM - 8:00 PM ET

## Limitations

1. **Simulated Execution**: Slippage is estimated, not actual
2. **Market Impact**: Assumes orders don't affect market prices
3. **Data Latency**: Yahoo Finance has ~15-minute delay for free tier
4. **No Order Book**: Cannot simulate limit orders or market depth
5. **Simplified Fills**: All orders fill at estimated price

## Next Steps

After successful paper trading:

1. **Analyze Results**: Review P&L, win rate, and execution quality
2. **Tune Strategy**: Adjust conviction thresholds and position sizing
3. **Live Trading**: Connect to real broker API (한국투자증권)
4. **Scale Up**: Increase capital and number of positions

## Troubleshooting

### Issue: No market data available

**Solution**: Check internet connection and Yahoo Finance availability:
```bash
python -c "import yfinance; print(yfinance.Ticker('AAPL').info)"
```

### Issue: Orders not executing

**Solution**: Check capital and position limits:
- Ensure sufficient cash for orders
- Check max_positions limit
- Verify tickers are valid

### Issue: Slow performance

**Solution**: Adjust intervals and reduce tickers:
```bash
python run_paper_trading.py --interval 60 --tickers AAPL NVDA
```

## Conclusion

The Paper Trading system provides a safe and realistic environment to test your AI trading strategy. Use it extensively before deploying with real money!

**Remember**: Paper trading success doesn't guarantee live trading success, but it's an essential validation step.

---

*Generated by AI Trading System Team*
*Date: 2025-11-15*
