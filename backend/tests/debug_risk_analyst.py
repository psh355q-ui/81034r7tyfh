"""
Debug RiskAgentMVP and AnalystAgentMVP responses
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


async def test_risk_agent():
    """Test RiskAgentMVP system prompt"""
    print("\n" + "=" * 60)
    print("DEBUG: RiskAgentMVP")
    print("=" * 60)

    client = GLMClient()

    system_prompt = """당신은 'War Room'의 방어적 리스크 관리자입니다.

🚨 **GLM-4.7 추론 모델 출력 지침** 🚨
당신은 GLM-4.7 추론 모델입니다. 분석 과정을 reasoning_content에 작성한 후, **반드시 마지막에 아래 JSON 형식으로 답변을 제시하십시오.**

**중요**: reasoning_content의 마지막 부분에 반드시 아래 JSON을 포함하십시오.

출력 형식 (reasoning_content 마지막에 반드시 포함):
{
    "risk_level": "high",
    "confidence": 0.7,
    "reasoning": "테스트",
    "stop_loss_pct": 0.02,
    "recommendation": "reduce_size"
}"""

    user_prompt = "AAPL 리스크를 분석하고 JSON으로 답변하세요."

    response = await client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=500,
        temperature=0.3
    )

    msg = response["choices"][0]["message"]
    reasoning = msg.get("reasoning_content", "")

    print(f"Reasoning length: {len(reasoning)}")
    print(f"\n--- LAST 800 CHARS ---")
    print(reasoning[-800:])

    # Check for JSON
    import re
    import json

    # Try to find JSON at the end
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}$', reasoning)

    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            print(f"\n--- FOUND JSON ---")
            print(f"Keys: {list(parsed.keys())}")
        except:
            print(f"\n--- FOUND BUT INVALID JSON ---")
            print(json_match.group(0)[:200])
    else:
        print(f"\n--- NO JSON FOUND ---")

    await client.close()


async def main():
    await test_risk_agent()


if __name__ == "__main__":
    asyncio.run(main())
