"""
Accountability Scheduler - Automated News Interpretation Accuracy Tracking

1시간마다 자동으로 실행되어 뉴스 해석의 정확도를 추적합니다.

Key Features:
- 1시간마다 자동 실행 (매시 정각)
- 1h/1d/3d time horizon 검증
- NIA (News Interpretation Accuracy) 자동 계산
- Failure Learning Agent 트리거 (틀린 판단 발견 시)

Integration:
- Daily Learning Scheduler와 통합 가능
- FastAPI 서버와 독립 실행 가능

Author: AI Trading System
Date: 2025-12-30
Phase: Accountability System (Phase 26)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from backend.automation.price_tracking_verifier import PriceTrackingVerifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccountabilityScheduler:
    """
    Accountability 시스템 자동화 스케줄러

    매시간 실행되어 뉴스 해석 후 1h/1d/3d 가격 변화를 추적하고
    AI 해석의 정확도를 자동으로 검증합니다.

    Example:
        scheduler = AccountabilityScheduler()
        await scheduler.start()  # Runs indefinitely
    """

    def __init__(
        self,
        run_interval_minutes: int = 60,  # 1시간마다 실행
        retry_on_failure: bool = True,
        max_retries: int = 3,
        trigger_failure_learning: bool = True  # 틀린 판단 발견 시 Failure Learning Agent 트리거
    ):
        """
        Initialize scheduler.

        Args:
            run_interval_minutes: 실행 간격 (분) - 기본 60분 (1시간)
            retry_on_failure: 실패 시 재시도 여부
            max_retries: 최대 재시도 횟수
            trigger_failure_learning: 틀린 판단 발견 시 Failure Learning Agent 트리거 여부
        """
        self.run_interval_minutes = run_interval_minutes
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries
        self.trigger_failure_learning = trigger_failure_learning

        self.verifier = PriceTrackingVerifier()
        self.is_running = False

        logger.info(
            f"AccountabilityScheduler initialized: "
            f"interval={run_interval_minutes}min, "
            f"retry={retry_on_failure}, "
            f"max_retries={max_retries}, "
            f"failure_learning={trigger_failure_learning}"
        )

    async def start(self):
        """
        Start the scheduler (runs indefinitely).

        매시간 정각에 실행되도록 조정됩니다.
        예: 03:00, 04:00, 05:00...

        This should be run in a background task:
            asyncio.create_task(scheduler.start())

        Example:
            >>> scheduler = AccountabilityScheduler()
            >>> await scheduler.start()  # Blocks until stopped
        """
        self.is_running = True
        logger.info(f"⏰ Accountability scheduler started (every {self.run_interval_minutes} min)")

        while self.is_running:
            # Calculate time until next run (next hour)
            now = datetime.now()

            # Next hour at 00 minutes
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            wait_seconds = (next_run - now).total_seconds()

            logger.info(f"⏰ Next accountability verification: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️  Waiting {wait_seconds/60:.1f} minutes...")

            # Wait until next run time
            await asyncio.sleep(wait_seconds)

            # Run verification
            if self.is_running:
                await self._execute_with_retry()

    async def _execute_with_retry(self):
        """Execute accountability verification with retry logic (non-blocking)."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🚀 Executing accountability verification (attempt {attempt}/{self.max_retries})")
                logger.info("⚡ Running in background - main server remains responsive")

                # Execute all horizon verifications (1h, 1d, 3d)
                results = await self.verifier.verify_all_horizons()

                # Log results
                logger.info("=" * 60)
                logger.info("✅ Accountability Verification Complete")
                logger.info("=" * 60)

                total_verified = 0
                total_correct = 0
                failed_interpretations = []

                for horizon, result in results.items():
                    logger.info(
                        f"{horizon}: {result['correct_count']}/{result['verified_count']} correct "
                        f"({result['accuracy']*100:.1f}%)"
                    )
                    total_verified += result['verified_count']
                    total_correct += result['correct_count']

                    # Track failed interpretations (for 1d only - main metric)
                    if horizon == "1d" and result['verified_count'] > 0:
                        failed_count = result['verified_count'] - result['correct_count']
                        if failed_count > 0:
                            logger.warning(f"⚠️  {failed_count} failed interpretations detected on 1d horizon")
                            # TODO: Query DB for failed interpretation IDs

                # Calculate overall NIA (News Interpretation Accuracy)
                if total_verified > 0:
                    nia = (total_correct / total_verified) * 100
                    logger.info(f"📊 Overall NIA (News Interpretation Accuracy): {nia:.1f}%")

                    # Alert if NIA is below threshold
                    if nia < 50.0:
                        logger.warning(f"⚠️  NIA below threshold (50%): {nia:.1f}%")
                else:
                    logger.info("📊 No interpretations to verify at this time")

                logger.info("=" * 60)

                # Trigger Failure Learning Agent if enabled and failures detected
                if self.trigger_failure_learning and total_verified > 0 and total_correct < total_verified:
                    failed_count = total_verified - total_correct
                    logger.info(f"🔍 Triggering Failure Learning Agent for {failed_count} failed interpretations...")

                    # TODO: Implement Failure Learning Agent trigger
                    # await self._trigger_failure_learning(failed_interpretations)

                # Success - exit retry loop
                break

            except Exception as e:
                logger.error(f"❌ Accountability verification failed (attempt {attempt}): {str(e)}", exc_info=True)

                if attempt < self.max_retries and self.retry_on_failure:
                    wait_minutes = attempt * 5  # Exponential backoff: 5, 10, 15 min
                    logger.info(f"⏳ Retrying in {wait_minutes} minutes...")
                    await asyncio.sleep(wait_minutes * 60)
                else:
                    logger.error("❌ Max retries exceeded. Accountability verification skipped for this hour.")
                    break

    async def _trigger_failure_learning(self, failed_interpretation_ids: list):
        """
        Trigger Failure Learning Agent for failed interpretations.

        Args:
            failed_interpretation_ids: List of NewsInterpretation IDs that were incorrect
        """
        # TODO: Implement Failure Learning Agent integration
        logger.info(f"🧠 Failure Learning Agent would analyze {len(failed_interpretation_ids)} failures")
        pass

    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("🛑 Accountability scheduler stopped")

    async def run_once(self):
        """
        Run accountability verification once (for testing).

        Example:
            >>> scheduler = AccountabilityScheduler()
            >>> results = await scheduler.run_once()
        """
        logger.info("🧪 Running single accountability verification (test mode)")
        results = await self.verifier.verify_all_horizons()

        # Calculate NIA
        total_verified = sum(r['verified_count'] for r in results.values())
        total_correct = sum(r['correct_count'] for r in results.values())

        if total_verified > 0:
            nia = (total_correct / total_verified) * 100
            results['nia'] = nia
        else:
            results['nia'] = 0.0

        return results


# Example usage
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🧪 Testing AccountabilityScheduler\n")

    async def test_scheduler():
        scheduler = AccountabilityScheduler(run_interval_minutes=60)

        # Run once for testing
        print("Running single accountability verification...")
        results = await scheduler.run_once()

        print(f"\nResults:")
        for horizon, result in results.items():
            if horizon != 'nia':
                print(f"{horizon}: {result['verified_count']} verified, {result['correct_count']} correct ({result['accuracy']*100:.1f}%)")

        if 'nia' in results:
            print(f"\nOverall NIA: {results['nia']:.1f}%")

    # Run test
    asyncio.run(test_scheduler())
