"""
Two-Stage WarRoomMVP Integration Test

Tests the complete Two-Stage WarRoomMVP system.

Run with:
    python backend/tests/test_warroom_twostage.py
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_warroom_initialization():
    """Test WarRoomMVP initialization"""
    print("\n" + "="*60)
    print("Testing WarRoomMVP Initialization")
    print("="*60)

    from backend.ai.mvp.war_room_mvp_twostage import WarRoomMVP

    war_room = WarRoomMVP()

    print(f"✓ WarRoomMVP initialized")

    info = war_room.get_war_room_info()
    print(f"  Version: {info['version']}")
    print(f"  Architecture: {info['architecture']}")

    for agent in info['agents']:
        if 'implementation' in agent:
            print(f"  - {agent['name']}: {agent['implementation']} ({agent['weight']})")

    return True


async def test_warroom_deliberation():
    """Test WarRoomMVP deliberation (with mocked API calls)"""
    print("\n" + "="*60)
    print("Testing WarRoomMVP Deliberation (Mocked)")
    print("="*60)

    from backend.ai.mvp.war_room_mvp_twostage import WarRoomMVP
    from unittest.mock import AsyncMock, patch, MagicMock

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
                print(f"  Trader: {result['agent_opinions']['trader']['action']} ({result['agent_opinions']['trader']['latency_seconds']}s)")
                print(f"  Risk: {result['agent_opinions']['risk']['recommendation']} ({result['agent_opinions']['risk']['latency_seconds']}s)")
                print(f"  Analyst: {result['agent_opinions']['analyst']['action']} ({result['agent_opinions']['analyst']['latency_seconds']}s)")

                return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Two-Stage WarRoomMVP Test Suite")
    print("="*60)

    tests = [
        ("Initialization", test_warroom_initialization),
        ("Deliberation (Mocked)", test_warroom_deliberation)
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
        print("\n🎉 Two-Stage WarRoomMVP is ready!")
        print("\n📋 Next Steps:")
        print("   1. Deprecate legacy MVP agents")
        print("   2. Run E2E tests with real GLM API")
        print("   3. Measure latency improvements")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
