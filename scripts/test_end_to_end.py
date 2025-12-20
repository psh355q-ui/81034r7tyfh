"""
End-to-End Test: RSS News → Deep Reasoning → Trading Signal

실제 워크플로우 검증:
1. RSS 뉴스 크롤링
2. Deep Reasoning 분석
3. 트레이딩 시그널 생성
4. 결과 출력
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy


# Mock news data (실제로는 RSS에서 가져옴)
MOCK_NEWS_ITEMS = [
    {
        "title": "Amazon announces $10B investment in cloud AI infrastructure",
        "content": """
        Amazon Web Services announced a massive $10 billion investment in AI infrastructure,
        partnering with Nvidia for H200 GPUs and Marvell for custom networking chips.
        The deal includes exclusive access to Nvidia's next-gen Blackwell architecture.
        """,
        "source": "Reuters",
        "date": "2025-01-15"
    },
    {
        "title": "Apple unveils M4 chip with breakthrough AI capabilities",
        "content": """
        Apple introduced the M4 chip featuring revolutionary Neural Engine improvements.
        Industry sources reveal TSMC manufactured the chip using 3nm process technology.
        The chip will power all Apple AI features, reducing dependency on cloud services.
        """,
        "source": "Bloomberg",
        "date": "2025-01-14"
    },
    {
        "title": "Tesla signs deal with Luminar for next-gen LiDAR sensors",
        "content": """
        Tesla announced partnership with Luminar Technologies for advanced LiDAR systems
        in its upcoming Cybertruck and Model 2 vehicles. The deal marks Tesla's shift
        from camera-only to sensor fusion approach for autonomous driving.
        """,
        "source": "WSJ",
        "date": "2025-01-13"
    }
]


async def analyze_news_item(strategy: DeepReasoningStrategy, news: dict, index: int):
    """단일 뉴스 분석"""
    print(f"\n{'='*80}")
    print(f"[NEWS {index+1}] {news['title']}")
    print(f"Source: {news['source']} | Date: {news['date']}")
    print(f"{'='*80}")

    # 뉴스 텍스트 준비
    news_text = f"{news['title']}. {news['content']}"

    try:
        # Deep Reasoning 분석
        print("\n[ANALYZING...]")
        result = await strategy.analyze_news(news_text)

        # 결과 출력
        print(f"\n[RESULT] Theme: {result.theme}")

        if result.primary_beneficiary:
            pb = result.primary_beneficiary
            print(f"\n  Primary: {pb.get('ticker', 'N/A')} ({pb.get('action', 'N/A')}, {pb.get('confidence', 0):.0%})")

        if result.hidden_beneficiary:
            hb = result.hidden_beneficiary
            print(f"  Hidden: {hb.get('ticker', 'N/A')} ({hb.get('action', 'N/A')}, {hb.get('confidence', 0):.0%}) [STAR]")

        if result.loser:
            loser = result.loser
            print(f"  Loser: {loser.get('ticker', 'N/A')} ({loser.get('action', 'N/A')}, {loser.get('confidence', 0):.0%})")

        print(f"\n  Bull Case: {result.bull_case[:100]}...")
        print(f"  Bear Case: {result.bear_case[:100]}...")

        return {
            "success": True,
            "news": news['title'],
            "result": result
        }

    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")
        return {
            "success": False,
            "news": news['title'],
            "error": str(e)
        }


async def main():
    print("=" * 80)
    print("End-to-End Test: RSS News → Deep Reasoning → Trading Signals")
    print("=" * 80)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"News Items: {len(MOCK_NEWS_ITEMS)}")

    # Deep Reasoning Strategy 초기화
    strategy = DeepReasoningStrategy()

    # 모든 뉴스 분석
    results = []
    for i, news in enumerate(MOCK_NEWS_ITEMS):
        result = await analyze_news_item(strategy, news, i)
        results.append(result)

    # 최종 요약
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal Analyzed: {len(results)}")
    print(f"  Success: {len(successful)}")
    print(f"  Failed: {len(failed)}")

    if successful:
        print(f"\n[SUCCESS] Signals Generated:")
        for r in successful:
            result = r['result']
            if result.hidden_beneficiary:
                ticker = result.hidden_beneficiary.get('ticker', 'N/A')
                print(f"  - {r['news'][:50]}... → Hidden: {ticker}")

    if failed:
        print(f"\n[FAILED] Errors:")
        for r in failed:
            print(f"  - {r['news'][:50]}... → {r['error'][:50]}")

    print("\n" + "=" * 80)
    print("End-to-End Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
