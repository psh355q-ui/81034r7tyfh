"""
Simple Two-Stage TraderAgentMVP Integration Test

Standalone test that doesn't require full app context.
Run with:
    python backend/tests/test_twostage_simple.py
"""

import asyncio
import sys
import os

# Set environment before imports
os.environ.setdefault('GLM_API_KEY', os.getenv('GLM_API_KEY', 'test_key'))

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_reasoning_agent():
    """Test Stage 1: Reasoning Agent"""
    print("\n=== Testing Stage 1: Reasoning Agent ===")

    from backend.ai.mvp.trader_agent_twostage import TraderReasoningAgent

    agent = TraderReasoningAgent()

    print(f"✓ Agent initialized: {agent.agent_name} - {agent.role}")

    # Test prompt building
    prompt = agent._build_reasoning_prompt(
        symbol='AAPL',
        price_data={'current_price': 150.25, 'open': 148.50, 'high': 151.00, 'low': 147.80, 'volume': 45000000},
        technical_data={'rsi': 62.5, 'macd': {'value': 1.2, 'signal': 0.8}}
    )

    print(f"✓ Prompt built with {len(prompt)} characters")
    print(f"  Prompt preview: {prompt[:100]}...")

    return True


async def test_structuring_agent():
    """Test Stage 2: Structuring Agent"""
    print("\n=== Testing Stage 2: Structuring Agent ===")

    from backend.ai.mvp.structuring_agent import StructuringAgent

    agent = StructuringAgent()

    print(f"✓ Agent initialized: {agent.model}")

    # Test JSON extraction
    test_cases = [
        ('Direct JSON', '{"action": "buy", "confidence": 0.8}'),
        ('Markdown', '```json\n{"action": "sell", "confidence": 0.7}\n```'),
        ('Embedded text', 'Analysis result: {"action": "hold", "confidence": 0.5}\nDone.')
    ]

    for name, text in test_cases:
        result = agent._extract_json(text)
        print(f"✓ {name}: action={result.get('action')}, confidence={result.get('confidence')}")

    # Test default result
    default = agent._get_default_result('trader', 'AAPL', 'Test error')
    print(f"✓ Default result: action={default['action']}, stage={default.get('stage')}")

    return True


async def test_two_stage_integration():
    """Test Two-Stage Integration"""
    print("\n=== Testing Two-Stage Integration ===")

    from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP

    agent = TraderAgentMVP()

    print(f"✓ Two-Stage Agent initialized")
    print(f"  - Weight: {agent.weight}")
    print(f"  - Architecture: two-stage")

    info = agent.get_agent_info()
    print(f"✓ Agent info:")
    print(f"  - Name: {info['name']}")
    print(f"  - Stages: {info['stages']}")

    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Two-Stage TraderAgentMVP Test Suite")
    print("="*60)

    tests = [
        ("Reasoning Agent", test_reasoning_agent),
        ("Structuring Agent", test_structuring_agent),
        ("Two-Stage Integration", test_two_stage_integration)
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

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
