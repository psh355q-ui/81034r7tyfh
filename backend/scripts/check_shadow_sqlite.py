"""
Shadow Trading DB 직접 조회 (SQLite)
"""
import sqlite3
from pathlib import Path

# SQLite DB 경로
db_path = Path("d:/code/ai-trading-system/ai_trading.db")

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"📂 Database: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Shadow Trading Sessions
print("=" * 60)
print("📊 Shadow Trading Sessions")
print("=" * 60)
cursor.execute("""
    SELECT session_id, start_date, status, initial_capital, available_cash, end_date
    FROM shadow_trading_sessions
    ORDER BY start_date DESC
    LIMIT 5
""")
sessions = cursor.fetchall()

if sessions:
    for row in sessions:
        session_id, start_date, status, initial, cash, end_date = row
        print(f"\nSession: {session_id}")
        print(f"  Start: {start_date}")
        print(f"  Status: {status}")
        print(f"  Initial: ${initial:,.2f}")
        print(f"  Cash: ${cash:,.2f}")
        print(f"  End: {end_date}")
else:
    print("  No sessions found")

print("\n" + "=" * 60)
print("💼 Open Positions")
print("=" * 60)

# 2. Active session 찾기
cursor.execute("""
    SELECT session_id, available_cash, initial_capital
    FROM shadow_trading_sessions
    WHERE status = 'active'
    ORDER BY start_date DESC
    LIMIT 1
""")
active_session = cursor.fetchone()

if active_session:
    session_id, cash, initial = active_session
    print(f"\n✅ Active Session: {session_id}")
    print(f"  Initial Capital: ${initial:,.2f}")
    print(f"  Available Cash: ${cash:,.2f}")
    
    # 3. Open Positions
    cursor.execute("""
        SELECT symbol, quantity, entry_price, entry_date, stop_loss_price
        FROM shadow_trading_positions
        WHERE session_id = ? AND exit_date IS NULL
    """, (session_id,))
    
    positions = cursor.fetchall()
    
    if positions:
        print(f"\n  Open Positions: {len(positions)}")
        for symbol, qty, entry, date, stop_loss in positions:
            print(f"\n  {symbol}:")
            print(f"    Quantity: {qty}")
            print(f"    Entry Price: ${entry:.2f}")
            print(f"    Entry Date: {date}")
            print(f"    Stop Loss: ${stop_loss:.2f}")
            position_value = qty * entry
            print(f"    Position Value: ${position_value:,.2f}")
    else:
        print("\n  ⚠️ No open positions found")
    
    # 4. Closed Positions
    cursor.execute("""
        SELECT COUNT(*), SUM(pnl)
        FROM shadow_trading_positions
        WHERE session_id = ? AND exit_date IS NOT NULL
    """, (session_id,))
    
    closed_count, total_pnl = cursor.fetchone()
    if closed_count:
        print(f"\n  Closed Trades: {closed_count}")
        print(f"  Total P&L: ${total_pnl:,.2f}")
    else:
        print(f"\n  No closed trades yet")
        
else:
    print("\n❌ No active session found")

print("\n" + "=" * 60)

conn.close()
