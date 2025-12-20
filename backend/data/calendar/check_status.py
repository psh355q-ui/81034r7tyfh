"""
DB 확인 및 실시간 수집기 상태 체크
"""
import asyncio
import asyncpg
from datetime import datetime


async def check_event_status():
    """이벤트 상태 확인"""
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5541,
        user="ai_trading_user",
        password="wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU",
        database="ai_trading"
    )
    
    try:
        print("=" * 70)
        print("  경제 캘린더 이벤트 상태")
        print("=" * 70)
        print()
        
        # 오늘 이벤트 조회
        events = await conn.fetch(
            """
            SELECT 
                id,
                event_name,
                event_type,
                scheduled_at,
                importance,
                data_source,
                expected_news_burst,
                created_at
            FROM economic_calendar_events
            WHERE DATE(scheduled_at) = CURRENT_DATE
            ORDER BY scheduled_at
            """
        )
        
        if not events:
            print("❌ No events found for today")
            return
        
        print(f"📅 오늘 이벤트: {len(events)}개\n")
        
        for i, event in enumerate(events, 1):
            event_time = event['scheduled_at']
            now = datetime.now()
            time_diff = (event_time - now).total_seconds()
            
            print(f"{i}. {event['event_name']}")
            print(f"   ├─ ID: {event['id']}")
            print(f"   ├─ Type: {event['event_type']}")
            print(f"   ├─ Time: {event_time.strftime('%H:%M')} (한국시간)")
            
            if time_diff > 0:
                print(f"   ├─ Status: ⏳ {int(time_diff/60)}분 {int(time_diff%60)}초 후")
            else:
                print(f"   ├─ Status: ⚡ {int(abs(time_diff)/60)}분 {int(abs(time_diff)%60)}초 전")
            
            print(f"   ├─ Importance: {event['importance']} ({importance_label(event['importance'])})")
            print(f"   └─ Source: {event['data_source']}")
            print()
        
        # 결과 확인
        print("=" * 70)
        print("  이벤트 결과")
        print("=" * 70)
        print()
        
        results = await conn.fetch(
            """
            SELECT 
                r.id,
                r.event_id,
                e.event_name,
                r.actual_value,
                r.data_source,
                r.result_announced_at,
                r.data_collected_at
            FROM economic_event_results r
            JOIN economic_calendar_events e ON r.event_id = e.id
            WHERE DATE(e.scheduled_at) = CURRENT_DATE
            ORDER BY r.data_collected_at DESC
            """
        )
        
        if results:
            print(f"✅ 수집된 결과: {len(results)}개\n")
            for result in results:
                print(f"• {result['event_name']}")
                print(f"  └─ Data: {result['actual_value']}")
                print(f"  └─ Source: {result['data_source']}")
                print(f"  └─ Collected: {result['data_collected_at']}")
                print()
        else:
            print("⏳ 아직 수집된 결과 없음")
            print()
            print("💡 실시간 수집기가 작동 중이라면:")
            print("   - 발표 직전/직후 10초마다 API 체크")
            print("   - Twitter, 뉴스 API, Forex Factory 모니터링")
            print("   - 결과 발견 시 자동 저장")
        
        print()
        
    finally:
        await conn.close()


def importance_label(importance: int) -> str:
    """중요도 라벨"""
    if importance == 1:
        return "⚠️ Critical"
    elif importance == 2:
        return "🔴 High"
    elif importance == 3:
        return "🟠 Medium"
    else:
        return "🟡 Low"


if __name__ == "__main__":
    asyncio.run(check_event_status())
