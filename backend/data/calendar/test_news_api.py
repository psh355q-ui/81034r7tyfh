"""
NEWS API로 윌리엄스 발언 검색 테스트
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 경로 명시
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


async def search_williams_news():
    """NEWS API로 윌리엄스 발언 검색"""
    
    api_key = os.getenv('NEWS_API_KEY', '')  # 수정됨
    
    if not api_key:
        print("❌ NEWS_API_KEY not found in .env")
        print("   Get free key at: https://newsapi.org/")
        return
    
    print("=" * 70)
    print("  NEWS API 검색 테스트: Williams Fed Speech")
    print("=" * 70)
    print()
    
    # 검색 쿼리들
    queries = [
        "Williams Federal Reserve",
        "Williams Fed speech",
        "John Williams NY Fed",
        "Federal Reserve Williams",
    ]
    
    for query in queries:
        print(f"🔍 검색: '{query}'")
        print("-" * 70)
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': (datetime.now() - timedelta(hours=2)).isoformat(),
                'to': datetime.now().isoformat(),
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': api_key,
                'pageSize': 5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        print(f"   ❌ API Error: {resp.status}")
                        data = await resp.json()
                        print(f"   {data.get('message', 'Unknown error')}")
                        continue
                    
                    data = await resp.json()
            
            articles = data.get('articles', [])
            total = data.get('totalResults', 0)
            
            if articles:
                print(f"   ✅ Found: {total} articles (showing top 5)\n")
                
                for i, article in enumerate(articles, 1):
                    title = article.get('title', 'No title')
                    source = article.get('source', {}).get('name', 'Unknown')
                    published = article.get('publishedAt', '')
                    url = article.get('url', '')
                    
                    # 시간 파싱
                    try:
                        pub_time = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        time_ago = (datetime.now() - pub_time.replace(tzinfo=None)).total_seconds() / 60
                        time_str = f"{int(time_ago)}분 전" if time_ago < 60 else f"{int(time_ago/60)}시간 전"
                    except:
                        time_str = published
                    
                    print(f"   {i}. {title}")
                    print(f"      ├─ Source: {source}")
                    print(f"      ├─ Time: {time_str}")
                    print(f"      └─ URL: {url[:60]}...")
                    print()
            else:
                print(f"   ❌ No articles found")
                print()
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    # 추가: 최근 Fed 관련 뉴스
    print("=" * 70)
    print("  최근 Fed 관련 모든 뉴스 (지난 2시간)")
    print("=" * 70)
    print()
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'Federal Reserve OR Fed OR FOMC',
            'from': (datetime.now() - timedelta(hours=2)).isoformat(),
            'to': datetime.now().isoformat(),
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': api_key,
            'pageSize': 10
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    articles = data.get('articles', [])
                    
                    if articles:
                        print(f"✅ Found: {len(articles)} Fed-related articles\n")
                        
                        for i, article in enumerate(articles, 1):
                            title = article.get('title', 'No title')
                            source = article.get('source', {}).get('name', 'Unknown')
                            published = article.get('publishedAt', '')
                            
                            try:
                                pub_time = datetime.fromisoformat(published.replace('Z', '+00:00'))
                                time_ago = (datetime.now() - pub_time.replace(tzinfo=None)).total_seconds() / 60
                                time_str = f"{int(time_ago)}분 전"
                            except:
                                time_str = published
                            
                            # Williams 언급 체크
                            williams_mentioned = 'williams' in title.lower()
                            marker = "⭐" if williams_mentioned else ""
                            
                            print(f"{marker}{i}. {title}")
                            print(f"   └─ {source} | {time_str}")
                            print()
                    else:
                        print("❌ No Fed-related news in last 2 hours")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("💡 NEWS API 특징:")
    print("   - 무료: 100 requests/day")
    print("   - 지연: 보통 5-15분")
    print("   - 커버리지: 전 세계 주요 언론")
    print("   - 한계: 실시간성이 낮음, Forex Factory가 더 빠름")


if __name__ == "__main__":
    asyncio.run(search_williams_news())
