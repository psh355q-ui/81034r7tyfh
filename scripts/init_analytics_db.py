"""
Initialize database schema for Advanced Analytics
"""
import asyncio
import os
from sqlalchemy import inspect
from backend.core.database import engine, Base
from backend.core.models.analytics_models import (
    DailyAnalytics,
    WeeklyAnalytics,
    MonthlyAnalytics,
    TradeExecution,
    PortfolioSnapshot,
    SignalPerformance,
)

async def init_db():
    """Create all tables for analytics"""
    print("Initializing database schema...")

    async with engine.begin() as conn:
        # Drop all tables (optional - comment out if you want to keep existing data)
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Check what tables were created
        def get_tables(conn):
            inspector = inspect(conn)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        print(f"\n✓ Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")

    print("\n✓ Database schema initialized successfully!")

if __name__ == "__main__":
    # Set DATABASE_URL if not already set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5432/ai_trading"
        print(f"Using DATABASE_URL: {os.environ['DATABASE_URL']}")

    asyncio.run(init_db())
