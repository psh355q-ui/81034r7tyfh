"""
5541 DB 테이블 존재 확인 스크립트
"""
import asyncio
import asyncpg


async def check_tables():
    conn_str = 'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    
    conn = await asyncpg.connect(conn_str)
    
    # 현재 DB 확인
    current_db = await conn.fetchval('SELECT current_database()')
    print(f"✅ Connected to: {current_db}")
    
    # 모든 테이블 목록
    tables = await conn.fetch("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """)
    
    print(f"\n📊 Total tables: {len(tables)}")
    for t in tables:
        print(f"  - {t['tablename']}")
    
    # trading_signals 존재 확인
    has_trading_signals = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename = 'trading_signals'
        )
    """)
    
    print(f"\n🔍 Has 'trading_signals' table: {has_trading_signals}")
    
    if has_trading_signals:
        count = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
        print(f"   → trading_signals count: {count}")
    
    # news_articles 컬럼 확인
    news_cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'news_articles'
        ORDER BY ordinal_position
    """)
    
    print(f"\n📋 news_articles columns ({len(news_cols)}):")
    for col in news_cols:
        print(f"  - {col['column_name']}: {col['data_type']}")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_tables())
