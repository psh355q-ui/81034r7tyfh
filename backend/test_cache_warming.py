"""
Test Cache Warming Integration.

Tests:
1. Basic cache warming
2. Advanced priority-based warming
3. Performance comparison (cold vs warm cache)
4. Metrics validation

Usage:
    cd backend
    python test_cache_warming.py
"""

import asyncio
import logging
import time
from datetime import datetime

from data.feature_store import FeatureStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_basic_warming():
    """Test 1: Basic cache warming."""
    logger.info("=" * 80)
    logger.info("TEST 1: Basic Cache Warming")
    logger.info("=" * 80)

    store = FeatureStore()
    await store.initialize()

    # Warm cache for a few tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]

    logger.info(f"Warming cache for {len(tickers)} tickers...")
    stats = await store.warm_cache(tickers)

    logger.info(f"Results: {stats}")
    logger.info(f"✓ Test 1 completed\n")

    await store.close()


async def test_advanced_warming():
    """Test 2: Advanced priority-based warming."""
    logger.info("=" * 80)
    logger.info("TEST 2: Advanced Priority-Based Warming")
    logger.info("=" * 80)

    store = FeatureStore()
    await store.initialize()

    # Define priorities
    portfolio = ["AAPL", "MSFT"]
    watchlist = ["GOOGL", "NVDA", "TSLA", "AMD", "META"]

    logger.info(f"Portfolio: {portfolio}")
    logger.info(f"Watchlist: {watchlist}")
    logger.info(f"Top market cap: 30")

    # Warm with priorities
    stats = await store.warm_cache_advanced(
        portfolio_tickers=portfolio,
        watchlist_tickers=watchlist,
        top_market_cap_count=30,
        max_workers=10,
    )

    logger.info("\nResults:")
    logger.info(f"  Total tickers:  {stats['total_tickers']}")
    logger.info(f"  Successful:     {stats['successful']}")
    logger.info(f"  Failed:         {stats['failed']}")
    logger.info(f"  Duration:       {stats['duration_seconds']:.1f}s")
    logger.info(f"  Speed:          {stats['tickers_per_second']:.1f} tickers/s")
    logger.info(f"✓ Test 2 completed\n")

    await store.close()


async def test_performance_comparison():
    """Test 3: Performance comparison (cold vs warm cache)."""
    logger.info("=" * 80)
    logger.info("TEST 3: Performance Comparison (Cold vs Warm Cache)")
    logger.info("=" * 80)

    store = FeatureStore()
    await store.initialize()

    test_ticker = "AAPL"
    features = ["ret_5d", "ret_20d", "vol_20d", "mom_20d"]

    # Phase 1: Cold cache (first request)
    logger.info(f"\n📊 Phase 1: Cold cache (first request for {test_ticker})")
    start = time.time()
    cold_response = await store.get_features(test_ticker, features)
    cold_time = (time.time() - start) * 1000
    logger.info(f"  Latency: {cold_time:.1f}ms")
    logger.info(f"  Cache hits: {cold_response.cache_hits}")
    logger.info(f"  Cache misses: {cold_response.cache_misses}")

    # Phase 2: Warm cache (second request - should hit Redis)
    logger.info(f"\n🔥 Phase 2: Warm cache (second request)")
    start = time.time()
    warm_response = await store.get_features(test_ticker, features)
    warm_time = (time.time() - start) * 1000
    logger.info(f"  Latency: {warm_time:.1f}ms")
    logger.info(f"  Cache hits: {warm_response.cache_hits}")
    logger.info(f"  Cache misses: {warm_response.cache_misses}")

    # Calculate improvement
    improvement = ((cold_time - warm_time) / cold_time) * 100
    speedup = cold_time / warm_time if warm_time > 0 else 0

    logger.info(f"\n📈 Performance Improvement:")
    logger.info(f"  Cold cache:     {cold_time:.1f}ms")
    logger.info(f"  Warm cache:     {warm_time:.1f}ms")
    logger.info(f"  Improvement:    {improvement:.1f}%")
    logger.info(f"  Speedup:        {speedup:.0f}x faster")
    logger.info(f"✓ Test 3 completed\n")

    await store.close()


async def test_metrics():
    """Test 4: Metrics validation."""
    logger.info("=" * 80)
    logger.info("TEST 4: Metrics Validation")
    logger.info("=" * 80)

    store = FeatureStore()
    await store.initialize()

    # Warm cache
    portfolio = ["AAPL", "MSFT", "GOOGL"]
    await store.warm_cache_advanced(
        portfolio_tickers=portfolio,
        top_market_cap_count=10,
    )

    # Get metrics
    metrics = store.get_metrics()

    logger.info("\nFeature Store Metrics:")
    logger.info(f"  Cache hits (Redis):      {metrics['cache_hits_redis']}")
    logger.info(f"  Cache hits (TimescaleDB): {metrics['cache_hits_timescale']}")
    logger.info(f"  Cache misses:            {metrics['cache_misses']}")
    logger.info(f"  Cache hit rate:          {metrics['cache_hit_rate']:.1%}")
    logger.info(f"  Computations:            {metrics['computations']}")

    if "cache_warmer" in metrics:
        logger.info("\nCache Warmer Metrics:")
        cw = metrics["cache_warmer"]
        logger.info(f"  Total warmed:    {cw['total_warmed']}")
        logger.info(f"  Total failed:    {cw['total_failed']}")
        logger.info(f"  Duration:        {cw['warming_duration']:.1f}s")
        logger.info(f"  Last warming:    {cw['last_warming_time']}")

    logger.info(f"✓ Test 4 completed\n")

    await store.close()


async def main():
    """Run all tests."""
    logger.info("🧪 Cache Warming Integration Tests\n")

    try:
        await test_basic_warming()
        await asyncio.sleep(1)

        await test_advanced_warming()
        await asyncio.sleep(1)

        await test_performance_comparison()
        await asyncio.sleep(1)

        await test_metrics()

        logger.info("=" * 80)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())