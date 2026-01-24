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

📤 Database Models (49 classes):
    1. NewsArticle: RSS 뉴스 (embedding, sentiment, tickers, Market Intelligence v2.0 fields)
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
    13. Order: 실제 주문 실행 기록 (KIS Broker, strategy_id 추가)
    14. DividendAristocrat: 배당 귀족주 캐시 (연 1회 갱신)
    ...
    35. Strategy: 전략 레지스트리 (멀티 전략 오케스트레이션)
    36. PositionOwnership: 포지션 소유권 추적 (충돌 방지)
    37. ConflictLog: 전략 간 충돌 로그 (AI 설명 가능성)
    38. UserFeedback: 사용자 피드백
    39. NarrativeState: 내러티브 상태 추적 (Market Intelligence v2.0)
    40. MarketConfirmation: 시장 확인 로그 (Market Intelligence v2.0)
    41. NarrativeFatigue: 내러티브 피로도 (Market Intelligence v2.0)
    42. ContrarySignal: 역발상 시그널 (Market Intelligence v2.0)
    43. HorizonTag: 시간축 태깅 (Market Intelligence v2.0)
    44. PolicyFeasibility: 정책 실현 확률 (Market Intelligence v2.0)
    45. InsightReview: 인사이트 사후 분석 (Market Intelligence v2.0)
    46. UserFeedbackIntelligence: 사용자 피드백 (Market Intelligence v2.0)
    47. PromptVersion: 프롬프트 버전 관리 (Market Intelligence v2.0)
    48. GeneratedChart: 생성된 차트 로그 (Market Intelligence v2.0)
    49. ... (existing models)

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

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, ForeignKey, Index, BigInteger, Numeric, UniqueConstraint, JSON, text
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

    # GLM-4.7 뉴스 해석 결과 (Added in Phase 0)
    glm_analysis = Column(JSONB, nullable=True)  # GLM 분석 결과: tickers, sectors, confidence, reasoning

    # Market Intelligence v2.0 Fields (Added in Phase 0, T0.1)
    # Narrative tracking (ChatGPT P0)
    narrative_phase = Column(String(20), nullable=True)  # EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING
    narrative_strength = Column(Float, nullable=True)     # 0.0 ~ 1.0
    narrative_consensus = Column(Float, nullable=True)    # 0.0 ~ 1.0

    # Fact verification (Gemini P0)
    fact_verification_status = Column(String(20), nullable=True)  # VERIFIED, PARTIAL, MISMATCH, UNVERIFIED
    fact_confidence_adjustment = Column(Float, default=0.0)       # -0.2 ~ +0.1

    # Market confirmation (ChatGPT P0)
    price_correlation_score = Column(Float, nullable=True)  # -1.0 ~ 1.0
    confirmation_status = Column(String(20), nullable=True)  # CONFIRMED, DIVERGENT, LEADING, NOISE

    # Enhanced tagging
    narrative_tags = Column(ARRAY(String), nullable=True)   # Fact vs Narrative tags
    horizon_tags = Column(ARRAY(String), nullable=True)     # SHORT, MEDIUM, LONG

    # Relationships
    analyses = relationship("AnalysisResult", back_populates="article", cascade="all, delete-orphan")
    analysis = relationship("NewsAnalysis", back_populates="article", uselist=False, cascade="all, delete-orphan")
    ticker_relevances = relationship("NewsTickerRelevance", back_populates="article", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_news_published_date', 'published_date'),
        Index('idx_news_source', 'source'),
        Index('idx_news_crawled_at', 'crawled_at'),
        Index('idx_news_tickers', 'tickers', postgresql_using='gin'),
        Index('idx_news_tags', 'tags', postgresql_using='gin'),
        # Phase 1 Optimization: 복합 인덱스
        Index('idx_news_ticker_date', 'tickers', 'published_date'),  # 티커별 뉴스 조회
        Index('idx_news_processed', 'published_date', postgresql_where='processed_at IS NOT NULL'),  # 처리된 뉴스만
        # Market Intelligence v2.0 Indexes (Phase 0, T0.1)
        Index('idx_news_narrative_phase', 'narrative_phase', postgresql_where='narrative_phase IS NOT NULL'),
        Index('idx_news_fact_status', 'fact_verification_status', postgresql_where='fact_verification_status IS NOT NULL'),
        Index('idx_news_confirmation_status', 'confirmation_status', postgresql_where='confirmation_status IS NOT NULL'),
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
        # Phase 1 Optimization: 복합 인덱스
        Index('idx_signal_ticker_date', 'ticker', 'created_at'),  # 티커별 최신 신호
        Index('idx_signal_pending_alert', 'ticker', postgresql_where='alert_sent = FALSE'),  # 대기 중 알림
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
    ticker = Column(String(50), nullable=True)
    query = Column(Text, nullable=False)
    result_count = Column(Integer, nullable=False, default=0)
    search_date = Column(DateTime, nullable=False, default=datetime.now, index=True)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    response_time_ms = Column(Integer, nullable=True)
    emergency_trigger = Column(String(255), nullable=True)
    was_emergency = Column(Boolean, default=False)
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
        # Phase 1 Optimization: 최신 가격 조회용 DESC 인덱스
        Index('idx_stock_ticker_time_desc', 'ticker', 'time', postgresql_ops={'time': 'DESC'}),
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


class RSSFeed(Base):
    """RSS 피드 설정 (뉴스 크롤러용)"""
    __tablename__ = 'rss_feeds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    url = Column(String(2048), nullable=False)
    category = Column(String(64))  # global | korea | sector_specific
    enabled = Column(Boolean, nullable=False, default=True)

    # Stats
    last_fetched = Column(DateTime, nullable=True)
    total_articles = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_rss_feed_enabled', 'enabled'),
        Index('idx_rss_feed_category', 'category'),
    )

    def __repr__(self):
        return f"<RSSFeed(id={self.id}, name='{self.name}', category='{self.category}', enabled={self.enabled})>"


# MacroSnapshot은 MacroContextSnapshot의 별칭 (호환성 유지)
# 실제 클래스는 아래 Accountability System Models 섹션에 정의됨
# MacroSnapshot = MacroContextSnapshot (런타임에 할당됨)


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
    filled_quantity = Column(Integer, nullable=True)  # Added for partial fills
    status = Column(String(20), nullable=False, default='idle')  # Changed default to 'idle'
    order_id = Column(String(100), nullable=True, unique=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # Added for state machine
    filled_at = Column(DateTime, nullable=True)
    signal_id = Column(Integer, ForeignKey('trading_signals.id'), nullable=True)
    error_message = Column(Text, nullable=True)
    order_metadata = Column(JSONB, nullable=True)  # Added for flexible metadata storage (renamed from 'metadata' to avoid SQLAlchemy conflict)
    needs_manual_review = Column(Boolean, nullable=False, default=False)  # Added for recovery logic

    # Multi-Strategy Orchestration (Phase 0, T0.2)
    strategy_id = Column(String(36), ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True, index=True)
    conflict_check_passed = Column(Boolean, nullable=False, default=False)
    conflict_reasoning = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_order_ticker', 'ticker'),
        Index('idx_order_status', 'status'),
        Index('idx_order_created_at', 'created_at'),
        Index('idx_orders_strategy_id', 'strategy_id'),
        Index('idx_orders_strategy_status', 'strategy_id', 'status'),
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


class EconomicEvent(Base):
    """
    경제 지표 이벤트 (v2.2)
    
    Phase 3.5: Real-time Economic Watcher
    
    Data Sources:
        - Investing.com Economic Calendar 크롤링
        - FMP API 백업 (선택적)
    
    Features:
        - 발표 시간까지 대기 (asyncio.sleep)
        - 발표 +10초 후 Actual 값 수집
        - 예상(Forecast) vs 실제(Actual) 괴리(Surprise) 계산
        - 즉시 알림 + 브리핑 Context 주입
    
    Importance Levels:
        - ★★★: GDP, PCE, CPI, 고용지표, FOMC 회의록
        - ★★: EIA 재고, 주택지표, PMI
        - ★: 기타 참고 지표
    """
    __tablename__ = "economic_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(200), nullable=False)  # 예: "미국 3분기 실질 GDP"
    country = Column(String(10), nullable=False)      # US, KR, EU, CN, JP
    category = Column(String(50), nullable=False)     # GDP, Inflation, Employment, etc.
    
    event_time = Column(DateTime, nullable=False, index=True)  # 발표 예정 시간 (KST)
    importance = Column(Integer, nullable=False)      # 1=★, 2=★★, 3=★★★
    
    # 데이터 값
    forecast = Column(String(50), nullable=True)      # 예상치 (4.3%)
    actual = Column(String(50), nullable=True)        # 실제치 (발표 후 업데이트)
    previous = Column(String(50), nullable=True)      # 이전치
    
    # Surprise 분석
    surprise_pct = Column(Float, nullable=True)      # (실제-예상)/예상 * 100
    impact_direction = Column(String(20), nullable=True)  # Bullish/Bearish/Neutral
    impact_score = Column(Integer, nullable=True)        # 영향도 점수 (0-100)
    
    # 처리 상태
    is_processed = Column(Boolean, default=False)    # 처리 완료 여부
    processed_at = Column(DateTime, nullable=True)      # 처리 완료 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)              # 추가 메모
    updated_at = Column(DateTime, nullable=True)       # 업데이트 시간
    
    # Indexes
    __table_args__ = (
        Index('idx_economic_event_time', 'event_time'),
        Index('idx_economic_importance', 'importance'),
        Index('idx_economic_processed', 'is_processed'),
    )
    
    def __repr__(self):
        return f"<EconomicEvent(id={self.id}, name='{self.event_name}', time={self.event_time}, importance={self.importance})>"
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


class DeepReasoningAnalysis(Base):
    """Deep Reasoning 분석 이력 (3-Step CoT 추론 결과)"""
    __tablename__ = "deep_reasoning_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_text = Column(Text, nullable=False)
    theme = Column(String(500), nullable=False)

    # Primary Beneficiary
    primary_beneficiary_ticker = Column(String(20), nullable=True, index=True)
    primary_beneficiary_action = Column(String(10), nullable=True)
    primary_beneficiary_confidence = Column(Float, nullable=True)
    primary_beneficiary_reasoning = Column(Text, nullable=True)

    # Hidden Beneficiary
    hidden_beneficiary_ticker = Column(String(20), nullable=True, index=True)
    hidden_beneficiary_action = Column(String(10), nullable=True)
    hidden_beneficiary_confidence = Column(Float, nullable=True)
    hidden_beneficiary_reasoning = Column(Text, nullable=True)

    # Loser
    loser_ticker = Column(String(20), nullable=True)
    loser_action = Column(String(10), nullable=True)
    loser_confidence = Column(Float, nullable=True)
    loser_reasoning = Column(Text, nullable=True)

    # Analysis Results
    bull_case = Column(Text, nullable=False)
    bear_case = Column(Text, nullable=False)
    reasoning_trace = Column(JSONB, nullable=False)

    # Metadata
    model_used = Column(String(50), nullable=False, index=True)
    processing_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)


# ====================================
# Accountability System Models
# Phase 1 (Week 1-2) - Added 2025-12-29
# ====================================

class MacroContextSnapshot(Base):
    """거시 경제 상황 스냅샷 - 매일 갱신되는 시장 체제 정보"""
    __tablename__ = "macro_context_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, unique=True)
    regime = Column(String(30), nullable=False)  # RISK_ON, RISK_OFF, ROTATION, UNCERTAINTY
    fed_stance = Column(String(20), nullable=False)  # HAWKISH, DOVISH, NEUTRAL
    vix_level = Column(Numeric(6, 2), nullable=True)
    vix_category = Column(String(20), nullable=True)  # LOW, NORMAL, ELEVATED, HIGH, EXTREME
    sector_rotation = Column(String(50), nullable=True)
    dominant_narrative = Column(Text, nullable=True)
    geopolitical_risk = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW
    earnings_season = Column(Boolean, nullable=True, default=False)
    market_sentiment = Column(String(20), nullable=True)  # EXTREME_FEAR, FEAR, NEUTRAL, GREED, EXTREME_GREED
    sp500_trend = Column(String(20), nullable=True)  # STRONG_UPTREND, UPTREND, SIDEWAYS, DOWNTREND, STRONG_DOWNTREND
    snapshot_metadata = Column(JSONB, nullable=True)  # Additional flexible metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Relationships
    interpretations = relationship("NewsInterpretation", back_populates="macro_context")

    __table_args__ = (
        Index('idx_macro_snapshot_date', 'snapshot_date'),
        Index('idx_macro_regime', 'regime', 'fed_stance'),
        Index('idx_macro_vix', 'vix_category'),
        Index('idx_macro_sentiment', 'market_sentiment'),
    )

    def __repr__(self):
        return f"<MacroContextSnapshot(date={self.snapshot_date}, regime='{self.regime}', fed='{self.fed_stance}')>"


class NewsInterpretation(Base):
    """AI의 뉴스 해석 저장 - War Room 실행 중 News Agent가 생성"""
    __tablename__ = "news_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_article_id = Column(Integer, ForeignKey('news_articles.id', ondelete='CASCADE'), nullable=True)
    ticker = Column(String(20), nullable=False)
    headline_bias = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    expected_impact = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    time_horizon = Column(String(20), nullable=False)  # IMMEDIATE, INTRADAY, MULTI_DAY
    confidence = Column(Integer, nullable=False)  # 0-100
    reasoning = Column(Text, nullable=False)
    macro_context_id = Column(Integer, ForeignKey('macro_context_snapshots.id', ondelete='SET NULL'), nullable=True)
    interpreted_at = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    news_article = relationship("NewsArticle")
    macro_context = relationship("MacroContextSnapshot", back_populates="interpretations")
    market_reaction = relationship("NewsMarketReaction", back_populates="interpretation", uselist=False)
    decision_links = relationship("NewsDecisionLink", back_populates="interpretation")
    narratives = relationship("NewsNarrative", back_populates="interpretation")
    failure_analyses = relationship("FailureAnalysis", back_populates="interpretation")

    __table_args__ = (
        Index('idx_interpretation_news_article', 'news_article_id'),
        Index('idx_interpretation_ticker', 'ticker'),
        Index('idx_interpretation_date', 'interpreted_at'),
        Index('idx_interpretation_impact', 'expected_impact', 'headline_bias'),
    )

    def __repr__(self):
        return f"<NewsInterpretation(id={self.id}, ticker='{self.ticker}', bias='{self.headline_bias}', impact='{self.expected_impact}')>"


class NewsMarketReaction(Base):
    """뉴스 후 실제 시장 반응 검증 - AI 해석의 정확도 측정"""
    __tablename__ = "news_market_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interpretation_id = Column(Integer, ForeignKey('news_interpretations.id', ondelete='CASCADE'), nullable=False, unique=True)
    ticker = Column(String(20), nullable=False)
    price_at_news = Column(Numeric(12, 2), nullable=True)  # Fixed: nullable=True to match DB
    price_1h_after = Column(Numeric(12, 2), nullable=True)  # Fixed: NUMERIC(12,2) instead of Float
    price_1d_after = Column(Numeric(12, 2), nullable=True)  # Fixed: NUMERIC(12,2) instead of Float
    price_3d_after = Column(Numeric(12, 2), nullable=True)  # Fixed: NUMERIC(12,2) instead of Float
    actual_price_change_1h = Column(Numeric(8, 4), nullable=True)  # Fixed: NUMERIC(8,4) instead of Float
    actual_price_change_1d = Column(Numeric(8, 4), nullable=True)  # Fixed: NUMERIC(8,4) instead of Float
    actual_price_change_3d = Column(Numeric(8, 4), nullable=True)  # Fixed: NUMERIC(8,4) instead of Float
    interpretation_correct = Column(Boolean, nullable=True)
    confidence_justified = Column(Boolean, nullable=True)  # Fixed: Boolean instead of Float
    magnitude_accuracy = Column(Numeric(4, 2), nullable=True)  # Fixed: NUMERIC(4,2) instead of Float
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Accountability System 컬럼 (Phase 29)
    news_at = Column(DateTime, nullable=True)  # 뉴스 발생 시각
    price_change_1h = Column(Numeric(8, 4), nullable=True)  # 1시간 후 가격 변화율 (%)
    price_change_1d = Column(Numeric(8, 4), nullable=True)  # 1일 후 가격 변화율 (%)
    price_change_3d = Column(Numeric(8, 4), nullable=True)  # 3일 후 가격 변화율 (%)
    accuracy_1h = Column(Numeric(4, 2), nullable=True)  # 1시간 예측 정확도 (0.0~1.0)
    accuracy_1d = Column(Numeric(4, 2), nullable=True)  # 1일 예측 정확도 (0.0~1.0)
    accuracy_3d = Column(Numeric(4, 2), nullable=True)  # 3일 예측 정확도 (0.0~1.0)
    verified_at_1h = Column(DateTime, nullable=True)  # 1시간 검증 완료 시각
    verified_at_1d = Column(DateTime, nullable=True)  # 1일 검증 완료 시각
    verified_at_3d = Column(DateTime, nullable=True)  # 3일 검증 완료 시각

    # Relationships
    interpretation = relationship("NewsInterpretation", back_populates="market_reaction")

    __table_args__ = (
        Index('idx_reaction_interpretation', 'interpretation_id'),
        Index('idx_reaction_ticker', 'ticker'),
        Index('idx_reaction_verified', 'verified_at'),
        Index('idx_reaction_correctness', 'interpretation_correct', 'confidence_justified'),
    )

    def __repr__(self):
        return f"<NewsMarketReaction(id={self.id}, ticker='{self.ticker}', correct={self.interpretation_correct})>"


class NewsDecisionLink(Base):
    """뉴스 → 해석 → 의사결정 → 결과 연결 - Accountability Chain"""
    __tablename__ = "news_decision_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interpretation_id = Column(Integer, ForeignKey('news_interpretations.id', ondelete='CASCADE'), nullable=False)
    debate_session_id = Column(Integer, ForeignKey('ai_debate_sessions.id', ondelete='SET NULL'), nullable=True)
    trading_signal_id = Column(Integer, ForeignKey('trading_signals.id', ondelete='SET NULL'), nullable=True)
    ticker = Column(String(20), nullable=False)
    final_decision = Column(String(10), nullable=True)  # BUY, SELL, HOLD
    decision_outcome = Column(String(20), nullable=True, default='PENDING')  # SUCCESS, FAILURE, PENDING
    profit_loss = Column(Numeric(12, 2), nullable=True)
    news_influence_weight = Column(Numeric(4, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    outcome_verified_at = Column(DateTime, nullable=True)

    # Relationships
    interpretation = relationship("NewsInterpretation", back_populates="decision_links")
    debate_session = relationship("AIDebateSession")
    trading_signal = relationship("TradingSignal")
    failure_analyses = relationship("FailureAnalysis", back_populates="decision_link")

    __table_args__ = (
        Index('idx_link_interpretation', 'interpretation_id'),
        Index('idx_link_debate_session', 'debate_session_id'),
        Index('idx_link_trading_signal', 'trading_signal_id'),
        Index('idx_link_ticker', 'ticker'),
        Index('idx_link_outcome', 'decision_outcome', 'final_decision'),
    )

    def __repr__(self):
        return f"<NewsDecisionLink(id={self.id}, ticker='{self.ticker}', decision='{self.final_decision}', outcome='{self.decision_outcome}')>"


class NewsNarrative(Base):
    """리포트에 사용된 문장 추적 - 리포트 정확도 측정용"""
    __tablename__ = "news_narratives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False)
    report_type = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, QUARTERLY, HALF_YEARLY, ANNUAL
    page_number = Column(Integer, nullable=True)
    section = Column(String(50), nullable=True)
    narrative_text = Column(Text, nullable=False)
    interpretation_id = Column(Integer, ForeignKey('news_interpretations.id', ondelete='SET NULL'), nullable=True)
    ticker = Column(String(20), nullable=True)
    claim_type = Column(String(30), nullable=True)  # PREDICTION, ANALYSIS, OBSERVATION, RECOMMENDATION
    accuracy_score = Column(Numeric(4, 2), nullable=True)
    verified = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    interpretation = relationship("NewsInterpretation", back_populates="narratives")

    __table_args__ = (
        Index('idx_narrative_report_date', 'report_date', 'report_type'),
        Index('idx_narrative_interpretation', 'interpretation_id'),
        Index('idx_narrative_ticker', 'ticker'),
        Index('idx_narrative_claim_type', 'claim_type', 'verified'),
        Index('idx_narrative_accuracy', 'accuracy_score'),
    )

    def __repr__(self):
        return f"<NewsNarrative(id={self.id}, report_date={self.report_date}, type='{self.report_type}', claim='{self.claim_type}')>"


class FailureAnalysis(Base):
    """실패 분석 및 학습 저장소 - AI가 틀렸던 판단에 대한 사후 분석"""
    __tablename__ = "failure_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interpretation_id = Column(Integer, ForeignKey('news_interpretations.id', ondelete='SET NULL'), nullable=True)
    decision_link_id = Column(Integer, ForeignKey('news_decision_links.id', ondelete='SET NULL'), nullable=True)
    ticker = Column(String(20), nullable=False)
    failure_type = Column(String(50), nullable=False)  # WRONG_DIRECTION, WRONG_MAGNITUDE, WRONG_TIMING, WRONG_CONFIDENCE, MISSED_SIGNAL, FALSE_POSITIVE
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    expected_outcome = Column(Text, nullable=True)
    actual_outcome = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=False)
    lesson_learned = Column(Text, nullable=False)
    recommended_fix = Column(Text, nullable=False)
    fix_applied = Column(Boolean, nullable=True, default=False)
    fix_description = Column(Text, nullable=True)
    fix_effective = Column(Boolean, nullable=True)
    rag_context_updated = Column(Boolean, nullable=True, default=False)
    analyzed_by = Column(String(50), nullable=True, default='failure_learning_agent')
    analyzed_at = Column(DateTime, nullable=True, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    # Relationships
    interpretation = relationship("NewsInterpretation", back_populates="failure_analyses")
    decision_link = relationship("NewsDecisionLink", back_populates="failure_analyses")

    __table_args__ = (
        Index('idx_failure_interpretation', 'interpretation_id'),
        Index('idx_failure_decision_link', 'decision_link_id'),
        Index('idx_failure_ticker', 'ticker'),
        Index('idx_failure_type_severity', 'failure_type', 'severity'),
        Index('idx_failure_fix_status', 'fix_applied', 'fix_effective'),
        Index('idx_failure_analyzed_at', 'analyzed_at'),
    )

    def __repr__(self):
        return f"<FailureAnalysis(id={self.id}, ticker='{self.ticker}', type='{self.failure_type}', severity='{self.severity}')>"


class AgentWeightsHistory(Base):
    """Agent 가중치 조정 이력 (Failure Learning)"""
    __tablename__ = 'agent_weights_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    changed_at = Column(DateTime, nullable=False, server_default='NOW()')
    changed_by = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    trader_agent = Column(Numeric(5, 4), nullable=False)
    risk_agent = Column(Numeric(5, 4), nullable=False)
    analyst_agent = Column(Numeric(5, 4), nullable=False)
    macro_agent = Column(Numeric(5, 4), nullable=False)
    institutional_agent = Column(Numeric(5, 4), nullable=False)
    news_agent = Column(Numeric(5, 4), nullable=False)
    chip_war_agent = Column(Numeric(5, 4), nullable=False)
    dividend_risk_agent = Column(Numeric(5, 4), nullable=False)
    pm_agent = Column(Numeric(5, 4), nullable=False)
    
    __table_args__ = (
        Index('idx_agent_weights_changed_at', 'changed_at', postgresql_using='btree'),
    )
    
    def __repr__(self):
        return f"<AgentWeightsHistory(id={self.id}, changed_at={self.changed_at}, changed_by='{self.changed_by}')>"


class DailyBriefing(Base):
    """
    Daily Briefing - AI Generated Daily Market Report
    
    Generates a comprehensive market summary including:
    - Pre-market Gap Analysis (KIS/yfinance)
    - Dark Pool & Options Flow (OptionsDataFetcher)
    - Sector Rotation Analysis (SectorRotationAnalyzer)
    - Market Sentiment (NewsPoller)
    - Earnings Calendar (EarningsCalendarService)
    - Macro Economic Events (EconomicCalendarService)
    
    Used by:
    - DailyBriefingService
    - Frontend Dashboard (Briefing Tab)
    """
    __tablename__ = "daily_briefings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)  # Markdown content
    
    # Structured Data for Charts/Analytics
    metrics = Column(JSONB, nullable=True)
    # Expected structure:
    # {
    #   "gap_up_count": 12,
    #   "gap_down_count": 5,
    #   "leading_sector": "Technology",
    #   "market_sentiment": "Fear",
    #   "vix_close": 18.5
    # }
    
    # v2.2: Caching Fields (70% API Cost Reduction)
    cache_key = Column(String(200), nullable=True)  # Cache key (e.g., "briefing_2026-01-23")
    cache_hit = Column(Boolean, default=False)  # Cache hit (true if cached, false if regenerated)
    cache_ttl = Column(Integer, default=86400)  # Cache TTL in seconds (24 hours)
    importance_score = Column(Integer, nullable=True)  # Importance score (0-100) based on market volatility
    economic_events_count = Column(Integer, default=0)  # Number of economic events included
    sector_rotation_score = Column(Float, nullable=True)  # Sector rotation score (-1.0 to 1.0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_daily_briefing_date', 'date'),
        Index('idx_daily_briefing_cache_key', 'cache_key'),
        Index('idx_daily_briefing_cache_hit', 'cache_hit'),
    )
    
    def __repr__(self):
        return f"<DailyBriefing(date={self.date}, id={self.id})>"


class WeeklyReport(Base):
    """
    Weekly Report - AI Generated Weekly Market Analysis
    
    Generates a weekly market analysis including:
    - Weekly performance summary
    - Sector rotation analysis
    - Economic events impact
    - Market sentiment trends
    - Trading signal performance
    
    Used by:
    - WeeklyReportService
    - Frontend Dashboard (Weekly Tab)
    """
    __tablename__ = "weekly_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(Date, nullable=False, index=True)  # Week start date (Monday)
    week_end = Column(Date, nullable=False, index=True)    # Week end date (Sunday)
    content = Column(Text, nullable=False)  # Markdown content
    
    # Structured Data for Charts/Analytics
    metrics = Column(JSONB, nullable=True)
    # Expected structure:
    # {
    #   "weekly_return": 2.5,
    #   "best_performing_sector": "Technology",
    #   "worst_performing_sector": "Energy",
    #   "economic_events_count": 5,
    #   "high_importance_events_count": 2,
    #   "market_sentiment_trend": "Improving",
    #   "signals_generated": 12,
    #   "signals_won": 7,
    #   "signals_lost": 5
    # }
    
    # v2.2: Caching Fields (70% API Cost Reduction)
    cache_key = Column(String(200), nullable=True)  # Cache key (e.g., "weekly_report_2026-W03")
    cache_hit = Column(Boolean, default=False)  # Cache hit (true if cached, false if regenerated)
    cache_ttl = Column(Integer, default=604800)  # Cache TTL in seconds (7 days)
    
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_weekly_report_week_start', 'week_start'),
        Index('idx_weekly_report_week_end', 'week_end'),
        Index('idx_weekly_report_cache_key', 'cache_key'),
        Index('idx_weekly_report_cache_hit', 'cache_hit'),
    )
    
    def __repr__(self):
        return f"<WeeklyReport(week_start={self.week_start}, id={self.id})>"


class UserFeedback(Base):
    """사용자가 AI 리포트/시그널에 대해 남긴 피드백"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=True)  # Optional (Login not fully implemented yet)
    target_type = Column(String(50), nullable=False) # 'report', 'signal', 'briefing'
    target_id = Column(String(100), nullable=False)  # identifier of the target
    feedback_type = Column(String(20), nullable=False) # 'like', 'dislike'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_feedback_target', 'target_type', 'target_id'),
    )

    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type={self.target_type}, feedback={self.feedback_type})>"


# ====================================
# Multi-Strategy Orchestration Models
# Phase 0, Task T0.2
# ====================================

class Strategy(Base):
    """전략 레지스트리 - 멀티 전략 오케스트레이션을 위한 전략 메타데이터"""
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    persona_type = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False)
    time_horizon = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    config_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, server_default="NOW()")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now, server_default="NOW()")

    # Relationships
    position_ownerships = relationship("PositionOwnership", back_populates="strategy", foreign_keys="PositionOwnership.strategy_id")
    conflicting_logs = relationship("ConflictLog", back_populates="conflicting_strategy", foreign_keys="ConflictLog.conflicting_strategy_id")
    owning_logs = relationship("ConflictLog", back_populates="owning_strategy", foreign_keys="ConflictLog.owning_strategy_id")

    __table_args__ = (
        Index('idx_strategies_name', 'name', unique=True),
        Index('idx_strategies_priority', 'priority', postgresql_ops={'priority': 'DESC'}),
        Index('idx_strategies_active', 'is_active', postgresql_where="is_active = true"),
    )

    def __repr__(self):
        return f"<Strategy(name={self.name}, priority={self.priority}, active={self.is_active})>"


class PositionOwnership(Base):
    """포지션 소유권 추적 - 어떤 전략이 어떤 포지션을 소유하는지 관리"""
    __tablename__ = "position_ownership"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()"))
    position_id = Column(String(36), nullable=True)  # FK 추후 연결 (positions 테이블 미구현)
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="RESTRICT"), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    ownership_type = Column(String(20), nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, server_default="NOW()")

    # Relationships
    strategy = relationship("Strategy", back_populates="position_ownerships", foreign_keys=[strategy_id], lazy="joined")
    conflict_logs = relationship("ConflictLog", back_populates="ownership", foreign_keys="ConflictLog.ownership_id")

    __table_args__ = (
        Index('idx_ownership_position', 'position_id'),
        Index('idx_ownership_strategy', 'strategy_id'),
        Index('idx_ownership_ticker', 'ticker'),
        Index('idx_ownership_ticker_strategy', 'ticker', 'strategy_id'),
        Index('idx_ownership_locked', 'locked_until', postgresql_where=text("locked_until IS NOT NULL")),
        Index('uk_ownership_primary_ticker', 'ticker', unique=True, postgresql_where=text("ownership_type = 'primary'")),
    )

    def __repr__(self):
        return f"<PositionOwnership(ticker={self.ticker}, strategy={self.strategy_id}, type={self.ownership_type})>"


class ConflictLog(Base):
    """충돌 로그 - 전략 간 충돌 발생 이력 및 해결 방법 기록"""
    __tablename__ = "conflict_logs"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()"))
    ticker = Column(String(50), nullable=False, index=True)
    conflicting_strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    owning_strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    action_attempted = Column(String(50), nullable=False)
    action_blocked = Column(Boolean, nullable=False)
    resolution = Column(String(50), nullable=False)
    reasoning = Column(Text, nullable=False)
    conflicting_strategy_priority = Column(Integer, nullable=True)
    owning_strategy_priority = Column(Integer, nullable=True)
    order_id = Column(String(100), nullable=True)
    ownership_id = Column(String(36), ForeignKey("position_ownership.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, server_default="NOW()")

    # Relationships
    conflicting_strategy = relationship("Strategy", back_populates="conflicting_logs", foreign_keys=[conflicting_strategy_id])
    owning_strategy = relationship("Strategy", back_populates="owning_logs", foreign_keys=[owning_strategy_id])
    ownership = relationship("PositionOwnership", back_populates="conflict_logs", foreign_keys=[ownership_id])

    __table_args__ = (
        Index('idx_conflict_ticker', 'ticker'),
        Index('idx_conflict_created_at', 'created_at', postgresql_ops={'created_at': 'DESC'}),
        Index('idx_conflict_conflicting_strategy', 'conflicting_strategy_id'),
        Index('idx_conflict_owning_strategy', 'owning_strategy_id'),
        Index('idx_conflict_resolution', 'resolution', 'action_blocked'),
        Index('idx_conflict_ticker_date', 'ticker', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

    def __repr__(self):
        return f"<ConflictLog(ticker={self.ticker}, resolution={self.resolution}, blocked={self.action_blocked})>"


# ====================================
# Market Intelligence v2.0 Models
# Phase 0, Task T0.1 - Added 2026-01-18
# Reference: docs/planning/260118_market_intelligence_roadmap.md
# ====================================

class NarrativeState(Base):
    """내러티브 상태 추적 - 팩트와 내러티브를 분리하여 추적 (ChatGPT P0)"""
    __tablename__ = "narrative_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(50), nullable=False, index=True)
    fact_layer = Column(Text, nullable=True)
    narrative_layer = Column(Text, nullable=True)
    market_expectation = Column(Text, nullable=True)
    expectation_gap = Column(Float, nullable=True)
    phase = Column(String(20), nullable=True, index=True)
    change_velocity = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_narrative_states_topic', 'topic'),
        Index('idx_narrative_states_phase', 'phase'),
        Index('idx_narrative_states_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NarrativeState(id={self.id}, topic='{self.topic}', phase='{self.phase}')>"


class MarketConfirmation(Base):
    """시장 확인 로그 - 뉴스 강도와 시장 반응 교차 검증 (ChatGPT P0)"""
    __tablename__ = "market_confirmations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme = Column(String(50), nullable=False, index=True)
    news_intensity = Column(Float, nullable=True)
    price_momentum = Column(Float, nullable=True)
    volume_anomaly = Column(Float, nullable=True)
    signal = Column(String(20), nullable=True, index=True)
    divergence_score = Column(Float, nullable=True)
    proxy_tickers = Column(ARRAY(String), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_market_confirmations_theme', 'theme'),
        Index('idx_market_confirmations_signal', 'signal'),
        Index('idx_market_confirmations_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<MarketConfirmation(id={self.id}, theme='{self.theme}', signal='{self.signal}')>"


class NarrativeFatigue(Base):
    """내러티브 피로도 - 테마 과열/피크 탐지 (ChatGPT P1)"""
    __tablename__ = "narrative_fatigue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme = Column(String(50), nullable=False, index=True)
    fatigue_score = Column(Float, nullable=True)
    signal = Column(String(20), nullable=True, index=True)
    mention_growth = Column(Float, nullable=True)
    price_response = Column(Float, nullable=True)
    new_info_ratio = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_narrative_fatigue_theme', 'theme'),
        Index('idx_narrative_fatigue_signal', 'signal'),
        Index('idx_narrative_fatigue_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NarrativeFatigue(id={self.id}, theme='{self.theme}', signal='{self.signal}')>"


class ContrarySignal(Base):
    """역발상 시그널 - 시장 쏠림/과열 경고 (ChatGPT P1)"""
    __tablename__ = "contrary_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme = Column(String(50), nullable=False, index=True)
    crowding_level = Column(String(20), nullable=True, index=True)
    contrarian_signal = Column(String(30), nullable=True)
    indicators = Column(JSONB, nullable=True, server_default="'{}'::jsonb")
    reasoning = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_contrary_signals_theme', 'theme'),
        Index('idx_contrary_signals_crowding', 'crowding_level'),
        Index('idx_contrary_signals_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ContrarySignal(id={self.id}, theme='{self.theme}', crowding='{self.crowding_level}')>"


class HorizonTag(Base):
    """시간축 태깅 - 인사이트를 투자 기간별로 분리 (ChatGPT P1)"""
    __tablename__ = "horizon_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_article_id = Column(Integer, ForeignKey('news_articles.id', ondelete='SET NULL'), nullable=True, index=True)
    short_term = Column(Text, nullable=True)
    mid_term = Column(Text, nullable=True)
    long_term = Column(Text, nullable=True)
    recommended_horizon = Column(String(10), nullable=True, index=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_horizon_tags_article_id', 'news_article_id'),
        Index('idx_horizon_tags_horizon', 'recommended_horizon'),
        Index('idx_horizon_tags_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<HorizonTag(id={self.id}, article_id={self.news_article_id}, horizon='{self.recommended_horizon}')>"


class PolicyFeasibility(Base):
    """정책 실현 확률 - 정책 발언의 실현 가능성 분석 (ChatGPT P2)"""
    __tablename__ = "policy_feasibility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_name = Column(String(255), nullable=False, index=True)
    feasibility_score = Column(Float, nullable=True, index=True)
    factors = Column(JSONB, nullable=True, server_default="'{}'::jsonb")
    risks = Column(ARRAY(String), nullable=True)
    reasoning = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_policy_feasibility_name', 'policy_name'),
        Index('idx_policy_feasibility_score', 'feasibility_score'),
        Index('idx_policy_feasibility_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<PolicyFeasibility(id={self.id}, policy='{self.policy_name}', score={self.feasibility_score})>"


class InsightReview(Base):
    """인사이트 사후 분석 - 예측 정확도 추적 및 학습 (ChatGPT+Gemini P2)"""
    __tablename__ = "insight_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_id = Column(Integer, nullable=False, index=True)
    insight_type = Column(String(50), nullable=True)
    predicted_direction = Column(String(20), nullable=True)
    actual_outcome_7d = Column(Float, nullable=True)
    actual_outcome_30d = Column(Float, nullable=True)
    success = Column(Boolean, nullable=True, index=True)
    accuracy_score = Column(Float, nullable=True)
    failure_reason = Column(Text, nullable=True)
    lesson_learned = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    reviewed_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_insight_reviews_insight_id', 'insight_id'),
        Index('idx_insight_reviews_success', 'success'),
        Index('idx_insight_reviews_reviewed_at', 'reviewed_at'),
    )

    def __repr__(self):
        return f"<InsightReview(id={self.id}, insight_id={self.insight_id}, success={self.success})>"


class UserFeedbackIntelligence(Base):
    """사용자 피드백 - 액티브 러닝을 위한 피드백 수집 (Gemini P2)"""
    __tablename__ = "user_feedback_intelligence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_id = Column(Integer, nullable=True, index=True)
    insight_type = Column(String(50), nullable=True)
    feedback_type = Column(String(20), nullable=True, index=True)
    user_comment = Column(Text, nullable=True)
    corrected_data = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_user_feedback_intelligence_insight_id', 'insight_id'),
        Index('idx_user_feedback_intelligence_type', 'feedback_type'),
        Index('idx_user_feedback_intelligence_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<UserFeedbackIntelligence(id={self.id}, insight_id={self.insight_id}, type='{self.feedback_type}')>"


class PromptVersion(Base):
    """프롬프트 버전 관리 - A/B 테스트 및 최적화 (Gemini P2)"""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    prompt_text = Column(Text, nullable=False)
    performance_score = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_prompt_versions_name', 'prompt_name'),
        Index('idx_prompt_versions_active', 'is_active', postgresql_where=text("is_active = true")),
        Index('idx_prompt_versions_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<PromptVersion(id={self.id}, name='{self.prompt_name}', version={self.version}, active={self.is_active})>"


class GeneratedChart(Base):
    """생성된 차트 로그 - 시각화 자동 생성 추적 (Gemini P1)"""
    __tablename__ = "generated_charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chart_type = Column(String(50), nullable=True, index=True)
    chart_title = Column(String(255), nullable=True)
    parameters = Column(JSONB, nullable=True, server_default="'{}'::jsonb")
    file_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="'{}'::jsonb")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_generated_charts_type', 'chart_type'),
        Index('idx_generated_charts_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<GeneratedChart(id={self.id}, type='{self.chart_type}', title='{self.chart_title}')>"


# ====================================
# AI Trade Decisions (v2.3)
# ====================================

class AITradeDecision(Base):
    """
    AI 트레이딩 프로토콜 결정 - v2.3

    ChatGPT/Gemini 합의 기반 JSON 프로토콜 저장
    - Closing/Morning 모드 지원
    - 자동매매/백테스트 연동
    - Human-in-the-loop 체크포인트
    """
    __tablename__ = "ai_trade_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 핵심 메타데이터 (인덱싱용)
    mode = Column(String(20), nullable=False, index=True)  # CLOSING, MORNING, INTRADAY, KOREAN
    execution_intent = Column(String(20), nullable=False, index=True)  # AUTO, HUMAN_APPROVAL
    market_trend = Column(String(10), nullable=True, index=True)  # UP, SIDE, DOWN
    risk_level = Column(String(10), nullable=True, index=True)  # LOW, MEDIUM, HIGH
    risk_score = Column(Integer, nullable=True)  # 0-100

    # 전체 JSON 데이터
    full_report_json = Column(JSONB, nullable=False)

    # 백테스트용 (JSON에서 추출)
    target_asset = Column(String(50), nullable=True, index=True)
    suggested_action = Column(String(20), nullable=True)
    suggested_size_pct = Column(Numeric(5, 4), nullable=True)  # -1.0000 ~ 1.0000
    expected_rr_ratio = Column(Numeric(5, 2), nullable=True)  # 기대 손익비

    # 사후 검증용 (트레이딩 후 업데이트)
    actual_profit_loss = Column(Numeric(12, 2), nullable=True)
    is_strategy_correct = Column(Boolean, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(Text, nullable=True)

    # 버전 관리
    model_version = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=True, default='v2.3')

    # 연관 브리핑
    briefing_file_path = Column(String(255), nullable=True)

    # 감사
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_ai_decisions_created_at', 'created_at'),
        Index('idx_ai_decisions_mode', 'mode'),
        Index('idx_ai_decisions_intent', 'execution_intent'),
        Index('idx_ai_decisions_risk', 'risk_level'),
        Index('idx_ai_decisions_trend', 'market_trend'),
        Index('idx_ai_decisions_asset', 'target_asset'),
    )

    def __repr__(self):
        return f"<AITradeDecision(id={self.id}, mode='{self.mode}', intent='{self.execution_intent}', risk='{self.risk_level}')>"


# ====================================
# Aliases for backward compatibility
# ====================================
# MacroSnapshot은 MacroContextSnapshot의 별칭 (기존 코드 호환성 유지)
MacroSnapshot = MacroContextSnapshot
