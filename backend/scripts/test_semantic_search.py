
import sys
import os
from sqlalchemy import create_engine, text
from pgvector.sqlalchemy import Vector

# Add project root
sys.path.append(os.getcwd())

from backend.ai.rag.embedding_service import embedding_service
from backend.database.vector_db import VECTOR_DATABASE_URL

def test_semantic_search(query_text: str):
    print(f"Query: '{query_text}'")
    
    # 1. Generate Query Embedding
    query_vector = embedding_service.generate_embedding(query_text)
    if not query_vector:
        print("Failed to generate embedding.")
        return

    # 2. Search in Vector DB
    engine = create_engine(VECTOR_DATABASE_URL)
    
    with engine.connect() as conn:
        # Distance metric: <=> is cosine distance (lower is better, 0=identical, 1=orthogonal, 2=opposite)
        # Note: pgvector vector(768)
        
        # Cast parameter to vector type explicitly if needed, typically sqlalchemy handles list->vector
        sql = text("""
            SELECT title, sector, embedding <=> :qv as distance
            FROM news_embeddings
            ORDER BY distance ASC
            LIMIT 5
        """)
        
        # Pass vector as string representation for raw SQL compatibility if needed, 
        # or list if driver supports it. psycopg2/asyncpg handle list for vector type usually.
        # Ensure 'vector' extension loaded or cast.
        
        try:
            result = conn.execute(sql, {"qv": str(query_vector)})
            rows = result.fetchall()
            
            print("\nTop 5 Results:")
            for row in rows:
                title = row[0]
                sector = row[1]
                distance = row[2]
                print(f"[{distance:.4f}] {title} (Sector: {sector})")
                
        except Exception as e:
            print(f"Search Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        q = sys.argv[1]
    else:
        q = "Market crash risk"
    
    test_semantic_search(q)
