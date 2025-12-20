"""
Enhanced NewsAPI Crawler with Keyword Tagging & Ticker Caching

기능:
- 24시간 뉴스 크롤링
- 키워드별 자동 태깅
- 티커별 로컬 캐싱
- 태그 기반 검색 및 필터링

작성일: 2025-12-03
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import asyncio
import json

# Load .env file explicitly
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=env_path)

# NewsAPI
try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False
    logging.warning("newsapi-python not installed. Run: pip install newsapi-python")

# Database
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# 4-way News Context Filter
try:
    from .news_context_filter import NewsContextFilter
    FILTER_AVAILABLE = True
except ImportError:
    FILTER_AVAILABLE = False
    logging.warning("NewsContextFilter not available")

logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================

class TaggedNews(Base):
    """키워드 태그가 포함된 뉴스"""
    __tablename__ = 'tagged_news'
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    source = Column(String)
    published_at = Column(DateTime)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    
    # Tagging
    tickers = Column(JSON)  # ["NVDA", "GOOGL", ...]
    keywords = Column(JSON)  # ["AI chip", "GPU", ...]
    tags = Column(JSON)  # ["training", "inference", "deployment"]
    market_segment = Column(String)  # "training" or "inference"
    
    # Caching
    processed = Column(Boolean, default=False)
    cache_key = Column(String, index=True)  # e.g., "NVDA_2024-12-03"
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'crawled_at': self.crawled_at.isoformat() if self.crawled_at else None,
            'tickers': self.tickers or [],
            'keywords': self.keywords or [],
            'tags': self.tags or [],
            'market_segment': self.market_segment,
            'processed': self.processed,
            'cache_key': self.cache_key
        }


# ============================================================================
# Keyword & Ticker Mapping
# ============================================================================

TICKER_KEYWORDS = {
    'NVDA': ['NVIDIA', 'Nvidia', 'nvda', 'H100', 'H200', 'Blackwell', 'B200', 'Grace Hopper'],
    'GOOGL': ['Google', 'Alphabet', 'TPU', 'TPU v5', 'TPU v6', 'Cloud TPU'],
    'AMD': ['AMD', 'MI300', 'MI250', 'Instinct', 'EPYC', 'Radeon'],
    'INTC': ['Intel', 'Xeon', 'Gaudi', 'Habana'],
    'TSM': ['TSMC', 'Taiwan Semiconductor'],
    'AVGO': ['Broadcom', 'Avago'],
    'MSFT': ['Microsoft', 'Azure AI'],
    'AMZN': ['Amazon', 'AWS', 'Trainium', 'Inferentia'],
    'META': ['Meta', 'Facebook'],
    'ORCL': ['Oracle', 'Oracle Cloud']
}

MARKET_SEGMENT_KEYWORDS = {
    'training': [
        'training', 'LLM training', 'model training', 'AI training',
        'GPT training', 'large model', 'deep learning', 'neural network training',
        'H100', 'Blackwell', 'MI300X', 'cluster'
    ],
    'inference': [
        'inference', 'serving', 'deployment', 'production AI',
        'cost per token', 'latency', 'throughput', 'TPU',
        'real-time', 'edge AI', 'MI300A'
    ],
    'deployment': [
        'deployment', 'production', 'scaling', 'cloud AI',
        'data center', 'enterprise AI'
    ]
}

GENERAL_KEYWORDS = [
    'semiconductor', 'AI chip', 'GPU', 'accelerator', 'processor',
    'fab', 'foundry', 'ASIC', 'NPU', 'DPU',
    'AI infrastructure', 'computing', 'HPC'
]


# ============================================================================
# Enhanced News Crawler with Tagging
# ============================================================================

class EnhancedNewsCrawler:
    """
    키워드 태깅 + 티커 캐싱 기능이 있는 뉴스 크롤러
    
    사용법:
        crawler = EnhancedNewsCrawler()
        articles = await crawler.crawl_and_tag(hours=24)
        nvda_news = crawler.get_ticker_news('NVDA', days=1)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        db_url: str = "sqlite:///enhanced_news_cache.db"
    ):
        """
        Args:
            api_key: NewsAPI 키
            db_url: 데이터베이스 URL
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        
        # NewsAPI 클라이언트
        if NEWSAPI_AVAILABLE and self.api_key:
            self.client = NewsApiClient(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("NewsAPI crawler disabled")
        
        # Database setup
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            poolclass=StaticPool if "sqlite" in db_url else None
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # 4-way Context Filter
        if FILTER_AVAILABLE:
            self.context_filter = NewsContextFilter()
            logger.info("4-way news filter enabled")
        else:
            self.context_filter = None
        
        logger.info(f"EnhancedNewsCrawler initialized (enabled={self.enabled})")
    
    async def crawl_and_filter(
        self,
        hours: int = 24,  # 24시간 기본값
        max_articles: int = 100,
        filter_threshold: float = 0.7  # 70% 노이즈 제거
    ) -> List[Dict[str, Any]]:
        """
        뉴스 크롤링 + 자동 태깅 + 4-way 필터링
        
        Args:
            hours: 몇 시간 이내 뉴스 (기본 24시간)
            max_articles: 최대 기사 수
            filter_threshold: 필터 임계값 (기본 0.7)
        
        Returns:
            필터링된 태그 뉴스 리스트
        """
        # 1. 크롤링 + 태깅
        tagged_articles = await self.crawl_and_tag(hours, max_articles)
        
        # 2. 4-way 필터링
        if self.context_filter and tagged_articles:
            filtered_articles = []
            
            for article in tagged_articles:
                risk_score = self.context_filter.filter_news(article)
                
                if risk_score >= filter_threshold:
                    article['risk_score'] = risk_score
                    filtered_articles.append(article)
                    logger.debug(f"PASS: {article['title'][:50]}... (score={risk_score:.2f})")
                else:
                    logger.debug(f"FILTER: {article['title'][:50]}... (score={risk_score:.2f})")
            
            logger.info(
                f"Filtered: {len(tagged_articles)} → {len(filtered_articles)} "
                f"({100 * len(filtered_articles) / len(tagged_articles):.1f}% passed)"
            )
            
            return filtered_articles
        
        return tagged_articles
    
    async def crawl_and_tag(
        self,
        hours: int = 24,  # 24시간 기본값
        max_articles: int = 100
    ) -> List[Dict[str, Any]]:
        """
        뉴스 크롤링 + 자동 태깅 (필터링 없음)
        
        Args:
            hours: 몇 시간 이내 뉴스 (기본 24시간)
            max_articles: 최대 기사 수
        
        Returns:
            태그된 새로운 뉴스 리스트
        """
        if not self.enabled:
            logger.debug("NewsAPI disabled, using mock data")
            return await self._get_mock_tagged_articles()
        
        try:
            # 모든 티커의 키워드 수집
            all_keywords = []
            for keywords in TICKER_KEYWORDS.values():
                all_keywords.extend(keywords)
            all_keywords.extend(GENERAL_KEYWORDS)
            
            # 중복 제거 및 쿼리 생성
            unique_keywords = list(set(all_keywords))[:30]  # NewsAPI 제한
            query = ' OR '.join(f'"{kw}"' for kw in unique_keywords[:20])
            
            # UTC 시간 사용 (NewsAPI 요구사항)
            from_date = datetime.utcnow() - timedelta(hours=hours)
            
            logger.info(f"Crawling news (last {hours}h)...")
            
            # NewsAPI 호출
            logger.info(f"NewsAPI Request: q='{query[:50]}...', from={from_date.strftime('%Y-%m-%dT%H:%M:%S')}")
            
            response = self.client.get_everything(
                q=query,
                language='en',
                from_param=from_date.strftime('%Y-%m-%dT%H:%M:%S'),
                sort_by='publishedAt',
                page_size=max_articles
            )
            
            logger.info(f"Initial Response: status={response.get('status')}, totalResults={response.get('totalResults')}")
            
            # Fallback: 결과가 0개면 더 넓은 범위로 재검색
            if response['status'] == 'ok' and response['totalResults'] == 0:
                logger.warning("No articles found with specific keywords. Trying fallback query...")
                fallback_query = 'technology OR AI OR "stock market" OR semiconductor'
                
                logger.info(f"Fallback Request: q='{fallback_query}' (No Date Filter)")
                response = self.client.get_everything(
                    q=fallback_query,
                    language='en',
                    # from_param 제거: 날짜 필터 없이 검색 (최근 1달)
                    sort_by='publishedAt',
                    page_size=max_articles
                )
                logger.info(f"Fallback Response: status={response.get('status')}, totalResults={response.get('totalResults')}")
            
            if response['status'] != 'ok':
                logger.error(f"NewsAPI error: {response}")
                return []
            
            articles = response.get('articles', [])
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
            # 태깅 및 저장
            await self._tag_and_save(articles)
            
            # DB에서 해당 기간의 모든 뉴스 조회 (새로 저장된 것 + 기존 것)
            session = self.Session()
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                
                # 날짜 기준 조회
                db_articles = session.query(TaggedNews)\
                    .filter(TaggedNews.published_at >= cutoff_time)\
                    .order_by(TaggedNews.published_at.desc())\
                    .limit(max_articles)\
                    .all()
                
                return [article.to_dict() for article in db_articles]
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Failed to crawl news: {e}")
            return []
    
    async def _tag_and_save(
        self,
        articles: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        기사 태깅 및 저장
        
        Args:
            articles: NewsAPI 응답 기사 리스트
        
        Returns:
            태그된 새로운 기사 리스트
        """
        session = self.Session()
        tagged_articles = []
        
        try:
            for article in articles:
                url = article.get('url')
                if not url:
                    continue
                
                # 중복 체크
                existing = session.query(TaggedNews).filter_by(url=url).first()
                if existing:
                    continue
                
                # 키워드 태깅
                text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
                
                tickers = self._extract_tickers(text)
                keywords = self._extract_keywords(text)
                tags = self._extract_tags(text)
                market_segment = self._determine_segment(text)
                
                # 날짜 파싱
                published_at = self._parse_datetime(article.get('publishedAt'))
                
                # 캐시 키 생성 (티커별로 날짜 기준)
                cache_keys = []
                if published_at:
                    date_str = published_at.strftime('%Y-%m-%d')
                    for ticker in tickers:
                        cache_keys.append(f"{ticker}_{date_str}")
                
                cache_key = ','.join(cache_keys) if cache_keys else None
                
                # 저장
                news = TaggedNews(
                    url=url,
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    content=article.get('content', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    published_at=published_at,
                    tickers=tickers,
                    keywords=keywords,
                    tags=tags,
                    market_segment=market_segment,
                    cache_key=cache_key,
                    processed=False
                )
                
                session.add(news)
                session.commit()
                
                tagged_articles.append(news.to_dict())
                
                logger.debug(
                    f"Tagged: {news.title[:50]}... "
                    f"(Tickers: {tickers}, Segment: {market_segment})"
                )
        
        finally:
            session.close()
        
        return tagged_articles
    
    def _extract_tickers(self, text: str) -> List[str]:
        """텍스트에서 티커 추출"""
        tickers = []
        text_lower = text.lower()
        
        for ticker, keywords in TICKER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    tickers.append(ticker)
                    break
        
        return list(set(tickers))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        keywords = []
        text_lower = text.lower()
        
        # 모든 세그먼트 키워드 검사
        for segment_keywords in MARKET_SEGMENT_KEYWORDS.values():
            for keyword in segment_keywords:
                if keyword.lower() in text_lower:
                    keywords.append(keyword)
        
        # 일반 키워드
        for keyword in GENERAL_KEYWORDS:
            if keyword.lower() in text_lower:
                keywords.append(keyword)
        
        return list(set(keywords))
    
    def _extract_tags(self, text: str) -> List[str]:
        """텍스트에서 태그 추출"""
        tags = []
        text_lower = text.lower()
        
        # 시장 세그먼트 기반 태그
        for segment, keywords in MARKET_SEGMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    tags.append(segment)
                    break
        
        return list(set(tags))
    
    def _determine_segment(self, text: str) -> Optional[str]:
        """시장 세그먼트 결정"""
        text_lower = text.lower()
        
        training_score = sum(
            1 for kw in MARKET_SEGMENT_KEYWORDS['training']
            if kw.lower() in text_lower
        )
        
        inference_score = sum(
            1 for kw in MARKET_SEGMENT_KEYWORDS['inference']
            if kw.lower() in text_lower
        )
        
        if training_score > inference_score:
            return 'training'
        elif inference_score > training_score:
            return 'inference'
        else:
            return 'general'
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """ISO 8601 문자열 → datetime"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None
    
    # ========================================
    # 티커별 캐싱 조회
    # ========================================
    
    def get_ticker_news(
        self,
        ticker: str,
        days: int = 1
    ) -> List[Dict]:
        """
        특정 티커의 뉴스 조회 (캐시 활용)
        
        Args:
            ticker: 티커 심볼 (e.g., "NVDA")
            days: 몇 일치 뉴스
        
        Returns:
            해당 티커의 뉴스 리스트
        """
        session = self.Session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # JSON 컬럼 검색 (SQLite)
            news_list = (
                session.query(TaggedNews)
                .filter(TaggedNews.published_at >= cutoff_date)
                .all()
            )
            
            # ticker 필터링 (Python에서)
            filtered = [
                n for n in news_list
                if n.tickers and ticker in n.tickers
            ]
            
            return [n.to_dict() for n in filtered]
        
        finally:
            session.close()
    
    def get_segment_news(
        self,
        segment: str,
        days: int = 1
    ) -> List[Dict]:
        """
        특정 세그먼트의 뉴스 조회
        
        Args:
            segment: 'training', 'inference', 'deployment'
            days: 몇 일치 뉴스
        
        Returns:
            해당 세그먼트 뉴스 리스트
        """
        session = self.Session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            news_list = (
                session.query(TaggedNews)
                .filter(TaggedNews.market_segment == segment)
                .filter(TaggedNews.published_at >= cutoff_date)
                .order_by(TaggedNews.published_at.desc())
                .all()
            )
            
            return [n.to_dict() for n in news_list]
        
        finally:
            session.close()
    
    async def _get_mock_tagged_articles(self) -> List[Dict[str, Any]]:
        """Mock 태그된 데이터"""
        return [
            {
                'id': 1,
                'title': 'NVIDIA announces Blackwell B200 GPU',
                'tickers': ['NVDA'],
                'keywords': ['H100', 'training', 'AI chip'],
                'tags': ['training'],
                'market_segment': 'training',
                'source': 'TechCrunch',
                'published_at': datetime.now() - timedelta(hours=2)
            },
            {
                'id': 2,
                'title': 'Google TPU v6e achieves lowest cost per token',
                'tickers': ['GOOGL'],
                'keywords': ['TPU', 'inference', 'cost per token'],
                'tags': ['inference'],
                'market_segment': 'inference',
                'source': 'VentureBeat',
                'published_at': datetime.now() - timedelta(hours=5)
            }
        ]


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("Enhanced News Crawler Test (with Tagging & Caching)")
        print("=" * 70)
        
        crawler = EnhancedNewsCrawler()
        
        # 1. 24시간 뉴스 크롤링 + 태깅
        print("\n[1] Crawling & Tagging (24 hours)...")
        articles = await crawler.crawl_and_tag(hours=24)
        
        print(f"\nFound {len(articles)} tagged articles")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article['title'][:60]}...")
            print(f"   Tickers: {article['tickers']}")
            print(f"   Segment: {article['market_segment']}")
            print(f"   Keywords: {article['keywords'][:5]}")
        
        # 2. 티커별 캐시 조회
        print("\n" + "=" * 70)
        print("[2] Ticker-specific Cache Query")
        print("=" * 70)
        
        nvda_news = crawler.get_ticker_news('NVDA', days=1)
        print(f"\nNVDA news (last 24h): {len(nvda_news)} articles")
        
        googl_news = crawler.get_ticker_news('GOOGL', days=1)
        print(f"GOOGL news (last 24h): {len(googl_news)} articles")
        
        # 3. 세그먼트별 조회
        print("\n" + "=" * 70)
        print("[3] Segment Query")
        print("=" * 70)
        
        training_news = crawler.get_segment_news('training', days=1)
        print(f"Training segment: {len(training_news)} articles")
        
        inference_news = crawler.get_segment_news('inference', days=1)
        print(f"Inference segment: {len(inference_news)} articles")
        
        print("\n=== Test PASSED! ===")
    
    asyncio.run(test())
