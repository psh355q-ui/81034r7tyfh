"""
Test Phase 16: RSS News Crawler

RSS 피드 크롤링 및 자동 분석 테스트
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.news.rss_crawler import RSSNewsCrawler


async def test_rss_crawler():
    """RSS 크롤러 테스트"""
    print("=" * 80)
    print("Phase 16: RSS News Crawler Test")
    print("=" * 80)

    # 크롤러 초기화
    crawler = RSSNewsCrawler()

    print(f"\nMonitoring {len(crawler.RSS_FEEDS)} RSS feeds:")
    for name in crawler.RSS_FEEDS.keys():
        print(f"  - {name}")

    print(f"\nFiltering with {len(crawler.KEYWORDS)} keywords")

    # 단일 사이클 실행
    print("\nRunning single crawl cycle...")
    results = await crawler.run_single_cycle()

    # 결과 출력
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    if results:
        print(f"\nArticles with trading signals: {len(results)}")

        for i, result in enumerate(results, 1):
            article = result['article']
            analysis = result['analysis']
            signals = result['signals']

            print(f"\n{'='*80}")
            print(f"[ARTICLE {i}]")
            print(f"{'='*80}")
            print(f"Title: {article.title}")
            print(f"Source: {article.source}")
            print(f"Published: {article.published_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"URL: {article.url}")

            print(f"\n[ANALYSIS]")
            print(f"Theme: {analysis.theme}")
            print(f"\nBull Case: {analysis.bull_case[:150]}...")
            print(f"\nBear Case: {analysis.bear_case[:150]}...")

            print(f"\n[SIGNALS] ({len(signals)} total)")
            for signal in signals:
                print(f"  {signal['type']:8} | {signal['ticker']:6} | {signal['action']:6} | {signal['confidence']:.0%}")
                if signal.get('reasoning'):
                    print(f"           {signal['reasoning'][:100]}...")

    else:
        print("\nNo relevant articles with signals found")
        print("This is normal if:")
        print("  1. No new AI/semiconductor news in the past 24 hours")
        print("  2. News doesn't match keyword filters")
        print("  3. RSS feeds are temporarily unavailable")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rss_crawler())
