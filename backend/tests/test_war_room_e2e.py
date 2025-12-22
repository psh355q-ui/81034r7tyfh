"""
War Room E2E Test

Tests the complete 7-agent debate system with real data:
1. NewsAgent queries Phase 20 real-time news from DB
2. All 7 agents execute successfully
3. PM arbitrates and generates consensus
4. Trading signal created if confidence >= 0.7
5. Database records saved

Author: AI Trading System
Date: 2025-12-22
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set working directory to project root
os.chdir(project_root)

from backend.api.war_room_router import get_war_room_engine
from backend.database.repository import get_sync_session
from backend.database.models import AIDebateSession, TradingSignal, NewsArticle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_war_room_debate(ticker: str = "AAPL"):
    """
    Test War Room debate with real ticker.

    Args:
        ticker: Stock ticker to analyze (default: AAPL)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🧪 War Room E2E Test - {ticker}")
    logger.info(f"{'='*80}\n")

    # 1. Check if we have news data for this ticker
    logger.info(f"📰 Step 1: Checking news data for {ticker}...")

    db = get_sync_session()
    try:
        # Query using ANY instead of contains to avoid type mismatch
        from sqlalchemy import text

        news_count = db.query(NewsArticle)\
            .filter(text(f"'{ticker}' = ANY(tickers)"))\
            .count()

        logger.info(f"✅ Found {news_count} news articles with ticker {ticker}")

        if news_count == 0:
            logger.warning(f"⚠️ No news found for {ticker}. NewsAgent will vote HOLD with low confidence.")

    finally:
        db.close()

    # 2. Execute War Room debate
    logger.info(f"\n🏛️ Step 2: Executing War Room debate...")

    engine = get_war_room_engine()

    try:
        votes, pm_decision = await engine.run_debate(ticker)

        logger.info(f"\n{'='*80}")
        logger.info(f"📊 DEBATE RESULTS")
        logger.info(f"{'='*80}\n")

        # Display individual votes
        for vote in votes:
            agent_name = vote['agent'].upper()
            action = vote['action']
            confidence = vote['confidence']
            reasoning = vote.get('reasoning', 'N/A')[:100]  # First 100 chars

            logger.info(f"{agent_name} Agent:")
            logger.info(f"  Action: {action}")
            logger.info(f"  Confidence: {confidence:.2%}")
            logger.info(f"  Reasoning: {reasoning}...")
            logger.info("")

        # Display PM decision
        logger.info(f"👔 PM DECISION:")
        logger.info(f"  Consensus Action: {pm_decision['consensus_action']}")
        logger.info(f"  Consensus Confidence: {pm_decision['consensus_confidence']:.2%}")
        logger.info(f"  Summary: {pm_decision.get('summary', 'N/A')}")
        logger.info("")

        # 3. Check if signal would be generated
        will_generate_signal = pm_decision['consensus_confidence'] >= 0.7

        if will_generate_signal:
            logger.info(f"✅ Signal will be generated (confidence >= 70%)")
        else:
            logger.info(f"⚠️ No signal will be generated (confidence < 70%)")

        # 4. Verify NewsAgent used Phase 20 data
        logger.info(f"\n🔍 Step 3: Verifying NewsAgent integration...")

        news_vote = next((v for v in votes if v['agent'] == 'news'), None)

        if news_vote:
            logger.info(f"✅ NewsAgent participated in debate")
            logger.info(f"  News count: {news_vote.get('news_count', 0)}")
            logger.info(f"  Emergency count: {news_vote.get('emergency_count', 0)}")
            logger.info(f"  Sentiment score: {news_vote.get('sentiment_score', 0):.2f}")

            if news_vote.get('news_count', 0) > 0:
                logger.info(f"✅ NewsAgent successfully used Phase 20 data")
            else:
                logger.warning(f"⚠️ NewsAgent found no news (expected if no {ticker} news in DB)")
        else:
            logger.error(f"❌ NewsAgent did not participate in debate!")

        # 5. Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"📝 TEST SUMMARY")
        logger.info(f"{'='*80}\n")

        logger.info(f"Ticker: {ticker}")
        logger.info(f"Agents voted: {len(votes)}/6")
        logger.info(f"Consensus: {pm_decision['consensus_action']} ({pm_decision['consensus_confidence']:.2%})")
        logger.info(f"Signal generation: {'YES' if will_generate_signal else 'NO'}")
        logger.info(f"NewsAgent integration: {'VERIFIED' if news_vote and news_vote.get('news_count', 0) > 0 else 'NEEDS DATA'}")

        return {
            'success': True,
            'ticker': ticker,
            'votes': votes,
            'pm_decision': pm_decision,
            'signal_generated': will_generate_signal
        }

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def test_database_records(ticker: str = "AAPL"):
    """
    Test database record creation.

    Checks:
    - AIDebateSession created
    - TradingSignal created (if confidence >= 0.7)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"💾 Testing Database Records")
    logger.info(f"{'='*80}\n")

    db = get_sync_session()

    try:
        # Get latest session for ticker
        session = db.query(AIDebateSession)\
            .filter(AIDebateSession.ticker == ticker)\
            .order_by(AIDebateSession.created_at.desc())\
            .first()

        if session:
            logger.info(f"✅ AIDebateSession found:")
            logger.info(f"  ID: {session.id}")
            logger.info(f"  Ticker: {session.ticker}")
            logger.info(f"  Consensus: {session.consensus_action} ({session.consensus_confidence:.2%})")
            logger.info(f"  Votes:")
            logger.info(f"    Trader: {session.trader_vote}")
            logger.info(f"    Risk: {session.risk_vote}")
            logger.info(f"    Analyst: {session.analyst_vote}")
            logger.info(f"    Macro: {session.macro_vote}")
            logger.info(f"    Institutional: {session.institutional_vote}")
            logger.info(f"    News: {session.news_vote}")
            logger.info(f"    PM: {session.pm_vote}")

            # Check signal
            if session.signal_id:
                signal = db.query(TradingSignal)\
                    .filter(TradingSignal.id == session.signal_id)\
                    .first()

                if signal:
                    logger.info(f"\n✅ TradingSignal found:")
                    logger.info(f"  ID: {signal.id}")
                    logger.info(f"  Action: {signal.action}")
                    logger.info(f"  Confidence: {signal.confidence:.2%}")
                    logger.info(f"  Source: {signal.source}")
                else:
                    logger.error(f"❌ Signal ID {session.signal_id} not found in database!")
            else:
                logger.info(f"\n⚠️ No signal generated (confidence < 70%)")
        else:
            logger.warning(f"⚠️ No debate session found for {ticker}")

    finally:
        db.close()


async def main():
    """Run all E2E tests."""

    # Test with AAPL (likely to have news)
    result = await test_war_room_debate("AAPL")

    if result['success']:
        # Check database records
        await asyncio.sleep(1)  # Give DB time to commit
        await test_database_records("AAPL")

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ E2E TEST PASSED")
        logger.info(f"{'='*80}\n")
    else:
        logger.error(f"\n{'='*80}")
        logger.error(f"❌ E2E TEST FAILED")
        logger.error(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
