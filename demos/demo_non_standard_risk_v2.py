"""
Demo Test for Non-Standard Risk Factor with Mock Data.

⚠️ IMPORTANT: Run this from backend/ directory:
   cd backend
   python ../demos/demo_non_standard_risk.py
"""

import asyncio
import logging
from datetime import datetime, timedelta

from data.feature_store.ai_factors.non_standard_risk import NonStandardRiskCalculator, RISK_KEYWORDS
from data.feature_store.ai_factors.news_collector import NewsArticle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_mock_news(ticker: str, scenario: str) -> list[NewsArticle]:
    """Create mock news data for testing."""
    
    now = datetime.now()
    
    if scenario == "clean":
        # Clean company - no risk keywords
        return [
            NewsArticle(
                title=f"{ticker} Reports Strong Q3 Earnings",
                content="Company exceeded expectations with 25% revenue growth",
                published_at=now - timedelta(days=1),
                source="Mock Financial Times",
                url=f"https://example.com/{ticker}-earnings",
            ),
            NewsArticle(
                title=f"{ticker} Announces New Product Line",
                content="Innovation continues with new product launch next quarter",
                published_at=now - timedelta(days=5),
                source="Mock TechCrunch",
                url=f"https://example.com/{ticker}-product",
            ),
            NewsArticle(
                title=f"Analysts Upgrade {ticker} Stock",
                content="Positive outlook drives upgrades from major investment banks",
                published_at=now - timedelta(days=10),
                source="Mock Bloomberg",
                url=f"https://example.com/{ticker}-upgrade",
            ),
        ]
    
    elif scenario == "moderate_risk":
        # Some concerning news
        return [
            NewsArticle(
                title=f"{ticker} Faces Class Action Lawsuit Over Product Defect",
                content="Customers filed lawsuit claiming product defects caused injuries",
                published_at=now - timedelta(days=2),
                source="Mock Reuters",
                url=f"https://example.com/{ticker}-lawsuit",
            ),
            NewsArticle(
                title=f"SEC Investigating {ticker} Accounting Practices",
                content="Regulatory investigation into revenue recognition practices",
                published_at=now - timedelta(days=7),
                source="Mock Wall Street Journal",
                url=f"https://example.com/{ticker}-sec",
            ),
            NewsArticle(
                title=f"{ticker} Reports Strong Quarter Despite Challenges",
                content="Company maintains growth despite ongoing investigations",
                published_at=now - timedelta(days=15),
                source="Mock CNBC",
                url=f"https://example.com/{ticker}-earnings",
            ),
        ]
    
    elif scenario == "high_risk":
        # Major crisis
        return [
            NewsArticle(
                title=f"FBI Raids {ticker} Headquarters in Fraud Investigation",
                content="Federal agents raided offices as part of embezzlement probe",
                published_at=now - timedelta(days=1),
                source="Mock CNN",
                url=f"https://example.com/{ticker}-raid",
            ),
            NewsArticle(
                title=f"{ticker} CEO Arrested on Fraud Charges",
                content="Chief Executive taken into custody on allegations of accounting fraud",
                published_at=now - timedelta(days=1),
                source="Mock New York Times",
                url=f"https://example.com/{ticker}-arrest",
            ),
            NewsArticle(
                title=f"Massive Product Recall Announced for {ticker}",
                content="Safety defect affects millions of units, company stock plummets",
                published_at=now - timedelta(days=2),
                source="Mock Reuters",
                url=f"https://example.com/{ticker}-recall",
            ),
            NewsArticle(
                title=f"Workers Strike at {ticker} Manufacturing Plants",
                content="Union workers walkout over safety concerns and wage disputes",
                published_at=now - timedelta(days=5),
                source="Mock Bloomberg",
                url=f"https://example.com/{ticker}-strike",
            ),
            NewsArticle(
                title=f"Whistleblower Exposes Corruption at {ticker}",
                content="Internal documents reveal systemic fraud and bribery",
                published_at=now - timedelta(days=7),
                source="Mock Wall Street Journal",
                url=f"https://example.com/{ticker}-whistleblower",
            ),
        ]
    
    return []


async def demo_risk_analysis():
    """Demonstrate risk analysis with different scenarios."""
    print("\n" + "=" * 80)
    print("NON-STANDARD RISK FACTOR - DEMO WITH MOCK DATA")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print(f"Cost: $0 (Rule-based, no AI)")
    print("=" * 80)
    
    calculator = NonStandardRiskCalculator()
    
    # Test scenarios
    scenarios = [
        ("CLEAN", "clean", "Clean company with positive news"),
        ("MODERATE", "moderate_risk", "Some concerning developments"),
        ("CRISIS", "high_risk", "Major crisis situation"),
    ]
    
    for ticker, scenario, description in scenarios:
        print("\n" + "─" * 80)
        print(f"Scenario: {description}")
        print(f"Ticker: {ticker}")
        print("─" * 80)
        
        # Create mock news
        mock_news = create_mock_news(ticker, scenario)
        print(f"\n📰 Mock News Articles ({len(mock_news)}):")
        for i, article in enumerate(mock_news, 1):
            print(f"   {i}. {article.title}")
        
        # Manually analyze (simulating what calculator does)
        category_mentions = {cat: 0 for cat in RISK_KEYWORDS.keys()}
        risk_articles = []
        all_keywords_found = {}
        
        for article in mock_news:
            text = article.get_full_text().lower()
            article_risk = False
            article_keywords = []
            
            for category, keywords in RISK_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        category_mentions[category] += 1
                        article_risk = True
                        article_keywords.append(keyword)
                        all_keywords_found[keyword] = all_keywords_found.get(keyword, 0) + 1
            
            if article_risk:
                risk_articles.append({
                    "title": article.title,
                    "keywords": article_keywords,
                })
        
        # Calculate scores
        total_articles = len(mock_news)
        category_scores = {}
        
        for category, mentions in category_mentions.items():
            raw_score = mentions / total_articles if total_articles > 0 else 0
            normalized_score = min(raw_score / 0.3, 1.0)
            category_scores[category] = normalized_score
        
        # Weighted score
        weights = {
            "legal": 0.15,
            "regulatory": 0.25,
            "operational": 0.20,
            "labor": 0.10,
            "governance": 0.25,
            "reputation": 0.05,
        }
        
        risk_score = sum(
            category_scores[cat] * weights[cat]
            for cat in RISK_KEYWORDS.keys()
        )
        
        # Display results
        print(f"\n📊 Risk Analysis Results:")
        print(f"   Overall Risk Score:  {risk_score:.2f}")
        print(f"   Total Articles:      {total_articles}")
        print(f"   Risk Articles:       {len(risk_articles)}")
        
        print(f"\n📈 Category Scores:")
        for category, score in category_scores.items():
            bar = "█" * int(score * 20)
            print(f"   {category:15s}: {score:.2f} {bar}")
        
        if all_keywords_found:
            print(f"\n🔍 Keywords Found:")
            for keyword, count in sorted(
                all_keywords_found.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"   {keyword:20s}: {count:2d} mentions")
        
        # Interpretation
        interpretation = calculator.interpret_risk_score(risk_score)
        print(f"\n💡 Risk Assessment:")
        print(f"   Level:              {interpretation['level']}")
        print(f"   Assessment:         {interpretation['interpretation']}")
        print(f"   Recommended Action: {interpretation['action']}")
        print(f"   Max Position Size:  {interpretation['max_position_size']:.1f}%")
        
        # Trading impact
        print(f"\n🎯 Trading Impact:")
        if risk_score < 0.1:
            print(f"   ✅ Safe to trade - full position allowed")
        elif risk_score < 0.3:
            print(f"   ⚠️  Reduce position size to 3%")
        elif risk_score < 0.6:
            print(f"   🚫 Avoid new positions, reduce existing")
        else:
            print(f"   🛑 DO NOT TRADE - critical risk detected")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED")
    print("=" * 80)
    
    # Summary
    print("\n📋 Summary:")
    print("   • Rule-based keyword analysis")
    print("   • No AI required = $0 cost")
    print("   • 6 risk categories monitored")
    print("   • Real-time news scanning capability")
    print("   • Integrates with Feature Store")
    print("\n")


if __name__ == "__main__":
    asyncio.run(demo_risk_analysis())