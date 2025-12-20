"""
Stock Price Scheduler Service.

Automated daily stock price updates using incremental update strategy.

Features:
- Daily scheduled updates (6:00 AM)
- Error recovery with retry logic
- Performance monitoring
- Batch processing for multiple tickers

Cost Savings:
- Before: 100 tickers × 5 years × 365 days = 182,500 API calls/day
- After: 100 tickers × 1 day = 100 API calls/day
- Reduction: 99.95%
"""

import logging
import asyncio
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data.stock_price_storage import StockPriceStorage, batch_update_all_tickers
from backend.core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class UpdateStats:
    """Statistics for stock price updates."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_tickers: int = 0
    successful: int = 0
    failed: int = 0
    up_to_date: int = 0
    total_new_rows: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tickers == 0:
            return 0.0
        return (self.successful / self.total_tickers) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_tickers": self.total_tickers,
            "successful": self.successful,
            "failed": self.failed,
            "up_to_date": self.up_to_date,
            "total_new_rows": self.total_new_rows,
            "success_rate": self.success_rate,
            "errors": self.errors
        }


class StockPriceScheduler:
    """
    Automated stock price update scheduler.
    
    Features:
    - Daily updates at 6:00 AM
    - Error recovery with retry logic
    - Performance monitoring
    - Batch processing
    
    Usage:
        scheduler = StockPriceScheduler(tickers=["AAPL", "MSFT", ...])
        scheduler.start()
    """
    
    def __init__(
        self,
        tickers: List[str],
        schedule_time: time = time(hour=6, minute=0),
        max_retries: int = 3,
        retry_delay_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize stock price scheduler.
        
        Args:
            tickers: List of stock tickers to update
            schedule_time: Time to run daily update (default: 6:00 AM)
            max_retries: Maximum retry attempts for failed updates
            retry_delay_seconds: Delay between retries in seconds
        """
        self.tickers = tickers
        self.schedule_time = schedule_time
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        self.scheduler = AsyncIOScheduler()
        self.last_update_stats: Optional[UpdateStats] = None
        self.is_running = False
        
        logger.info(
            f"StockPriceScheduler initialized with {len(tickers)} tickers, "
            f"scheduled at {schedule_time}"
        )
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily update
        self.scheduler.add_job(
            self._run_daily_update,
            trigger=CronTrigger(
                hour=self.schedule_time.hour,
                minute=self.schedule_time.minute
            ),
            id="daily_stock_price_update",
            name="Daily Stock Price Update",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"Scheduler started - Daily updates at {self.schedule_time}"
        )
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def _run_daily_update(self):
        """Run daily stock price update with error recovery."""
        logger.info("Starting daily stock price update")
        
        stats = UpdateStats()
        stats.total_tickers = len(self.tickers)
        
        try:
            async with get_db() as db:
                # Batch update all tickers
                result = await batch_update_all_tickers(db, self.tickers)
                
                stats.successful = result.get("updated", 0)
                stats.up_to_date = result.get("up_to_date", 0)
                stats.failed = result.get("errors", 0)
                stats.total_new_rows = result.get("total_new_rows", 0)
                stats.end_time = datetime.now()
                
                # Retry failed tickers
                if stats.failed > 0:
                    logger.warning(f"{stats.failed} tickers failed, retrying...")
                    await self._retry_failed_tickers(db, stats)
                
                self.last_update_stats = stats
                
                logger.info(
                    f"Daily update complete: {stats.successful} updated, "
                    f"{stats.up_to_date} up-to-date, {stats.failed} failed "
                    f"in {stats.duration_seconds:.2f}s"
                )
                
        except Exception as e:
            logger.error(f"Daily update failed: {e}", exc_info=True)
            stats.end_time = datetime.now()
            stats.errors.append({
                "error": "Daily update exception",
                "message": str(e)
            })
            self.last_update_stats = stats
    
    async def _retry_failed_tickers(
        self,
        db: AsyncSession,
        stats: UpdateStats
    ):
        """
        Retry failed ticker updates.
        
        Args:
            db: Database session
            stats: Update statistics to update
        """
        storage = StockPriceStorage(db)
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Retry attempt {attempt}/{self.max_retries}")
            
            # Wait before retry
            await asyncio.sleep(self.retry_delay_seconds)
            
            # Retry each ticker
            retry_count = 0
            for ticker in self.tickers:
                try:
                    result = await storage.update_stock_prices_incremental(ticker)
                    
                    if "error" not in result and result.get("new_rows", 0) > 0:
                        stats.successful += 1
                        stats.failed -= 1
                        stats.total_new_rows += result["new_rows"]
                        retry_count += 1
                        
                except Exception as e:
                    logger.error(f"Retry failed for {ticker}: {e}")
                    stats.errors.append({
                        "ticker": ticker,
                        "attempt": attempt,
                        "error": str(e)
                    })
            
            logger.info(f"Retry {attempt}: {retry_count} tickers recovered")
            
            if stats.failed == 0:
                logger.info("All tickers recovered")
                break
    
    async def run_manual_update(self) -> UpdateStats:
        """
        Run manual update (for testing or immediate update).
        
        Returns:
            Update statistics
        """
        logger.info("Running manual stock price update")
        await self._run_daily_update()
        return self.last_update_stats
    
    def get_last_update_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get last update statistics.
        
        Returns:
            Statistics dictionary or None
        """
        if self.last_update_stats:
            return self.last_update_stats.to_dict()
        return None


# Global scheduler instance
_scheduler: Optional[StockPriceScheduler] = None


def get_stock_price_scheduler(
    tickers: Optional[List[str]] = None
) -> StockPriceScheduler:
    """
    Get or create stock price scheduler singleton.
    
    Args:
        tickers: List of tickers (required for first call)
    
    Returns:
        StockPriceScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        if not tickers:
            raise ValueError("Tickers required for first initialization")
        _scheduler = StockPriceScheduler(tickers=tickers)
    
    return _scheduler


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Example tickers (top 10 stocks)
        tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "BRK-B", "UNH", "JNJ"
        ]
        
        scheduler = StockPriceScheduler(
            tickers=tickers,
            schedule_time=time(hour=6, minute=0)
        )
        
        # Run manual update for testing
        print("Running manual update...")
        stats = await scheduler.run_manual_update()
        
        if stats:
            print("\n=== Update Statistics ===")
            print(f"Duration: {stats.duration_seconds:.2f}s")
            print(f"Successful: {stats.successful}")
            print(f"Up-to-date: {stats.up_to_date}")
            print(f"Failed: {stats.failed}")
            print(f"New rows: {stats.total_new_rows}")
            print(f"Success rate: {stats.success_rate:.1f}%")
        
        # Start scheduler (would run daily at 6:00 AM)
        # scheduler.start()
        # Keep running...
        # await asyncio.sleep(3600)  # Run for 1 hour
        # scheduler.stop()
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
