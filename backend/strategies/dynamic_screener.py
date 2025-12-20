"""
Dynamic Stock Screener with Risk-Based Filtering

Purpose: Filter 100 stocks → 50 stocks using Gemini risk screening
Cost: $0.03/day (100 stocks × $0.0003)

Priority System:
1. Portfolio Holdings (highest priority, always included)
2. Watchlist (user-defined stocks)
3. Top Market Cap (S&P 500 by market cap)

Risk Filtering:
- CRITICAL risk (≥0.6): Filter out
- HIGH risk (0.3-0.6): Include but flag
- MODERATE/LOW (< 0.3): Include normally

Phase: 5 (Strategy Ensemble)
Task: 3 (Dynamic Screener)
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StockPriority(Enum):
    """Stock priority levels"""
    PORTFOLIO = 1      # Current holdings (highest priority)
    WATCHLIST = 2      # User watchlist
    TOP_MARKET_CAP = 3 # Top S&P 500 by market cap


@dataclass
class StockCandidate:
    """Stock candidate for screening"""
    ticker: str
    priority: StockPriority
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    
    def __lt__(self, other):
        """Comparison for sorting"""
        # Primary: priority (lower number = higher priority)
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        
        # Secondary: risk score (lower risk = higher priority)
        if self.risk_score is not None and other.risk_score is not None:
            return self.risk_score < other.risk_score
        
        # Tertiary: market cap (higher = higher priority)
        if self.market_cap is not None and other.market_cap is not None:
            return self.market_cap > other.market_cap
        
        return self.ticker < other.ticker


class DynamicScreener:
    """
    Dynamic stock screener with Gemini risk-based filtering.
    
    Workflow:
    1. Collect candidates (portfolio + watchlist + top market cap)
    2. Screen risks using Gemini (parallel processing)
    3. Filter CRITICAL risks (≥0.6)
    4. Sort by priority + risk score
    5. Return top 50 stocks
    """
    
    def __init__(self):
        """Initialize screener"""
        # Lazy import to avoid circular dependencies
        self.gemini_client = None
        self.feature_store = None
        
        # Metrics
        self.metrics = {
            "total_candidates": 0,
            "filtered_critical": 0,
            "filtered_high": 0,
            "final_count": 0,
            "gemini_calls": 0,
            "gemini_cost": 0.0,
            "screening_time_ms": 0.0,
        }
        
        logger.info("DynamicScreener initialized")
    
    async def screen(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
        top_market_cap_tickers: List[str],
        target_count: int = 50,
        max_risk_score: float = 0.6,  # Filter CRITICAL
    ) -> List[StockCandidate]:
        """
        Screen stocks and return top candidates.
        
        Args:
            portfolio_tickers: Current holdings (always included)
            watchlist_tickers: User watchlist
            top_market_cap_tickers: Top market cap stocks
            target_count: Target number of stocks (default 50)
            max_risk_score: Maximum acceptable risk score (default 0.6)
        
        Returns:
            List of StockCandidate (sorted by priority + risk)
        """
        start_time = datetime.now()
        
        logger.info(f"Starting screening: portfolio={len(portfolio_tickers)}, "
                   f"watchlist={len(watchlist_tickers)}, "
                   f"top_market_cap={len(top_market_cap_tickers)}")
        
        # Step 1: Collect candidates
        candidates = self._collect_candidates(
            portfolio_tickers,
            watchlist_tickers,
            top_market_cap_tickers,
        )
        
        self.metrics["total_candidates"] = len(candidates)
        logger.info(f"Total candidates: {len(candidates)}")
        
        # Step 2: Screen risks (parallel processing)
        candidates = await self._screen_risks(candidates)
        
        # Step 3: Filter CRITICAL risks
        candidates = self._filter_critical_risks(candidates, max_risk_score)
        
        # Step 4: Sort by priority + risk
        candidates = self._sort_candidates(candidates)
        
        # Step 5: Select top N
        final_candidates = candidates[:target_count]
        
        self.metrics["final_count"] = len(final_candidates)
        self.metrics["screening_time_ms"] = (
            (datetime.now() - start_time).total_seconds() * 1000
        )
        
        logger.info(f"Screening complete: {len(final_candidates)} stocks selected "
                   f"({self.metrics['screening_time_ms']:.0f}ms)")
        
        return final_candidates
    
    def _collect_candidates(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
        top_market_cap_tickers: List[str],
    ) -> List[StockCandidate]:
        """
        Collect candidates from 3 sources.
        
        Deduplication: If same ticker in multiple sources, use highest priority
        """
        candidates = []
        seen = set()
        
        # Priority 1: Portfolio holdings
        for ticker in portfolio_tickers:
            if ticker not in seen:
                candidates.append(StockCandidate(
                    ticker=ticker,
                    priority=StockPriority.PORTFOLIO,
                ))
                seen.add(ticker)
        
        # Priority 2: Watchlist
        for ticker in watchlist_tickers:
            if ticker not in seen:
                candidates.append(StockCandidate(
                    ticker=ticker,
                    priority=StockPriority.WATCHLIST,
                ))
                seen.add(ticker)
        
        # Priority 3: Top market cap
        for ticker in top_market_cap_tickers:
            if ticker not in seen:
                candidates.append(StockCandidate(
                    ticker=ticker,
                    priority=StockPriority.TOP_MARKET_CAP,
                ))
                seen.add(ticker)
        
        logger.info(f"Collected {len(candidates)} unique candidates")
        
        return candidates
    
    async def _screen_risks(
        self,
        candidates: List[StockCandidate],
    ) -> List[StockCandidate]:
        """
        Screen risks for all candidates (parallel processing).
        
        Performance:
        - 100 stocks × 500ms = 50 seconds (sequential)
        - 100 stocks / 10 concurrent = 5 seconds (parallel)
        """
        # Lazy import Gemini client
        if self.gemini_client is None:
            try:
                from ai.gemini_client import GeminiClient
                self.gemini_client = GeminiClient()
            except ImportError:
                logger.warning("Gemini client not available, using mock risk scores")
                # Mock risk scores for testing
                for candidate in candidates:
                    candidate.risk_score = 0.2  # LOW risk
                    candidate.risk_level = "LOW"
                return candidates
        
        # Parallel screening (10 concurrent)
        semaphore = asyncio.Semaphore(10)
        
        async def screen_one(candidate: StockCandidate):
            async with semaphore:
                try:
                    # Get news headlines
                    news = await self._get_news(candidate.ticker)
                    
                    # Screen risk with Gemini
                    result = await self.gemini_client.screen_risk(
                        ticker=candidate.ticker,
                        news_headlines=news,
                        recent_events=[],
                    )
                    
                    # Update candidate
                    candidate.risk_score = result["risk_score"]
                    candidate.risk_level = result["risk_level"]
                    
                    # Update metrics
                    self.metrics["gemini_calls"] += 1
                    self.metrics["gemini_cost"] += 0.0003
                    
                    logger.debug(f"{candidate.ticker}: {candidate.risk_level} ({candidate.risk_score:.2f})")
                
                except Exception as e:
                    logger.error(f"Error screening {candidate.ticker}: {e}")
                    # Conservative default on error
                    candidate.risk_score = 0.5
                    candidate.risk_level = "MODERATE"
        
        # Execute parallel screening
        await asyncio.gather(*[screen_one(c) for c in candidates])
        
        logger.info(f"Risk screening complete: {self.metrics['gemini_calls']} calls, "
                   f"${self.metrics['gemini_cost']:.2f}")
        
        return candidates
    
    def _filter_critical_risks(
        self,
        candidates: List[StockCandidate],
        max_risk_score: float,
    ) -> List[StockCandidate]:
        """
        Filter out CRITICAL risk stocks.
        
        Rules:
        - CRITICAL (≥0.6): Filter out (except portfolio holdings)
        - HIGH (0.3-0.6): Include but flag
        - MODERATE/LOW (< 0.3): Include normally
        """
        filtered = []
        
        for candidate in candidates:
            # Always keep portfolio holdings (already invested)
            if candidate.priority == StockPriority.PORTFOLIO:
                filtered.append(candidate)
                continue
            
            # Filter CRITICAL risks
            if candidate.risk_score is not None and candidate.risk_score >= max_risk_score:
                self.metrics["filtered_critical"] += 1
                logger.info(f"Filtered CRITICAL risk: {candidate.ticker} ({candidate.risk_score:.2f})")
                continue
            
            # Flag HIGH risks
            if candidate.risk_score is not None and candidate.risk_score >= 0.3:
                self.metrics["filtered_high"] += 1
                logger.debug(f"HIGH risk flagged: {candidate.ticker} ({candidate.risk_score:.2f})")
            
            filtered.append(candidate)
        
        logger.info(f"Filtered {self.metrics['filtered_critical']} CRITICAL risks, "
                   f"{len(filtered)} candidates remaining")
        
        return filtered
    
    def _sort_candidates(
        self,
        candidates: List[StockCandidate],
    ) -> List[StockCandidate]:
        """
        Sort candidates by priority + risk score.
        
        Sort order:
        1. Portfolio holdings (priority 1)
        2. Watchlist (priority 2)
        3. Top market cap (priority 3)
        
        Within each priority: lower risk = higher rank
        """
        sorted_candidates = sorted(candidates)
        
        logger.info(f"Sorted {len(sorted_candidates)} candidates")
        
        return sorted_candidates
    
    async def _get_news(self, ticker: str) -> List[str]:
        """
        Get news headlines for risk screening.
        
        Uses NewsCollector from Phase 4, Task 1
        """
        try:
            from data.collectors.news_collector import NewsCollector
            collector = NewsCollector()
            news_data = await collector.collect_news(ticker, max_age_days=7)
            return [item["title"] for item in news_data.get("articles", [])]
        except Exception as e:
            logger.warning(f"Failed to get news for {ticker}: {e}")
            return []
    
    def get_metrics(self) -> Dict:
        """Get screening metrics"""
        return {
            **self.metrics,
            "filter_rate": (
                self.metrics["filtered_critical"] / self.metrics["total_candidates"]
                if self.metrics["total_candidates"] > 0
                else 0.0
            ),
        }
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics = {
            "total_candidates": 0,
            "filtered_critical": 0,
            "filtered_high": 0,
            "final_count": 0,
            "gemini_calls": 0,
            "gemini_cost": 0.0,
            "screening_time_ms": 0.0,
        }


# ==================== Helper Functions ====================

def get_sp500_top_by_market_cap(limit: int = 100) -> List[str]:
    """
    Get top S&P 500 stocks by market cap.
    
    Note: This is a simplified version. In production, fetch from:
    - Yahoo Finance (yfinance)
    - Financial data API
    - Pre-computed list
    
    Returns: List of tickers sorted by market cap (descending)
    """
    # Top 100 S&P 500 by market cap (as of 2024-11)
    # This is a static list for testing - should be dynamic in production
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "LLY", "V",
        "UNH", "XOM", "JPM", "JNJ", "WMT", "MA", "PG", "AVGO", "HD", "CVX",
        "MRK", "COST", "ABBV", "KO", "PEP", "ADBE", "BAC", "CRM", "NFLX", "TMO",
        "MCD", "CSCO", "ACN", "LIN", "ABT", "NKE", "DHR", "TXN", "PM", "AMD",
        "DIS", "WFC", "INTU", "VZ", "NEE", "CMCSA", "COP", "UPS", "QCOM", "ORCL",
        "IBM", "RTX", "HON", "GE", "AMGN", "T", "LOW", "SBUX", "SPGI", "CAT",
        "AXP", "BKNG", "BLK", "GILD", "DE", "MDT", "NOW", "SYK", "PLD", "ISRG",
        "TJX", "MDLZ", "MMC", "ADP", "VRTX", "CVS", "CI", "REGN", "ZTS", "C",
        "SO", "CB", "ADI", "DUK", "MO", "SCHW", "PGR", "EOG", "BDX", "BSX",
        "ETN", "SLB", "TGT", "USB", "FI", "ITW", "ICE", "CME", "NOC", "GD",
    ]


# ==================== Example Usage ====================

async def example_screening():
    """Example: Screen 100 stocks → 50 stocks"""
    
    # Initialize screener
    screener = DynamicScreener()
    
    # Define inputs
    portfolio = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]  # 5 holdings
    watchlist = ["TSLA", "META", "NFLX", "ADBE", "CRM"]     # 5 watchlist
    top_market_cap = get_sp500_top_by_market_cap(100)       # 100 top stocks
    
    # Screen
    candidates = await screener.screen(
        portfolio_tickers=portfolio,
        watchlist_tickers=watchlist,
        top_market_cap_tickers=top_market_cap,
        target_count=50,
        max_risk_score=0.6,
    )
    
    # Display results
    print("\n" + "="*80)
    print("Dynamic Screening Results")
    print("="*80)
    print(f"Total candidates: {screener.metrics['total_candidates']}")
    print(f"CRITICAL filtered: {screener.metrics['filtered_critical']}")
    print(f"Final count: {screener.metrics['final_count']}")
    print(f"Gemini cost: ${screener.metrics['gemini_cost']:.2f}")
    print(f"Time: {screener.metrics['screening_time_ms']:.0f}ms")
    print("="*80)
    
    print("\nTop 10 Candidates:")
    print("-"*80)
    print(f"{'Rank':<6}{'Ticker':<10}{'Priority':<15}{'Risk Level':<12}{'Risk Score':<12}")
    print("-"*80)
    
    for i, candidate in enumerate(candidates[:10], 1):
        print(f"{i:<6}{candidate.ticker:<10}{candidate.priority.name:<15}"
              f"{candidate.risk_level or 'N/A':<12}{candidate.risk_score or 0.0:<12.2f}")
    
    print("-"*80 + "\n")
    
    return candidates


if __name__ == "__main__":
    asyncio.run(example_screening())