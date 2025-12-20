"""
Test Management Credibility Calculator.

Tests both with and without AI (for cost control).
"""

import asyncio
import logging
import os
from datetime import datetime

from management_credibility import ManagementCredibilityCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_single_stock(ticker: str, use_ai: bool = False):
    """
    Test credibility calculation for a single stock.
    
    Args:
        ticker: Stock ticker
        use_ai: Whether to use Claude API (costs money!)
    """
    print(f"\n{'='*80}")
    print(f"Testing Management Credibility: {ticker}")
    print(f"AI Analysis: {'ENABLED (costs $0.0013)' if use_ai else 'DISABLED (free)'}")
    print(f"{'='*80}\n")
    
    # Initialize calculator
    calculator = ManagementCredibilityCalculator()
    
    # Calculate credibility
    start_time = datetime.now()
    result = await calculator.calculate_credibility(ticker, use_ai=use_ai)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Print results
    print(f"✅ Completed in {elapsed:.2f}s\n")
    print("📊 Results:")
    print(f"  Overall Score: {result['score']:.4f}")
    print(f"  Confidence: {result['confidence']}")
    print()
    
    print("🔍 Component Breakdown:")
    components = result['components']
    print(f"  Tenure Score:        {components.get('tenure_score', 0):.4f} / 0.2000")
    print(f"  Sentiment Score:     {components.get('sentiment_score', 0):.4f} / 0.4000")
    print(f"  Compensation Score:  {components.get('compensation_score', 0):.4f} / 0.2000")
    print(f"  Insider Score:       {components.get('insider_score', 0):.4f} / 0.1000")
    print(f"  Board Score:         {components.get('board_score', 0):.4f} / 0.1000")
    print()
    
    print("📋 Details:")
    details = result.get('details', {})
    print(f"  CEO: {details.get('ceo_name', 'Unknown')}")
    print(f"  Tenure: {details.get('ceo_tenure_years', 0):.1f} years")
    print(f"  Board Size: {details.get('board_independence', 0)}")
    print()
    
    print("💰 Cost Metrics:")
    metrics = calculator.get_metrics()
    print(f"  API Calls: {metrics['total_api_calls']}")
    print(f"  Total Cost: ${metrics['total_cost_usd']:.4f}")
    if metrics['total_api_calls'] > 0:
        print(f"  Avg Cost/Call: ${metrics['avg_cost_per_call']:.4f}")
    print()
    
    print("⏰ Cache Info:")
    print(f"  Last Updated: {result['last_updated']}")
    print(f"  TTL: {result['ttl_days']} days (quarterly refresh)")
    print()
    
    if 'error' in result:
        print(f"⚠️  Warning: {result['error']}")
    
    return result


async def test_multiple_stocks(tickers: list, use_ai: bool = False):
    """
    Test credibility calculation for multiple stocks.
    
    Args:
        tickers: List of stock tickers
        use_ai: Whether to use Claude API
    """
    print(f"\n{'='*80}")
    print(f"Testing {len(tickers)} stocks")
    print(f"AI Analysis: {'ENABLED' if use_ai else 'DISABLED'}")
    print(f"{'='*80}\n")
    
    calculator = ManagementCredibilityCalculator()
    results = {}
    
    for ticker in tickers:
        print(f"📈 Analyzing {ticker}...", end=" ")
        try:
            result = await calculator.calculate_credibility(ticker, use_ai=use_ai)
            results[ticker] = result
            print(f"✅ Score: {result['score']:.4f} ({result['confidence']} confidence)")
        except Exception as e:
            print(f"❌ Error: {e}")
            results[ticker] = None
    
    print(f"\n{'='*80}")
    print("📊 Summary")
    print(f"{'='*80}\n")
    
    # Sort by score
    sorted_tickers = sorted(
        [(t, r) for t, r in results.items() if r is not None],
        key=lambda x: x[1]['score'],
        reverse=True
    )
    
    print("Top Credibility Scores:")
    for i, (ticker, result) in enumerate(sorted_tickers[:5], 1):
        ceo = result['details'].get('ceo_name', 'Unknown')
        print(f"  {i}. {ticker:6s} {result['score']:.4f}  ({ceo})")
    
    print()
    
    # Cost summary
    metrics = calculator.get_metrics()
    print("💰 Total Cost:")
    print(f"  API Calls: {metrics['total_api_calls']}")
    print(f"  Total Cost: ${metrics['total_cost_usd']:.4f}")
    if metrics['total_api_calls'] > 0:
        print(f"  Avg Cost/Call: ${metrics['avg_cost_per_call']:.4f}")
    
    if use_ai:
        monthly_cost = metrics['total_cost_usd'] * 4  # Quarterly = 4 times/year
        print(f"\n  📅 Estimated Monthly Cost (quarterly updates):")
        print(f"     ${monthly_cost:.4f}/month for {len(tickers)} stocks")
    
    return results


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Management Credibility Calculator - Test Suite")
    print("="*80)
    
    # Check for API key
    api_key = os.environ.get("CLAUDE_API_KEY", "")
    
    if not api_key:
        print("\n⚠️  CLAUDE_API_KEY not found in environment")
        print("   Tests will run without AI analysis (cost-free mode)")
        use_ai = False
    else:
        print(f"\n✅ CLAUDE_API_KEY found: {api_key[:20]}...")
        user_input = input("\n   Use Claude API for sentiment analysis? (y/N): ")
        use_ai = user_input.lower() == 'y'
        
        if use_ai:
            print("\n   ⚠️  WARNING: This will incur API costs (~$0.0013 per stock)")
            confirm = input("   Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("   Switching to cost-free mode")
                use_ai = False
    
    print(f"\n   Mode: {'AI ENABLED (costs money)' if use_ai else 'COST-FREE (no AI)'}")
    
    # Test 1: Single stock (detailed)
    print("\n" + "="*80)
    print("TEST 1: Single Stock Analysis (AAPL)")
    print("="*80)
    await test_single_stock("AAPL", use_ai=use_ai)
    
    # Test 2: Multiple stocks
    print("\n" + "="*80)
    print("TEST 2: Multiple Stocks Comparison")
    print("="*80)
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    await test_multiple_stocks(test_tickers, use_ai=use_ai)
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())