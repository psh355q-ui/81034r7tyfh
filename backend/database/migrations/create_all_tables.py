"""
Create all database tables using SQLAlchemy models
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env', override=True)

from sqlalchemy import create_engine
from backend.database.models import Base
import os

# Get database URL from environment
db_url = os.getenv('DATABASE_URL')
if not db_url:
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'Qkqhdi1!')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'ai_trading')
    # Use psycopg2 (synchronous) for table creation
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
else:
    db_name = os.getenv('DB_NAME', 'ai_trading')
    db_user = os.getenv('DB_USER', 'postgres')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    # Replace asyncpg with psycopg2
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"Creating tables in: {db_name}")
print(f"Connection: {db_user}@{db_host}:{db_port}")

# Create engine
engine = create_engine(db_url)

# Create all tables
print("\nCreating all tables from SQLAlchemy models...")
Base.metadata.create_all(engine)

print("✅ All tables created successfully!")

# Verify data_collection_progress table
from sqlalchemy import inspect
inspector = inspect(engine)
columns = inspector.get_columns('data_collection_progress')

print("\ndata_collection_progress columns:")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")
