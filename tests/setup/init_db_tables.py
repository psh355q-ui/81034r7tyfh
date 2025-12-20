
import asyncio
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from backend.core.database import init_db
# Explicitly import models to register them with Base.metadata
from backend.database.models import Base, TradingSignal, NewsArticle, AnalysisResult, BacktestRun, BacktestTrade, SignalPerformance

async def main():
    print("Imported models...")
    print(f"Tables to create: {list(Base.metadata.tables.keys())}")
    
    print("Initializing database tables...")
    await init_db()
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to initialize database: {e}")
