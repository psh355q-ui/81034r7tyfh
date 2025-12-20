"""
직접 127.0.0.1로 마이그레이션 실행
"""
import asyncio
import asyncpg
from pathlib import Path

async def run_migration():
    print("🔄 뉴스 클러스터링 & 경제 캘린더 마이그레이션 시작...")
    print("📍 Host: 127.0.0.1")
    print("📍 Port: 5432")
    print("📍 Database: ai_trading")
    
    # 하드코딩된 연결 정보
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=5432,
            user="postgres",
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
        
        print(f"📄 마이그레이션 파일 로드 완료")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await conn.close()

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    
    if success:
        print("\n🎉 마이그레이션 성공!")
        print("\n✅ Phase 1 우선순위 1 완료!")
        print("\n다음 단계:")
        print("  1. .env 파일에서 TIMESCALE_HOST=127.0.0.1 로 변경")
        print("  2. .env 파일에서 TIMESCALE_PORT=5432 로 변경")
        print("  3. backend/intelligence/ 구현 시작")
