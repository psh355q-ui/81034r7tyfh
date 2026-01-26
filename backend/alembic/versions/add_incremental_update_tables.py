"""
Add incremental update tables for SEC filings, stock prices, and AI cache.

Revision ID: incremental_update_001
Revises: previous_migration
Create Date: 2025-11-23

Tables:
1. sec_filings: SEC file metadata with hierarchical tags
2. stock_prices: Yahoo Finance OHLCV data (TimescaleDB hypertable)
3. price_sync_status: Incremental update tracking
4. ai_analysis_cache: AI analysis caching with prompt versioning
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'incremental_update_001'
down_revision = '001'  # Links to 001_create_features_table
branch_labels = None
depends_on = None


def upgrade():
    """Create incremental update tables."""

    # 1. SEC Filings Metadata Table
    op.create_table(
        'sec_filings',
        sa.Column('accession_number', sa.String(24), primary_key=True),
        sa.Column('ticker', sa.String(20), nullable=False, index=True),
        sa.Column('filing_type', sa.String(10), nullable=False),  # 10-Q, 10-K, 8-K
        sa.Column('filing_date', sa.Date, nullable=False, index=True),
        sa.Column('local_path', sa.Text, nullable=False),  # Relative path from storage root
        sa.Column('file_hash', sa.String(64), nullable=False),  # SHA-256
        sa.Column('file_size_bytes', sa.BigInteger),
        sa.Column('download_status', sa.String(20), default='PENDING'),  # PENDING, SUCCESS, FAILED
        sa.Column('parse_status', sa.String(20)),  # PENDING, SUCCESS, FAILED
        sa.Column('downloaded_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('parsed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for fast tag-based queries
    op.create_index('idx_sec_ticker_date', 'sec_filings', ['ticker', 'filing_date'], postgresql_ops={'filing_date': 'DESC'})
    op.create_index('idx_sec_type_date', 'sec_filings', ['filing_type', 'filing_date'])

    # 2. Stock Prices (TimescaleDB Hypertable)
    op.create_table(
        'stock_prices',
        sa.Column('time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('open', sa.DECIMAL(12, 4)),
        sa.Column('high', sa.DECIMAL(12, 4)),
        sa.Column('low', sa.DECIMAL(12, 4)),
        sa.Column('close', sa.DECIMAL(12, 4)),
        sa.Column('volume', sa.BigInteger),
        sa.Column('adjusted_close', sa.DECIMAL(12, 4)),
        sa.PrimaryKeyConstraint('time', 'ticker'),
    )

    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable(
            'stock_prices',
            'time',
            if_not_exists => TRUE,
            migrate_data => TRUE
        );
    """)

    # Create index for ticker queries
    op.create_index('idx_stock_ticker_time', 'stock_prices', ['ticker', 'time'])

    # 3. Price Sync Status (Incremental Update Tracking)
    op.create_table(
        'price_sync_status',
        sa.Column('ticker', sa.String(20), primary_key=True),
        sa.Column('last_sync_date', sa.Date, nullable=False),  # Last time we ran sync
        sa.Column('last_price_date', sa.Date, nullable=False),  # Latest price date in DB
        sa.Column('total_rows', sa.Integer, default=0),
        sa.Column('first_sync_date', sa.Date),  # Initial backfill date
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 4. AI Analysis Cache (Enhanced with Prompt Versioning)
    op.create_table(
        'ai_analysis_cache',
        sa.Column('cache_id', sa.String(32), primary_key=True),  # Hash of (ticker, type, features, prompt_version)
        sa.Column('ticker', sa.String(20), nullable=False, index=True),
        sa.Column('analysis_type', sa.String(50), nullable=False),  # investment_decision, sec_analysis, etc.
        sa.Column('feature_fingerprint', sa.String(32), nullable=False),  # Hash of input features
        sa.Column('prompt_version', sa.String(10), nullable=False),  # v1.0, v2.1, etc.
        sa.Column('result', postgresql.JSONB, nullable=False),  # AI analysis result
        sa.Column('input_tokens', sa.Integer),
        sa.Column('output_tokens', sa.Integer),
        sa.Column('input_cost_usd', sa.DECIMAL(10, 6), default=0.0),
        sa.Column('output_cost_usd', sa.DECIMAL(10, 6), default=0.0),
        sa.Column('model_used', sa.String(50)),  # claude-haiku-4, claude-sonnet-4.5, etc.
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column('access_count', sa.Integer, default=0),  # Cache hit tracking
        sa.Column('last_accessed_at', sa.TIMESTAMP(timezone=True)),
    )

    # Indexes for cache queries
    op.create_index('idx_cache_ticker_type', 'ai_analysis_cache', ['ticker', 'analysis_type'])
    op.create_index('idx_cache_expires', 'ai_analysis_cache', ['expires_at'])
    op.create_index('idx_cache_prompt_version', 'ai_analysis_cache', ['analysis_type', 'prompt_version'])

    # 5. Cost Analytics View (Materialized for performance)
    op.execute("""
        CREATE MATERIALIZED VIEW ai_cost_analytics AS
        SELECT
            ticker,
            analysis_type,
            COUNT(*) as total_analyses,
            SUM(access_count) as total_cache_hits,
            SUM(input_cost_usd + output_cost_usd) as total_cost_usd,
            AVG(input_cost_usd + output_cost_usd) as avg_cost_usd,
            MAX(created_at) as last_analysis_at
        FROM ai_analysis_cache
        WHERE expires_at > NOW()
        GROUP BY ticker, analysis_type;
    """)

    # Create index on materialized view
    op.create_index('idx_cost_analytics_ticker', 'ai_cost_analytics', ['ticker'])

    # 6. Auto-cleanup expired cache (PostgreSQL function + trigger)
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_cache()
        RETURNS void AS $$
        BEGIN
            DELETE FROM ai_analysis_cache
            WHERE expires_at < NOW() - INTERVAL '7 days';
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create scheduled job (requires pg_cron extension)
    # Uncomment if pg_cron is installed:
    # op.execute("""
    #     SELECT cron.schedule(
    #         'cleanup-expired-cache',
    #         '0 3 * * *',  -- Run at 3 AM daily
    #         'SELECT cleanup_expired_cache();'
    #     );
    # """)


def downgrade():
    """Remove incremental update tables."""

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ai_cost_analytics;")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS cleanup_expired_cache();")

    # Drop tables (order matters due to dependencies)
    op.drop_table('ai_analysis_cache')
    op.drop_table('price_sync_status')
    op.drop_table('stock_prices')
    op.drop_table('sec_filings')
