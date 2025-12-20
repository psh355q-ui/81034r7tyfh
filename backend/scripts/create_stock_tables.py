"""
Create missing tables for stock prices.

Run this to fix 500 errors on /api/stock-prices/* endpoints.

Usage:
    cd D:\code\ai-trading-system
    python -m backend.scripts.create_stock_tables
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.core.database import AsyncSessionLocal


async def create_tables():
    """Create stock_prices and price_sync_status tables."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Create stock_prices table (TimescaleDB hypertable compatible)
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    time TIMESTAMPTZ NOT NULL,
                    ticker VARCHAR(20) NOT NULL,
                    open DECIMAL(12, 4),
                    high DECIMAL(12, 4),
                    low DECIMAL(12, 4),
                    close DECIMAL(12, 4),
                    volume BIGINT,
                    adjusted_close DECIMAL(12, 4),
                    PRIMARY KEY (time, ticker)
                )
            """))
            
            # Create index
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker 
                ON stock_prices (ticker)
            """))
            
            # Create price_sync_status table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS price_sync_status (
                    ticker VARCHAR(20) PRIMARY KEY,
                    last_sync_date DATE NOT NULL,
                    last_price_date DATE NOT NULL,
                    total_rows INTEGER DEFAULT 0,
                    first_sync_date DATE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            
            await db.commit()
            print("✅ Tables created successfully!")
            print("   - stock_prices")
            print("   - price_sync_status")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(create_tables())
