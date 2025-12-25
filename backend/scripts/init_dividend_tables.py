"""
Dividend Database Initialization Script

배당 관련 테이블을 PostgreSQL에 생성합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from backend.core.models.dividend_models import Base, create_tables
import asyncpg
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# DB 설정
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('DB_NAME', 'trading_db')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def init_dividend_tables():
    """배당 테이블 초기화"""
    
    print("=" * 60)
    print("Dividend Tables Initialization")
    print("=" * 60)
    print(f"Database: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print()
    
    try:
        # SQLAlchemy 엔진 생성
        engine = create_engine(DATABASE_URL, echo=True)
        
        # 테이블 생성
        print("Creating tables...")
        create_tables(engine)
        
        print()
        print("=" * 60)
        print("✅ Dividend tables created successfully!")
        print("=" * 60)
        print()
        print("Created tables:")
        print("  - dividend_history")
        print("  - dividend_snapshot")
        print("  - dividend_aristocrats")
        print()
        
        # 테이블 확인
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # 테이블 목록 조회
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'dividend%'
            ORDER BY table_name
        """)
        
        print("Verified tables in database:")
        for table in tables:
            print(f"  ✓ {table['table_name']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_dividend_tables())
