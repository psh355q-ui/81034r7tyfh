"""
RSS Crawler Service

Features:
- 실시간 RSS 피드 크롤링 (지연 없음)
- newspaper3k로 본문 전체 추출
- 무제한 요청 (무료)
- 중복 제거 (URL 기반)
- Storage: PostgreSQL (via NewsRepository)
"""

import asyncio
import feedparser
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import time
import logging
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
from sqlalchemy import text
from backend.database.repository import get_sync_session, NewsRepository, NewsArticle
from backend.database.models import RSSFeed  # Now in main models

logger = logging.getLogger(__name__)

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
    자체 RSS 크롤러 (PostgreSQL Integration)
    
    Features:
    - 실시간 뉴스 수집 (지연 없음)
    - 본문 전체 추출 (newspaper3k)
    - 무제한 요청 (무료)
    - 중복 제거 (URL 기반)
    """
    
    def __init__(self, db: Session = None):
        # Allow passing session, otherwise create new one
        self.db = db if db else get_sync_session()
        self.repo = NewsRepository(self.db)
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
                    "published_at": published,
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
                "text": article.text,  # 전체 본문
                "authors": article.authors or [],
                "publish_date": article.publish_date,
                "top_image": article.top_image or "",
                "keywords": keywords,
                "summary": summary,
            }
            
        except Exception as e:
            # logger.warning(f"Failed to extract content from {url}: {e}") # Reduce noise
            return {
                "error": str(e),
                "url": url,
                "text": "",
                "keywords": [],
                "summary": ""
            }
    
    def save_article(self, article_data: Dict[str, Any]) -> Optional[NewsArticle]:
        """기사 DB 저장 (중복 체크)"""
        url = article_data.get("url", "")
        if not url:
            return None
        
        # 중복 체크 via Repository
        if self.repo.get_article_by_url(url):
            self.stats["articles_skipped"] += 1
            return None
        
        # 새 기사 저장
        try:
            # NewsRepository expects a dict for save_processed_article
            # Map keys to match schema expected by repository if needed
            
            # Repository save_processed_article handles:
            # url, title, content, source, published_at, summary, keywords (tags), metadata
            
            save_data = {
                'url': url,
                'title': article_data.get("title", ""),
                'content': article_data.get("text", "") or article_data.get("summary", ""),
                'source': article_data.get("source", "RSS"),
                'published_at': article_data.get("published_at") or datetime.utcnow(),
                'summary': article_data.get("summary", ""),
                'tags': article_data.get("keywords", []),
                # Metadata for extra fields
                'metadata': {
                    'feed_source': article_data.get("feed_source", "rss"),
                    'authors': article_data.get("authors", []),
                    'top_image': article_data.get("top_image", "")
                }
            }
            
            saved = self.repo.save_processed_article(save_data)
            # Commit handled by repo generally or here? 
            # save_processed_article usually commits. 
            # If we want batch commit we might need different method, 
            # but for RSS crawling article by article is safer.
            
            self.stats["articles_new"] += 1
            return saved
        except Exception as e:
            logger.error(f"Failed to save article {url}: {e}")
            return None
    
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
            if saved:
                saved_articles.append(saved)
        
        # 피드 통계 업데이트
        try:
            feed.last_fetched = datetime.utcnow()
            feed.total_articles = (feed.total_articles or 0) + len(saved_articles)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update feed stats: {e}")
        
        self.stats["feeds_processed"] += 1
        return saved_articles
    
    def crawl_all_feeds(self, extract_content: bool = True) -> Dict[str, Any]:
        """모든 활성화된 피드 크롤링"""
        try:
            feeds = self.db.query(RSSFeed).filter(RSSFeed.enabled == True).all()
            
            # If no feeds, initialize defaults
            if not feeds:
                self.init_default_feeds()
                feeds = self.db.query(RSSFeed).filter(RSSFeed.enabled == True).all()

            all_articles = []
            for feed in feeds:
                print(f"📰 Crawling: {feed.name}...")
                articles = self.crawl_feed(feed, extract_content)
                all_articles.extend(articles)
                time.sleep(0.5)  # Rate limiting (예의)
            
            return {
                "total_articles": len(all_articles),
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Crawl all feeds failed: {e}")
            return {"error": str(e), "stats": self.stats}

    def init_default_feeds(self):
        """기본 RSS 피드 초기화"""
        default_feeds = [
            RSSFeed(name="CNBC Top News", url="https://www.cnbc.com/id/100003114/device/rss/rss.html", category="global"),
            RSSFeed(name="MarketWatch", url="https://feeds.marketwatch.com/marketwatch/topstories/", category="global"),
            RSSFeed(name="Seeking Alpha", url="https://seekingalpha.com/feed.xml", category="global"),
            RSSFeed(name="Investing.com", url="https://www.investing.com/rss/news.rss", category="global"),
            RSSFeed(name="연합뉴스 경제", url="https://www.yna.co.kr/rss/economy.xml", category="korea"),
            RSSFeed(name="한국경제", url="https://www.hankyung.com/feed/all-news", category="korea"),
            RSSFeed(name="매일경제", url="https://www.mk.co.kr/rss/30000001/", category="korea"),
        ]
        
        try:
            for feed in default_feeds:
                # Check exist
                exists = self.db.query(RSSFeed).filter(RSSFeed.name == feed.name).first()
                if not exists:
                    self.db.add(feed)
            self.db.commit()
            print(f"[OK] Added default RSS feeds")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to init default feeds: {e}")
    
    def crawl_ticker_news(self, ticker: str) -> List[NewsArticle]:
        """특정 티커 관련 뉴스 (Yahoo Finance RSS)"""
        yahoo_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        
        articles = self.fetch_feed(yahoo_url, f"Yahoo Finance - {ticker}")
        saved_articles = []
        
        for article_data in articles:
            full_content = self.extract_full_content(article_data["url"])
            article_data.update(full_content)
            article_data["source"] = f"Yahoo Finance ({ticker})"
            # Add ticker tag
            keywords = article_data.get("keywords", [])
            if ticker not in keywords:
                keywords.append(ticker)
            article_data["keywords"] = keywords
            
            saved = self.save_article(article_data)
            if saved:
                saved_articles.append(saved)
        
        return saved_articles


# ============================================================================
# Utility Functions
# ============================================================================

def get_recent_articles(
    limit: int = 50,
    hours: int = 24,
    source: Optional[str] = None
) -> List[NewsArticle]:
    """최근 기사 조회"""
    session = get_sync_session()
    repo = NewsRepository(session)
    try:
        # Use repo method
        return repo.get_latest_news(limit=limit)
    finally:
        session.close()


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    print("🚀 RSS Crawler Test (PostgreSQL)")
    
    crawler = RSSCrawler()
    
    try:
        # Crawl all feeds
        print("\n📡 Crawling all RSS feeds...")
        result = crawler.crawl_all_feeds(extract_content=True)
        
        print(f"\n✅ Crawling Complete!")
        print(f"  Feeds processed: {result['stats']['feeds_processed']}")
        print(f"  Articles found: {result['stats']['articles_found']}")
        print(f"  New articles: {result['stats']['articles_new']}")
        print(f"  Skipped (duplicate): {result['stats']['articles_skipped']}")
        print(f"  Content extracted: {result['stats']['content_extracted']}")
        
    finally:
        # Close session if it was created internally
        if hasattr(crawler, 'db'):
            crawler.db.close()
