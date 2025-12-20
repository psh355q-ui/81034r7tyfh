"""
윌리엄스 총재 발표 실시간 테스트
23:05 발표 이벤트를 DB에 추가하고 실시간 모니터링
"""
import asyncio
import asyncpg
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.config.settings import settings


async def add_williams_event():
    """윌리엄스 총재 발표 이벤트 DB에 추가"""
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5541,
        user="ai_trading_user",
        password=settings.timescale_password,
        database="ai_trading"
    )
    
    try:
        # 윌리엄스 총재 이벤트 추가
        event_time = datetime(2025, 12, 17, 23, 5, 0)  # 23:05
        
        event_id = await conn.fetchval(
            """
            INSERT INTO economic_calendar_events (
                event_name,
                event_type,
                scheduled_at,
                speech_topic,
                speech_location,
                importance,
                data_source,
                expected_news_burst,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            RETURNING id
            """,
            "John Williams - NY Fed President Speech",
            "FED_SPEECH",
            event_time,
            "Economic Outlook and Monetary Policy",
            "Online Event",
            2,  # 중요도 2 (NY Fed는 항상 투표권)
            "Manual",
            True
        )
        
        print(f"✅ Event added! ID: {event_id}")
        print(f"📅 Event: John Williams Speech")
        print(f"⏰ Time: {event_time}")
        print(f"🔔 Importance: 2 (High - NY Fed President with voting rights)")
        
        return event_id
    
    finally:
        await conn.close()


async def start_realtime_monitoring():
    """실시간 모니터링 시작 (간단 버전)"""
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5541,
        user="ai_trading_user",
        password=settings.timescale_password,
        database="ai_trading"
    )
    
    try:
        # 방금 추가한 이벤트 조회
        event = await conn.fetchrow(
            """
            SELECT * FROM economic_calendar_events
            WHERE event_name LIKE '%Williams%'
            AND scheduled_at::date = CURRENT_DATE
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        
        if not event:
            print("❌ Event not found!")
            return
        
        print(f"\n🎯 Monitoring event: {event['event_name']}")
        print(f"⏰ Scheduled: {event['scheduled_at']}")
        
        now = datetime.now()
        event_time = event['scheduled_at']
        time_diff = (event_time - now).total_seconds()
        
        print(f"\n⏳ Time difference: {int(time_diff)} seconds")
        
        if time_diff > 0:
            print(f"   Event starts in {int(time_diff/60)} minutes {int(time_diff%60)} seconds")
        else:
            print(f"   Event started {int(abs(time_diff)/60)} minutes ago")
        
        print("\n🔍 Will check for results from:")
        print("   1. Twitter/X - real-time")
        print("   2. News APIs - 1-3 minutes after")
        print("   3. Forex Factory - 5-10 minutes after")
        
        # 간단한 폴링 루프
        print("\n🚀 Starting monitoring (Press Ctrl+C to stop)...")
        
        check_count = 0
        while check_count < 60:  # 최대 60회 체크 (10분)
            check_count += 1
            
            now = datetime.now()
            time_diff = (event_time - now).total_seconds()
            
            # 폴링 간격 결정
            if abs(time_diff) < 300:  # ±5분 이내
                interval = 10  # 10초마다
            elif abs(time_diff) < 900:  # ±15분 이내
                interval = 30  # 30초마다
            else:
                interval = 60  # 1분마다
            
            # 상태 출력
            if time_diff > 0:
                status = f"⏳ T-{int(time_diff/60)}m{int(time_diff%60)}s"
            else:
                status = f"⚡ T+{int(abs(time_diff)/60)}m{int(abs(time_diff)%60)}s"
            
            print(f"{status} | Check #{check_count} | Next in {interval}s", end='\r')
            
            # TODO: 여기서 실제 API 체크
            # - Twitter API
            # - News API
            # - Forex Factory
            
            # 결과 확인
            result = await conn.fetchrow(
                """
                SELECT * FROM economic_event_results
                WHERE event_id = $1
                """,
                event['id']
            )
            
            if result:
                print(f"\n\n✅ RESULT FOUND!")
                print(f"   Data: {result}")
                break
            
            await asyncio.sleep(interval)
        
        if check_count >= 60:
            print(f"\n⏱️ Monitoring timeout (10 minutes)")
    
    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("  윌리엄스 총재 발표 실시간 테스트")
    print("  2025-12-17 23:05")
    print("=" * 60)
    print()
    
    # 1. 이벤트 추가
    print("📝 Step 1: Adding event to database...")
    event_id = await add_williams_event()
    
    print()
    input("Press Enter to start monitoring...")
    
    # 2. 실시간 모니터링
    print("\n📡 Step 2: Starting realtime monitoring...")
    await start_realtime_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
