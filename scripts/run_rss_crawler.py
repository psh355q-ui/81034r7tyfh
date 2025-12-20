"""
RSS Crawler Automation Script

실시간 RSS 크롤링 → DB 저장 → Deep Reasoning → Alert 발송

Features:
- 5분마다 자동 크롤링
- 에러 자동 복구
- 상태 로깅
- Prometheus 메트릭 기록
- Alert 발송

Usage:
    # 기본 실행 (5분 간격)
    python scripts/run_rss_crawler.py

    # 커스텀 간격 (초)
    python scripts/run_rss_crawler.py --interval 300

    # 한 번만 실행 (테스트)
    python scripts/run_rss_crawler.py --once
"""

import asyncio
import argparse
import sys
import os
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.news.rss_crawler_with_db import RSSCrawlerWithDB
from backend.alerts.alert_system import AlertSystem
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'rss_crawler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CrawlerService:
    """RSS Crawler Service with auto-restart on errors"""

    def __init__(
        self,
        interval_seconds: int = 300,
        enable_alerts: bool = True,
        enable_metrics: bool = True
    ):
        self.interval_seconds = interval_seconds
        self.enable_alerts = enable_alerts
        self.enable_metrics = enable_metrics
        self.crawler: Optional[RSSCrawlerWithDB] = None
        self.running = False
        self.error_count = 0
        self.max_errors = 10
        self.last_success_time: Optional[datetime] = None

    def initialize_crawler(self):
        """Initialize or reinitialize crawler"""
        try:
            # Initialize Alert System
            alert_system = None
            if self.enable_alerts:
                telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
                telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
                slack_webhook = os.getenv("SLACK_WEBHOOK_URL")

                if telegram_token or slack_webhook:
                    alert_system = AlertSystem(
                        telegram_bot_token=telegram_token,
                        telegram_chat_id=telegram_chat_id,
                        slack_webhook_url=slack_webhook,
                        confidence_threshold=float(os.getenv("ALERT_CONFIDENCE_THRESHOLD", "0.85"))
                    )
                    logger.info("Alert system initialized")
                else:
                    logger.warning("No alert credentials found - alerts disabled")

            # Initialize Crawler
            self.crawler = RSSCrawlerWithDB(
                alert_system=alert_system,
                enable_alerts=self.enable_alerts and alert_system is not None,
                enable_metrics=self.enable_metrics
            )

            logger.info("Crawler initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize crawler: {e}")
            return False

    async def run_single_cycle(self) -> bool:
        """Run single crawl cycle, returns success status"""
        try:
            logger.info(f"Starting crawl cycle...")
            results = await self.crawler.run_single_cycle()

            # Update success time
            self.last_success_time = datetime.now()
            self.error_count = 0

            # Log results
            if results:
                total_signals = sum(len(r['db_signals']) for r in results)
                total_alerts = sum(len(r['alerts_sent']) for r in results)
                hidden_count = sum(
                    1 for r in results
                    for s in r['signal_dicts']
                    if s['type'] == 'HIDDEN'
                )

                logger.info(f"Cycle complete: {len(results)} articles, {total_signals} signals, {total_alerts} alerts")
                if hidden_count > 0:
                    logger.info(f"🌟 Found {hidden_count} HIDDEN beneficiaries!")
            else:
                logger.info("No new articles found in this cycle")

            return True

        except Exception as e:
            self.error_count += 1
            logger.error(f"Crawl cycle failed (error {self.error_count}/{self.max_errors}): {e}")

            # Check if we should restart
            if self.error_count >= self.max_errors:
                logger.error("Too many errors - reinitializing crawler...")
                if not self.initialize_crawler():
                    logger.critical("Failed to reinitialize crawler - stopping service")
                    return False
                self.error_count = 0

            return True

    async def run_continuous(self):
        """Run continuous monitoring"""
        logger.info("=" * 80)
        logger.info("RSS Crawler Service Starting")
        logger.info("=" * 80)
        logger.info(f"Interval: {self.interval_seconds} seconds ({self.interval_seconds/60:.1f} minutes)")
        logger.info(f"Alerts: {'ENABLED' if self.enable_alerts else 'DISABLED'}")
        logger.info(f"Metrics: {'ENABLED' if self.enable_metrics else 'DISABLED'}")
        logger.info("=" * 80)

        # Initialize crawler
        if not self.initialize_crawler():
            logger.critical("Failed to start service")
            return

        self.running = True
        cycle_count = 0

        try:
            while self.running:
                cycle_count += 1
                logger.info(f"\n[CYCLE #{cycle_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Run cycle
                success = await self.run_single_cycle()

                if not success:
                    logger.critical("Service stopping due to critical error")
                    break

                # Wait for next cycle
                logger.info(f"Waiting {self.interval_seconds} seconds until next cycle...")
                await asyncio.sleep(self.interval_seconds)

        except KeyboardInterrupt:
            logger.info("\n\n[STOPPED] Service stopped by user (Ctrl+C)")
        except Exception as e:
            logger.critical(f"Service crashed: {e}")
            raise
        finally:
            self.running = False
            logger.info("RSS Crawler Service Stopped")

    async def run_once(self):
        """Run single cycle and exit (for testing)"""
        logger.info("=" * 80)
        logger.info("RSS Crawler - Single Cycle Mode")
        logger.info("=" * 80)

        if not self.initialize_crawler():
            logger.error("Failed to initialize crawler")
            return

        await self.run_single_cycle()

        logger.info("=" * 80)
        logger.info("Single cycle complete")
        logger.info("=" * 80)

    def stop(self):
        """Stop the service gracefully"""
        logger.info("Stopping crawler service...")
        self.running = False


# Global service instance for signal handling
crawler_service: Optional[CrawlerService] = None


def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"\nReceived signal {signum}")
    if crawler_service:
        crawler_service.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="RSS Crawler Automation")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Crawl interval in seconds (default: 300 = 5 minutes)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )
    parser.add_argument(
        "--no-alerts",
        action="store_true",
        help="Disable alert notifications"
    )
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Disable Prometheus metrics"
    )

    args = parser.parse_args()

    # Register signal handlers
    global crawler_service
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create service
    crawler_service = CrawlerService(
        interval_seconds=args.interval,
        enable_alerts=not args.no_alerts,
        enable_metrics=not args.no_metrics
    )

    # Run
    try:
        if args.once:
            asyncio.run(crawler_service.run_once())
        else:
            asyncio.run(crawler_service.run_continuous())
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
