#!/usr/bin/env python
"""
Run Live Trading Engine

Launch the live trading system with real broker integration.

Usage:
    # Dry run (no execution)
    python run_live_trading.py --mode dry_run --account 12345678

    # Paper trading (virtual account)
    python run_live_trading.py --mode paper --account 12345678

    # Live trading (real account) - USE WITH CAUTION!
    python run_live_trading.py --mode live --account 12345678 --confirm

Author: AI Trading System Team
Date: 2025-11-15
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from live_trading_engine import LiveTradingEngine, LiveTradingConfig, TradingMode
from config import get_settings


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Live Trading Engine with KIS Broker Integration"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["dry_run", "paper", "live"],
        default="dry_run",
        help="Trading mode (default: dry_run)",
    )

    parser.add_argument(
        "--account",
        type=str,
        required=True,
        help="KIS account number (8 digits)",
    )

    parser.add_argument(
        "--tickers",
        type=str,
        nargs="+",
        default=["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"],
        help="List of tickers to trade (default: AAPL NVDA MSFT GOOGL AMZN)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Decision interval in seconds (default: 300 = 5 minutes)",
    )

    parser.add_argument(
        "--max-positions",
        type=int,
        default=10,
        help="Maximum number of positions (default: 10)",
    )

    parser.add_argument(
        "--max-position-size",
        type=float,
        default=10000.0,
        help="Maximum position size in USD (default: 10000)",
    )

    parser.add_argument(
        "--max-daily-trades",
        type=int,
        default=20,
        help="Maximum trades per day (default: 20)",
    )

    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Disable trade confirmation prompts (USE WITH CAUTION)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Safety warning for live trading
    if args.mode == "live":
        logger.warning("=" * 80)
        logger.warning("LIVE TRADING MODE ENABLED")
        logger.warning("Real money will be used for trading!")
        logger.warning("=" * 80)

        confirm = input("\nType 'YES I UNDERSTAND' to continue: ").strip()
        if confirm != "YES I UNDERSTAND":
            logger.info("Live trading cancelled")
            return

    # Convert mode string to enum
    mode_map = {
        "dry_run": TradingMode.DRY_RUN,
        "paper": TradingMode.PAPER,
        "live": TradingMode.LIVE,
    }
    mode = mode_map[args.mode]

    # Create configuration
    config = LiveTradingConfig(
        kis_account_no=args.account,
        mode=mode,
        tickers=args.tickers,
        decision_interval_seconds=args.interval,
        max_positions=args.max_positions,
        max_position_size_usd=args.max_position_size,
        max_daily_trades=args.max_daily_trades,
        require_confirmation=(not args.no_confirm) and (mode == TradingMode.LIVE),
        enable_notifications=True,
    )

    logger.info("Live Trading Configuration:")
    logger.info(f"  Mode: {config.mode.value}")
    logger.info(f"  Account: {config.kis_account_no}")
    logger.info(f"  Tickers: {', '.join(config.tickers)}")
    logger.info(f"  Decision Interval: {config.decision_interval_seconds}s")
    logger.info(f"  Max Positions: {config.max_positions}")
    logger.info(f"  Max Position Size: ${config.max_position_size_usd:,.2f}")
    logger.info(f"  Max Daily Trades: {config.max_daily_trades}")
    logger.info(f"  Require Confirmation: {config.require_confirmation}")
    logger.info("")

    # Create and start engine
    try:
        engine = LiveTradingEngine(config=config)
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt - shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
