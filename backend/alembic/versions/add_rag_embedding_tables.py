"""
Add RAG embedding tables for Phase 13.

Revision ID: rag_embedding_001
Revises: incremental_update_001
Create Date: 2025-11-23

Tables:
1. document_embeddings: Vector embeddings with pgvector
2. embedding_cache: Content hash-based deduplication
3. embedding_sync_status: Incremental update tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "rag_embedding_001"
down_revision = "incremental_update_001"
branch_labels = None
depends_on = None


def upgrade():
    """Create RAG embedding tables."""

    # 0. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Document Embeddings Table (with pgvector)
    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        # Document reference (polymorphic)
        sa.Column("document_type", sa.String(50), nullable=False, index=True),
        sa.Column("document_id", sa.Integer, nullable=False, index=True),
        # Content metadata
        sa.Column("ticker", sa.String(20), index=True),
        sa.Column("title", sa.Text),
        sa.Column("content_preview", sa.Text),
        sa.Column("chunk_index", sa.Integer, default=0),
        sa.Column("total_chunks", sa.Integer, default=1),
        # Embedding vector (1536 dimensions for text-embedding-3-small)
        sa.Column(
            "embedding",
            postgresql.ARRAY(sa.Float, dimensions=1),
            nullable=False,
        ),
        # Note: The Vector type from pgvector will be created via raw SQL below
        # Cost tracking
        sa.Column("embedding_model", sa.String(50), default="text-embedding-3-small"),
        sa.Column("embedding_cost_usd", sa.Float, default=0.0),
        sa.Column("token_count", sa.Integer),
        # Timestamps
        sa.Column("source_date", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), index=True
        ),
        # Metadata
        sa.Column("metadata", postgresql.JSONB),
    )

    # Convert embedding column to vector type (pgvector)
    op.execute("""
        ALTER TABLE document_embeddings
        ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536);
    """)

    # Create indexes
    op.create_index(
        "idx_embeddings_type_ticker",
        "document_embeddings",
        ["document_type", "ticker"],
    )

    op.create_index(
        "idx_embeddings_source_date",
        "document_embeddings",
        [sa.text("source_date DESC")],
    )

    # Create HNSW index for vector similarity search
    # HNSW (Hierarchical Navigable Small World) for fast approximate search
    op.execute("""
        CREATE INDEX idx_embeddings_vector_hnsw
        ON document_embeddings
        USING hnsw (embedding vector_cosine_ops);
    """)

    # 2. Embedding Cache Table (deduplication)
    op.create_table(
        "embedding_cache",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("embedding_id", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )

    # 3. Embedding Sync Status Table (incremental updates)
    op.create_table(
        "embedding_sync_status",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("ticker", sa.String(20)),
        sa.Column("last_sync_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_document_id", sa.Integer),
        sa.Column("documents_embedded", sa.Integer, default=0),
        sa.Column("total_cost_usd", sa.Float, default=0.0),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Unique constraint for sync status
    op.create_index(
        "idx_embedding_sync_unique",
        "embedding_sync_status",
        ["document_type", "ticker"],
        unique=True,
    )

    # 4. Embedding Cost Analytics View (Materialized)
    op.execute("""
        CREATE MATERIALIZED VIEW embedding_cost_analytics AS
        SELECT
            document_type,
            ticker,
            COUNT(*) as total_embeddings,
            SUM(token_count) as total_tokens,
            SUM(embedding_cost_usd) as total_cost_usd,
            AVG(embedding_cost_usd) as avg_cost_usd,
            MAX(created_at) as last_embedded_at,
            MIN(created_at) as first_embedded_at
        FROM document_embeddings
        GROUP BY document_type, ticker;
    """)

    # Create index on materialized view
    op.create_index(
        "idx_embedding_cost_ticker",
        "embedding_cost_analytics",
        ["ticker"],
    )

    # 5. Auto-cleanup function (remove old news embeddings)
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_news_embeddings()
        RETURNS void AS $$
        BEGIN
            -- Delete news embeddings older than 30 days
            DELETE FROM document_embeddings
            WHERE document_type = 'news_article'
              AND source_date < NOW() - INTERVAL '30 days';

            -- Refresh materialized view
            REFRESH MATERIALIZED VIEW CONCURRENTLY embedding_cost_analytics;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 6. Scheduled cleanup job (requires pg_cron extension)
    # Uncomment if pg_cron is installed:
    # op.execute("""
    #     SELECT cron.schedule(
    #         'cleanup-old-news-embeddings',
    #         '0 4 * * *',  -- Run at 4 AM daily
    #         'SELECT cleanup_old_news_embeddings();'
    #     );
    # """)


def downgrade():
    """Remove RAG embedding tables."""

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS embedding_cost_analytics;")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_news_embeddings();")

    # Drop tables
    op.drop_table("embedding_sync_status")
    op.drop_table("embedding_cache")
    op.drop_table("document_embeddings")

    # Drop pgvector extension (optional - may be used by other tables)
    # op.execute("DROP EXTENSION IF EXISTS vector;")
