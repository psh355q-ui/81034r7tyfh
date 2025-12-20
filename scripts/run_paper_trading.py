import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.brokers.kis_broker import KISBroker
from backend.ai.consensus.consensus_engine import get_consensus_engine
from backend.automation.auto_trader import AutoTrader
from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_paper_trading():
    print("================================================================================")
    print("                    AI Trading System: Paper Trading Mode")
    print("================================================================================")
    
    # 1. Initialize Components
    print("\n[1] Initializing Components...")
    
    # KIS Broker (Paper Trading)
    # Ensure you have KIS_APP_KEY_PAPER, KIS_APP_SECRET_PAPER, KIS_ACCOUNT_NO_PAPER in env/logic
    try:
        # Assuming defaults or env vars handle credentials
        # For safety in this test script, we might mock if no credentials, 
        # but the goal is to test the integration.
        # If Init fails, we'll know.
        broker = KISBroker(account_no="88888888", is_virtual=True) # Mock account for safety if env missing
    except Exception as e:
        logger.warning(f"KIS Broker init failed (expected if no keys): {e}")
        logger.info("Proceeding with Mock Broker for logic verification")
        broker = None 

    # Consensus Engine (Real AI)
    consensus_engine = get_consensus_engine()
    
    # Auto Trader
    trader = AutoTrader(
        kis_broker=broker,
        auto_execute=True, # Execute orders (Virtual)
        position_size_pct=0.1 # 10% per trade
    )

    # 2. Define Tickers to Scan
    tickers = ["AAPL", "NVDA", "TSLA"]
    print(f"\n[2] Scanning Tickers: {tickers}")

    summary_stats = {"scanned": 0, "approved": 0, "executed": 0}

    # 3. Execution Loop
    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        summary_stats["scanned"] += 1
        
        try:
            # 3.1 Get Market Data (Price)
            current_price = 0.0
            if broker:
                price_info = broker.get_price(ticker)
                if price_info:
                    current_price = price_info['current_price']
            
            # Fallback if broker fails or no keys
            if current_price == 0:
                print(f"  - Warning: Could not fetch price from Broker. Using Mock Price.")
                current_price = 150.0 # Mock

            print(f"  - Current Price: ${current_price}")

            # 3.2 Build Market Context
            # In a real loop, we would fetch news here. 
            # For verification, we inject robust signals to trigger action.
            context = MarketContext(
                ticker=ticker,
                company_name=ticker,
                current_price=current_price,
                news=NewsFeatures(
                    headline=f"{ticker} announces revolutionary AI breakthrough",
                    segment=MarketSegment.TRAINING,
                    sentiment=0.9 # High positive sentiment to encourage BUY
                )
            )

            # 3.3 Consensus Vote
            print("  - Requesting AI Consensus Vote...")
            consensus_result = await consensus_engine.vote_on_signal(
                context=context,
                action="BUY",
                additional_info={"source": "paper_trading_script"}
            )
            
            print(f"  - Vote Result: {'APPROVED' if consensus_result.approved else 'REJECTED'}")
            print(f"  - Score: {consensus_result.approve_count}/3 ({consensus_result.consensus_strength.value})")
            
            if consensus_result.approved:
                summary_stats["approved"] += 1
                
                # 3.4 Auto Execution
                print("  - Executing Order via AutoTrader...")
                exec_result = await trader.on_consensus_approved(
                    consensus_result=consensus_result,
                    market_context=context,
                    current_price=current_price
                )
                
                if exec_result.get("executed") or exec_result.get("dry_run"):
                     summary_stats["executed"] += 1
                     print(f"  - Order Status: {exec_result.get('status', 'Submitted/DryRun')}")
                     if "order_id" in exec_result:
                         print(f"  - Order ID: {exec_result['order_id']}")
                else:
                    print(f"  - Execution Failed: {exec_result.get('error')}")

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")

    # 4. Final Report
    print("\n================================================================================")
    print("                    Paper Trading Session Complete")
    print("================================================================================")
    print(f"Scanned: {summary_stats['scanned']}")
    print(f"Approved: {summary_stats['approved']}")
    print(f"Executed: {summary_stats['executed']}")
    
    if trader.execution_history:
        print("\n[Execution History]")
        for exec_rec in trader.execution_history:
            print(f"- {exec_rec['timestamp']} {exec_rec['action']} {exec_rec['ticker']} (Success: {exec_rec.get('executed')})")

if __name__ == "__main__":
    asyncio.run(run_paper_trading())
