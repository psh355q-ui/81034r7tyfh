"""
Forex Factory 스크래퍼 실전 테스트
실제 Fed 이벤트 수집
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data.calendar.forex_factory_scraper import ForexFactoryScraper


async def test_forex_factory():
    print("=" * 70)
    print("  Forex Factory 실시간 수집 테스트")
    print("=" * 70)
    print()
    
    scraper = ForexFactoryScraper()
    
    # 1. 향후 24시간 이벤트 수집
    print("📅 Step 1: 향후 24시간 이벤트 수집")
    print("-" * 70)
    
    upcoming = await scraper.get_upcoming_events(hours_ahead=24)
    
    if upcoming:
        print(f"✅ Found {len(upcoming)} events\n")
        
        for i, event in enumerate(upcoming, 1):
            print(f"{i}. {event['event_name']}")
            print(f"   ├─ Time: {event['scheduled_at'].strftime('%H:%M %Z')}")
            print(f"   ├─ Importance: {event['importance']} (1=High, 5=Low)")
            if event.get('forecast'):
                print(f"   ├─ Forecast: {event['forecast']}")
            print(f"   └─ Source: {event['source']}")
            print()
    else:
        print("❌ No upcoming events found")
    
    print()
    
    # 2. 특정 이벤트 결과 검색 (Williams 발언)
    print("=" * 70)
    print("  Step 2: Williams 발언 결과 검색")
    print("=" * 70)
    print()
    
    search_terms = [
        "Williams",
        "Fed Speaks",
        "FOMC",
        "Federal Reserve"
    ]
    
    for term in search_terms:
        print(f"🔍 검색: '{term}'")
        result = await scraper.get_latest_result(term)
        
        if result:
            print(f"   ✅ Found!")
            print(f"   ├─ Event: {result.get('event_name', 'Unknown')}")
            print(f"   ├─ Actual: {result.get('actual', 'N/A')}")
            print(f"   ├─ Forecast: {result.get('forecast', 'N/A')}")
            print(f"   ├─ Previous: {result.get('previous', 'N/A')}")
            print(f"   └─ Time: {result.get('time', 'Unknown')}")
        else:
            print(f"   ❌ No result yet")
        print()
    
    # 3. 일반적인 경제 지표 체크 (CPI, GDP 등)
    print("=" * 70)
    print("  Step 3: 주요 경제 지표 최신 결과")
    print("=" * 70)
    print()
    
    indicators = ["CPI", "GDP", "NFP", "Unemployment"]
    
    for indicator in indicators:
        result = await scraper.get_latest_result(indicator)
        
        if result:
            print(f"✅ {indicator}")
            print(f"   ├─ Actual: {result.get('actual')}{result.get('unit', '')}")
            print(f"   ├─ Forecast: {result.get('forecast')}{result.get('unit', '')}")
            print(f"   └─ Time: {result.get('time')}")
            print()
        else:
            print(f"⏳ {indicator}: No recent data")
            print()


if __name__ == "__main__":
    try:
        asyncio.run(test_forex_factory())
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
