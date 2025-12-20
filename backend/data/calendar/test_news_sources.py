"""
NEWS API와 Finviz 실시간 뉴스 테스트
23:30 ASML 뉴스 수집 가능 여부
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


async def test_news_api():
    """NEWS API 테스트"""
    print("=" * 70)
    print("  1. NEWS API 테스트")
    print("=" * 70)
    print()
    
    api_key = os.getenv('NEWS_API_KEY', '')
    
    if not api_key:
        print("❌ NEWS_API_KEY not found")
        return
    
    # ASML 검색
    queries = ["ASML EUV", "ASML China", "ASML semiconductor"]
    
    for query in queries:
        print(f"🔍 '{query}'")
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': datetime.now().strftime('%Y-%m-%dT20:00:00'),  # 20:00부터
                'to': datetime.now().isoformat(),
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': api_key,
                'pageSize': 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        print(f"   ❌ Error {resp.status}")
                        data = await resp.json()
                        print(f"   {data.get('message', '')}\n")
                        continue
                    
                    data = await resp.json()
            
            articles = data.get('articles', [])
            
            if articles:
                print(f"   ✅ Found {len(articles)} articles\n")
                
                for i, article in enumerate(articles[:5], 1):
                    title = article.get('title', '')
                    source = article.get('source', {}).get('name', '')
                    pub = article.get('publishedAt', '')
                    
                    try:
                        pub_time = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                        minutes_ago = (datetime.now() - pub_time.replace(tzinfo=None)).total_seconds() / 60
                        
                        # 23:30 근처 체크
                        if pub_time.hour == 23 and 25 <= pub_time.minute <= 35:
                            marker = "⭐ TARGET! "
                        else:
                            marker = ""
                        
                        print(f"   {i}. {marker}{title[:55]}...")
                        print(f"      └─ {source} | {int(minutes_ago)}분 전")
                    except:
                        print(f"   {i}. {title[:60]}...")
                        print(f"      └─ {source}")
                
                print()
            else:
                print(f"   ❌ No articles\n")
        
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def test_finviz():
    """Finviz 스크래핑 테스트"""
    print("=" * 70)
    print("  2. Finviz 스크래핑 테스트")
    print("=" * 70)
    print()
    
    url = "https://finviz.com/news.ashx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status != 200:
                    print("❌ Failed to access Finviz")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Finviz 뉴스 테이블 찾기
        news_table = soup.find('table', {'id': 'news'})
        
        if not news_table:
            # 다른 방법 시도
            news_table = soup.find('table', class_='news_table')
        
        if not news_table:
            # 모든 테이블 확인
            tables = soup.find_all('table')
            print(f"\n📊 Found {len(tables)} tables on page")
            
            # 뉴스 링크 찾기
            news_links = soup.find_all('a', class_='nn-tab-link')
            if not news_links:
                news_links = soup.find_all('a', href=True, text=True)[:20]
            
            print(f"📰 Found {len(news_links)} news links\n")
            
            for i, link in enumerate(news_links[:10], 1):
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                # ASML 관련만
                if 'ASML' in text.upper() or 'EUV' in text.upper():
                    print(f"⭐ {i}. {text[:60]}...")
                    print(f"   └─ {href[:50]}...")
                else:
                    print(f"   {i}. {text[:60]}...")
            
            print()
        else:
            rows = news_table.find_all('tr')
            print(f"✅ Found news table with {len(rows)} rows\n")
            
            for i, row in enumerate(rows[:10], 1):
                # 시간과 제목 추출
                cells = row.find_all('td')
                if len(cells) >= 2:
                    time_cell = cells[0].get_text(strip=True)
                    news_cell = cells[1]
                    
                    title = news_cell.get_text(strip=True)
                    link = news_cell.find('a')
                    
                    # ASML 체크
                    if 'ASML' in title.upper() or 'EUV' in title.upper():
                        marker = "⭐ ASML! "
                    else:
                        marker = ""
                    
                    print(f"{i}. {marker}{title[:60]}...")
                    print(f"   └─ {time_cell}")
                    if link:
                        print(f"   └─ {link.get('href', '')[:50]}...")
                    print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("\n🔍 실시간 뉴스 수집 테스트")
    print(f"현재 시각: {datetime.now().strftime('%H:%M:%S')}")
    print(f"목표: 23:30 ASML/EUV 뉴스\n")
    
    # 1. NEWS API
    await test_news_api()
    
    # 2. Finviz
    await test_finviz()
    
    print()
    print("=" * 70)
    print("  결론")
    print("=" * 70)
    print()
    print("✅ NEWS API:")
    print("   - 전 세계 주요 언론 커버")
    print("   - 5-15분 지연")
    print("   - 무료 100회/일")
    print()
    print("✅ Finviz:")
    print("   - 금융 뉴스 전문")
    print("   - 실시간성 높음")
    print("   - 무료, bot 차단 가능성")


if __name__ == "__main__":
    asyncio.run(main())
