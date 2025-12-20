"""
Proposal Model - AI 제안 데이터 모델

AI가 생성한 매매 제안을 저장하고 추적

작성일: 2025-12-15
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.core.models.base import Base


class Proposal(Base):
    """
    Proposal (제안)
    
    AI Debate Engine이 생성한 매매 제안
    Commander(사용자)의 승인을 기다립니다.
    
    헌법 제3조: "최종 실행권은 인간에게 있다"
    """
    
    __tablename__ = "proposals"
    
    # 기본 정보
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 제안 정보
    ticker = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    
    # 가격 정보
    target_price = Column(Float, nullable=False)
    """목표 가격"""
    
    position_size = Column(Float, default=0.0)
    """포지션 크기 (비율)"""
    
    order_value_usd = Column(Float, default=0.0)
    """주문 금액 ($)"""
    
    shares = Column(Integer, default=0)
    """주식 수"""
    
    # AI 분석
    reasoning = Column(Text, nullable=True)
    """AI 추론 근거"""
    
    confidence = Column(Float, default=0.0)
    """신뢰도 (0-1)"""
    
    consensus_level = Column(Float, default=0.0)
    """합의 수준 (0-1)"""
    
    debate_summary = Column(Text, nullable=True)
    """토론 요약"""
    
    model_votes = Column(JSON, nullable=True)
    """모델별 투표 결과"""
    
    # 헌법 검증
    is_constitutional = Column(Boolean, default=False)
    """헌법 준수 여부"""
    
    violated_articles = Column(Text, nullable=True)
    """위반된 헌법 조항"""
    
    constitutional_warnings = Column(Text, nullable=True)
    """헌법 경고 사항"""
    
    # 승인 상태
    status = Column(String(20), default='PENDING')
    """PENDING, APPROVED, REJECTED, EXECUTED, EXPIRED"""
    
    is_approved = Column(Boolean, default=False)
    """Commander 승인 여부"""
    
    approved_by = Column(String(100), nullable=True)
    """승인자"""
    
    approved_at = Column(DateTime, nullable=True)
    """승인 시각"""
    
    rejection_reason = Column(String(200), nullable=True)
    """거부 사유"""
    
    rejected_at = Column(DateTime, nullable=True)
    """거부 시각"""
    
    # 실행 정보
    executed_at = Column(DateTime, nullable=True)
    """실행 시각"""
    
    execution_price = Column(Float, nullable=True)
    """실제 실행 가격"""
    
    # 시장 컨텍스트
    market_regime = Column(String(20), nullable=True)
    """시장 체제"""
    
    vix = Column(Float, nullable=True)
    """VIX"""
    
    news_title = Column(String(500), nullable=True)
    """관련 뉴스"""
    
    # 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    """제안 생성 시각"""
    
    expires_at = Column(DateTime, nullable=True)
    """만료 시각"""
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    """마지막 업데이트"""
    
    # 메타데이터
    telegram_message_id = Column(String(50), nullable=True)
    """텔레그램 메시지 ID"""
    
    notes = Column(Text, nullable=True)
    """추가 메모"""
    
    def __repr__(self):
        return f"<Proposal {self.ticker} {self.action} @ ${self.target_price} ({self.status})>"
    
    def approve(self, approved_by: str):
        """
        제안 승인
        
        Args:
            approved_by: 승인자 (텔레그램 username 등)
        """
        self.is_approved = True
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()
    
    def reject(self, reason: str, rejected_by: str = None):
        """
        제안 거부
        
        Args:
            reason: 거부 사유
            rejected_by: 거부자
        """
        self.is_approved = False
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.rejected_at = datetime.utcnow()
        if rejected_by:
            self.approved_by = rejected_by  # 거부자도 기록
    
    def execute(self, execution_price: float):
        """
        제안 실행 완료
        
        Args:
            execution_price: 실제 실행 가격
        """
        self.status = 'EXECUTED'
        self.executed_at = datetime.utcnow()
        self.execution_price = execution_price
    
    def expire(self):
        """제안 만료"""
        self.status = 'EXPIRED'
    
    def is_pending(self) -> bool:
        """승인 대기 중인지"""
        return self.status == 'PENDING'
    
    def is_expired(self) -> bool:
        """만료되었는지"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return self.status == 'EXPIRED'
    
    def get_action_emoji(self) -> str:
        """액션 이모지"""
        emojis = {
            'BUY': '📈',
            'SELL': '📉',
            'HOLD': '⏸️'
        }
        return emojis.get(self.action, '❓')
    
    def get_status_emoji(self) -> str:
        """상태 이모지"""
        emojis = {
            'PENDING': '⏳',
            'APPROVED': '✅',
            'REJECTED': '❌',
            'EXECUTED': '✔️',
            'EXPIRED': '⏱️'
        }
        return emojis.get(self.status, '❓')
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': str(self.id),
            'ticker': self.ticker,
            'action': self.action,
            'target_price': self.target_price,
            'position_size': self.position_size,
            'order_value_usd': self.order_value_usd,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'consensus_level': self.consensus_level,
            'is_constitutional': self.is_constitutional,
            'violated_articles': self.violated_articles,
            'status': self.status,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'market_regime': self.market_regime,
            'vix': self.vix
        }
