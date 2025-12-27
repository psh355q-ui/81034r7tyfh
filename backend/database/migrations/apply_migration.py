
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.database.repository import get_sync_session
from sqlalchemy import text

def apply_migration():
    print("Applying Phase 3 Migration via SQLAlchemy...")
    session = get_sync_session()
    
    try:
        # Read SQL file
        sql_path = Path(__file__).parent / "phase3_schema_sync.sql"
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        # Split by semicolon (roughly) or execute as block if DB supports it.
        # Postgres supports executing block if not using transaction controls inside nicely.
        # But split is safer for individual statements if there are many.
        # Our script has ALTER TABLE etc.
        # Let's try executing the whole block first.
        
        print(f"Reading migration from {sql_path}")
        session.execute(text(sql_content))
        session.commit()
        print("✅ Migration applied successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    apply_migration()
