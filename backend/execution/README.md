# Smart Order Execution Algorithms

## Overview

Production-grade order execution algorithms for minimizing market impact and achieving optimal fill prices.

**Integration Status**: ✅ **Tier 1 Complete** (Gemini Code Review: 4/5)

## Algorithms

### 1. TWAP (Time-Weighted Average Price)

**Strategy**: Distribute order uniformly over time period.

**Best for**:
- Consistent execution without information leakage
- When you don't have access to volume data
- Small-medium sized orders

**Example**:
```python
from execution import execute_twap

fills = await execute_twap(
    ticker="AAPL",
    total_quantity=100,      # Buy 100 shares
    duration_minutes=30,     # Over 30 minutes
    slice_interval_seconds=60  # Every 60 seconds
)
# Result: 30 orders of ~3.33 shares each
```

**Pros**:
- ✅ Simple and predictable
- ✅ No volume data required
- ✅ Low implementation complexity

**Cons**:
- ⚠️ Doesn't account for natural volume patterns
- ⚠️ May trade during low-liquidity periods

---

### 2. VWAP (Volume-Weighted Average Price)

**Strategy**: Distribute order proportionally to historical volume profile.

**Best for**:
- Minimizing market impact
- Large orders
- When historical volume data is available

**Example**:
```python
from execution import execute_vwap

fills = await execute_vwap(
    ticker="AAPL",
    total_quantity=500,        # Buy 500 shares
    start_time_str="09:00",    # Market open
    end_time_str="15:30",      # Market close
    volume_profile_days=5      # Use 5-day avg volume
)
# Result: More shares traded at open/close (high volume), fewer midday
```

**Pros**:
- ✅ Minimizes market impact
- ✅ Follows natural volume flow
- ✅ Industry-standard benchmark

**Cons**:
- ⚠️ Requires historical volume data
- ⚠️ More complex implementation
- ⚠️ May miss price opportunities

---

## Architecture

### Class Hierarchy

```
OrderExecutor (ABC)
├── TWAPExecutor
└── VWAPExecutor
```

### Broker Abstraction

```
BrokerAPI (ABC)
├── SimulatedBroker (Phase 4-5: Testing)
└── KISBroker (Phase 6: Production)
```

**Current**: Using `SimulatedBroker` for testing
**Phase 6**: Implement `KISBroker` for real Korean market API

---

## Usage

### Basic Usage with Executors

```python
import asyncio
from execution import TWAPExecutor, VWAPExecutor, SimulatedBroker

async def main():
    # Create broker
    broker = SimulatedBroker(commission_rate=0.00015)

    # Create executor
    executor = TWAPExecutor(broker)

    # Execute order
    fills = await executor.execute(
        ticker="AAPL",
        total_quantity=100,
        duration_minutes=10,
        slice_interval_seconds=30
    )

    # Get summary
    summary = executor.get_execution_summary()
    print(f"Avg fill price: ${summary['avg_fill_price']:.2f}")
    print(f"Total commission: ${summary['total_commission']:.2f}")
    print(f"Number of slices: {summary['num_slices']}")

asyncio.run(main())
```

### Integration with TradingAgent

```python
from ai.trading_agent import TradingAgent
from execution import execute_twap

async def execute_ai_decision(ticker: str):
    # 1. Get AI decision
    agent = TradingAgent()
    decision = await agent.analyze(ticker)

    if decision.action == "BUY":
        # 2. Calculate quantity based on position_size
        quantity = calculate_quantity(decision.position_size)

        # 3. Execute using TWAP
        fills = await execute_twap(
            ticker=ticker,
            total_quantity=quantity,
            duration_minutes=30
        )

        return fills
```

### Integration with Backtest Engine

```python
from backtesting import BacktestEngine, Strategy, OrderEvent
from execution import TWAPExecutor

class TWAPStrategy(Strategy):
    def __init__(self, event_queue, data_handler):
        super().__init__(event_queue, data_handler)
        self.executor = TWAPExecutor(SimulatedBroker())

    async def on_order(self, order: OrderEvent):
        # Execute order using TWAP instead of market order
        fills = await self.executor.execute(
            ticker=order.symbol,
            total_quantity=order.quantity,
            duration_minutes=5
        )
```

---

## Configuration

### Commission Rate

Set in [config.py](../config.py) or pass to broker:

```python
from config import get_settings

settings = get_settings()
broker = SimulatedBroker(
    commission_rate=0.00015  # 0.015% (KRX standard)
)
```

### Market Hours

VWAP respects market hours from config:

```python
# config.py
trading_start_time: str = "09:00"  # Market open
trading_end_time: str = "15:30"    # Market close
```

---

## Testing

### Run Demo

```bash
cd backend
python -m execution.executors
```

**Output**:
```
[TWAP] Starting: AAPL 100 shares over 5min
[TWAP] Plan: 5 slices, avg 20.00 per slice
[TWAP] Slice 1/5: 20 @ $100.09
[TWAP] Slice 2/5: 20 @ $99.95
...
[TWAP] Completed: 100 @ avg $100.03
```

### Unit Tests

```python
# Test TWAP slicing
async def test_twap_slicing():
    executor = TWAPExecutor(SimulatedBroker())
    fills = await executor.execute(
        ticker="TEST",
        total_quantity=100,
        duration_minutes=5,
        slice_interval_seconds=1  # Fast for testing
    )

    assert len(fills) == 5
    assert sum(f.quantity for f in fills) == 100
```

---

## Performance Metrics

### Execution Summary

After execution, get detailed metrics:

```python
summary = executor.get_execution_summary()

{
    'total_quantity': 100,
    'avg_fill_price': 100.03,
    'total_commission': 1.50,
    'num_slices': 5,
    'fills': [
        {'timestamp': '2025-11-09T10:00:00', 'quantity': 20, 'fill_price': 100.09, ...},
        ...
    ]
}
```

### Slippage Analysis

Compare execution price vs benchmark:

```python
benchmark_price = 100.00  # VWAP of the period
execution_price = summary['avg_fill_price']
slippage_bps = ((execution_price - benchmark_price) / benchmark_price) * 10000

print(f"Slippage: {slippage_bps:.1f} bps")
```

---

## Phase 6: Production Deployment

### KIS API Integration

```python
from execution import BrokerAPI

class KISBroker(BrokerAPI):
    """한국투자증권 API 연동"""

    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.token = self._get_access_token()

    async def place_order(self, ticker, quantity, order_type='MKT', limit_price=None):
        # KIS API 주문 전송
        response = await self._post_order(ticker, quantity, order_type, limit_price)

        return Fill(
            timestamp=datetime.now(),
            ticker=ticker,
            quantity=response['filled_qty'],
            fill_price=response['avg_price'],
            commission=response['commission']
        )

    async def get_historical_volume_profile(self, ticker, days=5):
        # KIS API에서 분봉 데이터 가져오기
        bars = await self._get_minute_bars(ticker, days)

        # 시간대별 평균 거래량 계산
        profile = bars.groupby(bars.index.time)['volume'].mean()
        return profile / profile.sum()
```

### Liquidity-Aware Enhancement (Future)

```python
class LiquidityAwareExecutor(OrderExecutor):
    """
    Adjust slice size based on real-time market depth.
    """

    async def execute(self, ticker, total_quantity, ...):
        while remaining_quantity > 0:
            # Get current order book
            depth = await self.broker.get_market_depth(ticker)

            # Calculate safe slice size (e.g., 10% of bid/ask volume)
            safe_size = min(
                depth['bid_volume'] * 0.10,
                depth['ask_volume'] * 0.10
            )

            slice_qty = min(safe_size, remaining_quantity)

            # Execute slice
            fill = await self.broker.place_order(ticker, slice_qty)
            ...
```

---

## Files

- [executors.py](executors.py) - Main execution algorithms (520 lines)
- [__init__.py](__init__.py) - Module exports
- [README.md](README.md) - This file

---

## Improvements from Gemini Version

Gemini's original version (4/5 rating) had these issues, now fixed:

1. ✅ **Missing `Optional` import** - Added typing imports
2. ✅ **No error handling** - Added try/except in execution loops
3. ✅ **No execution summary** - Added `get_execution_summary()` method
4. ✅ **No broker abstraction** - Created `BrokerAPI` abstract class
5. ✅ **No integration examples** - Added TradingAgent/BacktestEngine examples
6. ✅ **No logging** - Added comprehensive logging

---

## Next Steps

1. **Week 2-3**: Test with backtest engine (Phase 4)
2. **Phase 6**: Implement `KISBroker` for real trading
3. **Phase 6**: Add Liquidity-Aware algorithm
4. **Phase 7**: Monitor execution quality metrics in Grafana

---

## References

- **MASTER_GUIDE.md**: Section 3.5 (Smart Execution)
- **GEMINI_CODE_REVIEW.md**: Tier 1 File Review (Score: 4/5)
- **Industry Standard**: VWAP is used by institutional traders globally

---

**Status**: ✅ Production-ready (simulation mode)
**AI Cost**: $0 (rule-based algorithms)
**Added**: 2025-11-09 (Gemini Tier 1 Integration)
**Phase 6 Ready**: Just needs broker API implementation
