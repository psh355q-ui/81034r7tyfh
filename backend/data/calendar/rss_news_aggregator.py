"""
RSS 크롤러 PostgreSQL 어댑터 (Simplified)
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import sys
from pathlib import Path

# Updated RSS Crawler import
from backend.data.rss_crawler import RSSCrawler
from backend.database.repository import NewsRepository, get_sync_session

logger = logging.getLogger(__name__)


class RSSNewsAggregator:
    """
    RSS 크롤러 Wrapper (Repository 패턴, PostgreSQL 직접 사용)
    """
    
    def __init__(self):
        """
        Initializes with a fresh session/crawler that connects to Postgres.
        """
        self.crawler = RSSCrawler() # Internal session created
    
    def crawl_and_save(self, extract_content: bool = True) -> Dict[str, int]:
        """
        RSS 피드 크롤링하고 PostgreSQL에 저장 (Direct)
        
        Returns:
            {'crawled': count, 'saved': count}
        """
        logger.info("Crawling RSS feeds via RSSCrawler...")
        
        try:
            result = self.crawler.crawl_all_feeds(extract_content=extract_content)
            stats = result.get('stats', {})
            
            return {
                'crawled': stats.get('articles_found', 0),
                'saved': stats.get('articles_new', 0)
            }
        except Exception as e:
            logger.error(f"Error in crawl_and_save: {e}")
            return {'crawled': 0, 'saved': 0}
        
    def get_realtime_news(
        self,
        limit: int = 50,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL에서 실시간 뉴스 조회 (Finviz 스타일)
        """
        session = get_sync_session()
        
        try:
            repo = NewsRepository(session)
            articles = repo.get_recent_articles(hours=hours, source=None)
            
            # Limit 적용
            articles = articles[:limit]
            
            news = []
            for article in articles:
                # 시간 계산
                time_diff = datetime.now() - article.published_date
                minutes_ago = time_diff.total_seconds() / 60
                
                # Finviz 스타일 시간 표시
                if minutes_ago < 60:
                    time_ago = f"{int(minutes_ago)} min"
                elif minutes_ago < 1440:
                    time_ago = f"{int(minutes_ago/60)}h ago"
                else:
                    time_ago = f"{int(minutes_ago/1440)}d ago"
                
                news.append({
                    'title': article.title,
                    'link': article.url,
                    'source': article.source,
                    'time_ago': time_ago,
                    'published_at': article.published_date
                })
            
            return news
        
        finally:
            session.close()


async def test_aggregator():
    """테스트"""
    print("=" * 70)
    print("  RSS News Aggregator 테스트 (Direct Postgres)")
    print("=" * 70)
    print()
    
    aggregator = RSSNewsAggregator()
    
    # 1. 크롤링 & 저장
    print("1. Crawling RSS feeds...")
    stats = aggregator.crawl_and_save(extract_content=False)  # 빠른 테스트
    print(f"   ✅ Crawled: {stats['crawled']}")
    print(f"   ✅ Saved: {stats['saved']}")
    print()
    
    # 2. 실시간 뉴스 조회
    print("2. Fetching realtime news (Finviz style)...")
    news = aggregator.get_realtime_news(limit=10)
    
    if news:
        print(f"   ✅ Found {len(news)} articles\n")
        
        for i, article in enumerate(news, 1):
            # ASML/China 체크
            if any(kw in article['title'].upper() for kw in ['ASML', 'CHINA', 'AI', 'CHIP']):
                marker = "⭐ "
            else:
                marker = "   "
            
            print(f"{marker}{i}. [{article['time_ago']}] {article['title'][:55]}...")
            print(f"       └─ {article['source']}")
            print()
    else:
        print("   ❌ No news found")


if __name__ == "__main__":
    asyncio.run(test_aggregator())
