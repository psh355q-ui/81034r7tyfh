"""
from __future__ import annotations

Database Repository Layer

Repository pattern for data access:
- NewsRepository: News article CRUD
- AnalysisRepository: Analysis results storage
- SignalRepository: Trading signals management
- BacktestRepository: Backtest results tracking
- PerformanceRepository: Signal outcome evaluation

Usage:
    async with get_db_session() as session:
        news_repo = NewsRepository(session)
        article = await news_repo.create_article(...)
"""

from typing import List, Optional, Dict, Tuple, TYPE_CHECKING

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from contextlib import asynccontextmanager

from backend.database.models import (
    NewsArticle,
    AnalysisResult,
    TradingSignal,
    BacktestRun,
    BacktestTrade,
    SignalPerformance,
    StockPrice,
    DataCollectionProgress,
    NewsSource,
    PriceTracking,
    AgentVoteTracking,
    MacroContextSnapshot,
    NewsInterpretation,
    NewsMarketReaction,
    NewsDecisionLink,
    NewsNarrative,
    FailureAnalysis,
    DeepReasoningAnalysis
)

if TYPE_CHECKING:
    from backend.news.rss_crawler import NewsArticle as RSSNewsArticle
    from backend.ai.reasoning.deep_reasoning import DeepReasoningResult



class NewsRepository:
    """뉴스 기사 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create_article(self, article: RSSNewsArticle) -> NewsArticle:
        """
        RSS 크롤링 결과 저장

        Returns:
            NewsArticle ORM object
        """
        db_article = NewsArticle(
            title=article.title,
            content=article.content,
            url=article.url,
            source=article.source,
            published_date=article.published_date,
            crawled_at=datetime.now(),
            content_hash=article.content_hash
        )
        self.session.add(db_article)
        self.session.commit()
        self.session.refresh(db_article)
        return db_article

    def save_processed_article(self, article_data: Dict) -> NewsArticle:
        """
        NLP 처리된 뉴스 저장 (Embeddings 포함)
        
        Args:
            article_data: Dict from ProcessedNews.to_db_dict()
        """
        # Check existing hash first to avoid duplicates
        content_hash = article_data.get('content_hash')
        if content_hash:
            existing = self.session.query(NewsArticle).filter_by(content_hash=content_hash).first()
            if existing:
                return existing
        else:
             # Generated fallback hash if missing
             import hashlib
             slug = f"{article_data['title']}{article_data['url']}"
             content_hash = hashlib.md5(slug.encode()).hexdigest()

        db_article = NewsArticle(
            title=article_data['title'],
            content=article_data['content'],
            url=article_data['url'],
            source=article_data['source'],
            source_category=article_data.get('source_category'),
            published_date=article_data['published_at'],
            crawled_at=article_data.get('processed_at', datetime.now()),
            content_hash=content_hash,
            
            # Phase 3 Added Fields
            author=article_data.get('author'),
            summary=article_data.get('summary'),
            
            # New fields
            embedding=article_data.get('embedding'),
            sentiment_score=article_data.get('sentiment_score'),
            sentiment_label=article_data.get('sentiment_label'),
            tags=article_data.get('tags'),
            tickers=article_data.get('tickers'),
            embedding_model=article_data.get('embedding_model')
        )
        
        # Handle metadata JSONB
        if 'metadata' in article_data:
            db_article.metadata_ = article_data['metadata']

        self.session.add(db_article)
        try:
            self.session.commit()
            self.session.refresh(db_article)
        except Exception:
            self.session.rollback()
            # Double check race condition
            existing = self.session.query(NewsArticle).filter_by(content_hash=content_hash).first()
            if existing:
                return existing
            raise

        return db_article

    def get_by_hash(self, content_hash: str) -> Optional[NewsArticle]:
        """중복 체크: 해시로 기사 조회"""
        return self.session.query(NewsArticle).filter_by(content_hash=content_hash).first()

    def get_by_url(self, url: str) -> Optional[NewsArticle]:
        """URL로 기사 조회"""
        return self.session.query(NewsArticle).filter_by(url=url).first()

    def get_recent_articles(self, hours: int = 24, source: Optional[str] = None) -> List[NewsArticle]:
        """최근 N시간 내 기사 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        query = self.session.query(NewsArticle).filter(NewsArticle.crawled_at >= cutoff_time)

        if source:
            query = query.filter(NewsArticle.source == source)

        return query.order_by(desc(NewsArticle.published_date)).all()

    def count_by_source(self, start_date: datetime, end_date: datetime) -> List[Tuple[str, int]]:
        """소스별 기사 수 집계"""
        return (
            self.session.query(NewsArticle.source, func.count(NewsArticle.id))
            .filter(and_(
                NewsArticle.crawled_at >= start_date,
                NewsArticle.crawled_at <= end_date
            ))
            .group_by(NewsArticle.source)
            .all()
        )


class AnalysisRepository:
    """분석 결과 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create_analysis(
        self,
        article_id: int,
        result: DeepReasoningResult,
        model_name: str,
        duration_seconds: Optional[float] = None
    ) -> AnalysisResult:
        """
        Deep Reasoning 결과 저장

        Args:
            article_id: NewsArticle ID
            result: DeepReasoningResult from deep_reasoning.py
            model_name: AI model name (e.g., gemini-2.5-pro)
            duration_seconds: Analysis duration
        """
        db_analysis = AnalysisResult(
            article_id=article_id,
            analyzed_at=datetime.now(),
            model_name=model_name,
            analysis_duration_seconds=duration_seconds,
            theme=result.theme,
            bull_case=result.bull_case,
            bear_case=result.bear_case,
            step1_direct_impact=result.reasoning_trace.get('step1', '') if result.reasoning_trace else '',
            step2_secondary_impact=result.reasoning_trace.get('step2', '') if result.reasoning_trace else '',
            step3_conclusion=result.reasoning_trace.get('step3', '') if result.reasoning_trace else ''
        )
        self.session.add(db_analysis)
        self.session.commit()
        self.session.refresh(db_analysis)
        return db_analysis

    def get_by_id(self, analysis_id: int) -> Optional[AnalysisResult]:
        """분석 ID로 조회"""
        return self.session.query(AnalysisResult).filter_by(id=analysis_id).first()

    def get_recent_analyses(self, hours: int = 24) -> List[AnalysisResult]:
        """최근 N시간 내 분석 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return (
            self.session.query(AnalysisResult)
            .filter(AnalysisResult.analyzed_at >= cutoff_time)
            .order_by(desc(AnalysisResult.analyzed_at))
            .all()
        )

    def get_avg_analysis_duration(self) -> float:
        """평균 분석 시간 계산"""
        result = self.session.query(func.avg(AnalysisResult.analysis_duration_seconds)).scalar()
        return result if result else 0.0


class SignalRepository:
    """트레이딩 시그널 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create_signal(
        self,
        analysis_id: int,
        ticker: str,
        action: str,
        signal_type: str,
        confidence: float,
        reasoning: str,
        entry_price: Optional[float] = None
    ) -> TradingSignal:
        """
        시그널 생성 및 저장

        Args:
            analysis_id: AnalysisResult ID
            ticker: Stock ticker (e.g., NVDA)
            action: BUY, SELL, TRIM, HOLD
            signal_type: PRIMARY, HIDDEN, LOSER
            confidence: 0.0 ~ 1.0
            reasoning: Signal reasoning
            entry_price: Entry price if available
        """
        db_signal = TradingSignal(
            analysis_id=analysis_id,
            ticker=ticker,
            action=action,
            signal_type=signal_type,
            confidence=confidence,
            reasoning=reasoning,
            generated_at=datetime.now(),
            entry_price=entry_price,
            alert_sent=False
        )
        self.session.add(db_signal)
        self.session.commit()
        self.session.refresh(db_signal)
        return db_signal

    def mark_alert_sent(self, signal_id: int):
        """Alert 전송 완료 마킹"""
        signal = self.session.query(TradingSignal).filter_by(id=signal_id).first()
        if signal:
            signal.alert_sent = True
            signal.alert_sent_at = datetime.now()
            self.session.commit()

    def record_outcome(
        self,
        signal_id: int,
        exit_price: float,
        actual_return_pct: float
    ):
        """시그널 실제 성과 기록"""
        signal = self.session.query(TradingSignal).filter_by(id=signal_id).first()
        if signal:
            signal.exit_price = exit_price
            signal.actual_return_pct = actual_return_pct
            signal.outcome_recorded_at = datetime.now()
            self.session.commit()

    def get_recent_signals(
        self,
        hours: int = 24,
        signal_type: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[TradingSignal]:
        """최근 시그널 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        query = self.session.query(TradingSignal).filter(TradingSignal.generated_at >= cutoff_time)

        if signal_type:
            query = query.filter(TradingSignal.signal_type == signal_type)

        if min_confidence:
            query = query.filter(TradingSignal.confidence >= min_confidence)

        return query.order_by(desc(TradingSignal.generated_at)).all()

    def get_signals_pending_alert(self, min_confidence: float = 0.85) -> List[TradingSignal]:
        """Alert 미발송 시그널 조회"""
        return (
            self.session.query(TradingSignal)
            .filter(and_(
                TradingSignal.alert_sent == False,
                TradingSignal.confidence >= min_confidence
            ))
            .order_by(desc(TradingSignal.confidence))
            .all()
        )

    def count_by_type(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """시그널 타입별 집계"""
        results = (
            self.session.query(TradingSignal.signal_type, func.count(TradingSignal.id))
            .filter(and_(
                TradingSignal.generated_at >= start_date,
                TradingSignal.generated_at <= end_date
            ))
            .group_by(TradingSignal.signal_type)
            .all()
        )
        return {signal_type: count for signal_type, count in results}

    def get_top_tickers(self, days: int = 7, limit: int = 10) -> List[Tuple[str, int, float]]:
        """
        Top N 자주 언급된 종목

        Returns:
            List of (ticker, count, avg_confidence)
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        return (
            self.session.query(
                TradingSignal.ticker,
                func.count(TradingSignal.id).label('count'),
                func.avg(TradingSignal.confidence).label('avg_confidence')
            )
            .filter(TradingSignal.generated_at >= cutoff_time)
            .group_by(TradingSignal.ticker)
            .order_by(desc('count'))
            .limit(limit)
            .all()
        )


class BacktestRepository:
    """백테스트 결과 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create_backtest_run(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        win_rate: float,
        avg_return: float,
        total_return: float,
        sharpe_ratio: float,
        max_drawdown: float,
        hidden_beneficiaries_found: int = 0
    ) -> BacktestRun:
        """백테스트 실행 결과 저장"""
        db_backtest = BacktestRun(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            executed_at=datetime.now(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_return=avg_return,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            hidden_beneficiaries_found=hidden_beneficiaries_found
        )
        self.session.add(db_backtest)
        self.session.commit()
        self.session.refresh(db_backtest)
        return db_backtest

    def add_trade_to_backtest(
        self,
        backtest_run_id: int,
        ticker: str,
        action: str,
        signal_type: str,
        entry_date: datetime,
        entry_price: float,
        exit_date: Optional[datetime],
        exit_price: Optional[float],
        return_pct: Optional[float],
        reason: str,
        news_headline: Optional[str] = None
    ) -> BacktestTrade:
        """백테스트 개별 거래 기록"""
        db_trade = BacktestTrade(
            backtest_run_id=backtest_run_id,
            ticker=ticker,
            action=action,
            signal_type=signal_type,
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            return_pct=return_pct,
            reason=reason,
            news_headline=news_headline
        )
        self.session.add(db_trade)
        self.session.commit()
        self.session.refresh(db_trade)
        return db_trade

    def get_recent_backtests(self, limit: int = 10) -> List[BacktestRun]:
        """최근 백테스트 실행 조회"""
        return (
            self.session.query(BacktestRun)
            .order_by(desc(BacktestRun.executed_at))
            .limit(limit)
            .all()
        )

    def compare_strategies(
        self,
        strategy1: str,
        strategy2: str,
        days: int = 30
    ) -> Tuple[Optional[BacktestRun], Optional[BacktestRun]]:
        """전략 비교 (최근 N일 내 최신 결과)"""
        cutoff_time = datetime.now() - timedelta(days=days)

        run1 = (
            self.session.query(BacktestRun)
            .filter(and_(
                BacktestRun.strategy_name == strategy1,
                BacktestRun.executed_at >= cutoff_time
            ))
            .order_by(desc(BacktestRun.executed_at))
            .first()
        )

        run2 = (
            self.session.query(BacktestRun)
            .filter(and_(
                BacktestRun.strategy_name == strategy2,
                BacktestRun.executed_at >= cutoff_time
            ))
            .order_by(desc(BacktestRun.executed_at))
            .first()
        )

        return run1, run2

    def get_best_performing_strategy(self, days: int = 30) -> Optional[BacktestRun]:
        """최고 성과 전략 조회"""
        cutoff_time = datetime.now() - timedelta(days=days)
        return (
            self.session.query(BacktestRun)
            .filter(BacktestRun.executed_at >= cutoff_time)
            .order_by(desc(BacktestRun.sharpe_ratio))
            .first()
        )


class PerformanceRepository:
    """시그널 실제 성과 추적"""

    def __init__(self, session: Session):
        self.session = session

    def record_signal_performance(
        self,
        signal_id: int,
        evaluation_date: datetime,
        days_held: int,
        actual_return_pct: float,
        spy_return_pct: Optional[float] = None,
        sector_return_pct: Optional[float] = None
    ) -> SignalPerformance:
        """시그널 성과 기록"""
        # Calculate alpha
        alpha = None
        if spy_return_pct is not None:
            alpha = actual_return_pct - spy_return_pct

        # Classify outcome
        if actual_return_pct > 5.0:
            outcome = "WIN"
        elif actual_return_pct < -5.0:
            outcome = "LOSS"
        else:
            outcome = "NEUTRAL"

        db_perf = SignalPerformance(
            signal_id=signal_id,
            evaluation_date=evaluation_date,
            days_held=days_held,
            actual_return_pct=actual_return_pct,
            spy_return_pct=spy_return_pct,
            sector_return_pct=sector_return_pct,
            alpha=alpha,
            outcome=outcome
        )
        self.session.add(db_perf)
        self.session.commit()
        self.session.refresh(db_perf)
        return db_perf

    def get_win_rate_by_signal_type(self, days: int = 30) -> Dict[str, float]:
        """
        시그널 타입별 승률 계산

        Returns:
            {"PRIMARY": 0.75, "HIDDEN": 0.83, "LOSER": 0.60}
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        results = (
            self.session.query(
                TradingSignal.signal_type,
                func.count(SignalPerformance.id).label('total'),
                func.sum(
                    func.case(
                        (SignalPerformance.outcome == 'WIN', 1),
                        else_=0
                    )
                ).label('wins')
            )
            .join(SignalPerformance, TradingSignal.id == SignalPerformance.signal_id)
            .filter(SignalPerformance.evaluation_date >= cutoff_time)
            .group_by(TradingSignal.signal_type)
            .all()
        )

        win_rates = {}
        for signal_type, total, wins in results:
            win_rates[signal_type] = (wins / total) if total > 0 else 0.0

        return win_rates

    def get_avg_return_by_signal_type(self, days: int = 30) -> Dict[str, float]:
        """시그널 타입별 평균 수익률"""
        cutoff_time = datetime.now() - timedelta(days=days)

        results = (
            self.session.query(
                TradingSignal.signal_type,
                func.avg(SignalPerformance.actual_return_pct).label('avg_return')
            )
            .join(SignalPerformance, TradingSignal.id == SignalPerformance.signal_id)
            .filter(SignalPerformance.evaluation_date >= cutoff_time)
            .group_by(TradingSignal.signal_type)
            .all()
        )

        return {signal_type: avg_return for signal_type, avg_return in results}

    def get_hidden_beneficiary_outperformance(self, days: int = 30) -> Dict[str, float]:
        """
        Hidden beneficiary vs Primary 성과 비교

        Returns:
            {
                "hidden_avg": 17.4,
                "primary_avg": 5.9,
                "outperformance_ratio": 2.95
            }
        """
        avg_returns = self.get_avg_return_by_signal_type(days)

        hidden_avg = avg_returns.get("HIDDEN", 0.0)
        primary_avg = avg_returns.get("PRIMARY", 0.0)

        return {
            "hidden_avg": hidden_avg,
            "primary_avg": primary_avg,
            "outperformance_ratio": (hidden_avg / primary_avg) if primary_avg != 0 else 0.0
        }



class DataCollectionRepository:
    """Historical Data Collection Progress"""

    def __init__(self, session: Session):
        self.session = session

    def create_job(
        self,
        source: str,
        collection_type: str,
        start_date: datetime,
        end_date: datetime,
        metadata: Optional[Dict] = None
    ) -> DataCollectionProgress:
        """Create new progress tracking job"""
        job = DataCollectionProgress(
            source=source,
            collection_type=collection_type,
            start_date=start_date,
            end_date=end_date,
            job_metadata=metadata,
            status='pending'
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def update_progress(
        self,
        job_id: int,
        processed: int,
        failed: int = 0,
        total: Optional[int] = None,
        status: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update job progress"""
        job = self.session.query(DataCollectionProgress).filter_by(id=job_id).first()
        if job:
            job.processed_items = processed
            job.failed_items = failed
            if total is not None:
                job.total_items = total
            if status:
                job.status = status
                if status == 'running' and not job.started_at:
                    job.started_at = datetime.now()
                elif status in ['completed', 'failed']:
                    job.completed_at = datetime.now()
            if error:
                job.error_message = error
            self.session.commit()

    def get_active_jobs(self) -> List[DataCollectionProgress]:
        """Get currently running jobs"""
        return (
            self.session.query(DataCollectionProgress)
            .filter(DataCollectionProgress.status.in_(['pending', 'running']))
            .all()
        )

    def get_collected_news(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        ticker: Optional[str] = None,
        limit: int = 100
    ) -> List[NewsArticle]:
        """
        Get collected processed news from the specific progress
        (Using NewsArticle table directly which is shared)
        """
        query = self.session.query(NewsArticle)

        if start_date:
            query = query.filter(NewsArticle.published_date >= start_date)
        if end_date:
            query = query.filter(NewsArticle.published_date <= end_date)
        
        # Ticker filtering (using ANY operator for ARRAY column)
        if ticker:
            # Postgres ARRAY check: ticker = ANY(tickers)
            query = query.filter(NewsArticle.tickers.any(ticker))

        return query.order_by(desc(NewsArticle.published_date)).limit(limit).all()


class StockRepository:
    """Stock Price Data Repository"""

    def __init__(self, session: Session):
        self.session = session

    def save_prices(self, prices: List[Dict]):
        """
        Bulk save stock prices
        
        Args:
            prices: List of dicts matching StockPrice model fields
        """
        db_objects = []
        for p in prices:
            db_obj = StockPrice(
                ticker=p['ticker'],
                time=p.get('time') or p.get('date'),  # Map to 'time' column
                open=p['open'],
                high=p['high'],
                low=p['low'],
                close=p['close'],
                volume=p['volume'],
                adjusted_close=p.get('adjusted_close') or p.get('adj_close')
            )
            db_objects.append(db_obj)
            
        self.session.add_all(db_objects)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def get_prices(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[StockPrice]:
        """Get OHLCV data for ticker"""
        return (
            self.session.query(StockPrice)
            .filter(and_(
                StockPrice.ticker == ticker,
                StockPrice.date >= start_date,
                StockPrice.date <= end_date
            ))
            .order_by(StockPrice.date)
            .all()
        )


class DividendRepository:
    """Dividend History Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_dividend(
        self,
        ticker: str,
        ex_dividend_date,
        amount: float,
        frequency: Optional[str] = None,
        payment_date = None
    ):
        """
        Save or update dividend history
        
        Args:
            ticker: Stock ticker
            ex_dividend_date: Ex-dividend date
            amount: Dividend amount
            frequency: Payment frequency (Monthly, Quarterly, Annual)
            payment_date: Payment date
        """
        from sqlalchemy import update
        from backend.database.models import DividendHistory
        from decimal import Decimal
        
        # Check if exists
        existing = self.session.query(DividendHistory).filter(
            and_(
                DividendHistory.ticker == ticker,
                DividendHistory.ex_dividend_date == ex_dividend_date
            )
        ).first()
        
        if existing:
            # Update
            existing.amount = Decimal(str(amount))
            existing.frequency = frequency
            existing.payment_date = payment_date
            existing.updated_at = datetime.now()
        else:
            # Insert
            dividend = DividendHistory(
                ticker=ticker,
                ex_dividend_date=ex_dividend_date,
                payment_date=payment_date,
                amount=Decimal(str(amount)),
                frequency=frequency
            )
            self.session.add(dividend)
        
        self.session.commit()
    
    def get_upcoming_ex_dates(self, days: int = 3):
        """
        Get upcoming ex-dividend dates
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of dividend records
        """
        from backend.database.models import DividendHistory
        from datetime import date, timedelta
        
        today = date.today()
        target_date = today + timedelta(days=days)
        
        return (
            self.session.query(DividendHistory)
            .filter(and_(
                DividendHistory.ex_dividend_date >= today,
                DividendHistory.ex_dividend_date <= target_date
            ))
            .order_by(DividendHistory.ex_dividend_date, DividendHistory.ticker)
            .all()
        )
    
    def get_dividend_history(
        self,
        ticker: str,
        start_date=None,
        end_date=None
    ):
        """Get dividend history for a ticker"""
        from backend.database.models import DividendHistory
        
        query = self.session.query(DividendHistory).filter(
            DividendHistory.ticker == ticker
        )
        
        if start_date:
            query = query.filter(DividendHistory.ex_dividend_date >= start_date)
        if end_date:
            query = query.filter(DividendHistory.ex_dividend_date <= end_date)
        
        return query.order_by(DividendHistory.ex_dividend_date).all()


# ============================================
# Database Session Management
# ============================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed

# Database URL from environment
# Convert asyncpg URL to psycopg2 URL for SQLAlchemy sync engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_trading")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@asynccontextmanager
async def get_db_session():
    """
    Database session context manager

    Usage:
        async with get_db_session() as session:
            news_repo = NewsRepository(session)
            article = news_repo.create_article(...)
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

class TrackingRepository:
    """성과 추적 Repository (PriceTracking & AgentVoteTracking)"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_pending_price_tracking(self, hours_old: int = 24) -> List[PriceTracking]:
        """24시간 지난 대기 중인 가격 추적 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        return (
            self.session.query(PriceTracking)
            .filter(and_(
                PriceTracking.status == 'PENDING',
                PriceTracking.initial_timestamp <= cutoff_time
            ))
            .order_by(PriceTracking.initial_timestamp.asc())
            .all()
        )
        
    def get_pending_agent_votes(self, hours_old: int = 24) -> List[AgentVoteTracking]:
        """24시간 지난 대기 중인 에이전트 투표 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        return (
            self.session.query(AgentVoteTracking)
            .filter(and_(
                AgentVoteTracking.status == 'PENDING',
                AgentVoteTracking.initial_timestamp <= cutoff_time
            ))
            .order_by(AgentVoteTracking.initial_timestamp.asc())
            .all()
        )
    
    def update_evaluation(self, db_obj: object, result: Dict):
        """평가 결과 업데이트"""
        for key, value in result.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        db_obj.status = 'COMPLETED'
        db_obj.evaluated_at = datetime.now()
        
        self.session.add(db_obj)
        self.session.commit()
    
    def mark_failed(self, db_obj: object, error_message: str):
        """평가 실패 처리"""
        db_obj.status = 'FAILED'
        db_obj.notes = error_message
        db_obj.evaluated_at = datetime.now()
        
        self.session.add(db_obj)
        self.session.commit()


def get_sync_session():
    """
    Synchronous session (for non-async contexts)

    Usage:
        with get_sync_session() as session:
            news_repo = NewsRepository(session)
    """
    return SessionLocal()


# ====================================
# Accountability System Repositories
# Phase 1 (Week 1-2) - Added 2025-12-29
# ====================================

class MacroContextRepository:
    """거시 경제 컨텍스트 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> MacroContextSnapshot:
        """새로운 macro context 스냅샷 생성"""
        snapshot = MacroContextSnapshot(**data)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def get_by_date(self, snapshot_date) -> Optional[MacroContextSnapshot]:
        """특정 날짜의 macro context 조회"""
        return self.session.query(MacroContextSnapshot).filter(
            MacroContextSnapshot.snapshot_date == snapshot_date
        ).first()

    def get_latest(self) -> Optional[MacroContextSnapshot]:
        """가장 최근 macro context 조회"""
        return self.session.query(MacroContextSnapshot).order_by(
            desc(MacroContextSnapshot.snapshot_date)
        ).first()

    def get_by_date_range(self, start_date, end_date) -> List[MacroContextSnapshot]:
        """날짜 범위로 macro context 조회"""
        return self.session.query(MacroContextSnapshot).filter(
            and_(
                MacroContextSnapshot.snapshot_date >= start_date,
                MacroContextSnapshot.snapshot_date <= end_date
            )
        ).order_by(MacroContextSnapshot.snapshot_date.asc()).all()


class NewsInterpretationRepository:
    """뉴스 해석 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> NewsInterpretation:
        """새로운 뉴스 해석 생성"""
        interpretation = NewsInterpretation(**data)
        self.session.add(interpretation)
        self.session.commit()
        self.session.refresh(interpretation)
        return interpretation

    def get_by_id(self, interpretation_id: int) -> Optional[NewsInterpretation]:
        """ID로 해석 조회"""
        return self.session.query(NewsInterpretation).filter(
            NewsInterpretation.id == interpretation_id
        ).first()

    def get_by_news_article(self, news_article_id: int) -> List[NewsInterpretation]:
        """뉴스 기사 ID로 해석 조회"""
        return self.session.query(NewsInterpretation).filter(
            NewsInterpretation.news_article_id == news_article_id
        ).all()

    def get_by_ticker(self, ticker: str, limit: int = 10) -> List[NewsInterpretation]:
        """종목별 최근 해석 조회"""
        return self.session.query(NewsInterpretation).filter(
            NewsInterpretation.ticker == ticker
        ).order_by(desc(NewsInterpretation.interpreted_at)).limit(limit).all()

    def get_by_date_range(self, start_date, end_date) -> List[NewsInterpretation]:
        """날짜 범위로 해석 조회"""
        return self.session.query(NewsInterpretation).filter(
            and_(
                NewsInterpretation.interpreted_at >= start_date,
                NewsInterpretation.interpreted_at <= end_date
            )
        ).order_by(NewsInterpretation.interpreted_at.asc()).all()

    def get_high_impact_recent(self, hours: int = 24) -> List[NewsInterpretation]:
        """최근 HIGH impact 해석 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return self.session.query(NewsInterpretation).filter(
            and_(
                NewsInterpretation.expected_impact == 'HIGH',
                NewsInterpretation.interpreted_at >= cutoff_time
            )
        ).order_by(desc(NewsInterpretation.interpreted_at)).all()


class NewsMarketReactionRepository:
    """시장 반응 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> NewsMarketReaction:
        """새로운 시장 반응 생성"""
        reaction = NewsMarketReaction(**data)
        self.session.add(reaction)
        self.session.commit()
        self.session.refresh(reaction)
        return reaction

    def get_by_interpretation_id(self, interpretation_id: int) -> Optional[NewsMarketReaction]:
        """해석 ID로 반응 조회 (1:1 관계)"""
        return self.session.query(NewsMarketReaction).filter(
            NewsMarketReaction.interpretation_id == interpretation_id
        ).first()

    def update(self, reaction: NewsMarketReaction, data: Dict) -> NewsMarketReaction:
        """시장 반응 업데이트 (1h, 1d, 3d 후 가격)"""
        for key, value in data.items():
            if hasattr(reaction, key):
                setattr(reaction, key, value)
        self.session.commit()
        self.session.refresh(reaction)
        return reaction

    def get_pending_verifications(self, time_horizon: str = '1h') -> List[NewsMarketReaction]:
        """검증 대기 중인 반응 조회"""
        cutoff_hours = {'1h': 1, '1d': 24, '3d': 72}
        cutoff_time = datetime.now() - timedelta(hours=cutoff_hours.get(time_horizon, 1))

        if time_horizon == '1h':
            return self.session.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.price_1h_after.is_(None),
                    NewsMarketReaction.created_at <= cutoff_time
                )
            ).all()
        elif time_horizon == '1d':
            return self.session.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.price_1d_after.is_(None),
                    NewsMarketReaction.created_at <= cutoff_time
                )
            ).all()
        else:  # 3d
            return self.session.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.price_3d_after.is_(None),
                    NewsMarketReaction.created_at <= cutoff_time
                )
            ).all()

    def get_verified_reactions(self, start_date, end_date) -> List[NewsMarketReaction]:
        """검증 완료된 반응 조회"""
        return self.session.query(NewsMarketReaction).filter(
            and_(
                NewsMarketReaction.verified_at.isnot(None),
                NewsMarketReaction.verified_at >= start_date,
                NewsMarketReaction.verified_at <= end_date
            )
        ).all()

    def get_worst_failures(self, limit: int = 10) -> List[NewsMarketReaction]:
        """가장 틀린 판단 조회 (연간 리포트용)"""
        return self.session.query(NewsMarketReaction).filter(
            NewsMarketReaction.interpretation_correct == False
        ).order_by(NewsMarketReaction.confidence_justified.asc()).limit(limit).all()


class NewsDecisionLinkRepository:
    """의사결정 링크 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> NewsDecisionLink:
        """새로운 의사결정 링크 생성"""
        link = NewsDecisionLink(**data)
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def get_by_interpretation_id(self, interpretation_id: int) -> List[NewsDecisionLink]:
        """해석 ID로 링크 조회"""
        return self.session.query(NewsDecisionLink).filter(
            NewsDecisionLink.interpretation_id == interpretation_id
        ).all()

    def get_by_debate_session(self, debate_session_id: int) -> List[NewsDecisionLink]:
        """War Room 세션 ID로 링크 조회"""
        return self.session.query(NewsDecisionLink).filter(
            NewsDecisionLink.debate_session_id == debate_session_id
        ).all()

    def update_outcome(self, link: NewsDecisionLink, outcome: str, profit_loss: float) -> NewsDecisionLink:
        """의사결정 결과 업데이트"""
        link.decision_outcome = outcome
        link.profit_loss = profit_loss
        link.outcome_verified_at = datetime.now()
        self.session.commit()
        self.session.refresh(link)
        return link

    def get_pending_outcomes(self, hours_old: int = 24) -> List[NewsDecisionLink]:
        """결과 대기 중인 링크 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        return self.session.query(NewsDecisionLink).filter(
            and_(
                NewsDecisionLink.decision_outcome == 'PENDING',
                NewsDecisionLink.created_at <= cutoff_time
            )
        ).all()

    def get_by_outcome(self, outcome: str, start_date, end_date) -> List[NewsDecisionLink]:
        """결과별 링크 조회 (SUCCESS/FAILURE)"""
        return self.session.query(NewsDecisionLink).filter(
            and_(
                NewsDecisionLink.decision_outcome == outcome,
                NewsDecisionLink.created_at >= start_date,
                NewsDecisionLink.created_at <= end_date
            )
        ).all()


class NewsNarrativeRepository:
    """리포트 서술 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> NewsNarrative:
        """새로운 서술 생성"""
        narrative = NewsNarrative(**data)
        self.session.add(narrative)
        self.session.commit()
        self.session.refresh(narrative)
        return narrative

    def get_by_report_date(self, report_date, report_type: str = 'DAILY') -> List[NewsNarrative]:
        """리포트 날짜+타입으로 서술 조회"""
        return self.session.query(NewsNarrative).filter(
            and_(
                NewsNarrative.report_date == report_date,
                NewsNarrative.report_type == report_type
            )
        ).order_by(NewsNarrative.page_number.asc()).all()

    def get_by_interpretation_id(self, interpretation_id: int) -> List[NewsNarrative]:
        """해석 ID로 서술 조회"""
        return self.session.query(NewsNarrative).filter(
            NewsNarrative.interpretation_id == interpretation_id
        ).all()

    def update_accuracy(self, narrative: NewsNarrative, accuracy_score: float) -> NewsNarrative:
        """서술 정확도 업데이트"""
        narrative.accuracy_score = accuracy_score
        narrative.verified = True
        narrative.verified_at = datetime.now()
        self.session.commit()
        self.session.refresh(narrative)
        return narrative

    def get_unverified_predictions(self, days_old: int = 1) -> List[NewsNarrative]:
        """검증 대기 중인 예측 조회"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        return self.session.query(NewsNarrative).filter(
            and_(
                NewsNarrative.claim_type == 'PREDICTION',
                NewsNarrative.verified == False,
                NewsNarrative.created_at <= cutoff_date
            )
        ).all()

    def get_accuracy_stats(self, start_date, end_date, report_type: str = 'DAILY') -> Dict:
        """기간별 정확도 통계"""
        narratives = self.session.query(NewsNarrative).filter(
            and_(
                NewsNarrative.report_date >= start_date,
                NewsNarrative.report_date <= end_date,
                NewsNarrative.report_type == report_type,
                NewsNarrative.verified == True,
                NewsNarrative.accuracy_score.isnot(None)
            )
        ).all()

        if not narratives:
            return {'count': 0, 'avg_accuracy': 0, 'by_claim_type': {}}

        total = len(narratives)
        avg_accuracy = sum(n.accuracy_score for n in narratives) / total

        by_claim_type = {}
        for claim_type in ['PREDICTION', 'ANALYSIS', 'OBSERVATION', 'RECOMMENDATION']:
            filtered = [n for n in narratives if n.claim_type == claim_type]
            if filtered:
                by_claim_type[claim_type] = {
                    'count': len(filtered),
                    'avg_accuracy': sum(n.accuracy_score for n in filtered) / len(filtered)
                }

        return {
            'count': total,
            'avg_accuracy': avg_accuracy,
            'by_claim_type': by_claim_type
        }


class FailureAnalysisRepository:
    """실패 분석 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict) -> FailureAnalysis:
        """새로운 실패 분석 생성"""
        analysis = FailureAnalysis(**data)
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_by_interpretation_id(self, interpretation_id: int) -> Optional[FailureAnalysis]:
        """해석 ID로 분석 조회"""
        return self.session.query(FailureAnalysis).filter(
            FailureAnalysis.interpretation_id == interpretation_id
        ).first()

    def get_by_decision_link_id(self, decision_link_id: int) -> Optional[FailureAnalysis]:
        """의사결정 링크 ID로 분석 조회"""
        return self.session.query(FailureAnalysis).filter(
            FailureAnalysis.decision_link_id == decision_link_id
        ).first()

    def get_by_severity(self, severity: str, limit: int = 10) -> List[FailureAnalysis]:
        """심각도별 실패 조회 (CRITICAL/HIGH/MEDIUM/LOW)"""
        return self.session.query(FailureAnalysis).filter(
            FailureAnalysis.severity == severity
        ).order_by(desc(FailureAnalysis.analyzed_at)).limit(limit).all()

    def get_unfixed(self, severity: Optional[str] = None) -> List[FailureAnalysis]:
        """미수정 실패 조회"""
        query = self.session.query(FailureAnalysis).filter(
            FailureAnalysis.fix_applied == False
        )
        if severity:
            query = query.filter(FailureAnalysis.severity == severity)
        return query.order_by(desc(FailureAnalysis.severity), desc(FailureAnalysis.analyzed_at)).all()

    def mark_fix_applied(self, analysis: FailureAnalysis, fix_description: str) -> FailureAnalysis:
        """수정 적용 표시"""
        analysis.fix_applied = True
        analysis.fix_description = fix_description
        analysis.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def mark_fix_effective(self, analysis: FailureAnalysis, effective: bool) -> FailureAnalysis:
        """수정 효과 평가"""
        analysis.fix_effective = effective
        analysis.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_by_date_range(self, start_date, end_date) -> List[FailureAnalysis]:
        """날짜 범위로 실패 조회"""
        return self.session.query(FailureAnalysis).filter(
            and_(
                FailureAnalysis.analyzed_at >= start_date,
                FailureAnalysis.analyzed_at <= end_date
            )
        ).order_by(FailureAnalysis.analyzed_at.asc()).all()

    def get_by_ticker(self, ticker: str, limit: int = 10) -> List[FailureAnalysis]:
        """종목별 실패 분석 조회"""
        return self.session.query(FailureAnalysis).filter(
            FailureAnalysis.ticker == ticker
        ).order_by(desc(FailureAnalysis.analyzed_at)).limit(limit).all()


class DeepReasoningRepository:
    """Deep Reasoning 분석 이력 저장 및 조회"""

    def __init__(self, session: Session):
        self.session = session

    def create_analysis(self, analysis_data: Dict) -> DeepReasoningAnalysis:
        """
        Deep Reasoning 분석 결과 저장

        Args:
            analysis_data: Dict with analysis result data
                - news_text: str
                - theme: str
                - primary_beneficiary_ticker: Optional[str]
                - primary_beneficiary_action: Optional[str]
                - primary_beneficiary_confidence: Optional[float]
                - primary_beneficiary_reasoning: Optional[str]
                - hidden_beneficiary_ticker: Optional[str]
                - hidden_beneficiary_action: Optional[str]
                - hidden_beneficiary_confidence: Optional[float]
                - hidden_beneficiary_reasoning: Optional[str]
                - loser_ticker: Optional[str]
                - loser_action: Optional[str]
                - loser_confidence: Optional[float]
                - loser_reasoning: Optional[str]
                - bull_case: str
                - bear_case: str
                - reasoning_trace: List[Dict]
                - model_used: str
                - processing_time_ms: int

        Returns:
            DeepReasoningAnalysis ORM object
        """
        db_analysis = DeepReasoningAnalysis(
            news_text=analysis_data['news_text'],
            theme=analysis_data['theme'],
            primary_beneficiary_ticker=analysis_data.get('primary_beneficiary_ticker'),
            primary_beneficiary_action=analysis_data.get('primary_beneficiary_action'),
            primary_beneficiary_confidence=analysis_data.get('primary_beneficiary_confidence'),
            primary_beneficiary_reasoning=analysis_data.get('primary_beneficiary_reasoning'),
            hidden_beneficiary_ticker=analysis_data.get('hidden_beneficiary_ticker'),
            hidden_beneficiary_action=analysis_data.get('hidden_beneficiary_action'),
            hidden_beneficiary_confidence=analysis_data.get('hidden_beneficiary_confidence'),
            hidden_beneficiary_reasoning=analysis_data.get('hidden_beneficiary_reasoning'),
            loser_ticker=analysis_data.get('loser_ticker'),
            loser_action=analysis_data.get('loser_action'),
            loser_confidence=analysis_data.get('loser_confidence'),
            loser_reasoning=analysis_data.get('loser_reasoning'),
            bull_case=analysis_data['bull_case'],
            bear_case=analysis_data['bear_case'],
            reasoning_trace=analysis_data['reasoning_trace'],
            model_used=analysis_data['model_used'],
            processing_time_ms=analysis_data['processing_time_ms'],
            created_at=datetime.now()
        )
        self.session.add(db_analysis)
        self.session.commit()
        self.session.refresh(db_analysis)
        return db_analysis

    def get_all(self, limit: int = 50, offset: int = 0) -> List[DeepReasoningAnalysis]:
        """
        모든 분석 이력 조회 (최신순)

        Args:
            limit: 최대 조회 개수 (default: 50)
            offset: 시작 위치 (default: 0)

        Returns:
            List of DeepReasoningAnalysis
        """
        return (
            self.session.query(DeepReasoningAnalysis)
            .order_by(desc(DeepReasoningAnalysis.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_id(self, analysis_id: int) -> Optional[DeepReasoningAnalysis]:
        """ID로 특정 분석 조회"""
        return self.session.query(DeepReasoningAnalysis).filter(
            DeepReasoningAnalysis.id == analysis_id
        ).first()

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[DeepReasoningAnalysis]:
        """
        날짜 범위로 분석 조회

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            List of DeepReasoningAnalysis
        """
        return (
            self.session.query(DeepReasoningAnalysis)
            .filter(and_(
                DeepReasoningAnalysis.created_at >= start_date,
                DeepReasoningAnalysis.created_at <= end_date
            ))
            .order_by(desc(DeepReasoningAnalysis.created_at))
            .limit(limit)
            .all()
        )

    def get_by_ticker(
        self,
        ticker: str,
        limit: int = 20
    ) -> List[DeepReasoningAnalysis]:
        """
        특정 티커가 포함된 분석 조회 (주 수혜주 또는 숨은 수혜주)

        Args:
            ticker: 종목 코드
            limit: 최대 조회 개수

        Returns:
            List of DeepReasoningAnalysis
        """
        return (
            self.session.query(DeepReasoningAnalysis)
            .filter(or_(
                DeepReasoningAnalysis.primary_beneficiary_ticker == ticker,
                DeepReasoningAnalysis.hidden_beneficiary_ticker == ticker
            ))
            .order_by(desc(DeepReasoningAnalysis.created_at))
            .limit(limit)
            .all()
        )

    def delete_analysis(self, analysis_id: int) -> bool:
        """
        분석 삭제

        Args:
            analysis_id: 삭제할 분석 ID

        Returns:
            bool: 삭제 성공 여부
        """
        analysis = self.get_by_id(analysis_id)
        if analysis:
            self.session.delete(analysis)
            self.session.commit()
            return True
        return False

    def count_total(self) -> int:
        """전체 분석 개수"""
        return self.session.query(func.count(DeepReasoningAnalysis.id)).scalar()

    def get_recent(self, hours: int = 24, limit: int = 20) -> List[DeepReasoningAnalysis]:
        """
        최근 N시간 내 분석 조회

        Args:
            hours: 조회 시간 범위 (시간)
            limit: 최대 조회 개수

        Returns:
            List of DeepReasoningAnalysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return (
            self.session.query(DeepReasoningAnalysis)
            .filter(DeepReasoningAnalysis.created_at >= cutoff_time)
            .order_by(desc(DeepReasoningAnalysis.created_at))
            .limit(limit)
            .all()
        )
