"""
.env 설정 테스트 스크립트
모든 agent와 서비스가 새 DB 설정을 제대로 읽는지 확인
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
import os
import asyncio
import asyncpg

# .env 로드
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

print("=" * 70)
print("  .env 설정 테스트")
print("=" * 70)
print()

# 1. 환경변수 확인
print("📋 환경변수 읽기:")
print(f"  DB_HOST: {os.getenv('DB_HOST')}")
print(f"  DB_PORT: {os.getenv('DB_PORT')}")
print(f"  DB_NAME: {os.getenv('DB_NAME')}")
print(f"  DB_USER: {os.getenv('DB_USER')}")
print(f"  DB_PASSWORD: {'(설정됨)' if os.getenv('DB_PASSWORD') else '(비어있음)'}")
print(f"  DATABASE_URL: {os.getenv('DATABASE_URL', '').split('@')[0]}@...")
print()

# 2. asyncpg로 연결 테스트
async def test_connection():
    try:
        print("🔌 DB 연결 테스트 (asyncpg)...")
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ai_trading'),
            user=os.getenv('DB_USER', 'ai_trading_user'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        # 버전 확인
        version = await conn.fetchval('SELECT version()')
        print(f"  ✅ 연결 성공!")
        print(f"  PostgreSQL: {version[:80]}")
        
        # data_collection_progress 테이블 확인
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'data_collection_progress'"
        )
        if result:
            print(f"  ✅ data_collection_progress 테이블 존재")
        else:
            print(f"  ⚠️  data_collection_progress 테이블 없음")
        
        # extension 확인
        extensions = await conn.fetch("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'timescaledb')")
        if extensions:
            print(f"  ✅ Extensions: {[e['extname'] for e in extensions]}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ 연결 실패: {e}")
        return False

# 3. SQLAlchemy로 연결 테스트 (backend 코드가 사용하는 방식)
def test_sqlalchemy():
    try:
        print("\n🔌 DB 연결 테스트 (SQLAlchemy)...")
        from sqlalchemy import create_engine, text
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', 5432)
            db_name = os.getenv('DB_NAME', 'ai_trading')
            db_user = os.getenv('DB_USER', 'ai_trading_user')
            db_pass = os.getenv('DB_PASSWORD', '')
            # SQLAlchemy는 postgresql:// (asyncpg가 아님)
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            # asyncpg를 psycopg2로 변경
            db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  ✅ SQLAlchemy 연결 성공!")
            print(f"  PostgreSQL: {version[:80]}")
            
            # 테이블 확인
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' LIMIT 5"))
            tables = [row[0] for row in result]
            print(f"  ✅ 테이블: {tables}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ SQLAlchemy 연결 실패: {e}")
        return False

# 실행
if __name__ == "__main__":
    print("테스트 시작...\n")
    
    # asyncpg 테스트
    success1 = asyncio.run(test_connection())
    
    # SQLAlchemy 테스트
    success2 = test_sqlalchemy()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("✅ 모든 연결 테스트 통과!")
        print("\n다음 단계:")
        print("  1. 백엔드 서버 재시작")
        print("  2. 프론트엔드에서 뉴스 백필 테스트")
    else:
        print("❌ 일부 테스트 실패 - .env 설정을 다시 확인하세요")
    print("=" * 70)
