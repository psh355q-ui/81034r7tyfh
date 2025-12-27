"""
Analyze database structure for storage optimization
"""
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='ai_trading',
    user='postgres',
    password='Qkqhdi1!'
)
cursor = conn.cursor()

print("=" * 80)
print("DATABASE STORAGE ANALYSIS")
print("=" * 80)

# Table sizes
print("\n📊 TABLE SIZES:")
cursor.execute("""
    SELECT 
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
        pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN ('news_articles', 'trading_signals', 'stock_prices', 'data_collection_progress')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
""")
for row in cursor.fetchall():
    print(f"  {row[0]:30s} {row[1]:>15s} ({row[2]:,} bytes)")

# news_articles columns
print("\n\n📋 NEWS_ARTICLES COLUMNS:")
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'news_articles'
    ORDER BY ordinal_position;
""")
for row in cursor.fetchall():
    max_len = f" ({row[2]})" if row[2] else ""
    print(f"  {row[0]:30s} {row[1]}{max_len:20s} NULL={row[3]}")

# trading_signals columns
print("\n\n📋 TRADING_SIGNALS COLUMNS:")
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'trading_signals'
    ORDER BY ordinal_position;
""")
for row in cursor.fetchall():
    max_len = f" ({row[2]})" if row[2] else ""
    print(f"  {row[0]:30s} {row[1]}{max_len:20s} NULL={row[3]}")

# Count rows
print("\n\n📈 ROW COUNTS:")
for table in ['news_articles', 'trading_signals', 'stock_prices']:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"  {table:30s} {count:,} rows")

conn.close()
print("\n" + "=" * 80)
