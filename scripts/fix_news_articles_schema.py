
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_schema():
    load_dotenv()
    
    # Use DB_URL directly or construct it
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Force sync driver for this script
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")

    print(f"🔄 Connecting to database: {database_url.split('@')[-1]}") # Hide password
    
    engine = create_engine(database_url)
    
    cols_to_add = [
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS narrative_phase VARCHAR(20);",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS narrative_strength DOUBLE PRECISION;",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS narrative_consensus DOUBLE PRECISION;",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS fact_verification_status VARCHAR(20);",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS fact_confidence_adjustment DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS price_correlation_score DOUBLE PRECISION;",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS confirmation_status VARCHAR(20);",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS narrative_tags VARCHAR[];",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS horizon_tags VARCHAR[];",
        "ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS glm_analysis JSONB;"
    ]

    with engine.connect() as conn:
        with conn.begin(): # Start transaction
            for stmt in cols_to_add:
                try:
                    conn.execute(text(stmt))
                    print(f"✅ Executed: {stmt}")
                except Exception as e:
                    print(f"⚠️ Failed to execute: {stmt}. Error: {e}")
    
    print("✅ Schema update completed successfully.")

if __name__ == "__main__":
    fix_schema()
