"""
RSS 크롤러 PostgreSQL 어댑터
기존 rss_crawler.py를 PostgreSQL과 연결
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import sys
from pathlib import Path

# 기존 RSS 크롤러 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.rss_crawler import RSSCrawler
from data.news_models import SessionLocal, RSSFeed, NewsArticle

logger = logging.getLogger(__name__)


class RSSNewsAggregator:
    """
    RSS 크롤러 + PostgreSQL 통합
    
    Finviz 스타일 실시간 뉴스 DB
    """
    
    def __init__(self, pg_connection_string: str):
        """
        Args:
            pg_connection_string: PostgreSQL 연결 문자열
                예: "postgresql://user:pass@localhost:5541/ai_trading"
        """
        self.pg_conn_str = pg_connection_string
        self.sqlite_db = SessionLocal()  # 기존 SQLite DB
        self.rss_crawler = RSSCrawler(self.sqlite_db)
    
    async def sync_to_postgres(self) -> Dict[str, int]:
        """
        SQLite (기존)에서 PostgreSQL로 뉴스 동기화
        
        Returns:
            {'synced': count, 'skipped': count}
        """
        conn = await asyncpg.connect(self.pg_conn_str)
        
        try:
            stats = {'synced': 0, 'skipped': 0, 'errors': 0}
            
            # SQLite에서 최근 24시간 뉴스 조회
            from data.rss_crawler import get_recent_articles
            recent_articles = get_recent_articles(
                self.sqlite_db,
                limit=1000,
                hours=24
            )
            
            logger.info(f"Found {len(recent_articles)} recent articles in SQLite")
            
            for article in recent_articles:
                try:
                    # PostgreSQL에 저장 (중복 체크)
                    exists = await conn.fetchval(
                        "SELECT id FROM news_articles WHERE url = $1",
                        article.url
                    )
                    
                    if exists:
                        stats['skipped'] += 1
                        continue
                    
                    # 새 기사 삽입
                    await conn.execute(
                        """
                        INSERT INTO news_articles (
                            url,
                            title,
                            content,
                            summary,
                            published_at,
                            author,
                            source,
                            tags,
                            sentiment_score,
                            created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                        """,
                        article.url,
                        article.title,
                        article.content or '',
                        article.summary or '',
                        article.published_at or datetime.now(),
                        article.author or '',
                        article.feed_source or 'rss',
                        article.tags or [],
                        article.sentiment_score or 0.0
                    )
                    
                    stats['synced'] += 1
                
                except Exception as e:
                    logger.error(f"Error syncing article {article.url}: {e}")
                    stats['errors'] += 1
            
            logger.info(f"Sync complete: {stats}")
            return stats
        
        finally:
            await conn.close()
    
    async def crawl_and_save(self, extract_content: bool = True) -> Dict[str, int]:
        """
        RSS 피드 크롤링하고 바로 PostgreSQL에 저장
        
        Returns:
            {'crawled': count, 'saved': count}
        """
        # 1. RSS 크롤링 (SQLite에 저장)
        logger.info("Crawling RSS feeds...")
        new_articles = self.rss_crawler.crawl_all_feeds(extract_content=extract_content)
        
        # 2. PostgreSQL에 동기화
        logger.info(f"Crawled {len(new_articles)} articles, syncing to PostgreSQL...")
        stats = await self.sync_to_postgres()
        
        return {
            'crawled': len(new_articles),
            'saved': stats['synced']
        }
    
    async def get_realtime_news(
        self,
        limit: int = 50,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL에서 실시간 뉴스 조회 (Finviz 스타일)
        
        Returns:
            [
                {
                    'title': str,
                    'link': str,
                    'source': str,
                    'time_ago': '24 min',
                    'published_at': datetime
                }
            ]
        """
        conn = await asyncpg.connect(self.pg_conn_str)
        
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            rows = await conn.fetch(
                """
                SELECT 
                    title,
                    url as link,
                    source,
                    published_at,
                    EXTRACT(EPOCH FROM (NOW() - published_at))/60 as minutes_ago
                FROM news_articles
                WHERE published_at > $1
                ORDER BY published_at DESC
                LIMIT $2
                """,
                cutoff,
                limit
            )
            
            news = []
            for row in rows:
                minutes_ago = row['minutes_ago']
                
                # Finviz 스타일 시간 표시
                if minutes_ago < 60:
                    time_ago = f"{int(minutes_ago)} min"
                elif minutes_ago < 1440:
                    time_ago = f"{int(minutes_ago/60)}h ago"
                else:
                    time_ago = f"{int(minutes_ago/1440)}d ago"
                
                news.append({
                    'title': row['title'],
                    'link': row['link'],
                    'source': row['source'],
                    'time_ago': time_ago,
                    'published_at': row['published_at']
                })
            
            return news
        
        finally:
            await conn.close()


async def test_aggregator():
    """테스트"""
    print("=" * 70)
    print("  RSS News Aggregator 테스트")
    print("=" * 70)
    print()
    
    # PostgreSQL 연결
    pg_conn = "postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading"
    
    aggregator = RSSNewsAggregator(pg_conn)
    
    # 1. 크롤링 & 저장
    print("1. Crawling RSS feeds...")
    stats = await aggregator.crawl_and_save(extract_content=False)  # 빠른 테스트
    print(f"   ✅ Crawled: {stats['crawled']}")
    print(f"   ✅ Saved: {stats['saved']}")
    print()
    
    # 2. 실시간 뉴스 조회
    print("2. Fetching realtime news (Finviz style)...")
    news = await aggregator.get_realtime_news(limit=10)
    
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
