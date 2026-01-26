"""Add AI collective intelligence tables

Phase F1: AI 집단지성 고도화

Revision ID: add_ai_collective_tables
Revises: add_rag_embedding_tables
Create Date: 2025-12-08

New Tables:
- debate_history: AI 토론 기록
- ai_agent_performance: AI 에이전트별 성과
- ai_role_assignments: AI 역할 할당 이력
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = 'add_ai_collective_tables'
down_revision = 'analytics_001'  # Links to add_analytics_tables (not rag_embedding_001)
branch_labels = None
depends_on = None


def upgrade():
    """Create AI collective intelligence tables"""
    
    # ═══════════════════════════════════════════════════════════════
    # 1. debate_history 테이블 - AI 토론 기록
    # ═══════════════════════════════════════════════════════════════
    op.create_table(
        'debate_history',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.func.now()),
        sa.Column('ticker', sa.String(20), nullable=False, index=True),
        sa.Column('topic', sa.String(200), nullable=False),
        
        # AI별 투표 (JSON)
        sa.Column('ai_votes', JSONB, nullable=False),
        # 예: {"claude": {"vote": "BUY", "confidence": 0.75, "reasoning": "..."}}
        
        # 최종 결정
        sa.Column('final_decision', sa.String(20), nullable=False),
        sa.Column('consensus_strength', sa.Float, nullable=False),
        sa.Column('dissenting_agents', JSONB, default=[]),
        
        # 시장 컨텍스트
        sa.Column('market_context', JSONB, nullable=True),
        # 예: {"price": 560.0, "volatility": 0.25, "vix": 18.5}
        
        # 실행 결과 (사후 기록)
        sa.Column('executed', sa.Boolean, default=False),
        sa.Column('execution_price', sa.Float, nullable=True),
        sa.Column('pnl_result', sa.Numeric(12, 2), nullable=True),
        sa.Column('pnl_percentage', sa.Float, nullable=True),
        sa.Column('outcome_recorded_at', sa.DateTime(timezone=True), nullable=True),
        
        # 추론 로그 (상세 논거)
        sa.Column('reasoning_log', sa.Text, nullable=True),
        
        # 메타데이터
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # 인덱스 생성
    op.create_index(
        'ix_debate_history_timestamp',
        'debate_history',
        ['timestamp']
    )
    op.create_index(
        'ix_debate_history_ticker_timestamp',
        'debate_history',
        ['ticker', 'timestamp']
    )
    op.create_index(
        'ix_debate_history_final_decision',
        'debate_history',
        ['final_decision']
    )
    
    # ═══════════════════════════════════════════════════════════════
    # 2. ai_agent_performance 테이블 - AI 에이전트별 성과
    # ═══════════════════════════════════════════════════════════════
    op.create_table(
        'ai_agent_performance',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('agent_name', sa.String(50), nullable=False, index=True),
        sa.Column('period_date', sa.Date, nullable=False, index=True),
        
        # 거래 통계
        sa.Column('total_trades', sa.Integer, default=0),
        sa.Column('winning_trades', sa.Integer, default=0),
        sa.Column('losing_trades', sa.Integer, default=0),
        
        # 성과 지표
        sa.Column('win_rate', sa.Float, default=0.5),
        sa.Column('avg_return', sa.Float, default=0.0),
        sa.Column('total_return', sa.Float, default=0.0),
        sa.Column('max_drawdown', sa.Float, default=0.0),
        sa.Column('sharpe_ratio', sa.Float, nullable=True),
        
        # 예측 정확도
        sa.Column('prediction_accuracy', sa.Float, default=0.5),
        
        # 신뢰도 보정
        sa.Column('avg_confidence', sa.Float, default=0.5),
        sa.Column('confidence_calibration', sa.Float, default=1.0),
        
        # 가중치
        sa.Column('current_weight', sa.Float, default=1.0),
        
        # 역할 정보
        sa.Column('primary_role', sa.String(50), nullable=True),
        
        # 메타데이터
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # 유니크 제약: 에이전트 + 날짜 조합
        sa.UniqueConstraint('agent_name', 'period_date', name='uq_agent_period')
    )
    
    # 인덱스 생성
    op.create_index(
        'ix_ai_agent_performance_agent_date',
        'ai_agent_performance',
        ['agent_name', 'period_date']
    )
    
    # ═══════════════════════════════════════════════════════════════
    # 3. ai_role_assignments 테이블 - AI 역할 할당 이력
    # ═══════════════════════════════════════════════════════════════
    op.create_table(
        'ai_role_assignments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('agent_name', sa.String(50), nullable=False, index=True),
        sa.Column('primary_role', sa.String(50), nullable=False),
        sa.Column('secondary_roles', JSONB, default=[]),
        
        # 할당 기간
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        
        # 할당 사유
        sa.Column('assignment_reason', sa.String(200), nullable=True),
        
        # 메타데이터
        sa.Column('metadata', JSONB, default={})
    )
    
    # 인덱스 생성
    op.create_index(
        'ix_ai_role_assignments_active',
        'ai_role_assignments',
        ['agent_name', 'is_active']
    )
    
    # ═══════════════════════════════════════════════════════════════
    # 4. ai_weight_history 테이블 - 가중치 변경 이력
    # ═══════════════════════════════════════════════════════════════
    op.create_table(
        'ai_weight_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        
        # 변경 전후 가중치
        sa.Column('old_weights', JSONB, nullable=False),
        # 예: {"claude": 1.0, "chatgpt": 1.0, "gemini": 1.0}
        sa.Column('new_weights', JSONB, nullable=False),
        
        # 변경 사유
        sa.Column('trigger', sa.String(50), nullable=False),
        # auto_recalculation, manual_override, performance_based
        
        # 계산 기반 메트릭
        sa.Column('metrics_snapshot', JSONB, nullable=True),
        
        # 메타데이터
        sa.Column('metadata', JSONB, default={})
    )
    
    # 인덱스 생성
    op.create_index(
        'ix_ai_weight_history_timestamp',
        'ai_weight_history',
        ['timestamp']
    )


def downgrade():
    """Drop AI collective intelligence tables"""
    op.drop_table('ai_weight_history')
    op.drop_table('ai_role_assignments')
    op.drop_table('ai_agent_performance')
    op.drop_table('debate_history')
