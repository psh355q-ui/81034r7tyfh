"""
Analyze actual DB structure to update schema JSONs
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

def get_table_structure(table_name):
    """Get complete table structure"""
    cursor.execute(f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    
    columns = []
    for row in cursor.fetchall():
        col = {
            'name': row[0],
            'type': row[1],
            'max_length': row[2],
            'nullable': row[3] == 'YES',
            'default': row[4]
        }
        columns.append(col)
    
    return columns

print("=" * 80)
print("ACTUAL DATABASE STRUCTURE")
print("=" * 80)

# news_articles
print("\n📋 NEWS_ARTICLES:")
print("-" * 80)
news_cols = get_table_structure('news_articles')
for col in news_cols:
    type_str = col['type']
    if col['max_length']:
        type_str += f"({col['max_length']})"
    null_str = "NULL" if col['nullable'] else "NOT NULL"
    default_str = f" DEFAULT {col['default']}" if col['default'] else ""
    print(f"{col['name']:30s} {type_str:30s} {null_str:10s}{default_str}")

# trading_signals
print("\n\n📋 TRADING_SIGNALS:")
print("-" * 80)
signal_cols = get_table_structure('trading_signals')
for col in signal_cols:
    type_str = col['type']
    if col['max_length']:
        type_str += f"({col['max_length']})"
    null_str = "NULL" if col['nullable'] else "NOT NULL"
    default_str = f" DEFAULT {col['default']}" if col['default'] else ""
    print(f"{col['name']:30s} {type_str:30s} {null_str:10s}{default_str}")

# data_collection_progress
print("\n\n📋 DATA_COLLECTION_PROGRESS:")
print("-" * 80)
progress_cols = get_table_structure('data_collection_progress')
for col in progress_cols:
    type_str = col['type']
    if col['max_length']:
        type_str += f"({col['max_length']})"
    null_str = "NULL" if col['nullable'] else "NOT NULL"
    default_str = f" DEFAULT {col['default']}" if col['default'] else ""
    print(f"{col['name']:30s} {type_str:30s} {null_str:10s}{default_str}")

conn.close()
print("\n" + "=" * 80)
