"""
Simple standalone test for Claude Prompt Caching.
No imports from backend modules to avoid circular dependencies.
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from anthropic import Anthropic


CONSTITUTION_PROMPT = """You are an expert quantitative trading analyst with a strong focus on risk management and capital preservation.

CORE CONSTITUTION PRINCIPLES:

Article 1: Risk Management First
- Capital preservation is paramount
- Never recommend trades that could result in catastrophic loss (>5% of portfolio)

Article 2: Data-Driven Decisions
- All recommendations must be based on quantitative data
- Technical indicators (RSI, MACD, volume, momentum) are primary signals

Article 3: Conservative Approach
- When in doubt, recommend HOLD
- BUY only if conviction ≥ 70% AND risk is acceptable

RESPONSE FORMAT:
Return valid JSON:
{
    "action": "BUY" | "SELL" | "HOLD",
    "conviction": 0.0-1.0,
    "reasoning": "Brief explanation",
    "risk_factors": ["factor1", "factor2"]
}"""


async def test_caching():
    """Test Claude prompt caching."""
    print("=" * 80)
    print("Claude Prompt Caching Test (Standalone)")
    print("=" * 80)
    print()

    # Get API key
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("❌ ERROR: CLAUDE_API_KEY not set")
        print("Set environment variable: $env:CLAUDE_API_KEY='your-key'")
        return

    print(f"✅ API key found: {api_key[:10]}...")
    print()

    # Initialize client
    client = Anthropic(api_key=api_key)

    # Metrics
    metrics = {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "total_cost": 0.0
    }

    # Request 1: Create cache
    print("=" * 80)
    print("REQUEST 1: Creating cache")
    print("=" * 80)

    start = time.time()
    response1 = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        temperature=0.3,
        system=[{
            "type": "text",
            "text": CONSTITUTION_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{
            "role": "user",
            "content": "Analyze AAPL: RSI=65.2, MACD=1.5, Price=$180.50"
        }]
    )
    latency1 = (time.time() - start) * 1000

    # Update metrics
    metrics["requests"] += 1
    metrics["input_tokens"] += response1.usage.input_tokens
    metrics["output_tokens"] += response1.usage.output_tokens
    if hasattr(response1.usage, 'cache_creation_input_tokens'):
        metrics["cache_creation_tokens"] += response1.usage.cache_creation_input_tokens

    # Calculate cost
    cost1 = (
        response1.usage.input_tokens * 0.80 / 1_000_000 +
        response1.usage.output_tokens * 4.00 / 1_000_000
    )
    if hasattr(response1.usage, 'cache_creation_input_tokens'):
        cost1 += response1.usage.cache_creation_input_tokens * 1.00 / 1_000_000
    metrics["total_cost"] += cost1

    print(f"Response: {response1.content[0].text[:100]}...")
    print(f"Input tokens: {response1.usage.input_tokens}")
    print(f"Output tokens: {response1.usage.output_tokens}")
    if hasattr(response1.usage, 'cache_creation_input_tokens'):
        print(f"Cache created: {response1.usage.cache_creation_input_tokens} tokens")
    print(f"Cost: ${cost1:.6f}")
    print(f"Latency: {latency1:.0f}ms")
    print()

    # Request 2: Use cache
    print("=" * 80)
    print("REQUEST 2: Using cache (within 5 minutes)")
    print("=" * 80)

    start = time.time()
    response2 = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        temperature=0.3,
        system=[{
            "type": "text",
            "text": CONSTITUTION_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{
            "role": "user",
            "content": "Analyze GOOGL: RSI=55.8, MACD=0.8, Price=$140.20"
        }]
    )
    latency2 = (time.time() - start) * 1000

    # Update metrics
    metrics["requests"] += 1
    metrics["input_tokens"] += response2.usage.input_tokens
    metrics["output_tokens"] += response2.usage.output_tokens
    if hasattr(response2.usage, 'cache_read_input_tokens'):
        metrics["cache_read_tokens"] += response2.usage.cache_read_input_tokens

    # Calculate cost
    cost2 = (
        response2.usage.input_tokens * 0.80 / 1_000_000 +
        response2.usage.output_tokens * 4.00 / 1_000_000
    )
    if hasattr(response2.usage, 'cache_read_input_tokens'):
        cost2 += response2.usage.cache_read_input_tokens * 0.08 / 1_000_000
    metrics["total_cost"] += cost2

    print(f"Response: {response2.content[0].text[:100]}...")
    print(f"Input tokens: {response2.usage.input_tokens}")
    print(f"Output tokens: {response2.usage.output_tokens}")
    if hasattr(response2.usage, 'cache_read_input_tokens'):
        print(f"Cache read: {response2.usage.cache_read_input_tokens} tokens ✅")
    print(f"Cost: ${cost2:.6f}")
    print(f"Latency: {latency2:.0f}ms")
    print()

    # Request 3: Another cache hit
    print("=" * 80)
    print("REQUEST 3: Using cache again")
    print("=" * 80)

    start = time.time()
    response3 = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        temperature=0.3,
        system=[{
            "type": "text",
            "text": CONSTITUTION_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{
            "role": "user",
            "content": "Analyze MSFT: RSI=70.1, MACD=2.0, Price=$420.30"
        }]
    )
    latency3 = (time.time() - start) * 1000

    # Update metrics
    metrics["requests"] += 1
    metrics["input_tokens"] += response3.usage.input_tokens
    metrics["output_tokens"] += response3.usage.output_tokens
    if hasattr(response3.usage, 'cache_read_input_tokens'):
        metrics["cache_read_tokens"] += response3.usage.cache_read_input_tokens

    # Calculate cost
    cost3 = (
        response3.usage.input_tokens * 0.80 / 1_000_000 +
        response3.usage.output_tokens * 4.00 / 1_000_000
    )
    if hasattr(response3.usage, 'cache_read_input_tokens'):
        cost3 += response3.usage.cache_read_input_tokens * 0.08 / 1_000_000
    metrics["total_cost"] += cost3

    print(f"Response: {response3.content[0].text[:100]}...")
    print(f"Input tokens: {response3.usage.input_tokens}")
    print(f"Output tokens: {response3.usage.output_tokens}")
    if hasattr(response3.usage, 'cache_read_input_tokens'):
        print(f"Cache read: {response3.usage.cache_read_input_tokens} tokens ✅")
    print(f"Cost: ${cost3:.6f}")
    print(f"Latency: {latency3:.0f}ms")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY: Cost Savings Analysis")
    print("=" * 80)

    # Calculate cost without caching
    cost_without_caching = (
        metrics["input_tokens"] * 0.80 / 1_000_000 +
        metrics["output_tokens"] * 4.00 / 1_000_000
    )

    savings = cost_without_caching - metrics["total_cost"]
    savings_pct = (savings / cost_without_caching * 100) if cost_without_caching > 0 else 0

    print(f"Total requests: {metrics['requests']}")
    print(f"Total input tokens: {metrics['input_tokens']}")
    print(f"Total output tokens: {metrics['output_tokens']}")
    print(f"Cache creation tokens: {metrics['cache_creation_tokens']}")
    print(f"Cache read tokens: {metrics['cache_read_tokens']}")
    print()
    print(f"Cost WITH caching: ${metrics['total_cost']:.6f}")
    print(f"Cost WITHOUT caching: ${cost_without_caching:.6f}")
    print(f"Savings: ${savings:.6f} ({savings_pct:.1f}%)")
    print()

    # Verification
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    success = True

    if metrics["cache_creation_tokens"] == 0:
        print("❌ FAILED: No cache creation tokens")
        success = False
    else:
        print(f"✅ Cache created: {metrics['cache_creation_tokens']} tokens")

    if metrics["cache_read_tokens"] == 0:
        print("❌ FAILED: No cache read tokens")
        success = False
    else:
        print(f"✅ Cache used: {metrics['cache_read_tokens']} tokens")

    cache_hit_rate = (metrics['cache_read_tokens'] / metrics['input_tokens'] * 100) if metrics['input_tokens'] > 0 else 0
    print(f"✅ Cache hit rate: {cache_hit_rate:.1f}%")

    if savings_pct < 10:
        print(f"⚠️  WARNING: Low savings: {savings_pct:.1f}%")
    else:
        print(f"✅ Cost savings: {savings_pct:.1f}%")

    print()

    if success:
        print("🎉 ALL TESTS PASSED - Prompt Caching works!")
    else:
        print("❌ SOME TESTS FAILED")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_caching())
