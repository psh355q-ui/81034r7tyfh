"""
Standalone News Crawler Runner
==============================

This script runs the NewsPoller in a separate process.
Use this if the main API server is experiencing performance issues due to heavy crawling.

Usage:
    python -m backend.run_news_crawler

Features:
- Windows/Linux/macOS compatible
- Graceful shutdown with Ctrl+C
- Automatic log file creation
- Can be run alongside or instead of main server's embedded poller
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.news_poller import NewsPoller
from backend.database.models import Base

# Create logs directory if not exists
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / "news_crawler.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("NewsCrawlerProcess")


class GracefulShutdown:
    """Cross-platform graceful shutdown handler."""

    def __init__(self):
        self.stop_event = asyncio.Event()
        self._shutdown_requested = False

    def request_shutdown(self):
        """Request graceful shutdown."""
        if not self._shutdown_requested:
            self._shutdown_requested = True
            logger.info("🛑 Shutdown signal received")
            self.stop_event.set()

    def setup_signal_handlers(self, loop: asyncio.AbstractEventLoop):
        """Setup platform-specific signal handlers."""
        if sys.platform == 'win32':
            # Windows: Use signal module directly (no loop.add_signal_handler support)
            signal.signal(signal.SIGINT, lambda s, f: self.request_shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self.request_shutdown())
            logger.info("📡 Windows signal handlers registered")
        else:
            # Unix-like: Use loop's signal handler for async compatibility
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self.request_shutdown)
            logger.info("📡 Unix signal handlers registered")


async def main():
    logger.info("=" * 60)
    logger.info("🚀 Starting Standalone News Crawler")
    logger.info("=" * 60)
    logger.info(f"📂 Working directory: {os.getcwd()}")
    logger.info(f"🖥️  Platform: {sys.platform}")

    # Ensure DB tables exist (optional - usually done by main server)
    # Base.metadata.create_all(bind=engine)

    # Initialize shutdown handler
    shutdown = GracefulShutdown()
    loop = asyncio.get_running_loop()
    shutdown.setup_signal_handlers(loop)

    # Initialize and start NewsPoller
    poller = NewsPoller()
    crawler_task = asyncio.create_task(poller.start())

    logger.info("✅ Crawler is running in background")
    logger.info("💡 Press Ctrl+C to stop gracefully")
    logger.info("-" * 60)

    # Wait for stop signal
    await shutdown.stop_event.wait()

    # Graceful shutdown
    logger.info("-" * 60)
    logger.info("👋 Initiating graceful shutdown...")

    # Cancel the crawler task
    crawler_task.cancel()
    try:
        await asyncio.wait_for(crawler_task, timeout=5.0)
    except asyncio.CancelledError:
        logger.info("📋 Crawler task cancelled")
    except asyncio.TimeoutError:
        logger.warning("⚠️ Crawler task did not stop within timeout")

    logger.info("✅ News Crawler stopped successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Windows event loop policy fix
    if sys.platform == 'win32':
        # Use WindowsSelectorEventLoopPolicy to avoid ProactorEventLoop issues
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This catches Ctrl+C on Windows before the event loop processes it
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
