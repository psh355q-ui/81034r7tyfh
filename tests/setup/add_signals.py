"""
5541 포트 DB에 샘플 signals 추가 - .env 설정 사용
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta


async def insert_samples():
    # .env: ai_trading_user / wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU
    conn_str = 'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    
    try:
        conn = await asyncpg.connect(conn_str)
        print("✅ DB 연결 성공!")
        
        # 현재 개수 확인
        count_before = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
        print(f"현재 trading_signals: {count_before}개\n")
        
        # 5개 샘플 추가
        now = datetime.now()
        signals = [
            ('AAPL', 'BUY', 'PRIMARY', 0.92, 'Strong momentum', now - timedelta(days=1), 180.50),
            ('NVDA', 'BUY', 'PRIMARY', 0.95, 'AI boom', now - timedelta(days=2), 495.30),
            ('TSLA', 'BUY', 'HIDDEN', 0.78, 'Hidden gem', now - timedelta(days=3), 245.00),
            ('MSFT', 'BUY', 'PRIMARY', 0.89, 'Cloud leader', now - timedelta(hours=18), 380.00),
            ('GOOGL', 'BUY', 'PRIMARY', 0.85, 'Search king', now - timedelta(hours=6), 142.50),
        ]
        
        print(f"📝 {len(signals)}개 signals 추가 중...")
        for ticker, action, signal_type, conf, reason, gen_at, price in signals:
            await conn.execute("""
                INSERT INTO trading_signals (
                    ticker, action, signal_type, confidence, reasoning,
                    generated_at, alert_sent, entry_price, quantity
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, ticker, action, signal_type, conf, reason, gen_at, True, price, 10)
            print(f"  ✓ {ticker} {action} - ${price}")
        
        count_after = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
        print(f"\n✅ 완료! trading_signals: {count_before}개 → {count_after}개\n")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(insert_samples())
