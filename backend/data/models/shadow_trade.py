"""
Shadow Trade Model - 그림자 거래 데이터 모델

거부되거나 HOLD된 제안을 가상으로 추적

작성일: 2025-12-15
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.core.models.base import Base


class ShadowTrade(Base):
    """
    Shadow Trade (그림자 거래)
    
    AI가 제안했으나 거부되거나 HOLD된 거래를
    가상으로 추적하여 "방어 성과"를 측정합니다.
    """
    
    __tablename__ = "shadow_trades"
    
    # 기본 정보
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), nullable=True)  # 원본 제안 ID
    
    # 거래 정보
    ticker = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    
    # 가격 정보
    entry_price = Column(Float, nullable=False)
    """진입 가격 (거부 시점의 가격)"""
    
    exit_price = Column(Float, nullable=True)
    """청산 가격 (추적 종료 시점)"""
    
    shares = Column(Integer, default=0)
    """가상 매수 주식 수"""
    
    # 손익 정보
    virtual_pnl = Column(Float, default=0.0)
    """가상 손익 ($)"""
    
    virtual_pnl_pct = Column(Float, default=0.0)
    """가상 손익률 (%)"""
    
    # 거부 정보
    rejection_reason = Column(String(200), nullable=True)
    """거부 사유"""
    
    violated_articles = Column(Text, nullable=True)
    """위반된 헌법 조항"""
    
    # 상태
    status = Column(String(20), default='TRACKING')
    """TRACKING, CLOSED, EXPIRED"""
    
    tracking_days = Column(Integer, default=7)
    """추적 기간 (일)"""
    
    # 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    """거부 시점"""
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    """마지막 업데이트"""
    
    closed_at = Column(DateTime, nullable=True)
    """추적 종료 시점"""
    
    # 메타데이터
    notes = Column(Text, nullable=True)
    """추가 메모"""
    
    def __repr__(self):
        return f"<ShadowTrade {self.ticker} {self.action} @ ${self.entry_price} PnL: ${self.virtual_pnl}>"
    
    def calculate_pnl(self, current_price: float) -> tuple[float, float]:
        """
        현재 가격으로 가상 손익 계산
        
        Args:
            current_price: 현재 시장 가격
            
        Returns:
            (pnl_dollars, pnl_percent)
        """
        if self.action == 'BUY':
            # 매수 거부 → 현재 가격이 올랐으면 손실 (기회 비용)
            # 현재 가격이 내렸으면 이득 (방어 성공)
            pnl_pct = (current_price - self.entry_price) / self.entry_price
            pnl_dollars = (current_price - self.entry_price) * self.shares
        
        elif self.action == 'SELL':
            # 매도 거부 → 현재 가격이 내렸으면 손실
            # 현재 가격이 올랐으면 이득
            pnl_pct = (self.entry_price - current_price) / self.entry_price
            pnl_dollars = (self.entry_price - current_price) * self.shares
        
        else:  # HOLD
            # 변화 없음
            pnl_pct = 0.0
            pnl_dollars = 0.0
        
        return pnl_dollars, pnl_pct
    
    def update_pnl(self, current_price: float):
        """
        현재 가격으로 손익 업데이트
        
        Args:
            current_price: 현재 시장 가격
        """
        self.virtual_pnl, self.virtual_pnl_pct = self.calculate_pnl(current_price)
        self.exit_price = current_price
        self.updated_at = datetime.utcnow()
    
    def close_tracking(self, final_price: float):
        """
        추적 종료
        
        Args:
            final_price: 최종 가격
        """
        self.update_pnl(final_price)
        self.status = 'CLOSED'
        self.closed_at = datetime.utcnow()
    
    def is_defensive_win(self) -> bool:
        """
        방어 성공 여부 (손실을 피했는지)
        
        Returns:
            True if 손실 방어 성공
        """
        if self.action == 'BUY':
            # 매수 거부 후 가격이 내렸으면 방어 성공
            return self.virtual_pnl_pct < 0
        
        elif self.action == 'SELL':
            # 매도 거부 후 가격이 올랐으면 방어 성공
            return self.virtual_pnl_pct > 0
        
        return False
    
    def get_avoided_loss(self) -> float:
        """
        방어한 손실 금액
        
        Returns:
            방어 성공 시 손실 금액 (양수), 아니면 0
        """
        if self.is_defensive_win():
            return abs(self.virtual_pnl)
        return 0.0
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': str(self.id),
            'ticker': self.ticker,
            'action': self.action,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'shares': self.shares,
            'virtual_pnl': self.virtual_pnl,
            'virtual_pnl_pct': self.virtual_pnl_pct,
            'rejection_reason': self.rejection_reason,
            'violated_articles': self.violated_articles,
            'status': self.status,
            'is_defensive_win': self.is_defensive_win(),
            'avoided_loss': self.get_avoided_loss(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
