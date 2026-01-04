"""
Shadow Trading 테이블 마이그레이션 실행 스크립트
"""
import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# .env 로드
load_dotenv()

# DB 연결
db_url = os.getenv('DATABASE_URL')
if not db_url:
    raise ValueError("DATABASE_URL not found in .env")

# asyncpg → psycopg2 변환
if 'postgresql+asyncpg://' in db_url:
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"📊 Connecting to database...")
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# SQL 파일 로드 및 실행
migration_dir = Path(__file__).parent
sql_files = [
    'create_shadow_trading_sessions.sql',
    'create_shadow_trading_positions.sql'
]

try:
    for sql_file in sql_files:
        filepath = migration_dir / sql_file
        print(f"\n📝 Executing: {sql_file}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cursor.execute(sql)
        conn.commit()
        print(f"✅ Success: {sql_file}")
    
    # 테이블 확인
    print("\n📋 Verifying tables...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE 'shadow_trading%'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    if tables:
        print("\n✅ Created tables:")
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("\n⚠️  No tables found!")
    
    print("\n🎉 Migration completed successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()
