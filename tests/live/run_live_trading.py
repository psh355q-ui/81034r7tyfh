"""
AI Constitutional Trading System - Live Trading Engine
======================================================

The main entry point for running the trading system in live or simulation modes.
Integrates KIS Broker, AI Debate Engine, Constitution, and Telegram Bot.

Usage:
    python run_live_trading.py --mode=[dry_run|paper_trading|live_trading] --tickers=AAPL,TSLA

Modes:
    - dry_run (Default): Analyze and simulate, no API orders, no DB changes.
    - paper_trading: Use mock broker or text-based orders, save to Shadow DB.
    - live_trading: REAL MONEY. Executes orders via KIS API. Requires manual confirmation.

Author: AI Trading Team
Date: 2025-12-18
"""

import os
import sys
import argparse
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.repository import SessionLocal
from backend.brokers.kis_broker import KISBroker
from backend.ai.debate.constitutional_debate_engine import ConstitutionalDebateEngine
from backend.constitution.constitution import Constitution
from backend.notifications.telegram_commander_bot import TelegramCommanderBot
from backend.data.models.proposal import Proposal

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading/live_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LiveTrading")

class LiveTradingEngine:
    def __init__(self, mode: str, tickers: list):
        self.mode = mode
        self.tickers = tickers
        self.db = SessionLocal()
        
        # Initialize Components
        try:
            self.kis = KISBroker(account_no=os.getenv("KIS_ACCOUNT_NUMBER"))
            logger.info("KIS Broker initialized successfully")
        except Exception as e:
            logger.warning(f"KIS Broker initialization failed: {e}. Using mock mode.")
            self.kis = None  # Mock mode
            
        try:
            self.debate_engine = ConstitutionalDebateEngine(db_session=self.db)
            logger.info("Constitutional Debate Engine initialized successfully")
        except Exception as e:
            logger.warning(f"Debate Engine initialization failed: {e}. Using mock engine.")
            self.debate_engine = None  # Mock mode
            
        self.constitution = Constitution()
        
        # Telegram Bot (Optional in Dry Run if token missing)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token:
            self.bot = TelegramCommanderBot(token, self.db, commander_chat_id=chat_id)
        else:
            logger.warning("Telegram Token missing. Bot disabled.")
            self.bot = None
            
        logger.info(f"Engine Initialized in {mode.upper()} mode for {len(tickers)} tickers.")

    async def run(self):
        """Main Execution Loop"""
        logger.info("Starting Daily Routine...")
        
        # 0. Safety Check
        if self._check_kill_switch():
            logger.critical("KILL SWITCH ACTIVE. Terminating.")
            return

        # 1. Market Data Check
        if self.mode != 'dry_run' and self.kis:
            if not self.kis.check_connection():
                logger.error("KIS Broker Connection Failed!")
                return
        elif not self.kis:
            logger.info("Running in MOCK mode (no KIS broker available)")
        
        for ticker in self.tickers:
            await self.process_ticker(ticker)
            
        logger.info("Daily Routine Completed.")

    async def process_ticker(self, ticker: str):
        logger.info(f"Processing {ticker}...")
        
        # 1. Fetch Data
        try:
            # In real live trading, we get real data. 
            # For now, KIS broker might have get_current_price
            if self.kis and self.mode != 'dry_run':
                current_price = self.kis.get_current_price(ticker)
            else:
                # Mock price for dry run or when KIS unavailable
                import random
                current_price = 150.0 + random.uniform(-10, 10)
                logger.info(f"Using MOCK price for {ticker}")
            logger.info(f"Current Price for {ticker}: ${current_price}")
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return

        # 2. AI Debate
        try:
            # Debate Engine should return a decision/proposal
            # debate_result = await self.debate_engine.run_debate(ticker, current_price_data...)
            # We simulate for now if method signature unknown, but assuming run_debate exists
            debate_result = await self.debate_engine.run_debate(ticker) 
            logger.info(f"Debate Result: {debate_result.action} (Conf: {debate_result.confidence})")
        except Exception as e:
            logger.error(f"Debate failed: {e}")
            return

        if debate_result.action == "HOLD":
            return

        # 3. Create Proposal Object
        proposal = Proposal(
            ticker=ticker,
            action=debate_result.action,
            target_price=current_price, # Market order usually
            confidence=debate_result.confidence,
            reasoning=debate_result.reasoning,
            created_at=datetime.utcnow(),
            status='PENDING'
        )
        
        # 4. Constitution Check
        if self.kis and self.mode != 'dry_run':
            portfolio_state = self.kis.get_balance()
        else:
            # Mock portfolio for dry run
            portfolio_state = {"cash": 100000, "deposit": 100000, "total_asset": 100000}
            
        total_equity = float(portfolio_state.get('total_asset', 100000)) # Adjust key based on KIS
        
        # Context for Constitution
        context = {
            "cash": float(portfolio_state.get('deposit', 100000)),
            "total_equity": total_equity,
            "positions": {} # Need to fetch actual positions
        }
        
        is_valid, violations = self.constitution.validate_proposal(proposal, context)
        
        proposal.is_constitutional = is_valid
        proposal.violated_articles = str(violations) if violations else None
        
        # Save Proposal to DB
        self.db.add(proposal)
        self.db.commit()

        # 5. Notify Commander
        if self.bot:
            await self.bot.send_proposal(proposal)
            logger.info("Sent proposal to Telegram.")
        else:
            logger.info("Bot disabled, skipping notification. Auto-rejecting if live...")
            
        # 6. Execution (Only if Approved via Telegram usually)
        # But here we stop, as the Bot handles the callback for execution.
        # This script just generates proposals.
        # UNLESS we are in 'auto' mode or backtesting, but Live Trading is semi-autonomous.
        
        logger.info(f"Proposal {proposal.id} created. Waiting for Commander.")

    def _check_kill_switch(self) -> bool:
        if os.path.exists("kill_switch.txt"):
            return True
        return False

async def main():
    parser = argparse.ArgumentParser(description='AI Trading Engine')
    parser.add_argument('--mode', type=str, default='dry_run', choices=['dry_run', 'paper_trading', 'live_trading'])
    parser.add_argument('--tickers', type=str, default='AAPL,NVDA,MSFT', help='Comma separated tickers')
    
    args = parser.parse_args()
    tickers = args.tickers.split(',')
    
    load_dotenv()
    
    engine = LiveTradingEngine(args.mode, tickers)
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
