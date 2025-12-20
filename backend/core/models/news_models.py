"""
News Article Models for PostgreSQL

Migrates from SQLite to PostgreSQL for unified data management.
Includes support for:
- News articles storage
- RSS source management
- Auto-tagging with ticker/sector
- Embedding integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, Index, Float
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func

from backend.core.database import Base


class NewsArticle(Base):
    """
    News article storage.
    
    Migrated from SQLite news.db for unified management.
    """
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core fields
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary
    url = Column(String(2048), unique=True, nullable=False, index=True)
    source = Column(String(255), index=True)  # Reuters, Bloomberg, etc.
    
    # Timestamps
    published_at = Column(TIMESTAMP(timezone=True), index=True)
    crawled_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Auto-tagging
    tickers = Column(ARRAY(String(20)), default=[])  # ["AAPL", "MSFT"]
    sectors = Column(ARRAY(String(50)), default=[])  # ["Technology", "Healthcare"]
    
    # Sentiment analysis
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1.0 to 1.0
    
    # Event classification
    event_type = Column(String(50))  # earnings, merger, dividend, lawsuit, etc.
    importance = Column(Integer, default=1)  # 1-5 scale
    
    # Processing status
    is_embedded = Column(Boolean, default=False, index=True)
    embedding_id = Column(Integer)  # Reference to document_embeddings
    
    # Metadata
    language = Column(String(10), default="en")
    word_count = Column(Integer)
    extra_data = Column(JSONB)  # 'metadata' is reserved in SQLAlchemy
    
    __table_args__ = (
        Index('idx_news_published', 'published_at'),
        Index('idx_news_source_date', 'source', 'published_at'),
        Index('idx_news_tickers', 'tickers', postgresql_using='gin'),
        Index('idx_news_sectors', 'sectors', postgresql_using='gin'),
        Index('idx_news_sentiment', 'sentiment'),
        Index('idx_news_event_type', 'event_type'),
    )
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...')>"


class NewsSource(Base):
    """
    RSS/News source configuration.
    
    Manages news crawling sources.
    """
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(2048), nullable=False)
    source_type = Column(String(50), default="rss")  # rss, api, scraper
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    crawl_interval_minutes = Column(Integer, default=30)
    
    # Statistics
    last_crawl_at = Column(TIMESTAMP(timezone=True))
    total_articles = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Metadata
    category = Column(String(100))  # finance, tech, general
    priority = Column(Integer, default=5)  # 1-10
    config = Column(JSONB)  # Source-specific config
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NewsSource(name='{self.name}', active={self.is_active})>"


class NewsSyncStatus(Base):
    """
    Tracks news crawling sync status.
    """
    __tablename__ = "news_sync_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, index=True)
    
    last_sync_at = Column(TIMESTAMP(timezone=True), nullable=False)
    articles_synced = Column(Integer, default=0)
    articles_new = Column(Integer, default=0)
    articles_updated = Column(Integer, default=0)
    
    status = Column(String(50), default="completed")  # running, completed, failed
    error_message = Column(Text)
    duration_seconds = Column(Float)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NewsSyncStatus(source_id={self.source_id}, status={self.status})>"
