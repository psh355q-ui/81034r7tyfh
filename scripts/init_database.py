"""
Database Initialization Script

테이블 생성 및 TimescaleDB 설정:
- NewsArticle, AnalysisResult, TradingSignal
- BacktestRun, BacktestTrade
- SignalPerformance
- TimescaleDB hypertables (optional)

Usage:
    python scripts/init_database.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.models import (
    create_all_tables,
    setup_timescaledb_hypertables,
    Base
)
from backend.database.repository import engine
from sqlalchemy import text


def check_database_connection():
    """데이터베이스 연결 확인"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"[OK] Database connection successful")
            print(f"     PostgreSQL version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


def check_timescaledb_extension():
    """TimescaleDB extension 확인"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';"))
            if result.fetchone():
                print("[OK] TimescaleDB extension is installed")
                return True
            else:
                print("[WARNING] TimescaleDB extension not found")
                print("          Skipping hypertable creation")
                return False
    except Exception as e:
        print(f"[WARNING] Could not check TimescaleDB: {e}")
        return False


def list_existing_tables():
    """기존 테이블 목록 조회"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            return tables
    except Exception as e:
        print(f"[ERROR] Could not list tables: {e}")
        return []


def main():
    print("=" * 80)
    print("Database Initialization Script")
    print("=" * 80)

    # 1. Check connection
    print("\n[STEP 1] Checking database connection...")
    if not check_database_connection():
        print("\n[FAILED] Cannot connect to database")
        print("Please check:")
        print("  - DATABASE_URL environment variable")
        print("  - PostgreSQL service is running")
        print("  - Database exists and credentials are correct")
        sys.exit(1)

    # 2. List existing tables
    print("\n[STEP 2] Checking existing tables...")
    existing_tables = list_existing_tables()
    if existing_tables:
        print(f"[INFO] Found {len(existing_tables)} existing tables:")
        for table in existing_tables:
            print(f"  - {table}")

        # Warn if any of our tables exist
        our_tables = {'news_articles', 'analysis_results', 'trading_signals',
                      'backtest_runs', 'backtest_trades', 'signal_performance'}
        existing_our_tables = set(existing_tables) & our_tables

        if existing_our_tables:
            print(f"\n[WARNING] The following tables already exist:")
            for table in existing_our_tables:
                print(f"  - {table}")

            response = input("\nDo you want to recreate them? (y/N): ")
            if response.lower() != 'y':
                print("\n[CANCELLED] Database initialization cancelled")
                sys.exit(0)

            print("\n[INFO] Dropping existing tables...")
            from backend.database.models import drop_all_tables
            drop_all_tables(engine)
            print("[OK] Existing tables dropped")
    else:
        print("[INFO] No existing tables found")

    # 3. Create tables
    print("\n[STEP 3] Creating tables...")
    try:
        create_all_tables(engine)
        print("[OK] All tables created successfully")

        # List created tables
        new_tables = list_existing_tables()
        print(f"\n[INFO] Created {len(new_tables)} tables:")
        for table in new_tables:
            print(f"  - {table}")

    except Exception as e:
        print(f"[ERROR] Table creation failed: {e}")
        sys.exit(1)

    # 4. Setup TimescaleDB (optional)
    print("\n[STEP 4] Setting up TimescaleDB (optional)...")
    has_timescaledb = check_timescaledb_extension()

    if has_timescaledb:
        try:
            with engine.connect() as conn:
                setup_timescaledb_hypertables(conn)
            print("[OK] TimescaleDB hypertables created")
        except Exception as e:
            print(f"[WARNING] TimescaleDB setup failed: {e}")
            print("          Continuing without hypertables (not critical)")
    else:
        print("[SKIP] TimescaleDB not available, using regular tables")

    # 5. Verify tables
    print("\n[STEP 5] Verifying table schema...")
    try:
        with engine.connect() as conn:
            # Check each table has expected columns
            tables_to_check = [
                ('news_articles', ['id', 'title', 'content', 'url', 'source', 'published_date', 'content_hash']),
                ('analysis_results', ['id', 'article_id', 'theme', 'bull_case', 'bear_case']),
                ('trading_signals', ['id', 'analysis_id', 'ticker', 'action', 'signal_type', 'confidence']),
                ('backtest_runs', ['id', 'strategy_name', 'total_trades', 'win_rate', 'sharpe_ratio']),
                ('signal_performance', ['id', 'signal_id', 'actual_return_pct', 'outcome'])
            ]

            for table_name, expected_columns in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))
                columns = [row[0] for row in result.fetchall()]

                missing = set(expected_columns) - set(columns)
                if missing:
                    print(f"[WARNING] Table '{table_name}' missing columns: {missing}")
                else:
                    print(f"[OK] Table '{table_name}' has all expected columns ({len(columns)} total)")

    except Exception as e:
        print(f"[WARNING] Could not verify schema: {e}")

    # 6. Summary
    print("\n" + "=" * 80)
    print("INITIALIZATION COMPLETE")
    print("=" * 80)
    print("\nDatabase is ready to use!")
    print("\nNext steps:")
    print("  1. Run RSS crawler: python scripts/test_rss_crawler.py")
    print("  2. Test database integration: python scripts/test_db_integration.py")
    print("  3. Start monitoring: python scripts/run_monitoring.py")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
