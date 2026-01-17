import sys
sys.path.insert(0, ".")

from backend.database.models import RSSFeed
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(url)
RSSFeed.__table__.create(engine, checkfirst=True)
print("rss_feeds table created")

# Add default feeds if empty
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    count = db.query(RSSFeed).count()
    if count == 0:
        feeds = [
            RSSFeed(name="CNBC Top News", url="https://www.cnbc.com/id/100003114/device/rss/rss.html", category="global"),
            RSSFeed(name="MarketWatch", url="https://feeds.marketwatch.com/marketwatch/topstories/", category="global"),
            RSSFeed(name="Seeking Alpha", url="https://seekingalpha.com/feed.xml", category="global"),
            RSSFeed(name="Investing.com", url="https://www.investing.com/rss/news.rss", category="global"),
            RSSFeed(name="연합뉴스 경제", url="https://www.yna.co.kr/rss/economy.xml", category="korea"),
            RSSFeed(name="한국경제", url="https://www.hankyung.com/feed/all-news", category="korea"),
            RSSFeed(name="매일경제", url="https://www.mk.co.kr/rss/30000001/", category="korea"),
        ]
        for f in feeds:
            db.add(f)
        db.commit()
        print(f"Added {len(feeds)} default RSS feeds")
    else:
        print(f"RSS feeds already exist: {count}")
finally:
    db.close()
