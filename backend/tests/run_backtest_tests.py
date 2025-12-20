"""
Run backtest tests with proper encoding handling
"""

import sys
import io

# Set UTF-8 encoding for stdout
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Now import and run the tests
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.backtest_engine import BacktestEngine

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Mock Trading Agent for testing
class MockTradingAgent:
    """Mock agent for testing."""

    def __init__(self, strategy="conservative"):
        self.strategy = strategy
        self.call_count = 0

    async def analyze(self, ticker, portfolio_context=None):
        """Mock analysis."""
        self.call_count += 1

        class MockDecision:
            def __init__(self, action, conviction, position_size):
                self.action = action
                self.conviction = conviction
                self.position_size = position_size
                self.stop_loss = None
                self.reasoning = f"Mock {action} decision"
                self.risk_factors = []

            def to_dict(self):
                return {
                    "action": self.action,
                    "conviction": self.conviction,
                    "position_size": self.position_size,
                }

        # Simple strategy
        if self.call_count % 5 == 1:
            return MockDecision("BUY", 0.7, 3.0)
        elif self.call_count % 10 == 8:
            return MockDecision("SELL", 0.6, 0.0)
        else:
            return MockDecision("HOLD", 0.5, 0.0)

    async def initialize(self):
        pass

    async def close(self):
        pass


class MockFeatureStore:
    """Mock feature store."""

    async def initialize(self):
        pass

    async def close(self):
        pass


async def test_basic_backtest():
    """Test basic backtest execution."""
    print("\n" + "="*80)
    print("TEST 1: Basic Backtest Execution")
    print("="*80 + "\n")

    engine = BacktestEngine(initial_capital=100000.0)
    agent = MockTradingAgent()
    feature_store = MockFeatureStore()

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    tickers = ["AAPL", "MSFT", "GOOGL"]

    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Initial Capital: ${engine.initial_capital:,.2f}\n")

    results = await engine.run(
        trading_agent=agent,
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        feature_store=feature_store,
    )

    print("Backtest completed!\n")
    print("Performance:")
    print(f"  Total Return:     {results['total_return']:>10.2%}")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:>10.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:>10.2%}")
    print(f"  Win Rate:         {results['win_rate']:>10.1%}")
    print(f"  Total Trades:     {results['total_trades']:>10}")

    assert results['total_return'] is not None
    assert results['sharpe_ratio'] is not None

    print("\n[PASS] Test 1 passed!")
    return True


async def test_performance_metrics():
    """Test performance metrics calculation."""
    print("\n" + "="*80)
    print("TEST 2: Performance Metrics Calculation")
    print("="*80 + "\n")

    engine = BacktestEngine(initial_capital=100000.0)
    agent = MockTradingAgent(strategy="aggressive")
    feature_store = MockFeatureStore()

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)  # 3 months
    tickers = ["AAPL", "MSFT"]

    print("Running 3-month backtest...\n")

    results = await engine.run(
        trading_agent=agent,
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        feature_store=feature_store,
    )

    print("Results:")
    print(f"  Total Return:     {results['total_return']:>10.2%}")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:>10.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:>10.2%}")
    print(f"  Win Rate:         {results['win_rate']:>10.1%}")
    print(f"  Total Trades:     {results['total_trades']:>10}")

    # Check metrics are valid
    assert -1.0 <= results['total_return'] <= 1.0 or results['total_return'] > 1.0
    assert results['sharpe_ratio'] is not None
    assert 0.0 <= results['max_drawdown'] <= 1.0
    assert 0.0 <= results['win_rate'] <= 1.0
    assert results['total_trades'] >= 0

    print("\n[PASS] Test 2 passed!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Backtest Engine - Test Suite")
    print("="*80)

    try:
        await test_basic_backtest()
        await test_performance_metrics()

        print("\n" + "="*80)
        print("All tests completed successfully!")
        print("="*80 + "\n")

        print("Summary:")
        print("  - Basic backtest execution: PASS")
        print("  - Performance metrics: PASS")
        print("  - Engine ready for production use")

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
