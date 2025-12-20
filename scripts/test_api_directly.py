"""
Test Deep Reasoning API directly without running server

Phase 14 Option C: Frontend API 통합 테스트 (Direct Call)
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy


async def main():
    print("=" * 80)
    print("Phase 14 Option C: Deep Reasoning API Direct Test")
    print("=" * 80)

    # Deep Reasoning Strategy 생성
    strategy = DeepReasoningStrategy()

    # 테스트 뉴스
    news_text = """
    Microsoft announces $500M investment in OpenAI's new data center project,
    which will exclusively use AMD's MI300 AI accelerators instead of Nvidia GPUs.
    The deal represents a major shift in the AI infrastructure market.
    """

    print(f"\n[NEWS INPUT]\n{news_text.strip()}")
    print("\n[ANALYZING with Gemini 2.5 Pro...]")

    # Deep Reasoning 분석
    result = await strategy.analyze_news(news_text)

    # 결과 출력
    print("\n" + "=" * 80)
    print("ANALYSIS RESULT (This would be sent to Frontend)")
    print("=" * 80)

    print(f"\nInvestment Theme: {result.theme}")

    if result.primary_beneficiary:
        pb = result.primary_beneficiary
        print(f"\n[PRIMARY] Primary Beneficiary:")
        print(f"   Ticker: {pb.get('ticker', 'N/A')}")
        print(f"   Action: {pb.get('action', 'N/A')}")
        print(f"   Confidence: {pb.get('confidence', 0):.0%}")
        if 'reasoning' in pb:
            print(f"   Reason: {pb.get('reasoning', 'N/A')}")

    if result.hidden_beneficiary:
        hb = result.hidden_beneficiary
        print(f"\n[HIDDEN] Hidden Beneficiary:")
        print(f"   Ticker: {hb.get('ticker', 'N/A')}")
        print(f"   Action: {hb.get('action', 'N/A')}")
        print(f"   Confidence: {hb.get('confidence', 0):.0%}")
        if 'reasoning' in hb:
            print(f"   Reason: {hb.get('reasoning', 'N/A')}")

    if result.loser:
        loser = result.loser
        print(f"\n[LOSER] Potential Loser:")
        print(f"   Ticker: {loser.get('ticker', 'N/A')}")
        print(f"   Action: {loser.get('action', 'N/A')}")
        print(f"   Confidence: {loser.get('confidence', 0):.0%}")

    print(f"\n[BULL] Bull Case:")
    print(f"{result.bull_case[:200]}...")

    print(f"\n[BEAR] Bear Case:")
    print(f"{result.bear_case[:200]}...")

    print(f"\n[TRACE] Reasoning Steps:")
    for i, step in enumerate(result.reasoning_trace[:3], 1):
        print(f"   {i}. {step}")

    print("\n" + "=" * 80)
    print("Frontend Integration Test Complete!")
    print("=" * 80)
    print("\nThis result would be displayed in DeepReasoning.tsx component:")
    print("  - Investment theme banner")
    print("  - 3-column beneficiary cards (Primary/Hidden/Loser)")
    print("  - Bull/Bear case panels")
    print("  - Reasoning trace timeline")


if __name__ == "__main__":
    asyncio.run(main())
