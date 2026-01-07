
import asyncio
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import select

# Add project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.models import TradingSignal, Order
from backend.core.database import DatabaseSession
from backend.ai.trading.shadow_trading_agent import ShadowTradingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_shadow_loop():
    print("\n" + "="*50)
    print("🕵️ verifying Phase 4: Shadow Trading Loop (Async)")
    print("="*50)

    TEST_TICKER = "AAPL"
    TEST_ACTION = "BUY"
    
    # 1. Create Dummy Signal
    logger.info(f"1. Injecting Test Signal for {TEST_TICKER}...")
    async with DatabaseSession() as db:
        signal = TradingSignal(
            ticker=TEST_TICKER,
            action=TEST_ACTION,
            signal_type="TEST_SIGNAL",
            confidence=99.9,
            reasoning="Integration Test Signal",
            source="API_TEST",
            created_at=datetime.now()
        )
        db.add(signal)
        await db.commit()
        await db.refresh(signal)
        signal_id = signal.id
        print(f"   -> Created Signal ID: {signal_id}")

    # 2. Run Agent (Single Pass)
    logger.info("2. Running ShadowTradingAgent...")
    agent = ShadowTradingAgent()
    await agent.process_pending_signals()
    
    # 3. Verify Order Creation
    logger.info("3. Verifying Order Table...")
    async with DatabaseSession() as db:
        result = await db.execute(select(Order).where(Order.signal_id == signal_id))
        order = result.scalars().first()
        
        if order:
            print(f"   -> ✅ Order Found!")
            print(f"      ID: {order.id}")
            print(f"      Order ID: {order.order_id}")
            print(f"      Status: {order.status}")
            print(f"      Filled Price: {order.filled_price}")
            
            if "SHADOW_" in str(order.order_id):
                print("   -> ✅ 'SHADOW_' prefix confirmed.")
            else:
                print("   -> ❌ 'SHADOW_' prefix MISSING.")
        else:
            print("   -> ❌ Order NOT found for signal.")

    print("\n" + "="*50)
    print("🏁 Verification Complete")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(verify_shadow_loop())
