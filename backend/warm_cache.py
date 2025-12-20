"""
Cache Warming Script.

Usage (run from backend directory):
    cd backend

    # Manual warming (immediate)
    python warm_cache.py

    # Scheduled warming (before market open)
    python warm_cache.py --scheduled

    # Custom tickers
    python warm_cache.py --portfolio AAPL,MSFT,GOOGL --watchlist TSLA,NVDA

Examples:
    # Warm portfolio + watchlist + top 30
    python warm_cache.py --portfolio AAPL,MSFT --watchlist TSLA,NVDA,AMD

    # Warm only top 50 market cap stocks
    python warm_cache.py --top-market-cap 50

    # Schedule for next market open
    python warm_cache.py --scheduled --minutes-before 30
"""

import argparse
import asyncio
import logging
import sys

from data.feature_store import FeatureStore
from data.feature_store.cache_warming import CacheWarmer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main cache warming execution."""
    parser = argparse.ArgumentParser(
        description="Warm Feature Store cache before market open"
    )
    
    # Ticker lists
    parser.add_argument(
        "--portfolio",
        type=str,
        default="",
        help="Portfolio tickers (comma-separated, e.g., AAPL,MSFT,GOOGL)",
    )
    parser.add_argument(
        "--watchlist",
        type=str,
        default="",
        help="Watchlist tickers (comma-separated, e.g., TSLA,NVDA,AMD)",
    )
    parser.add_argument(
        "--top-market-cap",
        type=int,
        default=30,
        help="Number of top market cap stocks to warm (default: 30)",
    )
    
    # Scheduling
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Schedule warming before market open (instead of immediate)",
    )
    parser.add_argument(
        "--minutes-before",
        type=int,
        default=30,
        help="Minutes before market open to warm cache (default: 30)",
    )
    
    # Performance
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum concurrent workers (default: 10)",
    )
    
    args = parser.parse_args()
    
    # Parse ticker lists
    portfolio_tickers = (
        [t.strip().upper() for t in args.portfolio.split(",") if t.strip()]
        if args.portfolio
        else []
    )
    watchlist_tickers = (
        [t.strip().upper() for t in args.watchlist.split(",") if t.strip()]
        if args.watchlist
        else []
    )
    
    # If no tickers specified, use defaults from config
    if not portfolio_tickers and not watchlist_tickers:
        logger.info("No tickers specified, using defaults from config...")
        from config import get_settings
        settings = get_settings()
        default_tickers = settings.feature_cache_warm_up_tickers.split(",")
        watchlist_tickers = [t.strip() for t in default_tickers]
    
    logger.info("=" * 80)
    logger.info("CACHE WARMING STARTED")
    logger.info("=" * 80)
    logger.info(f"Portfolio tickers: {portfolio_tickers or 'None'}")
    logger.info(f"Watchlist tickers: {watchlist_tickers or 'None'}")
    logger.info(f"Top market cap count: {args.top_market_cap}")
    logger.info(f"Max workers: {args.max_workers}")
    logger.info(f"Scheduled: {args.scheduled}")
    if args.scheduled:
        logger.info(f"Minutes before open: {args.minutes_before}")
    logger.info("=" * 80)
    
    # Initialize Feature Store and Cache Warmer
    feature_store = FeatureStore()
    await feature_store.initialize()
    
    cache_warmer = CacheWarmer(feature_store)
    
    try:
        if args.scheduled:
            # Schedule warming before market open
            logger.info(
                f"🗓️  Scheduling cache warming {args.minutes_before} minutes "
                "before market open..."
            )
            metrics = await cache_warmer.warm_before_market_open(
                portfolio_tickers=portfolio_tickers or None,
                watchlist_tickers=watchlist_tickers or None,
                minutes_before_open=args.minutes_before,
            )
        else:
            # Immediate warming
            logger.info("🔥 Starting immediate cache warming...")
            metrics = await cache_warmer.warm_cache(
                portfolio_tickers=portfolio_tickers or None,
                watchlist_tickers=watchlist_tickers or None,
                top_market_cap_count=args.top_market_cap,
                max_workers=args.max_workers,
            )
        
        # Print results
        logger.info("")
        logger.info("=" * 80)
        logger.info("CACHE WARMING RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total tickers:    {metrics['total_tickers']}")
        logger.info(f"Successful:       {metrics['successful']}")
        logger.info(f"Failed:           {metrics['failed']}")
        logger.info(f"Duration:         {metrics['duration_seconds']:.1f}s")
        logger.info(f"Speed:            {metrics['tickers_per_second']:.1f} tickers/s")
        logger.info("=" * 80)
        
        # Check Feature Store metrics
        fs_metrics = feature_store.get_metrics()
        logger.info("")
        logger.info("FEATURE STORE METRICS")
        logger.info("=" * 80)
        logger.info(f"Cache hits (Redis):      {fs_metrics['cache_hits_redis']}")
        logger.info(f"Cache hits (TimescaleDB): {fs_metrics['cache_hits_timescale']}")
        logger.info(f"Cache misses:            {fs_metrics['cache_misses']}")
        logger.info(f"Cache hit rate:          {fs_metrics['cache_hit_rate']:.1%}")
        logger.info("=" * 80)
        
        # Success if > 90% warmed
        success_rate = metrics['successful'] / metrics['total_tickers']
        if success_rate >= 0.9:
            logger.info("✅ Cache warming completed successfully!")
            return 0
        else:
            logger.warning(
                f"⚠️  Cache warming completed with warnings "
                f"(success rate: {success_rate:.1%})"
            )
            return 1
            
    except Exception as e:
        logger.error(f"❌ Cache warming failed: {e}", exc_info=True)
        return 1
        
    finally:
        await feature_store.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)