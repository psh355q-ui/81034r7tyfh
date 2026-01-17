"""
RSS Crawler Service

Features:
- 실시간 RSS 피드 크롤링 (지연 없음)
- newspaper3k로 본문 전체 추출
- 무제한 요청 (무료)
- 중복 제거 (URL 기반)
"""

import asyncio
import logging
import feedparser
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import time
from urllib.parse import urlparse

# newspaper3k for content extraction
try:
    from newspaper import Article, Config
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    Article = None
    Config = None

from sqlalchemy.orm import Session
# Use PostgreSQL models instead of SQLite
from backend.database.models import NewsArticle, RSSFeed

logger = logging.getLogger(__name__)


# ============================================================================
# Utility Functions
# ============================================================================

def generate_content_hash(title: str, content: str) -> str:
    """
    콘텐츠 해시 생성 (중복 감지용)
    
    제목 + 본문의 처음 1000자로 SHA256 해시 생성
    같은 내용의 다른 URL 기사도 중복으로 감지 가능
    """
    # 제목과 본문 결합 (본문은 첫 1000자만)
    text = f"{title.strip()}\n{content.strip()[:1000]}"
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ============================================================================
# Configuration
# ============================================================================

# Newspaper3k config
if NEWSPAPER_AVAILABLE:
    newspaper_config = Config()
    newspaper_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    newspaper_config.request_timeout = 10
    newspaper_config.fetch_images = False  # 이미지 다운로드 비활성화 (속도 향상)
    newspaper_config.memoize_articles = False


# ============================================================================
# RSS Crawler
# ============================================================================

class RSSCrawler:
    """
    자체 RSS 크롤러
    
    Features:
    - 실시간 뉴스 수집 (지연 없음)
    - 본문 전체 추출 (newspaper3k)
    - 무제한 요청 (무료)
    - 중복 제거 (URL 기반)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            "feeds_processed": 0,
            "articles_found": 0,
            "articles_new": 0,
            "articles_skipped": 0,
            "content_extracted": 0,
            "errors": []
        }
    
    def fetch_feed(self, feed_url: str, feed_name: str = "") -> List[Dict[str, Any]]:
        """RSS 피드 파싱"""
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # 파싱 에러
                self.stats["errors"].append({
                    "feed": feed_name,
                    "error": str(feed.bozo_exception)
                })
            
            articles = []
            for entry in feed.entries[:20]:  # 최신 20개
                # 발행일 파싱
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                else:
                    published = datetime.utcnow()
                
                article = {
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "published_date": published,
                    "source": feed.feed.get("title", feed_name),
                    "feed_source": "rss",
                }
                
                if article["url"]:
                    articles.append(article)
            
            self.stats["articles_found"] += len(articles)
            return articles
            
        except Exception as e:
            self.stats["errors"].append({
                "feed": feed_name,
                "error": str(e)
            })
            return []
    


    def extract_full_content(self, url: str) -> Dict[str, Any]:
        """
        뉴스 본문 전체 추출 (newspaper3k)
        
        Returns:
            {
                "title": str,
                "text": str,  # 전체 본문
                "authors": List[str],
                "publish_date": datetime,
                "top_image": str,
                "keywords": List[str],
                "summary": str  # 자동 요약
            }
        """
        if not NEWSPAPER_AVAILABLE:
            return {"error": "newspaper3k not installed"}
        
        try:
            article = Article(url, config=newspaper_config)
            article.download()
            article.parse()
            
            # NLP 분석 (키워드, 요약)
            try:
                article.nlp()
                keywords = article.keywords[:10] if article.keywords else []
                summary = article.summary if article.summary else ""
            except:
                keywords = []
                summary = ""
            
            self.stats["content_extracted"] += 1
            
            return {
                "title": article.title,
                "content": article.text,  # 전체 본문
                "author": article.authors or [],
                "published_date": article.publish_date,
                "top_image": article.top_image or "",
                "keywords": keywords,
                "summary": summary,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "url": url,
                "text": "",
                "keywords": [],
                "summary": ""
            }
    
    def save_article(self, article_data: Dict[str, Any]) -> Optional[NewsArticle]:
        """기사 DB 저장 (개선된 중복 체크)"""
        url = article_data.get("url", "")
        title = article_data.get("title", "")
        content = article_data.get("content", "")
        
        if not url or not title:
            return None
        
        # 1. URL 중복 체크 (가장 빠름)
        existing = self.db.query(NewsArticle).filter(NewsArticle.url == url).first()
        if existing:
            self.stats["articles_skipped"] += 1
            logger.debug(f"Skipped (URL duplicate): {title[:50]}...")
            return existing
        
        # 2. Content Hash 중복 체크 (내용 기반)
        content_hash = None
        if content and len(content) > 50:  # 본문이 충분히 긴 경우만
            content_hash = generate_content_hash(title, content)
            
            existing_by_hash = self.db.query(NewsArticle).filter(
                NewsArticle.content_hash == content_hash
            ).first()
            
            if existing_by_hash:
                self.stats["articles_skipped"] += 1
                logger.info(f"✓ Skipped (Content duplicate): {title[:50]}... (different URL!)")
                return existing_by_hash
        
        # 3. 새 기사 저장
        news_article = NewsArticle(
            url=url,
            title=title,
            source=article_data.get("source", ""),
            feed_source=article_data.get("feed_source", "rss"),
            published_date=article_data.get("published_date"),
            content=content,
            summary=article_data.get("summary", ""),
            keywords=article_data.get("keywords", []),
            author=article_data.get("author", []),
            top_image=article_data.get("top_image", ""),
            content_hash=content_hash,  # ✅ 해시 저장
        )
        
        self.db.add(news_article)
        self.db.commit()
        self.db.refresh(news_article)
        
        self.stats["articles_new"] += 1
        logger.info(f"✅ New article saved: {title[:50]}...")
        return news_article
    
    def crawl_feed(self, feed: RSSFeed, extract_content: bool = True) -> List[NewsArticle]:
        """단일 피드 크롤링"""
        articles = self.fetch_feed(feed.url, feed.name)
        saved_articles = []
        
        for article_data in articles:
            # 본문 추출
            if extract_content and article_data.get("url"):
                full_content = self.extract_full_content(article_data["url"])
                article_data.update(full_content)
            
            # DB 저장
            saved = self.save_article(article_data)
            if saved and saved.id:
                saved_articles.append(saved)
        
        # 피드 통계 업데이트
        feed.last_fetched = datetime.utcnow()
        feed.total_articles += len(saved_articles)
        self.db.commit()
        
        self.stats["feeds_processed"] += 1
        return saved_articles
    
    def crawl_all_feeds(self, extract_content: bool = True) -> List[NewsArticle]:
        """모든 활성화된 피드 크롤링"""
        feeds = self.db.query(RSSFeed).filter(RSSFeed.enabled == True).all()
        
        all_articles = []
        for feed in feeds:
            print(f"📰 Crawling: {feed.name}...")
            articles = self.crawl_feed(feed, extract_content)
            all_articles.extend(articles)
            time.sleep(0.5)  # Rate limiting (예의)
        
        return all_articles
    
    def crawl_ticker_news(self, ticker: str) -> List[NewsArticle]:
        """특정 티커 관련 뉴스 (Yahoo Finance RSS)"""
        yahoo_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        
        articles = self.fetch_feed(yahoo_url, f"Yahoo Finance - {ticker}")
        saved_articles = []
        
        for article_data in articles:
            full_content = self.extract_full_content(article_data["url"])
            article_data.update(full_content)
            article_data["source"] = f"Yahoo Finance ({ticker})"
            
            saved = self.save_article(article_data)
            if saved:
                saved_articles.append(saved)
        
        return saved_articles
    
    def fetch_all_feeds(self, extract_content: bool = True) -> List[Dict[str, Any]]:
        """
        모든 RSS 피드 크롤링 (DB 저장 안함)
        
        UnifiedNewsProcessor와 함께 사용하기 위한 메서드
        원시 기사 데이터만 반환하고 DB 저장은 하지 않음
        
        Returns:
            List[Dict]: 크롤링된 원시 기사 목록
        """
        feeds = self.db.query(RSSFeed).filter(RSSFeed.enabled == True).all()
        
        all_raw_articles = []
        for feed in feeds:
            logger.info(f"📡 Fetching: {feed.name}...")
            
            # RSS 피드 파싱
            articles = self.fetch_feed(feed.url, feed.name)
            
            # 본문 추출
            for article_data in articles:
                if extract_content and article_data.get("url"):
                    full_content = self.extract_full_content(article_data["url"])
                    article_data.update(full_content)
                
                all_raw_articles.append(article_data)
            
            # 피드 통계 업데이트 (마지막 크롤링 시간만)
            feed.last_fetched = datetime.utcnow()
            self.db.commit()
            
            time.sleep(0.5)  # Rate limiting
            
            self.stats["feeds_processed"] += 1
        
        logger.info(f"✅ Fetched {len(all_raw_articles)} raw articles from {len(feeds)} feeds")
        return all_raw_articles


# ============================================================================
# Utility Functions
# ============================================================================

async def get_recent_articles(
    db: Session,
    limit: int = 50,
    hours: int = 24,
    source: Optional[str] = None
) -> List[NewsArticle]:
    """
    최근 기사 조회 (비동기)

    AsyncSession을 사용하므로 select() 문법 사용
    """
    from sqlalchemy import select, func

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # select() 문법으로 쿼리 생성
    stmt = select(NewsArticle).filter(NewsArticle.published_date >= cutoff)

    if source:
        stmt = stmt.filter(NewsArticle.source.ilike(f"%{source}%"))

    stmt = stmt.order_by(NewsArticle.published_date.desc()).limit(limit)

    # 비동기 실행
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_unanalyzed_articles(db: Session, limit: int = 100) -> List[NewsArticle]:
    """
    분석되지 않은 기사 조회 (비동기)

    AsyncSession을 사용하므로 select() 문법 사용
    """
    from sqlalchemy import select

    stmt = (
        select(NewsArticle)
        .outerjoin(NewsArticle.analysis)
        .filter(NewsArticle.analysis == None)
        .filter(NewsArticle.content != None)
        .filter(NewsArticle.content != "")
        .order_by(NewsArticle.published_date.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_feed_stats(db: Session) -> List[Dict[str, Any]]:
    """
    피드별 통계 (비동기)

    AsyncSession을 사용하므로 select() 문법 사용
    """
    from sqlalchemy import select

    stmt = select(RSSFeed)
    result = await db.execute(stmt)
    feeds = result.scalars().all()

    return [
        {
            "id": f.id,
            "name": f.name,
            "url": f.url,
            "category": f.category,
            "enabled": f.enabled,
            "last_fetched": f.last_fetched.isoformat() if f.last_fetched else None,
            "total_articles": f.total_articles,
            "error_count": f.error_count,
        }
        for f in feeds
    ]


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    print("🚀 RSS Crawler Test")
    
    # Initialize DB
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create crawler
        crawler = RSSCrawler(db)
        
        # Crawl all feeds
        print("\n📡 Crawling all RSS feeds...")
        result = crawler.crawl_all_feeds(extract_content=True)
        
        print(f"\n✅ Crawling Complete!")
        print(f"  Feeds processed: {result['stats']['feeds_processed']}")
        print(f"  Articles found: {result['stats']['articles_found']}")
        print(f"  New articles: {result['stats']['articles_new']}")
        print(f"  Skipped (duplicate): {result['stats']['articles_skipped']}")
        print(f"  Content extracted: {result['stats']['content_extracted']}")
        
        if result['stats']['errors']:
            print(f"\n⚠️ Errors:")
            for err in result['stats']['errors']:
                print(f"  - {err['feed']}: {err['error']}")
        
        # Show recent articles
        print("\n📰 Recent Articles:")
        recent = get_recent_articles(db, limit=5)
        for article in recent:
            print(f"  - {article.title[:60]}...")
            print(f"    Source: {article.source}")
            print(f"    Content: {len(article.content_text or '')} chars")
            print()
        
    finally:
        db.close()
