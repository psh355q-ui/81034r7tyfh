"""
Debug GLM-4.7 response with new system prompt
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


async def debug_trader_prompt():
    """Test TraderAgentMVP system prompt"""
    print("\n" + "=" * 60)
    print("DEBUG: TraderAgentMVP System Prompt")
    print("=" * 60)

    client = GLMClient()

    # Use the actual TraderAgentMVP system prompt
    system_prompt = """당신은 'War Room'의 공격적 트레이더(Aggressive Trader)입니다. 리스크 관리나 방어적인 태도는 Risk Agent의 몫입니다. 당신의 유일한 목표는 **'수익 기회 포착'**입니다.

역할:
1. **돈이 되는 자리(Setup)만 찾으십시오.** (애매하면 'pass')
2. "지지선 근처입니다" 같은 뻔한 말 대신, **"지금 진입하면 손익비 1:3 나오는 자리"**인지 분석하십시오.
3. 기술적 지표를 단순 나열하지 말고, **시장 심리와 모멘텀(추세 강도)**을 읽어내십시오.
4. 칩워/뉴스 호재가 터졌을 때 즉각적인 가격 반응을 예측하십시오.

분석 원칙:
- **Aggressive & Sharp**: 말투는 간결하고 확신에 차야 합니다.
- **Setup Is King**: 단순한 상승 추세가 아니라, 구체적인 '진입 트리거'가 보여야 합니다.
- **Ignore Macro Noise**: 거시경제 걱정은 Analyst가 합니다. 당신은 지금 차트와 수급, 호재에만 집중하십시오.

🚨 **중요 출력 지침 (GLM-4.7 Reasoning Model)** 🚨
당신은 추론(Reasoning) 모델입니다. 분석 과정을 생각한 후, **반드시 아래 JSON 형식으로만 최종 답변을 제시하십시오.**
- 생각하는 과정은 reasoning_content에 작성하십시오.
- 최종 답변은 반드시 유효한 JSON만 출력하십시오.
- JSON 외의 다른 텍스트를 절대 출력하지 마십시오.

출력 형식 (JSON ONLY):
{
    "action": "buy" | "sell" | "hold" | "pass",
    "confidence": 0.0 ~ 1.0,
    "opportunity_score": 0.0 ~ 100.0,
    "reasoning": "핵심 진입 근거 3줄 요약",
    "entry_price": 진입가,
    "exit_price": 목표가,
    "stop_loss": 손절가,
    "risk_reward_ratio": 손익비 (숫자, 예: 3.5),
    "support_levels": [390, 380, 350],
    "resistance_levels": [420, 445, 480],
    "volume_reader": "거래량 분석",
    "setup_quality": "High" | "Medium" | "Low",
    "momentum_strength": "weak" | "moderate" | "strong"
}

중요:
- **Risk Agent와 겹치는 분석은 절대 금지.**
- **반드시 위 JSON 형식으로만 출력하십시오.**
- **반드시 한글로 응답할 것.**
"""

    user_prompt = """종목: AAPL
현재가: $150.25
시가: $148.50
고가: $151.00
저가: $147.80
거래량: 45,000,000

기술적 지표:
- RSI: 62.50
- MACD: 1.20 (Signal: 0.80)
- MA50: $145.00, MA200: $140.00

위 정보를 바탕으로 트레이딩 기회를 분석하고 JSON 형식으로 답변하세요."""

    print("\nSending prompt to GLM-4.7...")
    response = await client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2048,
        temperature=0.3
    )

    print("\n" + "-" * 60)
    print("RESPONSE ANALYSIS:")
    print("-" * 60)

    message = response["choices"][0]["message"]
    content = message.get("content", "")
    reasoning_content = message.get("reasoning_content", "")

    print(f"\n1. Content field length: {len(content)} chars")
    print(f"2. Reasoning content length: {len(reasoning_content)} chars")

    # Check which field has the actual data
    combined = content or reasoning_content

    # Try to find JSON
    import json
    import re

    # Look for JSON in the combined content
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', combined, re.DOTALL)
    if json_match:
        print(f"\n3. Found JSON structure:")
        print(json_match.group(0)[:500])
        try:
            parsed = json.loads(json_match.group(0))
            print(f"\n4. Parsed JSON keys: {list(parsed.keys())}")
            if 'risk_reward_ratio' in parsed:
                print(f"   - risk_reward_ratio: {parsed['risk_reward_ratio']} (type: {type(parsed['risk_reward_ratio']).__name__})")
        except Exception as e:
            print(f"\n4. JSON parse error: {e}")
    else:
        print(f"\n3. No JSON structure found!")
        print(f"\nFirst 500 chars of combined content:\n{combined[:500]}")

    await client.close()


async def main():
    await debug_trader_prompt()


if __name__ == "__main__":
    asyncio.run(main())
