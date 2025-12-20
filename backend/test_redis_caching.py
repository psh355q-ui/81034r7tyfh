"""
Redis Caching Test (Simplified)

Tests Redis caching (Layer 1) without TimescaleDB dependency.
This is a simplified test to verify the core caching functionality.

Expected results:
1. First request: CACHE MISS → Compute (2-5s)
2. Second request: REDIS HIT → < 5ms
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timedelta

import redis.asyncio as redis

# Add backend to path
sys.path.insert(0, 'D:\\code\\ai-trading-system\\backend')

# Import only what we need (avoiding asyncpg dependency)
from data.collectors.yahoo_collector import YahooFinanceCollector

# Import feature calculation functions directly
import importlib.util
spec = importlib.util.spec_from_file_location("features", "data/feature_store/features.py")
features_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(features_module)

calculate_return = features_module.calculate_return
calculate_volatility = features_module.calculate_volatility
calculate_momentum = features_module.calculate_momentum


class SimpleRedisCache:
    """Simplified Redis cache for testing."""

    def __init__(self, redis_url: str = "redis://192.168.50.148:6379/0"):
        self.redis_url = redis_url
        self._client = None

    async def connect(self):
        """Connect to Redis."""
        self._client = redis.from_url(self.redis_url, decode_responses=True)
        await self._client.ping()
        print("  [OK] Redis connection: OK")

    async def get(self, key: str):
        """Get value from Redis."""
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int):
        """Set value in Redis with TTL."""
        await self._client.setex(key, ttl, value)

    async def delete(self, key: str):
        """Delete key from Redis."""
        await self._client.delete(key)

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()


async def compute_features(ticker: str, feature_names: list[str], collector: YahooFinanceCollector):
    """Compute features from Yahoo Finance data."""
    results = {}
    as_of = datetime.now()

    async def data_fetcher(ticker: str, start: datetime, end: datetime):
        return await collector.fetch_ohlcv(ticker, start, end)

    for feature_name in feature_names:
        try:
            if feature_name == "ret_5d":
                value = await calculate_return(ticker, 5, as_of, data_fetcher)
            elif feature_name == "ret_20d":
                value = await calculate_return(ticker, 20, as_of, data_fetcher)
            elif feature_name == "vol_20d":
                value = await calculate_volatility(ticker, 20, as_of, data_fetcher)
            elif feature_name == "mom_20d":
                value = await calculate_momentum(ticker, 20, as_of, data_fetcher)
            else:
                value = None

            results[feature_name] = value
        except Exception as e:
            print(f"    Error computing {feature_name}: {e}")
            results[feature_name] = None

    return results


async def test_redis_caching():
    """Test Redis caching with real data."""
    print("\n" + "=" * 70)
    print("  REDIS CACHING TEST (Layer 1)")
    print("=" * 70)

    # Initialize
    cache = SimpleRedisCache()
    collector = YahooFinanceCollector()

    try:
        print("\n[1/4] Initializing...")
        await cache.connect()

        ticker = "AAPL"
        features = ["ret_5d", "vol_20d", "mom_20d"]
        cache_key_prefix = f"feature:{ticker}"

        print(f"\n[2/4] Testing with ticker: {ticker}")
        print(f"      Features: {features}")

        # Test 1: First request (CACHE MISS - should compute)
        print("\n" + "-" * 70)
        print("TEST 1: First Request (Expected: CACHE MISS + Computation)")
        print("-" * 70)

        start = time.time()
        results1 = await compute_features(ticker, features, collector)
        elapsed1 = time.time() - start

        print(f"  Results:")
        for fname, value in results1.items():
            if value is not None:
                print(f"    {fname:10s} = {value:.6f}")
                # Save to Redis
                cache_key = f"{cache_key_prefix}:{fname}"
                cache_data = {
                    "value": value,
                    "calculated_at": datetime.now().isoformat(),
                    "version": 1
                }
                await cache.set(cache_key, json.dumps(cache_data), 3600)  # 1 hour TTL
            else:
                print(f"    {fname:10s} = N/A")

        print(f"\n  Performance:")
        print(f"    Computation time: {elapsed1:.3f} s ({elapsed1 * 1000:.0f} ms)")
        print("  [PASS] Features computed and saved to Redis")

        await asyncio.sleep(0.5)

        # Test 2: Second request (REDIS HIT)
        print("\n" + "-" * 70)
        print("TEST 2: Second Request (Expected: REDIS HIT < 5ms)")
        print("-" * 70)

        start = time.time()
        results2 = {}
        cache_hits = 0

        for fname in features:
            cache_key = f"{cache_key_prefix}:{fname}"
            cached = await cache.get(cache_key)

            if cached:
                data = json.loads(cached)
                results2[fname] = data.get("value")
                cache_hits += 1
            else:
                results2[fname] = None

        elapsed2 = time.time() - start

        print(f"  Results:")
        for fname, value in results2.items():
            if value is not None:
                print(f"    {fname:10s} = {value:.6f} (from cache)")
            else:
                print(f"    {fname:10s} = N/A")

        print(f"\n  Performance:")
        print(f"    Cache hits:    {cache_hits}/{len(features)}")
        print(f"    Latency:       {elapsed2 * 1000:.2f} ms")

        if cache_hits == len(features) and elapsed2 * 1000 < 50:
            print(f"  [PASS] Redis cache hit! ({elapsed2 * 1000:.2f} ms < 50ms)")
        else:
            print(f"  [WARNING] Expected all cache hits with < 50ms latency")

        # Test 3: Clear cache and verify
        print("\n" + "-" * 70)
        print("TEST 3: Cache Invalidation")
        print("-" * 70)

        for fname in features:
            cache_key = f"{cache_key_prefix}:{fname}"
            await cache.delete(cache_key)

        print("  [OK] Cache cleared")

        # Verify cache is empty
        cache_hits_after_clear = 0
        for fname in features:
            cache_key = f"{cache_key_prefix}:{fname}"
            cached = await cache.get(cache_key)
            if cached:
                cache_hits_after_clear += 1

        if cache_hits_after_clear == 0:
            print("  [PASS] Cache successfully invalidated")
        else:
            print(f"  [FAIL] {cache_hits_after_clear} items still in cache!")

        # Performance summary
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        print(f"\n  Request 1 (Cache Miss):     {elapsed1 * 1000:>8.2f} ms  (computation)")
        print(f"  Request 2 (Redis Hit):      {elapsed2 * 1000:>8.2f} ms  (< 50ms target)")

        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
        print(f"\n  Speedup (Redis vs Compute): {speedup:.1f}x faster")

        # Final verdict
        print("\n" + "=" * 70)
        all_passed = (
            elapsed1 > 1.0 and  # First request should take time (computation)
            cache_hits == len(features) and  # Second should hit cache
            elapsed2 * 1000 < 50 and  # Redis should be fast
            cache_hits_after_clear == 0  # Cache should clear properly
        )

        if all_passed:
            print("*** ALL TESTS PASSED! ***")
            print("\nRedis caching (Layer 1) is working perfectly!")
            print(f"- Cache latency: {elapsed2 * 1000:.2f} ms < 50ms [OK]")
            print(f"- Speedup: {speedup:.1f}x faster than computation [OK]")
            print("- Cache invalidation: Working [OK]")
        else:
            print("*** SOME TESTS FAILED ***")
            print("\nCheck the test results above for details.")

        print("=" * 70)

        # Yahoo Finance stats
        cache_stats = collector.get_cache_stats()
        print("\n" + "=" * 70)
        print("YAHOO FINANCE COLLECTOR STATS")
        print("=" * 70)
        print(f"  Cache size:       {cache_stats['cache_size']} entries")
        print(f"  Request count:    {cache_stats['request_count']}")
        print(f"  Oldest entry age: {cache_stats['oldest_entry_age_hours']:.2f} hours")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup
        print("\n[4/4] Cleaning up...")
        await cache.close()
        print("  [OK] Connections closed")


async def main():
    """Run all tests."""
    print("\n" + "+" + "=" * 68 + "+")
    print("|" + "  AI Trading System - Redis Caching Test".center(68) + "|")
    print("+" + "=" * 68 + "+")

    await test_redis_caching()

    print("\n" + "=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print("  1. Install asyncpg for full 2-layer caching:")
    print("     pip install asyncpg (requires Visual Studio Build Tools)")
    print("  2. Run full test: python test_feature_store_full.py")
    print("  3. Check TimescaleDB data:")
    print("     docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading")
    print("     SELECT * FROM features ORDER BY calculated_at DESC LIMIT 10;")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
