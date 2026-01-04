import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='shadow_trading_sessions' 
    ORDER BY ordinal_position
""")
print("shadow_trading_sessions columns:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='shadow_trading_positions' 
    ORDER BY ordinal_position
""")
print("\nshadow_trading_positions columns:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
