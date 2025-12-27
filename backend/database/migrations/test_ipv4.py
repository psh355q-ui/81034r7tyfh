"""
Test with explicit 127.0.0.1 instead of localhost
"""
import psycopg2

print("Testing connection with 127.0.0.1...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',  # IPv4 explicitly
        port=5432,
        database='ai_trading',
        user='ai_trading_user',
        password='Qkqhdi1!'
    )
    print("✅ Connection successful with 127.0.0.1!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0][:80]}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
