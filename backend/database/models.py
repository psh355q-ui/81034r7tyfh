"""
Phase 16+: Database Models for Persistent Storage

SQLAlchemy models for storing:
- News articles (RSS crawled)
- Analysis results (Deep Reasoning)
- Trading signals (PRIMARY/HIDDEN/LOSER)
- Backtest results (historical performance)
- Signal outcomes (actual returns)

Database: TimescaleDB (PostgreSQL with time-series extensions)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()


class NewsArticle(Base):
    """RSS 크롤링된 뉴스 기사"""
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=False)  # TechCrunch, Reuters, etc.
    published_date = Column(DateTime, nullable=False)
    crawled_at = Column(DateTime, nullable=False, default=datetime.now)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)

    # Relationships
    analyses = relationship("AnalysisResult", back_populates="article", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_news_published_date', 'published_date'),
        Index('idx_news_source', 'source'),
        Index('idx_news_crawled_at', 'crawled_at'),
    )

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"


class AnalysisResult(Base):
    """Deep Reasoning 분석 결과"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False)

    # Analysis metadata
    analyzed_at = Column(DateTime, nullable=False, default=datetime.now)
    model_name = Column(String(50), nullable=False)  # gemini-2.5-pro
    analysis_duration_seconds = Column(Float, nullable=True)

    # Deep Reasoning outputs
    theme = Column(String(200), nullable=False)
    bull_case = Column(Text, nullable=False)
    bear_case = Column(Text, nullable=False)

    # Reasoning trace (3-step CoT)
    step1_direct_impact = Column(Text, nullable=True)
    step2_secondary_impact = Column(Text, nullable=True)
    step3_conclusion = Column(Text, nullable=True)

    # Relationships
    article = relationship("NewsArticle", back_populates="analyses")
    signals = relationship("TradingSignal", back_populates="analysis", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_analysis_analyzed_at', 'analyzed_at'),
        Index('idx_analysis_article_id', 'article_id'),
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, theme='{self.theme}', signals={len(self.signals)})>"


class TradingSignal(Base):
    """생성된 트레이딩 시그널"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analysis_results.id'), nullable=False)

    # Signal details
    ticker = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY, SELL, TRIM, HOLD
    signal_type = Column(String(20), nullable=False, index=True)  # PRIMARY, HIDDEN, LOSER
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)

    # Timestamps
    generated_at = Column(DateTime, nullable=False, default=datetime.now)

    # Alert status
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime, nullable=True)

    # Outcome tracking
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    actual_return_pct = Column(Float, nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)

    # Relationships
    analysis = relationship("AnalysisResult", back_populates="signals")

    # Indexes
    __table_args__ = (
        Index('idx_signal_generated_at', 'generated_at'),
        Index('idx_signal_ticker', 'ticker'),
        Index('idx_signal_type', 'signal_type'),
        Index('idx_signal_confidence', 'confidence'),
        Index('idx_signal_ticker_generated', 'ticker', 'generated_at'),
    )

    def __repr__(self):
        return f"<TradingSignal(id={self.id}, ticker='{self.ticker}', action='{self.action}', confidence={self.confidence:.0%})>"


class BacktestRun(Base):
    """백테스트 실행 기록"""
    __tablename__ = 'backtest_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Backtest metadata
    strategy_name = Column(String(100), nullable=False)  # Keyword-Only, CoT+RAG
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    executed_at = Column(DateTime, nullable=False, default=datetime.now)

    # Performance metrics
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)  # %

    avg_return = Column(Float, nullable=False)  # %
    total_return = Column(Float, nullable=False)  # %
    sharpe_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)  # %

    # Special metrics
    hidden_beneficiaries_found = Column(Integer, default=0)

    # Relationships
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_executed_at', 'executed_at'),
        Index('idx_backtest_strategy', 'strategy_name'),
        Index('idx_backtest_period', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return f"<BacktestRun(id={self.id}, strategy='{self.strategy_name}', return={self.total_return:.1f}%)>"


class BacktestTrade(Base):
    """백테스트 개별 거래 기록"""
    __tablename__ = 'backtest_trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)

    # Trade details
    ticker = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL, TRIM
    signal_type = Column(String(20), nullable=False)  # PRIMARY, HIDDEN, LOSER

    # Prices and returns
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime, nullable=True)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)

    # Context
    reason = Column(Text, nullable=False)
    news_headline = Column(String(500), nullable=True)

    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_trade_ticker', 'ticker'),
        Index('idx_backtest_trade_entry_date', 'entry_date'),
        Index('idx_backtest_trade_signal_type', 'signal_type'),
    )

    def __repr__(self):
        return f"<BacktestTrade(id={self.id}, ticker='{self.ticker}', return={self.return_pct:.1f}%)>"


class SignalPerformance(Base):
    """시그널 실제 성과 추적 (Production)"""
    __tablename__ = 'signal_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey('trading_signals.id'), nullable=False)

    # Performance tracking
    evaluation_date = Column(DateTime, nullable=False)  # When we checked the outcome
    days_held = Column(Integer, nullable=False)  # How long we held the position

    actual_return_pct = Column(Float, nullable=False)

    # Market context
    spy_return_pct = Column(Float, nullable=True)  # S&P 500 benchmark
    sector_return_pct = Column(Float, nullable=True)  # Sector benchmark

    # Alpha calculation
    alpha = Column(Float, nullable=True)  # Outperformance vs SPY

    # Classification
    outcome = Column(String(20), nullable=False)  # WIN, LOSS, NEUTRAL

    # Indexes
    __table_args__ = (
        Index('idx_signal_perf_signal_id', 'signal_id'),
        Index('idx_signal_perf_evaluation_date', 'evaluation_date'),
        Index('idx_signal_perf_outcome', 'outcome'),
    )

    def __repr__(self):
        return f"<SignalPerformance(signal_id={self.signal_id}, return={self.actual_return_pct:.1f}%, outcome='{self.outcome}')>"


# ============================================
# Utility Functions
# ============================================

def create_all_tables(engine):
    """모든 테이블 생성"""
    Base.metadata.create_all(engine)
    print("[DB] All tables created successfully")


def drop_all_tables(engine):
    """모든 테이블 삭제 (주의: 데이터 손실!)"""
    Base.metadata.drop_all(engine)
    print("[DB] All tables dropped")


# TimescaleDB Hypertable 설정
TIMESCALEDB_HYPERTABLES = [
    ("news_articles", "crawled_at"),
    ("analysis_results", "analyzed_at"),
    ("trading_signals", "generated_at"),
    ("backtest_runs", "executed_at"),
    ("signal_performance", "evaluation_date"),
]


def setup_timescaledb_hypertables(connection):
    """
    TimescaleDB hypertable 변환

    Note: TimescaleDB extension이 활성화된 PostgreSQL 필요
    """
    for table_name, time_column in TIMESCALEDB_HYPERTABLES:
        try:
            sql = f"SELECT create_hypertable('{table_name}', '{time_column}', if_not_exists => TRUE);"
            connection.execute(sql)
            print(f"[TimescaleDB] Created hypertable: {table_name} (time_column: {time_column})")
        except Exception as e:
            print(f"[WARNING] Failed to create hypertable {table_name}: {e}")
            print("  This is normal if TimescaleDB extension is not installed")
