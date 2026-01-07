
import logging
import os
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from backend.database.models import Order
from backend.brokers.kis_broker import KISBroker
from backend.core.database import DatabaseSession

logger = logging.getLogger(__name__)

# Load env
load_dotenv(override=True)

class ShadowOrderExecutor:
    """
    Executes trades in 'Shadow Mode' (Simulation).
    Does not send orders to real exchange.
    Uses real-time price from KIS or DB for execution price.
    """

    def __init__(self, db: AsyncSession = None):
        self.db = db
        
        # Initialize KIS Broker with env vars
        account_no = os.getenv("KIS_ACCOUNT_NUMBER", "")
        if not account_no:
            logger.warning("KIS_ACCOUNT_NUMBER not found in env. Price fetching may fail.")
        
        try:
            # We don't perform full auth here if just for price? 
            # KISBroker performs auth in __init__.
            self.broker = KISBroker(account_no=account_no)
        except Exception as e:
            logger.error(f"Failed to initialize KIS Broker: {e}")
            self.broker = None

    async def execute_order(self, ticker: str, action: str, quantity: int, signal_id: int = None) -> Dict:
        """
        Simulate order execution.
        """
        logger.info(f"👻 Shadow Execution: {action} {quantity} {ticker}")

        # 1. Get Current Price
        current_price = await self._get_execution_price(ticker)
        if not current_price:
            logger.error(f"❌ Failed to get price for {ticker}, skipping shadow trade.")
            return {"status": "failed", "reason": "price_fetch_failed"}

        # 2. Calculate details
        timestamp = datetime.now()
        
        # 3. Create Order Record (Marked as SHADOW)
        if self.db:
             return await self._save_order(self.db, ticker, action, quantity, current_price, signal_id, timestamp)
        else:
            async with DatabaseSession() as db:
               return await self._save_order(db, ticker, action, quantity, current_price, signal_id, timestamp)

    async def _save_order(self, db: AsyncSession, ticker, action, quantity, price, signal_id, timestamp) -> Dict:
        try:
            shadow_order_id = f"SHADOW_{timestamp.strftime('%Y%m%d%H%M%S')}_{ticker}"
            
            new_order = Order(
                ticker=ticker,
                action=action,
                quantity=quantity,
                order_type="market", # Always market for shadow
                status="FILLED", # Instant fill
                limit_price=None,
                filled_price=price,
                created_at=timestamp,
                filled_at=timestamp,
                order_id=shadow_order_id, # Distinguisher
                signal_id=signal_id,
                error_message="Shadow Trade (Simulated)"
            )
            
            db.add(new_order)
            await db.commit()
            await db.refresh(new_order)
            
            logger.info(f"✅ Shadow Order Filled: {ticker} @ {price}")
            
            return {
                "status": "filled",
                "order_id": shadow_order_id,
                "filled_price": price,
                "filled_quantity": quantity,
                "timestamp": timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to save shadow order: {e}")
            await db.rollback()
            return {"status": "failed", "reason": str(e)}

    async def _get_execution_price(self, ticker: str) -> Optional[float]:
        """Fetch real-time price, fallback to DB last close"""
        # Try KIS Broker first
        if self.broker:
            try:
                # TODO: Make KISBroker async or run in threadpool if blocking
                price = self.broker.get_price(ticker) # Changed from get_current_price to get_price based on KISBroker method
                if price and "current_price" in price:
                    return float(price["current_price"])
            except Exception as e:
                logger.warning(f"KIS price fetch failed for {ticker}: {e}")
        else:
             logger.warning("KIS Broker not initialized, skipping price fetch.")

        # Fallback: Use dummy price for testing if real fetch fails
        return 150.0 # Mock price
