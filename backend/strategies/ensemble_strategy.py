"""
Ensemble Strategy Manager

Purpose: Orchestrate 3-AI pipeline for optimal trading decisions
Pipeline: ChatGPT (Regime) → Gemini (Risk) → Claude (Decision)
Cost: ~$2.00/month total

Phase: 5 (Strategy Ensemble)
Task: 5 (Ensemble Integration)
Author: AI Trading System Team
Date: 2025-11-14
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# Ensemble Strategy Manager
# ============================================================================

class EnsembleStrategyManager:
    """
    Orchestrate multi-AI trading pipeline.
    
    Pipeline Stages:
    1. ChatGPT: Market Regime Detection (daily)
    2. Gemini: Risk Screening (100 → 50 stocks)
    3. Claude: Trading Decisions (50 stocks)
    
    Cost Breakdown:
    - ChatGPT: $0.03/day = $0.90/month
    - Gemini: $0.03/day = $0.90/month
    - Claude: $0.035/day = $1.05/month (50 stocks @ $0.0007/stock)
    - Total: ~$2.85/month
    
    Features:
    - Adaptive screening based on regime
    - Risk-adjusted position sizing
    - Failover mechanisms
    - Complete metrics tracking
    """
    
    def __init__(
        self,
        chatgpt_client=None,
        gemini_client=None,
        claude_client=None,
        redis_client=None,
        feature_store=None,
    ):
        """
        Initialize ensemble manager.
        
        Args:
            chatgpt_client: ChatGPT client for regime detection
            gemini_client: Gemini client for risk screening
            claude_client: Claude client for trading decisions
            redis_client: Redis for caching
            feature_store: Feature store for market data
        """
        self.chatgpt = chatgpt_client
        self.gemini = gemini_client
        self.claude = claude_client
        self.redis = redis_client
        self.feature_store = feature_store
        
        # Metrics
        self.metrics = {
            "total_runs": 0,
            "total_cost_usd": 0.0,
            "avg_pipeline_time_ms": 0.0,
            "stocks_analyzed": 0,
            "decisions_made": 0,
            "last_run": None,
            "last_regime": None,
        }
        
        # Configuration
        self.config = {
            "max_candidates": 100,
            "target_after_screening": 50,
            "critical_risk_threshold": 0.6,
            "high_risk_threshold": 0.3,
            "min_sector_weight": 0.8,
        }
        
        logger.info("Ensemble Strategy Manager initialized")
    
    async def run_full_pipeline(
        self,
        ticker_universe: List[str],
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Run complete 3-stage AI pipeline.
        
        Args:
            ticker_universe: List of tickers to analyze (up to 100)
            force_refresh: Skip all caching
        
        Returns:
            Dict containing:
                - regime: Current market regime
                - screened_stocks: Stocks after risk screening
                - decisions: Trading decisions for each stock
                - metrics: Pipeline performance metrics
                - total_cost_usd: Total cost of this run
        """
        import time
        start_time = time.time()
        
        logger.info(
            "Starting ensemble pipeline with %d stocks",
            len(ticker_universe)
        )
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "input_stocks": len(ticker_universe),
            "regime": None,
            "screened_stocks": [],
            "decisions": [],
            "stage_costs": {},
            "total_cost_usd": 0.0,
            "pipeline_time_ms": 0.0,
            "errors": [],
        }
        
        try:
            # Stage 1: Market Regime Detection (ChatGPT)
            regime_result = await self._stage1_regime_detection(force_refresh)
            result["regime"] = regime_result["regime"]
            result["regime_confidence"] = regime_result.get("confidence", 0.5)
            result["stage_costs"]["chatgpt"] = regime_result.get("cost_usd", 0.0)
            
            # Stage 2: Risk Screening (Gemini)
            screened = await self._stage2_risk_screening(
                ticker_universe,
                regime_result["regime"],
                force_refresh
            )
            result["screened_stocks"] = screened["stocks"]
            result["stage_costs"]["gemini"] = screened.get("cost_usd", 0.0)
            
            # Stage 3: Trading Decisions (Claude)
            decisions = await self._stage3_trading_decisions(
                screened["stocks"],
                regime_result
            )
            result["decisions"] = decisions["decisions"]
            result["stage_costs"]["claude"] = decisions.get("cost_usd", 0.0)
            
            # Calculate total cost
            result["total_cost_usd"] = sum(result["stage_costs"].values())
            
            # Calculate pipeline time
            pipeline_time_ms = (time.time() - start_time) * 1000
            result["pipeline_time_ms"] = pipeline_time_ms
            
            # Update metrics
            self._update_metrics(result)
            
            logger.info(
                "Pipeline complete: %d stocks → %d screened → %d decisions, "
                "Cost: $%.4f, Time: %.1fms",
                len(ticker_universe),
                len(screened["stocks"]),
                len(decisions["decisions"]),
                result["total_cost_usd"],
                pipeline_time_ms
            )
            
        except Exception as e:
            logger.error("Pipeline error: %s", str(e))
            result["errors"].append(str(e))
            result["pipeline_time_ms"] = (time.time() - start_time) * 1000
        
        return result
    
    async def _stage1_regime_detection(
        self,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Stage 1: Detect market regime using ChatGPT.
        
        Cost: $0.03/call (cached 24 hours)
        """
        logger.info("Stage 1: Market Regime Detection (ChatGPT)")
        
        if not self.chatgpt:
            logger.warning("ChatGPT client not available, using fallback")
            return {
                "regime": "SIDEWAYS",
                "confidence": 0.5,
                "cost_usd": 0.0,
                "fallback": True,
            }
        
        # Get market data
        if self.feature_store:
            market_data = await self._get_market_data_from_store()
        else:
            market_data = self._get_default_market_data()
        
        # Detect regime
        regime_result = await self.chatgpt.detect_regime(
            market_data,
            force_refresh=force_refresh
        )
        
        logger.info(
            "Regime: %s (confidence: %.2f)",
            regime_result["regime"],
            regime_result.get("confidence", 0.5)
        )
        
        return regime_result
    
    async def _stage2_risk_screening(
        self,
        tickers: List[str],
        regime: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Stage 2: Screen stocks using Gemini for risk assessment.
        
        Cost: $0.0003/stock = $0.03/day for 100 stocks
        """
        logger.info("Stage 2: Risk Screening (Gemini)")
        
        result = {
            "stocks": [],
            "cost_usd": 0.0,
            "screened_out": 0,
        }
        
        if not self.gemini:
            logger.warning("Gemini client not available, using all stocks")
            result["stocks"] = tickers[:self.config["target_after_screening"]]
            return result
        
        # Screen each stock for risk
        screened_stocks = []
        total_cost = 0.0
        
        for ticker in tickers[:self.config["max_candidates"]]:
            try:
                # Get news for risk screening
                news_headlines = await self._get_news_headlines(ticker)
                
                # Screen risk with Gemini
                risk_result = await self.gemini.screen_risk(
                    ticker=ticker,
                    news_headlines=news_headlines,
                    recent_events=[]  # Could add recent events here
                )
                
                total_cost += risk_result.get("cost_usd", 0.0003)
                
                # Check risk thresholds
                risk_score = risk_result.get("risk_score", 0.0)
                
                if risk_score >= self.config["critical_risk_threshold"]:
                    logger.debug(
                        "%s excluded (CRITICAL risk: %.2f)",
                        ticker,
                        risk_score
                    )
                    result["screened_out"] += 1
                    continue
                
                # Add sector info for regime-based filtering
                sector = await self._get_stock_sector(ticker)
                
                screened_stocks.append({
                    "ticker": ticker,
                    "risk_score": risk_score,
                    "risk_level": risk_result.get("risk_level", "MODERATE"),
                    "sector": sector,
                    "categories": risk_result.get("categories", {}),
                })
                
            except Exception as e:
                logger.warning("Error screening %s: %s", ticker, str(e))
                # Include on error to be conservative
                screened_stocks.append({
                    "ticker": ticker,
                    "risk_score": 0.5,
                    "risk_level": "UNKNOWN",
                    "sector": "Unknown",
                    "categories": {},
                })
        
        # Apply regime-based sector filtering
        if self.chatgpt:
            from chatgpt_client import RegimeBasedScreener
            screener = RegimeBasedScreener(self.chatgpt)
            screened_stocks = await screener.filter_by_regime(
                screened_stocks,
                regime,
                min_weight=self.config["min_sector_weight"]
            )
        
        # Sort by risk score (lowest first) and take top N
        screened_stocks.sort(key=lambda x: x["risk_score"])
        result["stocks"] = screened_stocks[:self.config["target_after_screening"]]
        result["cost_usd"] = total_cost
        
        logger.info(
            "Screened: %d → %d stocks (cost: $%.4f)",
            len(tickers),
            len(result["stocks"]),
            total_cost
        )
        
        return result
    
    async def _stage3_trading_decisions(
        self,
        screened_stocks: List[Dict[str, Any]],
        regime_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 3: Generate trading decisions using Claude.
        
        Cost: $0.0007/stock = $0.035/day for 50 stocks
        """
        logger.info("Stage 3: Trading Decisions (Claude)")
        
        result = {
            "decisions": [],
            "cost_usd": 0.0,
        }
        
        if not self.claude:
            logger.warning("Claude client not available, using HOLD for all")
            for stock in screened_stocks:
                result["decisions"].append({
                    "ticker": stock["ticker"],
                    "action": "HOLD",
                    "conviction": 0.0,
                    "reasoning": "Claude client not available",
                })
            return result
        
        regime = regime_result.get("regime", "SIDEWAYS")
        sector_weights = regime_result.get("sector_weights", {})
        
        # Process each stock
        total_cost = 0.0
        
        for stock in screened_stocks:
            ticker = stock["ticker"]
            sector = stock.get("sector", "Unknown")
            risk_score = stock.get("risk_score", 0.0)
            
            try:
                # Get stock features
                if self.feature_store:
                    features = await self.feature_store.get_features(ticker)
                else:
                    features = self._get_default_features(ticker)
                
                # Add regime context to features
                features["market_regime"] = regime
                features["regime_confidence"] = regime_result.get("confidence", 0.5)
                features["sector_weight"] = sector_weights.get(sector, 1.0)
                features["risk_score"] = risk_score
                features["risk_level"] = stock.get("risk_level", "MODERATE")
                
                # Get Claude decision
                decision = await self.claude.analyze(ticker, features)
                
                # Adjust position size based on regime and risk
                if "position_size" in decision:
                    decision["position_size"] = self._adjust_position_size(
                        decision["position_size"],
                        regime,
                        sector,
                        risk_score
                    )
                
                total_cost += decision.get("cost_usd", 0.0007)
                result["decisions"].append(decision)
                
            except Exception as e:
                logger.warning("Error analyzing %s: %s", ticker, str(e))
                result["decisions"].append({
                    "ticker": ticker,
                    "action": "HOLD",
                    "conviction": 0.0,
                    "reasoning": f"Error: {str(e)}",
                })
        
        result["cost_usd"] = total_cost
        
        logger.info(
            "Decisions: %d stocks analyzed (cost: $%.4f)",
            len(result["decisions"]),
            total_cost
        )
        
        return result
    
    def _adjust_position_size(
        self,
        base_size: float,
        regime: str,
        sector: str,
        risk_score: float
    ) -> float:
        """
        Adjust position size based on regime, sector, and risk.
        
        Adjustments:
        1. Regime-based sector weight
        2. Risk-based reduction for HIGH risk
        3. CRASH regime reduces all positions
        """
        adjusted = base_size
        
        # 1. Regime-based sector adjustment
        if self.chatgpt:
            sector_weight = self.chatgpt.get_sector_weight(regime, sector)
            adjusted *= sector_weight
        
        # 2. Risk-based adjustment
        if risk_score >= self.config["high_risk_threshold"]:
            # Reduce by 50% for HIGH risk
            adjusted *= 0.5
            logger.debug(
                "Reduced position for HIGH risk (%.2f)",
                risk_score
            )
        
        # 3. CRASH regime reduces all
        if regime == "CRASH":
            adjusted *= 0.3  # 70% reduction
            logger.debug("CRASH regime: position reduced to 30%")
        
        return adjusted
    
    async def _get_market_data_from_store(self) -> Dict[str, Any]:
        """Get market data from feature store."""
        # This would integrate with your actual feature store
        # For now, return default data
        return self._get_default_market_data()
    
    def _get_default_market_data(self) -> Dict[str, Any]:
        """Get default market data for testing."""
        return {
            "spy_price": 490.00,
            "spy_50ma": 485.00,
            "spy_200ma": 470.00,
            "vix": 18.5,
            "vix_percentile": 45.0,
            "recent_returns": {
                "1d": 0.25,
                "5d": 1.20,
                "20d": 2.80,
                "60d": 6.50,
            },
            "credit_spreads": {
                "investment_grade_spread": 1.35,
                "high_yield_spread": 3.80,
            },
            "economic_indicators": {
                "unemployment_rate": 4.0,
                "gdp_growth": 2.6,
                "inflation_rate": 3.1,
                "consumer_sentiment": 71.0,
            },
            "earnings_season": {
                "beat_rate": 68.0,
                "avg_surprise": 4.5,
            },
        }
    
    async def _get_news_headlines(self, ticker: str) -> List[str]:
        """Get news headlines for a stock."""
        # This would integrate with NewsAPI or similar
        # For now, return empty list
        return []
    
    async def _get_stock_sector(self, ticker: str) -> str:
        """Get stock's sector."""
        # This would integrate with your data source
        # For now, return placeholder
        sector_map = {
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology",
            "AMZN": "Consumer Discretionary",
            "TSLA": "Consumer Discretionary",
            "JNJ": "Healthcare",
            "UNH": "Healthcare",
            "JPM": "Financials",
            "V": "Financials",
            "XOM": "Energy",
            "NEE": "Utilities",
            "PG": "Consumer Staples",
        }
        return sector_map.get(ticker, "Unknown")
    
    def _get_default_features(self, ticker: str) -> Dict[str, Any]:
        """Get default features for testing."""
        return {
            "ticker": ticker,
            "current_price": 100.0,
            "pe_ratio": 25.0,
            "market_cap": 100e9,
            "volume": 10000000,
            "rsi_14": 55.0,
            "macd": 0.5,
            "bollinger_position": 0.6,
        }
    
    def _update_metrics(self, result: Dict[str, Any]):
        """Update internal metrics."""
        self.metrics["total_runs"] += 1
        self.metrics["total_cost_usd"] += result["total_cost_usd"]
        self.metrics["stocks_analyzed"] += len(result["screened_stocks"])
        self.metrics["decisions_made"] += len(result["decisions"])
        self.metrics["last_run"] = datetime.utcnow().isoformat()
        self.metrics["last_regime"] = result["regime"]
        
        # Update average pipeline time
        n = self.metrics["total_runs"]
        old_avg = self.metrics["avg_pipeline_time_ms"]
        new_time = result["pipeline_time_ms"]
        self.metrics["avg_pipeline_time_ms"] = old_avg + (new_time - old_avg) / n
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        daily_cost = self.metrics["total_cost_usd"] / max(1, self.metrics["total_runs"])
        monthly_cost = daily_cost * 30
        
        return {
            "total_cost_usd": self.metrics["total_cost_usd"],
            "total_runs": self.metrics["total_runs"],
            "avg_cost_per_run": daily_cost,
            "estimated_monthly_cost": monthly_cost,
            "cost_breakdown": {
                "chatgpt_monthly": 0.90,  # $0.03/day * 30
                "gemini_monthly": 0.90,   # $0.03/day * 30
                "claude_monthly": 1.05,   # $0.035/day * 30
                "total_estimated": 2.85,
            },
        }


# ============================================================================
# Quick Actions
# ============================================================================

class QuickActions:
    """
    Quick action shortcuts for common operations.
    """
    
    def __init__(self, ensemble_manager: EnsembleStrategyManager):
        self.manager = ensemble_manager
    
    async def morning_analysis(self, watchlist: List[str]) -> Dict[str, Any]:
        """
        Run morning analysis before market open.
        
        Called: 9:00 AM EST
        """
        logger.info("Running morning analysis...")
        return await self.manager.run_full_pipeline(watchlist)
    
    async def quick_check(self, ticker: str) -> Dict[str, Any]:
        """
        Quick check for a single stock.
        """
        logger.info("Quick check for %s", ticker)
        result = await self.manager.run_full_pipeline([ticker])
        
        if result["decisions"]:
            return result["decisions"][0]
        return {"ticker": ticker, "action": "HOLD", "reasoning": "No decision"}
    
    async def regime_check(self) -> Dict[str, Any]:
        """
        Check current market regime only.
        """
        logger.info("Checking market regime...")
        return await self.manager._stage1_regime_detection(force_refresh=False)
    
    async def risk_scan(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """
        Scan stocks for risk only (no trading decisions).
        """
        logger.info("Running risk scan on %d stocks", len(tickers))
        
        regime_result = await self.manager._stage1_regime_detection()
        screening_result = await self.manager._stage2_risk_screening(
            tickers,
            regime_result["regime"],
            force_refresh=False
        )
        
        return screening_result["stocks"]


if __name__ == "__main__":
    print("Ensemble Strategy Manager")
    print("=" * 50)
    print("3-AI Pipeline: ChatGPT → Gemini → Claude")
    print("\nCost Breakdown:")
    print("  ChatGPT (Regime): $0.90/month")
    print("  Gemini (Risk):    $0.90/month")
    print("  Claude (Trade):   $1.05/month")
    print("  Total:            $2.85/month")
    print("\nPipeline:")
    print("  100 stocks → Risk Screen → 50 stocks → Decisions")
