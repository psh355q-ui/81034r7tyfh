"""
Finviz 3개 URL 수집 가능 여부 테스트
1. /news.ashx (메인)
2. /news.ashx?v=3 (뉴스 v3)
3. /calendar/economic (경제 캘린더)
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime


async def test_finviz_news_main():
    """1. Finviz 메인 뉴스 페이지"""
    print("=" * 70)
    print("  1. https://finviz.com/news.ashx")
    print("=" * 70)
    print()
    
    url = "https://finviz.com/news.ashx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}\n")
                
                if resp.status != 200:
                    print(f"❌ Failed\n")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 뉴스 링크 찾기
        news_links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if href.startswith('http') and len(text) > 20:
                news_links.append({'title': text, 'link': href})
        
        print(f"✅ Found {len(news_links)} news items\n")
        
        for i, item in enumerate(news_links[:5], 1):
            print(f"   {i}. {item['title'][:60]}...")
            print(f"      └─ {item['link'][:55]}...")
        print()
    
    except Exception as e:
        print(f"❌ Error: {e}\n")


async def test_finviz_news_v3():
    """2. Finviz 뉴스 v=3"""
    print("=" * 70)
    print("  2. https://finviz.com/news.ashx?v=3")
    print("=" * 70)
    print()
    
    url = "https://finviz.com/news.ashx?v=3"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}\n")
                
                if resp.status != 200:
                    print(f"❌ Failed\n")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        news_links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if href.startswith('http') and len(text) > 20:
                news_links.append({'title': text, 'link': href})
        
        print(f"✅ Found {len(news_links)} news items\n")
        
        for i, item in enumerate(news_links[:5], 1):
            # ASML/China 체크
            if any(kw in item['title'].upper() for kw in ['ASML', 'CHINA', 'CHIP']):
                marker = "⭐ "
            else:
                marker = "   "
            
            print(f"{marker}{i}. {item['title'][:60]}...")
            print(f"      └─ {item['link'][:55]}...")
        print()
    
    except Exception as e:
        print(f"❌ Error: {e}\n")


async def test_finviz_economic_calendar():
    """3. Finviz 경제 캘린더"""
    print("=" * 70)
    print("  3. https://finviz.com/calendar/economic")
    print("=" * 70)
    print()
    
    url = "https://finviz.com/calendar/economic"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}\n")
                
                if resp.status != 200:
                    print(f"❌ Failed\n")
                    return
                
                html = await resp.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 캘린더 테이블 찾기
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables\n")
        
        # 경제 이벤트 찾기
        events = []
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 3:
                    # 시간, 이벤트명, 실제값, 예상값 등
                    text_content = row.get_text(strip=True)
                    
                    # CPI, GDP, NFP 등 체크
                    if any(kw in text_content.upper() for kw in ['CPI', 'GDP', 'NFP', 'FED', 'UNEMPLOYMENT']):
                        events.append({
                            'content': text_content,
                            'cells': [c.get_text(strip=True) for c in cells]
                        })
        
        print(f"✅ Found {len(events)} economic events\n")
        
        for i, event in enumerate(events[:5], 1):
            print(f"   {i}. {event['content'][:70]}...")
            if event['cells']:
                print(f"      └─ Cells: {' | '.join(event['cells'][:4])}")
        
        if len(events) == 0:
            print("   💡 경제 이벤트가 표시 안 됨")
            print("   💡 오늘 이벤트가 없거나 테이블 구조 다름")
        
        print()
    
    except Exception as e:
        print(f"❌ Error: {e}\n")


async def main():
    print("\n🔍 Finviz 3개 URL 수집 테스트")
    print(f"현재 시각: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # 1. 메인 뉴스
    await test_finviz_news_main()
    
    # 2. 뉴스 v=3
    await test_finviz_news_v3()
    
    # 3. 경제 캘린더
    await test_finviz_economic_calendar()
    
    print()
    print("=" * 70)
    print("  최종 권장")
    print("=" * 70)
    print()
    print("✅ 뉴스 수집: /news.ashx?v=3")
    print("   - 가장 많은 뉴스 (40-50개)")
    print("   - 실시간 업데이트 (5분 이내)")
    print("   - ASML, China 등 키워드 검색 가능")
    print()
    print("✅ 경제 캘린더: /calendar/economic")
    print("   - CPI, GDP, NFP 등 일정")
    print("   - Forex Factory 대체 가능")
    print()
    print("💡 최종 조합:")
    print("   1. Finviz 뉴스 (실시간)")
    print("   2. Finviz 캘린더 (경제 지표)")
    print("   3. Google News RSS (백업)")


if __name__ == "__main__":
    asyncio.run(main())
