"""
Create Test News Interpretations

Phase 29: Accountability System Testing
Date: 2025-12-30

Creates sample news interpretations for testing the Accountability system.

Usage:
    python backend/automation/create_test_interpretations.py
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from backend.database.repository import get_sync_session
from backend.database.models import NewsInterpretation, NewsMarketReaction, MacroContextSnapshot
from sqlalchemy import text


def create_test_data(force_recreate=False):
    """Create test news interpretations and market reactions"""

    print("🧪 Creating test data for Accountability System...")
    print()

    with get_sync_session() as session:
        # Check if we already have test data
        existing_count = session.query(NewsInterpretation).count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing interpretations")

            if not force_recreate:
                print("💡 Run with --force to delete and recreate")
                print("❌ Aborted")
                return False

            # Delete existing data
            session.execute(text("DELETE FROM news_market_reactions"))
            session.execute(text("DELETE FROM news_interpretations"))
            session.execute(text("DELETE FROM macro_context_snapshots"))
            session.commit()
            print("🗑️  Deleted existing data")
            print()

        # Create macro context snapshot (for today)
        macro_snapshot = MacroContextSnapshot(
            snapshot_date=datetime.now().date(),
            regime="RISK_ON",  # Valid values: RISK_ON, RISK_OFF, ROTATION, UNCERTAINTY
            fed_stance="NEUTRAL",
            vix_level=15.5,
            vix_category="NORMAL",
            sector_rotation="TECH_TO_DEFENSIVE",
            dominant_narrative="AI and tech leadership continues",
            geopolitical_risk="LOW",
            earnings_season=False,
            market_sentiment="GREED",
            sp500_trend="UPTREND"
        )
        session.add(macro_snapshot)
        session.flush()

        print(f"✅ Created macro context snapshot (ID: {macro_snapshot.id})")

        # Test interpretations
        test_cases = [
            {
                "ticker": "NVDA",
                "headline_bias": "BULLISH",
                "expected_impact": "HIGH",
                "time_horizon": "INTRADAY",
                "confidence": 85,
                "reasoning": "NVIDIA announces new AI chip partnership with major cloud providers. Expected to boost revenue by 15-20% next quarter.",
                "interpreted_at": datetime.now() - timedelta(hours=2),  # 2 hours ago
                "initial_price": 875.50
            },
            {
                "ticker": "TSLA",
                "headline_bias": "BEARISH",
                "expected_impact": "MEDIUM",
                "time_horizon": "INTRADAY",
                "confidence": 70,
                "reasoning": "Tesla recalls 50,000 vehicles due to autopilot issues. Short-term negative sentiment expected.",
                "interpreted_at": datetime.now() - timedelta(hours=25),  # 25 hours ago (for 1d test)
                "initial_price": 245.30
            },
            {
                "ticker": "AAPL",
                "headline_bias": "BULLISH",
                "expected_impact": "LOW",
                "time_horizon": "MULTI_DAY",
                "confidence": 60,
                "reasoning": "Apple announces minor software update. Low immediate impact but positive for ecosystem.",
                "interpreted_at": datetime.now() - timedelta(days=3, hours=2),  # 3+ days ago (for 3d test)
                "initial_price": 192.75
            },
            {
                "ticker": "MSFT",
                "headline_bias": "NEUTRAL",
                "expected_impact": "MEDIUM",
                "time_horizon": "INTRADAY",
                "confidence": 50,
                "reasoning": "Microsoft cloud services maintain steady growth. No major surprises.",
                "interpreted_at": datetime.now() - timedelta(hours=26),  # 26 hours ago
                "initial_price": 425.80
            },
            {
                "ticker": "GOOGL",
                "headline_bias": "BULLISH",
                "expected_impact": "HIGH",
                "time_horizon": "MULTI_DAY",
                "confidence": 90,
                "reasoning": "Google AI chatbot gains significant market share. Major competitive advantage in AI race.",
                "interpreted_at": datetime.now() - timedelta(days=4),  # 4 days ago
                "initial_price": 142.60
            }
        ]

        created_interpretations = []

        for test_case in test_cases:
            # Create news interpretation
            interpretation = NewsInterpretation(
                ticker=test_case["ticker"],
                headline_bias=test_case["headline_bias"],
                expected_impact=test_case["expected_impact"],
                time_horizon=test_case["time_horizon"],
                confidence=test_case["confidence"],
                reasoning=test_case["reasoning"],
                macro_context_id=macro_snapshot.id,
                interpreted_at=test_case["interpreted_at"]
            )
            session.add(interpretation)
            session.flush()

            # Create news market reaction (PENDING state)
            # IMPORTANT: Set created_at to match interpreted_at so verification logic works
            reaction = NewsMarketReaction(
                interpretation_id=interpretation.id,
                ticker=test_case["ticker"],
                price_at_news=test_case["initial_price"],
                created_at=test_case["interpreted_at"]  # Match interpretation time
            )
            session.add(reaction)

            created_interpretations.append({
                "id": interpretation.id,
                "ticker": test_case["ticker"],
                "bias": test_case["headline_bias"],
                "age": (datetime.now() - test_case["interpreted_at"]).total_seconds() / 3600
            })

        session.commit()

        print()
        print("=" * 80)
        print("📊 Created Test Data")
        print("=" * 80)
        for interp in created_interpretations:
            print(f"✅ ID {interp['id']}: {interp['ticker']} ({interp['bias']}) - {interp['age']:.1f} hours old")
        print()
        print(f"Total: {len(created_interpretations)} interpretations + {len(created_interpretations)} market reactions")
        print("=" * 80)

        return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create test news interpretations")
    parser.add_argument("--force", action="store_true", help="Force recreate (delete existing data)")
    args = parser.parse_args()

    success = create_test_data(force_recreate=args.force)
    sys.exit(0 if success else 1)
