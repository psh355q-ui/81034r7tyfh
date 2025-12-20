"""
Constitutional Backtest Engine.

The core engine that integrates the Constitution, Trading Agents, and Logic 
to simulate a safety-first AI trading strategy.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd

from backend.constitution.constitution import Constitution
from backend.data.models.proposal import Proposal
from backend.data.models.shadow_trade import ShadowTrade
from backend.backtesting.portfolio_manager import PortfolioManager
from backend.backtesting.shadow_trade_tracker import ShadowTradeTracker

logger = logging.getLogger(__name__)

class ConstitutionalBacktestEngine:
    """
    Backtest Engine with Constitutional Guardrails.
    
    Flow:
    1. Market Data -> AI Agents -> Trading Proposal
    2. Proposal -> Constitution -> Validation
    3. If Valid -> Portfolio Manager -> Execute Trade
    4. If Invalid -> Shadow Trade Tracker -> Track 'What If'
    """
    
    def __init__(
        self,
        constitution: Constitution,
        initial_capital: float = 100000.0,
    ):
        self.constitution = constitution
        self.portfolio = PortfolioManager(initial_capital=initial_capital)
        self.shadow_tracker = ShadowTradeTracker()
        self.history: List[Dict] = []
        
    async def run(
        self,
        trading_agent, # Function or Class that returns a decision
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        feature_store = None # Optional data source
    ) -> Dict:
        """
        Run the Backtest.
        """
        logger.info(f"Starting Constitutional Backtest: {start_date.date()} to {end_date.date()}")
        
        current_date = start_date
        # Simple daily loop
        while current_date <= end_date:
            if current_date.weekday() >= 5: # Skip weekends
                current_date += timedelta(days=1)
                continue
                
            logger.info(f"Simulating {current_date.date()}...")
            
            # 1. Get Market Data (Mock or Real)
            market_data = await self._get_market_data(tickers, current_date)
            
            # 2. Update Portfolio & Shadow Trades
            current_prices = {t: d['close'] for t, d in market_data.items()}
            self.portfolio.update_mark_to_market(current_date, current_prices)
            self.shadow_tracker.update(current_date, current_prices)
            
            # 3. AI Analysis & Trading
            for ticker in tickers:
                if ticker not in market_data:
                    continue
                    
                # A. Generate Proposal
                try:
                    # Mocking agent response if it's a mock test, otherwise call agent
                    decision = await trading_agent.analyze(ticker, current_date=current_date) 
                    # decision expected to have: action, conviction, rationale, etc.
                except Exception as e:
                    logger.error(f"Agent failed for {ticker}: {e}")
                    continue
                
                if decision.action == "HOLD":
                    continue
                    
                # Create Proposal Object
                proposal_price = market_data[ticker]['close']
                proposal = Proposal(
                    ticker=ticker,
                    action=decision.action,
                    price=proposal_price,
                    confidence=decision.conviction,
                    rationale=decision.rationale,
                    created_at=current_date
                )
                
                # B. Constitutional Validation
                # We need to calculate potential position size to check risk limits
                # For simplicity, assume a standard size or ask agent
                # In robust system, `allocation_rules` determines size.
                
                # Let's say we want to buy 5% of equity (just for validation check)
                target_value = self.portfolio.get_current_equity(current_prices) * 0.05
                shares = int(target_value / proposal_price) if decision.action == "BUY" else 0
                
                # Need Portfolio Context for Constitution
                portfolio_context = {
                    "cash": self.portfolio.cash,
                    "total_equity": self.portfolio.get_current_equity(current_prices),
                    "positions": self.portfolio.positions
                }
                
                is_valid, violations = self.constitution.validate_proposal(
                    proposal, 
                    portfolio_context
                )
                
                # C. Execution or Rejection
                if is_valid:
                    # Approved!
                    success = self.portfolio.execute_trade(
                        ticker=ticker,
                        action=decision.action,
                        amount=shares if decision.action == "BUY" else self.portfolio.positions.get(ticker, {}).get('shares', 0), # Sell all if sell?
                        price=proposal_price,
                        date=current_date,
                        reason="Constitutional Approval"
                    )
                    if success:
                        logger.info(f"Executed {decision.action} {ticker}")
                else:
                    # Rejected! -> Shadow Trade
                    logger.info(f"Rejected {decision.action} {ticker}: {violations}")
                    
                    shadow_trade = ShadowTrade(
                        ticker=ticker,
                        action=decision.action,
                        entry_price=proposal_price,
                        shares=shares if decision.action == "BUY" else 0, # If SELL reject, we track 'holding' impact? 
                        # Tracking SELL rejection is tricky. If we wanted to sell but were forced to hold.
                        # Then 'Shadow Trade' is effectively 'Holding'.
                        # PnL of shadow trade = (Current - Entry) for BUY.
                        # For SELL REJECT: We KEEP the position. PnL impact is diff. 
                        # Simplified: Track BUY rejections mostly for 'Defensive' metrics.
                        rejection_reason=str(violations),
                        violated_articles=str(violations),
                        created_at=current_date,
                        tracking_days=7
                    )
                    self.shadow_tracker.add_trade(shadow_trade)

            current_date += timedelta(days=1)
            
        return self._generate_report()

    async def _get_market_data(self, tickers, date):
        # Placeholder for data fetching
        # In real impl, check `backtest_engine.py` for standard implementation or Fetcher
        import random
        data = {}
        for t in tickers:
            base = 100.0 if t == 'AAPL' else 200.0
            # Mock random walk
            price = base * (1 + random.uniform(-0.05, 0.05)) 
            data[t] = {"close": price, "open": price, "high": price, "low": price, "volume": 1000}
        return data

    def _generate_report(self):
        """Combine Portfolio and Shadow metrics."""
        port_metrics = self.portfolio.get_metrics()
        shadow_metrics = self.shadow_tracker.get_metrics()
        
        return {
            "portfolio": port_metrics,
            "shadow": shadow_metrics,
            "constitution": {
                "total_proposals": port_metrics.get('total_trades', 0) + shadow_metrics.get('total_shadow_trades', 0),
                "rejected_proposals": shadow_metrics.get('total_shadow_trades', 0)
            }
        }
