# Event-Driven Backtest Engine

## Overview

Event-driven backtesting system that simulates trading strategies with realistic market conditions.

**Integration Status**: ✅ **Tier 1 Complete** (Gemini Code Review: 4/5)

## Features

### Core Architecture
- **Event-Driven Design**: Market → Signal → Order → Fill event flow
- **Constitution Rules**: Automatic enforcement from [config.py](../config.py)
- **Slippage Modeling**: Realistic execution with bid-ask spread simulation
- **Commission Modeling**: 0.015% default (KRX standard)
- **Performance Metrics**: Sharpe Ratio, Max Drawdown, Win Rate

### Constitution Rules Integration

All rules from [config.py:74-83](../config.py#L74-L83) are automatically enforced:

```python
conviction_threshold_buy: 0.7        # 70% confidence required
conviction_threshold_sell: 0.6       # 60% confidence required
max_position_size_pct: 5.0           # Max 5% per position
max_positions: 10                    # Max 10 concurrent positions
kill_switch_daily_loss_pct: 2.0      # 2% daily loss limit
```

### Performance Metrics

Calculated automatically after backtest:

1. **Total Return**: Portfolio growth from initial capital
2. **Sharpe Ratio**: Risk-adjusted return (annualized)
3. **Max Drawdown (MDD)**: Largest peak-to-trough decline
4. **Win Rate**: Percentage of profitable trades
5. **Total PnL**: Sum of all trade profits/losses

## Usage

### Basic Example

```python
from backtesting import BacktestEngine, DataHandler, Strategy

# 1. Create your data handler (subclass DataHandler)
class MyDataHandler(DataHandler):
    async def next(self) -> bool:
        # Load next bar and emit MarketEvent
        pass

    def get_latest_price(self, symbol: str) -> float:
        # Return current price
        pass

# 2. Create your strategy (subclass Strategy)
class MyStrategy(Strategy):
    async def on_market(self, event: MarketEvent):
        # Analyze market and emit SignalEvent
        if should_buy:
            self.event_queue.put(
                SignalEvent(
                    timestamp=event.timestamp,
                    symbol='AAPL',
                    action='BUY',
                    conviction=0.75
                )
            )

# 3. Run backtest
engine = BacktestEngine(
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_capital=100000.0,
    DataHandlerCls=MyDataHandler,
    StrategyCls=MyStrategy,
    commission_rate=0.00015,  # 0.015%
    slippage_bps=1.0          # 1 basis point
)

results = await engine.run()
print(results)
```

### Output Example

```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 100000.0,
  "final_value": 115234.50,
  "total_return_pct": 15.23,
  "sharpe_ratio": 1.85,
  "max_drawdown_pct": -8.45,
  "win_rate": 0.62,
  "total_trades": 45,
  "total_pnl": 15234.50
}
```

## Event Flow

```
1. DataHandler.next()
   → MarketEvent(timestamp, data)

2. Strategy.on_market(MarketEvent)
   → SignalEvent(symbol, action, conviction)

3. Portfolio.on_signal(SignalEvent)
   → [Constitution Check]
   → OrderEvent(symbol, quantity)

4. Broker.on_order(OrderEvent)
   → [Apply slippage & commission]
   → FillEvent(symbol, quantity, fill_price, commission)

5. Portfolio.on_fill(FillEvent)
   → [Update cash & positions]
   → [Record trade history]
```

## Constitution Rules Pre-Check

Before creating orders, the Portfolio enforces:

| Rule | Check | Action if Failed |
|------|-------|------------------|
| Conviction threshold | `conviction >= threshold` | Reject signal |
| Max positions | `len(positions) < max_positions` | Reject new positions |
| Position size | `quantity * price <= max_position_value` | Reduce quantity |
| Available cash | `cost <= portfolio.cash` | Reduce quantity |

## Integration with Existing System

### With TradingAgent

```python
from ai.trading_agent import TradingAgent
from backtesting import Strategy, SignalEvent

class ClaudeStrategy(Strategy):
    """Strategy that uses TradingAgent for decisions."""

    def __init__(self, event_queue, data_handler):
        super().__init__(event_queue, data_handler)
        self.agent = TradingAgent()

    async def on_market(self, event: MarketEvent):
        for symbol in event.data.keys():
            # Get TradingDecision from Claude
            decision = await self.agent.analyze(symbol)

            # Convert to SignalEvent
            if decision.action in ['BUY', 'SELL']:
                signal = SignalEvent(
                    timestamp=event.timestamp,
                    symbol=symbol,
                    action=decision.action,
                    conviction=decision.conviction
                )
                self.event_queue.put(signal)
```

### With FeatureStore

```python
from data.feature_store import FeatureStore

class MyStrategy(Strategy):
    def __init__(self, event_queue, data_handler):
        super().__init__(event_queue, data_handler)
        self.features = FeatureStore()

    async def on_market(self, event: MarketEvent):
        # Get features from FeatureStore (cached!)
        features = await self.features.get_features('AAPL', event.timestamp)

        # Use momentum for signal
        if features['mom_20d'] > 0.05:
            self.event_queue.put(SignalEvent(...))
```

## Testing

Run demo backtest:

```bash
cd backend
python -m backtesting.engine
```

## Files

- [engine.py](engine.py) - Main backtest engine (510 lines)
- [__init__.py](__init__.py) - Module exports
- [README.md](README.md) - This file

## Improvements from Gemini Version

Gemini's original version (4/5 rating) had these issues, now fixed:

1. ✅ **Missing `json` import** - Added for results serialization
2. ✅ **Incomplete win rate calculation** - Now tracks actual trade PnL
3. ✅ **No Constitution rules** - Fully integrated with config.py
4. ✅ **No integration examples** - Added TradingAgent/FeatureStore examples
5. ✅ **Missing type hints** - Added Optional, Dict, List imports

## Next Steps

1. **Week 2-3**: Integrate with actual strategies (Phase 4 Tasks 2-7)
2. **Phase 4**: Use for AI Model A/B Testing (Haiku vs Sonnet)
3. **Phase 5**: Test CVaR optimizer with backtests
4. **Phase 6**: Validate TWAP/VWAP execution algorithms

## References

- **MASTER_GUIDE.md**: Section 3.4 (Backtesting), 5.6 (Event-Driven Architecture)
- **GEMINI_CODE_REVIEW.md**: Tier 1 File Review (Score: 4/5)
- **Constitution Rules**: [config.py:74-83](../config.py#L74-L83)

---

**Status**: ✅ Production-ready (with demo strategies)
**AI Cost**: $0 (rule-based simulation)
**Added**: 2025-11-09 (Gemini Tier 1 Integration)
