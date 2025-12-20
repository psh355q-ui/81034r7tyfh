"""
analysis_id NULL 허용 후 샘플 signals 추가
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta


async def fix_and_insert():
    conn_str = 'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    
    conn = await asyncpg.connect(conn_str)
    print("✅ DB 연결 성공!\n")
    
    # analysis_id를 NULL 허용으로 변경
    print("📝 analysis_id를 NULL 허용으로 변경 중...")
    try:
        await conn.execute("ALTER TABLE trading_signals ALTER COLUMN analysis_id DROP NOT NULL")
        print("✅ analysis_id NULL 허용 완료\n")
    except Exception as e:
        print(f"⚠️  이미 NULL 허용일 수 있음: {e}\n")
    
    # 5개 샘플 추가
    now = datetime.now()
    signals = [
        ('AAPL', 'BUY', 'PRIMARY', 0.92, 'Strong tech momentum', now - timedelta(days=1), 180.50),
        ('NVDA', 'BUY', 'PRIMARY', 0.95, 'AI chip leader', now - timedelta(days=2), 495.30),
        ('TSLA', 'BUY', 'HIDDEN', 0.78, 'EV recovery', now - timedelta(days=3), 245.00),
        ('MSFT', 'BUY', 'PRIMARY', 0.89, 'Cloud dominance', now - timedelta(hours=18), 380.00),
        ('GOOGL', 'BUY', 'PRIMARY', 0.85, 'Search + AI', now - timedelta(hours=6), 142.50),
    ]
    
    print(f"📝 {len(signals)}개 signals 추가 중...")
    for ticker, action, signal_type, conf, reason, gen_at, price in signals:
        await conn.execute("""
            INSERT INTO trading_signals (
                ticker, action, signal_type, confidence, reasoning,
                generated_at, alert_sent, entry_price, quantity
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, ticker, action, signal_type, conf, reason, gen_at, True, price, 10)
        print(f"  ✓ {ticker} {action} - ${price} ({conf:.0%})")
    
    count = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
    print(f"\n✅ 총 {count}개 signals 생성 완료!\n")
    
    # 샘플 조회
    samples = await conn.fetch("""
        SELECT ticker, action, confidence, entry_price, generated_at
        FROM trading_signals
        ORDER BY generated_at DESC
        LIMIT 5
    """)
    
    print("📊 최근 signals:")
    for s in samples:
        print(f"  {s['ticker']} {s['action']} - ${s['entry_price']:.2f} ({s['confidence']:.0%})")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_and_insert())
