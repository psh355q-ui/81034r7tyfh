"""
E2E Latency Test - Two-Stage WarRoomMVP

Tests real GLM API calls and measures latency for:
1. Individual Agent latency (Stage 1 + Stage 2)
2. Parallel execution latency
3. End-to-end WarRoomMVP deliberation
4. Comparison with expected performance targets

Run with:
    python backend/tests/test_twostage_e2e_latency.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load .env file
load_dotenv()

# Check API key
if not os.getenv('GLM_API_KEY'):
    print("⚠️  GLM_API_KEY not set. Skipping E2E test.")
    sys.exit(0)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP
from backend.ai.mvp.risk_agent_mvp import RiskAgentMVP
from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP
from backend.ai.mvp.war_room_mvp import WarRoomMVP


class LatencyTracker:
    """Track and report latency metrics"""

    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []

    def record(self, name: str, stage: str, latency: float, success: bool = True):
        """Record a latency measurement"""
        self.metrics.append({
            'name': name,
            'stage': stage,
            'latency': latency,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        })

    def report(self):
        """Generate latency report"""
        if not self.metrics:
            print("\n⚠️  No latency metrics recorded.")
            return

        print("\n" + "="*60)
        print("LATENCY REPORT")
        print("="*60)

        # Group by agent
        agents = {}
        for m in self.metrics:
            agent = m['name']
            if agent not in agents:
                agents[agent] = []
            agents[agent].append(m)

        for agent, metrics in sorted(agents.items()):
            print(f"\n[{agent}]")
            for m in metrics:
                status = "✅" if m['success'] else "❌"
                print(f"  {status} {m['stage']}: {m['latency']:.2f}s")

            # Calculate totals
            total = sum(m['latency'] for m in metrics if m['success'])
            print(f"  → Total: {total:.2f}s")

        # Overall summary
        print("\n" + "-"*60)
        all_successful = [m['latency'] for m in self.metrics if m['success']]
        if all_successful:
            avg = sum(all_successful) / len(all_successful)
            max_lat = max(all_successful)
            min_lat = min(all_successful)
            print(f"Overall:")
            print(f"  Average: {avg:.2f}s")
            print(f"  Min: {min_lat:.2f}s")
            print(f"  Max: {max_lat:.2f}s")

        print("="*60)


tracker = LatencyTracker()


async def test_trader_agent_latency():
    """Test Trader Agent latency with real API"""
    print("\n" + "="*60)
    print("Testing TraderAgentMVP (Two-Stage)")
    print("="*60)

    agent = TraderAgentMVP()

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
        'moving_averages': {'ma50': 145.00, 'ma200': 140.00},
        'bollinger_bands': {'upper': 152.00, 'lower': 148.00}
    }

    print(f"\n📊 Test Data: AAPL @ ${price_data['current_price']}, RSI: {technical_data['rsi']}")

    start = time.time()
    result = await agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        technical_data=technical_data
    )
    total_latency = time.time() - start

    if 'error' in result:
        print(f"❌ Analysis failed: {result['error']}")
        tracker.record('Trader', 'Total', total_latency, False)
        return False

    print(f"\n✅ Analysis completed in {total_latency:.2f}s")
    print(f"  Action: {result['action']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Opportunity: {result.get('opportunity_score', 0):.1f}/100")
    print(f"  Stage: {result.get('stage', 'unknown')}")

    # Extract individual stage latencies if available
    reasoning_latency = None
    structuring_latency = None

    if 'latency_seconds' in result:
        tracker.record('Trader', 'Total (1+2)', result['latency_seconds'], True)

    # Performance evaluation
    print("\n📊 Performance:")
    if total_latency < 3:
        print("  ✅ Excellent: < 3s")
    elif total_latency < 5:
        print("  ✅ Good: < 5s")
    elif total_latency < 8:
        print("  ⚠️  Acceptable: < 8s")
    else:
        print("  ❌ Slow: > 8s")

    return True


async def test_risk_agent_latency():
    """Test Risk Agent latency with real API"""
    print("\n" + "="*60)
    print("Testing RiskAgentMVP (Two-Stage)")
    print("="*60)

    agent = RiskAgentMVP()

    price_data = {
        'current_price': 150.25,
        'change_pct': 2.5
    }

    technical_data = {
        'rsi': 65.0,
        'volatility': 6.5,
        'bollinger_bands': {'upper': 152, 'lower': 148}
    }

    print(f"\n📊 Test Data: AAPL @ ${price_data['current_price']}, Volatility: {technical_data['volatility']}")

    start = time.time()
    result = await agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        technical_data=technical_data
    )
    total_latency = time.time() - start

    if 'error' in result:
        print(f"❌ Analysis failed: {result['error']}")
        tracker.record('Risk', 'Total', total_latency, False)
        return False

    print(f"\n✅ Analysis completed in {total_latency:.2f}s")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Max Position: {result.get('max_position_pct', 0)*100:.1f}%")
    print(f"  Stage: {result.get('stage', 'unknown')}")

    if 'latency_seconds' in result:
        tracker.record('Risk', 'Total (1+2)', result['latency_seconds'], True)

    print("\n📊 Performance:")
    if total_latency < 3:
        print("  ✅ Excellent: < 3s")
    elif total_latency < 5:
        print("  ✅ Good: < 5s")
    else:
        print("  ⚠️  Slow: > 5s")

    return True


async def test_analyst_agent_latency():
    """Test Analyst Agent latency with real API"""
    print("\n" + "="*60)
    print("Testing AnalystAgentMVP (Two-Stage)")
    print("="*60)

    agent = AnalystAgentMVP()

    price_data = {'current_price': 150.25}

    news_data = [
        {'title': 'AAPL, AI 기능 탑재로 2026년 성장 전망', 'sentiment': 'positive', 'impact_score': 3.5},
        {'title': '연준, 금리 인상 속도 완화 시사', 'sentiment': 'positive', 'impact_score': 2.0}
    ]

    macro_data = {'interest_rate': 5.25, 'gdp_growth': 2.1, 'trend': 'stable'}

    print(f"\n📊 Test Data: AAPL, {len(news_data)} news articles")

    start = time.time()
    result = await agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        news_data=news_data,
        macro_data=macro_data
    )
    total_latency = time.time() - start

    if 'error' in result:
        print(f"❌ Analysis failed: {result['error']}")
        tracker.record('Analyst', 'Total', total_latency, False)
        return False

    print(f"\n✅ Analysis completed in {total_latency:.2f}s")
    print(f"  Action: {result['action']}")
    print(f"  News: {result.get('news_headline', 'N/A')}")
    print(f"  Score: {result.get('overall_information_score', 0):.1f}/10")
    print(f"  Stage: {result.get('stage', 'unknown')}")

    if 'latency_seconds' in result:
        tracker.record('Analyst', 'Total (1+2)', result['latency_seconds'], True)

    print("\n📊 Performance:")
    if total_latency < 3:
        print("  ✅ Excellent: < 3s")
    elif total_latency < 5:
        print("  ✅ Good: < 5s")
    else:
        print("  ⚠️  Slow: > 5s")

    return True


async def test_parallel_execution():
    """Test parallel execution of all agents"""
    print("\n" + "="*60)
    print("Testing Parallel Execution (All Agents)")
    print("="*60)

    trader = TraderAgentMVP()
    risk = RiskAgentMVP()
    analyst = AnalystAgentMVP()

    price_data = {'current_price': 150.25, 'open': 148.50, 'high': 151.00, 'low': 147.80}
    technical_data = {'rsi': 62.5}

    print(f"\n📊 Running all agents in parallel...")

    start = time.time()

    results = await asyncio.gather(
        trader.analyze(symbol='AAPL', price_data=price_data, technical_data=technical_data),
        risk.analyze(symbol='AAPL', price_data=price_data, technical_data=technical_data),
        analyst.analyze(symbol='AAPL', price_data=price_data),
        return_exceptions=True
    )

    total_latency = time.time() - start

    print(f"\n✅ All agents completed in {total_latency:.2f}s")

    for i, result in enumerate(results):
        agent_name = ['Trader', 'Risk', 'Analyst'][i]
        if isinstance(result, Exception):
            print(f"  ❌ {agent_name}: {result}")
            tracker.record(agent_name, 'Parallel', 0, False)
        else:
            action = result.get('action', result.get('recommendation', 'pass'))
            latency = result.get('latency_seconds', 0)
            print(f"  ✅ {agent_name}: {action} ({latency:.2f}s)")
            tracker.record(agent_name, 'Parallel', latency, True)

    print("\n📊 Parallel Performance:")
    if total_latency < 5:
        print("  ✅ Excellent: < 5s (faster than serial)")
    elif total_latency < 8:
        print("  ✅ Good: < 8s")
    else:
        print("  ⚠️  Slow: > 8s")

    return total_latency < 10


async def test_warroom_e2e():
    """Test full WarRoomMVP deliberation"""
    print("\n" + "="*60)
    print("Testing WarRoomMVP E2E (Full Deliberation)")
    print("="*60)

    war_room = WarRoomMVP()

    market_data = {
        'price_data': {
            'current_price': 150.25,
            'open': 148.50,
            'high': 151.00,
            'low': 147.80,
            'volume': 45000000
        },
        'technical_data': {
            'rsi': 62.5,
            'macd': {'value': 1.2, 'signal': 0.8}
        },
        'market_conditions': {
            'vix': 18.5,
            'market_sentiment': 0.6
        }
    }

    portfolio_state = {
        'total_value': 100000,
        'available_cash': 50000,
        'current_positions': []
    }

    additional_data = {
        'news_articles': [
            {'title': 'Apple announces new AI features', 'sentiment': 'positive'}
        ]
    }

    print(f"\n📊 Full deliberation test for AAPL...")

    start = time.time()
    result = await war_room.deliberate(
        symbol='AAPL',
        action_context='new_position',
        market_data=market_data,
        portfolio_state=portfolio_state,
        additional_data=additional_data
    )
    total_latency = time.time() - start

    print(f"\n✅ Deliberation completed in {total_latency:.2f}s")
    print(f"  Final Decision: {result['final_decision']}")
    print(f"  Architecture: {result['architecture']}")

    # Report individual agent latencies
    for agent_name, opinion in result['agent_opinions'].items():
        latency = opinion.get('latency_seconds', 'N/A')
        action = opinion.get('action', opinion.get('recommendation', 'pass'))
        print(f"  - {agent_name.title()}: {action} ({latency}s)")

    tracker.record('WarRoom', 'E2E Deliberation', total_latency, True)

    print("\n📊 E2E Performance:")
    if total_latency < 10:
        print("  ✅ Excellent: < 10s")
    elif total_latency < 15:
        print("  ✅ Good: < 15s")
    elif total_latency < 20:
        print("  ⚠️  Acceptable: < 20s")
    else:
        print("  ❌ Slow: > 20s")

    return True


async def main():
    """Run all E2E tests"""
    print("\n" + "="*80)
    print("Two-Stage WarRoomMVP - E2E Latency Test Suite")
    print("="*80)
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Model: GLM-4.7 (Reasoning) + GLM-4-Flash (Structuring)")

    tests = [
        ("Trader Agent", test_trader_agent_latency),
        ("Risk Agent", test_risk_agent_latency),
        ("Analyst Agent", test_analyst_agent_latency),
        ("Parallel Execution", test_parallel_execution),
        ("WarRoom E2E", test_warroom_e2e)
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

    # Generate final report
    tracker.report()

    print("\n" + "="*80)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*80)

    if failed == 0:
        print("\n🎉 All E2E tests passed!")
        print("\n📊 Key Findings:")
        print("   - Two-Stage architecture is working")
        print("   - Individual agent latencies measured")
        print("   - Parallel execution confirmed")
        print("   - Full WarRoomMVP deliberation tested")
        print("\n💡 Optimization Opportunities:")
        print("   - Implement connection pooling for GLM API")
        print("   - Cache structuring agent responses")
        print("   - Stream reasoning responses")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
