"""
Create Accountability Tables

Phase 29: Accountability System
Date: 2025-12-30

Creates all Accountability-related tables:
- macro_context_snapshots
- news_interpretations
- news_market_reactions
- news_decision_links
- news_narratives
- failure_analysis

Usage:
    python backend/automation/create_accountability_tables.py
"""

import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from sqlalchemy import create_engine, inspect
from backend.database.models import (
    Base,
    MacroContextSnapshot,
    NewsInterpretation,
    NewsMarketReaction,
    NewsDecisionLink,
    NewsNarrative,
    FailureAnalysis
)

def create_accountability_tables():
    """Create all Accountability tables if they don't exist"""

    # Get database URL from environment
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        return False

    # Convert async driver to sync driver (postgresql+asyncpg → postgresql+psycopg2)
    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    print("🔧 Creating Accountability tables...")
    print(f"📍 Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print()

    # Create engine
    engine = create_engine(db_url)
    inspector = inspect(engine)

    # List of Accountability tables
    accountability_tables = [
        ("macro_context_snapshots", MacroContextSnapshot),
        ("news_interpretations", NewsInterpretation),
        ("news_market_reactions", NewsMarketReaction),
        ("news_decision_links", NewsDecisionLink),
        ("news_narratives", NewsNarrative),
        ("failure_analysis", FailureAnalysis)
    ]

    created = []
    existing = []

    # Check and create each table
    for table_name, model_class in accountability_tables:
        if inspector.has_table(table_name):
            existing.append(table_name)
            print(f"⏭️  {table_name}: Already exists")
        else:
            # Create this specific table
            model_class.__table__.create(engine)
            created.append(table_name)
            print(f"✅ {table_name}: Created successfully")

    print()
    print("=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"✅ Created: {len(created)} tables")
    if created:
        for table in created:
            print(f"   - {table}")
    print()
    print(f"⏭️  Existing: {len(existing)} tables")
    if existing:
        for table in existing:
            print(f"   - {table}")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = create_accountability_tables()
    sys.exit(0 if success else 1)
