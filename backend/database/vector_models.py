
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from pgvector.sqlalchemy import Vector
from backend.database.vector_db import VectorBase
from datetime import datetime

class NewsEmbedding(VectorBase):
    """
    Stores vector embeddings for News Articles.
    """
    __tablename__ = 'news_embeddings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, unique=True, nullable=False)  # Reference to Main DB NewsArticle.id
    
    # Metadata for filtering without joining Main DB instantly
    title = Column(String(500), nullable=True)
    published_date = Column(DateTime, nullable=True)
    sector = Column(String(100), nullable=True)
    tickers = Column(String(200), nullable=True)
    
    # The Embedding Vector (Dimension 768 for Gemini Text Embedding 004)
    # or 1536 for OpenAI text-embedding-3-small
    # We will assume Gemini-004 which is 768.
    embedding = Column(Vector(768), nullable=False)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        # IVFFlat index for faster approximate search (requires rows to be populated first usually)
        # We start with HNSW which is better but more expensive, or just standard for small data.
        # Index('idx_news_embedding', 'embedding', postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}),
    )

class SectorEmbedding(VectorBase):
    """
    Stores embeddings for Sector descriptions/trends.
    """
    __tablename__ = 'sector_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
