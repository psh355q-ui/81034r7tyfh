"""
Shadow Trading 상태 직접 확인

DB에서 직접 세션 및 포지션 정보 조회
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from backend.database.connection import get_async_session
from sqlalchemy import text

async def check_shadow_trading():
    """Shadow Trading 세션 및 포지션 확인"""
    
    async for session in get_async_session():
        try:
            # 1. 활성 세션 확인
            result = await session.execute(text("""
                SELECT session_id, start_date, status, initial_capital, available_cash
                FROM shadow_trading_sessions
                WHERE status = 'active'
                ORDER BY start_date DESC
                LIMIT 1
            """))
            active_session = result.fetchone()
            
            if active_session:
                print("\n📊 Active Shadow Trading Session:")
                print(f"  Session ID: {active_session[0]}")
                print(f"  Start Date: {active_session[1]}")
                print(f"  Status: {active_session[2]}")
                print(f"  Initial Capital: ${active_session[3]:,.2f}")
                print(f"  Available Cash: ${active_session[4]:,.2f}")
                
                # 2. 열린 포지션 확인
                result = await session.execute(text("""
                    SELECT symbol, quantity, entry_price, entry_date, stop_loss_price
                    FROM shadow_trading_positions
                    WHERE session_id = :session_id
                    AND exit_date IS NULL
                """), {"session_id": active_session[0]})
                
                positions = result.fetchall()
                
                if positions:
                    print(f"\n💼 Open Positions ({len(positions)}):")
                    for pos in positions:
                        symbol, qty, entry, date, stop_loss = pos
                        print(f"  {symbol}: {qty} shares @ ${entry:.2f}")
                        print(f"    Entry: {date}")
                        print(f"    Stop Loss: ${stop_loss:.2f}")
                else:
                    print("\n⚠️  No open positions found")
                
                # 3. 완료된 거래 확인
                result = await session.execute(text("""
                    SELECT COUNT(*), 
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                           SUM(pnl) as total_pnl
                    FROM shadow_trading_positions
                    WHERE session_id = :session_id
                    AND exit_date IS NOT NULL
                """), {"session_id": active_session[0]})
                
                stats = result.fetchone()
                if stats and stats[0] > 0:
                    print(f"\n📈 Completed Trades:")
                    print(f"  Total: {stats[0]}")
                    print(f"  Wins: {stats[1]}")
                    print(f"  Total P&L: ${stats[2]:,.2f}")
                else:
                    print("\n📭 No completed trades yet")
                    
            else:
                print("\n❌ No active Shadow Trading session found")
                
                # 모든 세션 확인
                result = await session.execute(text("""
                    SELECT session_id, start_date, status
                    FROM shadow_trading_sessions
                    ORDER BY start_date DESC
                    LIMIT 5
                """))
                
                all_sessions = result.fetchall()
                if all_sessions:
                    print("\n📋 Recent Sessions:")
                    for s in all_sessions:
                        print(f"  {s[0]}: {s[1]} ({s[2]})")
                        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_shadow_trading())
