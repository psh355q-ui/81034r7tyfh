"""
Phase 6: Smart Execution - Complete Test Suite

Tests:
1. Execution Engine functionality
2. Smart Executor workflow
3. Portfolio Management
4. Risk Controls
5. Algorithm performance

Run: python test_phase6.py
"""

import asyncio
import sys
from datetime import datetime


def test_execution_engine():
    """Test Smart Execution Engine."""
    print("\n" + "=" * 60)
    print("TEST 1: Smart Execution Engine")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine
    
    # Initialize
    engine = SmartExecutionEngine()
    print("✅ Engine initialized")
    
    # Test market impact estimation
    impact_100 = engine._estimate_market_impact(100, "MODERATE")
    impact_1000 = engine._estimate_market_impact(1000, "AGGRESSIVE")
    
    print(f"✅ Market impact (100 shares, MODERATE): {impact_100:.2f} bps")
    print(f"✅ Market impact (1000 shares, AGGRESSIVE): {impact_1000:.2f} bps")
    
    assert impact_100 < impact_1000, "More shares should have higher impact"
    print("✅ Impact model validated")
    
    # Test order size calculation
    class MockDecision:
        ticker = "AAPL"
        action = "BUY"
        position_size = 5.0  # 5%
    
    shares = engine._calculate_order_size(MockDecision(), 100000, 200.0)
    expected = int(100000 * 0.05 / 200.0)  # 25 shares
    
    print(f"✅ Order size calculation: {shares} shares (expected ~{expected})")
    assert shares == expected, f"Expected {expected}, got {shares}"
    
    print("\n✅ Execution Engine tests passed!")
    return True


async def test_twap_simulation():
    """Test TWAP execution simulation."""
    print("\n" + "=" * 60)
    print("TEST 2: TWAP Simulation")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine, ExecutionRequest
    
    engine = SmartExecutionEngine()
    
    request = ExecutionRequest(
        ticker="NVDA",
        action="BUY",
        shares=100,
        urgency="MEDIUM",
    )
    
    result = await engine._simulate_twap(request, 875.50, duration=30, slices=10)
    
    print(f"✅ TWAP executed: {result['status']}")
    print(f"  Filled shares: {result['filled_shares']}")
    print(f"  Avg price: ${result['avg_price']:.2f}")
    print(f"  Slippage: {result['slippage_bps']:.2f} bps")
    print(f"  Child orders: {len(result['child_orders'])}")
    
    assert result["status"] == "SUCCESS"
    assert result["filled_shares"] == 100
    assert len(result["child_orders"]) == 10
    assert result["slippage_bps"] < 10  # Should be reasonable
    
    print("\n✅ TWAP simulation tests passed!")
    return True


async def test_vwap_simulation():
    """Test VWAP execution simulation."""
    print("\n" + "=" * 60)
    print("TEST 3: VWAP Simulation")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine, ExecutionRequest
    
    engine = SmartExecutionEngine()
    
    request = ExecutionRequest(
        ticker="AAPL",
        action="SELL",
        shares=200,
        urgency="LOW",
    )
    
    result = await engine._simulate_vwap(request, 185.25)
    
    print(f"✅ VWAP executed: {result['status']}")
    print(f"  Filled shares: {result['filled_shares']}")
    print(f"  Avg price: ${result['avg_price']:.2f}")
    print(f"  Slippage: {result['slippage_bps']:.2f} bps")
    print(f"  Child orders: {len(result['child_orders'])}")
    
    assert result["status"] == "SUCCESS"
    assert result["filled_shares"] == 200
    assert len(result["child_orders"]) == 10  # 10 volume buckets
    assert result["slippage_bps"] < 5  # VWAP should be lower impact
    
    print("\n✅ VWAP simulation tests passed!")
    return True


async def test_algorithm_selection():
    """Test algorithm selection based on urgency."""
    print("\n" + "=" * 60)
    print("TEST 4: Algorithm Selection")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine, ExecutionRequest
    
    engine = SmartExecutionEngine()
    
    test_cases = [
        ("CRITICAL", "MARKET"),
        ("HIGH", "TWAP_AGGRESSIVE"),
        ("MEDIUM", "TWAP_STANDARD"),
        ("LOW", "VWAP"),
    ]
    
    for urgency, expected_algo in test_cases:
        request = ExecutionRequest(
            ticker="TEST",
            action="BUY",
            shares=50,
            urgency=urgency,
        )
        
        result = await engine._execute_with_algorithm(request, 100.0)
        
        print(f"✅ {urgency} urgency → {result.algorithm_used}")
        assert result.algorithm_used == expected_algo, \
            f"Expected {expected_algo}, got {result.algorithm_used}"
    
    print("\n✅ Algorithm selection tests passed!")
    return True


def test_portfolio_manager():
    """Test portfolio management."""
    print("\n" + "=" * 60)
    print("TEST 5: Portfolio Manager")
    print("=" * 60)
    
    from smart_executor import SimplePortfolioManager
    
    # Initialize with $100k
    pm = SimplePortfolioManager(initial_cash=100000.0)
    print(f"✅ Portfolio initialized: ${pm.cash:,.0f}")
    
    # Test BUY
    result = pm.update_position(
        ticker="NVDA",
        action="BUY",
        shares=10,
        price=875.50,
        cost=8757.31,  # includes commission
    )
    
    print(f"✅ BUY executed: {result['action']}")
    print(f"  Cash remaining: ${pm.cash:,.2f}")
    assert "NVDA" in pm.positions
    assert pm.cash < 100000
    
    # Test portfolio context
    context = pm.get_context()
    print(f"✅ Portfolio context:")
    print(f"  Total value: ${context['total_value']:,.2f}")
    print(f"  Num positions: {context['num_positions']}")
    
    assert context["num_positions"] == 1
    assert context["total_value"] > 90000
    
    # Test SELL
    result = pm.update_position(
        ticker="NVDA",
        action="SELL",
        shares=10,
        price=880.00,
        cost=0,  # proceeds
    )
    
    print(f"✅ SELL executed: {result['action']}")
    print(f"  P&L: ${result['pnl']:,.2f}")
    print(f"  Cash: ${pm.cash:,.2f}")
    
    assert "NVDA" not in pm.positions
    
    # Test summary
    summary = pm.get_summary()
    print(f"✅ Portfolio summary:")
    print(f"  Total P&L: ${summary['total_pnl']:,.2f}")
    print(f"  Return: {summary['return_pct']:.2f}%")
    
    print("\n✅ Portfolio Manager tests passed!")
    return True


def test_risk_manager():
    """Test risk management controls."""
    print("\n" + "=" * 60)
    print("TEST 6: Risk Manager")
    print("=" * 60)
    
    from smart_executor import SimpleRiskManager
    
    rm = SimpleRiskManager()
    print("✅ Risk Manager initialized")
    
    portfolio_context = {
        "total_value": 100000,
        "num_positions": 5,
    }
    
    # Test normal trade
    check = rm.check_trade("AAPL", "BUY", portfolio_context)
    print(f"✅ Normal trade check: {check['approved']}")
    assert check["approved"] is True
    
    # Test kill switch
    rm.activate_kill_switch("Test activation")
    check = rm.check_trade("AAPL", "BUY", portfolio_context)
    print(f"✅ Trade with kill switch: {check['approved']}")
    assert check["approved"] is False
    
    rm.deactivate_kill_switch()
    
    # Test max positions
    portfolio_context["num_positions"] = 20  # At limit
    check = rm.check_trade("AAPL", "BUY", portfolio_context)
    print(f"✅ Trade at max positions: {check['approved']}")
    assert check["approved"] is False
    
    # SELL should be allowed
    check = rm.check_trade("AAPL", "SELL", portfolio_context)
    print(f"✅ SELL at max positions: {check['approved']}")
    assert check["approved"] is True
    
    print("\n✅ Risk Manager tests passed!")
    return True


async def test_smart_executor():
    """Test complete Smart Executor workflow."""
    print("\n" + "=" * 60)
    print("TEST 7: Smart Executor Workflow")
    print("=" * 60)
    
    from smart_executor import SmartExecutor
    from execution_engine import SmartExecutionEngine
    
    # Initialize
    engine = SmartExecutionEngine()
    executor = SmartExecutor(execution_engine=engine)
    
    print("✅ Smart Executor initialized")
    
    # Process single ticker
    result = await executor.process_ticker("NVDA", urgency="MEDIUM")
    
    print(f"✅ Ticker processed: {result['ticker']}")
    print(f"  Status: {result['status']}")
    print(f"  Decision: {result.get('decision', {}).get('action', 'N/A')}")
    
    # Check summary
    summary = executor.get_summary()
    print(f"✅ Execution summary:")
    print(f"  Total trades: {summary['metrics']['total_trades']}")
    print(f"  Portfolio value: ${summary['portfolio']['total_value']:,.2f}")
    
    print("\n✅ Smart Executor tests passed!")
    return True


async def test_batch_processing():
    """Test batch processing of multiple tickers."""
    print("\n" + "=" * 60)
    print("TEST 8: Batch Processing")
    print("=" * 60)
    
    from smart_executor import SmartExecutor
    from execution_engine import SmartExecutionEngine
    
    engine = SmartExecutionEngine()
    executor = SmartExecutor(execution_engine=engine)
    
    tickers = ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"]
    
    print(f"✅ Processing {len(tickers)} tickers...")
    
    results = await executor.process_batch(
        tickers=tickers,
        urgency="MEDIUM",
        max_concurrent=3,
    )
    
    print(f"✅ Batch complete: {len(results)} results")
    
    for result in results:
        status = result["status"]
        print(f"  {result['ticker']}: {status}")
    
    # Verify all processed
    assert len(results) == len(tickers)
    
    print("\n✅ Batch processing tests passed!")
    return True


async def test_execution_metrics():
    """Test execution metrics tracking."""
    print("\n" + "=" * 60)
    print("TEST 9: Execution Metrics")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine
    
    engine = SmartExecutionEngine()
    
    # Create multiple executions
    class MockDecision:
        def __init__(self, ticker, action):
            self.ticker = ticker
            self.action = action
            self.position_size = 3.0
    
    decisions = [
        MockDecision("NVDA", "BUY"),
        MockDecision("AAPL", "BUY"),
        MockDecision("MSFT", "SELL"),
    ]
    
    for decision in decisions:
        await engine.execute_decision(
            trading_decision=decision,
            portfolio_value=100000,
            current_price=100.0,
            urgency="MEDIUM",
        )
    
    summary = engine.get_execution_summary()
    
    print(f"✅ Metrics tracked:")
    print(f"  Total executions: {summary['metrics']['total_executions']}")
    print(f"  Successful: {summary['metrics']['successful_executions']}")
    print(f"  Avg slippage: {summary['metrics']['avg_slippage_bps']:.2f} bps")
    print(f"  Total volume: {summary['metrics']['total_volume_traded']} shares")
    
    assert summary["metrics"]["total_executions"] == 3
    assert summary["metrics"]["successful_executions"] == 3
    assert summary["metrics"]["avg_slippage_bps"] > 0
    
    # Algorithm stats
    print(f"✅ Algorithm performance:")
    for algo, stats in summary["algorithm_performance"].items():
        print(f"  {algo}: {stats['count']} executions, {stats['avg_slippage_bps']:.2f} bps avg")
    
    print("\n✅ Execution metrics tests passed!")
    return True


async def test_hold_decision():
    """Test HOLD decision handling."""
    print("\n" + "=" * 60)
    print("TEST 10: HOLD Decision Handling")
    print("=" * 60)
    
    from execution_engine import SmartExecutionEngine
    
    engine = SmartExecutionEngine()
    
    class HoldDecision:
        ticker = "GOOGL"
        action = "HOLD"
        conviction = 0.5
        position_size = 0.0
    
    result = await engine.execute_decision(
        trading_decision=HoldDecision(),
        portfolio_value=100000,
        current_price=175.00,
        urgency="MEDIUM",
    )
    
    print(f"✅ HOLD decision result:")
    print(f"  Status: {result.status}")
    print(f"  Algorithm: {result.algorithm_used}")
    print(f"  Filled shares: {result.filled_shares}")
    
    assert result.status == "NO_ACTION"
    assert result.algorithm_used == "NONE"
    assert result.filled_shares == 0
    
    print("\n✅ HOLD decision tests passed!")
    return True


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 60)
    print("PHASE 6: SMART EXECUTION - COMPLETE TEST SUITE")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Execution Engine", test_execution_engine),
        ("TWAP Simulation", test_twap_simulation),
        ("VWAP Simulation", test_vwap_simulation),
        ("Algorithm Selection", test_algorithm_selection),
        ("Portfolio Manager", test_portfolio_manager),
        ("Risk Manager", test_risk_manager),
        ("Smart Executor", test_smart_executor),
        ("Batch Processing", test_batch_processing),
        ("Execution Metrics", test_execution_metrics),
        ("HOLD Decision", test_hold_decision),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for name, test_func in tests:
        try:
            # Run async or sync test
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                errors.append(f"{name}: Test returned False")
        except Exception as e:
            failed += 1
            errors.append(f"{name}: {str(e)}")
            print(f"\n❌ {name} FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {(passed/len(tests))*100:.1f}%")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 6 is ready for production.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review and fix.")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()