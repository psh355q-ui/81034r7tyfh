"""
5541 DB에 누락된 테이블 생성
"""
import asyncio
import asyncpg


async def create_tables():
    conn_str = 'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    
    conn = await asyncpg.connect(conn_str)
    
    print("=" * 70)
    print("  5541 DB: 누락된 테이블 생성")
    print("=" * 70)
    print()
    
    # trading_signals 테이블 생성
    print("📝 Creating trading_signals table...")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS trading_signals (
            id SERIAL PRIMARY KEY,
            analysis_id INTEGER,
            ticker VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL,
            signal_type VARCHAR(20),
            confidence FLOAT,
            reasoning TEXT,
            generated_at TIMESTAMPTZ DEFAULT NOW(),
            alert_sent BOOLEAN DEFAULT FALSE,
            alert_sent_at TIMESTAMPTZ,
            entry_price FLOAT,
            exit_price FLOAT,
            exit_date TIMESTAMPTZ,
            quantity INTEGER DEFAULT 10,
            actual_return_pct FLOAT,
            outcome_recorded_at TIMESTAMPTZ,
            news_summary TEXT
        )
    """)
    print("✅ trading_signals created\n")
    
    # news_articles에 published_date 컬럼 추가
    print("📝 Adding published_date to news_articles...")
    try:
        await conn.execute("""
            ALTER TABLE news_articles 
            ADD COLUMN IF NOT EXISTS published_date TIMESTAMPTZ
        """)
        print("✅ published_date column added\n")
    except Exception as e:
        print(f"⚠️  Column might already exist: {e}\n")
    
    # analysis_results 테이블 확인/생성
    print("📝 Creating analysis_results table...")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            article_id INTEGER,
            theme TEXT,
            bull_case TEXT,
            bear_case TEXT,
            step1_direct_impact TEXT,
            step2_secondary_impact TEXT,
            step3_conclusion TEXT,
            model_name VARCHAR(50),
            analysis_duration_seconds FLOAT,
            analyzed_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    print("✅ analysis_results created\n")
    
    # 테이블 목록 확인
    tables = await conn.fetch("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """)
    
    print(f"📊 Total tables: {len(tables)}")
    for t in tables:
        count = await conn.fetchval(f'SELECT COUNT(*) FROM "{t["tablename"]}"')
        print(f"  - {t['tablename']}: {count} rows")
    
    await conn.close()
    print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(create_tables())
