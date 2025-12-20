"""
Quick Backtest Runner

Easy command-line interface for running backtests.

Usage:
    python run_backtest.py --period 3m --capital 100000
    python run_backtest.py --start 2024-01-01 --end 2024-06-30
    python run_backtest.py --quick  # Quick 1-month test

Author: AI Trading System Team
Date: 2025-11-14
"""

import asyncio
import argparse
from datetime import datetime, timedelta
import logging

from backtesting import (
    BacktestConfig,
    AIStrategyConfig,
    AIStrategyBacktest,
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="AI Trading Strategy Backtest")

    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--period",
        type=str,
        choices=["1m", "3m", "6m", "1y"],
        help="Backtest period (1m=1 month, 3m=3 months, etc.)",
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
        default=["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META"],
        help="Tickers to trade",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test (1 month, 5 tickers)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def calculate_dates(args):
    """Calculate start and end dates."""
    if args.quick:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    elif args.period:
        end_date = datetime.now()
        if args.period == "1m":
            start_date = end_date - timedelta(days=30)
        elif args.period == "3m":
            start_date = end_date - timedelta(days=90)
        elif args.period == "6m":
            start_date = end_date - timedelta(days=180)
        elif args.period == "1y":
            start_date = end_date - timedelta(days=365)
    elif args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        # Default: last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Calculate dates
    start_date, end_date = calculate_dates(args)

    # Quick mode adjustments
    if args.quick:
        tickers = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"]
    else:
        tickers = args.tickers

    print("\n" + "=" * 70)
    print("AI TRADING STRATEGY - BACKTEST")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Initial Capital: ${args.capital:,.0f}")
    print(f"  Tickers: {', '.join(tickers)}")
    print(f"  Mode: {'Quick Test' if args.quick else 'Full Backtest'}")

    # Create configurations
    backtest_config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital,
        tickers=tickers,
        commission_rate=0.001,
        slippage_bps=2.5,
        max_positions=10 if args.quick else 15,
    )

    ai_config = AIStrategyConfig(
        use_ensemble=not args.quick,  # Quick mode uses simpler strategy
        enable_risk_screening=True,
        enable_regime_detection=True,
        min_conviction=0.7,
        max_position_size=5.0,
    )

    # Run backtest
    print("\nRunning backtest...")
    backtest = AIStrategyBacktest(backtest_config, ai_config)
    result = await backtest.run()

    # Display report
    report = backtest.get_performance_report(result)
    print(report)

    # Save results
    output_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\nSaving results to: {output_file}")

    import json
    with open(output_file, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    print(f"OK: Results saved to: {output_file}")

    # Summary
    metrics = result.metrics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Return: {metrics['total_return_pct']:+.2f}%")
    print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
    print(f"Max DD: {metrics['max_drawdown_pct']:.2f}%")
    print(f"Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.1%}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
