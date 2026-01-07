import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from backend.database.repository import get_sync_session, NewsInterpretationRepository, NewsMarketReactionRepository
from backend.database.models import NewsInterpretation, NewsArticle, NewsMarketReaction
from backend.automation.price_tracking_verifier import PriceTrackingVerifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_data(session):
    """테스트용 과거 데이터 주입"""
    logger.info("🛠️ Setting up test data...")
    
    # 1. Create a dummy article
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import hashlib
    content = f"This is a test article created at {timestamp}."
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    article = NewsArticle(
        title=f"Test Article for Price Verification {timestamp}",
        content=content,
        published_date=datetime.now() - timedelta(hours=3),
        source="Test Source",
        url=f"http://test.com/{timestamp}",
        content_hash=content_hash
    )
    session.add(article)
    session.flush()
    
    # 2. Create a dummy interpretation (BULLISH, 2 hours ago)
    interp = NewsInterpretation(
        news_article_id=article.id,
        ticker="AAPL",
        headline_bias="BULLISH",
        expected_impact="HIGH",
        time_horizon="IMMEDIATE",
        confidence=90,
        reasoning="Test reasoning",
        interpreted_at=datetime.now() - timedelta(hours=2)
    )
    session.add(interp)
    session.flush()
    
    # 3. Create a pending reaction record (Price at news time: $100)
    # We will assume current price of AAPL is different (likely > 100 or < 100)
    # KIS Broker (Paper) AAPL price is typically around $150-$200
    reaction = NewsMarketReaction(
        interpretation_id=interp.id,
        ticker="AAPL",
        price_at_news=Decimal("150.00"), # Assume price near current levels
        news_at=datetime.now() - timedelta(hours=2),
        created_at=datetime.now() - timedelta(hours=2) # IMPORTANT for verification query
    )
    session.add(reaction)
    session.commit()
    
    logger.info(f"✅ Test data created: Interpretation ID {interp.id}, Reaction ID {reaction.id}")
    return reaction.id

async def run_verification():
    """Verifier 실행 및 결과 확인"""
    logger.info("🏃 Running verification...")
    
    verifier = PriceTrackingVerifier()
    
    # Run 1h verification
    result = await verifier.verify_interpretations("1h")
    print(f"Result: {result}")
    
    return result

def check_result(session, reaction_id):
    """결과 검증"""
    reaction = session.query(NewsMarketReaction).filter_by(id=reaction_id).first()
    
    logger.info(f"🧐 Checking result for ID {reaction_id}...")
    logger.info(f"    - Verified At: {reaction.verified_at}")
    logger.info(f"    - Price 1h After: {reaction.price_1h_after}")
    logger.info(f"    - Actual Change: {reaction.actual_price_change_1h}%")
    logger.info(f"    - Interpretation Correct: {reaction.interpretation_correct}")
    
    if reaction.verified_at:
        print("✅ Verification Successful! DB updated.")
    else:
        print("❌ Verification Failed! DB not updated.")

if __name__ == "__main__":
    session = get_sync_session()
    try:
        # 1. Setup
        reaction_id = setup_test_data(session)
        
        # 2. Run
        asyncio.run(run_verification())
        
        # 3. Check
        check_result(session, reaction_id)
        
    finally:
        # Clean up (Optional, but good for repeatability)
        # session.query(NewsMarketReaction).filter_by(id=reaction_id).delete()
        # session.commit()
        session.close()
