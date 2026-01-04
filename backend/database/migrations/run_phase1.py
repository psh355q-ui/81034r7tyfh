"""
간단한 마이그레이션 실행 스크립트
포트 5433, .env 파일에서 패스워드 로드
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
# migrations/run_phase1.py -> migrations -> database -> backend -> project_root
project_root = Path(__file__).parent.parent.parent.parent  # 수정: 4단계 위로
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    import psycopg2
except ImportError as e:
    print(f"❌ 필요한 패키지를 설치하세요: pip install psycopg2-binary python-dotenv")
    sys.exit(1)

# .env 로드
env_path = project_root / '.env'
print(f"🔍 프로젝트 루트: {project_root}")
print(f"🔍 .env 파일 경로: {env_path}")
print(f"🔍 .env 파일 존재: {env_path.exists()}")

load_dotenv(env_path)

# DATABASE_URL 파싱
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ .env 파일에 DATABASE_URL이 없습니다.")
    print("   예: DATABASE_URL=postgresql://user:password@localhost:5433/ai_trading_dev")
    sys.exit(1)

# asyncpg 제거 (psycopg2 호환)
if '+asyncpg' in database_url:
    database_url = database_url.replace('+asyncpg', '')
    print("🔄 asyncpg 제거: psycopg2 호환 모드")

# URL 파싱 (postgresql://user:password@host:port/database)
try:
    from urllib.parse import urlparse
    result = urlparse(database_url)
    
    conn_params = {
        'host': result.hostname or 'localhost',
        'port': result.port or 5432,
        'dbname': result.path[1:] if result.path else 'ai_trading_dev',  # '/' 제거
        'user': result.username or 'postgres',
        'password': result.password or ''
    }
except Exception as e:
    print(f"❌ DATABASE_URL 파싱 실패: {e}")
    print(f"   DATABASE_URL: {database_url}")
    sys.exit(1)

migration_file = Path(__file__).parent / '20260102_add_composite_indexes.sql'

print(f"🔌 연결 시도: {conn_params['dbname']}@{conn_params['host']}:{conn_params['port']}")
print(f"👤 사용자: {conn_params['user']}")

try:
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ 연결 성공!")
    print(f"📄 마이그레이션 파일: {migration_file.name}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("\n🔨 인덱스 생성 중...")
    cursor.execute(sql)
    
    print("✅ 마이그레이션 완료!")
    
    # 생성된 인덱스 확인
    cursor.execute("""
        SELECT tablename, indexname, 
               pg_size_pretty(pg_relation_size(indexname::regclass)) as size
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND (indexname LIKE 'idx_news_ticker_date'
          OR indexname LIKE 'idx_news_processed'
          OR indexname LIKE 'idx_signal_ticker_date'  
          OR indexname LIKE 'idx_signal_pending_alert'
          OR indexname LIKE 'idx_stock_ticker_time_desc')
        ORDER BY tablename;
    """)
    
    print("\n📊 생성된 인덱스:")
    print("-" * 70)
    for table, index, size in cursor.fetchall():
        print(f"  {table:20} | {index:35} | {size}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Phase 1 최적화 완료!")
    print("   War Room MVP 성능 향상 예상: DB 쿼리 0.3-0.4s 단축")
    
except psycopg2.Error as e:
    print(f"\n❌ DB 오류: {e}")
    print("\n💡 해결 방법:")
    print("  1. PostgreSQL이 5433 포트에서 실행 중인지 확인")
    print("  2. .env 파일의 DB_PASSWORD 확인")
    print("  3. 수동 실행: psql -h localhost -p 5433 -U postgres -d ai_trading_dev")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 오류: {e}")
    sys.exit(1)
