
import sys
import os
import aiohttp
import asyncio
import feedparser
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.data.news_models import get_db, RSSFeed
from sqlalchemy.orm import Session

NEW_FEEDS = [
    # Global Finance
    {"name": "Financial Times", "url": "https://www.ft.com/rss/home", "category": "global_finance"},
    {"name": "Fortune", "url": "https://fortune.com/feed/fortune-feed.xml", "category": "global_finance"},
    {"name": "Nasdaq Market News", "url": "https://www.nasdaq.com/feed/rssoutbound?category=MarketNews", "category": "global_finance"},
    {"name": "Yahoo Finance Top", "url": "https://finance.yahoo.com/rss/", "category": "global_finance"},
    {"name": "Benzinga", "url": "https://feeds.benzinga.com/benzinga", "category": "global_finance"},
    {"name": "TheStreet", "url": "https://www.thestreet.com/.rss/full", "category": "global_finance"},
    
    # Geopolitics & Macro
    {"name": "IMF News", "url": "https://www.imf.org/en/rss-list", "category": "macro"},
    {"name": "WTO News", "url": "http://www.wto.org/library/rss/latest_news_e.xml", "category": "macro"},
    {"name": "Reuters World", "url": "https://www.reuters.com/world/rss", "category": "geopolitics"},
    {"name": "Al Jazeera World", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "geopolitics"},
    {"name": "BBC World News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "geopolitics"},
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "category": "defense"},
    {"name": "Foreign Policy", "url": "https://foreignpolicy.com/feed/", "category": "geopolitics"},
    
    # Energy
    {"name": "OilPrice.com", "url": "https://oilprice.com/rss/main", "category": "energy"},
    {"name": "EIA Today in Energy", "url": "https://www.eia.gov/rss/todayinenergy.xml", "category": "energy"},
    {"name": "Investing Commodities", "url": "https://www.investing.com/rss/commodities.rss", "category": "energy"},
    
    # Google News Custom (The "Hack")
    {"name": "Google News: Venezuela Oil", "url": "https://news.google.com/rss/search?q=Venezuela+Oil+Crisis+Maduro&hl=en-US&gl=US&ceid=US:en", "category": "special_topic"},
    {"name": "Google News: Exxon Chevron", "url": "https://news.google.com/rss/search?q=ExxonMobil+Chevron+Stock+News&hl=en-US&gl=US&ceid=US:en", "category": "special_topic"},
    {"name": "Google News: US Treasury Fed", "url": "https://news.google.com/rss/search?q=US+Treasury+Yield+Federal+Reserve&hl=en-US&gl=US&ceid=US:en", "category": "macro"}
]

async def verify_feed(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                return False, f"HTTP {response.status}"
            content = await response.text()
            feed = feedparser.parse(content)
            if feed.bozo:
                return False, "Parse Error (Bozo)"
            if not feed.entries:
                return False, "No Entries"
            return True, f"OK ({len(feed.entries)} entries)"
    except Exception as e:
        return False, str(e)

async def main():
    db_gen = get_db()
    db = next(db_gen)
    
    print(f"Checking {len(NEW_FEEDS)} new feeds...")
    
    async with aiohttp.ClientSession() as session:
        for feed_data in NEW_FEEDS:
            # Check for existing URL
            existing = db.query(RSSFeed).filter(RSSFeed.url == feed_data["url"]).first()
            if existing:
                print(f"Skipping existing URL: {feed_data['name']}")
                continue
                
            # Check for existing Name
            existing_name = db.query(RSSFeed).filter(RSSFeed.name == feed_data["name"]).first()
            if existing_name:
                print(f"Skipping existing Name: {feed_data['name']}")
                continue

            print(f"Verifying {feed_data['name']}...", end=" ", flush=True)
            valid, msg = await verify_feed(session, feed_data["url"])
            
            if valid:
                print(f"✅ {msg}")
                new_feed = RSSFeed(
                    name=feed_data["name"],
                    url=feed_data["url"],
                    category=feed_data["category"],
                    enabled=True,
                    created_at=datetime.utcnow()
                )
                db.add(new_feed)
            else:
                print(f"❌ {msg} - Skipping")
        
        db.commit()
    
    print("\nAttempting to cleanup broken feeds (Reuters/Bloomberg main)...")
    # Logic to disable known broken feeds if needed, for now just logging
    broken_keywords = ["bloomberg.com", "reuters.com"] # Only main ones, not the specific working RSS
    # (Note: The new Reuters ones are sub-sections which might work, main ones usually block)
    
    db.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
