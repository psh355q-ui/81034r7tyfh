"""
Paper Trading CLI Runner

Command-line interface for running live paper trading simulation.

Usage:
    python run_paper_trading.py --duration 1h --capital 100000
    python run_paper_trading.py --quick  # 5-minute test
    python run_paper_trading.py --tickers AAPL NVDA MSFT --duration 30m

Author: AI Trading System Team
Date: 2025-11-15
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

from paper_trading import PaperTradingEngine, PaperTradingConfig


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.

    Args:
        duration_str: Duration string (e.g., "5m", "1h", "30s")

    Returns:
        Duration in seconds
    """
    if duration_str.endswith("s"):
        return int(duration_str[:-1])
    elif duration_str.endswith("m"):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith("h"):
        return int(duration_str[:-1]) * 3600
    else:
        # Default to minutes if no unit specified
        return int(duration_str) * 60


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Trading System - Paper Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick 5-minute test
  python run_paper_trading.py --quick

  # 1-hour trading session
  python run_paper_trading.py --duration 1h

  # Custom tickers and capital
  python run_paper_trading.py --tickers AAPL NVDA TSLA --capital 50000 --duration 30m

  # Continuous trading (manual stop with Ctrl+C)
  python run_paper_trading.py --continuous
        """
    )

    parser.add_argument(
        "--duration",
        type=str,
        help="Trading duration (e.g., 5m, 1h, 30s)",
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=100000.0,
        help="Initial capital (default: 100000)",
    )

    parser.add_argument(
        "--tickers",
        type=str,
        nargs="+",
        default=["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"],
        help="Tickers to trade (default: AAPL NVDA MSFT GOOGL AMZN)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Decision interval in seconds (default: 60)",
    )

    parser.add_argument(
        "--max-positions",
        type=int,
        default=10,
        help="Maximum number of positions (default: 10)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test (5 minutes, 3 tickers)",
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously until manual stop (Ctrl+C)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI (use mock strategy)",
    )

    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="Disable monitoring/metrics",
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Quick mode adjustments
    if args.quick:
        tickers = ["AAPL", "NVDA", "MSFT"]
        duration_seconds = 300  # 5 minutes
        interval = 30  # 30 seconds
    else:
        tickers = args.tickers
        interval = args.interval

        if args.continuous:
            duration_seconds = None
        elif args.duration:
            duration_seconds = parse_duration(args.duration)
        else:
            # Default: 30 minutes
            duration_seconds = 1800

    # Create configuration
    config = PaperTradingConfig(
        initial_cash=args.capital,
        tickers=tickers,
        decision_interval_seconds=interval,
        max_positions=args.max_positions,
        enable_ai=not args.no_ai,
        enable_monitoring=not args.no_monitoring,
    )

    print("\n" + "=" * 70)
    print("AI TRADING SYSTEM - PAPER TRADING")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Initial Capital:     ${args.capital:,.0f}")
    print(f"  Tickers:             {', '.join(tickers)}")
    print(f"  Decision Interval:   {interval}s")
    print(f"  Max Positions:       {args.max_positions}")
    print(f"  AI Enabled:          {not args.no_ai}")
    print(f"  Monitoring Enabled:  {not args.no_monitoring}")

    if args.continuous:
        print(f"  Duration:            Continuous (press Ctrl+C to stop)")
    else:
        print(f"  Duration:            {duration_seconds}s ({duration_seconds/60:.1f} minutes)")

    print(f"  Mode:                {'Quick Test' if args.quick else 'Full Trading'}")
    print("=" * 70)

    # Create engine
    engine = PaperTradingEngine(config)

    try:
        if args.continuous:
            # Continuous mode - run until Ctrl+C
            print("\nStarting continuous paper trading...")
            print("Press Ctrl+C to stop\n")
            await engine.start()
        else:
            # Fixed duration mode
            print(f"\nStarting paper trading for {duration_seconds}s...")
            print("This is a simulation - no real money is involved\n")
            await engine.run_for_duration(duration_seconds)

    except KeyboardInterrupt:
        print("\n\nStopping paper trading (Ctrl+C pressed)...")
        engine.stop()
        await asyncio.sleep(1)  # Give time for graceful shutdown

    # Print final summary
    print("\n")
    engine.print_summary()

    # Print positions detail if any
    if engine.portfolio.positions:
        print("\nPosition Details:")
        for pos_dict in engine.portfolio.get_positions_dict():
            print(f"  {pos_dict['ticker']}: {pos_dict['shares']} shares @ "
                  f"${pos_dict['avg_cost']:.2f} -> ${pos_dict['current_price']:.2f} "
                  f"(P&L: ${pos_dict['unrealized_pnl']:+.2f})")

    # Print recent trades
    recent_trades = engine.portfolio.get_recent_trades(limit=5)
    if recent_trades:
        print("\nRecent Trades (last 5):")
        for trade in recent_trades:
            print(f"  {trade['timestamp'][:19]} | {trade['action']:4} {trade['shares']:4} "
                  f"{trade['ticker']:6} @ ${trade['price']:7.2f} | "
                  f"Commission: ${trade['commission']:.2f}")

    print("\n" + "=" * 70)
    print("Paper Trading Session Complete")
    print("=" * 70)


if __name__ == "__main__":
    # Check if we're on Windows and set proper event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
