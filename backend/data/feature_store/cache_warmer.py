"""
Smart Cache Warming for AI Trading System.

Pre-load features into cache before market opens to ensure fast response times.

Strategy:
1. Priority 1: Portfolio holdings (20 stocks)
2. Priority 2: Watchlist stocks (50 stocks)
3. Priority 3: Top market cap stocks (30 stocks)

Schedule: 30 minutes before market open (9:00 AM ET)
Duration: ~5 minutes to warm 100 stocks
Cost: $0 (no AI, just Feature Store)
"""

import asyncio
import logging
from datetime import datetime, time
from typing import List, Set

logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    Smart cache warming system.
    
    Pre-loads features for important stocks before market opens:
    - Portfolio holdings (highest priority)
    - Watchlist stocks (medium priority)
    - Top market cap stocks (low priority)
    
    Usage:
        warmer = CacheWarmer(feature_store)
        await warmer.warm_cache()
    """
    
    def __init__(self, feature_store, portfolio_manager=None):
        """
        Initialize cache warmer.
        
        Args:
            feature_store: FeatureStore instance
            portfolio_manager: Optional portfolio manager to get holdings
        """
        self.feature_store = feature_store
        self.portfolio_manager = portfolio_manager
        
        # Default tickers if no portfolio manager
        self.default_portfolio = []
        self.default_watchlist = []
        self.default_top_stocks = [
            # Top 30 by market cap (2024)
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "BRK.B", "V", "JNJ",
            "WMT", "XOM", "UNH", "MA", "PG",
            "JPM", "HD", "CVX", "LLY", "ABBV",
            "MRK", "KO", "PEP", "AVGO", "COST",
            "TMO", "MCD", "CSCO", "ACN", "ABT",
        ]
        
        # Metrics
        self.warmed_count = 0
        self.failed_count = 0
        self.total_time_seconds = 0.0
        
        logger.info("CacheWarmer initialized")
    
    async def warm_cache(self, feature_names: List[str] = None) -> dict:
        """
        Warm cache for all priority tickers.
        
        Args:
            feature_names: List of feature names to warm (None = all features)
        
        Returns:
            {
                "warmed_count": int,
                "failed_count": int,
                "total_time_seconds": float,
                "tickers_warmed": List[str],
            }
        """
        start_time = datetime.now()
        logger.info("Starting cache warming...")
        
        # Get priority tickers
        tickers = self._get_priority_tickers()
        logger.info(f"Warming cache for {len(tickers)} tickers")
        
        # Reset metrics
        self.warmed_count = 0
        self.failed_count = 0
        tickers_warmed = []
        
        # Warm cache for each ticker
        tasks = []
        for ticker in tickers:
            task = self._warm_single_ticker(ticker, feature_names)
            tasks.append(task)
        
        # Execute in parallel (with concurrency limit)
        results = await self._execute_with_limit(tasks, max_concurrent=10)
        
        # Count results
        for ticker, success in zip(tickers, results):
            if success:
                self.warmed_count += 1
                tickers_warmed.append(ticker)
            else:
                self.failed_count += 1
        
        # Calculate total time
        end_time = datetime.now()
        self.total_time_seconds = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Cache warming complete: "
            f"{self.warmed_count} warmed, "
            f"{self.failed_count} failed, "
            f"{self.total_time_seconds:.1f}s"
        )
        
        return {
            "warmed_count": self.warmed_count,
            "failed_count": self.failed_count,
            "total_time_seconds": self.total_time_seconds,
            "tickers_warmed": tickers_warmed,
        }
    
    def _get_priority_tickers(self) -> List[str]:
        """
        Get priority tickers in order.
        
        Returns:
            List of tickers ordered by priority
        """
        tickers = []
        
        # Priority 1: Portfolio holdings
        if self.portfolio_manager:
            holdings = self.portfolio_manager.get_holdings()
            tickers.extend(holdings)
            logger.info(f"Priority 1: {len(holdings)} portfolio holdings")
        elif self.default_portfolio:
            tickers.extend(self.default_portfolio)
            logger.info(f"Priority 1: {len(self.default_portfolio)} default portfolio")
        
        # Priority 2: Watchlist
        if self.portfolio_manager:
            watchlist = self.portfolio_manager.get_watchlist()
            tickers.extend(watchlist)
            logger.info(f"Priority 2: {len(watchlist)} watchlist stocks")
        elif self.default_watchlist:
            tickers.extend(self.default_watchlist)
            logger.info(f"Priority 2: {len(self.default_watchlist)} default watchlist")
        
        # Priority 3: Top market cap
        tickers.extend(self.default_top_stocks)
        logger.info(f"Priority 3: {len(self.default_top_stocks)} top stocks")
        
        # Remove duplicates (preserve order)
        seen = set()
        unique_tickers = []
        for ticker in tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)
        
        return unique_tickers
    
    async def _warm_single_ticker(
        self,
        ticker: str,
        feature_names: List[str] = None,
    ) -> bool:
        """
        Warm cache for a single ticker.
        
        Args:
            ticker: Stock ticker
            feature_names: List of feature names (None = all)
        
        Returns:
            True if successful, False if failed
        """
        try:
            # Get features (this will cache them)
            features = await self.feature_store.get_features(
                ticker=ticker,
                as_of_date=datetime.now(),
            )
            
            if features:
                logger.debug(f"Warmed cache for {ticker}")
                return True
            else:
                logger.warning(f"No features returned for {ticker}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to warm cache for {ticker}: {e}")
            return False
    
    async def _execute_with_limit(self, tasks, max_concurrent: int = 10):
        """
        Execute tasks with concurrency limit.
        
        Args:
            tasks: List of coroutines
            max_concurrent: Max concurrent tasks
        
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[bounded_task(task) for task in tasks])
    
    def set_portfolio_tickers(self, tickers: List[str]):
        """Set default portfolio tickers."""
        self.default_portfolio = tickers
        logger.info(f"Set portfolio tickers: {len(tickers)} stocks")
    
    def set_watchlist_tickers(self, tickers: List[str]):
        """Set default watchlist tickers."""
        self.default_watchlist = tickers
        logger.info(f"Set watchlist tickers: {len(tickers)} stocks")
    
    def get_metrics(self) -> dict:
        """Get cache warming metrics."""
        return {
            "warmed_count": self.warmed_count,
            "failed_count": self.failed_count,
            "total_time_seconds": self.total_time_seconds,
            "success_rate": (
                self.warmed_count / (self.warmed_count + self.failed_count)
                if (self.warmed_count + self.failed_count) > 0
                else 0.0
            ),
        }


class ScheduledCacheWarmer:
    """
    Scheduled cache warming (runs automatically before market open).
    
    Usage:
        scheduler = ScheduledCacheWarmer(feature_store)
        scheduler.set_portfolio_tickers(["AAPL", "MSFT", ...])
        await scheduler.start()  # Runs in background
    """
    
    def __init__(self, feature_store, portfolio_manager=None):
        """Initialize scheduled warmer."""
        self.warmer = CacheWarmer(feature_store, portfolio_manager)
        self.running = False
        self.market_open_time = time(9, 30)  # 9:30 AM ET
        self.warm_before_minutes = 30  # Warm 30 minutes before
        
        logger.info("ScheduledCacheWarmer initialized")
    
    async def start(self):
        """Start scheduled warming (runs in background)."""
        self.running = True
        logger.info("ScheduledCacheWarmer started")
        
        while self.running:
            # Check if it's time to warm
            if self._should_warm_now():
                logger.info("Time to warm cache!")
                result = await self.warmer.warm_cache()
                logger.info(f"Cache warmed: {result}")
            
            # Sleep for 1 minute
            await asyncio.sleep(60)
    
    def stop(self):
        """Stop scheduled warming."""
        self.running = False
        logger.info("ScheduledCacheWarmer stopped")
    
    def _should_warm_now(self) -> bool:
        """Check if it's time to warm cache."""
        now = datetime.now()
        current_time = now.time()
        
        # Calculate warm time (30 minutes before market open)
        warm_hour = self.market_open_time.hour
        warm_minute = self.market_open_time.minute - self.warm_before_minutes
        
        if warm_minute < 0:
            warm_hour -= 1
            warm_minute += 60
        
        warm_time = time(warm_hour, warm_minute)
        
        # Check if current time is within 1 minute of warm time
        # (since we check every minute)
        if (
            current_time.hour == warm_time.hour
            and abs(current_time.minute - warm_time.minute) <= 1
        ):
            return True
        
        return False
    
    def set_portfolio_tickers(self, tickers: List[str]):
        """Set portfolio tickers."""
        self.warmer.set_portfolio_tickers(tickers)
    
    def set_watchlist_tickers(self, tickers: List[str]):
        """Set watchlist tickers."""
        self.warmer.set_watchlist_tickers(tickers)


# Example usage
if __name__ == "__main__":
    
    async def demo():
        """Demo cache warming."""
        
        # Mock Feature Store
        class MockFeatureStore:
            async def get_features(self, ticker, as_of_date):
                await asyncio.sleep(0.01)  # Simulate API call
                return {"ret_5d": 0.05}
        
        feature_store = MockFeatureStore()
        
        # Create warmer
        warmer = CacheWarmer(feature_store)
        
        # Set custom portfolio/watchlist
        warmer.set_portfolio_tickers(["AAPL", "MSFT", "GOOGL"])
        warmer.set_watchlist_tickers(["TSLA", "NVDA"])
        
        # Warm cache
        result = await warmer.warm_cache()
        
        print(f"\nCache Warming Results:")
        print(f"  Warmed: {result['warmed_count']} tickers")
        print(f"  Failed: {result['failed_count']} tickers")
        print(f"  Time: {result['total_time_seconds']:.1f}s")
        print(f"  Tickers: {', '.join(result['tickers_warmed'][:10])}...")
    
    asyncio.run(demo())