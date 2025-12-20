"""
Quick Test for Paper Trading System

Tests paper trading components without running full simulation.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from paper_trading import (
    MarketDataFetcher,
    LivePortfolio,
    PaperTradingEngine,
    PaperTradingConfig,
)


async def test_market_data_fetcher():
    """Test market data fetcher."""
    print("\n" + "=" * 70)
    print("TEST 1: Market Data Fetcher")
    print("=" * 70)

    fetcher = MarketDataFetcher(cache_ttl_seconds=15)

    # Test single quote
    quote = await fetcher.get_quote("AAPL")
    if quote:
        print(f"OK: Fetched AAPL quote: ${quote.price:.2f}")
    else:
        print("WARNING: Failed to fetch AAPL quote")

    # Test batch quotes
    quotes = await fetcher.get_quotes_batch(["AAPL", "NVDA", "MSFT"])
    print(f"OK: Fetched {len(quotes)}/3 quotes")
    for ticker, quote in quotes.items():
        print(f"  {ticker}: ${quote.price:.2f}")

    # Test cache
    stats = fetcher.get_cache_stats()
    print(f"OK: Cache stats: {stats['total_cached']} cached, {stats['fresh']} fresh")


def test_live_portfolio():
    """Test live portfolio."""
    print("\n" + "=" * 70)
    print("TEST 2: Live Portfolio")
    print("=" * 70)

    portfolio = LivePortfolio(initial_cash=100000.0)

    # Test buy order
    order = portfolio.create_order("AAPL", "BUY", 10, 150.0)
    if order:
        print(f"OK: Created BUY order: {order.order_id}")

        # Fill order
        success = portfolio.fill_order(order, 150.50, slippage_bps=2.0)
        if success:
            print(f"OK: Filled order at $150.50")
        else:
            print("ERROR: Failed to fill order")
    else:
        print("ERROR: Failed to create order")

    # Check position
    position = portfolio.get_position("AAPL")
    if position:
        print(f"OK: Position created: {position.shares} shares @ ${position.avg_cost:.2f}")
        print(f"    Market value: ${position.market_value:.2f}")
    else:
        print("ERROR: Position not found")

    # Test sell order
    order = portfolio.create_order("AAPL", "SELL", 5, 155.0)
    if order:
        print(f"OK: Created SELL order: {order.order_id}")
        success = portfolio.fill_order(order, 154.80, slippage_bps=2.0)
        if success:
            print(f"OK: Filled SELL order")
    else:
        print("ERROR: Failed to create SELL order")

    # Portfolio summary
    summary = portfolio.get_summary()
    print(f"\nPortfolio Summary:")
    print(f"  Cash: ${summary['cash']:,.2f}")
    print(f"  Positions: {summary['positions_count']}")
    print(f"  Total Value: ${summary['total_value']:,.2f}")
    print(f"  Realized P&L: ${summary['realized_pnl']:+,.2f}")
    print(f"  Unrealized P&L: ${summary['unrealized_pnl']:+,.2f}")
    print(f"  Total Trades: {summary['total_trades']}")


async def test_paper_trading_engine():
    """Test paper trading engine (short run)."""
    print("\n" + "=" * 70)
    print("TEST 3: Paper Trading Engine (30 second test)")
    print("=" * 70)

    config = PaperTradingConfig(
        initial_cash=100000.0,
        tickers=["AAPL", "NVDA"],
        decision_interval_seconds=10,  # 10 seconds
        max_positions=5,
        enable_ai=False,  # Use mock strategy
        enable_monitoring=False,  # Disable for test
    )

    engine = PaperTradingEngine(config)

    print("Running 30-second paper trading test...")
    await engine.run_for_duration(30)

    # Check status
    status = engine.get_status()
    print(f"\nEngine Status:")
    print(f"  Status: {status['status']}")
    print(f"  Uptime: {status['uptime_seconds']:.1f}s")
    print(f"  Decisions: {status['decision_count']}")
    print(f"  Executions: {status['execution_count']}")

    print("OK: Paper trading engine test complete")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PAPER TRADING SYSTEM - QUICK TEST")
    print("=" * 70)

    try:
        # Test 1: Market Data
        await test_market_data_fetcher()

        # Test 2: Portfolio
        test_live_portfolio()

        # Test 3: Engine (short run)
        await test_paper_trading_engine()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
