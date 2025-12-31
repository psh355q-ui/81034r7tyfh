"""
Verify Multi-Asset Data

Phase 30: Multi-Asset Support
Date: 2025-12-30

Verify all assets are properly stored in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.repository import SessionLocal
from backend.database.models_assets import Asset, MultiAssetPosition, AssetCorrelation, AssetAllocation
from sqlalchemy import func

def verify_data():
    """Verify multi-asset data in database"""
    print("=" * 80)
    print("Multi-Asset Data Verification")
    print("=" * 80)
    print()

    session = SessionLocal()

    try:
        # 1. Count assets by class
        print("1️⃣ Assets by Class:")
        print("-" * 80)

        asset_counts = (
            session.query(Asset.asset_class, func.count(Asset.id))
            .group_by(Asset.asset_class)
            .order_by(Asset.asset_class)
            .all()
        )

        total = 0
        for asset_class, count in asset_counts:
            print(f"  {asset_class:12s}: {count:3d} assets")
            total += count

        print(f"  {'TOTAL':12s}: {total:3d} assets")
        print()

        # 2. Sample assets from each class
        print("2️⃣ Sample Assets:")
        print("-" * 80)

        for asset_class, _ in asset_counts:
            assets = (
                session.query(Asset)
                .filter(Asset.asset_class == asset_class)
                .limit(3)
                .all()
            )

            print(f"\n{asset_class}:")
            for asset in assets:
                risk = asset.risk_level
                corr = f"{asset.correlation_to_sp500:.2f}" if asset.correlation_to_sp500 else "N/A"
                print(f"  {asset.symbol:10s} - {asset.name:30s} (Risk: {risk}, Corr: {corr})")

        print()

        # 3. Check extra_data field
        print("3️⃣ Extra Data Sample:")
        print("-" * 80)

        asset_with_data = (
            session.query(Asset)
            .filter(Asset.extra_data.isnot(None))
            .first()
        )

        if asset_with_data:
            print(f"Symbol: {asset_with_data.symbol}")
            print(f"Extra Data: {asset_with_data.extra_data}")
        else:
            print("No assets with extra_data found")

        print()

        # 4. Check positions
        print("4️⃣ Multi-Asset Positions:")
        print("-" * 80)

        position_count = session.query(func.count(MultiAssetPosition.id)).scalar()
        print(f"Total positions: {position_count}")
        print()

        # 5. Check correlations
        print("5️⃣ Asset Correlations:")
        print("-" * 80)

        correlation_count = session.query(func.count(AssetCorrelation.id)).scalar()
        print(f"Total correlation pairs: {correlation_count}")
        print()

        # 6. Check allocations
        print("6️⃣ Asset Allocations:")
        print("-" * 80)

        allocation_count = session.query(func.count(AssetAllocation.id)).scalar()
        print(f"Total allocation strategies: {allocation_count}")
        print()

        print("=" * 80)
        print("✅ Verification Complete")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.close()

if __name__ == "__main__":
    verify_data()
