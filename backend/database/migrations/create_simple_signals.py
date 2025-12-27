"""
간단한 샘플 trading_signals 생성 (5432 포트 DB)
"""
import asyncio
import asyncpg
import os
from datetime import datetime, timedelta


async def create_simple_signals():
    # 5541 포트로 연결 (docker-compose.yml의 host port)
    db_password = os.getenv('DB_PASSWORD', '')
    conn_str = f'postgresql://postgres:{db_password}@localhost:5541/ai_trading'
    
    conn = await asyncpg.connect(conn_str)
    
    print("=" * 70)
    print("  간단한 샘플 Trading Signals 생성")
    print("=" * 70)
    print()
    
    # 샘플 데이터 (5개)
    now = datetime.now()
    signals = [
        ('AAPL', 'BUY', 'PRIMARY', 0.92, 'Strong buy signal', now - timedelta(days=1), 180.50, None),
        ('NVDA', 'BUY', 'PRIMARY', 0.95, 'AI momentum', now - timedelta(days=2), 495.30, None),
        ('TSLA', 'BUY', 'HIDDEN', 0.78, 'Hidden opportunity', now - timedelta(days=3), 245.00, None),
        ('MSFT', 'BUY', 'PRIMARY', 0.89, 'Cloud growth', now - timedelta(days=1), 380.00, None),
        ('GOOGL', 'BUY', 'PRIMARY', 0.85, 'Search dominance', now - timedelta(hours=12), 142.50, None),
    ]
    
    print(f"📝 {len(signals)}개 signals 생성 중...")
    for ticker, action, signal_type, confidence, reasoning, gen_at, entry_price, exit_price in signals:
        await conn.execute("""
            INSERT INTO trading_signals (
                ticker, action, signal_type, confidence, reasoning,
                generated_at, alert_sent, entry_price, exit_price, quantity
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, ticker, action, signal_type, confidence, reasoning, gen_at, True, entry_price, exit_price, 10)
        print(f"  ✓ {ticker} {action} ({confidence:.2f})")
    
    count = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
    print(f"\n✅ 총 {count}개 signals 생성 완료!\n")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(create_simple_signals())
