"""
Alembic Migration: Add proposals table

작성일: 2025-12-15
목적: AI 제안 승인/거부 워크플로우
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from datetime import datetime


# Revision identifiers
revision = '251215_proposals'
down_revision = '251215_shadow_trades'
branch_labels = None
depends_on = None


def upgrade():
    """
    proposals 테이블 생성
    """
    op.create_table(
        'proposals',
        
        # 기본 정보
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        
        # 제안 정보
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        
        # 가격 정보
        sa.Column('target_price', sa.Float, nullable=False),
        sa.Column('position_size', sa.Float, default=0.0),
        sa.Column('order_value_usd', sa.Float, default=0.0),
        sa.Column('shares', sa.Integer, default=0),
        
        # AI 분석
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('consensus_level', sa.Float, default=0.0),
        sa.Column('debate_summary', sa.Text, nullable=True),
        sa.Column('model_votes', JSON, nullable=True),
        
        # 헌법 검증
        sa.Column('is_constitutional', sa.Boolean, default=False),
        sa.Column('violated_articles', sa.Text, nullable=True),
        sa.Column('constitutional_warnings', sa.Text, nullable=True),
        
        # 승인 상태
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('is_approved', sa.Boolean, default=False),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.String(200), nullable=True),
        sa.Column('rejected_at', sa.DateTime, nullable=True),
        
        # 실행 정보
        sa.Column('executed_at', sa.DateTime, nullable=True),
        sa.Column('execution_price', sa.Float, nullable=True),
        
        # 시장 컨텍스트
        sa.Column('market_regime', sa.String(20), nullable=True),
        sa.Column('vix', sa.Float, nullable=True),
        sa.Column('news_title', sa.String(500), nullable=True),
        
        # 시간
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        
        # 메타데이터
        sa.Column('telegram_message_id', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    )
    
    # 인덱스 생성
    op.create_index('idx_proposals_ticker', 'proposals', ['ticker'])
    op.create_index('idx_proposals_status', 'proposals', ['status'])
    op.create_index('idx_proposals_created_at', 'proposals', ['created_at'])
    op.create_index('idx_proposals_approved_at', 'proposals', ['approved_at'])
    
    print("✅ proposals 테이블 생성 완료")


def downgrade():
    """
    proposals 테이블 삭제
    """
    op.drop_index('idx_proposals_approved_at', 'proposals')
   op.drop_index('idx_proposals_created_at', 'proposals')
    op.drop_index('idx_proposals_status', 'proposals')
    op.drop_index('idx_proposals_ticker', 'proposals')
    
    op.drop_table('proposals')
    
    print("✅ proposals 테이블 삭제 완료")


if __name__ == "__main__":
    print("=== Proposals Migration ===\n")
    print("이 파일은 Alembic 마이그레이션 스크립트입니다.")
    print("\n실행:")
    print("  alembic upgrade head")
    print("\n롤백:")
    print("  alembic downgrade -1")
