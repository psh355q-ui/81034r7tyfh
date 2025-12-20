"""
RSS Feed Discovery & Auto-Update

Automatically discover RSS feeds from Finviz news sources
and update RSS Management system

Features:
- Scrape news sources from Finviz
- Discover RSS feed URLs for each source
- Auto-add to rss_feeds table
- API endpoint for RSS Management frontend
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import logging
from sqlalchemy.orm import Session
from datetime import datetime
import re

from backend.data.news_models import RSSFeed, SessionLocal

logger = logging.getLogger(__name__)


# =============================================================================
# Known RSS Feed Mappings (Major sources)
# =============================================================================

RSS_FEED_MAPPINGS = {
    # Major financial news
    'Bloomberg': 'https://www.bloomberg.com/feeds/podcasts/etf-iq.xml',
    'Reuters': 'https://www.reutersagency.com/feed/',
    'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    'MarketWatch': 'https://feeds.marketwatch.com/marketwatch/topstories/',
    'WSJ': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
    'Financial Times': 'https://www.ft.com/?format=rss',
    
    # Tech/Business
    'TechCrunch': 'https://techcrunch.com/feed/',
    'Business Insider': 'https://www.businessinsider.com/rss',
    'Forbes': 'https://www.forbes.com/real-time/feed2/',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    
    # Investment
    'Seeking Alpha': 'https://seekingalpha.com/feed.xml',
    'Benzinga': 'https://www.benzinga.com/feed',
    'Investing.com': 'https://www.investing.com/rss/news.rss',
    'Zacks': 'https://www.zacks.com/rss/stock_news.xml',
    
    # Alternative matches
    'bloomberg.com': 'https://www.bloomberg.com/feeds/podcasts/etf-iq.xml',
    'reuters.com': 'https://www.reutersagency.com/feed/',
    'cnbc.com': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    'marketwatch.com': 'https://feeds.marketwatch.com/marketwatch/topstories/',
    'wsj.com': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
}


# =============================================================================
# RSS Feed Discovery
# =============================================================================

class RSSFeedDiscovery:
    """
    Discover RSS feeds from Finviz news sources
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.discovered_sources: Set[str] = set()
        self.discovered_feeds: List[Dict] = []
    
    async def discover_from_finviz(self) -> List[Dict]:
        """
        Scrape Finviz news page and discover sources
        
        Returns:
            List of {
                'source_name': str,
                'rss_url': str,
                'category': str,
                'confidence': 'high'|'medium'|'low'
            }
        """
        logger.info("🔍 Discovering news sources from Finviz...")
        
        # Scrape both Finviz versions
        sources = set()
        for url in ['https://finviz.com/news.ashx', 'https://finviz.com/news.ashx?v=3']:
            try:
                page_sources = await self._scrape_finviz_sources(url)
                sources.update(page_sources)
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
        
        logger.info(f"📊 Found {len(sources)} unique sources from Finviz")
        
        # Discover RSS feeds for each source
        feeds = []
        for source_name in sources:
            feed_data = await self._discover_rss_for_source(source_name)
            if feed_data:
                feeds.append(feed_data)
        
        self.discovered_feeds = feeds
        logger.info(f"✅ Discovered {len(feeds)} RSS feeds")
        
        return feeds
    
    async def _scrape_finviz_sources(self, url: str) -> Set[str]:
        """Scrape news sources from Finviz page"""
        sources = set()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        return sources
                    
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find news table
            news_table = soup.find('table', id='news')
            if not news_table:
                # Try alternative selectors
                news_table = soup.find('table', class_='news')
            
            if news_table:
                # Extract sources from news items
                for row in news_table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Source is usually in 3rd cell
                        source_cell = cells[2]
                        source_text = source_cell.get_text(strip=True)
                        
                        if source_text and len(source_text) > 2:
                            # Clean source name
                            source_text = source_text.replace('...', '').strip()
                            sources.add(source_text)
            
            # Also check links for domain-based sources
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(domain in href for domain in ['bloomberg.com', 'reuters.com', 'cnbc.com', 'marketwatch.com']):
                    # Extract domain-based source
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', href)
                    if domain_match:
                        domain = domain_match.group(1)
                        sources.add(domain)
            
        except Exception as e:
            logger.error(f"Error scraping sources: {e}")
        
        return sources
    
    async def _discover_rss_for_source(self, source_name: str) -> Optional[Dict]:
        """
        Discover RSS feed URL for a source
        
        Methods:
        1. Check known mappings
        2. Try common RSS patterns
        3. Search website for RSS links
        """
        # Method 1: Known mappings
        for key, rss_url in RSS_FEED_MAPPINGS.items():
            if key.lower() in source_name.lower() or source_name.lower() in key.lower():
                logger.info(f"✅ Found known RSS: {source_name} → {rss_url}")
                return {
                    'source_name': source_name,
                    'rss_url': rss_url,
                    'category': 'global',
                    'confidence': 'high'
                }
        
        # Method 2: Try common RSS patterns
        common_patterns = self._generate_rss_patterns(source_name)
        for pattern_url in common_patterns:
            if await self._verify_rss_url(pattern_url):
                logger.info(f"✅ Discovered RSS: {source_name} → {pattern_url}")
                return {
                    'source_name': source_name,
                    'rss_url': pattern_url,
                    'category': 'global',
                    'confidence': 'medium'
                }
        
        # Method 3: Search website (advanced, skip for now)
        logger.warning(f"⚠️  No RSS found for: {source_name}")
        return None
    
    def _generate_rss_patterns(self, source_name: str) -> List[str]:
        """Generate common RSS URL patterns"""
        patterns = []
        
        # Extract base domain if looks like domain
        if '.' in source_name and ' ' not in source_name:
            domain = source_name
            patterns.extend([
                f"https://{domain}/feed",
                f"https://{domain}/rss",
                f"https://{domain}/feed.xml",
                f"https://{domain}/rss.xml",
                f"https://www.{domain}/feed",
                f"https://www.{domain}/rss",
            ])
        
        return patterns
    
    async def _verify_rss_url(self, url: str) -> bool:
        """Verify if URL is a valid RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return False
                    
                    content = await response.text()
                    
                    # Check for RSS/Atom markers
                    return any(marker in content[:500] for marker in [
                        '<rss', '<feed', '<?xml', '<channel'
                    ])
        except:
            return False
    
    def add_to_database(self, feeds: List[Dict] = None) -> int:
        """
        Add discovered feeds to database
        
        Returns:
            Number of new feeds added
        """
        if feeds is None:
            feeds = self.discovered_feeds
        
        added_count = 0
        
        for feed_data in feeds:
            try:
                # Check if already exists
                existing = self.db.query(RSSFeed).filter(
                    RSSFeed.url == feed_data['rss_url']
                ).first()
                
                if existing:
                    logger.debug(f"Feed already exists: {feed_data['source_name']}")
                    continue
                
                # Add new feed
                new_feed = RSSFeed(
                    name=feed_data['source_name'],
                    url=feed_data['rss_url'],
                    category=feed_data.get('category', 'global'),
                    enabled=True
                )
                
                self.db.add(new_feed)
                added_count += 1
                logger.info(f"➕ Added: {feed_data['source_name']}")
                
            except Exception as e:
                logger.error(f"Error adding feed {feed_data['source_name']}: {e}")
        
        # Commit all at once
        try:
            self.db.commit()
            logger.info(f"💾 Added {added_count} new RSS feeds to database")
        except Exception as e:
            logger.error(f"Database commit error: {e}")
            self.db.rollback()
            return 0
        
        return added_count


# =============================================================================
# Auto-Update Scheduler
# =============================================================================

class RSSAutoUpdater:
    """
    Periodically discover and update RSS feeds
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.discovery = RSSFeedDiscovery(db=self.db)
    
    async def run_discovery_cycle(self) -> Dict:
        """
        Run one discovery and update cycle
        
        Returns:
            Stats dict
        """
        logger.info("🔄 Starting RSS discovery cycle...")
        
        # Discover feeds
        feeds = await self.discovery.discover_from_finviz()
        
        # Add to database
        added = self.discovery.add_to_database(feeds)
        
        stats = {
            'discovered': len(feeds),
            'added': added,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(
            f"✅ Discovery cycle complete: "
            f"{stats['discovered']} discovered, {stats['added']} added"
        )
        
        return stats
    
    async def run_periodic(self, interval_hours: int = 24):
        """
        Run discovery periodically
        
        Args:
            interval_hours: Hours between discovery cycles (default 24)
        """
        logger.info(f"🚀 Starting periodic RSS discovery (every {interval_hours}h)")
        
        while True:
            try:
                await self.run_discovery_cycle()
            except Exception as e:
                logger.error(f"Discovery cycle error: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(interval_hours * 3600)


# =============================================================================
# API Helper Functions
# =============================================================================

async def discover_and_update_rss_feeds(db: Session = None) -> Dict:
    """
    One-shot: Discover RSS feeds and update database
    
    Usage in API:
        from backend.data.rss_feed_discovery import discover_and_update_rss_feeds
        
        @router.post("/rss/discover")
        async def discover_feeds():
            stats = await discover_and_update_rss_feeds()
            return stats
    """
    updater = RSSAutoUpdater(db=db)
    return await updater.run_discovery_cycle()


def get_all_rss_feeds(db: Session = None) -> List[Dict]:
    """
    Get all RSS feeds from database
    
    For RSS Management frontend
    """
    db = db or SessionLocal()
    
    feeds = db.query(RSSFeed).all()
    
    return [
        {
            'id': feed.id,
            'name': feed.name,
            'url': feed.url,
            'category': feed.category,
            'enabled': feed.enabled,
            'last_fetched': feed.last_fetched.isoformat() if feed.last_fetched else None,
            'total_articles': feed.total_articles
        }
        for feed in feeds
    ]


# =============================================================================
# Manual Feed Addition (for RSS Management UI)
# =============================================================================

def add_manual_rss_feed(
    name: str,
    url: str,
    category: str = 'global',
    db: Session = None
) -> Dict:
    """
    Manually add RSS feed (from frontend)
    
    Returns:
        {'success': bool, 'message': str, 'feed_id': int}
    """
    db = db or SessionLocal()
    
    try:
        # Check duplicate
        existing = db.query(RSSFeed).filter(RSSFeed.url == url).first()
        if existing:
            return {
                'success': False,
                'message': f'Feed already exists: {existing.name}',
                'feed_id': existing.id
            }
        
        # Add feed
        new_feed = RSSFeed(
            name=name,
            url=url,
            category=category,
            enabled=True
        )
        
        db.add(new_feed)
        db.commit()
        db.refresh(new_feed)
        
        return {
            'success': True,
            'message': f'RSS feed added: {name}',
            'feed_id': new_feed.id
        }
        
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'message': f'Error adding feed: {str(e)}',
            'feed_id': None
        }


# =============================================================================
# Test/Demo
# =============================================================================

async def test_discovery():
    """Test RSS feed discovery"""
    print("🧪 Testing RSS Feed Discovery\n")
    
    db = SessionLocal()
    discovery = RSSFeedDiscovery(db)
    
    # Discover feeds
    feeds = await discovery.discover_from_finviz()
    
    print(f"\n📊 Discovery Results:")
    print(f"  Total discovered: {len(feeds)}")
    print(f"\n📰 Discovered Feeds:")
    
    for i, feed in enumerate(feeds, 1):
        print(f"\n  {i}. {feed['source_name']}")
        print(f"     URL: {feed['rss_url']}")
        print(f"     Confidence: {feed['confidence']}")
    
    # Add to database
    print(f"\n💾 Adding to database...")
    added = discovery.add_to_database(feeds)
    print(f"✅ Added {added} new feeds")
    
    # Show all feeds
    all_feeds = get_all_rss_feeds(db)
    print(f"\n📋 Total RSS feeds in database: {len(all_feeds)}")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(test_discovery())
