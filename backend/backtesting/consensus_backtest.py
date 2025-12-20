import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.backtesting.backtest_engine import BacktestEngine, BacktestPosition
from backend.backtesting.consensus_performance_analyzer import ConsensusPerformanceAnalyzer

logger = logging.getLogger(__name__)

class ConsensusBacktest:
    """
    Consensus Strategy Backtest Runner
    
    Simulates the consensus strategy over historical data:
    1. Iterates through historical dates
    2. Generates mock consensus signals (or loads real ones if available)
    3. Executes trades via BacktestEngine
    4. Tracks performance and DCA logic
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        consensus_threshold: float = 0.6,  # 60% approval needed
        use_mock_consensus: bool = True
    ):
        self.engine = BacktestEngine(initial_capital=initial_capital)
        self.analyzer = ConsensusPerformanceAnalyzer()
        self.consensus_threshold = consensus_threshold
        self.use_mock_consensus = use_mock_consensus
        
        # Track Consensus Stats
        self.consensus_stats = {
            "total_signals": 0,
            "approved": 0,
            "rejected": 0,
            "approval_rate": 0.0
        }
        
        # Mock AI Models
        self.ai_models = ["Claude", "ChatGPT", "Gemini"]
        
    async def run(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ):
        """Run the backtest simulation"""
        logger.info(f"Starting Consensus Backtest: {start_date.date()} ~ {end_date.date()}")
        
        # 1. Generate Trading Days
        trading_days = self.engine._generate_trading_days(start_date, end_date)
        
        # 2. Simulation Loop
        for current_date in trading_days:
            # 2.1 Get Market Data (Mock or Real)
            market_data = await self.engine._get_market_data(tickers, current_date, None)
            
            # 2.2 Update Portfolio (Mark to Market)
            self.engine._update_portfolio_values(current_date, market_data)
            
            # 2.3 Generate & Process Signals
            for ticker in tickers:
                if ticker not in market_data:
                    continue
                    
                current_price = market_data[ticker]["close"]
                
                # Check DCA Conditions for existing positions
                if ticker in self.engine.positions:
                    await self._check_dca_condition(ticker, current_price, current_date)
                    continue
                
                # Check New Entry Signals
                signal = await self._generate_consensus_signal(ticker, current_date, market_data)
                
                # Update stats
                self.consensus_stats["total_signals"] += 1
                if signal["approved"]:
                    self.consensus_stats["approved"] += 1
                else:
                    self.consensus_stats["rejected"] += 1
                
                if signal["approved"]:
                    # Execute BUY
                    decision = self._create_buy_decision(signal)
                    self.engine._execute_trade(ticker, decision, current_price, current_date)
            
            # 2.4 Record Daily Snapshot
            self._record_snapshot(current_date, market_data)
        
        # Finalize stats
        total = self.consensus_stats["total_signals"]
        self.consensus_stats["approval_rate"] = self.consensus_stats["approved"] / total if total > 0 else 0
            
        # 3. Generate Final Report
        return self._generate_report()
            
    async def _generate_consensus_signal(self, ticker, date, market_data):
        """Generate a consensus signal (Mock or Real)"""
        
        # 1. Real Consensus Engine Logic
        if not self.use_mock_consensus:
            try:
                from backend.ai.consensus.consensus_engine import get_consensus_engine
                from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment
                
                # Get Singleton Engine
                engine = get_consensus_engine()
                
                # Construct Market Context from Backtest Data
                # Note: Backtest might not have news, so we use minimal context or synthetic
                # For Phase F, we focus on Price/Technical context potentially.
                ticker_data = market_data.get(ticker, {})
                current_price = ticker_data.get("close", 0)
                
                # Create Context
                context = MarketContext(
                    ticker=ticker,
                    company_name=ticker, # Simplified
                    current_price=current_price,
                    # We could add simulated news or fetch if available
                    news=None 
                )
                
                # Additional info for voting
                info = {
                    "date": date.strftime("%Y-%m-%d"),
                    "price": current_price,
                    "volume": ticker_data.get("volume", 0)
                }
                
                # Execute Vote
                # This calls real AI clients (slow!)
                result = await engine.vote_on_signal(context, "BUY", additional_info=info)
                
                # Convert to Backtest format
                return {
                    "ticker": ticker,
                    "date": date,
                    "votes": [
                        {"model": v.ai_model, "vote": v.decision.value} 
                        for v in result.votes.values()
                    ],
                    "approval_rate": result.approve_count / len(result.votes) if result.votes else 0,
                    "approved": result.approved
                }
                
            except Exception as e:
                logger.error(f"Real consensus failed for {ticker}: {e}")
                # Fallback to mock if real fails
                pass

        # 2. Mock Logic (Fallback)
        votes = []
        for model in self.ai_models:
            # Random vote: BUY (1), HOLD (0), SELL (-1)
            # Biased slightly towards BUY for testing
            vote = np.random.choice(["BUY", "HOLD"], p=[0.4, 0.6])
            votes.append({"model": model, "vote": vote})
            
        buy_votes = len([v for v in votes if v["vote"] == "BUY"])
        approval_rate = buy_votes / len(votes)
        
        return {
            "ticker": ticker,
            "date": date,
            "votes": votes,
            "approval_rate": approval_rate,
            "approved": approval_rate >= self.consensus_threshold
        }

    async def _check_dca_condition(self, ticker, current_price, current_date):
        """Check if DCA is needed for a losing position"""
        position = self.engine.positions[ticker]
        entry_price = position.avg_entry_price
        
        # If price dropped > 5% and we have DCA capacity
        if current_price < entry_price * 0.95:
             # Mock DCA Approval
             if np.random.random() > 0.5:
                 # Execute DCA (Add to position)
                 decision = self._create_dca_decision()
                 self.engine._execute_trade(ticker, decision, current_price, current_date)

    def _create_buy_decision(self, signal):
        class Decision:
            action = "BUY"
            conviction = signal["approval_rate"]
            position_size = 10 # 10% of portfolio
            stop_loss = None
        return Decision()
        
    def _create_dca_decision(self):
        class Decision:
            action = "BUY" # BacktestEngine treats DCA as BUY for now
            conviction = 1.0
            position_size = 5 # 5% for DCA
            stop_loss = None
        return Decision()

    def _record_snapshot(self, date, market_data):
        """Record daily portfolio state"""
        from backend.backtesting.backtest_engine import DailySnapshot
        
        equity = self.engine._calculate_total_equity(market_data)
        self.engine.equity_curve.append((date, equity))
        
        positions_val = equity - self.engine.cash
        prev_equity = self.engine.snapshots[-1].portfolio_value if self.engine.snapshots else self.engine.initial_capital
        daily_ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0
        
        self.engine.snapshots.append(DailySnapshot(
            date=date,
            portfolio_value=equity,
            cash=self.engine.cash,
            positions_value=positions_val,
            positions_count=len(self.engine.positions),
            unrealized_pnl=self.engine._calculate_unrealized_pnl(market_data),
            realized_pnl=sum(p.realized_pnl for p in self.engine.closed_positions),
            total_pnl=equity - self.engine.initial_capital,
            daily_return=daily_ret
        ))
    
    def _generate_report(self):
        """Generate comprehensive report using Analyzer"""
        # Get Engine Metrics
        engine_metrics = self.engine._calculate_performance_metrics()
        
        # Add Consensus Metrics
        engine_metrics["consensus"] = self.consensus_stats
        
        # Run Analyzer
        return self.analyzer.analyze(engine_metrics)
