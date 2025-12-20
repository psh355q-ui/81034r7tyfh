
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from backend.database.vector_db import engine, VectorBase
from backend.database.vector_models import NewsEmbedding, SectorEmbedding

def init_vector_db():
    print("Initializing Vector DB...")
    
    # 1. Enable pgvector extension
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("Vector extension enabled.")
        except Exception as e:
            print(f"Error enabling vector extension: {e}")
            
    # 2. Create Tables
    try:
        VectorBase.metadata.create_all(bind=engine)
        print("Vector tables created (news_embeddings, sector_embeddings).")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_vector_db()
