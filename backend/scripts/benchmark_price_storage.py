"""
Performance Benchmark: Yahoo Finance Incremental Storage vs Direct Download.

Tests the performance improvement of incremental storage over direct yfinance downloads.

Expected Results:
- Direct download: 2-5 seconds (full 5-year download)
- Incremental storage: 0.1 seconds (DB query)
- Speedup: 20-50x faster

Usage:
    python backend/scripts/benchmark_price_storage.py
"""

import logging
import time
import asyncio
from datetime import date, timedelta
import yfinance as yf
import pandas as pd

from backend.core.database import get_db
from backend.data.stock_price_storage import StockPriceStorage

logger = logging.getLogger(__name__)


async def benchmark_direct_download(ticker: str, years: int = 5) -> dict:
    """
    Benchmark: Direct yfinance download (current method).

    Args:
        ticker: Stock ticker
        years: Number of years

    Returns:
        Benchmark stats
    """
    print(f"\n1️⃣  Direct yfinance download ({ticker}, {years} years)")
    print("=" * 60)

    end_date = date.today()
    start_date = end_date - timedelta(days=365 * years)

    # Warm-up
    _ = yf.download(ticker, start=start_date, end=end_date, progress=False)

    # Benchmark
    start_time = time.time()
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    duration = time.time() - start_time

    print(f"✓ Downloaded {len(df)} rows in {duration:.3f}s")
    print(f"  Throughput: {len(df) / duration:.1f} rows/sec")

    return {
        "method": "direct_download",
        "ticker": ticker,
        "rows": len(df),
        "duration_seconds": duration,
        "throughput_rows_per_sec": len(df) / duration
    }


async def benchmark_incremental_storage_query(ticker: str, days: int = 1825) -> dict:
    """
    Benchmark: Incremental storage query (new method).

    Args:
        ticker: Stock ticker
        days: Number of days (default: 5 years = 1825 days)

    Returns:
        Benchmark stats
    """
    print(f"\n2️⃣  Incremental storage query ({ticker}, {days} days)")
    print("=" * 60)

    async with get_db() as db:
        storage = StockPriceStorage(db)

        # Ensure data exists
        existing = await storage._check_existing_data(ticker)
        if existing == 0:
            print(f"⚠️  No data in DB, running backfill first...")
            await storage.backfill_stock_prices(ticker, years=5)

        # Warm-up
        _ = await storage.get_stock_prices(ticker, days=days)

        # Benchmark
        start_time = time.time()
        df = await storage.get_stock_prices(ticker, days=days)
        duration = time.time() - start_time

        print(f"✓ Retrieved {len(df)} rows in {duration:.3f}s")
        print(f"  Throughput: {len(df) / duration:.1f} rows/sec")

        return {
            "method": "incremental_storage",
            "ticker": ticker,
            "rows": len(df),
            "duration_seconds": duration,
            "throughput_rows_per_sec": len(df) / duration
        }


async def benchmark_incremental_update(ticker: str) -> dict:
    """
    Benchmark: Incremental update (daily sync).

    Args:
        ticker: Stock ticker

    Returns:
        Benchmark stats
    """
    print(f"\n3️⃣  Incremental update ({ticker}, new data only)")
    print("=" * 60)

    async with get_db() as db:
        storage = StockPriceStorage(db)

        # Run update
        start_time = time.time()
        stats = await storage.update_stock_prices_incremental(ticker)
        duration = time.time() - start_time

        print(f"✓ Updated {stats.get('new_rows', 0)} new rows in {duration:.3f}s")

        if stats.get('new_rows', 0) > 0:
            print(f"  Throughput: {stats['new_rows'] / duration:.1f} rows/sec")
        else:
            print(f"  Status: {stats.get('message', 'Already up to date')}")

        return {
            "method": "incremental_update",
            "ticker": ticker,
            "new_rows": stats.get('new_rows', 0),
            "duration_seconds": duration,
            "message": stats.get('message', '')
        }


async def run_full_benchmark(ticker: str = "AAPL"):
    """
    Run full benchmark suite.

    Args:
        ticker: Stock ticker to test

    Returns:
        Benchmark results
    """
    print(f"\n{'='*60}")
    print(f"🚀 Yahoo Finance Incremental Storage Benchmark")
    print(f"{'='*60}")
    print(f"Ticker: {ticker}")
    print(f"Test: 5 years of historical data")
    print(f"{'='*60}")

    results = []

    # Test 1: Direct download (current method)
    try:
        result1 = await benchmark_direct_download(ticker, years=5)
        results.append(result1)
    except Exception as e:
        print(f"✗ Direct download failed: {e}")
        result1 = None

    # Test 2: Incremental storage query (new method)
    try:
        result2 = await benchmark_incremental_storage_query(ticker, days=1825)
        results.append(result2)
    except Exception as e:
        print(f"✗ Incremental storage query failed: {e}")
        result2 = None

    # Test 3: Incremental update (daily sync)
    try:
        result3 = await benchmark_incremental_update(ticker)
        results.append(result3)
    except Exception as e:
        print(f"✗ Incremental update failed: {e}")
        result3 = None

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Benchmark Results Summary")
    print(f"{'='*60}")

    if result1 and result2:
        speedup = result1['duration_seconds'] / result2['duration_seconds']

        print(f"\n⚡ Speed Improvement:")
        print(f"  Direct download:      {result1['duration_seconds']:.3f}s")
        print(f"  Incremental storage:  {result2['duration_seconds']:.3f}s")
        print(f"  Speedup:              {speedup:.1f}x faster ✅")

        print(f"\n💾 Data Efficiency:")
        print(f"  Direct download:      {result1['rows']} rows (full download)")
        print(f"  Incremental update:   {result3.get('new_rows', 0)} new rows only")

        api_reduction = (1 - result3.get('new_rows', 1) / result1['rows']) * 100
        print(f"  API call reduction:   {api_reduction:.1f}% ✅")

        print(f"\n🎯 Achievement:")
        if speedup >= 20:
            print(f"  ✓ Target achieved: 20-50x speedup (actual: {speedup:.1f}x)")
        else:
            print(f"  ⚠️  Target not met: {speedup:.1f}x (target: 20-50x)")

    else:
        print("⚠️  Benchmark incomplete (some tests failed)")

    return results


async def benchmark_batch_update(num_tickers: int = 10):
    """
    Benchmark batch update performance.

    Args:
        num_tickers: Number of tickers to test
    """
    from backend.services.daily_price_sync import TOP_100_SP500
    from backend.data.stock_price_storage import batch_update_all_tickers

    tickers = TOP_100_SP500[:num_tickers]

    print(f"\n{'='*60}")
    print(f"🔄 Batch Update Benchmark ({num_tickers} tickers)")
    print(f"{'='*60}")

    async with get_db() as db:
        start_time = time.time()
        stats = await batch_update_all_tickers(db, tickers)
        duration = time.time() - start_time

        print(f"\n✓ Batch update complete:")
        print(f"  Tickers: {num_tickers}")
        print(f"  Updated: {stats['updated']}")
        print(f"  Up-to-date: {stats['up_to_date']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {num_tickers / duration:.1f} tickers/sec")

        if stats['total_new_rows'] > 0:
            print(f"  New rows: {stats['total_new_rows']}")

    return stats


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.WARNING)  # Reduce noise

    if len(sys.argv) > 1:
        if sys.argv[1] == "batch":
            # Batch update benchmark
            num_tickers = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            asyncio.run(benchmark_batch_update(num_tickers))
        else:
            # Single ticker benchmark
            ticker = sys.argv[1].upper()
            asyncio.run(run_full_benchmark(ticker))
    else:
        # Default: AAPL benchmark
        asyncio.run(run_full_benchmark("AAPL"))
