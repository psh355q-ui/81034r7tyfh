"""
Dividend Models - 배당주 데이터베이스 모델

Phase 21: Dividend Intelligence Module
Date: 2025-12-25

Models:
- DividendHistory: 실제 배당 지급 이력
- DividendSnapshot: Twin Ledger용 예측/실제 비교
- DividendAristocrats: 배당 귀족주 (25년+ 연속 증가)
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class DividendHistory(Base):
    """배당 이력 (실제 지급 데이터)"""
    __tablename__ = "dividend_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    ex_dividend_date = Column(Date, nullable=False, index=True)  # 배당락일
    payment_date = Column(Date)  # 지급일
    amount = Column(Numeric(10, 4), nullable=False)  # 배당금 (USD)
    frequency = Column(String(20))  # Monthly, Quarterly, Annual
    record_date = Column(Date)  # 배당 기준일
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DividendHistory(ticker={self.ticker}, ex_date={self.ex_dividend_date}, amount={self.amount})>"


class DividendSnapshot(Base):
    """Twin Ledger용 배당 예측/실제 기록"""
    __tablename__ = "dividend_snapshot"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, default=func.current_date())
    
    # 예측 데이터
    predicted_annual_income = Column(Numeric(15, 2))  # 연간 예상 배당금 (KRW)
    predicted_monthly_avg = Column(Numeric(15, 2))    # 월평균 예상 배당금 (KRW)
    predicted_yield = Column(Numeric(5, 2))           # 예상 배당률 (%)
    
    # 실제 데이터 (12개월 후)
    actual_annual_income = Column(Numeric(15, 2))     # 실제 연간 배당금 (KRW)
    actual_monthly_avg = Column(Numeric(15, 2))       # 실제 월평균 배당금 (KRW)
    actual_yield = Column(Numeric(5, 2))              # 실제 배당률 (%)
    
    # 정확도
    accuracy_score = Column(Numeric(5, 2))  # 정확도 (%)
    prediction_error = Column(Numeric(10, 2))  # 예측 오차 (KRW)
    
    # 메타데이터
    shares_held = Column(Integer)  # 보유 주식 수
    avg_purchase_price = Column(Numeric(10, 2))  # 평균 매입가 (USD)
    exchange_rate = Column(Numeric(10, 2))  # 환율 (KRW/USD)
    
    created_at = Column(DateTime, default=func.now())
    evaluated_at = Column(DateTime)  # 평가 완료 시간 (12개월 후)
    
    def calculate_accuracy(self):
        """정확도 계산"""
        if self.predicted_annual_income and self.actual_annual_income:
            error = abs(self.actual_annual_income - self.predicted_annual_income)
            accuracy = (1 - error / self.predicted_annual_income) * 100
            self.accuracy_score = round(max(0, min(100, accuracy)), 2)
            self.prediction_error = round(error, 2)
    
    def __repr__(self):
        return f"<DividendSnapshot(ticker={self.ticker}, date={self.snapshot_date}, accuracy={self.accuracy_score})>"


class DividendAristocrats(Base):
    """배당 귀족주 (25년+ 연속 배당 증가)"""
    __tablename__ = "dividend_aristocrats"
    
    ticker = Column(String(10), primary_key=True)
    company_name = Column(String(200), nullable=False)
    sector = Column(String(50), index=True)
    industry = Column(String(100))
    
    # 배당 이력
    consecutive_years = Column(Integer, nullable=False)  # 연속 배당 증가 연수
    first_dividend_year = Column(Integer)  # 최초 배당 연도
    
    # 배당 데이터
    current_yield = Column(Numeric(5, 2))  # 현재 배당률 (%)
    payout_ratio = Column(Numeric(5, 2))   # 배당 성향 (%)
    dividend_growth_5y = Column(Numeric(5, 2))   # 5년 배당 성장률 (%)
    dividend_growth_10y = Column(Numeric(5, 2))  # 10년 배당 성장률 (%)
    
    # 재무 건전성
    debt_to_equity = Column(Numeric(10, 2))  # 부채비율
    free_cashflow = Column(Numeric(15, 2))   # 잉여현금흐름 (USD)
    market_cap = Column(Numeric(15, 2))      # 시가총액 (USD)
    
    # 메타데이터
    is_sp500 = Column(Integer, default=0)  # S&P 500 포함 여부 (boolean)
    is_reit = Column(Integer, default=0)   # REIT 여부 (boolean)
    notes = Column(Text)  # 특이사항
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DividendAristocrats(ticker={self.ticker}, company={self.company_name}, years={self.consecutive_years})>"


# 테이블 생성 스크립트
def create_tables(engine):
    """배당 관련 테이블 생성"""
    Base.metadata.create_all(engine)
    print("✅ Dividend tables created successfully")


# 마이그레이션 SQL (주석으로 보관)
"""
-- DividendHistory 테이블
CREATE TABLE IF NOT EXISTS dividend_history (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    ex_dividend_date DATE NOT NULL,
    payment_date DATE,
    amount NUMERIC(10, 4) NOT NULL,
    frequency VARCHAR(20),
    record_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dividend_history_ticker ON dividend_history(ticker);
CREATE INDEX idx_dividend_history_ex_date ON dividend_history(ex_dividend_date);
CREATE UNIQUE INDEX idx_dividend_history_unique ON dividend_history(ticker, ex_dividend_date);

-- DividendSnapshot 테이블
CREATE TABLE IF NOT EXISTS dividend_snapshot (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    predicted_annual_income NUMERIC(15, 2),
    predicted_monthly_avg NUMERIC(15, 2),
    predicted_yield NUMERIC(5, 2),
    actual_annual_income NUMERIC(15, 2),
    actual_monthly_avg NUMERIC(15, 2),
    actual_yield NUMERIC(5, 2),
    accuracy_score NUMERIC(5, 2),
    prediction_error NUMERIC(10, 2),
    shares_held INTEGER,
    avg_purchase_price NUMERIC(10, 2),
    exchange_rate NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP
);

CREATE INDEX idx_dividend_snapshot_ticker ON dividend_snapshot(ticker);
CREATE INDEX idx_dividend_snapshot_date ON dividend_snapshot(snapshot_date);

-- DividendAristocrats 테이블
CREATE TABLE IF NOT EXISTS dividend_aristocrats (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    sector VARCHAR(50),
    industry VARCHAR(100),
    consecutive_years INTEGER NOT NULL,
    first_dividend_year INTEGER,
    current_yield NUMERIC(5, 2),
    payout_ratio NUMERIC(5, 2),
    dividend_growth_5y NUMERIC(5, 2),
    dividend_growth_10y NUMERIC(5, 2),
    debt_to_equity NUMERIC(10, 2),
    free_cashflow NUMERIC(15, 2),
    market_cap NUMERIC(15, 2),
    is_sp500 INTEGER DEFAULT 0,
    is_reit INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dividend_aristocrats_sector ON dividend_aristocrats(sector);
CREATE INDEX idx_dividend_aristocrats_years ON dividend_aristocrats(consecutive_years DESC);
"""
