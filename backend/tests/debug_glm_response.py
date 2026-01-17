"""
Debug script to see actual GLM API responses for RiskAgentMVP
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from backend.ai.glm_client import GLMClient


async def debug_risk_agent_prompt():
    """Test Risk Agent prompt to see actual response"""
    print("\n" + "=" * 60)
    print("DEBUG: RiskAgentMVP GLM Response")
    print("=" * 60)

    client = GLMClient()

    # Risk Agent system prompt (simplified)
    system_prompt = """당신은 'War Room'의 방어적 리스크 관리자(Defensive Risk Manager)입니다."""

    # Simplified Risk Agent prompt
    prompt = """Analyze risk for AAPL based on the following data:

1. Price & Volatility:
- Current Price: 150.25
- 52W High: 180.00
- 52W Low: 120.00
- Volatility: 0.25

2. Trader Opinion (Attack View):
- Action: buy
- Confidence: 0.75
- Reasoning: Strong uptrend with RSI confirmation

3. Market Conditions:
- Market Sentiment: Neutral
- VIX: Unknown

4. Dividend Information:
No dividend info.

위 정보를 바탕으로 리스크를 분석하고 JSON 형식으로 답변하세요."""

    print("\nSending prompt to GLM...")
    response = await client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.3
    )

    print("\n" + "-" * 60)
    print("RAW RESPONSE STRUCTURE:")
    print("-" * 60)
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False)[:2000])

    print("\n" + "-" * 60)
    print("MESSAGE CONTENT:")
    print("-" * 60)
    message = response["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning_content", "")
    print(f"Content length: {len(content)} chars")
    print(f"\nContent (first 1500 chars):\n{content[:1500]}")
    print(f"\n... (truncated)")

    await client.close()


async def debug_analyst_agent_prompt():
    """Test Analyst Agent prompt to see actual response"""
    print("\n" + "=" * 60)
    print("DEBUG: AnalystAgentMVP GLM Response")
    print("=" * 60)

    client = GLMClient()

    # Analyst Agent system prompt (simplified)
    system_prompt = """당신은 'War Room'의 수석 정보 분석가(Lead Analyst)입니다."""

    # Simplified Analyst Agent prompt
    prompt = """Analyze information for AAPL based on the following data:

1. News & Events:
No recent news reported.

2. Macro Economic Context:
- interest_rate: 5.25
- inflation_rate: 3.1
- fed_policy: hawkish

3. Institutional Flow:
{'direction': 'neutral', 'magnitude': 0.0}

4. Chip War & Geopolitics:
No significant geopolitical events.

위 정보를 바탕으로 분석하고 JSON 형식으로 답변하세요."""

    print("\nSending prompt to GLM...")
    response = await client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.3
    )

    print("\n" + "-" * 60)
    print("RAW RESPONSE STRUCTURE:")
    print("-" * 60)
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False)[:2000])

    print("\n" + "-" * 60)
    print("MESSAGE CONTENT:")
    print("-" * 60)
    message = response["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning_content", "")
    print(f"Content length: {len(content)} chars")
    print(f"\nContent (first 1500 chars):\n{content[:1500]}")
    print(f"\n... (truncated)")

    await client.close()


async def main():
    await debug_risk_agent_prompt()
    await debug_analyst_agent_prompt()


if __name__ == "__main__":
    asyncio.run(main())
