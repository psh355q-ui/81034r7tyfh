"""
News Database Models

SQLite + SQLAlchemy for local storage
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pathlib import Path

# Docker 컨테이너 호환 경로 - 프로젝트 루트 기준 data 디렉토리 사용
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "news.db"
try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # 윈도우/권한문제시 임시폴더 사용 (Fallback)
    print(f"Warning: Could not create DB at {DB_PATH}, falling back to /tmp/news.db. Error: {e}")
    DB_PATH = Path("/tmp/news.db")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# Models
# ============================================================================

class NewsArticle(Base):
    """뉴스 기사"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    source = Column(String(128))
    feed_source = Column(String(64))  # 'rss' | 'newsapi'
    published_date = Column(DateTime)
    
    # Content
    content = Column(Text)  # 전체 본문
    summary = Column(Text)  # 자동 요약
    keywords = Column(JSON)  # 키워드 리스트
    
    # Metadata
    author = Column(JSON) # JSON으로 유지하되 이름은 author로 통일 (Postgres와 호환성 고려)
    top_image = Column(String(2048))
    content_hash = Column(String(64), index=True) # Added for compatibility
    
    # NLP & Embedding Fields (Added for compatibility with Postgres model)
    embedding = Column(JSON) # Stored as JSON list in SQLite
    tags = Column(JSON)      # Stored as JSON list
    tickers = Column(JSON)   # Stored as JSON list
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    source_category = Column(String(50))
    metadata_ = Column("metadata", JSON)
    processed_at = Column(DateTime)
    embedding_model = Column(String(100))
    
    # Timestamps
    crawled_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status flags (Phase 20 Week 3)
    has_tags = Column(Boolean, default=False, nullable=False)
    has_embedding = Column(Boolean, default=False, nullable=False)
    rag_indexed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    analysis = relationship("NewsAnalysis", back_populates="article", uselist=False)
    ticker_relevances = relationship("NewsTickerRelevance", back_populates="article")
    
    # Indexes
    __table_args__ = (
        Index('idx_published_at', 'published_date'),
        Index('idx_source', 'source'),
        Index('idx_feed_source', 'feed_source'),
    )


class NewsAnalysis(Base):
    """AI 분석 결과"""
    __tablename__ = "news_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), unique=True)
    
    # Sentiment
    sentiment_overall = Column(String(32))  # positive | negative | neutral | mixed
    sentiment_score = Column(Float)  # -1.0 ~ 1.0
    sentiment_confidence = Column(Float)  # 0.0 ~ 1.0
    
    # Tone Analysis
    tone_objective_score = Column(Float)  # 0.0 (객관) ~ 1.0 (주관)
    urgency = Column(String(32))  # low | medium | high | critical
    sensationalism = Column(Float)  # 0.0 ~ 1.0
    
    # Market Impact
    market_impact_short = Column(String(32))  # bullish | bearish | neutral | uncertain
    market_impact_long = Column(String(32))
    impact_magnitude = Column(Float)  # 0.0 ~ 1.0
    affected_sectors = Column(JSON)  # List[str]
    
    # Key Findings
    key_facts = Column(JSON)  # List[str]
    key_opinions = Column(JSON)  # List[str]
    key_implications = Column(JSON)  # List[str]
    key_warnings = Column(JSON)  # List[str]
    
    # Indirect Expressions
    indirect_expressions = Column(JSON)  # List[dict]
    red_flags = Column(JSON)  # List[str]
    
    # Trading Relevance
    trading_actionable = Column(Boolean, default=False)
    risk_category = Column(String(64))  # legal | regulatory | operational | financial | strategic | none
    recommendation = Column(Text)
    
    # Credibility
    source_reliability = Column(Float)  # 0.0 ~ 1.0
    data_backed = Column(Boolean)
    multiple_sources_cited = Column(Boolean)
    potential_bias = Column(String(256))
    
    # Model Info
    model_used = Column(String(64))
    tokens_used = Column(Integer)
    analysis_cost = Column(Float, default=0.0)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    article = relationship("NewsArticle", back_populates="analysis")
    
    __table_args__ = (
        Index('idx_sentiment_overall', 'sentiment_overall'),
        Index('idx_trading_actionable', 'trading_actionable'),
        Index('idx_risk_category', 'risk_category'),
    )


class NewsTickerRelevance(Base):
    """뉴스-티커 연관성"""
    __tablename__ = "news_ticker_relevance"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"))
    ticker = Column(String(16), nullable=False, index=True)
    
    relevance_score = Column(Float)  # 0.0 ~ 1.0
    sentiment_for_ticker = Column(Float)  # -1.0 ~ 1.0
    mention_count = Column(Integer, default=1)
    
    # Relationship
    article = relationship("NewsArticle", back_populates="ticker_relevances")
    
    __table_args__ = (
        Index('idx_ticker', 'ticker'),
        Index('idx_relevance', 'relevance_score'),
    )


class RSSFeed(Base):
    """RSS 피드 설정"""
    __tablename__ = "rss_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    url = Column(String(2048), nullable=False)
    category = Column(String(64))  # global | korea | sector_specific
    enabled = Column(Boolean, default=True)
    
    # Stats
    last_fetched = Column(DateTime)
    total_articles = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Initialize Database
# ============================================================================

def init_db():
    """데이터베이스 초기화"""
    Base.metadata.create_all(bind=engine)
    
    # 기본 RSS 피드 추가
    session = SessionLocal()
    try:
        existing_feeds = session.query(RSSFeed).count()
        if existing_feeds == 0:
            default_feeds = [
                # Global
                RSSFeed(name="CNBC Top News", url="https://www.cnbc.com/id/100003114/device/rss/rss.html", category="global"),
                RSSFeed(name="MarketWatch", url="https://feeds.marketwatch.com/marketwatch/topstories/", category="global"),
                RSSFeed(name="Seeking Alpha", url="https://seekingalpha.com/feed.xml", category="global"),
                RSSFeed(name="Investing.com", url="https://www.investing.com/rss/news.rss", category="global"),
                
                # Korea
                RSSFeed(name="연합뉴스 경제", url="https://www.yna.co.kr/rss/economy.xml", category="korea"),
                RSSFeed(name="한국경제", url="https://www.hankyung.com/feed/all-news", category="korea"),
                RSSFeed(name="매일경제", url="https://www.mk.co.kr/rss/30000001/", category="korea"),
            ]
            
            for feed in default_feeds:
                session.add(feed)
            
            session.commit()
            print(f"[OK] Added {len(default_feeds)} default RSS feeds")
    finally:
        session.close()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize on import
if __name__ == "__main__":
    init_db()
    print(f"✅ Database initialized at {DB_PATH}")
