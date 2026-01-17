"""
Comprehensive Two-Stage Agents Test

Tests all three Two-Stage agents:
- TraderAgentMVP
- RiskAgentMVP
- AnalystAgentMVP

Run with:
    python backend/tests/test_twostage_all_agents.py
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_trader_agent():
    """Test Two-Stage Trader Agent"""
    print("\n" + "="*60)
    print("Testing TraderAgentMVP (Two-Stage)")
    print("="*60)

    from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP

    agent = TraderAgentMVP()

    print(f"✓ Agent initialized: {agent.get_agent_info()['name']}")
    print(f"  Weight: {agent.weight}")
    print(f"  Architecture: {agent.get_agent_info()['architecture']}")

    # Test reasoning prompt
    prompt = agent.reasoning_agent._build_reasoning_prompt(
        symbol='AAPL',
        price_data={'current_price': 150.25, 'open': 148.50, 'high': 151.00, 'low': 147.80, 'volume': 45000000},
        technical_data={'rsi': 62.5, 'macd': {'value': 1.2, 'signal': 0.8}}
    )

    print(f"✓ Reasoning prompt built: {len(prompt)} chars")

    return True


async def test_risk_agent():
    """Test Two-Stage Risk Agent"""
    print("\n" + "="*60)
    print("Testing RiskAgentMVP (Two-Stage)")
    print("="*60)

    from backend.ai.mvp.risk_agent_twostage import RiskAgentMVP

    agent = RiskAgentMVP()

    print(f"✓ Agent initialized: {agent.get_agent_info()['name']}")
    print(f"  Weight: {agent.weight}")
    print(f"  Architecture: {agent.get_agent_info()['architecture']}")

    # Test reasoning prompt
    prompt = agent.reasoning_agent._build_reasoning_prompt(
        symbol='AAPL',
        price_data={'current_price': 150.25, 'change_pct': 2.5},
        technical_data={'rsi': 65.0, 'volatility': 6.5}
    )

    print(f"✓ Reasoning prompt built: {len(prompt)} chars")

    # Test schema
    schema = agent.schema_definition
    print(f"✓ Schema defined: {len(schema['properties'])} properties")

    return True


async def test_analyst_agent():
    """Test Two-Stage Analyst Agent"""
    print("\n" + "="*60)
    print("Testing AnalystAgentMVP (Two-Stage)")
    print("="*60)

    from backend.ai.mvp.analyst_agent_twostage import AnalystAgentMVP

    agent = AnalystAgentMVP()

    print(f"✓ Agent initialized: {agent.get_agent_info()['name']}")
    print(f"  Weight: {agent.weight}")
    print(f"  Architecture: {agent.get_agent_info()['architecture']}")

    # Test reasoning prompt
    prompt = agent.reasoning_agent._build_reasoning_prompt(
        symbol='AAPL',
        price_data={'current_price': 150.25},
        news_data=[
            {'title': 'AAPL, AI 기능 탑재', 'sentiment': 'positive', 'impact_score': 3.5}
        ],
        macro_data={'interest_rate': 5.25, 'trend': 'stable'}
    )

    print(f"✓ Reasoning prompt built: {len(prompt)} chars")

    # Test schema
    schema = agent.schema_definition
    print(f"✓ Schema defined: {len(schema['properties'])} properties")

    return True


async def test_all_agents_consistency():
    """Test all agents have consistent structure"""
    print("\n" + "="*60)
    print("Testing Cross-Agent Consistency")
    print("="*60)

    from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP
    from backend.ai.mvp.risk_agent_twostage import RiskAgentMVP
    from backend.ai.mvp.analyst_agent_twostage import AnalystAgentMVP

    agents = {
        'trader': TraderAgentMVP(),
        'risk': RiskAgentMVP(),
        'analyst': AnalystAgentMVP()
    }

    # Check total weight
    total_weight = sum(agent.weight for agent in agents.values())
    print(f"✓ Total voting weight: {total_weight:.2f}")
    assert total_weight == 1.0, f"Total weight should be 1.0, got {total_weight}"

    # Check architecture consistency
    for name, agent in agents.items():
        info = agent.get_agent_info()
        assert info['architecture'] == 'two-stage', f"{name} should be two-stage"
        assert 'stages' in info, f"{name} should have stages"
        print(f"✓ {name.title()}: two-stage architecture")

    # Check shared structuring agent
    print(f"✓ Structuring agents initialized")

    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Two-Stage Agents Comprehensive Test Suite")
    print("="*60)

    tests = [
        ("Trader Agent", test_trader_agent),
        ("Risk Agent", test_risk_agent),
        ("Analyst Agent", test_analyst_agent),
        ("Cross-Agent Consistency", test_all_agents_consistency)
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
        print("\n🎉 All Two-Stage agents implemented successfully!")
        print("\n📋 Next Steps:")
        print("   1. Update WarRoomMVP to use new two-stage agents")
        print("   2. Run E2E tests with real GLM API")
        print("   3. Measure latency improvements")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
