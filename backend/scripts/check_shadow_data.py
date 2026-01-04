"""
Shadow Trading DB 데이터 확인
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"📊 Connecting to database...")
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# 1. Sessions 확인
print("\n" + "="*60)
print("📊 Shadow Trading Sessions")
print("="*60)
cursor.execute("""
    SELECT session_id, status, start_date, initial_capital, available_cash
    FROM shadow_trading_sessions
    ORDER BY start_date DESC
    LIMIT 5
""")

sessions = cursor.fetchall()
if sessions:
    for sid, status, start, initial, cash in sessions:
        print(f"\nSession: {sid}")
        print(f"  Status: {status}")
        print(f"  Start: {start}")
        print(f"  Initial: ${initial:,.2f}")
        print(f"  Cash: ${cash:,.2f}")
else:
    print("\n❌ No sessions found!")

# 2. Positions 확인
print("\n" + "="*60)
print("💼 Shadow Trading Positions")
print("="*60)

cursor.execute("""
    SELECT session_id, symbol, quantity, entry_price, entry_date, exit_date
    FROM shadow_trading_positions
    ORDER BY entry_date DESC
    LIMIT 10
""")

positions = cursor.fetchall()
if positions:
    print(f"\n✅ Found {len(positions)} position(s):")
    for sid, symbol, qty, price, entry, exit in positions:
        status = "OPEN" if exit is None else "CLOSED"
        print(f"\n  {symbol} ({status}):")
        print(f"    Session: {sid}")
        print(f"    Qty: {qty} @ ${price:.2f}")
        print(f"    Entry: {entry}")
        if exit:
            print(f"    Exit: {exit}")
else:
    print("\n❌ No positions found!")

cursor.close()
conn.close()
