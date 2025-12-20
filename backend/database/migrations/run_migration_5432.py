"""
포트 5432 DB에 직접 마이그레이션 실행
"""
import asyncio
import asyncpg
from pathlib import Path


async def run_migration():
    """마이그레이션 실행"""
    print("=" * 70)
    print("  포트 5432 DB 마이그레이션")
    print("=" * 70)
    print()
    
    # PostgreSQL 연결
    conn_str = "postgresql://postgres:postgres@localhost:5432/ai_trading"
    
    try:
        conn = await asyncpg.connect(conn_str)
        print(f"✅ DB 연결 성공: localhost:5432/ai_trading\n")
        
        # SQL 파일 읽기
        sql_file = Path("backend/database/migrations/add_news_clustering.sql")
        
        if not sql_file.exists():
            print(f"❌ SQL 파일 없음: {sql_file}")
            return
        
        sql = sql_file.read_text(encoding='utf-8')
        
        print("📝 마이그레이션 SQL 실행 중...\n")
        
        # 트랜잭션으로 실행
        async with conn.transaction():
            await conn.execute(sql)
        
        print("✅ 마이그레이션 완료!\n")
        
        # 생성된 테이블 확인
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"📊 생성된 테이블 ({len(tables)}개):")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await conn.close()
        print("\n✅ 완료!")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_migration())
