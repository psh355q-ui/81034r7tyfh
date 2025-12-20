
import asyncio
import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
from backend.config_phase14 import SEED_KNOWLEDGE
from backend.database.repository import get_db_pool

async def main():
    print("Initializing Knowledge Graph via Repository Pool...")
    
    # Get shared pool which is known to work
    try:
        pool = await get_db_pool()
        if not pool:
            print("Failed to get pool from repository")
            return
        print("Successfully obtained DB pool from repository")
    except Exception as e:
        print(f"Failed to get db pool: {e}")
        return
    
    # Initialize Graph
    kg = KnowledgeGraph()
    # Inject the pool!
    kg._pool = pool
    
    # 1. Ensure Schema
    print("Creating schema...")
    try:
        await kg.ensure_schema_async()
    except Exception as e:
        print(f"Schema creation failed: {e}")

    # 2. Import Seed Knowledge
    print("Importing seed data...")
    try:
        count = await kg.import_seed_knowledge(SEED_KNOWLEDGE)
        print(f"Successfully imported {count} items.")
    except Exception as e:
        print(f"Seed import failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
