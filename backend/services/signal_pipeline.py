"""
Real-time Signal Generation Pipeline

뉴스 → AI 분석 → 신호 생성 → WebSocket 브로드캐스트

Features:
- 뉴스 크롤링 및 AI 분석 연동
- 실시간 신호 생성 및 브로드캐스트
- 신호 품질 관리 및 중복 제거
- 자동 실행 플래그 지원

Author: AI Trading System
Date: 2025-12-03
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import json

# Database
from sqlalchemy.orm import Session
from backend.data.news_models import NewsArticle, NewsAnalysis, get_db

# News Analysis
from backend.data.news_analyzer import NewsDeepAnalyzer

# Signal Generation
from backend.signals.news_signal_generator import (
    NewsSignalGenerator,
    TradingSignal,
    create_signal_generator
)

logger = logging.getLogger(__name__)


class SignalPipeline:
    """
    실시간 신호 생성 파이프라인

    Process:
    1. 미분석 뉴스 조회
    2. AI 분석 실행 (Gemini)
    3. 신호 생성 (NewsSignalGenerator)
    4. 중복 제거 및 품질 필터링
    5. WebSocket 브로드캐스트

    Usage:
        pipeline = SignalPipeline()
        signals = await pipeline.process_latest_news()
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        signal_generator: Optional[NewsSignalGenerator] = None,
        max_news_per_cycle: int = 10,
        analysis_batch_size: int = 5,
    ):
        """
        Args:
            db_session: Database session (optional)
            signal_generator: Pre-configured signal generator (optional)
            max_news_per_cycle: 한 사이클당 처리할 최대 뉴스 개수
            analysis_batch_size: 한 번에 분석할 뉴스 개수
        """
        self.db_session = db_session
        self.signal_generator = signal_generator or create_signal_generator()
        self.max_news_per_cycle = max_news_per_cycle
        self.analysis_batch_size = analysis_batch_size

        # 최근 생성된 신호 추적 (중복 방지)
        self.recent_signals: Set[str] = set()  # {ticker}_{timestamp}
        self.signal_history: List[Dict] = []

        # 통계
        self.stats = {
            "total_cycles": 0,
            "news_processed": 0,
            "news_analyzed": 0,
            "signals_generated": 0,
            "signals_duplicates": 0,
            "signals_low_quality": 0,
            "last_run": None,
        }

        logger.info("SignalPipeline initialized")

    async def process_latest_news(
        self,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        최신 뉴스 처리 및 신호 생성

        Returns:
            생성된 신호 리스트 (dict 형태)
        """
        self.stats["total_cycles"] += 1
        self.stats["last_run"] = datetime.now().isoformat()

        # DB 세션
        if db is None:
            db = next(get_db())

        try:
            # 1. 미분석 뉴스 조회
            unanalyzed_news = self._get_unanalyzed_news(db, self.max_news_per_cycle)

            if not unanalyzed_news:
                logger.info("No unanalyzed news found")
                return []

            logger.info(f"Found {len(unanalyzed_news)} unanalyzed articles")
            self.stats["news_processed"] += len(unanalyzed_news)

            # 2. AI 분석 실행
            analyzed_results = await self._analyze_news_batch(db, unanalyzed_news)
            self.stats["news_analyzed"] += len(analyzed_results)

            if not analyzed_results:
                logger.warning("No news passed AI analysis")
                return []

            # 3. 신호 생성
            signals = self._generate_signals(analyzed_results)

            if not signals:
                logger.info("No signals generated from analyzed news")
                return []

            # 4. 중복 제거 및 품질 필터링
            filtered_signals = self._filter_signals(signals)

            if not filtered_signals:
                logger.info("All signals filtered out (duplicates or low quality)")
                return []

            logger.info(f"Pipeline produced {len(filtered_signals)} signals")
            self.stats["signals_generated"] += len(filtered_signals)

            # 5. 신호 히스토리에 추가
            for signal in filtered_signals:
                self.signal_history.append(signal)

            # 히스토리 제한 (최근 100개만 유지)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]

            return filtered_signals

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return []

    def _get_unanalyzed_news(
        self,
        db: Session,
        limit: int
    ) -> List[NewsArticle]:
        """미분석 뉴스 조회"""

        # 최근 24시간 이내, 아직 분석되지 않은 뉴스
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        unanalyzed = (
            db.query(NewsArticle)
            .filter(NewsArticle.crawled_at >= cutoff_time)
            .filter(~NewsArticle.analysis_id.isnot(None) == False)  # No analysis
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
            .all()
        )

        return unanalyzed

    async def _analyze_news_batch(
        self,
        db: Session,
        articles: List[NewsArticle]
    ) -> List[Dict[str, Any]]:
        """
        뉴스 배치 분석

        Returns:
            분석 결과 리스트 (trading_actionable=True인 것만)
        """
        analyzer = NewsDeepAnalyzer(db)
        analyzed_results = []

        # 배치 단위로 분석
        for i in range(0, len(articles), self.analysis_batch_size):
            batch = articles[i:i + self.analysis_batch_size]

            for article in batch:
                try:
                    # 분석 실행
                    analysis = analyzer.analyze_article(article)

                    if not analysis:
                        logger.debug(f"Analysis failed for article {article.id}")
                        continue

                    # trading_actionable인 것만 선택
                    if analysis.trading_actionable:
                        # 분석 결과를 dict로 변환
                        analysis_dict = {
                            "article_id": article.id,
                            "title": article.title,
                            "source": article.source,
                            "published_at": article.published_at,
                            "sentiment_overall": analysis.sentiment_overall,
                            "sentiment_score": analysis.sentiment_score,
                            "sentiment_confidence": analysis.sentiment_confidence,
                            "urgency": analysis.urgency,
                            "market_impact_short": analysis.market_impact_short,
                            "market_impact_long": analysis.market_impact_long,
                            "impact_magnitude": analysis.impact_magnitude,
                            "affected_sectors": analysis.affected_sectors or [],
                            "key_facts": analysis.key_facts or [],
                            "key_warnings": analysis.key_warnings or [],
                            "trading_actionable": analysis.trading_actionable,
                            "risk_category": analysis.risk_category,
                            "recommendation": analysis.recommendation,
                            "red_flags": analysis.red_flags or [],
                            "related_tickers": self._extract_tickers(article),
                        }

                        analyzed_results.append(analysis_dict)
                        logger.info(
                            f"Actionable news: {article.title[:50]}... "
                            f"(sentiment={analysis.sentiment_overall}, impact={analysis.impact_magnitude:.2f})"
                        )

                except Exception as e:
                    logger.error(f"Error analyzing article {article.id}: {e}")
                    continue

            # Rate limiting (API 호출 제한 고려)
            if i + self.analysis_batch_size < len(articles):
                await asyncio.sleep(1)

        logger.info(f"Analysis complete: {len(analyzed_results)}/{len(articles)} actionable")
        return analyzed_results

    def _extract_tickers(self, article: NewsArticle) -> List[Dict]:
        """기사에서 티커 정보 추출"""

        if not article.ticker_relevances:
            return []

        return [
            {
                "ticker_symbol": rel.ticker,
                "relevance_score": rel.relevance_score,
                "sentiment": rel.sentiment_for_ticker,
            }
            for rel in article.ticker_relevances
        ]

    def _generate_signals(
        self,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        분석 결과에서 신호 생성

        Returns:
            TradingSignal dict 리스트
        """
        signals = []

        for analysis in analyses:
            try:
                # 신호 생성
                signal = self.signal_generator.generate_signal(analysis)

                if signal:
                    signals.append(signal.to_dict())
                    logger.info(
                        f"Signal generated: {signal.action.value} {signal.ticker} "
                        f"@ {signal.position_size:.1%} (confidence={signal.confidence:.2f})"
                    )

            except Exception as e:
                logger.error(f"Error generating signal from analysis: {e}")
                continue

        return signals

    def _filter_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        신호 필터링 (중복 제거 + 품질 검사)

        Rules:
        1. 같은 티커의 신호가 30분 이내에 중복되면 제거
        2. Confidence < 0.6 제거
        3. Position size < 0.01 제거
        """
        filtered = []
        now = datetime.now()

        for signal in signals:
            ticker = signal["ticker"]
            created_at = datetime.fromisoformat(signal["created_at"])
            confidence = signal["confidence"]
            position_size = signal["position_size"]

            # 1. 중복 체크 (30분 이내)
            signal_key = f"{ticker}_{created_at.strftime('%Y%m%d_%H%M')}"
            if signal_key in self.recent_signals:
                self.stats["signals_duplicates"] += 1
                logger.debug(f"Duplicate signal filtered: {ticker}")
                continue

            # 2. 품질 체크
            if confidence < 0.6:
                self.stats["signals_low_quality"] += 1
                logger.debug(f"Low confidence signal filtered: {ticker} ({confidence:.2f})")
                continue

            if position_size < 0.01:
                self.stats["signals_low_quality"] += 1
                logger.debug(f"Low position size signal filtered: {ticker} ({position_size:.1%})")
                continue

            # 통과!
            filtered.append(signal)
            self.recent_signals.add(signal_key)

        # 오래된 신호 키 정리 (1시간 이상)
        self._cleanup_recent_signals()

        return filtered

    def _cleanup_recent_signals(self):
        """오래된 신호 키 제거"""
        # 간단하게: 100개 이상이면 절반 제거
        if len(self.recent_signals) > 100:
            # Set은 순서가 없으므로 새로 생성
            self.recent_signals = set(list(self.recent_signals)[-50:])

    def get_statistics(self) -> Dict[str, Any]:
        """파이프라인 통계 조회"""
        return {
            **self.stats,
            "signal_rate": (
                self.stats["signals_generated"] / self.stats["news_analyzed"]
                if self.stats["news_analyzed"] > 0 else 0
            ),
            "recent_signals_count": len(self.recent_signals),
            "history_count": len(self.signal_history),
        }

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """최근 생성된 신호 조회"""
        return self.signal_history[-limit:]

    def clear_history(self):
        """히스토리 초기화"""
        self.signal_history.clear()
        self.recent_signals.clear()
        logger.info("Signal pipeline history cleared")


# ============================================================================
# Global Pipeline Instance
# ============================================================================

_global_pipeline: Optional[SignalPipeline] = None


def get_signal_pipeline() -> SignalPipeline:
    """전역 파이프라인 인스턴스 가져오기"""
    global _global_pipeline

    if _global_pipeline is None:
        _global_pipeline = SignalPipeline()
        logger.info("Global SignalPipeline created")

    return _global_pipeline


# ============================================================================
# Auto Signal Generation Scheduler
# ============================================================================

class SignalScheduler:
    """
    자동 신호 생성 스케줄러

    주기적으로 파이프라인 실행하여 신호 생성

    Usage:
        scheduler = SignalScheduler(interval_minutes=30)
        await scheduler.start()
    """

    def __init__(
        self,
        pipeline: Optional[SignalPipeline] = None,
        interval_minutes: int = 30,
        broadcast_callback: Optional[callable] = None,
    ):
        """
        Args:
            pipeline: SignalPipeline instance
            interval_minutes: 실행 간격 (분)
            broadcast_callback: 신호 생성 시 호출할 콜백 (WebSocket 브로드캐스트)
        """
        self.pipeline = pipeline or get_signal_pipeline()
        self.interval_minutes = interval_minutes
        self.broadcast_callback = broadcast_callback

        self.running = False
        self.task: Optional[asyncio.Task] = None

        logger.info(f"SignalScheduler initialized (interval={interval_minutes}min)")

    async def start(self):
        """스케줄러 시작"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("SignalScheduler started")

    async def stop(self):
        """스케줄러 중지"""
        if not self.running:
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("SignalScheduler stopped")

    async def _run_loop(self):
        """스케줄러 메인 루프"""
        while self.running:
            try:
                logger.info("Signal generation cycle starting...")

                # 파이프라인 실행
                signals = await self.pipeline.process_latest_news()

                # 신호가 생성되면 브로드캐스트
                if signals and self.broadcast_callback:
                    for signal in signals:
                        try:
                            await self.broadcast_callback(signal)
                        except Exception as e:
                            logger.error(f"Broadcast callback error: {e}")

                logger.info(
                    f"Cycle complete: {len(signals)} signals generated. "
                    f"Next run in {self.interval_minutes} minutes."
                )

            except Exception as e:
                logger.error(f"Scheduler cycle error: {e}", exc_info=True)

            # 대기
            await asyncio.sleep(self.interval_minutes * 60)

    def get_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        return {
            "running": self.running,
            "interval_minutes": self.interval_minutes,
            "pipeline_stats": self.pipeline.get_statistics(),
        }


# ============================================================================
# Manual Trigger
# ============================================================================

async def trigger_signal_generation(
    db: Optional[Session] = None,
    broadcast_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    수동으로 신호 생성 트리거

    Returns:
        {
            "success": bool,
            "signals_count": int,
            "signals": List[Dict],
            "message": str
        }
    """
    try:
        pipeline = get_signal_pipeline()

        # 신호 생성
        signals = await pipeline.process_latest_news(db)

        # 브로드캐스트
        if signals and broadcast_callback:
            for signal in signals:
                try:
                    await broadcast_callback(signal)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")

        return {
            "success": True,
            "signals_count": len(signals),
            "signals": signals,
            "message": f"Generated {len(signals)} signals"
        }

    except Exception as e:
        logger.error(f"Manual trigger error: {e}", exc_info=True)
        return {
            "success": False,
            "signals_count": 0,
            "signals": [],
            "message": f"Error: {str(e)}"
        }
