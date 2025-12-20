"""
Port 5541, ai_trading_user로 마이그레이션 실행
"""
import asyncio
import asyncpg
from pathlib import Path

async def run_migration():
    print("🔄 뉴스 클러스터링 & 경제 캘린더 마이그레이션 시작...")
    print("📍 Host: localhost")
    print("📍 Port: 5541")
    print("📍 User: ai_trading_user")
    print("📍 Database: ai_trading")
    
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5541,
            user="ai_trading_user",
            password="wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU",
            database="ai_trading"
        )
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    try:
        # 마이그레이션 SQL 파일 읽기
        migration_file = Path(__file__).parent / "add_news_clustering.sql"
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📄 마이그레이션 파일 로드 완료: {len(sql)} bytes")
        
        # 트랜잭션으로 실행
        async with conn.transaction():
            await conn.execute(sql)
        
        print("✅ 마이그레이션 실행 완료!")
        
        # 생성된 테이블 확인
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN (
                'news_clusters',
                'source_credibility',
                'central_bank_officials',
                'economic_calendar_events',
                'economic_event_results',
                'calendar_collection_logs',
                'official_stance_history',
                'voting_rights_history',
                'officials_update_logs'
            )
            ORDER BY table_name
        """)
        
        print(f"\n📊 생성된 테이블 ({len(tables)}개):")
        for table in tables:
            row_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {table['table_name']}"
            )
            print(f"   ✓ {table['table_name']:<30} ({row_count} rows)")
        
        # 초기 데이터 확인
        source_count = await conn.fetchval("SELECT COUNT(*) FROM source_credibility")
        print(f"\n📈 초기 시드 데이터:")
        print(f"   - 출처 신뢰도: {source_count}개 출처 등록됨")
        
        if source_count > 0:
            top_sources = await conn.fetch("""
                SELECT source, tier, credibility_weight 
                FROM source_credibility 
                WHERE tier = 1
                ORDER BY credibility_weight DESC
                LIMIT 5
            """)
            print(f"\n   🏆 Tier 1 출처:")
            for src in top_sources:
                print(f"      - {src['source']:<20} (가중치: {src['credibility_weight']})")
        
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await conn.close()
        print("\n🔌 데이터베이스 연결 종료")

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    
    if success:
        print("\n🎉🎉🎉 마이그레이션 성공! 🎉🎉🎉")
        print("\n✅ Phase 1 우선순위 1 완료!")
        print("\n📝 .env 파일 설정 확인:")
        print("   TIMESCALE_HOST=localhost")
        print("   TIMESCALE_PORT=5541")
        print("   TIMESCALE_USER=ai_trading_user")
        print("   TIMESCALE_PASSWORD=wLzg...")
        print("\n🚀 다음 단계:")
        print("   1. backend/intelligence/four_signal_calculator.py 구현")
        print("   2. backend/intelligence/verdict_classifier.py 구현")
        print("   3. backend/data/calendar/ 수집기 구현")
    else:
        print("\n❌ 마이그레이션 실패")
