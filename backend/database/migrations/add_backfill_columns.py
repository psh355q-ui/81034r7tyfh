"""
DB 마이그레이션: data_collection_progress 테이블에 컬럼 추가

추가할 컬럼:
- source (VARCHAR(50), NOT NULL)
- collection_type (VARCHAR(50), NOT NULL)
- start_date (TIMESTAMP)
- end_date (TIMESTAMP)
- job_metadata (JSONB)

변경할 컬럼:
- task_name: unique 제약조건 제거, nullable로 변경
"""
import sys
from pathlib import Path

# Add project root to path
# Current file is at: backend/database/migrations/add_backfill_columns.py
# So we need to go up 3 levels to reach project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load .env file from project root
env_path = project_root / '.env'
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path, override=True)
    print("✓ .env file loaded")
else:
    print("✗ .env file not found, using environment variables only")

# Database connection (reading from .env file)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'ai_trading')
DB_USER = os.getenv('DB_USER', 'postgres')  # postgres-prod의 실제 사용자
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

print(f"\nEnvironment variables read:")
print(f"  DB_HOST: {DB_HOST}")
print(f"  DB_PORT: {DB_PORT}")
print(f"  DB_NAME: {DB_NAME}")
print(f"  DB_USER: {DB_USER}")
print(f"  DB_PASSWORD: {'(set)' if DB_PASSWORD else '(empty)'}")

if not DB_PASSWORD:
    print("\n⚠️  WARNING: DB_PASSWORD is empty!")
    print("   Please check your .env file and ensure DB_PASSWORD is set")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"\nConnecting to: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}\n")



def run_migration():
    """Run migration to update data_collection_progress table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Starting migration...")
        
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'data_collection_progress'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("Table data_collection_progress does not exist. Creating from scratch...")
                conn.execute(text("""
                    CREATE TABLE data_collection_progress (
                        id SERIAL PRIMARY KEY,
                        task_name VARCHAR(100),
                        source VARCHAR(50) NOT NULL,
                        collection_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        progress_pct FLOAT NOT NULL DEFAULT 0.0,
                        items_processed INTEGER NOT NULL DEFAULT 0,
                        items_total INTEGER,
                        error_message TEXT,
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        job_metadata JSONB,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                    
                    CREATE INDEX idx_data_collection_source ON data_collection_progress(source);
                    CREATE INDEX idx_data_collection_type ON data_collection_progress(collection_type);
                    CREATE INDEX idx_data_collection_status ON data_collection_progress(status);
                    CREATE INDEX idx_data_collection_task_name ON data_collection_progress(task_name);
                """))
                conn.commit()
                print("✓ Table created successfully")
                return
            
            # Table exists, check and add missing columns
            print("Table exists, checking for missing columns...")
            
            # Get existing columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_collection_progress';
            """))
            existing_columns = {row[0] for row in result}
            
            print(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            if 'source' not in existing_columns:
                print("Adding column: source")
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    ADD COLUMN source VARCHAR(50);
                """))
                conn.commit()
            
            if 'collection_type' not in existing_columns:
                print("Adding column: collection_type")
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    ADD COLUMN collection_type VARCHAR(50);
                """))
                conn.commit()
            
            if 'start_date' not in existing_columns:
                print("Adding column: start_date")
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    ADD COLUMN start_date TIMESTAMP;
                """))
                conn.commit()
            
            if 'end_date' not in existing_columns:
                print("Adding column: end_date")
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    ADD COLUMN end_date TIMESTAMP;
                """))
                conn.commit()
            
            if 'job_metadata' not in existing_columns:
                print("Adding column: job_metadata")
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    ADD COLUMN job_metadata JSONB;
                """))
                conn.commit()
            
            # Set source and collection_type to NOT NULL after adding default values
            print("Updating NULL values and setting constraints...")
            conn.execute(text("""
                UPDATE data_collection_progress 
                SET source = 'unknown' 
                WHERE source IS NULL;
                
                UPDATE data_collection_progress 
                SET collection_type = 'unknown' 
                WHERE collection_type IS NULL;
                
                ALTER TABLE data_collection_progress 
                ALTER COLUMN source SET NOT NULL;
                
                ALTER TABLE data_collection_progress 
                ALTER COLUMN collection_type SET NOT NULL;
            """))
            conn.commit()
            
            # Drop unique constraint on task_name if exists
            print("Removing unique constraint from task_name...")
            try:
                conn.execute(text("""
                    ALTER TABLE data_collection_progress 
                    DROP CONSTRAINT IF EXISTS data_collection_progress_task_name_key;
                """))
                conn.commit()
            except Exception as e:
                print(f"Note: {e}")
            
            # Create indexes if they don't exist
            print("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_collection_source 
                ON data_collection_progress(source);
                
                CREATE INDEX IF NOT EXISTS idx_data_collection_type 
                ON data_collection_progress(collection_type);
                
                CREATE INDEX IF NOT EXISTS idx_data_collection_status 
                ON data_collection_progress(status);
            """))
            conn.commit()
            
            print("✓ Migration completed successfully!")
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()
