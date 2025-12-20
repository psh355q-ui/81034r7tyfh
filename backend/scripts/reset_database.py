"""
Reset Database - Drop all tables and recreate
WARNING: This will delete all data!

Usage:
    python backend/scripts/reset_database.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.models import Base
from backend.database.repository import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_database():
    """Drop all tables and recreate"""

    print("=" * 80)
    print("AI Trading System - Database Reset")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This will DELETE ALL data in the database!")
    print()

    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    try:
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
        print()

        # Recreate all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables recreated")
        print()

        print("Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        print()
        print("=" * 80)
        print("Database reset complete!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    reset_database()
