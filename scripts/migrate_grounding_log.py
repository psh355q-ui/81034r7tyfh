
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.repository import get_sync_session
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting GroundingSearchLog migration...")
    
    db = get_sync_session()
    try:
        # Add ticker column
        try:
            db.execute(text("ALTER TABLE grounding_search_logs ADD COLUMN ticker VARCHAR(50)"))
            logger.info("Added ticker column")
        except Exception as e:
            logger.warning(f"Could not add ticker column (might exist): {e}")
            db.rollback()

        # Add emergency_trigger column
        try:
            db.execute(text("ALTER TABLE grounding_search_logs ADD COLUMN emergency_trigger VARCHAR(255)"))
            logger.info("Added emergency_trigger column")
        except Exception as e:
            logger.warning(f"Could not add emergency_trigger column (might exist): {e}")
            db.rollback()

        # Add was_emergency column
        try:
            db.execute(text("ALTER TABLE grounding_search_logs ADD COLUMN was_emergency BOOLEAN DEFAULT FALSE"))
            logger.info("Added was_emergency column")
        except Exception as e:
            logger.warning(f"Could not add was_emergency column (might exist): {e}")
            db.rollback()
            
        # Create index
        try:
            db.execute(text("CREATE INDEX idx_grounding_ticker ON grounding_search_logs (ticker)"))
            logger.info("Created index idx_grounding_ticker")
        except Exception as e:
            logger.warning(f"Could not create index (might exist): {e}")
            db.rollback()

        db.commit()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
