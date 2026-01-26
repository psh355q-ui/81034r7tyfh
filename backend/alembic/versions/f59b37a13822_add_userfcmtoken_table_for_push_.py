"""Add UserFCMToken table for push notification management

Revision ID: f59b37a13822
Revises: add_ai_collective_tables
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f59b37a13822'
down_revision = 'add_ai_collective_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create UserFCMToken table for push notifications"""
    
    op.create_table(
        'user_fcm_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('token', sa.String(length=300), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('device_id', sa.String(length=200), nullable=True),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('app_version', sa.String(length=50), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_fcm_user_id', 'user_fcm_tokens', ['user_id'])
    op.create_index('idx_fcm_token', 'user_fcm_tokens', ['token'], unique=True)
    op.create_index('idx_fcm_active', 'user_fcm_tokens', ['is_active'], 
                   postgresql_where=sa.text('is_active = TRUE'))
    op.create_index('idx_fcm_user_active', 'user_fcm_tokens', ['user_id', 'is_active'])


def downgrade() -> None:
    """Drop UserFCMToken table"""
    
    # Drop indexes
    op.drop_index('idx_fcm_user_active', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_active', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_token', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_user_id', table_name='user_fcm_tokens')
    
    # Drop table
    op.drop_table('user_fcm_tokens')
