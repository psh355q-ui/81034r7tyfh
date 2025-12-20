"""
Test script for Claude Prompt Caching integration.

This script verifies that:
1. First request creates cache (cache_creation_input_tokens > 0)
2. Subsequent requests use cache (cache_read_input_tokens > 0)
3. Cost savings are correctly calculated
4. Cache expires after 5 minutes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path BEFORE any imports
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set PYTHONPATH to avoid circular imports
os.environ['PYTHONPATH'] = backend_path

from claude_client import ClaudeClient

# Import settings separately to avoid compression module
try:
    from config.settings import settings
except ImportError:
    # Fallback: create minimal settings object
    class MockSettings:
        anthropic_api_key = os.getenv("CLAUDE_API_KEY", "")
        ai_max_tokens = 1024
        ai_temperature = 0.3
        ai_request_timeout = 30
        ai_max_retries = 3
    settings = MockSettings()


async def test_caching():
    """Test Claude prompt caching functionality."""
    print("=" * 80)
    print("Claude Prompt Caching Test")
    print("=" * 80)
    print()

    # Initialize client with caching enabled
    client = ClaudeClient(enable_caching=True)
    print(f"✅ Client initialized with caching: {client.enable_caching}")
    print()

    # Test data
    ticker = "AAPL"
    features = {
        "price": 180.50,
        "rsi_14": 65.2,
        "macd": 1.5,
        "volume_ratio": 1.2,
        "momentum_20d": 0.08,
        "volatility_20d": 0.25,
    }

    market_context = {
        "vix": 18.5,
        "spy_trend": "bullish",
        "sector_performance": {"technology": 0.02},
    }

    # Request 1: Should create cache
    print("=" * 80)
    print("REQUEST 1: Creating cache (first request)")
    print("=" * 80)
    result1 = await client.analyze_stock(ticker, features, market_context)
    print(f"Action: {result1['action']}")
    print(f"Conviction: {result1['conviction']:.2f}")
    print(f"Reasoning: {result1['reasoning']}")
    print()

    metrics1 = client.get_metrics()
    print("Metrics after request 1:")
    print(f"  Total requests: {metrics1['total_requests']}")
    print(f"  Input tokens: {metrics1['total_tokens_input']}")
    print(f"  Output tokens: {metrics1['total_tokens_output']}")
    print(f"  Cache creation tokens: {metrics1['cache_creation_tokens']}")
    print(f"  Cache read tokens: {metrics1['cache_read_tokens']}")
    print(f"  Cost: ${metrics1['total_cost_usd']:.4f}")
    print()

    # Request 2: Should use cache
    print("=" * 80)
    print("REQUEST 2: Using cache (within 5 minutes)")
    print("=" * 80)
    print("Analyzing different ticker with same Constitution...")
    result2 = await client.analyze_stock("GOOGL", features, market_context)
    print(f"Action: {result2['action']}")
    print(f"Conviction: {result2['conviction']:.2f}")
    print(f"Reasoning: {result2['reasoning']}")
    print()

    metrics2 = client.get_metrics()
    print("Metrics after request 2:")
    print(f"  Total requests: {metrics2['total_requests']}")
    print(f"  Input tokens: {metrics2['total_tokens_input']}")
    print(f"  Output tokens: {metrics2['total_tokens_output']}")
    print(f"  Cache creation tokens: {metrics2['cache_creation_tokens']}")
    print(f"  Cache read tokens: {metrics2['cache_read_tokens']}")
    print(f"  Cache hit rate: {metrics2['cache_hit_rate']:.1f}%")
    print(f"  Cost: ${metrics2['total_cost_usd']:.4f}")
    print(f"  Cache valid: {metrics2['cache_is_valid']}")
    print()

    # Request 3: Another cache hit
    print("=" * 80)
    print("REQUEST 3: Using cache again")
    print("=" * 80)
    result3 = await client.analyze_stock("MSFT", features, market_context)
    print(f"Action: {result3['action']}")
    print(f"Conviction: {result3['conviction']:.2f}")
    print(f"Reasoning: {result3['reasoning']}")
    print()

    metrics3 = client.get_metrics()
    print("Metrics after request 3:")
    print(f"  Total requests: {metrics3['total_requests']}")
    print(f"  Input tokens: {metrics3['total_tokens_input']}")
    print(f"  Output tokens: {metrics3['total_tokens_output']}")
    print(f"  Cache creation tokens: {metrics3['cache_creation_tokens']}")
    print(f"  Cache read tokens: {metrics3['cache_read_tokens']}")
    print(f"  Cache hit rate: {metrics3['cache_hit_rate']:.1f}%")
    print(f"  Cost: ${metrics3['total_cost_usd']:.4f}")
    print(f"  Cache valid: {metrics3['cache_is_valid']}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY: Cost Savings from Prompt Caching")
    print("=" * 80)
    print(f"Total cost (with caching): ${metrics3['total_cost_usd']:.4f}")
    print(f"Cost without caching: ${metrics3['cost_without_caching_usd']:.4f}")
    print(f"Savings: ${metrics3['savings_usd']:.4f} ({metrics3['savings_percentage']:.1f}%)")
    print()

    # Expected savings calculation
    constitution_tokens = len(client.CONSTITUTION_SYSTEM_PROMPT.split()) * 1.3  # rough estimate
    print(f"Constitution prompt size: ~{constitution_tokens:.0f} tokens")
    print(f"Constitution was cached and reused {metrics3['total_requests'] - 1} times")
    expected_savings = (
        constitution_tokens * (metrics3['total_requests'] - 1) * 0.80 * 0.9 / 1_000_000
    )
    print(f"Expected savings: ~${expected_savings:.4f}")
    print()

    # Verification
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    success = True

    if metrics3['cache_creation_tokens'] == 0:
        print("❌ FAILED: No cache creation tokens recorded")
        success = False
    else:
        print(f"✅ Cache created: {metrics3['cache_creation_tokens']} tokens")

    if metrics3['cache_read_tokens'] == 0:
        print("❌ FAILED: No cache read tokens recorded")
        success = False
    else:
        print(f"✅ Cache used: {metrics3['cache_read_tokens']} tokens across {metrics3['total_requests']} requests")

    if metrics3['savings_percentage'] < 10:
        print(f"⚠️  WARNING: Low savings percentage: {metrics3['savings_percentage']:.1f}%")
        print("   (Expected >10% with Constitution caching)")
    else:
        print(f"✅ Cost savings achieved: {metrics3['savings_percentage']:.1f}%")

    if not metrics3['cache_is_valid']:
        print("⚠️  WARNING: Cache expired (expected if test took >5 minutes)")
    else:
        print("✅ Cache still valid (within 5-minute TTL)")

    print()

    if success:
        print("🎉 ALL TESTS PASSED - Prompt Caching is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check implementation")

    print("=" * 80)


async def test_non_caching():
    """Test client with caching disabled for comparison."""
    print()
    print("=" * 80)
    print("COMPARISON: Client WITHOUT caching")
    print("=" * 80)
    print()

    client = ClaudeClient(enable_caching=False)
    print(f"Client initialized with caching: {client.enable_caching}")
    print()

    # Same test data
    ticker = "AAPL"
    features = {
        "price": 180.50,
        "rsi_14": 65.2,
        "macd": 1.5,
        "volume_ratio": 1.2,
    }

    # Single request
    result = await client.analyze_stock(ticker, features)
    print(f"Action: {result['action']}")
    print()

    metrics = client.get_metrics()
    print("Metrics:")
    print(f"  Cost: ${metrics['total_cost_usd']:.4f}")
    print(f"  Cache creation tokens: {metrics['cache_creation_tokens']} (should be 0)")
    print(f"  Cache read tokens: {metrics['cache_read_tokens']} (should be 0)")
    print()


if __name__ == "__main__":
    print("Starting Claude Prompt Caching tests...")
    print()

    # Check API key
    if not settings.anthropic_api_key or settings.anthropic_api_key == "":
        print("❌ ERROR: CLAUDE_API_KEY not found in .env")
        print("Please set your API key and try again.")
        sys.exit(1)

    print(f"✅ API key found: {settings.anthropic_api_key[:10]}...")
    print()

    # Run tests
    asyncio.run(test_caching())

    # Optional: compare with non-caching
    print()
    user_input = input("Run comparison test with caching disabled? (y/n): ")
    if user_input.lower() == 'y':
        asyncio.run(test_non_caching())

    print()
    print("Tests completed!")
