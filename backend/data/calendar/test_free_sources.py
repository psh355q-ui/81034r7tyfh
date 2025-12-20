"""
Forex Factory와 Google News로 윌리엄스 발언 검색
(NEWS API 키 불필요)
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime


async def search_forex_factory():
    """Forex Factory에서 Fed 이벤트 검색"""
    
    print("=" * 70)
    print("  Forex Factory - Fed 이벤트 검색")
    print("=" * 70)
    print()
    
    url = "https://www.forexfactory.com/calendar"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"❌ Error: {resp.status}")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 캘린더 행 찾기
        rows = soup.find_all('tr', class_='calendar__row')
        
        print(f"📊 Found {len(rows)} calendar events\n")
        
        fed_events = []
        for row in rows:
            # 이벤트 제목
            title_elem = row.find('span', class_='calendar__event-title')
            if not title_elem:
                continue
            
            title = title_elem.text.strip()
            
            # Fed 관련만
            if not any(keyword in title.lower() for keyword in ['fed', 'fomc', 'williams', 'powell', 'yellen']):
                continue
            
            # 시간
            time_elem = row.find('td', class_='calendar__time')
            time_str = time_elem.text.strip() if time_elem else 'Unknown'
            
            # 중요도
            impact_elem = row.find('span', class_='calendar__impact')
            impact_class = impact_elem.get('class', []) if impact_elem else []
            
            if 'high' in ' '.join(impact_class) or 'red' in ' '.join(impact_class):
                importance = "🔴 High"
            elif 'medium' in ' '.join(impact_class):
                importance = "🟠 Medium"
            else:
                importance = "🟡 Low"
            
            # 실제값 (발표된 경우)
            actual_elem = row.find('span', class_='calendar__actual')
            actual = actual_elem.text.strip() if actual_elem and actual_elem.text.strip() else "⏳ Pending"
            
            fed_events.append({
                'title': title,
                'time': time_str,
                'importance': importance,
                'actual': actual
            })
        
        if fed_events:
            print(f"✅ Fed 관련 이벤트: {len(fed_events)}개\n")
            
            for i, event in enumerate(fed_events, 1):
                print(f"{i}. {event['title']}")
                print(f"   ├─ Time: {event['time']}")
                print(f"   ├─ Importance: {event['importance']}")
                print(f"   └─ Status: {event['actual']}")
                print()
        else:
            print("❌ No Fed events found today")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def search_google_news():
    """Google News RSS로 Fed 뉴스 검색"""
    
    print("=" * 70)
    print("  Google News - Fed/Williams 검색")
    print("=" * 70)
    print()
    
    queries = [
        "Williams Federal Reserve",
        "Fed Williams speech",
        "John Williams NY Fed"
    ]
    
    for query in queries:
        print(f"🔍 검색: '{query}'")
        print("-" * 70)
        
        try:
            # Google News RSS URL
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"   ❌ Error: {resp.status}\n")
                        continue
                    
                    xml = await resp.text()
            
            # XML 파싱
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml)
            
            items = root.findall('.//item')
            
            if items:
                print(f"   ✅ Found: {len(items)} articles\n")
                
                for i, item in enumerate(items[:5], 1):  # 상위 5개만
                    title = item.find('title').text if item.find('title') is not None else 'No title'
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    
                    print(f"   {i}. {title}")
                    print(f"      ├─ Published: {pub_date}")
                    print(f"      └─ Link: {link[:60]}...")
                    print()
            else:
                print(f"   ❌ No articles found\n")
        
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def main():
    print("\n🔍 윌리엄스 발언 검색 테스트 (무료 소스)\n")
    
    # 1. Forex Factory
    await search_forex_factory()
    
    # 2. Google News
    await search_google_news()
    
    print("=" * 70)
    print("  결론")
    print("=" * 70)
    print()
    print("✅ Forex Factory:")
    print("   - 실시간 업데이트 (20초-1분)")
    print("   - Fed 이벤트 일정표 제공")
    print("   - 무료, 무제한")
    print()
    print("✅ Google News RSS:")
    print("   - 뉴스 기사 검색")
    print("   - 5-15분 지연")
    print("   - 무료, 무제한")
    print()
    print("💡 권장 조합:")
    print("   1. Forex Factory - 발표 시각 추적 (가장 빠름)")
    print("   2. Google News - 발언 내용 상세")
    print("   3. Twitter API - 실시간 반응 (옵션)")


if __name__ == "__main__":
    asyncio.run(main())
