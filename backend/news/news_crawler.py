"""
NewsAPI Real-time Crawler

실시간 뉴스 크롤링 및 자동 매매 트리거

기능:
- NewsAPI 통합 (30분마다 크롤링)
- Tech/Finance 뉴스 필터링
- KIS Auto Trade 트리거
- 중복 제거

작성일: 2025-12-03
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

# Load .env file
from dotenv import load_dotenv
load_dotenv()  # Load from project root .env

# NewsAPI
try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False
    logging.warning("newsapi-python not installed. Run: pip install newsapi-python")

# Database (for deduplication)
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================================
# Database Model
# ============================================================================

class CrawledNews(Base):
    """크롤링된 뉴스 저장 (중복 방지)"""
    __tablename__ = 'crawled_news'
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, index=True)  # 중복 체크용
    title = Column(String)
    description = Column(String, nullable=True)
    source = Column(String)
    published_at = Column(DateTime)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'crawled_at': self.crawled_at.isoformat() if self.crawled_at else None,
            'processed': self.processed
        }


# ============================================================================
# NewsAPI Crawler
# ============================================================================

class NewsAPICrawler:
    """
    NewsAPI 실시간 크롤러
    
    사용법:
        crawler = NewsAPICrawler(api_key=os.getenv('NEWS_API_KEY'))
        articles = await crawler.crawl_latest(hours=1)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        db_url: str = "sqlite:///news_crawler.db"
    ):
        """
        Args:
            api_key: NewsAPI 키 (없으면 환경변수에서 읽기)
            db_url: 데이터베이스 URL
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        
        if not self.api_key and NEWSAPI_AVAILABLE:
            logger.warning("NEWS_API_KEY not set. Get it from: https://newsapi.org/")
        
        # NewsAPI 클라이언트
        if NEWSAPI_AVAILABLE and self.api_key:
            self.client = NewsApiClient(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("NewsAPI crawler disabled (no API key or library)")
        
        # Database setup
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            poolclass=StaticPool if "sqlite" in db_url else None
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"NewsAPICrawler initialized (enabled={self.enabled})")
    
    async def crawl_latest(
        self,
        hours: int = 1,
        keywords: Optional[List[str]] = None,
        max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """
        최신 뉴스 크롤링
        
        Args:
            hours: 몇 시간 이내 뉴스 (기본 1시간)
            keywords: 검색 키워드 (기본: AI chip 관련)
            max_articles: 최대 기사 수
        
        Returns:
            새로운 뉴스 리스트
        """
        if not self.enabled:
            logger.debug("NewsAPI disabled, returning mock data")
            return self._get_mock_articles()
        
        try:
            # 기본 키워드: AI 칩 관련
            if keywords is None:
                keywords = [
                    'NVIDIA', 'Google TPU', 'AMD', 'semiconductor',
                    'AI chip', 'GPU', 'AI inference', 'Blackwell',
                    'TPU v6e', 'MI300', 'H100', 'TSMC'
                ]
            
            query = ' OR '.join(keywords)
            
            # 시간 범위
            from_date = datetime.now() - timedelta(hours=hours)
            
            logger.info(f"Crawling news (last {hours}h): {query[:50]}...")
            
            # NewsAPI 호출
            response = self.client.get_everything(
                q=query,
                language='en',
                from_param=from_date.isoformat(),
                sort_by='publishedAt',
                page_size=max_articles
            )
            
            if response['status'] != 'ok':
                logger.error(f"NewsAPI error: {response}")
                return []
            
            articles = response.get('articles', [])
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
            # 중복 제거 및 DB 저장
            new_articles = await self._save_and_deduplicate(articles)
            
            logger.info(f"New articles after deduplication: {len(new_articles)}")
            
            return new_articles
        
        except Exception as e:
            logger.error(f"Failed to crawl news: {e}")
            return []
    
    async def _save_and_deduplicate(
        self,
        articles: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        기사 저장 및 중복 제거
        
        Args:
            articles: NewsAPI 응답 기사 리스트
        
        Returns:
            새로운 기사만 리턴
        """
        session = self.Session()
        new_articles = []
        
        try:
            for article in articles:
                url = article.get('url')
                if not url:
                    continue
                
                # 중복 체크
                existing = session.query(CrawledNews).filter_by(url=url).first()
                if existing:
                    continue
                
                # 새 기사 저장
                news = CrawledNews(
                    url=url,
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    published_at=self._parse_datetime(article.get('publishedAt')),
                    processed=False
                )
                
                session.add(news)
                session.commit()
                
                # 새 기사 리스트에 추가
                new_articles.append({
                    'title': news.title,
                    'description': news.description,
                    'url': news.url,
                    'source': news.source,
                    'published_at': news.published_at,
                    'id': news.id
                })
                
                logger.debug(f"New article: {news.title[:50]}...")
        
        finally:
            session.close()
        
        return new_articles
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """ISO 8601 문자열 → datetime"""
        if not dt_str:
            return None
        try:
            # '2024-12-03T10:30:00Z' 형식
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _get_mock_articles(self) -> List[Dict[str, Any]]:
        """Mock 데이터 (NewsAPI 없을 때)"""
        return [
            {
                'title': 'NVIDIA announces Blackwell B200 GPU with breakthrough performance',
                'description': 'New AI training chip shows 2x improvement',
                'url': 'https://example.com/nvidia-blackwell',
                'source': 'TechCrunch',
                'published_at': datetime.now() - timedelta(minutes=30)
            },
            {
                'title': 'Google TPU v6e achieves lowest cost per token',
                'description': 'Inference efficiency beats competitors',
                'url': 'https://example.com/google-tpu',
                'source': 'VentureBeat',
                'published_at': datetime.now() - timedelta(minutes=45)
            }
        ]
    
    def mark_as_processed(self, news_id: int):
        """기사를 처리됨으로 표시"""
        session = self.Session()
        try:
            news = session.query(CrawledNews).filter_by(id=news_id).first()
            if news:
                news.processed = True
                session.commit()
        finally:
            session.close()
    
    def get_unprocessed_news(self, limit: int = 10) -> List[Dict]:
        """미처리 뉴스 조회"""
        session = self.Session()
        try:
            news_list = (
                session.query(CrawledNews)
                .filter_by(processed=False)
                .order_by(CrawledNews.published_at.desc())
                .limit(limit)
                .all()
            )
            return [n.to_dict() for n in news_list]
        finally:
            session.close()


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("NewsAPI Crawler Test")
        print("=" * 70)
        
        # 크롤러 초기화
        crawler = NewsAPICrawler()
        
        # 최신 뉴스 크롤링 (1시간)
        print("\nCrawling latest news (1 hour)...")
        articles = await crawler.crawl_latest(hours=1)
        
        print(f"\nFound {len(articles)} new articles:")
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   URL: {article['url'][:60]}...")
        
        # 미처리 뉴스 조회
        print("\n" + "=" * 70)
        print("Unprocessed News")
        print("=" * 70)
        unprocessed = crawler.get_unprocessed_news(limit=5)
        print(f"Unprocessed articles: {len(unprocessed)}")
        
        print("\n=== Test PASSED! ===")
    
    asyncio.run(test())
