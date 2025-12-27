"""
Test with simple password
"""
import psycopg2

print("Testing connection with simple password...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='ai_trading',
        user='ai_trading_user',
        password='simplepass123'
    )
    print("✅ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0][:80]}")
    
    # Test table
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'data_collection_progress';")
    result = cursor.fetchone()
    print(f"data_collection_progress table exists: {result[0] > 0}")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
