"""
FeatureStore - Main class for 2-layer caching system.

Architecture:
    Request → Redis (< 5ms) → TimescaleDB (< 100ms) → Compute → Save to both layers

Usage:
    >>> from data.feature_store import FeatureStore
    >>> from data.collectors import YahooFinanceCollector
    >>>
    >>> store = FeatureStore()
    >>> await store.initialize()
    >>> features = await store.get_features("AAPL", ["ret_5d", "vol_20d"])
    >>> print(features)  # {"ret_5d": 0.0523, "vol_20d": 0.0234}
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.data.feature_store.cache_layer import RedisCache, TimescaleCache
from backend.data.collectors.yahoo_collector import YahooFinanceCollector
from backend.data.models.feature import FeatureResponse

logger = logging.getLogger(__name__)

class FeatureStore:
    """
    2-Layer Feature Store with Redis (L1) and TimescaleDB (L2).

    Key Methods:
    - get_features(): Retrieve features with caching
    - compute_feature(): Calculate feature from raw data
    - warm_cache(): Pre-load popular tickers (basic)
    - get_cache_warmer(): Get advanced CacheWarmer instance
    """

    def __init__(
        self,
        redis_cache: Optional[RedisCache] = None,
        timescale_cache: Optional[TimescaleCache] = None,
        data_collector: Optional[YahooFinanceCollector] = None,
        ttl_intraday: int = 300,  # 5 minutes
        ttl_daily: int = 86400,  # 24 hours
    ):
        """
        Initialize Feature Store.

        Args:
            redis_cache: Redis cache instance (L1)
            timescale_cache: TimescaleDB cache instance (L2)
            data_collector: Yahoo Finance data collector
            ttl_intraday: TTL for intraday features (seconds)
            ttl_daily: TTL for daily features (seconds)
        """
        # Use default instances if not provided
        self.redis_cache = redis_cache or RedisCache()
        self.timescale_cache = timescale_cache or TimescaleCache()
        self.data_collector = data_collector or YahooFinanceCollector()

        self.ttl_intraday = ttl_intraday
        self.ttl_daily = ttl_daily

        # Metrics
        self.cache_hits_redis = 0
        self.cache_hits_timescale = 0
        self.cache_misses = 0
        self.computations = 0
        self.total_cost_usd = 0.0

        # Lazy-loaded cache warmer
        self._cache_warmer = None

        logger.info("FeatureStore initialized")

    async def initialize(self) -> None:
        """Initialize connections (lazy initialization)."""
        # Test Redis connection
        await self.redis_cache._get_client()
        logger.info("Redis connection established")

        # Test TimescaleDB connection
        await self.timescale_cache._get_pool()
        logger.info("TimescaleDB connection established")

    async def get_features(
        self,
        ticker: str,
        feature_names: list[str],
        as_of: Optional[datetime] = None,
        version: Optional[int] = None,
    ) -> FeatureResponse:
        """
        Retrieve features with 2-layer caching.

        Flow:
        1. Check Redis (L1) → < 5ms
        2. If miss, check TimescaleDB (L2) → < 100ms
        3. If miss, compute from raw data → 2-5 seconds
        4. Save to both Redis and TimescaleDB

        Args:
            ticker: Stock ticker symbol
            feature_names: List of feature names
            as_of: Point-in-time (None = latest)
            version: Feature version (None = latest)

        Returns:
            FeatureResponse with features dict and metadata
        """
        start_time = time.time()
        ticker = ticker.upper()
        feature_names = [name.lower() for name in feature_names]

        if as_of is None:
            as_of = datetime.utcnow()

        results = {}
        cache_hits = 0
        cache_misses = 0

        for feature_name in feature_names:
            # Try to get from cache (L1 + L2)
            value = await self._get_from_cache(ticker, feature_name, as_of)

            if value is not None:
                results[feature_name] = value
                cache_hits += 1
            else:
                # Cache miss - compute feature
                value = await self.compute_feature(ticker, feature_name, as_of)
                results[feature_name] = value
                cache_misses += 1

                # Save to both layers
                if value is not None:
                    await self._save_feature(ticker, feature_name, value, as_of)

        # Update metrics
        self.cache_hits_redis += cache_hits  # Simplified - assumes all hits from Redis
        self.cache_misses += cache_misses

        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            f"get_features({ticker}, {feature_names}): {cache_hits} hits, {cache_misses} misses, {latency_ms:.2f}ms"
        )

        return FeatureResponse(
            ticker=ticker,
            features=results,
            as_of=as_of,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            latency_ms=latency_ms,
            cost_usd=cache_misses * 0.0,  # No cost for feature calculations (free)
        )

    async def _get_from_cache(
        self, ticker: str, feature_name: str, as_of: datetime
    ) -> Optional[float]:
        """
        Try to get feature from 2-layer cache.

        Returns:
            Feature value or None if not found
        """
        cache_key = self._make_cache_key(ticker, feature_name, as_of)

        # Layer 1: Redis (< 5ms)
        redis_value = await self.redis_cache.get(cache_key)
        if redis_value is not None:
            self.cache_hits_redis += 1
            logger.debug(f"Redis HIT: {cache_key}")
            try:
                data = json.loads(redis_value)
                return data.get("value")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in Redis for key {cache_key}")

        # Layer 2: TimescaleDB (< 100ms)
        timescale_value = await self.timescale_cache.get(cache_key)
        if timescale_value is not None:
            self.cache_hits_timescale += 1
            logger.debug(f"TimescaleDB HIT: {cache_key}")

            # Populate Redis for next time
            await self.redis_cache.set(cache_key, timescale_value, self.ttl_daily)

            try:
                data = json.loads(timescale_value)
                return data.get("value")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in TimescaleDB for key {cache_key}")

        # Cache miss
        return None

    async def compute_feature(
        self, ticker: str, feature_name: str, as_of: datetime
    ) -> Optional[float]:
        """
        Compute feature from raw data.

        Args:
            ticker: Stock ticker symbol
            feature_name: Feature name (e.g., "ret_5d")
            as_of: Point-in-time timestamp

        Returns:
            Computed feature value or None if calculation fails
        """
        # Get calculation function
        calculator = get_feature_calculator(feature_name)
        if calculator is None:
            logger.error(
                f"Unknown feature: {feature_name}. Available: {list_available_features()}"
            )
            return None

        # Define data fetcher (closure to pass to calculator)
        async def data_fetcher(ticker: str, start: datetime, end: datetime):
            return await self.data_collector.fetch_ohlcv(ticker, start, end)

        # Calculate feature
        logger.info(f"Computing {ticker} {feature_name} as of {as_of.date()}")
        self.computations += 1

        try:
            value = await calculator(ticker, as_of, data_fetcher)
            logger.info(f"Computed {ticker} {feature_name} = {value}")
            return value
        except Exception as e:
            logger.error(f"Error computing {ticker} {feature_name}: {e}")
            return None

    async def _save_feature(
        self, ticker: str, feature_name: str, value: float, as_of: datetime
    ) -> None:
        """
        Save feature to both Redis and TimescaleDB.

        Args:
            ticker: Stock ticker symbol
            feature_name: Feature name
            value: Computed value
            as_of: Point-in-time timestamp
        """
        cache_key = self._make_cache_key(ticker, feature_name, as_of)

        # Serialize feature data
        feature_data = {
            "value": value,
            "calculated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "metadata": {"source": "yahoo_finance", "cache_hit": False},
        }
        feature_json = json.dumps(feature_data)

        # Determine TTL based on feature type
        ttl = self.ttl_intraday if "intraday" in feature_name else self.ttl_daily

        # Save to Redis (L1)
        await self.redis_cache.set(cache_key, feature_json, ttl)

        # Save to TimescaleDB (L2)
        await self.timescale_cache.set(cache_key, feature_json, ttl)

        logger.debug(f"Saved {cache_key} to both layers (TTL={ttl}s)")

    async def warm_cache(self, tickers: list[str]) -> dict:
        """
        Pre-load features for popular tickers into Redis (BASIC VERSION).

        For advanced warming with priorities and scheduling, use get_cache_warmer().

        This should be called at market open to ensure fast responses.

        Args:
            tickers: List of ticker symbols to warm up

        Returns:
            Dict with statistics (tickers_warmed, features_loaded, time_taken)
        """
        start_time = time.time()
        features_loaded = 0

        standard_features = ["ret_5d", "ret_20d", "vol_20d", "mom_20d"]

        logger.info(f"[BASIC] Warming cache for {len(tickers)} tickers...")

        for ticker in tickers:
            try:
                response = await self.get_features(ticker, standard_features)
                features_loaded += len(
                    [v for v in response.features.values() if v is not None]
                )
            except Exception as e:
                logger.error(f"Error warming cache for {ticker}: {e}")

        time_taken = time.time() - start_time

        stats = {
            "tickers_warmed": len(tickers),
            "features_loaded": features_loaded,
            "time_taken_seconds": time_taken,
        }

        logger.info(f"[BASIC] Cache warm-up complete: {stats}")
        return stats

    def get_cache_warmer(self):
        """
        Get advanced CacheWarmer instance.

        The CacheWarmer provides:
        - Priority-based warming (portfolio > watchlist > market cap)
        - Parallel processing for speed
        - Scheduling before market open
        - Progress tracking

        Usage:
            >>> warmer = store.get_cache_warmer()
            >>> await warmer.warm_cache(
            ...     portfolio_tickers=["AAPL", "MSFT"],
            ...     watchlist_tickers=["TSLA", "NVDA"],
            ...     top_market_cap_count=30,
            ... )

        Returns:
            CacheWarmer instance
        """
        if self._cache_warmer is None:
            from .cache_warming import CacheWarmer
            self._cache_warmer = CacheWarmer(self)
            logger.info("CacheWarmer initialized")

        return self._cache_warmer

    async def warm_cache_advanced(
        self,
        portfolio_tickers: Optional[list[str]] = None,
        watchlist_tickers: Optional[list[str]] = None,
        top_market_cap_count: int = 30,
        max_workers: int = 10,
    ) -> dict:
        """
        Advanced cache warming with priority-based loading.

        This is a convenience wrapper around CacheWarmer.warm_cache().

        Args:
            portfolio_tickers: Current portfolio (highest priority)
            watchlist_tickers: Watchlist (medium priority)
            top_market_cap_count: Number of top market cap stocks
            max_workers: Maximum concurrent workers

        Returns:
            Warming statistics
        """
        warmer = self.get_cache_warmer()
        return await warmer.warm_cache(
            portfolio_tickers=portfolio_tickers,
            watchlist_tickers=watchlist_tickers,
            top_market_cap_count=top_market_cap_count,
            max_workers=max_workers,
        )

    async def warm_cache_scheduled(
        self,
        portfolio_tickers: Optional[list[str]] = None,
        watchlist_tickers: Optional[list[str]] = None,
        minutes_before_open: int = 30,
    ) -> dict:
        """
        Schedule cache warming before market open.

        Args:
            portfolio_tickers: Current portfolio
            watchlist_tickers: Watchlist
            minutes_before_open: How many minutes before open (default: 30)

        Returns:
            Warming statistics
        """
        warmer = self.get_cache_warmer()
        return await warmer.warm_before_market_open(
            portfolio_tickers=portfolio_tickers,
            watchlist_tickers=watchlist_tickers,
            minutes_before_open=minutes_before_open,
        )

    def _make_cache_key(self, ticker: str, feature_name: str, as_of: datetime) -> str:
        """
        Generate cache key.

        Format: feature:{ticker}:{feature_name}:{as_of_date}
        Example: feature:AAPL:ret_5d:2024-11-08
        """
        as_of_date = as_of.strftime("%Y-%m-%d")
        return f"feature:{ticker}:{feature_name}:{as_of_date}"

    def get_metrics(self) -> dict:
        """
        Get current metrics.

        Returns:
            Dict with cache hits, misses, hit rate, cost, etc.
        """
        total_requests = self.cache_hits_redis + self.cache_hits_timescale + self.cache_misses
        hit_rate = (
            (self.cache_hits_redis + self.cache_hits_timescale) / total_requests
            if total_requests > 0
            else 0.0
        )

        metrics = {
            "cache_hits_redis": self.cache_hits_redis,
            "cache_hits_timescale": self.cache_hits_timescale,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": hit_rate,
            "computations": self.computations,
            "total_cost_usd": self.total_cost_usd,
            "total_requests": total_requests,
        }

        # Add CacheWarmer metrics if available
        if self._cache_warmer is not None:
            metrics["cache_warmer"] = self._cache_warmer.get_metrics()

        return metrics

    async def close(self) -> None:
        """Close all connections."""
        await self.redis_cache.close()
        await self.timescale_cache.close()
        logger.info("FeatureStore closed")