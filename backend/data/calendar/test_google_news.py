"""
Google News RSS 실전 테스트
윌리엄스 발언 검색
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data.calendar.google_news_collector import GoogleNewsRSSCollector


async def test_google_news():
    print("=" * 70)
    print("  Google News RSS 실시간 테스트")
    print("=" * 70)
    print()
    
    collector = GoogleNewsRSSCollector()
    
    # 1. Williams 발언 검색
    print("📰 Step 1: Williams 연준 발언 검색")
    print("-" * 70)
    
    williams_news = await collector.search_fed_speech("Williams")
    
    if williams_news:
        print(f"✅ Found Williams news!\n")
        print(f"Title: {williams_news['title']}")
        print(f"Source: {williams_news['source']}")
        print(f"Published: {williams_news['published_at']}")
        print(f"Link: {williams_news['link']}")
        print()
    else:
        print("❌ No Williams news in last 2 hours")
        print()
    
    # 2. 일반 Fed 뉴스 검색
    print("=" * 70)
    print("  Step 2: 최근 Fed 관련 뉴스 (지난 2시간)")
    print("=" * 70)
    print()
    
    fed_queries = [
        "Federal Reserve",
        "Fed interest rate",
        "FOMC",
        "Powell Fed",
    ]
    
    for query in fed_queries:
        articles = await collector.search_news(query, hours_back=2)
        
        print(f"🔍 '{query}': {len(articles)} articles")
        
        if articles:
            # 상위 3개만 표시
            for i, article in enumerate(articles[:3], 1):
                minutes_ago = (datetime.now() - article['published_at']).total_seconds() / 60
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      └─ {article['source']} | {int(minutes_ago)}분 전")
            print()
    
    # 3. 경제 지표 뉴스
    print("=" * 70)
    print("  Step 3: 경제 지표 뉴스")
    print("=" * 70)
    print()
    
    indicators = ["CPI", "GDP", "NFP", "Unemployment"]
    
    for indicator in indicators:
        articles = await collector.search_economic_event(indicator)
        
        print(f"📊 {indicator}: {len(articles)} articles")
        
        if articles:
            latest = articles[0]
            hours_ago = (datetime.now() - latest['published_at']).total_seconds() / 3600
            print(f"   Latest: {latest['title'][:50]}...")
            print(f"   └─ {latest['source']} | {int(hours_ago)}시간 전")
        print()


from datetime import datetime

if __name__ == "__main__":
    try:
        asyncio.run(test_google_news())
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
