
import sys
import os
from sqlalchemy import create_engine, text

# Main DB (TimescaleDB)
MAIN_DB_URL = "postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading"

def check_vector_extension():
    engine = create_engine(MAIN_DB_URL, connect_args={'client_encoding': 'utf8'})
    with engine.connect() as conn:
        try:
            print("Attempting to CREATE EXTENSION vector on Main DB...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("SUCCESS: pgvector extension enabled on Main DB!")
        except Exception as e:
            print(f"FAILURE: Could not enable vector extension on Main DB.\nError: {e}")

if __name__ == "__main__":
    check_vector_extension()
