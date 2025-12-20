"""
Simple Backtest Engine Test - Mock Data
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# Handle UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.backtest_engine import BacktestEngine


# Mock Trading Agent
@dataclass
class MockDecision:
    """Mock trading decision."""
    action: str
    position_size: float  # Changed from position_size_pct
    conviction: float
    reasoning: str
    stop_loss: float = None  # Added stop_loss attribute


class MockTradingAgent:
    """Mock trading agent for testing."""

    def __init__(self):
        self.call_count = 0

    async def analyze(self, ticker: str) -> MockDecision:
        """Return mock trading decision."""
        self.call_count += 1

        # Simple strategy: Buy on even days, Sell on odd days
        if self.call_count % 2 == 0:
            return MockDecision(
                action="BUY",
                position_size=2.0,  # 2% position
                conviction=0.75,
                reasoning="Mock buy signal"
            )
        else:
            return MockDecision(
                action="HOLD",
                position_size=0.0,
                conviction=0.5,
                reasoning="Mock hold"
            )


class MockFeatureStore:
    """Mock feature store."""
    pass


async def test_basic_backtest():
    """Test basic backtest execution."""
    
    print("\n" + "="*80)
    print("🧪 Backtest Engine - Test Suite")
    print("="*80 + "\n")
    
    # Initialize
    print("Initializing backtest engine...")
    engine = BacktestEngine(
        initial_capital=100000.0,
        slippage_bps=1.0,
        commission_rate=0.00015,
        max_positions=5,
    )
    
    agent = MockTradingAgent()
    feature_store = MockFeatureStore()
    
    # Run backtest
    print("Running backtest (1 month, 2 tickers)...")
    results = await engine.run(
        trading_agent=agent,
        tickers=["AAPL", "MSFT"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        feature_store=feature_store,
    )
    
    # Print summary
    print(engine.get_summary())
    
    # Verify results
    print("\n📊 Results Verification:")
    print(f"  Final Equity:  ${results['final_equity']:,.2f}")
    print(f"  Total Return:  {results['total_return']:.2%}")
    print(f"  Sharpe Ratio:  {results['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:  {results['max_drawdown']:.2%}")
    print(f"  Win Rate:      {results['win_rate']:.1%}")
    print(f"  Total Trades:  {results['total_trades']}")

    assert results['final_equity'] > 0, "Final equity must be positive"
    assert -1.0 <= results['total_return'] <= 10.0, "Return must be reasonable"
    assert 0.0 <= results['win_rate'] <= 1.0, "Win rate must be between 0 and 1"
    
    print("\n✅ All tests passed!")
    print("\n" + "="*80)
    print("Backtest Engine is ready to use!")
    print("="*80)
    
    return results


if __name__ == "__main__":
    try:
        asyncio.run(test_basic_backtest())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)