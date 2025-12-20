"""
윌리엄스 총재 발표 - 간단 테스트 (비밀번호 하드코딩)
"""
import asyncio
import asyncpg
from datetime import datetime


async def test_williams_event():
    print("=" * 60)
    print("  윌리엄스 총재 발표 실시간 테스트")
    print("  2025-12-17 23:05")
    print("=" * 60)
    print()
    
    # DB 연결
    conn = await asyncpg.connect(
        host="localhost",
        port=5541,
        user="ai_trading_user",
        password="wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU",
        database="ai_trading"
    )
    
    try:
        # 1. 이벤트 추가
        print("📝 Step 1: Adding Williams event to database...")
        
        event_time = datetime(2025, 12, 17, 23, 5, 0)
        
        event_id = await conn.fetchval(
            """
            INSERT INTO economic_calendar_events (
                event_name,
                event_type,
                scheduled_at,
                speech_topic,
                importance,
                data_source,
                expected_news_burst
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            "John Williams - NY Fed President Speech",
            "FED_SPEECH",
            event_time,
            "Economic Outlook and Monetary Policy",
            2,
            "Manual",
            True
        )
        
        print(f"✅ Event added! ID: {event_id}")
        print(f"📅 Event: John Williams Speech")
        print(f"⏰ Scheduled: 23:05 (한국시간)")
        print()
        
        # 2. 현재 시간과 비교
        now = datetime.now()
        time_diff = (event_time - now).total_seconds()
        
        if time_diff > 0:
            print(f"⏳ Event starts in: {int(time_diff/60)}분 {int(time_diff%60)}초")
        else:
            print(f"⚡ Event started: {int(abs(time_diff)/60)}분 {int(abs(time_diff)%60)}초 전")
        
        print()
        print("=" * 60)
        print("  실시간 모니터링 시뮬레이션")
        print("=" * 60)
        print()
        
        # 3. 폴링 전략 시뮬레이션
        print("🎯 다층 폴링 전략:")
        print()
        
        test_times = [
            -1200,  # T-20분
            -900,   # T-15분
            -300,   # T-5분
            -60,    # T-1분
            0,      # T (발표!)
            +60,    # T+1분
            +300,   # T+5분
            +900,   # T+15분
        ]
        
        for seconds in test_times:
            interval = get_polling_interval(seconds)
            
            if seconds < 0:
                time_str = f"T-{abs(seconds)//60}분"
            elif seconds == 0:
                time_str = "T (발표!)"
            else:
                time_str = f"T+{seconds//60}분"
            
            print(f"  {time_str:<12} → {interval}초마다 체크", end="")
            
            if interval == 10:
                print("  ⚡⚡⚡ (집중 모니터링!)")
            elif interval == 30:
                print("  ⚡")
            else:
                print()
        
        print()
        print("✅ 실시간 수집기가 작동중이라면:")
        print("   - 현재는 발표 직전/직후이므로 10초마다 체크")
        print("   - Twitter, 뉴스 API, Forex Factory에서 결과 수집 시도")
        print("   - 결과 발견 시 즉시 DB 저장 및 알림 발송")
        
    finally:
        await conn.close()


def get_polling_interval(time_diff_seconds: float) -> int:
    """폴링 간격 계산"""
    if time_diff_seconds < -900:
        return 300  # 5분
    elif time_diff_seconds < -300:
        return 60   # 1분
    elif time_diff_seconds < 0:
        return 30   # 30초
    elif time_diff_seconds < 300:
        return 10   # 10초 ⚡⚡⚡
    elif time_diff_seconds < 900:
        return 30   # 30초
    else:
        return 60   # 1분


if __name__ == "__main__":
    asyncio.run(test_williams_event())
