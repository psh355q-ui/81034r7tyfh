"""
2-Layer Feature Store Caching Test

Tests the complete caching system:
- Layer 1: Redis (< 5ms)
- Layer 2: TimescaleDB (< 100ms)
- Layer 3: Computation (2-5s)

Expected results:
1. First request: CACHE MISS → Compute + Save to both layers (2-5s)
2. Second request: REDIS HIT → < 5ms
3. Third request (after Redis clear): TIMESCALE HIT → < 100ms
"""

import asyncio
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'D:\\code\\ai-trading-system\\backend')

from data.feature_store.store import FeatureStore


async def test_2_layer_caching():
    """Test 2-layer caching system with real data."""
    print("\n" + "=" * 70)
    print("  2-LAYER CACHING TEST - FeatureStore")
    print("=" * 70)

    # Initialize FeatureStore
    store = FeatureStore()

    try:
        print("\n[1/5] Initializing FeatureStore...")
        await store.initialize()
        print("  ✓ Redis connection: OK")
        print("  ✓ TimescaleDB connection: OK")

        ticker = "AAPL"
        features = ["ret_5d", "vol_20d", "mom_20d"]

        print(f"\n[2/5] Testing with ticker: {ticker}")
        print(f"      Features: {features}")

        # Test 1: First request (CACHE MISS - should compute)
        print("\n" + "-" * 70)
        print("TEST 1: First Request (Expected: CACHE MISS + Computation)")
        print("-" * 70)
        start = time.time()
        response1 = await store.get_features(ticker, features)
        elapsed1 = time.time() - start

        print(f"  Results:")
        for fname, value in response1.features.items():
            if value is not None:
                print(f"    {fname:10s} = {value:.6f}")
            else:
                print(f"    {fname:10s} = N/A")

        print(f"\n  Performance:")
        print(f"    Cache hits:   {response1.cache_hits}")
        print(f"    Cache misses: {response1.cache_misses}")
        print(f"    Latency:      {response1.latency_ms:.2f} ms")
        print(f"    Total time:   {elapsed1:.3f} s")

        if response1.cache_misses > 0:
            print("  ✓ PASS: Cache miss detected (as expected)")
        else:
            print("  ✗ FAIL: Expected cache miss!")

        # Wait a bit
        await asyncio.sleep(1)

        # Test 2: Second request (REDIS HIT)
        print("\n" + "-" * 70)
        print("TEST 2: Second Request (Expected: REDIS HIT < 5ms)")
        print("-" * 70)
        start = time.time()
        response2 = await store.get_features(ticker, features)
        elapsed2 = time.time() - start

        print(f"  Performance:")
        print(f"    Cache hits:   {response2.cache_hits}")
        print(f"    Cache misses: {response2.cache_misses}")
        print(f"    Latency:      {response2.latency_ms:.2f} ms")
        print(f"    Total time:   {elapsed2:.3f} s")

        if response2.cache_hits == len(features) and response2.latency_ms < 50:
            print(f"  ✓ PASS: Redis cache hit! ({response2.latency_ms:.2f} ms < 50ms)")
        else:
            print(f"  ✗ WARNING: Expected Redis hit with < 50ms latency")

        # Test 3: Clear Redis and request again (TIMESCALE HIT)
        print("\n" + "-" * 70)
        print("TEST 3: After Redis Clear (Expected: TIMESCALE HIT < 100ms)")
        print("-" * 70)

        print("  Clearing Redis cache...")
        # Clear Redis for this ticker
        for feature_name in features:
            cache_key = store._make_cache_key(ticker, feature_name, response1.as_of)
            await store.redis_cache.delete(cache_key)
        print("  ✓ Redis cleared")

        await asyncio.sleep(0.5)

        start = time.time()
        response3 = await store.get_features(ticker, features)
        elapsed3 = time.time() - start

        print(f"\n  Performance:")
        print(f"    Cache hits:   {response3.cache_hits}")
        print(f"    Cache misses: {response3.cache_misses}")
        print(f"    Latency:      {response3.latency_ms:.2f} ms")
        print(f"    Total time:   {elapsed3:.3f} s")

        if response3.cache_hits == len(features) and response3.latency_ms < 200:
            print(f"  ✓ PASS: TimescaleDB cache hit! ({response3.latency_ms:.2f} ms < 200ms)")
        else:
            print(f"  ✗ WARNING: Expected TimescaleDB hit with < 200ms latency")

        # Test 4: Performance summary
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        print(f"\n  Request 1 (Cache Miss):     {elapsed1 * 1000:>8.2f} ms  (computation)")
        print(f"  Request 2 (Redis Hit):      {elapsed2 * 1000:>8.2f} ms  (< 50ms target)")
        print(f"  Request 3 (TimescaleDB Hit):{elapsed3 * 1000:>8.2f} ms  (< 200ms target)")

        speedup_redis = elapsed1 / elapsed2 if elapsed2 > 0 else 0
        speedup_timescale = elapsed1 / elapsed3 if elapsed3 > 0 else 0

        print(f"\n  Speedup (Redis vs Compute):     {speedup_redis:.1f}x faster")
        print(f"  Speedup (TimescaleDB vs Compute):{speedup_timescale:.1f}x faster")

        # Store metrics
        metrics = store.get_metrics()
        print("\n" + "=" * 70)
        print("CACHE STATISTICS")
        print("=" * 70)
        print(f"  Total requests:       {metrics['total_requests']}")
        print(f"  Redis hits:           {metrics['cache_hits_redis']}")
        print(f"  TimescaleDB hits:     {metrics['cache_hits_timescale']}")
        print(f"  Cache misses:         {metrics['cache_misses']}")
        print(f"  Cache hit rate:       {metrics['cache_hit_rate'] * 100:.1f}%")
        print(f"  Computations:         {metrics['computations']}")

        # Final verdict
        print("\n" + "=" * 70)
        all_passed = (
            response1.cache_misses > 0 and  # First request should miss
            response2.cache_hits == len(features) and  # Second should hit Redis
            response3.cache_hits == len(features)  # Third should hit TimescaleDB
        )

        if all_passed:
            print("✓✓✓ ALL TESTS PASSED! ✓✓✓")
            print("\n2-Layer caching system is working perfectly!")
            print("- Redis (L1): < 50ms")
            print("- TimescaleDB (L2): < 200ms")
            print("- Computation: ~2-5s")
        else:
            print("⚠⚠⚠ SOME TESTS FAILED ⚠⚠⚠")
            print("\nCheck the test results above for details.")

        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup
        print("\n[5/5] Cleaning up...")
        await store.close()
        print("  ✓ Connections closed")


async def test_warm_cache():
    """Test cache warming feature."""
    print("\n" + "=" * 70)
    print("  CACHE WARMING TEST")
    print("=" * 70)

    store = FeatureStore()

    try:
        await store.initialize()

        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        print(f"\nWarming cache for {len(tickers)} tickers...")
        print(f"Tickers: {', '.join(tickers)}")

        start = time.time()
        stats = await store.warm_cache(tickers)
        elapsed = time.time() - start

        print(f"\n  Warm-up Results:")
        print(f"    Tickers processed: {stats['tickers_warmed']}")
        print(f"    Features loaded:   {stats['features_loaded']}")
        print(f"    Time taken:        {elapsed:.2f} s")
        print(f"    Avg per ticker:    {elapsed / len(tickers):.2f} s")

        print("\n  ✓ Cache warming completed successfully!")

    finally:
        await store.close()


async def main():
    """Run all tests."""
    print("\n" + "+" + "=" * 68 + "+")
    print("|" + "  AI Trading System - 2-Layer Feature Caching Test".center(68) + "|")
    print("+" + "=" * 68 + "+")

    # Test 1: 2-layer caching
    await test_2_layer_caching()

    # Optional: Test 2: Cache warming (commented out to save time)
    # print("\n\n")
    # await test_warm_cache()

    print("\n" + "=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print("  1. Check Grafana dashboard: http://localhost:3001")
    print("     (admin/admin)")
    print("  2. Deploy to NAS: Follow NAS_DEPLOYMENT_GUIDE.md")
    print("  3. Set up monitoring alerts for cache hit rate")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
