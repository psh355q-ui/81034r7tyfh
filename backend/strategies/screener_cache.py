"""
Dynamic Screener Cache & Feature Store Integration

Purpose: Cache screening results for 1 hour to avoid redundant Gemini calls

Cache Strategy:
- Key: "screener:candidates:{portfolio_hash}:{watchlist_hash}"
- TTL: 3600 seconds (1 hour)
- Invalidation: Portfolio/watchlist changes

Phase: 5 (Strategy Ensemble)
Task: 3 (Dynamic Screener)
"""

import hashlib
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== Cache Management ====================

class ScreenerCache:
    """
    Cache manager for screening results.
    
    Benefits:
    - Avoid redundant Gemini calls
    - 1-hour cache = $0.90/day → $0.90/month (if cached)
    - Fast response (< 10ms from Redis)
    """
    
    def __init__(self, redis_client):
        """
        Initialize cache.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.ttl_seconds = 3600  # 1 hour
        
        # Metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_saves": 0,
        }
        
        logger.info(f"ScreenerCache initialized (TTL={self.ttl_seconds}s)")
    
    def _generate_cache_key(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
    ) -> str:
        """
        Generate cache key from inputs.
        
        Uses MD5 hash of sorted ticker lists to ensure:
        - Same inputs → same key
        - Different order → same key
        - Any change → different key
        """
        # Sort for consistency
        portfolio_str = ",".join(sorted(portfolio_tickers))
        watchlist_str = ",".join(sorted(watchlist_tickers))
        
        # Hash
        combined = f"{portfolio_str}|{watchlist_str}"
        hash_str = hashlib.md5(combined.encode()).hexdigest()[:16]
        
        return f"screener:candidates:{hash_str}"
    
    async def get(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
    ) -> Optional[List[Dict]]:
        """
        Get cached screening results.
        
        Returns:
            List of candidate dicts or None if not cached
        """
        cache_key = self._generate_cache_key(portfolio_tickers, watchlist_tickers)
        
        try:
            cached = await self.redis.get(cache_key)
            
            if cached:
                self.metrics["cache_hits"] += 1
                logger.info(f"Cache HIT: {cache_key}")
                
                # Parse JSON
                candidates = json.loads(cached)
                
                # Log age
                if candidates and "cached_at" in candidates[0]:
                    cached_at = datetime.fromisoformat(candidates[0]["cached_at"])
                    age_minutes = (datetime.now() - cached_at).total_seconds() / 60
                    logger.info(f"Cache age: {age_minutes:.1f} minutes")
                
                return candidates
            else:
                self.metrics["cache_misses"] += 1
                logger.info(f"Cache MISS: {cache_key}")
                return None
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
        candidates: List[Dict],
    ):
        """
        Cache screening results.
        
        Args:
            portfolio_tickers: Portfolio tickers
            watchlist_tickers: Watchlist tickers
            candidates: Screening results to cache
        """
        cache_key = self._generate_cache_key(portfolio_tickers, watchlist_tickers)
        
        try:
            # Add timestamp
            for candidate in candidates:
                candidate["cached_at"] = datetime.now().isoformat()
            
            # Serialize
            cached_data = json.dumps(candidates)
            
            # Save with TTL
            await self.redis.setex(cache_key, self.ttl_seconds, cached_data)
            
            self.metrics["cache_saves"] += 1
            logger.info(f"Cached {len(candidates)} candidates (TTL={self.ttl_seconds}s)")
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
    ):
        """
        Invalidate cache for specific inputs.
        
        Use when:
        - Portfolio changes (buy/sell)
        - Watchlist updated
        - Manual refresh requested
        """
        cache_key = self._generate_cache_key(portfolio_tickers, watchlist_tickers)
        
        try:
            await self.redis.delete(cache_key)
            logger.info(f"Cache invalidated: {cache_key}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    def get_metrics(self) -> Dict:
        """Get cache metrics"""
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = self.metrics["cache_hits"] / total if total > 0 else 0.0
        
        return {
            **self.metrics,
            "hit_rate": hit_rate,
        }


# ==================== Feature Store Integration ====================

async def screen_stocks_cached(
    portfolio_tickers: List[str],
    watchlist_tickers: List[str],
    top_market_cap_tickers: List[str],
    redis_client,
    target_count: int = 50,
) -> List[Dict]:
    """
    Screen stocks with caching.
    
    Workflow:
    1. Check cache
    2. If HIT: Return cached results (< 10ms)
    3. If MISS: Run screening → Cache results → Return
    
    Args:
        portfolio_tickers: Portfolio holdings
        watchlist_tickers: User watchlist
        top_market_cap_tickers: Top stocks by market cap
        redis_client: Redis client
        target_count: Target number of stocks (default 50)
    
    Returns:
        List of candidate dicts
    """
    # Initialize cache
    cache = ScreenerCache(redis_client)
    
    # Check cache
    cached_results = await cache.get(portfolio_tickers, watchlist_tickers)
    
    if cached_results:
        logger.info("Using cached screening results")
        return cached_results
    
    # Cache miss - run screening
    logger.info("Cache miss - running fresh screening")
    
    from dynamic_screener import DynamicScreener
    screener = DynamicScreener()
    
    candidates = await screener.screen(
        portfolio_tickers=portfolio_tickers,
        watchlist_tickers=watchlist_tickers,
        top_market_cap_tickers=top_market_cap_tickers,
        target_count=target_count,
    )
    
    # Convert to dicts for caching
    candidates_dicts = [
        {
            "ticker": c.ticker,
            "priority": c.priority.name,
            "risk_score": c.risk_score,
            "risk_level": c.risk_level,
            "market_cap": c.market_cap,
            "sector": c.sector,
        }
        for c in candidates
    ]
    
    # Cache results
    await cache.set(portfolio_tickers, watchlist_tickers, candidates_dicts)
    
    return candidates_dicts


# ==================== Feature Store Feature Definition ====================

FEATURE_DEFINITIONS = {
    "screened_candidates": {
        "description": "Top 50 stocks after Gemini risk screening",
        "category": "screener",
        "update_frequency": "hourly",
        "ttl_seconds": 3600,
        "calculation_function": "screen_stocks_cached",
        "cost_per_calculation": 0.03,  # 100 stocks × $0.0003
        "dependencies": ["portfolio", "watchlist", "non_standard_risk"],
    },
}


# ==================== Screener Warmer (장 시작 전 준비) ====================

class ScreenerWarmer:
    """
    Pre-warm screener cache before market open.
    
    Benefits:
    - 장 시작 시 즉시 사용 가능
    - AI API 비용 0 (이미 캐시됨)
    - 응답 시간 < 10ms
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache = ScreenerCache(redis_client)
    
    async def warm_cache(
        self,
        portfolio_tickers: List[str],
        watchlist_tickers: List[str],
        top_market_cap_tickers: List[str],
    ):
        """
        Warm cache before market open.
        
        Schedule: Daily at 8:30 AM (30 minutes before market open)
        Cost: $0.03 (100 stocks × $0.0003)
        Time: ~5 seconds (10 concurrent)
        """
        logger.info("Starting cache warm-up...")
        
        start_time = datetime.now()
        
        # Run screening (will be cached)
        candidates = await screen_stocks_cached(
            portfolio_tickers=portfolio_tickers,
            watchlist_tickers=watchlist_tickers,
            top_market_cap_tickers=top_market_cap_tickers,
            redis_client=self.redis,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Cache warmed: {len(candidates)} stocks, {elapsed:.1f}s")
        
        return candidates


# ==================== Example Usage ====================

async def example_cached_screening():
    """Example: Cached screening workflow"""
    import redis.asyncio as redis_async
    
    # Initialize Redis
    redis_client = redis_async.from_url("redis://localhost:6379/0")
    
    # Define inputs
    portfolio = ["AAPL", "MSFT", "GOOGL"]
    watchlist = ["TSLA", "META", "NFLX"]
    from dynamic_screener import get_sp500_top_by_market_cap
    top_market_cap = get_sp500_top_by_market_cap(100)
    
    print("\n" + "="*80)
    print("Cached Screening Example")
    print("="*80)
    
    # First call (cache miss)
    print("\n1. First call (cache miss)...")
    start = datetime.now()
    candidates1 = await screen_stocks_cached(
        portfolio_tickers=portfolio,
        watchlist_tickers=watchlist,
        top_market_cap_tickers=top_market_cap,
        redis_client=redis_client,
    )
    time1 = (datetime.now() - start).total_seconds() * 1000
    print(f"   Time: {time1:.0f}ms")
    print(f"   Results: {len(candidates1)} stocks")
    
    # Second call (cache hit)
    print("\n2. Second call (cache hit)...")
    start = datetime.now()
    candidates2 = await screen_stocks_cached(
        portfolio_tickers=portfolio,
        watchlist_tickers=watchlist,
        top_market_cap_tickers=top_market_cap,
        redis_client=redis_client,
    )
    time2 = (datetime.now() - start).total_seconds() * 1000
    print(f"   Time: {time2:.0f}ms")
    print(f"   Results: {len(candidates2)} stocks")
    print(f"   Speedup: {time1/time2:.0f}x faster")
    
    print("\n" + "="*80 + "\n")
    
    await redis_client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_cached_screening())