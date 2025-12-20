"""
Price Update Scheduler

Periodic updates of portfolio prices and performance tracking

Features:
- Background task for price updates
- Configurable update interval
- Automatic performance calculation
- Error recovery

Usage:
    from backend.market_data.price_scheduler import PriceUpdateScheduler

    scheduler = PriceUpdateScheduler(interval_seconds=3600)  # 1 hour
    await scheduler.start()
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from backend.database.repository import (
    SignalRepository,
    PerformanceRepository,
    get_sync_session
)
from backend.database.models import TradingSignal, SignalPerformance
from backend.market_data.price_fetcher import get_multiple_prices

logger = logging.getLogger(__name__)


class PriceUpdateScheduler:
    """
    Scheduler for periodic portfolio price updates

    Updates current prices for all active positions and calculates performance.
    """

    def __init__(
        self,
        interval_seconds: int = 3600,  # 1 hour default
        update_closed_positions: bool = True
    ):
        """
        Args:
            interval_seconds: Update interval in seconds
            update_closed_positions: Whether to update historical performance
        """
        self.interval_seconds = interval_seconds
        self.update_closed_positions = update_closed_positions
        self.running = False
        self.last_update_time: Optional[datetime] = None
        self.update_count = 0
        self.error_count = 0

    async def update_active_positions(self, db: Session) -> Dict:
        """
        Update prices for all active positions

        Returns:
            dict: Update statistics
        """
        signal_repo = SignalRepository(db)

        # Get all active signals (entry price set, no exit price)
        active_signals = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).all()

        if not active_signals:
            logger.info("No active positions to update")
            return {
                "total_positions": 0,
                "updated": 0,
                "failed": 0
            }

        # Collect unique tickers
        tickers = list(set(signal.ticker for signal in active_signals))

        # Fetch current prices
        logger.info(f"Fetching prices for {len(tickers)} tickers...")
        current_prices = get_multiple_prices(tickers, use_cache=False)  # Force fresh prices

        updated_count = 0
        failed_count = 0

        for signal in active_signals:
            current_price = current_prices.get(signal.ticker)

            if current_price is None:
                logger.warning(f"Failed to fetch price for {signal.ticker}")
                failed_count += 1
                continue

            # Calculate return based on action
            if signal.action == "BUY":
                return_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
            else:  # SELL/SHORT
                return_pct = ((signal.entry_price - current_price) / signal.entry_price) * 100

            # Update signal (store latest price check)
            signal.updated_at = datetime.now()

            logger.debug(
                f"{signal.ticker}: ${signal.entry_price:.2f} → ${current_price:.2f} "
                f"({return_pct:+.2f}%)"
            )

            updated_count += 1

        db.commit()

        logger.info(
            f"Price update complete: {updated_count} updated, {failed_count} failed"
        )

        return {
            "total_positions": len(active_signals),
            "updated": updated_count,
            "failed": failed_count,
            "tickers": tickers,
            "prices": current_prices
        }

    async def update_signal_performance(self, db: Session) -> Dict:
        """
        Update performance records for closed positions

        Creates/updates SignalPerformance records for signals that have been realized.
        """
        perf_repo = PerformanceRepository(db)

        # Get signals with exit prices but no performance record
        closed_signals = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.isnot(None)
        ).all()

        if not closed_signals:
            return {
                "total_closed": 0,
                "created": 0
            }

        created_count = 0

        for signal in closed_signals:
            # Check if performance record already exists
            existing = db.query(SignalPerformance).filter(
                SignalPerformance.signal_id == signal.id
            ).first()

            if existing:
                continue

            # Calculate actual return
            if signal.action == "BUY":
                actual_return = ((signal.exit_price - signal.entry_price) / signal.entry_price) * 100
            else:
                actual_return = ((signal.entry_price - signal.exit_price) / signal.entry_price) * 100

            # Create performance record
            performance = SignalPerformance(
                signal_id=signal.id,
                ticker=signal.ticker,
                signal_type=signal.signal_type,
                action=signal.action,
                confidence=signal.confidence,
                entry_price=signal.entry_price,
                exit_price=signal.exit_price,
                actual_return=actual_return,
                signal_generated_at=signal.generated_at,
                position_opened_at=signal.generated_at,  # Assuming immediate execution
                position_closed_at=datetime.now()
            )

            db.add(performance)
            created_count += 1

            logger.debug(
                f"Performance recorded: {signal.ticker} {signal.signal_type} "
                f"{actual_return:+.2f}%"
            )

        db.commit()

        logger.info(f"Created {created_count} new performance records")

        return {
            "total_closed": len(closed_signals),
            "created": created_count
        }

    async def run_single_update(self) -> Dict:
        """
        Run a single update cycle

        Returns:
            dict: Update statistics
        """
        try:
            db = get_sync_session()

            try:
                # Update active positions
                active_stats = await self.update_active_positions(db)

                # Update performance records for closed positions
                perf_stats = {}
                if self.update_closed_positions:
                    perf_stats = await self.update_signal_performance(db)

                self.last_update_time = datetime.now()
                self.update_count += 1

                return {
                    "success": True,
                    "timestamp": self.last_update_time.isoformat(),
                    "active_positions": active_stats,
                    "performance": perf_stats
                }

            finally:
                db.close()

        except Exception as e:
            self.error_count += 1
            logger.error(f"Price update failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def start(self):
        """
        Start the scheduler (runs continuously)
        """
        logger.info("=" * 80)
        logger.info("Price Update Scheduler Starting")
        logger.info("=" * 80)
        logger.info(f"Update interval: {self.interval_seconds} seconds ({self.interval_seconds/60:.1f} minutes)")
        logger.info(f"Update closed positions: {self.update_closed_positions}")
        logger.info("=" * 80)

        self.running = True

        try:
            while self.running:
                logger.info(f"\n[Price Update #{self.update_count + 1}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Run update
                result = await self.run_single_update()

                if result["success"]:
                    logger.info(f"✓ Update successful")
                else:
                    logger.error(f"✗ Update failed: {result.get('error')}")

                # Wait for next cycle
                logger.info(f"Next update in {self.interval_seconds} seconds...")
                await asyncio.sleep(self.interval_seconds)

        except KeyboardInterrupt:
            logger.info("\n\n[STOPPED] Scheduler stopped by user (Ctrl+C)")
        except Exception as e:
            logger.critical(f"Scheduler crashed: {e}")
            raise
        finally:
            self.running = False
            logger.info("Price Update Scheduler Stopped")

    def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("Stopping price update scheduler...")
        self.running = False

    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "running": self.running,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "interval_seconds": self.interval_seconds,
            "uptime_seconds": (datetime.now() - self.last_update_time).total_seconds() if self.last_update_time else None
        }


# ============================================
# CLI Script
# ============================================

async def main():
    """Run price update scheduler from command line"""
    import argparse

    parser = argparse.ArgumentParser(description="Portfolio Price Update Scheduler")
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Update interval in seconds (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )
    parser.add_argument(
        "--no-performance",
        action="store_true",
        help="Skip updating closed position performance"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Create scheduler
    scheduler = PriceUpdateScheduler(
        interval_seconds=args.interval,
        update_closed_positions=not args.no_performance
    )

    if args.once:
        # Single run
        logger.info("Running single price update...")
        result = await scheduler.run_single_update()

        if result["success"]:
            logger.info("✓ Update completed successfully")
            print("\nResults:")
            print(f"  Active positions: {result['active_positions']}")
            if result.get('performance'):
                print(f"  Performance records: {result['performance']}")
        else:
            logger.error(f"✗ Update failed: {result.get('error')}")
    else:
        # Continuous run
        await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
