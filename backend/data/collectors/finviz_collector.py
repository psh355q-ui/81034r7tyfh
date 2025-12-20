"""
Finviz News Collector

Real-time US market news scraper
- Source: https://finviz.com/news.ashx
- Update frequency: 5 minutes
- Anti-scraping: User-Agent rotation
- Storage: news_articles table (feed_source='finviz')
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import random
from sqlalchemy.orm import Session

from backend.data.news_models import NewsArticle, SessionLocal

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
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
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
        
        Examples:
        - "12:45PM" → today 12:45 PM
        - "Dec-19" → December 19 this year
        - "Yesterday" → yesterday
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
        Save articles to database
        
        Returns:
            Number of new articles saved
        """
        new_count = 0
        
        for article_data in articles:
            try:
                # Check if already exists
                existing = self.db.query(NewsArticle).filter(
                    NewsArticle.url == article_data['url']
                ).first()
                
                if existing:
                    self.stats['duplicates'] += 1
                    continue
                
                # Create new article
                article = NewsArticle(
                    url=article_data['url'],
                    title=article_data['title'],
                    source=article_data['source'],
                    feed_source='finviz',  # New source type
                    published_at=article_data['published_at'],
                    # Finviz doesn't provide full content in listing
                    # Content will be extracted later if needed
                    content_text='',
                    content_summary=article_data['title'],
                    keywords=article_data.get('tickers', []),
                    crawled_at=datetime.now()
                )
                
                self.db.add(article)
                new_count += 1
                
            except Exception as e:
                logger.error(f"Error saving article: {e}")
                self.stats['errors'] += 1
                continue
        
        # Commit all at once
        try:
            self.db.commit()
            self.stats['new'] = new_count
            logger.info(f"💾 Saved {new_count} new articles to DB")
        except Exception as e:
            logger.error(f"DB commit error: {e}")
            self.db.rollback()
            return 0
        
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
    db: Session,
    hours: int = 24,
    limit: int = 50
) -> List[NewsArticle]:
    """Get recent Finviz news"""
    since = datetime.now() - timedelta(hours=hours)
    
    return db.query(NewsArticle).filter(
        NewsArticle.feed_source == 'finviz',
        NewsArticle.crawled_at >= since
    ).order_by(
        NewsArticle.published_at.desc()
    ).limit(limit).all()


def get_finviz_stats(db: Session) -> Dict:
    """Get Finviz collection statistics"""
    total = db.query(NewsArticle).filter(
        NewsArticle.feed_source == 'finviz'
    ).count()
    
    today = db.query(NewsArticle).filter(
        NewsArticle.feed_source == 'finviz',
        NewsArticle.crawled_at >= datetime.now().date()
    ).count()
    
    return {
        'total_articles': total,
        'today': today,
        'source': 'finviz'
    }


# =============================================================================
# Test/Demo
# =============================================================================

async def test_scraper():
    """Test Finviz scraper"""
    print("🧪 Testing Finviz Scraper\n")
    
    db = SessionLocal()
    collector = FinvizCollector(db)
    
    # Run once
    stats = await collector.run_once()
    
    print(f"\n📊 Results:")
    print(f"  Scraped: {stats['scraped']}")
    print(f"  New: {stats['new']}")
    print(f"  Duplicates: {stats['duplicates']}")
    print(f"  Errors: {stats['errors']}")
    
    # Show recent
    recent = get_recent_finviz_news(db, hours=1, limit=5)
    print(f"\n📰 Recent news ({len(recent)}):")
    for article in recent:
        print(f"  - {article.title[:60]}...")
        print(f"    Source: {article.source}, Keywords: {article.keywords}")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(test_scraper())
