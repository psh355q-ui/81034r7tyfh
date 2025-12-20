"""
Phase 16+: RSS Crawler with Database Integration

Enhanced RSS crawler that:
- Crawls RSS feeds
- Stores articles to database
- Runs Deep Reasoning analysis
- Saves analysis results and signals
- Triggers alerts for high-confidence signals
- Records metrics to Prometheus

Fully integrated with:
- Database (models.py, repository.py)
- Deep Reasoning (deep_reasoning.py)
- Alert System (alert_system.py)
- Metrics (ai_trading_metrics.py)

Usage:
    crawler = RSSCrawlerWithDB()
    await crawler.start_monitoring(interval_seconds=300)  # 5 minutes
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

from backend.news.rss_crawler import RSSNewsCrawler, NewsArticle
from backend.database.repository import (
    NewsRepository,
    AnalysisRepository,
    SignalRepository,
    get_sync_session
)
from backend.database.models import NewsArticle as DBNewsArticle
from backend.alerts.alert_system import AlertSystem, TradingSignal as AlertSignal
from backend.monitoring.ai_trading_metrics import get_metrics, AnalysisTimer


class RSSCrawlerWithDB:
    """
    Database-integrated RSS crawler

    전체 파이프라인:
    1. RSS feeds 크롤링
    2. 뉴스 기사 DB 저장 (중복 체크)
    3. Deep Reasoning 분석 실행
    4. 분석 결과 DB 저장
    5. Trading signals DB 저장
    6. High-confidence signals → Alert 발송
    7. Prometheus metrics 기록
    """

    def __init__(
        self,
        alert_system: Optional[AlertSystem] = None,
        enable_alerts: bool = True,
        enable_metrics: bool = True
    ):
        """
        Args:
            alert_system: AlertSystem instance (None이면 환경변수에서 자동 생성)
            enable_alerts: Alert 발송 활성화
            enable_metrics: Prometheus metrics 기록 활성화
        """
        # Core components
        self.crawler = RSSNewsCrawler()
        self.alert_system = alert_system
        self.enable_alerts = enable_alerts
        self.enable_metrics = enable_metrics

        # Initialize AlertSystem if needed
        if self.enable_alerts and self.alert_system is None:
            import os
            self.alert_system = AlertSystem(
                telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
                telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
                slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
                confidence_threshold=float(os.getenv("ALERT_CONFIDENCE_THRESHOLD", "0.85"))
            )

        # Metrics
        if self.enable_metrics:
            self.metrics = get_metrics()

    @contextmanager
    def _get_db_session(self):
        """Database session context manager"""
        session = get_sync_session()
        try:
            yield session
        finally:
            session.close()

    async def process_article(
        self,
        article: NewsArticle,
        session
    ) -> Optional[Dict]:
        """
        단일 기사 처리 파이프라인

        Args:
            article: RSS NewsArticle
            session: SQLAlchemy session

        Returns:
            {
                'db_article': DBNewsArticle,
                'db_analysis': AnalysisResult,
                'db_signals': List[TradingSignal],
                'alerts_sent': Dict
            }
        """
        # Repositories
        news_repo = NewsRepository(session)
        analysis_repo = AnalysisRepository(session)
        signal_repo = SignalRepository(session)

        # 1. Check for duplicates
        existing = news_repo.get_by_hash(article.content_hash)
        if existing:
            print(f"  [SKIP] Duplicate article: {article.title[:50]}...")
            return None

        # 2. Save article to DB
        db_article = news_repo.create_article(article)
        print(f"  [SAVED] Article ID={db_article.id}: {article.title[:50]}...")

        # Record metrics
        if self.enable_metrics:
            self.metrics.record_article_crawled(article.source)

        # 3. Run Deep Reasoning analysis
        print(f"  [ANALYZING] Running Deep Reasoning...")

        analysis_result = None
        duration = 0.0

        if self.enable_metrics:
            # Use timing context manager
            metrics = self.metrics
            class TimingContext:
                def __init__(self):
                    self.start_time = None
                    self.found_hidden = False

                async def __aenter__(self):
                    self.start_time = asyncio.get_event_loop().time()
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    nonlocal duration
                    duration = asyncio.get_event_loop().time() - self.start_time
                    metrics.record_analysis_complete(duration, self.found_hidden)

            timer = TimingContext()
            async with timer:
                news_text = f"{article.title}. {article.content}"
                analysis_result = await self.crawler.reasoning_strategy.analyze_news(news_text)
                timer.found_hidden = (analysis_result.hidden_beneficiary is not None)
        else:
            # Without metrics
            news_text = f"{article.title}. {article.content}"
            analysis_result = await self.crawler.reasoning_strategy.analyze_news(news_text)

        if not analysis_result:
            print(f"  [ERROR] Analysis failed")
            return None

        # 4. Save analysis to DB
        db_analysis = analysis_repo.create_analysis(
            article_id=db_article.id,
            result=analysis_result,
            model_name="gemini-2.5-pro",
            duration_seconds=duration
        )
        print(f"  [SAVED] Analysis ID={db_analysis.id}, Theme: {analysis_result.theme}")

        # 5. Save signals to DB
        db_signals = []
        signal_dicts = []

        # Primary beneficiary
        if analysis_result.primary_beneficiary:
            primary = analysis_result.primary_beneficiary
            db_signal = signal_repo.create_signal(
                analysis_id=db_analysis.id,
                ticker=primary.get('ticker'),
                action=primary.get('action'),
                signal_type='PRIMARY',
                confidence=primary.get('confidence'),
                reasoning=primary.get('reasoning', '')
            )
            db_signals.append(db_signal)
            signal_dicts.append({
                'type': 'PRIMARY',
                'ticker': primary.get('ticker'),
                'action': primary.get('action'),
                'confidence': primary.get('confidence'),
                'reasoning': primary.get('reasoning', '')
            })

            # Record metrics
            if self.enable_metrics:
                self.metrics.record_signal(
                    ticker=primary.get('ticker'),
                    action=primary.get('action'),
                    signal_type='PRIMARY',
                    confidence=primary.get('confidence')
                )

        # Hidden beneficiary
        if analysis_result.hidden_beneficiary:
            hidden = analysis_result.hidden_beneficiary
            db_signal = signal_repo.create_signal(
                analysis_id=db_analysis.id,
                ticker=hidden.get('ticker'),
                action=hidden.get('action'),
                signal_type='HIDDEN',
                confidence=hidden.get('confidence'),
                reasoning=hidden.get('reasoning', '')
            )
            db_signals.append(db_signal)
            signal_dicts.append({
                'type': 'HIDDEN',
                'ticker': hidden.get('ticker'),
                'action': hidden.get('action'),
                'confidence': hidden.get('confidence'),
                'reasoning': hidden.get('reasoning', '')
            })

            # Record metrics
            if self.enable_metrics:
                self.metrics.record_signal(
                    ticker=hidden.get('ticker'),
                    action=hidden.get('action'),
                    signal_type='HIDDEN',
                    confidence=hidden.get('confidence')
                )

        # Loser
        if analysis_result.loser:
            loser = analysis_result.loser
            db_signal = signal_repo.create_signal(
                analysis_id=db_analysis.id,
                ticker=loser.get('ticker'),
                action=loser.get('action'),
                signal_type='LOSER',
                confidence=loser.get('confidence'),
                reasoning=loser.get('reasoning', 'N/A')
            )
            db_signals.append(db_signal)
            signal_dicts.append({
                'type': 'LOSER',
                'ticker': loser.get('ticker'),
                'action': loser.get('action'),
                'confidence': loser.get('confidence'),
                'reasoning': loser.get('reasoning', 'N/A')
            })

            # Record metrics
            if self.enable_metrics:
                self.metrics.record_signal(
                    ticker=loser.get('ticker'),
                    action=loser.get('action'),
                    signal_type='LOSER',
                    confidence=loser.get('confidence')
                )

        print(f"  [SAVED] {len(db_signals)} signals")

        # 6. Send alerts for high-confidence signals
        alerts_sent = {}
        if self.enable_alerts and self.alert_system:
            for signal_dict in signal_dicts:
                if signal_dict['confidence'] >= 0.85:
                    alert_signal = AlertSignal(
                        ticker=signal_dict['ticker'],
                        action=signal_dict['action'],
                        signal_type=signal_dict['type'],
                        confidence=signal_dict['confidence'],
                        reasoning=signal_dict['reasoning'],
                        news_title=article.title,
                        timestamp=datetime.now()
                    )

                    # Send alert
                    alert_result = await self.alert_system.send_signal_alert(alert_signal)
                    alerts_sent[signal_dict['ticker']] = alert_result

                    # Mark as sent in DB
                    for db_sig in db_signals:
                        if db_sig.ticker == signal_dict['ticker']:
                            signal_repo.mark_alert_sent(db_sig.id)

                    print(f"  [ALERT] Sent for {signal_dict['ticker']} ({signal_dict['confidence']:.0%}): {alert_result}")

        return {
            'db_article': db_article,
            'db_analysis': db_analysis,
            'db_signals': db_signals,
            'alerts_sent': alerts_sent,
            'signal_dicts': signal_dicts
        }

    async def run_single_cycle(self) -> List[Dict]:
        """
        단일 크롤링 사이클 (DB 통합)

        Returns:
            처리된 기사 리스트
        """
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting DB-integrated crawl cycle")
        print(f"{'='*80}")

        # Record cycle start
        if self.enable_metrics:
            cycle_start = asyncio.get_event_loop().time()

        # 1. Fetch RSS feeds
        print(f"\n[STEP 1] Fetching RSS feeds...")
        articles = await self.crawler.fetch_all_feeds()
        print(f"  Found {len(articles)} relevant articles")

        if not articles:
            print("  No new articles found")
            return []

        # 2. Process each article
        print(f"\n[STEP 2] Processing articles (DB + Analysis + Alerts)...")
        processed_results = []

        with self._get_db_session() as session:
            for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
                print(f"\n  [{i}/{min(len(articles), 5)}] Processing: {article.title[:60]}...")

                try:
                    result = await self.process_article(article, session)
                    if result:
                        processed_results.append(result)
                except Exception as e:
                    print(f"  [ERROR] Failed to process article: {e}")
                    continue

        # Record cycle end
        if self.enable_metrics:
            cycle_duration = asyncio.get_event_loop().time() - cycle_start
            self.metrics.record_crawl_cycle_complete(cycle_duration, len(processed_results))

        print(f"\n{'='*80}")
        print(f"Cycle complete: {len(processed_results)} articles processed")
        print(f"{'='*80}")

        return processed_results

    async def start_monitoring(self, interval_seconds: int = 300):
        """
        실시간 모니터링 시작

        Args:
            interval_seconds: 크롤링 간격 (초), 기본 5분
        """
        print(f"\n{'='*80}")
        print("Phase 16+: DB-Integrated RSS Crawler Started")
        print(f"{'='*80}")
        print(f"  Monitoring {len(self.crawler.RSS_FEEDS)} RSS feeds")
        print(f"  Check interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
        print(f"  Database: ENABLED")
        print(f"  Alerts: {'ENABLED' if self.enable_alerts else 'DISABLED'}")
        print(f"  Metrics: {'ENABLED' if self.enable_metrics else 'DISABLED'}")
        print(f"{'='*80}\n")

        cycle_count = 0

        while True:
            try:
                cycle_count += 1
                print(f"\n[CYCLE #{cycle_count}]")

                # Crawl & process
                results = await self.run_single_cycle()

                # Summary
                if results:
                    total_signals = sum(len(r['db_signals']) for r in results)
                    total_alerts = sum(len(r['alerts_sent']) for r in results)
                    print(f"\n[SUMMARY] {len(results)} articles, {total_signals} signals, {total_alerts} alerts sent")

                # Wait
                print(f"\n[WAITING] Next check in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n\n[STOPPED] Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n[ERROR] Cycle failed: {e}")
                print(f"Retrying in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)


# ============================================
# Demo & Testing
# ============================================

async def demo():
    """DB-통합 크롤러 데모"""
    print("=" * 80)
    print("Phase 16+: DB-Integrated RSS Crawler Demo")
    print("=" * 80)

    # Initialize crawler
    crawler = RSSCrawlerWithDB(
        enable_alerts=True,
        enable_metrics=True
    )

    # Run single cycle
    results = await crawler.run_single_cycle()

    # Print results
    print("\n" + "=" * 80)
    print("DEMO RESULTS")
    print("=" * 80)

    if results:
        print(f"\nTotal articles processed: {len(results)}")

        for i, result in enumerate(results, 1):
            article = result['db_article']
            analysis = result['db_analysis']
            signals = result['db_signals']
            alerts = result['alerts_sent']

            print(f"\n[Article {i}] ID={article.id}")
            print(f"  Title: {article.title}")
            print(f"  Source: {article.source}")
            print(f"  Published: {article.published_date.strftime('%Y-%m-%d %H:%M')}")

            print(f"\n  [Analysis] ID={analysis.id}")
            print(f"    Theme: {analysis.theme}")
            print(f"    Duration: {analysis.analysis_duration_seconds:.2f}s")

            print(f"\n  [Signals] {len(signals)} total")
            for sig in signals:
                print(f"    - {sig.signal_type:8} | {sig.ticker:6} | {sig.action:6} | {sig.confidence:.0%}")

            if alerts:
                print(f"\n  [Alerts] Sent to {len(alerts)} channels")
                for ticker, channels in alerts.items():
                    print(f"    {ticker}: {channels}")
    else:
        print("\nNo articles processed in this cycle")

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo())

    # Start monitoring (uncomment to use)
    # crawler = RSSCrawlerWithDB()
    # asyncio.run(crawler.start_monitoring(interval_seconds=300))
