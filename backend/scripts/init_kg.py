
import asyncio
import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
from backend.config_phase14 import SEED_KNOWLEDGE
from backend.config.settings import settings

async def main():
    print("Initializing Knowledge Graph...")
    
    # Force localhost connection for local script execution
    # This overrides any 'timescaledb' host set in .env for Docker
    # Also forcing user 'ai_trading_user' and empty password (repository.py defaults)
    real_dsn = (
        f"postgresql://ai_trading_user:"
        f"@localhost:{settings.timescale_port}/{settings.timescale_db}"
    )
    print(f"Forcing connection to: {real_dsn.replace(settings.timescale_password, '***')}")
    
    # Initialize Graph
    kg = KnowledgeGraph(pg_dsn=real_dsn)
    
    # 1. Ensure Schema (Tables & Extensions)
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
