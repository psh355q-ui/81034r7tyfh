"""
WarRoomMVP Integration Test (Post-Migration)

Tests the WarRoomMVP after migration to Two-Stage architecture.

After migration:
- trader_agent_mvp.py now contains Two-Stage implementation
- risk_agent_mvp.py now contains Two-Stage implementation
- analyst_agent_mvp.py now contains Two-Stage implementation
- war_room_mvp.py now contains Two-Stage implementation

Run with:
    python backend/tests/test_warroom_twostage_final.py
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_imports():
    """Test that imports work from original file names"""
    print("\n" + "="*60)
    print("Testing Imports (Original File Names)")
    print("="*60)

    # Should import Two-Stage implementations
    from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP
    from backend.ai.mvp.risk_agent_mvp import RiskAgentMVP
    from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP
    from backend.ai.mvp.war_room_mvp import WarRoomMVP

    print("✓ All imports successful")

    # Verify these are Two-Stage implementations
    trader = TraderAgentMVP()
    risk = RiskAgentMVP()
    analyst = AnalystAgentMVP()

    trader_info = trader.get_agent_info()
    risk_info = risk.get_agent_info()
    analyst_info = analyst.get_agent_info()

    print(f"✓ Trader: {trader_info.get('name', 'Unknown')}")
    print(f"  Architecture: {trader_info.get('architecture', 'unknown')}")
    print(f"✓ Risk: {risk_info.get('name', 'Unknown')}")
    print(f"  Architecture: {risk_info.get('architecture', 'unknown')}")
    print(f"✓ Analyst: {analyst_info.get('name', 'Unknown')}")
    print(f"  Architecture: {analyst_info.get('architecture', 'unknown')}")

    # Verify Two-Stage architecture
    assert trader_info.get('architecture') == 'two-stage', "Trader should be two-stage"
    assert risk_info.get('architecture') == 'two-stage', "Risk should be two-stage"
    assert analyst_info.get('architecture') == 'two-stage', "Analyst should be two-stage"

    print("✓ All agents are Two-Stage architecture")

    return True


async def test_warroom_initialization():
    """Test WarRoomMVP initialization"""
    print("\n" + "="*60)
    print("Testing WarRoomMVP Initialization")
    print("="*60)

    from backend.ai.mvp.war_room_mvp import WarRoomMVP

    war_room = WarRoomMVP()

    print(f"✓ WarRoomMVP initialized")

    info = war_room.get_war_room_info()
    print(f"  Version: {info['version']}")
    print(f"  Architecture: {info['architecture']}")

    # Verify Two-Stage
    assert info['architecture'] == 'two-stage', "WarRoom should be two-stage"

    return True


async def test_warroom_deliberation():
    """Test WarRoomMVP deliberation (with mocked API calls)"""
    print("\n" + "="*60)
    print("Testing WarRoomMVP Deliberation (Mocked)")
    print("="*60)

    from backend.ai.mvp.war_room_mvp import WarRoomMVP
    from unittest.mock import AsyncMock, patch

    war_room = WarRoomMVP()

    # Mock the agent analyze methods
    mock_trader_result = {
        'agent': 'trader_mvp',
        'action': 'buy',
        'confidence': 0.75,
        'reasoning': 'Strong momentum with RSI 65',
        'opportunity_score': 72.0,
        'momentum_strength': 'strong',
        'risk_reward_ratio': 2.5,
        'weight': 0.35,
        'timestamp': '2026-01-17T00:00:00',
        'symbol': 'AAPL',
        'stage': 'structured',
        'latency_seconds': 2.5
    }

    mock_risk_result = {
        'agent': 'risk_mvp',
        'risk_level': 'medium',
        'confidence': 0.70,
        'reasoning': 'Moderate risk with clear stop loss',
        'stop_loss_pct': 0.03,
        'take_profit_pct': 0.10,
        'max_position_pct': 0.10,
        'recommendation': 'approve',
        'weight': 0.30,
        'timestamp': '2026-01-17T00:00:00',
        'symbol': 'AAPL',
        'stage': 'structured',
        'latency_seconds': 2.0
    }

    mock_analyst_result = {
        'agent': 'analyst_mvp',
        'action': 'buy',
        'confidence': 0.80,
        'reasoning': 'Positive news and macro environment',
        'news_headline': 'AAPL announces AI features',
        'news_sentiment': 'positive',
        'overall_information_score': 7.5,
        'weight': 0.35,
        'timestamp': '2026-01-17T00:00:00',
        'symbol': 'AAPL',
        'stage': 'structured',
        'latency_seconds': 2.2
    }

    # Apply mocks
    with patch.object(war_room.trader_agent, 'analyze', new=AsyncMock(return_value=mock_trader_result)):
        with patch.object(war_room.risk_agent, 'analyze', new=AsyncMock(return_value=mock_risk_result)):
            with patch.object(war_room.analyst_agent, 'analyze', new=AsyncMock(return_value=mock_analyst_result)):
                # Test data
                market_data = {
                    'price_data': {'current_price': 150.25},
                    'technical_data': {'rsi': 62.5},
                    'market_conditions': {'vix': 18.5}
                }

                portfolio_state = {'total_value': 100000, 'available_cash': 50000}

                result = await war_room.deliberate(
                    symbol='AAPL',
                    action_context='new_position',
                    market_data=market_data,
                    portfolio_state=portfolio_state
                )

                print(f"✓ Deliberation completed")
                print(f"  Final Decision: {result['final_decision']}")
                print(f"  Architecture: {result['architecture']}")

                assert result['architecture'] == 'two-stage', "Result should show two-stage architecture"

                return True


async def test_file_structure():
    """Test file structure after migration"""
    print("\n" + "="*60)
    print("Testing File Structure")
    print("="*60)

    from pathlib import Path

    mvp_dir = Path("backend/ai/mvp")
    deprecated_dir = mvp_dir / "deprecated"

    # Check deprecated folder exists and has legacy files
    assert deprecated_dir.exists(), "deprecated folder should exist"

    deprecated_files = list(deprecated_dir.glob('*.py'))
    print(f"✓ deprecated/ has {len(deprecated_files)} files")

    expected_legacy = ['trader_agent_mvp.py', 'risk_agent_mvp.py', 'analyst_agent_mvp.py', 'war_room_mvp.py']
    for expected in expected_legacy:
        assert (deprecated_dir / expected).exists(), f"deprecated/{expected} should exist"
        print(f"  ✓ {expected}")

    # Check twostage files still exist (we keep them for now)
    twostage_files = list(mvp_dir.glob('*_twostage.py'))
    print(f"\n✓ Twostage files still exist: {len(twostage_files)} files")
    for f in twostage_files:
        print(f"  - {f.name}")

    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("WarRoomMVP Post-Migration Test Suite")
    print("="*60)

    tests = [
        ("Import Tests", test_imports),
        ("File Structure", test_file_structure),
        ("WarRoom Initialization", test_warroom_initialization),
        ("WarRoom Deliberation", test_warroom_deliberation)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
            print(f"\n✅ {name}: PASSED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n🎉 Migration successful! Two-Stage architecture is live!")
        print("\n📋 Next Steps:")
        print("   1. Remove twostage files: python scripts/cleanup_twostage_files.py")
        print("   2. Run E2E tests with real GLM API")
        print("   3. Measure latency improvements")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
