"""
Create rss_feeds table in PostgreSQL
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')

from backend.database.models import RSSFeed

def create_rss_feeds_table():
    """Create rss_feeds table if not exists"""
    engine = create_engine(DATABASE_URL, echo=False)

    # Create only rss_feeds table
    RSSFeed.__table__.create(engine, checkfirst=True)
    print("✅ rss_feeds table created successfully")

    # Add default RSS feeds if empty
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        existing_count = db.query(RSSFeed).count()
        if existing_count == 0:
            default_feeds = [
                RSSFeed(name="CNBC Top News", url="https://www.cnbc.com/id/100003114/device/rss/rss.html", category="global"),
                RSSFeed(name="MarketWatch", url="https://feeds.marketwatch.com/marketwatch/topstories/", category="global"),
                RSSFeed(name="Seeking Alpha", url="https://seekingalpha.com/feed.xml", category="global"),
                RSSFeed(name="Investing.com", url="https://www.investing.com/rss/news.rss", category="global"),
                RSSFeed(name="연합뉴스 경제", url="https://www.yna.co.kr/rss/economy.xml", category="korea"),
                RSSFeed(name="한국경제", url="https://www.hankyung.com/feed/all-news", category="korea"),
                RSSFeed(name="매일경제", url="https://www.mk.co.kr/rss/30000001/", category="korea"),
            ]
            for feed in default_feeds:
                db.add(feed)
            db.commit()
            print(f"✅ Added {len(default_feeds)} default RSS feeds")
        else:
            print(f"ℹ️ RSS feeds already exist: {existing_count} feeds")
    finally:
        db.close()

if __name__ == "__main__":
    create_rss_feeds_table()
