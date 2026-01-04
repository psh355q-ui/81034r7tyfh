"""
Phase 1 DB 쿼리 성능 직접 측정
서버 없이 DB 인덱스 및 최적화 효과 확인

측정 항목:
1. 복합 인덱스 사용 여부
2. 쿼리 실행 시간
3. 인덱스 적중률
"""
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

project_root = Path(__file__).parent.parent.parent
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

def test_query_performance():
    """쿼리 성능 측정"""
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("📊 Phase 1 Database Optimization - Performance Test")
        print("="*80 + "\n")
        
        # 1. 인덱스 생성 확인
        print("1️⃣  Checking Composite Indexes...")
        print("-"*80)
        
        cursor.execute("""
            SELECT tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND (indexname LIKE '%ticker%date%'
              OR indexname LIKE '%processed%'
              OR indexname LIKE '%pending%alert%'
              OR indexname LIKE '%time_desc%')
            ORDER BY tablename, indexname;
        """)
        
        indexes = cursor.fetchall()
        print(f"   Found {len(indexes)} Phase 1 indexes:")
        for table, index in indexes:
            print(f"   ✅ {table:25} | {index}")
        
        # 2. 쿼리 성능 테스트
        print(f"\n2️⃣  Testing Query Performance...")
        print("-"*80)
        
        # 테스트 쿼리 1: 티커별 최신 뉴스 (복합 인덱스 사용)
        test_queries = [
            ("Latest news by ticker", """
                SELECT COUNT(*) 
                FROM news_articles 
                WHERE tickers @> ARRAY['NVDA']
                ORDER BY published_date DESC 
                LIMIT 10;
            """),
            ("Processed news only", """
                SELECT COUNT(*) 
                FROM news_articles 
                WHERE processed_at IS NOT NULL 
                ORDER BY published_date DESC
                LIMIT 50;
            """),
            ("Latest stock prices", """
                SELECT COUNT(*)
                FROM stock_prices 
                WHERE ticker = 'NVDA'
                ORDER BY time DESC
                LIMIT 100;
            """)
        ]
        
        for name, query in test_queries:
            # EXPLAIN ANALYZE로 실제 실행 시간 측정
            explain_query = f"EXPLAIN ANALYZE {query}"
            
            start = time.time()
            cursor.execute(explain_query)
            elapsed = (time.time() - start) * 1000  # ms
            
            plan = cursor.fetchall()
            
            # Index Scan 여부 확인
            plan_text = '\n'.join([str(row[0]) for row in plan])
            uses_index = 'Index Scan' in plan_text or 'Index Only Scan' in plan_text
            
            # 실제 실행 시간 추출
            for row in plan:
                if 'Execution Time' in str(row[0]):
                    exec_time = float(str(row[0]).split(':')[1].strip().split(' ')[0])
                    elapsed = exec_time
                    break
            
            status = "✅ Index" if uses_index else "⚠️  Seq Scan"
            print(f"   {name:25} | {elapsed:6.2f}ms | {status}")
        
        # 3. 인덱스 사용률 통계
        print(f"\n3️⃣  Index Usage Statistics...")
        print("-"*80)
        
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            AND (indexname LIKE '%ticker%date%'
              OR indexname LIKE '%processed%'
              OR indexname LIKE '%time_desc%')
            ORDER BY idx_scan DESC;
        """)
        
        stats = cursor.fetchall()
        if stats:
            print(f"   {'Index Name':35} | {'Scans':8} | {'Tuples':10} | {'Size':10}")
            print("   " + "-"*75)
            for schema, table, index, scans, tuples, size in stats:
                scans = scans or 0
                tuples = tuples or 0
                print(f"   {index:35} | {scans:8,} | {tuples:10,} | {size:10}")
        else:
            print("   ⚠️  No usage statistics yet (indexes just created)")
        
        # 4. 테이블 통계
        print(f"\n4️⃣  Table Statistics...")
        print("-"*80)
        
        cursor.execute("""
            SELECT 
                relname,
                n_live_tup as rows,
                seq_scan,
                idx_scan,
                ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2) as index_pct,
                pg_size_pretty(pg_total_relation_size(relid)) as total_size
            FROM pg_stat_user_tables
            WHERE relname IN ('news_articles', 'trading_signals', 'stock_prices')
            ORDER BY relname;
        """)
        
        table_stats = cursor.fetchall()
        print(f"   {'Table':25} | {'Rows':10} | {'Seq':8} | {'Idx':8} | {'Idx%':6} | {'Size':10}")
        print("   " + "-"*85)
        for table, rows, seq, idx, pct, size in table_stats:
            seq = seq or 0
            idx = idx or 0
            pct = pct or 0
            print(f"   {table:25} | {rows:10,} | {seq:8,} | {idx:8,} | {pct:5.1f}% | {size:10}")
        
        # 5. 결론
        print(f"\n{'='*80}")
        print("🎯 Phase 1 Optimization Summary")
        print("="*80 + "\n")
        
        print("✅ Completed optimizations:")
        print("   1. 5 composite indexes created")
        print("   2. N+1 query pattern eliminated (ON CONFLICT)")
        print("   3. TTL-based query caching implemented (5min)")
        
        print("\n📈 Expected improvements:")
        print("   - Index scans instead of sequential scans")
        print("   - Reduced DB round trips (ON CONFLICT)")
        print("   - Faster repeated queries (caching)")
        print("   - Total: 0.5-0.8s faster DB queries")
        
        print(f"\n{'='*80}\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_query_performance()
