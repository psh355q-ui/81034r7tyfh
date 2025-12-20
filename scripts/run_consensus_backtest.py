import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.backtesting.consensus_backtest import ConsensusBacktest

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Consensus Backtest Simulation...")
    
    # 1. Configuration
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 1) # 6 months
    tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
    
    # 2. Initialize Backtest Runner
    runner = ConsensusBacktest(
        initial_capital=100000.0,
        consensus_threshold=0.6, # 2/3 votes -> 66% so 0.6 is good cutoff
        use_mock_consensus=True
    )
    
    # 3. Run Simulation
    result = await runner.run(tickers, start_date, end_date)
    
    # 4. Print Summary
    print("\n" + result["summary"])
    
    # 5. Save Mock Report
    with open("logs/backtest/backtest_report.txt", "w", encoding="utf-8") as f:
        f.write(result["summary"])

if __name__ == "__main__":
    asyncio.run(main())
