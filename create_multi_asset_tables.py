"""
Create Multi-Asset Tables

Phase 30: Multi-Asset Support
Date: 2025-12-30

Creates 4 tables:
- assets
- multi_asset_positions
- asset_correlations
- asset_allocations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.models import Base
from backend.database.repository import engine
from backend.database.models_assets import (
    Asset,
    MultiAssetPosition,
    AssetCorrelation,
    AssetAllocation
)

def create_tables():
    """Create all multi-asset tables"""
    print("=" * 80)
    print("Creating Multi-Asset Tables")
    print("=" * 80)
    print()

    # Create tables
    try:
        print("Creating tables...")
        Base.metadata.create_all(
            bind=engine,
            tables=[
                Asset.__table__,
                MultiAssetPosition.__table__,
                AssetCorrelation.__table__,
                AssetAllocation.__table__
            ]
        )
        print("✅ All 4 tables created successfully")
        print()

        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)

        tables = [
            "assets",
            "multi_asset_positions",
            "asset_correlations",
            "asset_allocations"
        ]

        print("Verifying tables...")
        for table_name in tables:
            if inspector.has_table(table_name):
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                print(f"✅ {table_name}: {len(columns)} columns, {len(indexes)} indexes")
            else:
                print(f"❌ {table_name}: NOT FOUND")

        print()
        print("=" * 80)
        print("Table creation complete!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
