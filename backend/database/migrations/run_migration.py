"""
뉴스 클러스터링 & 경제 캘린더 DB 마이그레이션 실행기

사용법:
    python run_migration.py
"""
import asyncio
import asyncpg
from pathlib import Path
import sys
import os

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# settings import
from backend.config.settings import settings


async def run_migration():
    """마이그레이션 실행"""
    
    print("🔄 뉴스 클러스터링 & 경제 캘린더 마이그레이션 시작...")
    print(f"📍 데이터베이스: {settings.POSTGRES_DB}")
    
    # PostgreSQL 연결
    try:
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    try:
        # 마이그레이션 SQL 파일 읽기
        migration_file = Path(__file__).parent / "add_news_clustering.sql"
        
        if not migration_file.exists():
            print(f"❌ 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📄 마이그레이션 파일 로드 완료: {migration_file.name}")
        print(f"📏 SQL 길이: {len(sql)} bytes")
        
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


async def rollback_migration():
    """마이그레이션 롤백"""
    
    print("🔄 마이그레이션 롤백 시작...")
    
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB
    )
    
    try:
        tables_to_drop = [
            'officials_update_logs',
            'voting_rights_history',
            'official_stance_history',
            'calendar_collection_logs',
            'economic_event_results',
            'economic_calendar_events',
            'central_bank_officials',
            'source_credibility',
            'news_clusters'
        ]
        
        async with conn.transaction():
            for table in tables_to_drop:
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"   ✓ {table} 삭제됨")
        
        print("✅ 롤백 완료")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='뉴스 클러스터링 마이그레이션')
    parser.add_argument('--rollback', action='store_true', help='마이그레이션 롤백')
    args = parser.parse_args()
    
    if args.rollback:
        confirm = input("⚠️  정말 롤백하시겠습니까? (yes/no): ")
        if confirm.lower() == 'yes':
            asyncio.run(rollback_migration())
        else:
            print("❌ 롤백 취소됨")
    else:
        success = asyncio.run(run_migration())
        
        if success:
            print("\n🎉 마이그레이션 성공!")
            print("\n다음 단계:")
            print("  1. backend/intelligence/four_signal_calculator.py 구현")
            print("  2. backend/intelligence/verdict_classifier.py 구현")
            print("  3. backend/data/calendar/ 수집기 구현")
        else:
            print("\n❌ 마이그레이션 실패")
            sys.exit(1)
