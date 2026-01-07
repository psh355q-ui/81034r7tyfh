
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data.news_models import engine
from backend.database.models import Base, TradingSignal, Order

def fix_tables():
    print(f"Creating missing tables in SQLite DB: {engine.url}")
    
    # Create tables defined in backend.database.models within the SQLite engine
    # This includes TradingSignal and Order which are missing
    try:
        filtered_metadata = Base.metadata
        # Filter for specific tables we need in SQLite
        # This avoids errors with PostgreSQL-specific types (JSONB, Vector) in other tables
        target_tables = [
            Base.metadata.tables['trading_signals'],
            Base.metadata.tables['orders']
        ]
        
        Base.metadata.create_all(bind=engine, tables=target_tables)
        print("✅ Successfully created tables (TradingSignal, Order) in SQLite.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    fix_tables()
