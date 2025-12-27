"""
Test connection with Qkqhdi1 (no exclamation mark)
"""
import psycopg2

print("Testing connection...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='ai_trading',
        user='ai_trading_user',
        password='Qkqhdi1'  # No exclamation mark
    )
    print("✅ CONNECTION SUCCESSFUL!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0][:100]}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
