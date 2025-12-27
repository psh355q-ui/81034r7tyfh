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

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, ForeignKey, Index, BigInteger, Numeric, UniqueConstraint, JSON
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
    author = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)

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
    analysis_id = Column(Integer, ForeignKey('analysis_results.id'), nullable=True)
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
    debate_transcript = Column(JSONB, nullable=True)  # Full debate transcript with reasoning
    consensus_action = Column(String(10), nullable=True)  # BUY/SELL/HOLD
    consensus_confidence = Column(Float, nullable=True)
    constitutional_valid = Column(Boolean, nullable=True)  # Constitutional 검증 결과
    signal_id = Column(Integer, nullable=True)  # Trading signal ID

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
        return f"<AIDebateSession(id={self.id}, ticker='{self.ticker}', result='{self.consensus_action}')>"


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
    time = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted_close = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_stock_price_ticker', 'ticker'),
        Index('idx_stock_price_time', 'time'),
        Index('idx_stock_price_ticker_time', 'ticker', 'time'),
    )

    def __repr__(self):
        return f"<StockPrice(ticker='{self.ticker}', time={self.time}, close={self.close})>"


class DataCollectionProgress(Base):
    """데이터 수집 진행 상태"""
    __tablename__ = 'data_collection_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=True, index=True)  # Changed to nullable since we may use different identifiers
    source = Column(String(50), nullable=False, index=True)  # 데이터 소스 (multi_source, yfinance, etc.)
    collection_type = Column(String(50), nullable=False, index=True)  # 수집 타입 (news, prices, etc.)
    status = Column(String(20), nullable=False, default='pending')
    progress_pct = Column(Float, nullable=False, default=0.0)
    items_processed = Column(Integer, nullable=False, default=0)
    items_total = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)  # 수집 시작 날짜
    end_date = Column(DateTime, nullable=True)  # 수집 종료 날짜
    job_metadata = Column(JSONB, nullable=True)  # 작업 메타데이터
    started_at = Column(DateTime, nullable=True)  # 작업 시작 시간
    completed_at = Column(DateTime, nullable=True)  # 작업 완료 시간
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_data_collection_source', 'source'),
        Index('idx_data_collection_type', 'collection_type'),
        Index('idx_data_collection_status', 'status'),
    )

    def __repr__(self):
        return f"<DataCollectionProgress(source='{self.source}', type='{self.collection_type}', status='{self.status}', progress={self.progress_pct}%)>"


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


class DividendHistory(Base):
    """배당 이력 데이터"""
    __tablename__ = 'dividend_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    ex_dividend_date = Column(Date, nullable=False, index=True)
    payment_date = Column(Date, nullable=True)
    amount = Column(Numeric(10, 4), nullable=False)
    frequency = Column(String(20), nullable=True)  # Monthly, Quarterly, Annual
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Indexes
    __table_args__ = (
        Index('ix_dividend_history_ticker', 'ticker'),
        Index('ix_dividend_history_ex_dividend_date', 'ex_dividend_date'),
        # Unique constraint for ticker + ex_dividend_date
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<DividendHistory(ticker='{self.ticker}', ex_date={self.ex_dividend_date}, amount={self.amount})>"


class DividendAristocrat(Base):
    """
    배당 귀족주 (25년+ 연속 배당 증가)
    
    Phase 21: Dividend Intelligence Module
    
    연 1회 갱신 권장: 매년 3월 1일
    - S&P 배당 귀족주 리스트: 1월 말~2월 초 발표
    - 기업 배당금 확정: 2월 중순~3월 초
    
    Data Sources:
        - Yahoo Finance API (배당 이력, 재무 데이터)
        - S&P Dividend Aristocrats list
    
    Used By:
        - backend/api/dividend_router.py: /aristocrats endpoint
        - backend/core/models/dividend_models.py: Original schema definition
    """
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
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<DividendAristocrat(ticker={self.ticker}, company={self.company_name}, years={self.consecutive_years})>"


class PriceTracking(Base):
    """가격 추적 및 성과 평가 (24h)"""
    __tablename__ = 'price_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=True)
    ticker = Column(String(20), nullable=False, index=True)
    initial_price = Column(Float, nullable=False)
    initial_timestamp = Column(DateTime, nullable=False, default=datetime.now)
    consensus_action = Column(String(10), nullable=False)
    consensus_confidence = Column(Float, nullable=False)
    
    # Evaluation Results
    final_price = Column(Float, nullable=True)
    final_timestamp = Column(DateTime, nullable=True)
    price_change = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    performance_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default='PENDING', index=True)
    evaluated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_price_tracking_status_time', 'status', 'initial_timestamp'),
    )


class AgentVoteTracking(Base):
    """에이전트별 투표 성과 추적"""
    __tablename__ = 'agent_vote_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=True)
    agent_name = Column(String(50), nullable=False, index=True)
    vote_action = Column(String(10), nullable=False)
    vote_confidence = Column(Float, nullable=False)
    ticker = Column(String(20), nullable=False, index=True)
    initial_price = Column(Float, nullable=False)
    initial_timestamp = Column(DateTime, nullable=False, default=datetime.now)
    
    # Evaluation Results
    final_price = Column(Float, nullable=True)
    final_timestamp = Column(DateTime, nullable=True)
    price_change = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    performance_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default='PENDING', index=True)
    evaluated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_agent_vote_status_time', 'status', 'initial_timestamp'),
        Index('idx_agent_vote_name', 'agent_name'),
    )


class NewsAnalysis(Base):
    """AI 분석 결과"""
    __tablename__ = "news_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), unique=True)
    
    # Sentiment
    sentiment_overall = Column(String(32))  # positive | negative | neutral | mixed
    sentiment_score = Column(Float)  # -1.0 ~ 1.0
    sentiment_confidence = Column(Float)  # 0.0 ~ 1.0
    
    # Tone Analysis
    tone_objective_score = Column(Float)  # 0.0 (객관) ~ 1.0 (주관)
    urgency = Column(String(32))  # low | medium | high | critical
    sensationalism = Column(Float)  # 0.0 ~ 1.0
    
    # Market Impact
    market_impact_short = Column(String(32))  # bullish | bearish | neutral | uncertain
    market_impact_long = Column(String(32))
    impact_magnitude = Column(Float)  # 0.0 ~ 1.0
    affected_sectors = Column(JSONB)  # List[str]
    
    # Key Findings
    key_facts = Column(JSONB)  # List[str]
    key_opinions = Column(JSONB)  # List[str]
    key_implications = Column(JSONB)  # List[str]
    key_warnings = Column(JSONB)  # List[str]
    
    # Indirect Expressions
    indirect_expressions = Column(JSONB)  # List[dict]
    red_flags = Column(JSONB)  # List[str]
    
    # Trading Relevance
    trading_actionable = Column(Boolean, default=False)
    risk_category = Column(String(64))  # legal | regulatory | operational | financial | strategic | none
    recommendation = Column(Text)
    
    # Credibility
    source_reliability = Column(Float)  # 0.0 ~ 1.0
    data_backed = Column(Boolean)
    multiple_sources_cited = Column(Boolean)
    potential_bias = Column(String(256))
    
    # Model Info
    model_used = Column(String(64))
    tokens_used = Column(Integer)
    analysis_cost = Column(Float, default=0.0)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    article = relationship("NewsArticle", back_populates="analysis")
    
    __table_args__ = (
        Index('idx_sentiment_overall', 'sentiment_overall'),
        Index('idx_trading_actionable', 'trading_actionable'),
        Index('idx_risk_category', 'risk_category'),
    )


class NewsTickerRelevance(Base):
    """뉴스-티커 연관성"""
    __tablename__ = "news_ticker_relevance"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"))
    ticker = Column(String(16), nullable=False, index=True)
    
    relevance_score = Column(Float)  # 0.0 ~ 1.0
    sentiment_for_ticker = Column(Float)  # -1.0 ~ 1.0
    mention_count = Column(Integer, default=1)
    
    # Relationship
    article = relationship("NewsArticle", back_populates="ticker_relevances")
    
    __table_args__ = (
        Index('idx_ticker', 'ticker'),
        Index('idx_relevance', 'relevance_score'),
    )


class Relationship(Base):
    """지식 그래프 관계 (Triplets)"""
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False, index=True)
    relation = Column(String, nullable=False, index=True)
    object = Column(String, nullable=False, index=True)
    
    evidence_text = Column(Text)
    source = Column(String)
    date = Column(Date, default=datetime.utcnow)
    
    # pgvector embedding (1536 dim for OpenAI text-embedding-3-small)
    embedding = Column(Vector(1536))
    
    confidence = Column(Float, default=0.8)
    verified_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('subject', 'relation', 'object', name='uq_subject_relation_object'),
        Index('idx_rel_active', 'is_active'),
    )
