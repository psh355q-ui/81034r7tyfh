"""
Daily Stock Price Sync Scheduler.

Automatically updates stock prices every day at 5 PM (after market close).

Features:
- Runs daily at 17:00 (configurable)
- Updates top 100 S&P 500 stocks
- Incremental updates only (fast)
- Error recovery and retry
- Performance monitoring

Deployment:
- Linux/NAS: systemd timer or cron
- Docker: container restart policy
- Development: Manual trigger or APScheduler
"""

import logging
import asyncio
from datetime import time as dt_time
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.core.database import get_db
from backend.data.stock_price_storage import batch_update_all_tickers

logger = logging.getLogger(__name__)


# Top 100 S&P 500 stocks by market cap
TOP_100_SP500 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "JPM", "V", "XOM", "WMT", "PG", "MA", "HD", "CVX", "ABBV", "MRK",
    "KO", "PEP", "COST", "AVGO", "TMO", "MCD", "ACN", "CSCO", "ABT", "LLY",
    "DHR", "NKE", "VZ", "ADBE", "CRM", "NEE", "TXN", "CMCSA", "PM", "UNP",
    "DIS", "WFC", "BMY", "ORCL", "RTX", "T", "HON", "QCOM", "INTC", "AMD",
    "UPS", "IBM", "AMGN", "BA", "CAT", "GE", "SBUX", "INTU", "LOW", "AXP",
    "MS", "SPGI", "BLK", "DE", "GS", "C", "MMM", "MDT", "NOW", "GILD",
    "PLD", "AMT", "CVS", "ISRG", "SYK", "TJX", "ZTS", "MO", "CI", "ADP",
    "BKNG", "CB", "TMUS", "DUK", "MDLZ", "PGR", "SO", "SCHW", "EOG", "USB",
    "SLB", "BDX", "CL", "CME", "REGN", "ITW", "PNC", "AON", "MMC", "BSX"
]


class DailyPriceSyncScheduler:
    """
    Daily stock price sync scheduler.

    Runs incremental updates for all configured tickers at specified time.

    Usage:
        scheduler = DailyPriceSyncScheduler()
        await scheduler.start()  # Runs in background

        # Or manual trigger
        await scheduler.sync_now()
    """

    def __init__(
        self,
        tickers: Optional[List[str]] = None,
        sync_time: str = "17:00",  # 5 PM (after market close)
        timezone: str = "America/New_York"
    ):
        """
        Initialize scheduler.

        Args:
            tickers: List of tickers to sync (default: TOP_100_SP500)
            sync_time: Daily sync time in HH:MM format
            timezone: Timezone for sync time
        """
        self.tickers = tickers or TOP_100_SP500
        self.sync_time = sync_time
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.is_running = False

        logger.info(
            f"Initialized daily price sync: {len(self.tickers)} tickers, "
            f"sync at {sync_time} {timezone}"
        )

    async def sync_now(self) -> dict:
        """
        Trigger sync immediately (manual).

        Returns:
            Statistics dict
        """
        logger.info(f"Starting manual sync for {len(self.tickers)} tickers")

        async with get_db() as db:
            stats = await batch_update_all_tickers(db, self.tickers)

        logger.info(
            f"Manual sync complete: {stats['updated']} updated, "
            f"{stats['errors']} errors, {stats['duration_seconds']:.2f}s"
        )

        return stats

    async def _scheduled_sync(self):
        """Internal: Scheduled sync job."""
        logger.info("Starting scheduled price sync")

        try:
            stats = await self.sync_now()

            # Log summary
            logger.info(
                f"✓ Scheduled sync complete: "
                f"{stats['updated']} tickers updated, "
                f"{stats['total_new_rows']} new rows, "
                f"{stats['errors']} errors"
            )

            # Alert on high error rate
            if stats['errors'] > len(self.tickers) * 0.1:  # >10% errors
                logger.error(
                    f"High error rate: {stats['errors']}/{len(self.tickers)} tickers failed"
                )
                # TODO: Send alert via Telegram/Slack

        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}", exc_info=True)
            # TODO: Send error alert

    def start(self):
        """
        Start the scheduler (runs in background).

        Example:
            scheduler = DailyPriceSyncScheduler()
            scheduler.start()  # Non-blocking

            # Keep main thread alive
            while True:
                await asyncio.sleep(60)
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Parse sync time
        hour, minute = map(int, self.sync_time.split(":"))

        # Add job
        self.scheduler.add_job(
            self._scheduled_sync,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            id="daily_price_sync",
            name="Daily Stock Price Sync",
            replace_existing=True
        )

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info(
            f"✓ Scheduler started: Daily sync at {self.sync_time} {self.timezone}"
        )

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False

        logger.info("Scheduler stopped")

    def get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time."""
        if not self.is_running:
            return None

        job = self.scheduler.get_job("daily_price_sync")
        if job and job.next_run_time:
            return str(job.next_run_time)

        return None


# Singleton instance
_scheduler_instance: Optional[DailyPriceSyncScheduler] = None


def get_price_sync_scheduler() -> DailyPriceSyncScheduler:
    """Get or create scheduler singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DailyPriceSyncScheduler()
    return _scheduler_instance


# FastAPI integration
async def start_price_sync_on_startup():
    """
    Start price sync scheduler on FastAPI startup.

    Add to main.py:
        @app.on_event("startup")
        async def startup():
            await start_price_sync_on_startup()
    """
    scheduler = get_price_sync_scheduler()
    scheduler.start()

    logger.info(
        f"✓ Price sync scheduler started "
        f"(next run: {scheduler.get_next_run_time()})"
    )


async def stop_price_sync_on_shutdown():
    """
    Stop price sync scheduler on FastAPI shutdown.

    Add to main.py:
        @app.on_event("shutdown")
        async def shutdown():
            await stop_price_sync_on_shutdown()
    """
    scheduler = get_price_sync_scheduler()
    scheduler.stop()

    logger.info("Price sync scheduler stopped")


# CLI commands
async def cli_sync_now():
    """CLI: Trigger sync immediately."""
    scheduler = get_price_sync_scheduler()
    stats = await scheduler.sync_now()

    print(f"\n✓ Sync complete:")
    print(f"  Updated: {stats['updated']} tickers")
    print(f"  New rows: {stats['total_new_rows']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Duration: {stats['duration_seconds']:.2f}s")


async def cli_backfill_all(years: int = 5):
    """
    CLI: Backfill all tickers (initial setup).

    Args:
        years: Number of years to backfill
    """
    from backend.data.stock_price_storage import StockPriceStorage

    tickers = TOP_100_SP500

    print(f"Backfilling {len(tickers)} tickers ({years} years)...")
    print("This will take ~10 minutes. Press Ctrl+C to cancel.\n")

    success = 0
    errors = 0

    async with get_db() as db:
        storage = StockPriceStorage(db)

        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")

            try:
                stats = await storage.backfill_stock_prices(ticker, years=years)

                if "error" in stats:
                    print(f"✗ {stats['error']}")
                    errors += 1
                else:
                    print(f"✓ {stats['rows_inserted']} rows")
                    success += 1

            except Exception as e:
                print(f"✗ {e}")
                errors += 1

    print(f"\n✓ Backfill complete: {success} success, {errors} errors")


# Example usage
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        # Initial backfill
        asyncio.run(cli_backfill_all(years=5))
    elif len(sys.argv) > 1 and sys.argv[1] == "sync":
        # Manual sync
        asyncio.run(cli_sync_now())
    else:
        # Start scheduler
        print("Starting daily price sync scheduler...")
        print("Sync time: 17:00 America/New_York")
        print("Press Ctrl+C to stop\n")

        scheduler = get_price_sync_scheduler()
        scheduler.start()

        print(f"Next run: {scheduler.get_next_run_time()}\n")

        # Keep alive
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop()
