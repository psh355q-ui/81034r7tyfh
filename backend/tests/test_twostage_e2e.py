"""
End-to-End Two-Stage TraderAgentMVP Test

Tests real GLM API calls and measures latency.

Run with:
    python backend/tests/test_twostage_e2e.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Set environment before imports
os.environ.setdefault('GLM_API_KEY', os.getenv('GLM_API_KEY', ''))

# Verify API key is set
if not os.getenv('GLM_API_KEY'):
    print("⚠️  GLM_API_KEY not set. Please set it in environment or .env file.")
    print("   Skipping real API test.")
    sys.exit(0)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_real_api_e2e():
    """
    End-to-end test with real GLM API calls.

    This test:
    1. Calls Stage 1 (Reasoning) with GLM-4.7
    2. Calls Stage 2 (Structuring) with GLM-4-Flash
    3. Measures total latency
    4. Validates final JSON output
    """
    print("\n" + "="*60)
    print("Two-Stage TraderAgentMVP E2E Test")
    print("="*60)

    from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP

    agent = TraderAgentMVP()

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
        'moving_averages': {'ma50': 145.00, 'ma200': 140.00},
        'bollinger_bands': {'upper': 152.00, 'lower': 148.00}
    }

    print("\n📊 Test Data:")
    print(f"  Symbol: AAPL")
    print(f"  Price: ${price_data['current_price']}")
    print(f"  RSI: {technical_data['rsi']}")

    print("\n🔄 Stage 1: Reasoning (GLM-4.7)...")
    stage1_start = time.time()

    reasoning_result = await agent.reasoning_agent.reason(
        symbol='AAPL',
        price_data=price_data,
        technical_data=technical_data
    )

    stage1_latency = time.time() - stage1_start

    if 'error' in reasoning_result:
        print(f"❌ Stage 1 failed: {reasoning_result['error']}")
        return False

    print(f"✅ Stage 1 completed in {stage1_latency:.2f}s")
    print(f"   Reasoning preview: {reasoning_result['reasoning'][:100]}...")

    print("\n🔄 Stage 2: Structuring (GLM-4-Flash)...")

    schema_definition = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["buy", "sell", "hold", "pass"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "reasoning": {"type": "string"},
            "opportunity_score": {"type": "number", "minimum": 0.0, "maximum": 100.0},
            "momentum_strength": {"type": "string"},
            "risk_reward_ratio": {"type": "number"}
        }
    }

    stage2_start = time.time()

    structured_result = await agent.structuring_agent.structure(
        reasoning_text=reasoning_result['reasoning'],
        schema_definition=schema_definition,
        agent_type='trader',
        symbol='AAPL'
    )

    stage2_latency = time.time() - stage2_start

    if 'error' in structured_result:
        print(f"❌ Stage 2 failed: {structured_result['error']}")
        return False

    total_latency = stage1_latency + stage2_latency

    print(f"✅ Stage 2 completed in {stage2_latency:.2f}s")

    print("\n" + "="*60)
    print("📈 Results:")
    print("="*60)
    print(f"Action: {structured_result.get('action')}")
    print(f"Confidence: {structured_result.get('confidence', 0):.2f}")
    print(f"Reasoning: {structured_result.get('reasoning', 'N/A')[:100]}...")
    print(f"Opportunity Score: {structured_result.get('opportunity_score', 0):.1f}")
    print(f"Momentum: {structured_result.get('momentum_strength', 'N/A')}")

    print("\n" + "="*60)
    print("⏱️  Latency Breakdown:")
    print("="*60)
    print(f"Stage 1 (Reasoning):    {stage1_latency:.2f}s")
    print(f"Stage 2 (Structuring):  {stage2_latency:.2f}s")
    print(f"Total:                  {total_latency:.2f}s")

    # Evaluate performance
    print("\n" + "="*60)
    print("📊 Performance Analysis:")
    print("="*60)

    if total_latency < 3:
        print("✅ Excellent: < 3 seconds")
    elif total_latency < 5:
        print("✅ Good: < 5 seconds")
    elif total_latency < 8:
        print("⚠️  Acceptable: < 8 seconds")
    else:
        print("❌ Slow: > 8 seconds (consider optimization)")

    # Validate JSON output
    print("\n" + "="*60)
    print("✅ Validation:")
    print("="*60)

    required_fields = ['action', 'confidence', 'reasoning']
    all_present = all(field in structured_result for field in required_fields)

    if all_present:
        print("✅ All required fields present")
    else:
        missing = [f for f in required_fields if f not in structured_result]
        print(f"❌ Missing fields: {missing}")

    # Validate action enum
    valid_actions = ['buy', 'sell', 'hold', 'pass']
    if structured_result.get('action') in valid_actions:
        print("✅ Valid action value")
    else:
        print(f"❌ Invalid action: {structured_result.get('action')}")

    # Validate confidence range
    conf = structured_result.get('confidence', 0)
    if 0.0 <= conf <= 1.0:
        print("✅ Valid confidence range")
    else:
        print(f"❌ Invalid confidence: {conf}")

    print("\n" + "="*60)
    print("✅ E2E Test Completed Successfully")
    print("="*60)

    return True


async def test_comparison_with_original():
    """
    Compare Two-Stage vs Original architecture.

    This would test the old single-stage approach vs new two-stage,
    but for now we'll just benchmark the two-stage approach.
    """
    print("\n" + "="*60)
    print("Two-Stage Architecture Benchmark")
    print("="*60)

    from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP

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
        'macd': {'value': 1.2, 'signal': 0.8}
    }

    # Run 3 iterations to get average
    iterations = 3
    latencies = []

    print(f"\nRunning {iterations} iterations...")

    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}...")
        start = time.time()

        result = await agent.analyze(
            symbol='AAPL',
            price_data=price_data,
            technical_data=technical_data
        )

        latency = time.time() - start
        latencies.append(latency)

        if 'error' in result:
            print(f"❌ Failed: {result['error']}")
        else:
            print(f"✅ Completed: {latency:.2f}s (action={result.get('action')})")

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print("\n" + "="*60)
    print("📊 Benchmark Results:")
    print("="*60)
    print(f"Iterations:  {iterations}")
    print(f"Avg Latency: {avg_latency:.2f}s")
    print(f"Min Latency: {min_latency:.2f}s")
    print(f"Max Latency: {max_latency:.2f}s")

    return True


async def main():
    """Run E2E tests"""
    tests = [
        ("E2E Test", test_real_api_e2e),
        ("Benchmark", test_comparison_with_original)
    ]

    for name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n✅ All E2E tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
