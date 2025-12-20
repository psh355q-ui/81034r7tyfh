"""
샘플 Trading Signals 생성 스크립트
12/16-17 스크린샷에 보였던 것과 유사한 데이터 생성
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
import random


async def create_sample_data():
    conn_str = 'postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading'
    
    conn = await asyncpg.connect(conn_str)
    
    print("=" * 70)
    print("  샘플 Trading Signals 생성")
    print("=" * 70)
    print()
    
    # 먼저 기존 데이터 삭제
    print("🗑️  기존 trading_signals 삭제...")
    await conn.execute("DELETE FROM trading_signals")
    
    # 최근 30일간의 diverse한 신호 생성
    tickers = [
        'AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL', 'AMD', 'META', 'AMZN',
        'NFLX', 'DIS', 'INTC', 'BA', 'JPM', 'V', 'MA', 'PYPL',
        'SQ', 'COIN', 'PLTR', 'SNOW'
    ]
    
    actions = ['BUY', 'SELL']
    signal_types = ['PRIMARY', 'HIDDEN', 'LOSER']
    
    signals = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(50):  # 50개 신호 생성
        days_offset = random.randint(0, 30)
        hours_offset = random.randint(0, 23)
        generated_at = base_date + timedelta(days=days_offset, hours=hours_offset)
        
        ticker = random.choice(tickers)
        action = random.choice(actions)
        signal_type = random.choice(signal_types)
        confidence = round(random.uniform(0.65, 0.95), 2)
        
        # Entry price
        entry_price = round(random.uniform(50, 500), 2)
        
        # 일부는 이미 청산됨 (exit_price 있음)
        exit_price = None
        exit_date = None
        actual_return_pct = None
        
        if random.random() > 0.6:  # 40% 확률로 청산
            days_to_exit = random.randint(1, 20)
            exit_date = generated_at + timedelta(days=days_to_exit)
            
            if action == 'BUY':
                exit_price = round(entry_price * random.uniform(0.90, 1.15), 2)
                actual_return_pct = round((exit_price - entry_price) / entry_price * 100, 2)
            else:  # SELL
                exit_price = round(entry_price * random.uniform(0.85, 1.10), 2)
                actual_return_pct = round((entry_price - exit_price) / entry_price * 100, 2)
        
        reasoning = f"{ticker} shows strong momentum based on recent news analysis"
        
        signals.append((
            ticker, action, signal_type, confidence, reasoning,
            generated_at, True, generated_at,
            entry_price, exit_price, exit_date, 10,
            actual_return_pct, exit_date if exit_date else None,
            f"Latest {ticker} news summary"
        ))
    
    # Bulk insert
    print(f"📝 {len(signals)}개 trading signals 생성 중...")
    await conn.executemany("""
        INSERT INTO trading_signals (
            ticker, action, signal_type, confidence, reasoning,
            generated_at, alert_sent, alert_sent_at,
            entry_price, exit_price, exit_date, quantity,
            actual_return_pct, outcome_recorded_at, news_summary
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    """, signals)
    
    # 결과 확인
    count = await conn.fetchval('SELECT COUNT(*) FROM trading_signals')
    print(f"✅ {count}개 signals 생성 완료!\n")
    
    # 샘플 표시
    recent = await conn.fetch("""
        SELECT ticker, action, confidence, generated_at, exit_price
        FROM trading_signals
        ORDER BY generated_at DESC
        LIMIT 10
    """)
    
    print("📊 최근 10개 신호:")
    for r in recent:
        status = "청산" if r['exit_price'] else "활성"
        print(f"  {r['generated_at'].strftime('%m/%d %H:%M')}: {r['ticker']} {r['action']} - {r['confidence']:.2f} [{status}]")
    
    await conn.close()
    print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
