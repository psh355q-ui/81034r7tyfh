"""
NKE 포지션 복원 스크립트
Day 0 (2025-12-31): Buy NKE 259 shares @ $63.03
"""
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

db_url = os.getenv('DATABASE_URL')
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"📊 Restoring NKE position...")
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# NKE Position 데이터
session_id = 'shadow_2025-12-31T13:37:42.235264'
trade_id = 'NKE_2025-12-31T13:49:00.000000'  # 추정
symbol = 'NKE'
action = 'buy'
quantity = 259
entry_price = 63.03
entry_date = '2025-12-31 13:49:00'
stop_loss_price = entry_price * 0.98  # 2% Stop Loss
reason = 'Shadow buy - Phase 1 Day 0'

try:
    # Insert position
    cursor.execute("""
        INSERT INTO shadow_trading_positions
        (session_id, trade_id, symbol, action, quantity, entry_price, entry_date,
         exit_price, exit_date, pnl, pnl_pct, stop_loss_price, reason, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, (
        session_id, trade_id, symbol, action, quantity, entry_price, entry_date,
        None, None, None, None, stop_loss_price, reason
    ))
    
    conn.commit()
    
    print(f"\n✅ Successfully restored NKE position!")
    print(f"   Symbol: {symbol}")
    print(f"   Quantity: {quantity}")
    print(f"   Entry Price: ${entry_price:.2f}")
    print(f"   Entry Date: {entry_date}")
    print(f"   Stop Loss: ${stop_loss_price:.2f}")
    print(f"   Position Value: ${quantity * entry_price:,.2f}")
    
    # Verify
    cursor.execute("""
        SELECT symbol, quantity, entry_price, stop_loss_price
        FROM shadow_trading_positions
        WHERE session_id = %s AND exit_date IS NULL
    """, (session_id,))
    
    positions = cursor.fetchall()
    print(f"\n📊 Open Positions: {len(positions)}")
    for sym, qty, price, sl in positions:
        print(f"   {sym}: {qty} @ ${price:.2f} (SL: ${sl:.2f})")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Failed to restore position: {e}")
    raise
finally:
    cursor.close()
    conn.close()
