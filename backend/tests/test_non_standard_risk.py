"""
Test Non-Standard Risk Factor.

Tests:
1. News collection from Yahoo Finance
2. Keyword detection
3. Risk score calculation
4. Feature Store integration

No API keys required for basic test (Yahoo Finance only).
"""

import asyncio
import logging
from datetime import datetime

from non_standard_risk import NonStandardRiskCalculator
from news_collector import NewsCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_news_collection():
    """Test 1: News Collection"""
    print("=" * 80)
    print("TEST 1: News Collection")
    print("=" * 80)

    collector = NewsCollector()

    # Test with TSLA (usually has a lot of news)
    ticker = "TSLA"
    print(f"\nFetching news for {ticker}...")

    news = await collector.fetch_news(ticker, days=30, sources=["yahoo"])

    print(f"\nResults:")
    print(f"- Total articles: {len(news)}")

    if news:
        print(f"\nFirst 3 articles:")
        for i, article in enumerate(news[:3], 1):
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Published: {article.published_at}")
            print(f"   URL: {article.url}")

    print("\n✓ Test 1 completed\n")
    return news


async def test_risk_calculation():
    """Test 2: Risk Calculation"""
    print("=" * 80)
    print("TEST 2: Risk Calculation")
    print("=" * 80)

    calculator = NonStandardRiskCalculator()

    # Test with tickers that might have risk news
    test_tickers = ["TSLA", "AAPL", "BA"]  # Boeing often has operational risks

    for ticker in test_tickers:
        print(f"\n{'─' * 80}")
        print(f"Analyzing {ticker}...")
        print(f"{'─' * 80}")

        result = await calculator.calculate_risk(ticker, days=30)

        print(f"\n📊 Risk Analysis Results:")
        print(f"   Overall Risk Score:  {result['risk_score']:.2f}")
        print(f"   Total Articles:      {result['total_articles']}")
        print(f"   Risk Articles:       {len(result['risk_articles'])}")

        print(f"\n📈 Category Scores:")
        for category, score in result['category_scores'].items():
            print(f"   {category:15s}: {score:.2f}")

        if result['keywords_found']:
            print(f"\n🔍 Keywords Found:")
            for keyword, count in sorted(
                result['keywords_found'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]:
                print(f"   {keyword:20s}: {count:2d} mentions")

        # Interpretation
        interpretation = calculator.interpret_risk_score(result['risk_score'])
        print(f"\n💡 Interpretation:")
        print(f"   Level:              {interpretation['level']}")
        print(f"   Assessment:         {interpretation['interpretation']}")
        print(f"   Recommended Action: {interpretation['action']}")
        print(f"   Max Position Size:  {interpretation['max_position_size']:.1f}%")

        # Show risk articles
        if result['risk_articles']:
            print(f"\n📰 Risk Articles (top 3):")
            for i, article in enumerate(result['risk_articles'][:3], 1):
                print(f"\n   {i}. {article['title']}")
                print(f"      Keywords: {', '.join(article['keywords'][:5])}")
                print(f"      URL: {article['url']}")

    print("\n✓ Test 2 completed\n")


async def test_feature_calculation():
    """Test 3: Feature Calculation (for Feature Store)"""
    print("=" * 80)
    print("TEST 3: Feature Store Integration")
    print("=" * 80)

    from non_standard_risk import calculate_non_standard_risk_feature

    ticker = "AAPL"
    as_of_date = datetime.now()

    print(f"\nCalculating feature for {ticker}...")
    risk_score = await calculate_non_standard_risk_feature(ticker, as_of_date)

    print(f"\nFeature Value:")
    print(f"   non_standard_risk: {risk_score:.4f}")

    # This is what Feature Store would cache
    feature_data = {
        "ticker": ticker,
        "feature_name": "non_standard_risk",
        "value": risk_score,
        "as_of_date": as_of_date,
        "ttl": 3600,  # 1 hour cache (news doesn't change that fast)
    }

    print(f"\nFeature Store Entry:")
    print(f"   {feature_data}")

    print("\n✓ Test 3 completed\n")


async def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print("NON-STANDARD RISK FACTOR - COMPREHENSIVE TEST")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print(f"Cost: $0 (Rule-based, no AI)")
    print("=" * 80)
    print("\n")

    # Test 1: News collection
    news = await test_news_collection()

    # Test 2: Risk calculation
    if news:
        await test_risk_calculation()
    else:
        print("⚠️  Skipping Test 2 (no news fetched)")

    # Test 3: Feature calculation
    await test_feature_calculation()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())