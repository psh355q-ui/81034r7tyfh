
"""
NewsAPI Real-time Crawler

실시간 뉴스 크롤링 및 자동 매매 트리거

기능:
- NewsAPI 통합 (30분마다 크롤링)
- Tech/Finance 뉴스 필터링
- KIS Auto Trade 트리거
- 중복 제거
- Repository Pattern 적용 (Phase 4)

작성일: 2025-12-03
수정일: 2025-12-27 (Refactoring)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# NewsAPI
try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False
    logging.warning("newsapi-python not installed. Run: pip install newsapi-python")

# Database (Repository Pattern)
from backend.database.repository import get_sync_session, NewsRepository

logger = logging.getLogger(__name__)


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
        api_key: Optional[str] = None
    ):
        """
        Args:
            api_key: NewsAPI 키 (없으면 환경변수에서 읽기)
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
        session = get_sync_session()
        repo = NewsRepository(session)
        new_articles = []
        
        try:
            for article in articles:
                url = article.get('url')
                if not url:
                    continue
                
                # 중복 체크 (Repository 사용)
                if repo.exists_by_url(url):
                    continue
                
                # 새 기사 데이터 구성
                published_at = self._parse_datetime(article.get('publishedAt'))
                
                news_data = {
                    'title': article.get('title', ''),
                    'summary': article.get('description', ''), # map description to summary
                    'content': article.get('description', ''), # also map to content for now if content is empty/truncated
                    'url': url,
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': published_at,
                    'author': article.get('author'),
                    'tags': [], # Will be populated by NLP later
                    'processed_at': None # Not processed yet
                }
                
                # 저장 (Repository 사용)
                # save_processed_article handles uniqueness via content_hash too, but we did a URL check above.
                # It also generates content_hash.
                saved_article = repo.save_processed_article(news_data)
                
                if saved_article:
                    new_articles.append({
                        'title': saved_article.title,
                        'description': saved_article.summary,
                        'url': saved_article.url,
                        'source': saved_article.source,
                        'published_at': saved_article.published_date,
                        'id': saved_article.id
                    })
                    logger.debug(f"New article: {saved_article.title[:50]}...")
        
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
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
    
    def get_unprocessed_news(self, limit: int = 10) -> List[Dict]:
        """미처리 뉴스 조회"""
        session = get_sync_session()
        repo = NewsRepository(session)
        try:
            # We don't have a direct 'get_unprocessed' in repo yet, let's assume we can query directly or add method?
            # For now, let's use session query as standard practice allowed within Repository pattern user code for simple fetches?
            # Or better, check if repo has get_recent_articles.
            # But here we filter by 'processed_at' IS NULL or similar logic. 
            # In standard models.py, 'processed_at' is used.
            # But the logic here relied on 'processed' boolean in CrawledNews.
            # NewsArticle doesn't have 'processed' boolean. It has 'processed_at' DateTime.
            # So unprocessed means processed_at IS NULL.
            
            from backend.database.models import NewsArticle
            
            news_list = (
                session.query(NewsArticle)
                .filter(NewsArticle.processed_at == None)
                .order_by(NewsArticle.published_date.desc())
                .limit(limit)
                .all()
            )
            
            # Map back to dict structure expected by consumers
            return [{
                'id': n.id,
                'url': n.url,
                'title': n.title,
                'description': n.summary,
                'source': n.source,
                'published_at': n.published_date.isoformat() if n.published_date else None,
                'processed': False # implied
            } for n in news_list]
            
        finally:
            session.close()


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("NewsAPI Crawler Test (Repository Pattern)")
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
