
import sys
import os
sys.path.insert(0, os.getcwd())

from sqlalchemy import create_engine
from backend.database.models import Base
from backend.database.repository import DATABASE_URL

def create_table():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Filter only DeepReasoningAnalysis table
    target_table = "deep_reasoning_analyses"
    
    tables = [t for t in Base.metadata.sorted_tables if t.name == target_table]
    if not tables:
        print(f"❌ Table {target_table} not found in metadata!")
        return

    print(f"Creating table: {target_table}")
    Base.metadata.create_all(bind=engine, tables=tables)
    print("✅ Done.")

if __name__ == "__main__":
    create_table()
