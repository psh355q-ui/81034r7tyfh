
import logging
import asyncio
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import TradingSignal, Order
from backend.core.database import DatabaseSession
from backend.ai.order_execution.shadow_order_executor import ShadowOrderExecutor
from backend.ai.portfolio.account_partitioning import AccountPartitionManager

logger = logging.getLogger(__name__)

class ShadowTradingAgent:
    """
    Monitors TradingSignals and executes them in Shadow Mode.
    Integrates:
    - Signal Polling
    - Portfolio Sizing (Partition Manager)
    - Order Execution (ShadowExecutor)
    """

    def __init__(self):
        self.executor = ShadowOrderExecutor()
        self.partition_manager = AccountPartitionManager()
        self.min_confidence = 70.0 # Only act on high confidence signals

    async def run_loop(self, interval_seconds: int = 60):
        """Continuous monitoring loop"""
        logger.info("👻 Shadow Trading Agent started.")
        while True:
            try:
                await self.process_pending_signals()
            except Exception as e:
                logger.error(f"Error in shadow trading loop: {e}")
            
            await asyncio.sleep(interval_seconds)

    async def process_pending_signals(self):
        """Find unprocessed signals and execute them"""
        async with DatabaseSession() as db:
            # 1. Fetch recent unprocessed signals
            # Logic: Select signals where id is NOT in Orders.signal_id
            
            # Subquery for processed signal IDs
            # Note: in SQLAlchemy async, using notin_ with scalar subquery might require care
            processed_signals_query = select(Order.signal_id).where(Order.signal_id.isnot(None))
            
            # Query pending signals
            query = (
                select(TradingSignal)
                .where(TradingSignal.confidence >= self.min_confidence)
                .where(TradingSignal.id.notin_(processed_signals_query))
                .order_by(TradingSignal.created_at.desc())
                .limit(10) # Process batch
            )
            
            result = await db.execute(query)
            pending_signals = result.scalars().all()

            if not pending_signals:
                return

            logger.info(f"🔎 Found {len(pending_signals)} pending signals.")

            for signal in pending_signals:
                await self._execute_signal(db, signal)

    async def _execute_signal(self, db: AsyncSession, signal: TradingSignal):
        """Execute a single signal"""
        logger.info(f"⚡ Processing Signal #{signal.id}: {signal.action} {signal.ticker}")

        # 1. Determine Quantity based on Portfolio Rules
        # For MVP Shadow: Use fixed allocation or calculate based on 'Core' partition
        quantity = self._calculate_position_size(signal)
        
        if quantity <= 0:
            logger.warning(f"⚠️ Calculated quantity 0 for {signal.ticker}, skipping.")
            return

        # 2. Execute Shadow Order (Assuming executor handles its own DB session or we pass one)
        # Executor constructor takes db optional. If we pass db, it uses it.
        # But executor is initialized in __init__ without db.
        # So executor will create its own session unless we pass it.
        # But `executor.execute_order` only takes `ticker`, `action`... not `db`.
        # Wait, I updated `execute_order` to behave differently?
        # In current `ShadowOrderExecutor`:
        # `if self.db:` uses `self.db`. 
        # So if I want to reuse session, I must instantiate executor with session.
        # However, `process_pending_signals` iterates.
        # Let's initiate a temporary executor with current session for transaction safety?
        # Or just let executor handle it independently?
        # If I pass `db` to `_execute_signal`, I should use it.
        # Let's create a temporary executor or just implement logic here.
        # Cleaner: Instantiate executor with db for this batch.
        
        temp_executor = ShadowOrderExecutor(db=db)

        result = await temp_executor.execute_order(
            ticker=signal.ticker,
            action=signal.action,
            quantity=quantity,
            signal_id=signal.id
        )

        if result.get("status") == "filled":
            logger.info(f"✅ Signal #{signal.id} executed successfully.")
        else:
            logger.error(f"❌ Signal #{signal.id} execution failed: {result.get('reason')}")

    def _calculate_position_size(self, signal: TradingSignal) -> int:
        """
        Calculate number of shares to buy/sell.
        Strategy:
        - BUY: Allocate fixed USD amount (e.g., $5,000) or % of Cash.
        - SELL: Sell all or half? For MVP, let's assume 'Action' implies intent.
          If signal doesn't specify 'shares', we need a rule.
        """
        if signal.shares and signal.shares > 0:
            return signal.shares
        
        # Default Rule if shares not specified
        TARGET_ALLOCATION_USD = 5000.0 # $5k per trade for test
        
        # Need current price to convert USD to Shares
        # KISBroker fetch is sync blocking, careful.
        # For calculation, getting approx price is fine.
        try:
             price = 0.0
             if self.executor.broker:
                 price_data = self.executor.broker.get_price(signal.ticker)
                 if price_data and "current_price" in price_data:
                     price = float(price_data["current_price"])
             
             if price <= 0:
                 # If no real price, assume $150 for test or fallback
                 price = 150.0 
                 
             quantity = int(TARGET_ALLOCATION_USD // price)
             return max(1, quantity)
        except:
             return 0

if __name__ == "__main__":
    # Test Run
    agent = ShadowTradingAgent()
    asyncio.run(agent.process_pending_signals())
