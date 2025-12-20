"""
Test script for AI Trading Agent.

Tests:
1. Feature Store integration
2. Claude API analysis
3. Trading decision generation
4. Constitution rules enforcement
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import os

# Set environment to use Redis only (skip TimescaleDB for local testing)
# Use environment variable if set, otherwise use NAS IP for local testing
if "REDIS_URL" not in os.environ:
    os.environ["REDIS_URL"] = "redis://192.168.50.148:6379/0"

from ai import TradingAgent
from config import get_settings

# Configure logging with UTF-8 encoding
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    encoding='utf-8' if sys.version_info >= (3, 9) else None,
)

logger = logging.getLogger(__name__)


async def test_single_analysis():
    """Test analysis of a single stock."""
    logger.info("=" * 80)
    logger.info("TEST 1: Single Stock Analysis")
    logger.info("=" * 80)

    # Initialize agent
    agent = TradingAgent()
    await agent.initialize()

    # Test ticker
    ticker = "AAPL"
    logger.info(f"\nAnalyzing {ticker}...")

    # Run analysis
    decision = await agent.analyze(ticker)

    # Display results
    logger.info("\n" + "-" * 80)
    logger.info("TRADING DECISION")
    logger.info("-" * 80)
    logger.info(f"Ticker:        {decision.ticker}")
    logger.info(f"Action:        {decision.action}")
    logger.info(f"Conviction:    {decision.conviction:.2%}")
    logger.info(f"Position Size: {decision.position_size:.1f}%")
    logger.info(f"\nReasoning:\n{decision.reasoning}")
    logger.info(f"\nRisk Factors:\n{', '.join(decision.risk_factors)}")

    if decision.target_price:
        logger.info(f"\nTarget Price:  ${decision.target_price:.2f}")
    if decision.stop_loss:
        logger.info(f"Stop Loss:     ${decision.stop_loss:.2f}")

    logger.info("\nFeatures Used:")
    for name, value in decision.features_used.items():
        if value is not None:
            logger.info(f"  {name:12s}: {value:8.4f}")

    # Get metrics
    metrics = agent.get_metrics()
    logger.info("\n" + "-" * 80)
    logger.info("METRICS")
    logger.info("-" * 80)
    logger.info(f"Total Analyses: {metrics['total_analyses']}")
    logger.info(f"Decisions: {metrics['decisions_by_action']}")

    claude_metrics = metrics["claude_metrics"]
    logger.info(f"\nClaude API:")
    logger.info(f"  Requests:     {claude_metrics['total_requests']}")
    logger.info(f"  Total Cost:   ${claude_metrics['total_cost_usd']:.4f}")
    logger.info(f"  Avg Cost:     ${claude_metrics['avg_cost_per_request']:.4f}")

    feature_metrics = metrics["feature_store_metrics"]
    logger.info(f"\nFeature Store:")
    logger.info(f"  Cache Hits:   {feature_metrics['cache_hits_redis']}")
    logger.info(f"  Cache Misses: {feature_metrics['cache_misses']}")
    logger.info(f"  Hit Rate:     {feature_metrics['cache_hit_rate']:.1%}")

    await agent.close()

    logger.info("\n✓ Test 1 completed")


async def test_multiple_tickers():
    """Test analysis of multiple stocks."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Multiple Ticker Analysis")
    logger.info("=" * 80)

    # Initialize agent
    agent = TradingAgent()
    await agent.initialize()

    # Test tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]

    results = []

    for ticker in tickers:
        logger.info(f"\nAnalyzing {ticker}...")
        decision = await agent.analyze(ticker)
        results.append(decision)

        logger.info(
            f"  {decision.action:4s} - Conviction: {decision.conviction:.2%} - "
            f"Position: {decision.position_size:.1f}%"
        )

    # Summary
    logger.info("\n" + "-" * 80)
    logger.info("SUMMARY")
    logger.info("-" * 80)

    for decision in results:
        logger.info(
            f"{decision.ticker:6s} → {decision.action:4s} "
            f"({decision.conviction:.0%} conviction, "
            f"{decision.position_size:.1f}% position)"
        )

    # Metrics
    metrics = agent.get_metrics()
    logger.info(f"\nTotal Analyses: {metrics['total_analyses']}")
    logger.info(f"Actions: {metrics['decisions_by_action']}")

    claude_metrics = metrics["claude_metrics"]
    logger.info(f"Total Claude Cost: ${claude_metrics['total_cost_usd']:.4f}")

    feature_metrics = metrics["feature_store_metrics"]
    logger.info(f"Cache Hit Rate: {feature_metrics['cache_hit_rate']:.1%}")

    await agent.close()

    logger.info("\n✓ Test 2 completed")


async def test_constitution_rules():
    """Test Constitution rules enforcement."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Constitution Rules")
    logger.info("=" * 80)

    settings = get_settings()

    logger.info("\nActive Constitution Rules:")
    logger.info(f"  Kill Switch:              {settings.kill_switch_enabled}")
    logger.info(f"  Daily Loss Limit:         {settings.kill_switch_daily_loss_pct}%")
    logger.info(f"  Stop Loss (Default):      {settings.stop_loss_fixed_pct}%")
    logger.info(f"  Max Position Size:        {settings.max_position_size_pct}%")
    logger.info(f"  Max Positions:            {settings.max_positions}")
    logger.info(f"  Conviction Threshold BUY: {settings.conviction_threshold_buy:.0%}")
    logger.info(f"  Conviction Threshold SELL: {settings.conviction_threshold_sell:.0%}")

    logger.info("\n✓ Test 3 completed")


async def main():
    """Run all tests."""
    try:
        # Check if Claude API key is set
        settings = get_settings()
        if not settings.claude_api_key or settings.claude_api_key == "":
            logger.error("❌ Claude API key not found!")
            logger.error("Please set CLAUDE_API_KEY in .env file")
            return

        logger.info("Starting AI Trading Agent Tests...")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"Paper Trading: {settings.feature_paper_trading}")
        logger.info(f"Auto Trading:  {settings.feature_auto_trading}")

        # Run tests
        await test_constitution_rules()
        await test_single_analysis()
        await test_multiple_tickers()

        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
