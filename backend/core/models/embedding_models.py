"""
Document Embedding Models for RAG Foundation (Phase 13).

Supports:
1. SEC filings embeddings
2. News article embeddings
3. pgvector for similarity search
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Index, Float
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from backend.core.database import Base


class DocumentEmbedding(Base):
    """
    Universal document embedding table with pgvector support.

    Stores embeddings for all document types:
    - SEC filings (10-Q, 10-K, 8-K)
    - News articles
    - AI analysis results
    - Economic indicators

    Design:
    - document_type: Polymorphic discriminator
    - document_id: Reference to source table
    - embedding: 1536-dim vector (OpenAI text-embedding-3-small)
    - chunk_index: For long documents split into chunks
    """

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Document reference (polymorphic)
    document_type = Column(String(50), nullable=False, index=True)
    # 'sec_filing' | 'news_article' | 'ai_analysis' | 'economic_indicator'
    document_id = Column(Integer, nullable=False, index=True)

    # Content metadata
    ticker = Column(String(20), index=True)  # Primary ticker (AAPL, MSFT)
    title = Column(Text)  # Document title or headline
    content_preview = Column(Text)  # First 500 chars for preview
    chunk_index = Column(Integer, default=0)  # For multi-chunk documents
    total_chunks = Column(Integer, default=1)

    # Embedding vector (OpenAI text-embedding-3-small: 1536 dimensions)
    embedding = Column(Vector(1536), nullable=False)

    # Cost tracking
    embedding_model = Column(String(50), default="text-embedding-3-small")
    embedding_cost_usd = Column(Float, default=0.0)
    token_count = Column(Integer)

    # Timestamps
    source_date = Column(TIMESTAMP(timezone=True))  # Original document date
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now, index=True)

    # Additional metadata
    doc_metadata = Column(JSONB)  # Flexible metadata storage

    def __repr__(self):
        return (
            f"<DocumentEmbedding(id={self.id}, "
            f"type={self.document_type}, "
            f"ticker={self.ticker}, "
            f"chunk={self.chunk_index}/{self.total_chunks})>"
        )


# Create indexes for fast similarity search
Index(
    "idx_embeddings_type_ticker",
    DocumentEmbedding.document_type,
    DocumentEmbedding.ticker,
)

Index(
    "idx_embeddings_source_date",
    DocumentEmbedding.source_date.desc(),
)

# pgvector HNSW index for similarity search (created in migration)
# CREATE INDEX ON document_embeddings USING hnsw (embedding vector_cosine_ops);


class EmbeddingCache(Base):
    """
    Cache for embeddings to avoid re-embedding identical content.

    Uses content hash (SHA-256) to detect duplicates.
    """

    __tablename__ = "embedding_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)

    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    # SHA-256 hash of content

    embedding_id = Column(Integer, nullable=False)
    # Reference to document_embeddings.id

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)

    def __repr__(self):
        return f"<EmbeddingCache(hash={self.content_hash[:16]}..., embedding_id={self.embedding_id})>"


class EmbeddingSyncStatus(Base):
    """
    Track embedding progress for incremental updates.

    Ensures we don't re-embed already processed documents.
    """

    __tablename__ = "embedding_sync_status"

    id = Column(Integer, primary_key=True, autoincrement=True)

    document_type = Column(String(50), nullable=False)
    ticker = Column(String(20))  # NULL = all tickers

    last_sync_date = Column(TIMESTAMP(timezone=True), nullable=False)
    last_document_id = Column(Integer)  # Last processed document ID
    documents_embedded = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now)
    updated_at = Column(
        TIMESTAMP(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self):
        return (
            f"<EmbeddingSyncStatus(type={self.document_type}, "
            f"ticker={self.ticker}, "
            f"embedded={self.documents_embedded})>"
        )


# Unique constraint for sync status
Index(
    "idx_embedding_sync_unique",
    EmbeddingSyncStatus.document_type,
    EmbeddingSyncStatus.ticker,
    unique=True,
)
