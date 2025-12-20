"""
Database Initialization Script
Creates all tables defined in backend/database/models.py

Usage:
    python backend/scripts/init_database.py
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


def init_database():
    """Initialize database tables"""

    print("=" * 80)
    print("AI Trading System - Database Initialization")
    print("=" * 80)
    print()

    try:
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        print("✅ Database tables created successfully!")
        print()
        print("Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        print()
        print("=" * 80)
        print("Database initialization complete!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    init_database()
