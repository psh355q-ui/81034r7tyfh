import asyncio
import asyncpg
from datetime import datetime

async def check():
    conn = await asyncpg.connect('postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading')
    
    ts = await conn.fetch('SELECT * FROM trading_signals ORDER BY id LIMIT 11')
    
    print("5541 trading_signals:")
    for t in ts:
        print(f"ID {t['id']}: {t['ticker']} {t['action']} - confidence {t['confidence']:.2f}")
        if t['generated_at']:
            print(f"  Date: {t['generated_at']}")
    
    await conn.close()

asyncio.run(check())
