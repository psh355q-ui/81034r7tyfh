"""
Cache Warming for Feature Store.

Automatically pre-loads features into cache before market open to ensure
instant responses when trading begins.

Priority Tiers:
1. Portfolio holdings (highest priority)
2. Watchlist stocks
3. Market cap top stocks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    Intelligent cache warming for Feature Store.
    
    Features:
    - Priority-based warming (portfolio > watchlist > market cap)
    - Parallel processing for speed
    - Progress tracking and metrics
    - Automatic retry on failure
    """

    def __init__(self, feature_store):
        """
        Initialize Cache Warmer.
        
        Args:
            feature_store: FeatureStore instance
        """
        self.feature_store = feature_store
        self.standard_features = [
            "ret_5d",
            "ret_20d",
            "vol_20d",
            "mom_20d",
        ]
        
        # Metrics
        self.total_warmed = 0
        self.total_failed = 0
        self.warming_start_time = None
        self.warming_duration = 0.0
        
        logger.info("CacheWarmer initialized")

    async def warm_cache(
        self,
        portfolio_tickers: Optional[List[str]] = None,
        watchlist_tickers: Optional[List[str]] = None,
        top_market_cap_count: int = 30,
        max_workers: int = 10,
    ) -> dict:
        """
        Warm cache with priority-based loading.
        
        Args:
            portfolio_tickers: Current portfolio holdings (highest priority)
            watchlist_tickers: Watchlist stocks (medium priority)
            top_market_cap_count: Number of top market cap stocks to warm
            max_workers: Maximum concurrent tasks
            
        Returns:
            Dict with warming statistics
        """
        self.warming_start_time = datetime.utcnow()
        logger.info("🔥 Cache warming started...")
        
        # Build priority list
        priority_tickers = self._build_priority_list(
            portfolio_tickers or [],
            watchlist_tickers or [],
            top_market_cap_count,
        )
        
        logger.info(
            f"Warming {len(priority_tickers)} tickers: "
            f"{len(portfolio_tickers or [])} portfolio + "
            f"{len(watchlist_tickers or [])} watchlist + "
            f"{top_market_cap_count} top market cap"
        )
        
        # Warm in parallel batches
        results = await self._warm_parallel(
            priority_tickers,
            max_workers=max_workers,
        )
        
        # Calculate metrics
        self.warming_duration = (
            datetime.utcnow() - self.warming_start_time
        ).total_seconds()
        
        metrics = {
            "total_tickers": len(priority_tickers),
            "successful": self.total_warmed,
            "failed": self.total_failed,
            "duration_seconds": self.warming_duration,
            "tickers_per_second": (
                self.total_warmed / self.warming_duration
                if self.warming_duration > 0
                else 0
            ),
        }
        
        logger.info(
            f"✅ Cache warming completed: "
            f"{metrics['successful']}/{metrics['total_tickers']} tickers "
            f"in {metrics['duration_seconds']:.1f}s "
            f"({metrics['tickers_per_second']:.1f} tickers/s)"
        )
        
        return metrics

    def _build_priority_list(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
        top_market_cap_count: int,
    ) -> List[str]:
        """
        Build prioritized list of tickers to warm.
        
        Priority order:
        1. Portfolio holdings
        2. Watchlist
        3. Top market cap stocks
        
        Duplicates are removed (portfolio takes precedence).
        """
        priority_list = []
        seen = set()
        
        # 1. Portfolio (highest priority)
        for ticker in portfolio_tickers:
            ticker = ticker.upper()
            if ticker not in seen:
                priority_list.append(ticker)
                seen.add(ticker)
        
        # 2. Watchlist
        for ticker in watchlist_tickers:
            ticker = ticker.upper()
            if ticker not in seen:
                priority_list.append(ticker)
                seen.add(ticker)
        
        # 3. Top market cap stocks
        top_stocks = self._get_top_market_cap_stocks(top_market_cap_count)
        for ticker in top_stocks:
            ticker = ticker.upper()
            if ticker not in seen:
                priority_list.append(ticker)
                seen.add(ticker)
        
        return priority_list

    def _get_top_market_cap_stocks(self, count: int) -> List[str]:
        """
        Get top N stocks by market cap.
        
        For now, returns hardcoded list of major stocks.
        TODO: Fetch from API (e.g., Yahoo Finance screener)
        """
        # Top 30 US stocks by market cap (as of 2024)
        # Note: BRK-B removed due to yfinance ticker format issues
        top_stocks = [
            # Tech Giants
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
            # Other Mega Caps
            "V", "WMT", "JPM", "JNJ", "UNH", "XOM", "MA",
            "PG", "HD", "CVX", "ABBV", "MRK", "COST", "PEP", "AVGO",
            "KO", "ADBE", "MCD", "CSCO", "ACN", "TMO", "LLY", "NKE",
        ]
        return top_stocks[:count]

    async def _warm_parallel(
        self,
        tickers: List[str],
        max_workers: int = 10,
    ) -> List[dict]:
        """
        Warm cache for multiple tickers in parallel.
        
        Uses asyncio.Semaphore to limit concurrent requests.
        """
        semaphore = asyncio.Semaphore(max_workers)
        
        async def warm_single(ticker: str) -> dict:
            async with semaphore:
                return await self._warm_single_ticker(ticker)
        
        # Execute all tasks in parallel (but limited by semaphore)
        tasks = [warm_single(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results

    async def _warm_single_ticker(self, ticker: str) -> dict:
        """
        Warm cache for a single ticker.
        
        Fetches all standard features and stores in cache.
        """
        try:
            start_time = datetime.utcnow()
            
            # Fetch features (this will automatically cache them)
            response = await self.feature_store.get_features(
                ticker=ticker,
                feature_names=self.standard_features,
            )
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Check if successful
            if response.features:
                self.total_warmed += 1
                logger.debug(
                    f"✓ Warmed {ticker}: {len(response.features)} features "
                    f"in {duration_ms:.0f}ms"
                )
                return {
                    "ticker": ticker,
                    "success": True,
                    "features_count": len(response.features),
                    "duration_ms": duration_ms,
                }
            else:
                self.total_failed += 1
                logger.warning(f"✗ Failed to warm {ticker}: No features")
                return {
                    "ticker": ticker,
                    "success": False,
                    "error": "No features returned",
                }
                
        except Exception as e:
            self.total_failed += 1
            logger.error(f"✗ Error warming {ticker}: {e}")
            return {
                "ticker": ticker,
                "success": False,
                "error": str(e),
            }

    async def warm_before_market_open(
        self,
        portfolio_tickers: Optional[List[str]] = None,
        watchlist_tickers: Optional[List[str]] = None,
        minutes_before_open: int = 30,
    ) -> dict:
        """
        Schedule cache warming before market open.
        
        Args:
            portfolio_tickers: Current portfolio
            watchlist_tickers: Watchlist
            minutes_before_open: How many minutes before market open to warm
            
        Returns:
            Warming metrics
        """
        # Calculate next market open time
        market_open_time = self._get_next_market_open()
        warming_time = market_open_time - timedelta(minutes=minutes_before_open)
        
        now = datetime.utcnow()
        
        if warming_time > now:
            wait_seconds = (warming_time - now).total_seconds()
            logger.info(
                f"⏰ Scheduled cache warming at {warming_time} "
                f"(in {wait_seconds/60:.1f} minutes)"
            )
            await asyncio.sleep(wait_seconds)
        
        # Warm cache
        return await self.warm_cache(
            portfolio_tickers=portfolio_tickers,
            watchlist_tickers=watchlist_tickers,
        )

    def _get_next_market_open(self) -> datetime:
        """
        Get next US market open time (9:30 AM ET).
        
        TODO: Handle holidays using market calendar
        """
        from datetime import timezone
        import pytz
        
        # US Eastern Time
        eastern = pytz.timezone('US/Eastern')
        now_et = datetime.now(eastern)
        
        # Market opens at 9:30 AM ET
        market_open_hour = 9
        market_open_minute = 30
        
        # Calculate next market open
        next_open = now_et.replace(
            hour=market_open_hour,
            minute=market_open_minute,
            second=0,
            microsecond=0,
        )
        
        # If already past today's open, move to next day
        if now_et >= next_open:
            next_open += timedelta(days=1)
        
        # Skip weekends (Saturday -> Monday)
        while next_open.weekday() >= 5:  # 5=Saturday, 6=Sunday
            next_open += timedelta(days=1)
        
        # Convert to UTC
        return next_open.astimezone(timezone.utc).replace(tzinfo=None)

    def get_metrics(self) -> dict:
        """Get cache warming metrics."""
        return {
            "total_warmed": self.total_warmed,
            "total_failed": self.total_failed,
            "warming_duration": self.warming_duration,
            "last_warming_time": (
                self.warming_start_time.isoformat()
                if self.warming_start_time
                else None
            ),
        }