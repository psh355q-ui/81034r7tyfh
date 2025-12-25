"""
models.py - SQLAlchemy 데이터베이스 모델

📊 Data Sources:
    - PostgreSQL (TimescaleDB): 시계열 최적화 DB
        - Hypertables: news_articles, trading_signals, backtest_runs, etc.
        - pgvector: 임베딩 검색 (뉴스 semantic search)
    - 외부 시스템 연동:
        - News: RSS crawler, NewsAPI → NewsArticle
        - Signals: War Room, Deep Reasoning → TradingSignal
        - Orders: KIS Broker → Order
        - Backtest: SignalBacktestEngine → BacktestRun, BacktestTrade
        - Dividend: Yahoo Finance → DividendAristocrat (연 1회 갱신)

🔗 External Dependencies:
    - SQLAlchemy: ORM 프레임워크
    - pgvector: 벡터 유사도 검색
    - TimescaleDB: 시계열 데이터 압축 및 집계

📤 Database Models (16 classes):
    1. NewsArticle: RSS 뉴스 (embedding, sentiment, tickers)
    2. AnalysisResult: Deep Reasoning 분석 (bull/bear case)
    3. TradingSignal: 매매 시그널 (PRIMARY/HIDDEN/LOSER, 출처 추적)
    4. BacktestRun: 백테스트 실행 (Sharpe, Max DD, 수익률)
    5. BacktestTrade: 백테스트 개별 거래
    6. SignalPerformance: 실제 시그널 성과 (alpha, outcome)
    7. AIDebateSession: War Room 토론 기록 (9 agents vote)
    8. GroundingSearchLog: Grounding API 비용 추적
    9. GroundingDailyUsage: 일일 Grounding 사용량
    10. StockPrice: OHLCV 주가 데이터
    11. DataCollectionProgress: 데이터 수집 작업 진행률
    12. NewsSource: 뉴스 소스 설정
    13. Order: 실제 주문 실행 기록 (KIS Broker)
    14. DividendAristocrat: 배당 귀족주 캐시 (연 1회 갱신)

🔄 Imported By (참조가 가장 많음):
    - backend/api/*.py: 모든 API 라우터
    - backend/services/*.py: 모든 서비스
    - backend/data/*.py: 데이터 수집기
    - backend/scripts/*.py: 마이그레이션 스크립트
    - backend/analysis/*.py: 분석 엔진

📝 Notes:
    - TimescaleDB Hypertables: 시계열 데이터 자동 파티션닝
    - pgvector Vector(1536): OpenAI embedding 차원
    - JSONB: 메타데이터 유연한 저장
    - Relationships: SQLAlchemy ORM 관계 설정
    - Indexes: 쿼리 성능 최적화 (GIN, BTREE)
    - Phase 16+: 지속적 확장 중
    - DividendAristocrat: 매년 3월 1일 갱신 권장

Database: TimescaleDB (PostgreSQL with time-series extensions)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector
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

    # NLP & Embedding Fields (Added in Phase 17)
    embedding = Column(ARRAY(Float), nullable=True)  # Fallback: ARRAY(Float)
    tags = Column(ARRAY(String), nullable=True)
    tickers = Column(ARRAY(String), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    source_category = Column(String(50), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True) # mapped to 'metadata' column
    processed_at = Column(DateTime, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    # Relationships
    analyses = relationship("AnalysisResult", back_populates="article", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_news_published_date', 'published_date'),
        Index('idx_news_source', 'source'),
        Index('idx_news_crawled_at', 'crawled_at'),
        Index('idx_news_tickers', 'tickers', postgresql_using='gin'),
        Index('idx_news_tags', 'tags', postgresql_using='gin'),
        # Vector index would be created via migration, rarely defined in model for basic sync usage
        # Index('idx_news_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_with={'lists': 100}),
    )

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"


class AnalysisResult(Base):
    """Deep Reasoning 분석 결과"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False)
    ticker = Column(String(10), nullable=False, index=True)
    reasoning_theme = Column(String(200), nullable=True)
    bull_case = Column(Text, nullable=True)
    bear_case = Column(Text, nullable=True)
    final_verdict = Column(String(10), nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    article = relationship("NewsArticle", back_populates="analyses")

    # Indexes
    __table_args__ = (
        Index('idx_analysis_ticker', 'ticker'),
        Index('idx_analysis_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, ticker='{self.ticker}', verdict='{self.final_verdict}', conf={self.confidence_score})>"


class TradingSignal(Base):
    """트레이딩 시그널 (War Room, Deep Reasoning, Manual, News)"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    signal_type = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    
    # Optional fields
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    entry_price = Column(Float, nullable=True)
    shares = Column(Integer, nullable=True)
    alert_sent = Column(Boolean, default=False)
    
    # Metadata
    news_title = Column(String(500), nullable=True)
    news_source = Column(String(100), nullable=True)
    analysis_theme = Column(String(200), nullable=True)
    
    # Source tracking
    source = Column(String(50), nullable=False, default='unknown')

    # Indexes
    __table_args__ = (
        Index('idx_signal_ticker', 'ticker'),
        Index('idx_signal_type', 'signal_type'),
        Index('idx_signal_created_at', 'created_at'),
        Index('idx_signal_source', 'source'),
    )

    def __repr__(self):
        return f"<TradingSignal(id={self.id}, ticker='{self.ticker}', action='{self.action}', type='{self.signal_type}', conf={self.confidence})>"


class BacktestRun(Base):
    """백테스트 실행 결과"""
    __tablename__ = 'backtest_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='PENDING')
    
    # Configuration
    config = Column(JSONB, nullable=False)
    
    # Results
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_status', 'status'),
        Index('idx_backtest_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<BacktestRun(id={self.id}, name='{self.name}', status='{self.status}')>"


class BacktestTrade(Base):
    """백테스트 개별 거래"""
    __tablename__ = 'backtest_trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)
    ticker = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    shares = Column(Integer, nullable=False)
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)

    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_trade_run', 'backtest_run_id'),
        Index('idx_backtest_trade_ticker', 'ticker'),
    )

    def __repr__(self):
        return f"<BacktestTrade(id={self.id}, ticker='{self.ticker}', action='{self.action}', pnl={self.pnl})>"


class SignalPerformance(Base):
    """시그널 성과 추적"""
    __tablename__ = 'signal_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey('trading_signals.id'), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    outcome = Column(String(20), nullable=True)
    exit_reason = Column(String(50), nullable=True)
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime, nullable=True)
    holding_days = Column(Integer, nullable=True)
    alpha = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_signal_performance_signal', 'signal_id'),
        Index('idx_signal_performance_outcome', 'outcome'),
    )

    def __repr__(self):
        return f"<SignalPerformance(id={self.id}, signal_id={self.signal_id}, outcome='{self.outcome}', pnl={self.pnl})>"


class AIDebateSession(Base):
    """War Room AI 토론 세션"""
    __tablename__ = 'ai_debate_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    debate_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Votes
    votes = Column(JSONB, nullable=False)
    weighted_result = Column(String(10), nullable=True)
    consensus_confidence = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_debate_ticker', 'ticker'),
        Index('idx_debate_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AIDebateSession(id={self.id}, ticker='{self.ticker}', result='{self.weighted_result}')>"


class GroundingSearchLog(Base):
    """Grounding API 검색 로그"""
    __tablename__ = 'grounding_search_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    result_count = Column(Integer, nullable=False, default=0)
    search_date = Column(DateTime, nullable=False, default=datetime.now, index=True)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    response_time_ms = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_grounding_date', 'search_date'),
    )

    def __repr__(self):
        return f"<GroundingSearchLog(id={self.id}, query='{self.query[:50]}...', cost=${self.estimated_cost})>"


class GroundingDailyUsage(Base):
    """Grounding API 일일 사용량"""
    __tablename__ = 'grounding_daily_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    search_count = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)

    # Indexes
    __table_args__ = (
        Index('idx_grounding_daily_date', 'date'),
    )

    def __repr__(self):
        return f"<GroundingDailyUsage(date={self.date}, searches={self.search_count}, cost=${self.total_cost})>"


class StockPrice(Base):
    """주가 데이터 (OHLCV)"""
    __tablename__ = 'stock_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted_close = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_stock_price_ticker', 'ticker'),
        Index('idx_stock_price_date', 'date'),
        Index('idx_stock_price_ticker_date', 'ticker', 'date'),
    )

    def __repr__(self):
        return f"<StockPrice(ticker='{self.ticker}', date={self.date}, close={self.close})>"


class DataCollectionProgress(Base):
    """데이터 수집 진행 상태"""
    __tablename__ = 'data_collection_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default='pending')
    progress_pct = Column(Float, nullable=False, default=0.0)
    items_processed = Column(Integer, nullable=False, default=0)
    items_total = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<DataCollectionProgress(task='{self.task_name}', status='{self.status}', progress={self.progress_pct}%)>"


class NewsSource(Base):
    """뉴스 소스 설정"""
    __tablename__ = 'news_sources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    url = Column(String(1000), nullable=False)
    source_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_crawled = Column(DateTime, nullable=True)
    crawl_interval_minutes = Column(Integer, nullable=False, default=60)
    metadata_ = Column("metadata", JSONB, nullable=True)

    def __repr__(self):
        return f"<NewsSource(name='{self.name}', type='{self.source_type}', active={self.is_active})>"


class Order(Base):
    """실제 주문 실행 기록 (KIS Broker)"""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_type = Column(String(20), nullable=False, default='market')
    limit_price = Column(Float, nullable=True)
    filled_price = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    order_id = Column(String(100), nullable=True, unique=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    filled_at = Column(DateTime, nullable=True)
    signal_id = Column(Integer, ForeignKey('trading_signals.id'), nullable=True)
    error_message = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_order_ticker', 'ticker'),
        Index('idx_order_status', 'status'),
        Index('idx_order_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, ticker='{self.ticker}', action='{self.action}', quantity={self.quantity}, status='{self.status}')>"


class DividendAristocrat(Base):
    """
    배당 귀족주 캐시 테이블
    
    연 1회 갱신 (매년 3월 1일 권장)
    - S&P 배당 귀족주 리스트: 1월 말~2월 초 발표
    - 기업 배당금 확정: 2월 중순~3월 초
    
    Used By:
        - backend/api/dividend_router.py: /aristocrats endpoint
    """
    __tablename__ = "dividend_aristocrats"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    consecutive_years = Column(Integer, nullable=False, default=0)
    total_years = Column(Integer, nullable=False, default=0)
    current_yield = Column(Float, nullable=False, default=0.0)
    growth_rate = Column(Float, nullable=False, default=0.0)  # 평균 연간 증가율 (%)
    last_dividend = Column(Float, nullable=False, default=0.0)
    
    # 메타데이터
    analyzed_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Indexes
    __table_args__ = (
        Index('idx_aristocrat_ticker', 'ticker'),
        Index('idx_aristocrat_consecutive_years', 'consecutive_years'),
        Index('idx_aristocrat_sector', 'sector'),
    )
    
    def __repr__(self):
        return f"<DividendAristocrat {self.ticker}: {self.consecutive_years} years>"
