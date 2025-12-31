"""
Daily Learning Scheduler - Automated Learning Execution

This module schedules and executes daily learning cycles automatically.

Key Features:
- Scheduled daily execution (e.g., midnight)
- Error handling and retry logic
- Learning result persistence
- Alerting on failures

Author: AI Trading System
Date: 2025-12-23
Phase: 25.3
"""

import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional

from backend.ai.learning.learning_orchestrator import LearningOrchestrator

logger = logging.getLogger(__name__)


class DailyLearningScheduler:
    """
    Automated scheduler for daily AI learning cycles.
    
    Runs learning at a specific time each day (e.g., midnight).
    
    Example:
        scheduler = DailyLearningScheduler(run_time=time(0, 0))  # Midnight
        await scheduler.start()  # Runs indefinitely
    """
    
    def __init__(
        self,
        run_times: list[time] = None,  # Multiple run times per day
        retry_on_failure: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize scheduler.

        Args:
            run_times: List of times to run learning each day (e.g., [time(10,0), time(16,0)])
                      If None, defaults to [time(0, 0)] (midnight)
            retry_on_failure: Retry if learning fails (default: True)
            max_retries: Max retry attempts (default: 3)
        """
        self.run_times = run_times if run_times else [time(0, 0)]
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries

        self.orchestrator = LearningOrchestrator()
        self.is_running = False

        logger.info(
            f"DailyLearningScheduler initialized: "
            f"run_times={[t.strftime('%H:%M') for t in self.run_times]}, "
            f"retry={retry_on_failure}, "
            f"max_retries={max_retries}"
        )
    
    async def start(self):
        """
        Start the scheduler (runs indefinitely).

        Supports multiple run times per day (e.g., after US market close and after KR market close).

        This should be run in a background task:
            asyncio.create_task(scheduler.start())

        Example:
            >>> scheduler = DailyLearningScheduler(run_times=[time(10,0), time(16,0)])
            >>> await scheduler.start()  # Blocks until stopped
        """
        self.is_running = True
        logger.info(f"🕐 Daily learning scheduler started with {len(self.run_times)} run times per day")

        while self.is_running:
            # Calculate time until next run (from all run times)
            now = datetime.now()
            upcoming_runs = []

            for run_time in self.run_times:
                next_run = datetime.combine(now.date(), run_time)

                # If we've passed today's run time, schedule for tomorrow
                if now >= next_run:
                    next_run = datetime.combine(now.date(), run_time) + timedelta(days=1)

                upcoming_runs.append(next_run)

            # Get the earliest upcoming run
            next_run = min(upcoming_runs)
            wait_seconds = (next_run - now).total_seconds()

            logger.info(f"⏰ Next learning cycle scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️  Waiting {wait_seconds/3600:.1f} hours...")

            # Wait until next run time
            await asyncio.sleep(wait_seconds)

            # Run learning cycle
            if self.is_running:
                await self._execute_with_retry()
    
    async def _execute_with_retry(self):
        """Execute learning cycle with retry logic (non-blocking)."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🚀 Executing daily learning cycle (attempt {attempt}/{self.max_retries})")
                logger.info("⚡ Running in background - main server remains responsive")

                # Execute learning cycle (already async, won't block event loop)
                results = await self.orchestrator.run_daily_learning_cycle()

                logger.info(f"✅ Learning cycle completed: {results['agents_learned']}/6 agents")
                logger.info(f"⏱️  Duration: {results.get('duration_seconds', 0):.1f}s")

                # Success - exit retry loop
                break

            except Exception as e:
                logger.error(f"❌ Learning cycle failed (attempt {attempt}): {str(e)}", exc_info=True)

                if attempt < self.max_retries and self.retry_on_failure:
                    wait_minutes = attempt * 5  # Exponential backoff: 5, 10, 15 min
                    logger.info(f"⏳ Retrying in {wait_minutes} minutes...")
                    await asyncio.sleep(wait_minutes * 60)
                else:
                    logger.error("❌ Max retries exceeded. Learning cycle skipped for today.")
                    # In production: Send alert to admin
                    break
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("🛑 Daily learning scheduler stopped")
    
    async def run_once(self):
        """
        Run learning cycle once (for testing).
        
        Example:
            >>> scheduler = DailyLearningScheduler()
            >>> results = await scheduler.run_once()
        """
        logger.info("🧪 Running single learning cycle (test mode)")
        return await self.orchestrator.run_daily_learning_cycle()


# Example usage
if __name__ == "__main__":
    from datetime import timedelta
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Testing DailyLearningScheduler\n")
    
    async def test_scheduler():
        # Create scheduler with multiple run times (for testing)
        now = datetime.now()
        test_time_1 = (now + timedelta(seconds=10)).time()
        test_time_2 = (now + timedelta(seconds=20)).time()

        scheduler = DailyLearningScheduler(run_times=[test_time_1, test_time_2])
        
        # Run once for testing
        print("Running single learning cycle...")
        results = await scheduler.run_once()
        
        print(f"\nResults:")
        print(f"Success rate: {results['success_rate']:.0%}")
        print(f"Duration: {results['duration_seconds']:.1f}s")
    
    # Run test
    asyncio.run(test_scheduler())
