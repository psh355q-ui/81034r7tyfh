
import os
import sys
import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.models import AIDebateSession, Base

def test_persistence():
    load_dotenv()
    
    # Use DB_URL directly or construct it
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Force sync driver for this script
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")

    print(f"🔄 Connecting to database: {database_url.split('@')[-1]}")
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create dummy debate data
    ticker = "TEST_TICKER"
    debate_id = f"test-debate-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    votes = [
        {"agent": "trader", "action": "BUY", "confidence": 0.8, "reasoning": "Test reasoning 1"},
        {"agent": "risk", "action": "HOLD", "confidence": 0.6, "reasoning": "Test reasoning 2"}
    ]
    
    try:
        # Create new AIDebateSession object
        debate_session = AIDebateSession(
            ticker=ticker,
            debate_id=debate_id,
            votes=votes,
            consensus_action="BUY",
            consensus_confidence=0.75,
            constitutional_valid=True,
            created_at=datetime.datetime.now(),
            completed_at=datetime.datetime.now(),
            duration_seconds=1.5
        )
        
        # Add and commit
        session.add(debate_session)
        session.commit()
        
        print(f"✅ Saved dummy debate session with ID: {debate_session.id}")
        
        # Verify persistence by querying
        retrieved_session = session.query(AIDebateSession).filter_by(debate_id=debate_id).first()
        
        if retrieved_session:
            print(f"✅ Successfully retrieved session: {retrieved_session.debate_id}")
            print(f"   Ticker: {retrieved_session.ticker}")
            print(f"   Action: {retrieved_session.consensus_action}")
            print(f"   Votes: {json.dumps(retrieved_session.votes, indent=2)}")
        else:
            print("❌ Failed to retrieve session after saving!")

    except Exception as e:
        print(f"❌ Error during persistence test: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_persistence()
