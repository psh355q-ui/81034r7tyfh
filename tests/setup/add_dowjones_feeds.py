"""
Quick script to add Dow Jones / MarketWatch RSS feeds

Usage:
    python add_dowjones_feeds.py
"""

from backend.data.news_models import RSSFeed, SessionLocal, init_db

# Initialize DB first
init_db()

# Dow Jones / MarketWatch RSS feeds
FEEDS = [
    {
        "name": "WSJ World News",
        "url": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
        "category": "global"
    },
    {
        "name": "WSJ Opinion",
        "url": "https://feeds.content.dowjones.io/public/rss/RSSOpinion",
        "category": "global"
    },
    {
        "name": "MarketWatch Top Stories",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "category": "finance"
    },
    {
        "name": "MarketWatch Real-time Headlines",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
        "category": "finance"
    },
    {
        "name": "MarketWatch Bulletins",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_bulletins",
        "category": "finance"
    },
    {
        "name": "MarketWatch Market Pulse",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
        "category": "finance"
    },
]

def add_feeds():
    """Add Dow Jones feeds to database"""
    db = SessionLocal()
    added = 0
    skipped = 0
    
    try:
        for feed_data in FEEDS:
            # Check if already exists
            existing = db.query(RSSFeed).filter(
                RSSFeed.url == feed_data['url']
            ).first()
            
            if existing:
                print(f"⏭️  Skipped (exists): {feed_data['name']}")
                skipped += 1
                continue
            
            # Add new feed
            new_feed = RSSFeed(
                name=feed_data['name'],
                url=feed_data['url'],
                category=feed_data['category'],
                enabled=True
            )
            
            db.add(new_feed)
            print(f"✅ Added: {feed_data['name']}")
            added += 1
        
        db.commit()
        print(f"\n📊 Summary: {added} added, {skipped} skipped")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Adding Dow Jones / MarketWatch RSS feeds...\n")
    add_feeds()
    print("\n✅ Done!")
