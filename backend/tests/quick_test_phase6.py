"""
Quick Phase 6 validation test
Tests Phase 6 Smart Execution Engine components
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("Phase 6: Smart Execution Engine - Quick Test")
print("=" * 60)

# Test 1: Import modules
print("\n[1/5] Testing imports...")
try:
    from execution.execution_engine import SmartExecutionEngine, ExecutionRequest, ExecutionResult
    from execution.smart_executor import SmartExecutor, SimplePortfolioManager, SimpleRiskManager
    print("PASS - All modules imported successfully")
except Exception as e:
    print(f"FAIL - Import error: {e}")
    sys.exit(1)

# Test 2: Execution Engine
print("\n[2/5] Testing Execution Engine...")
try:
    engine = SmartExecutionEngine()

    # Test order size calculation
    from dataclasses import dataclass

    @dataclass
    class MockDecision:
        ticker: str = "AAPL"
        action: str = "BUY"
        position_size: float = 5.0
        conviction: float = 0.8

    shares = engine._calculate_order_size(MockDecision(), 100000, 200.0)
    assert shares == 25, f"Expected 25 shares, got {shares}"

    # Test market impact
    impact = engine._estimate_market_impact(100, "MODERATE")
    assert impact > 0, "Market impact should be positive"

    print("PASS - Execution Engine working")
except Exception as e:
    print(f"FAIL - Execution Engine error: {e}")
    sys.exit(1)

# Test 3: Portfolio Manager
print("\n[3/5] Testing Portfolio Manager...")
try:
    pm = SimplePortfolioManager(initial_cash=100000.0)

    # Test BUY
    result = pm.update_position("NVDA", "BUY", 10, 875.50, 8757.31)
    assert result["action"] == "BUY"
    assert "NVDA" in pm.positions
    assert pm.cash < 100000

    # Test portfolio context
    context = pm.get_context()
    assert context["num_positions"] == 1
    assert context["total_value"] > 90000

    print("PASS - Portfolio Manager working")
except Exception as e:
    print(f"FAIL - Portfolio Manager error: {e}")
    sys.exit(1)

# Test 4: Risk Manager
print("\n[4/5] Testing Risk Manager...")
try:
    rm = SimpleRiskManager()

    portfolio_context = {"total_value": 100000, "num_positions": 5}

    # Test normal trade
    check = rm.check_trade("AAPL", "BUY", portfolio_context)
    assert check["approved"] is True

    # Test kill switch
    rm.activate_kill_switch("Test")
    check = rm.check_trade("AAPL", "BUY", portfolio_context)
    assert check["approved"] is False
    rm.deactivate_kill_switch()

    print("PASS - Risk Manager working")
except Exception as e:
    print(f"FAIL - Risk Manager error: {e}")
    sys.exit(1)

# Test 5: Full execution flow
print("\n[5/5] Testing full execution flow...")
async def test_execution():
    try:
        engine = SmartExecutionEngine()

        @dataclass
        class TestDecision:
            ticker: str = "NVDA"
            action: str = "BUY"
            position_size: float = 3.0
            conviction: float = 0.75

        result = await engine.execute_decision(
            trading_decision=TestDecision(),
            portfolio_value=100000.0,
            current_price=875.50,
            urgency="MEDIUM"
        )

        assert result.status == "SUCCESS"
        assert result.filled_shares > 0
        assert result.algorithm_used == "TWAP_STANDARD"
        assert result.slippage_bps >= 0

        print("PASS - Full execution flow working")
        return True
    except Exception as e:
        print(f"FAIL - Execution flow error: {e}")
        return False

if not asyncio.run(test_execution()):
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("Phase 6 Quick Test: ALL TESTS PASSED")
print("=" * 60)
print("\nComponents validated:")
print("  - SmartExecutionEngine")
print("  - SmartExecutor")
print("  - SimplePortfolioManager")
print("  - SimpleRiskManager")
print("\nPhase 6 is ready for integration!")
