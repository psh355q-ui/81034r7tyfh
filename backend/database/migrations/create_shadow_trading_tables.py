"""
Shadow Trading Tables Migration

Purpose: Shadow Trading 데이터 영속성을 위한 DB 스키마 생성
Date: 2025-12-31

Tables:
    1. shadow_trading_sessions - Shadow Trading 세션 정보
    2. shadow_trades - Shadow Trade 거래 기록
"""

from sqlalchemy import create_engine, text
import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"✓ Loaded .env from: {env_path}")

def get_db_url():
    """DB 연결 문자열 가져오기"""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ai_trading')
    # Convert asyncpg to psycopg2 for sync migration
    if 'postgresql+asyncpg://' in db_url:
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    return db_url

def run_migration():
    """Shadow Trading tables migration 실행"""
    engine = create_engine(get_db_url())

    print("="*80)
    print("Shadow Trading Tables Migration")
    print("="*80)
    print()

    with engine.connect() as conn:
        try:
            # 1. shadow_trading_sessions 테이블 생성
            print("1. Creating shadow_trading_sessions table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS shadow_trading_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    status VARCHAR(20) NOT NULL,  -- active, paused, completed, failed
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    initial_capital FLOAT NOT NULL,
                    current_capital FLOAT NOT NULL,
                    available_cash FLOAT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("   ✅ shadow_trading_sessions table created/verified")

            # 2. shadow_trades 테이블 생성
            print("\n2. Creating shadow_trades table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS shadow_trades (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) NOT NULL,
                    trade_id VARCHAR(100) UNIQUE NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    action VARCHAR(10) NOT NULL,  -- buy, sell
                    quantity INTEGER NOT NULL,
                    entry_price FLOAT NOT NULL,
                    entry_date TIMESTAMP NOT NULL,
                    exit_price FLOAT,
                    exit_date TIMESTAMP,
                    pnl FLOAT,
                    pnl_pct FLOAT,
                    stop_loss_price FLOAT,
                    reason TEXT,
                    agent_decision JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (session_id) REFERENCES shadow_trading_sessions(session_id)
                )
            """))
            conn.commit()
            print("   ✅ shadow_trades table created/verified")

            # 3. 인덱스 생성
            print("\n3. Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shadow_sessions_status
                ON shadow_trading_sessions(status)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shadow_sessions_start_date
                ON shadow_trading_sessions(start_date)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shadow_trades_session
                ON shadow_trades(session_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shadow_trades_symbol
                ON shadow_trades(symbol)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shadow_trades_entry_date
                ON shadow_trades(entry_date)
            """))
            conn.commit()
            print("   ✅ Indexes created")

            # 4. 검증
            print("\n4. Verifying schema...")
            result = conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_name IN ('shadow_trading_sessions', 'shadow_trades')
                ORDER BY table_name, ordinal_position
            """))

            columns = result.fetchall()
            print("\n   Verified columns:")
            current_table = None
            for col in columns:
                if col[0] != current_table:
                    current_table = col[0]
                    print(f"\n   Table: {current_table}")
                print(f"     - {col[1]:25} {col[2]}")

            print("\n" + "="*80)
            print("✅ Migration completed successfully!")
            print("="*80)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()
