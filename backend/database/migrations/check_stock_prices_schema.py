"""
Check stock_prices table schema
"""
import psycopg2

print("Checking stock_prices table schema...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='ai_trading',
        user='postgres',
        password='Qkqhdi1!'
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'stock_prices'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    
    if columns:
        print("\n✅ stock_prices table columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    else:
        print("❌ stock_prices table does not exist or has no columns")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
