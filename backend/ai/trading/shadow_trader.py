import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.data.news_models import SessionLocal
from backend.database.models import TradingSignal, Order
from backend.ai.portfolio.account_partitioning import get_partition_manager, WalletType
from backend.brokers.kis_broker import KISBroker
from backend.ai.safety.leverage_guardian import get_leverage_guardian

logger = logging.getLogger(__name__)

STATUS_FILE = Path("data/shadow_trader_status.json")

class ShadowTradingAgent:
    def __init__(self):
        self.user_id = "default_user"
        self.partition_manager = get_partition_manager(self.user_id)
        self.is_running = False
        self.interval_seconds = 60
        self.broker = KISBroker()  # For price data
        self.guardian = get_leverage_guardian()
        
        self.last_signal_id = self._load_last_id()
        
    def _load_last_id(self) -> int:
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r") as f:
                    return json.load(f).get("last_signal_id", 0)
            except:
                return 0
        return 0

    def _save_last_id(self, signal_id: int):
        self.last_signal_id = signal_id
        try:
            STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATUS_FILE, "w") as f:
                json.dump({"last_signal_id": signal_id}, f)
        except Exception as e:
            logger.error(f"Failed to save shadow status: {e}")

    async def start(self):
        """Start the shadow trading loop"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"👻 ShadowTradingAgent started (Last ID: {self.last_signal_id})")
        
        while self.is_running:
            try:
                await self.process_signals()
            except Exception as e:
                logger.error(f"❌ ShadowTrading Loop Error: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.is_running = False
        logger.info("👻 ShadowTradingAgent stopped")

    async def process_signals(self):
        """Process new trading signals"""
        db = SessionLocal()
        try:
            # Fetch new signals
            signals = db.query(TradingSignal)\
                .filter(TradingSignal.id > self.last_signal_id)\
                .order_by(TradingSignal.id.asc())\
                .limit(10)\
                .all()
                
            if not signals:
                return

            logger.info(f"👻 Processing {len(signals)} new signals...")
            
            for signal in signals:
                await self.execute_trade(db, signal)
                self._save_last_id(signal.id)
                
        finally:
            db.close()

    async def execute_trade(self, db: Session, signal: TradingSignal):
        """Execute virtual trade"""
        ticker = signal.ticker
        action = signal.action.upper()
        
        # 1. Get Price (Sync call wrapped)
        try:
            price_info = await asyncio.to_thread(self.broker.get_current_price, ticker)
            current_price = float(price_info.get('price', 0))
            if current_price <= 0:
                logger.warning(f"Skipping {ticker}: Invalid price {current_price}")
                return
        except Exception as e:
            logger.error(f"Price fetch failed for {ticker}: {e}")
            return

        # 2. Strategy: Amount to Invest
        # MVP: Fixed $1,000 per signal
        invest_amount = 1000.0
        quantity = int(invest_amount / current_price)
        
        if quantity < 1:
            logger.warning(f"Skipping {ticker}: Price ${current_price} > Invest Amount ${invest_amount}")
            return

        # 3. Determine Wallet
        wallet = WalletType.CORE
        if self.guardian.is_leveraged(ticker):
            wallet = WalletType.SATELLITE
        # Add INCOME logic if dividend stock (later)

        # 4. Execute Allocation via Manager
        if action == "BUY":
            result = self.partition_manager.allocate_to_wallet(
                wallet=wallet.value,
                ticker=ticker,
                quantity=quantity,
                price=current_price
            )
            
            if result["success"]:
                logger.info(f"👻 BUY EXECUTED: {ticker} {quantity}qty @ ${current_price} -> {wallet.value}")
                self._record_order(db, signal, ticker, "BUY", quantity, current_price, "FILLED")
            else:
                logger.warning(f"👻 BUY FAILED: {result['error']}")
                self._record_order(db, signal, ticker, "BUY", quantity, current_price, "REJECTED", result['error'])

        elif action == "SELL":
            # Simple sell logic: Sell ALL from relevant wallet? Or matching quantity?
            # MVP: Try selling from all wallets (cascade) or just verify holding.
            # Used simplified 'sell_from_wallet'
            
            # Check holding in specific wallet
            result = self.partition_manager.sell_from_wallet(
                wallet=wallet.value,
                ticker=ticker,
                quantity=quantity, # Selling same amount as buy unit? naive.
                price=current_price
            )
            # Logic improvement needs Position Check before quantity determination
            
            if result["success"]:
                 logger.info(f"👻 SELL EXECUTED: {ticker} {quantity}qty @ ${current_price}")
                 self._record_order(db, signal, ticker, "SELL", quantity, current_price, "FILLED")
            else:
                 logger.warning(f"👻 SELL FAILED: {result.get('error')}")

    def _record_order(self, db: Session, signal, ticker, side, qty, price, status, msg=""):
        """Record to Order table (Shadow Mode)"""
        try:
            order = Order(
                ticker=ticker,
                action=side,
                quantity=qty,
                price=price,
                status=status,
                signal_id=signal.id,
                error_message=msg if msg else None,
                created_at=datetime.utcnow()
                # is_virtual=True if column exists? Assuming Order table usage for now.
            )
            db.add(order)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to record order: {e}")
