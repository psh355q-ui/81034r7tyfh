"""
Alembic Migration: Add shadow_trades table

작성일: 2025-12-15
목적: Shadow Trade 추적을 위한 테이블 생성
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# Revision identifiers
revision = '251215_shadow_trades'
down_revision = None  # 실제로는 이전 마이그레이션 ID
branch_labels = None
depends_on = None


def upgrade():
    """
    shadow_trades 테이블 생성
    """
    op.create_table(
        'shadow_trades',
        
        # 기본 정보
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('proposal_id', UUID(as_uuid=True), nullable=True),
        
        # 거래 정보
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        
        # 가격 정보
        sa.Column('entry_price', sa.Float, nullable=False),
        sa.Column('exit_price', sa.Float, nullable=True),
        sa.Column('shares', sa.Integer, default=0),
        
        # 손익 정보
        sa.Column('virtual_pnl', sa.Float, default=0.0),
        sa.Column('virtual_pnl_pct', sa.Float, default=0.0),
        
        # 거부 정보
        sa.Column('rejection_reason', sa.String(200), nullable=True),
        sa.Column('violated_articles', sa.Text, nullable=True),
        
        # 상태
        sa.Column('status', sa.String(20), default='TRACKING'),
        sa.Column('tracking_days', sa.Integer, default=7),
        
        # 시간
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('closed_at', sa.DateTime, nullable=True),
        
        # 메타데이터
        sa.Column('notes', sa.Text, nullable=True),
    )
    
    # 인덱스 생성
    op.create_index('idx_shadow_trades_ticker', 'shadow_trades', ['ticker'])
    op.create_index('idx_shadow_trades_status', 'shadow_trades', ['status'])
    op.create_index('idx_shadow_trades_created_at', 'shadow_trades', ['created_at'])
    
    print("✅ shadow_trades 테이블 생성 완료")


def downgrade():
    """
    shadow_trades 테이블 삭제
    """
    op.drop_index('idx_shadow_trades_created_at', 'shadow_trades')
    op.drop_index('idx_shadow_trades_status', 'shadow_trades')
    op.drop_index('idx_shadow_trades_ticker', 'shadow_trades')
    
    op.drop_table('shadow_trades')
    
    print("✅ shadow_trades 테이블 삭제 완료")


if __name__ == "__main__":
    print("=== Shadow Trades Migration ===\n")
    print("이 파일은 Alembic 마이그레이션 스크립트입니다.")
    print("\n실행:")
    print("  alembic upgrade head")
    print("\n롤백:")
    print("  alembic downgrade -1")
