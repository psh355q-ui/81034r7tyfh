"""Create features table with TimescaleDB hypertable

Revision ID: 001
Revises:
Create Date: 2024-11-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create features table with TimescaleDB hypertable.

    Schema follows spec.md and plan.md data-model section:
    - ticker: Stock symbol (e.g., AAPL, 005930.KS)
    - feature_name: Feature identifier (e.g., ret_5d, vol_20d)
    - value: Calculated feature value
    - as_of_timestamp: Point-in-time timestamp (for backtesting)
    - calculated_at: When this feature was computed
    - version: Feature calculation logic version
    - metadata: Additional context (JSONB)
    """
    # Create features table
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('feature_name', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Double(), nullable=True),
        sa.Column('as_of_timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('calculated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata', JSONB, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker', 'feature_name', 'as_of_timestamp', 'version', name='uq_features_ticker_name_time_version')
    )

    # Create hypertable (TimescaleDB-specific)
    # This optimizes time-series queries
    op.execute("""
        SELECT create_hypertable('features', 'as_of_timestamp',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)

    # Create index for fast lookups
    # Typical query: SELECT * FROM features WHERE ticker = ? AND feature_name = ? AND as_of_timestamp <= ? ORDER BY as_of_timestamp DESC LIMIT 1
    op.create_index(
        'idx_features_lookup',
        'features',
        ['ticker', 'feature_name', sa.text('as_of_timestamp DESC')],
        unique=False
    )

    # Create index for version queries (optional, for Phase 7)
    op.create_index(
        'idx_features_version',
        'features',
        ['ticker', 'feature_name', 'version'],
        unique=False
    )

    # Create index for calculated_at (for finding latest computed features)
    op.create_index(
        'idx_features_calculated_at',
        'features',
        [sa.text('calculated_at DESC')],
        unique=False
    )

    # Enable compression for old data (TimescaleDB feature)
    # Compress chunks older than 30 days to save space
    op.execute("""
        ALTER TABLE features SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker,feature_name'
        );
    """)

    op.execute("""
        SELECT add_compression_policy('features', INTERVAL '30 days');
    """)


def downgrade() -> None:
    """Drop features table and all indexes."""
    # Remove compression policy
    op.execute("""
        SELECT remove_compression_policy('features', if_exists => true);
    """)

    # Drop indexes
    op.drop_index('idx_features_calculated_at', table_name='features')
    op.drop_index('idx_features_version', table_name='features')
    op.drop_index('idx_features_lookup', table_name='features')

    # Drop hypertable (automatically drops table)
    op.execute("DROP TABLE IF EXISTS features CASCADE;")
