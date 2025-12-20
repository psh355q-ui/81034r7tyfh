import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.backtesting.consensus_backtest import ConsensusBacktest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("================================================================================")
    print("               Consensus Backtest: Real Data Integration Verification")
    print("================================================================================")
    
    # 1. Configuration
    # Use Real Data (yfinance implemented in BacktestEngine)
    # Use Real Consensus (AI Clients) - Set use_mock_consensus=False
    # Note: For this quick verification, we might still use Mock Consensus if API keys aren't set,
    # but we are verifying the *wiring*.
    
    print("\n[Configuration]")
    print("- Data Source: yfinance (Real Historical Data)")
    print("- Consensus: Real AI Engine (if keys present) or Mock Fallback")
    
    # Run for just a few days to avoid long wait if using Real AI
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7) 
    tickers = ["AAPL"] # Single ticker for speed
    
    print(f"- Period: {start_date.date()} ~ {end_date.date()}")
    print(f"- Tickers: {tickers}")
    
    # 2. Initialize Runner
    # We set use_mock_consensus=False to Trigger the new logic in _generate_consensus_signal
    # If API keys are missing, the ConsensusEngine will log warning and specific client might fail/mock,
    # but the path is exercised.
    try:
        runner = ConsensusBacktest(
            initial_capital=100000.0,
            use_mock_consensus=False # <--- KEY CHANGE: Request Real AI
        )
        
        # 3. Run Simulation
        print("\n[Running Backtest]...")
        report = await runner.run(tickers, start_date, end_date)
        
        # 4. Output Results
        if isinstance(report, dict):
            import json
            report_str = json.dumps(report, indent=2, default=str)
            print("\n" + report_str)
            
            # Also try to print the summary field if it exists and is a string
            if "summary" in report:
                 # It might be a dict or string
                 print("\n[Summary Section]")
                 print(report["summary"])
        else:
            report_str = str(report)
            print("\n" + report_str)
        
        # Save report
        with open("logs/backtest/real_data_backtest_report.txt", "w", encoding="utf-8") as f:
            f.write(report_str)
        print(f"\nReport saved to logs/backtest/real_data_backtest_report.txt")
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
