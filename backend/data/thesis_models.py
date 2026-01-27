"""
Thesis Keeper Model

투자 논리(Investment Thesis) 저장 모델
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, Index
from sqlalchemy.sql import func
from backend.core.database import Base


class PortfolioThesis(Base):
    """
    Portfolio Thesis Model
    
    투자 논리 저장 테이블
    """
    __tablename__ = 'portfolio_thesis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    thesis_text = Column(Text, nullable=False)
    moat_type = Column(String(50))  # 'network_effect', 'brand', 'cost_advantage', 'switching_cost', 'regulatory'
    moat_strength = Column(DECIMAL(3, 2))  # 0.0 ~ 1.0
    entry_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    status = Column(String(20), default='active', index=True)  # 'active', 'violated', 'exited'
    violation_reason = Column(Text, nullable=True)
    violation_date = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Indexes
    __table_args__ = (
        Index('idx_thesis_ticker_status', 'ticker', 'status'),
    )
    
    def __repr__(self):
        return f"<PortfolioThesis(ticker={self.ticker}, status={self.status})>"
