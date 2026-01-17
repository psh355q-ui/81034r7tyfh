"""
Test GLM Integration for MVP Agents

This test validates:
1. GLM Client basic connectivity
2. TraderAgentMVP analysis
3. RiskAgentMVP analysis
4. AnalystAgentMVP analysis
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from backend.ai.glm_client import GLMClient
from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP
from backend.ai.mvp.risk_agent_mvp import RiskAgentMVP
from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP


async def test_glm_client():
    """Test basic GLM client connectivity"""
    print("\n" + "=" * 60)
    print("TEST 1: GLM Client Basic Connectivity")
    print("=" * 60)

    client = GLMClient()
    print(f"✓ GLM Client initialized (model: {client.model})")

    # Test basic chat
    response = await client.chat(
        messages=[{"role": "user", "content": "Reply with 'OK' if you receive this."}],
        max_tokens=50,
        temperature=0.1
    )

    message = response["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning_content", "")
    print(f"✓ Response: {content[:100]}")
    print(f"✓ Finish reason: {response['choices'][0].get('finish_reason')}")

    await client.close()
    return True


async def test_trader_agent():
    """Test TraderAgentMVP"""
    print("\n" + "=" * 60)
    print("TEST 2: TraderAgentMVP")
    print("=" * 60)

    agent = TraderAgentMVP()
    print(f"✓ Trader Agent initialized (weight: {agent.weight})")

    # Test data
    price_data = {
        'current_price': 150.25,
        'open': 148.50,
        'high': 151.00,
        'low': 147.80,
        'volume': 45000000
    }

    technical_data = {
        'rsi': 62.5,
        'macd': {'value': 1.2, 'signal': 0.8},
        'moving_averages': {'ma50': 145.00, 'ma200': 140.00}
    }

    result = await agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        technical_data=technical_data
    )

    print(f"✓ Action: {result['action']}")
    print(f"✓ Confidence: {result['confidence']:.2f}")
    print(f"✓ Reasoning: {result['reasoning'][:100]}...")
    print(f"✓ Opportunity Score: {result.get('opportunity_score', 'N/A')}")

    if 'error' in result:
        print(f"⚠ Error: {result['error']}")
        return False
    return True


async def test_risk_agent():
    """Test RiskAgentMVP"""
    print("\n" + "=" * 60)
    print("TEST 3: RiskAgentMVP")
    print("=" * 60)

    agent = RiskAgentMVP()
    print(f"✓ Risk Agent initialized (weight: {agent.weight})")

    # Test data
    price_data = {
        'current_price': 150.25,
        'high_52w': 180.00,
        'low_52w': 120.00,
        'volatility': 0.25
    }

    trader_opinion = {
        'action': 'buy',
        'confidence': 0.75,
        'opportunity_score': 7.5
    }

    portfolio_context = {
        'current_cash': 50000,
        'total_value': 100000,
        'current_positions': 3
    }

    result = await agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        trader_opinion=trader_opinion,
        portfolio_state=portfolio_context
    )

    print(f"✓ Risk Level: {result['risk_level']}")
    print(f"✓ Recommendation: {result.get('recommendation', 'N/A')}")
    print(f"✓ Position Size: {result.get('position_size_pct', 0) * 100:.2f}%")
    print(f"✓ Reasoning: {result['reasoning'][:100]}...")

    if 'error' in result:
        print(f"⚠ Error: {result['error']}")
        return False
    return True


async def test_analyst_agent():
    """Test AnalystAgentMVP"""
    print("\n" + "=" * 60)
    print("TEST 4: AnalystAgentMVP")
    print("=" * 60)

    agent = AnalystAgentMVP()
    print(f"✓ Analyst Agent initialized (weight: {agent.weight})")

    # Test data
    news_articles = [
        {
            'title': 'Apple announces new AI chip',
            'source': 'Reuters',
            'published': '2025-12-30',
            'summary': 'New chip targets enterprise AI market with improved performance'
        }
    ]

    macro_indicators = {
        'interest_rate': 5.25,
        'inflation_rate': 3.1,
        'fed_policy': 'hawkish'
    }

    result = await agent.analyze(
        symbol='AAPL',
        news_articles=news_articles,
        macro_indicators=macro_indicators
    )

    print(f"✓ Action: {result['action']}")
    print(f"✓ Confidence: {result['confidence']:.2f}")
    print(f"✓ Overall Score: {result.get('overall_score', 0):.1f}")
    print(f"✓ Reasoning: {result['reasoning'][:100]}...")

    if 'error' in result:
        print(f"⚠ Error: {result['error']}")
        return False
    return True


async def main():
    """Run all tests"""
    print("\n🚀 GLM Integration Test Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # Test 1: Basic connectivity
        results['glm_client'] = await test_glm_client()
    except Exception as e:
        print(f"✗ GLM Client test failed: {e}")
        results['glm_client'] = False

    # Skip agent tests if basic connectivity failed
    if not results.get('glm_client'):
        print("\n⚠ Skipping agent tests due to connectivity failure")
        return

    try:
        # Test 2: Trader Agent
        results['trader'] = await test_trader_agent()
    except Exception as e:
        print(f"✗ Trader Agent test failed: {e}")
        results['trader'] = False

    try:
        # Test 3: Risk Agent
        results['risk'] = await test_risk_agent()
    except Exception as e:
        print(f"✗ Risk Agent test failed: {e}")
        results['risk'] = False

    try:
        # Test 4: Analyst Agent
        results['analyst'] = await test_analyst_agent()
    except Exception as e:
        print(f"✗ Analyst Agent test failed: {e}")
        results['analyst'] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! GLM integration is working correctly.")
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
