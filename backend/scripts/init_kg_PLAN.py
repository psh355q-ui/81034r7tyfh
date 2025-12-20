
import asyncio
import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
from backend.config_phase14 import SEED_KNOWLEDGE

async def main():
    print("Initializing Knowledge Graph...")
    
    # Initialize Graph
    kg = KnowledgeGraph()
    
    # 1. Ensure Schema (Tables & Extensions)
    print("Creating schema...")
    try:
        # Note: ensure_schema is synchronous but uses _get_connection which creates psycopg2 connection.
        # However, the KG code seems to mix asyncpg (for connection pool) and psycopg2 (for ensure_schema??)
        # Wait, let's check `ensure_schema` implementation again.
        # It calls `self._get_connection()` which returns None if HAS_ASYNCPG is used??
        # The file says:
        # def _get_connection(self):
        #     # asyncpg는 비동기이므로 sync 메서드에서는 메모리 모드 사용
        #     return None
        #
        # Oh, `ensure_schema` does nothing if `_get_connection` returns None!
        # And `_get_connection` ALWAYS returns None in that file!
        #
        # This means the schema creation logic in `knowledge_graph.py` is effectively disabled/broken for asyncpg.
        # I need to fix `knowledge_graph.py` or write the DDL via asyncpg here.
        pass
    except Exception as e:
        print(f"Schema creation failed: {e}")

    # Let's fix knowledge_graph.py first. It seems incomplete for asyncpg schema creation.
    # But wait, looking at the code:
    # `ensure_schema` uses `self._get_connection()` which returns None.
    # So `ensure_schema` prints "Using in-memory mode (no database)" and returns.
    # This explains why it doesn't work!
    
    # I should implement `ensure_schema_async` in the script using asyncpg because `knowledge_graph.py` is confused.
    # Or better, fix `knowledge_graph.py`.
    
    pass

if __name__ == "__main__":
    pass
