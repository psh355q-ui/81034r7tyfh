"""
5541 DB 테이블 확인 및 데이터 복구
"""
import asyncio
import asyncpg


async def check_db():
    print("=" * 70)
    print("  5541 DB 상태 확인")
    print("=" * 70)
    print()
    
    conn = await asyncpg.connect(
        'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    )
    
    # 테이블 목록
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    print(f"✅ 테이블 개수: {len(tables)}\n")
    
    for table in tables:
        table_name = table['table_name']
        
        # 레코드 개수 확인
        try:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
            print(f"  - {table_name}: {count} rows")
        except:
            print(f"  - {table_name}: ERROR")
    
    print()
    
    # trading_signals 확인
    if any(t['table_name'] == 'trading_signals' for t in tables):
        signals = await conn.fetch("SELECT * FROM trading_signals LIMIT 5")
        print(f"\n📊 trading_signals 샘플 ({len(signals)}개):")
        for sig in signals:
            print(f"  - {sig['ticker']}: {sig['action']}")
    else:
        print("\n❌ trading_signals 테이블 없음!")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_db())
