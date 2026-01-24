"""
Drop and Recreate Economic Events Table

Drops existing economic_events table and recreates it with updated schema.

Usage:
    python backend/database/migrations/drop_and_recreate_economic_events_table.py
"""

import asyncio
import logging
from sqlalchemy import text

from backend.database.db_service import get_db_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def drop_and_recreate_table():
    """
    Drop and recreate economic_events table
    """
    try:
        db_service = await get_db_service()
        
        async with db_service.get_session() as session:
            # 테이블 삭제
            drop_table_sql = "DROP TABLE IF EXISTS economic_events CASCADE;"
            await session.execute(text(drop_table_sql))
            logger.info("✓ Dropped economic_events table")
            
            # 테이블 생성 SQL
            create_table_sql = """
            CREATE TABLE economic_events (
                id SERIAL PRIMARY KEY,
                event_name VARCHAR(200) NOT NULL,
                country VARCHAR(10) NOT NULL,
                category VARCHAR(50) NOT NULL,
                event_time TIMESTAMP NOT NULL,
                importance INTEGER NOT NULL,
                forecast VARCHAR(50),
                actual VARCHAR(50),
                previous VARCHAR(50),
                surprise_pct FLOAT,
                impact_direction VARCHAR(20),
                impact_score INTEGER,
                is_processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                notes TEXT,
                updated_at TIMESTAMP
            );
            """
            
            # 인덱스 생성
            create_indexes_sql = [
                "CREATE INDEX idx_economic_event_time ON economic_events (event_time);",
                "CREATE INDEX idx_economic_importance ON economic_events (importance);",
                "CREATE INDEX idx_economic_processed ON economic_events (is_processed);",
            ]
            
            # 테이블 생성
            await session.execute(text(create_table_sql))
            logger.info("✓ Created economic_events table")
            
            # 인덱스 생성
            for index_sql in create_indexes_sql:
                await session.execute(text(index_sql))
            
            logger.info("✓ Created indexes for economic_events table")
            
            logger.info("✓ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error recreating economic_events table: {e}")
        raise


async def main():
    """Main function"""
    print("=" * 60)
    print("Dropping and recreating economic_events table")
    print("=" * 60)
    print()
    
    await drop_and_recreate_table()
    
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
