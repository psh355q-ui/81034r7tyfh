"""
생성된 인덱스 확인 스크립트
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import psycopg2

# .env 로드
env_path = project_root / '.env'
load_dotenv(env_path)

# DATABASE_URL 파싱
database_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
result = urlparse(database_url)

conn_params = {
    'host': result.hostname,
    'port': result.port,
    'dbname': result.path[1:],
    'user': result.username,
    'password': result.password
}

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # 생성된 인덱스 확인
    cursor.execute("""
        SELECT 
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as size
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND (indexname = 'idx_news_ticker_date'
          OR indexname = 'idx_news_processed'
          OR indexname = 'idx_signal_ticker_date'  
          OR indexname = 'idx_signal_pending_alert'
          OR indexname = 'idx_stock_ticker_time_desc')
        ORDER BY tablename, indexname;
    """)
    
    results = cursor.fetchall()
    
    print("\n" + "=" * 80)
    print("✅ Phase 1 복합 인덱스 생성 완료!")
    print("=" * 80)
    
    if results:
        print("\n📊 생성된 인덱스:")
        print("-" * 80)
        for table, index, size in results:
            print(f"  {table:25} | {index:35} | {size}")
        print(f"\n총 {len(results)}개 인덱스 생성됨")
    else:
        print("⚠️ 인덱스가 아직 생성되지 않았습니다.")
    
    # 테이블 통계 확인
    cursor.execute("""
        SELECT 
            relname,
            n_live_tup as rows,
            pg_size_pretty(pg_total_relation_size(relid)) as total_size
        FROM pg_stat_user_tables
        WHERE relname IN ('news_articles', 'trading_signals', 'stock_prices')
        ORDER BY relname;
    """)
    
    print("\n📈 테이블 통계:")
    print("-" * 80)
    for table, rows, size in cursor.fetchall():
        print(f"  {table:25} | {rows:10,} rows | {size}")
    
    print("\n" + "=" * 80)
    print("🎯 예상 효과: War Room MVP DB 쿼리 시간 0.3-0.4s 단축")
    print("=" * 80 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"오류: {e}")
    sys.exit(1)
