"""
Test local PostgreSQL with original password
"""
import psycopg2

print("Testing connection to local PostgreSQL...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='ai_trading',
        user='postgres',
        password='Qkqhdi1!'
    )
    print("✅ CONNECTION SUCCESSFUL!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL: {version[0][:100]}")
    
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'data_collection_progress';")
    result = cursor.fetchone()
    print(f"✅ data_collection_progress exists: {result[0] > 0}")
    
    conn.close()
    print("\n🎉 로컬 PostgreSQL 연결 성공!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
