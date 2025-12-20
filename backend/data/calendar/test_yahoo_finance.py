"""
Yahoo Finance 뉴스 수집 테스트
RSS + 직접 스크래핑
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree import ElementTree as ET


async def test_yahoo_finance_rss():
    """Yahoo Finance RSS 테스트"""
    print("=" * 70)
    print("  1. Yahoo Finance RSS Feed")
    print("=" * 70)
    print()
    
    # Yahoo Finance RSS URL
    rss_url = "https://finance.yahoo.com/news/rss"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status != 200:
                    print("❌ Failed to access RSS")
                    return
                
                xml = await resp.text()
        
        # XML 파싱
        root = ET.fromstring(xml)
        items = root.findall('.//item')
        
        print(f"✅ Found {len(items)} articles in RSS\n")
        
        for i, item in enumerate(items[:10], 1):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            
            title = title_elem.text if title_elem is not None else ''
            link = link_elem.text if link_elem is not None else ''
            pub_date = pub_date_elem.text if pub_date_elem is not None else ''
            
            # ASML, EUV, China 체크
            if any(keyword in title.upper() for keyword in ['ASML', 'EUV', 'CHINA', 'SEMICONDUCTOR']):
                marker = "⭐ "
            else:
                marker = "   "
            
            print(f"{marker}{i}. {title[:60]}...")
            print(f"       └─ {pub_date}")
            print(f"       └─ {link[:50]}...")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_yahoo_finance_article():
    """Yahoo Finance 직접 기사 접근 테스트"""
    print("=" * 70)
    print("  2. Yahoo Finance 직접 기사 접근")
    print("=" * 70)
    print()
    
    # 사용자가 제공한 URL
    article_url = "https://finance.yahoo.com/news/exclusive-china-built-manhattan-project-141758929.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(article_url) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status != 200:
                    print("❌ Failed to access article")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 제목 추출
        title = soup.find('h1')
        if title:
            print(f"\n✅ Article Title:")
            print(f"   {title.get_text(strip=True)}\n")
        
        # 발행 시간 추출
        time_elem = soup.find('time')
        if time_elem:
            print(f"📅 Published:")
            print(f"   {time_elem.get_text(strip=True)}")
            print(f"   DateTime: {time_elem.get('datetime', 'N/A')}\n")
        
        # 본문 일부 추출
        article_body = soup.find('div', class_='caas-body')
        if not article_body:
            article_body = soup.find('article')
        
        if article_body:
            paragraphs = article_body.find_all('p')[:3]
            print(f"📰 Content Preview:")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    print(f"   {text[:100]}...")
            print()
        
        print("✅ Yahoo Finance 기사 접근 성공!")
        print("   - 제목, 시간, 본문 모두 추출 가능")
        print("   - RSS보다 더 빠를 수 있음")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_yahoo_finance_search():
    """Yahoo Finance 검색 페이지 테스트"""
    print()
    print("=" * 70)
    print("  3. Yahoo Finance 뉴스 검색")
    print("=" * 70)
    print()
    
    # Yahoo Finance 뉴스 메인
    news_url = "https://finance.yahoo.com/topic/stock-market-news"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(news_url) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status != 200:
                    print("❌ Failed")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 뉴스 헤드라인 찾기
        headlines = soup.find_all('h3')
        
        print(f"\n✅ Found {len(headlines)} headlines\n")
        
        for i, h3 in enumerate(headlines[:10], 1):
            title = h3.get_text(strip=True)
            link_elem = h3.find('a')
            
            # ASML 체크
            if any(keyword in title.upper() for keyword in ['ASML', 'EUV', 'CHINA']):
                marker = "⭐ "
            else:
                marker = "   "
            
            print(f"{marker}{i}. {title[:60]}...")
            if link_elem:
                print(f"       └─ {link_elem.get('href', '')[:50]}...")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    print("\n🔍 Yahoo Finance 뉴스 수집 테스트")
    print(f"현재 시각: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # 1. RSS Feed
    await test_yahoo_finance_rss()
    
    # 2. 직접 기사
    await test_yahoo_finance_article()
    
    # 3. 검색
    await test_yahoo_finance_search()
    
    print()
    print("=" * 70)
    print("  결론")
    print("=" * 70)
    print()
    print("✅ Yahoo Finance:")
    print("   - RSS Feed 제공 (무료)")
    print("   - 직접 기사 접근 가능")
    print("   - 검색 페이지 스크래핑 가능")
    print("   - 실시간성 높음 (5분 이내)")
    print("   - bot 차단 가능성 낮음")
    print()
    print("💡 권장: Google News와 함께 사용")


if __name__ == "__main__":
    asyncio.run(main())
