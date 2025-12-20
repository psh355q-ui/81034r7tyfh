
import asyncio
import logging
import os
from datetime import datetime
from backend.data.vector_store.store import VectorStoreContext
from backend.data.vector_store.embedder import DocumentEmbedder
from backend.data.vector_store.tagger import AutoTagger
from backend.data.collectors.fred_collector import FredCollector
from backend.data.collectors.dart_collector import DartCollector
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

class MemoryBuilder:
    """
    Orchestrator for Phase G: Data & Memory Injection.
    Runs collectors and populates the VectorStore.
    """

    def __init__(self):
        if not os.getenv("DATABASE_URL"):
            db_user = os.getenv("DB_USER", "ai_trading_user")
            db_password = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("TIMESCALE_HOST", os.getenv("DB_HOST", "localhost"))
            db_port = os.getenv("TIMESCALE_PORT", os.getenv("DB_PORT", "5541"))
            db_name = os.getenv("TIMESCALE_DATABASE", os.getenv("DB_NAME", "ai_trading"))
            self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            self.db_url = os.getenv("DATABASE_URL")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY is required for embedding.")

    async def run(self, tickers=None):
        logger.info("Starting Memory Builder Pipeline...")
        
        # Initialize Components
        embedder = DocumentEmbedder(self.openai_key)
        tagger = None
        if self.anthropic_key:
            pass # Tagger initialization (optional for now, can use None)
            # tagger = AutoTagger(...) 

        # Collectors
        fred = FredCollector()
        dart = DartCollector()

        async with VectorStoreContext(self.db_url, embedder, tagger) as store:
            
            # 1. Macro Memory (FRED)
            try:
                await fred.collect_and_store(store)
            except Exception as e:
                logger.error(f"FRED collection failed: {e}")

            # 2. Corporate Memory (DART)
            if tickers:
                try:
                    await dart.collect_and_store(store, tickers)
                except Exception as e:
                    logger.error(f"DART collection failed: {e}")
            else:
                logger.info("No tickers provided for DART collection. Skipping.")

        logger.info("Memory Builder Pipeline Completed.")

if __name__ == "__main__":
    # Test Run
    logging.basicConfig(level=logging.INFO)
    
    # Example Tickers (Samsung, SK Hynix)
    target_tickers = ["005930", "000660"] 
    
    builder = MemoryBuilder()
    asyncio.run(builder.run(tickers=target_tickers))
