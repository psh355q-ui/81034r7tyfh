"""
Add v2.2 Caching Fields Migration

Adds caching fields to daily_briefings and creates weekly_reports table.

Usage:
    python backend/database/migrations/add_v2_2_caching_fields.py
"""

import asyncio
import logging
from sqlalchemy import text

from backend.database.db_service import get_db_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_caching_fields():
    """
    Add caching fields to daily_briefings table
    """
    try:
        db_service = await get_db_service()
        
        async with db_service.get_session() as session:
            # 캐싱 필드 추가
            alter_table_sql = """
            ALTER TABLE daily_briefings
            ADD COLUMN IF NOT EXISTS cache_key VARCHAR(200),
            ADD COLUMN IF NOT EXISTS cache_hit BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS cache_ttl INTEGER DEFAULT 86400,
            ADD COLUMN IF NOT EXISTS importance_score INTEGER,
            ADD COLUMN IF NOT EXISTS economic_events_count INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS sector_rotation_score FLOAT;
            """
            
            await session.execute(text(alter_table_sql))
            logger.info("✓ Added caching fields to daily_briefings table")
            
            # 인덱스 생성
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_daily_briefing_cache_key ON daily_briefings (cache_key);",
                "CREATE INDEX IF NOT EXISTS idx_daily_briefing_cache_hit ON daily_briefings (cache_hit);",
            ]
            
            for index_sql in create_indexes_sql:
                await session.execute(text(index_sql))
            
            logger.info("✓ Created indexes for daily_briefings caching fields")
            
            logger.info("✓ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error adding caching fields: {e}")
        raise


async def create_weekly_reports_table():
    """
    Create weekly_reports table
    """
    try:
        db_service = await get_db_service()
        
        async with db_service.get_session() as session:
            # 테이블 생성 SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS weekly_reports (
                id SERIAL PRIMARY KEY,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                content TEXT NOT NULL,
                metrics JSONB,
                cache_key VARCHAR(200),
                cache_hit BOOLEAN DEFAULT FALSE,
                cache_ttl INTEGER DEFAULT 604800,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # 인덱스 생성
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_weekly_report_week_start ON weekly_reports (week_start);",
                "CREATE INDEX IF NOT EXISTS idx_weekly_report_week_end ON weekly_reports (week_end);",
                "CREATE INDEX IF NOT EXISTS idx_weekly_report_cache_key ON weekly_reports (cache_key);",
                "CREATE INDEX IF NOT EXISTS idx_weekly_report_cache_hit ON weekly_reports (cache_hit);",
            ]
            
            # 테이블 생성
            await session.execute(text(create_table_sql))
            logger.info("✓ Created weekly_reports table")
            
            # 인덱스 생성
            for index_sql in create_indexes_sql:
                await session.execute(text(index_sql))
            
            logger.info("✓ Created indexes for weekly_reports table")
            
            logger.info("✓ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error creating weekly_reports table: {e}")
        raise


async def main():
    """Main function"""
    print("=" * 60)
    print("Adding v2.2 Caching Fields")
    print("=" * 60)
    print()
    
    # 캐싱 필드 추가
    print("1. Adding caching fields to daily_briefings...")
    await add_caching_fields()
    print()
    
    # weekly_reports 테이블 생성
    print("2. Creating weekly_reports table...")
    await create_weekly_reports_table()
    print()
    
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
