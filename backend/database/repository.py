"""
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

from typing import List, Optional, Dict, Tuple
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
    SignalPerformance
)
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


def get_sync_session():
    """
    Synchronous session (for non-async contexts)

    Usage:
        with get_sync_session() as session:
            news_repo = NewsRepository(session)
    """
    return SessionLocal()
