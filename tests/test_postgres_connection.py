"""
PostgreSQL 연결 테스트

실행: python test_postgres_connection.py
목적: DATABASE_URL이 올바르게 설정되었는지 확인
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
load_dotenv()

print("\n" + "="*70)
print(" "*20 + "🔍 PostgreSQL 연결 테스트")
print("="*70 + "\n")

# 1. DATABASE_URL 확인
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL이 .env에 없습니다!")
    print("\n.env 파일에 추가하세요:")
    print("DATABASE_URL=postgresql://postgres:비밀번호@localhost:5432/ai_trading")
    sys.exit(1)

# URL 파싱 (비밀번호 숨김)
if '://' in db_url:
    parts = db_url.split('://')
    if '@' in parts[1]:
        user_pass, host_db = parts[1].split('@')
        user = user_pass.split(':')[0]
        password = '***'
        display_url = f"{parts[0]}://{user}:{password}@{host_db}"
    else:
        display_url = db_url
else:
    display_url = db_url

print(f"DATABASE_URL: {display_url}\n")

# 2. psycopg2 확인
print("1️⃣ psycopg2 라이브러리 확인...")
try:
    import psycopg2
    print("   ✅ psycopg2 설치됨\n")
except ImportError:
    print("   ❌ psycopg2가 설치되지 않았습니다!")
    print("\n설치:")
    print("   pip install psycopg2-binary")
    sys.exit(1)

# 3. PostgreSQL 연결 테스트
print("2️⃣ PostgreSQL 서버 연결 테스트...")
try:
    # DATABASE_URL 파싱
    from urllib.parse import urlparse
    
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]  # Remove leading '/'
    hostname = result.hostname
    port = result.port
    
    # 연결 시도
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        database=database,
        user=username,
        password=password
    )
    
    print(f"   ✅ PostgreSQL 연결 성공!")
    print(f"   서버: {hostname}:{port}")
    print(f"   데이터베이스: {database}\n")
    
    # 4. 테이블 확인
    print("3️⃣ 테이블 목록 확인...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    if tables:
        print("   발견된 테이블:")
        for table in tables:
            print(f"     • {table[0]}")
        print()
    else:
        print("   ⚠️ 테이블이 없습니다.")
        print("   → Alembic 마이그레이션이 필요합니다!\n")
        print("   실행:")
        print("     cd backend")
        print("     alembic upgrade head\n")
    
    # 기대하는 테이블 확인
    print("4️⃣ 필수 테이블 확인...")
    expected_tables = ['proposals', 'shadow_trades', 'alembic_version']
    table_names = [t[0] for t in tables]
    
    all_present = True
    for expected in expected_tables:
        if expected in table_names:
            print(f"   ✅ {expected}")
        else:
            print(f"   ❌ {expected} (없음)")
            all_present = False
    
    if not all_present:
        print("\n   ⚠️ 일부 테이블이 없습니다.")
        print("   → Alembic 마이그레이션을 실행하세요:")
        print("     cd backend")
        print("     alembic upgrade head")
    else:
        print("\n   🎉 모든 테이블이 준비되었습니다!")
    
    # 연결 종료
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ PostgreSQL 설정 완료!")
    print("="*70)
    
    if all_present:
        print("\n🚀 이제 사용 가능:")
        print("  • Commander Mode (Telegram 승인/거부)")
        print("  • Shadow Trade 추적 (DB 저장)")
        print("  • 히스토리 관리 (모든 제안 기록)")
    else:
        print("\n📝 다음 단계:")
        print("  cd backend")
        print("  alembic upgrade head")
    
    print()
    
except psycopg2.OperationalError as e:
    print(f"   ❌ 연결 실패!")
    print(f"\n오류: {e}\n")
    print("해결 방법:")
    print("  1. PostgreSQL 서비스가 실행 중인지 확인")
    print("     → 작업 관리자 → 서비스 → postgresql")
    print("  2. 비밀번호가 올바른지 확인")
    print("  3. 데이터베이스 'ai_trading'이 생성되었는지 확인")
    print("     → SQL Shell에서: CREATE DATABASE ai_trading;")
    print()
    sys.exit(1)

except Exception as e:
    print(f"   ❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
