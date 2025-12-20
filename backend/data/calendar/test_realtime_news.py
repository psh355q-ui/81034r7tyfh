"""
실시간 뉴스 수집 테스트
23:30 발생 뉴스 (6분 전) 수집 가능 여부 확인
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data.calendar.google_news_collector import GoogleNewsRSSCollector


async def test_realtime_news():
    print("=" * 70)
    print("  실시간 뉴스 수집 테스트")
    print("  대상: 23:30 ASML/EUV 뉴스 (약 6분 전)")
    print("=" * 70)
    print()
    
    collector = GoogleNewsRSSCollector()
    
    # 검색 키워드 목록
    queries = [
        "ASML EUV",
        "ASML 중국",
        "ASML 2025",
        "EUV lithography",
        "ASML export",
    ]
    
    print(f"현재 시각: {datetime.now().strftime('%H:%M:%S')}")
    print(f"목표 시각: 23:30 (약 6분 전)")
    print()
    
    for query in queries:
        print(f"🔍 검색: '{query}'")
        print("-" * 70)
        
        # 지난 1시간 내 뉴스 검색
        articles = await collector.search_news(query, hours_back=1)
        
        if articles:
            print(f"   ✅ Found {len(articles)} articles\n")
            
            for i, article in enumerate(articles[:5], 1):
                pub_time = article['published_at']
                minutes_ago = (datetime.now() - pub_time).total_seconds() / 60
                
                # 23:30 근처 체크 (±10분)
                if 23 <= pub_time.hour <= 23 and 20 <= pub_time.minute <= 40:
                    marker = "⭐ TARGET!"
                else:
                    marker = ""
                
                print(f"   {i}. {marker} {article['title'][:60]}...")
                print(f"      ├─ Source: {article['source']}")
                print(f"      ├─ Time: {pub_time.strftime('%H:%M')} ({int(minutes_ago)}분 전)")
                print(f"      └─ Link: {article['link'][:50]}...")
                print()
        else:
            print(f"   ❌ No articles found\n")
    
    # 한국 뉴스 검색 (이미지가 한국어)
    print("=" * 70)
    print("  한국 뉴스 소스 검색")
    print("=" * 70)
    print()
    
    korean_queries = [
        "ASML",
        "반도체 장비",
        "EUV",
    ]
    
    for query in korean_queries:
        # 한글 검색 (hl=ko)
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        
        print(f"🔍 한국어 검색: '{query}'")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        from xml.etree import ElementTree as ET
                        xml = await resp.text()
                        root = ET.fromstring(xml)
                        items = root.findall('.//item')
                        
                        print(f"   ✅ Found {len(items)} articles")
                        
                        for i, item in enumerate(items[:3], 1):
                            title = item.find('title').text if item.find('title') is not None else ''
                            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                            
                            print(f"   {i}. {title[:60]}...")
                            print(f"      └─ {pub_date}")
                        print()
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(test_realtime_news())
