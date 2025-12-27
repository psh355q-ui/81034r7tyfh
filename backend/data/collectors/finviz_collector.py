"""
Finviz News Collector

Real-time US market news scraper
- Source: https://finviz.com/news.ashx
- Update frequency: 5 minutes
- Anti-scraping: User-Agent rotation
- Storage: news_articles table (via NewsRepository)
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import random
from sqlalchemy.orm import Session

from backend.database.repository import get_sync_session, NewsRepository, NewsArticle

logger = logging.getLogger(__name__)


# User-Agent rotation for anti-scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
]


class FinvizCollector:
    """
    Finviz News Scraper
    
    Features:
    - Real-time news collection
    - Ticker extraction
    - 5-minute update cycle
    - Duplicate prevention
    - Anti-scraping protection
    """
    
    def __init__(self):
        self.base_url = "https://finviz.com/news.ashx"
        self.stats = {
            'scraped': 0,
            'new': 0,
            'duplicates': 0,
            'errors': 0
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with random User-Agent"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_latest(self) -> List[Dict]:
        """
        Scrape latest news from Finviz
        
        Returns:
            List of {
                'title': str,
                'url': str,
                'source': str,
                'published_at': datetime,
                'tickers': List[str]
            }
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                
                async with session.get(
                    self.base_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Finviz returned status {response.status}")
                        return []
                    
                    html = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            news_table = soup.find('table', {'id': 'news'})
            
            if not news_table:
                logger.warning("Could not find news table on Finviz page")
                return []
            
            articles = []
            current_date = datetime.now().date()
            
            # Parse news rows
            for row in news_table.find_all('tr'):
                try:
                    article = self._parse_news_row(row, current_date)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            self.stats['scraped'] = len(articles)
            logger.info(f"✅ Finviz: Scraped {len(articles)} articles")
            
            return articles
            
        except asyncio.TimeoutError:
            logger.error("Finviz scraping timeout")
            self.stats['errors'] += 1
            return []
        except Exception as e:
            logger.error(f"Finviz scraping error: {e}")
            self.stats['errors'] += 1
            return []
    
    def _parse_news_row(self, row, current_date) -> Optional[Dict]:
        """
        Parse single news row
        
        Finviz format:
        <tr>
          <td>12:45PM</td>
          <td><a href="...">Title</a></td>
          <td>Source</td>
          <td><a href="/quote.ashx?t=AAPL">AAPL</a></td>
        </tr>
        """
        cells = row.find_all('td')
        if len(cells) < 3:
            return None
        
        # Parse time (e.g., "12:45PM")
        time_cell = cells[0].get_text(strip=True)
        published_at = self._parse_time(time_cell, current_date)
        
        # Parse title and link
        title_cell = cells[1]
        link_tag = title_cell.find('a')
        if not link_tag:
            return None
        
        title = link_tag.get_text(strip=True)
        url = link_tag.get('href', '')
        
        # Make absolute URL if relative
        if url.startswith('/'):
            url = f"https://finviz.com{url}"
        
        # Parse source
        source = cells[2].get_text(strip=True) if len(cells) > 2 else "Finviz"
        
        # Parse tickers (if present)
        tickers = []
        if len(cells) > 3:
            ticker_cell = cells[3]
            ticker_links = ticker_cell.find_all('a')
            for link in ticker_links:
                ticker = link.get_text(strip=True)
                if ticker and ticker.isupper():
                    tickers.append(ticker)
        
        return {
            'title': title,
            'url': url,
            'source': source,
            'published_at': published_at,
            'tickers': tickers
        }
    
    def _parse_time(self, time_str: str, current_date) -> datetime:
        """
        Parse Finviz time format
        """
        time_str = time_str.strip()
        
        # Handle "Yesterday"
        if time_str.lower() == 'yesterday':
            return datetime.combine(
                current_date - timedelta(days=1),
                datetime.min.time()
            )
        
        # Handle "Dec-19" format
        if '-' in time_str:
            try:
                month_day = datetime.strptime(time_str, "%b-%d")
                return datetime(
                    current_date.year,
                    month_day.month,
                    month_day.day
                )
            except:
                pass
        
        # Handle "12:45PM" format
        try:
            parsed_time = datetime.strptime(time_str, "%I:%M%p").time()
            return datetime.combine(current_date, parsed_time)
        except:
            # Default to now
            return datetime.now()
    
    def save_to_db(self, articles: List[Dict]) -> int:
        """
        Save articles to database using NewsRepository
        
        Returns:
            Number of new articles saved
        """
        new_count = 0
        session = get_sync_session()
        news_repo = NewsRepository(session)
        
        try:
            for article_data in articles:
                try:
                    # Check if already exists
                    existing = news_repo.get_article_by_url(article_data['url'])
                    
                    if existing:
                        self.stats['duplicates'] += 1
                        continue
                    
                    # Create article dict for repository
                    article_dict = {
                        'url': article_data['url'],
                        'title': article_data['title'],
                        'source': article_data['source'],
                        'published_at': article_data['published_at'],
                        'content': '',
                        'summary': article_data['title'], # Use title as summary initially
                        'tickers': article_data.get('tickers', []),
                        'tags': [],
                        'metadata': {
                            'feed_source': 'finviz'
                        }
                    }
                    
                    news_repo.save_processed_article(article_dict)
                    new_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving article: {e}")
                    self.stats['errors'] += 1
                    continue
            
            self.stats['new'] = new_count
            logger.info(f"💾 Saved {new_count} new articles to DB")
            
        except Exception as e:
            logger.error(f"DB save error: {e}")
        finally:
            session.close()
        
        return new_count
    
    async def run_once(self) -> Dict:
        """
        Run single scraping cycle
        
        Returns:
            Statistics dict
        """
        logger.info("🔄 Starting Finviz scraping cycle...")
        
        # Reset stats
        self.stats = {'scraped': 0, 'new': 0, 'duplicates': 0, 'errors': 0}
        
        # Scrape
        articles = await self.scrape_latest()
        
        # Save to DB
        if articles:
            self.save_to_db(articles)
        
        logger.info(
            f"✅ Finviz cycle complete: "
            f"{self.stats['scraped']} scraped, "
            f"{self.stats['new']} new, "
            f"{self.stats['duplicates']} duplicates"
        )
        
        return self.stats
    
    async def run_periodic(self, interval_minutes: int = 5):
        """
        Run scraper periodically
        
        Args:
            interval_minutes: Minutes between scraping cycles
        """
        logger.info(f"🚀 Starting Finviz periodic scraper (every {interval_minutes} min)")
        
        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"❌ Scraping cycle error: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(interval_minutes * 60)


# =============================================================================
# Utility Functions
# =============================================================================

def get_recent_finviz_news(
    hours: int = 24,
    limit: int = 50
) -> List[Dict]:
    """Get recent Finviz news"""
    session = get_sync_session()
    news_repo = NewsRepository(session)
    try:
        # Note: Repository might need a method to filter by source/metadata
        # For now, we reuse existing methods or add one if strictly needed.
        # But for 'recent', simple query via Repository is best.
        # Since repository returns NewsArticle objects, we can filter in python or add repo method.
        # Let's add a raw query here for simplicity or assume get_latest_news works.
        
        # Temporary: using repo session for custom query
        since = datetime.now() - timedelta(hours=hours)
        
        # We need to query based on metadata since we stored feed_source there
        # OR use the source column if that mapped effectively.
        # In save_to_db we set metadata={'feed_source': 'finviz'}
        
        # Let's just return latest news generally for now, or improve Repository later
        articles = news_repo.get_latest_news(limit=limit) 
        # Filter in memory for now if needed, but get_latest_news returns all sources.
        
        return [
            {
                "title": a.title,
                "source": a.source,
                "keywords": a.tickers # Map tickers to keywords for display
            }
            for a in articles if a.metadata_ and a.metadata_.get('feed_source') == 'finviz'
        ]
    finally:
        session.close()


def get_finviz_stats() -> Dict:
    """Get Finviz collection statistics"""
    session = get_sync_session()
    try:
        # Count articles where metadata->>'feed_source' = 'finviz'
        # This requires JSONB query support which might vary.
        # For now return dummy or basic stats
        return {
            'source': 'finviz',
            'status': 'active'
        }
    finally:
        session.close()


# =============================================================================
# Test/Demo
# =============================================================================

async def test_scraper():
    """Test Finviz scraper"""
    print("🧪 Testing Finviz Scraper\n")
    
    collector = FinvizCollector()
    
    # Run once
    stats = await collector.run_once()
    
    print(f"\n📊 Results:")
    print(f"  Scraped: {stats['scraped']}")
    print(f"  New: {stats['new']}")
    print(f"  Duplicates: {stats['duplicates']}")
    print(f"  Errors: {stats['errors']}")
    
    # Show recent
    recent = get_recent_finviz_news(hours=1, limit=5)
    print(f"\n📰 Recent news ({len(recent)}):")
    for article in recent:
        print(f"  - {article['title'][:60]}...")
        print(f"    Source: {article['source']}, Keywords: {article['keywords']}")


if __name__ == "__main__":
    asyncio.run(test_scraper())
