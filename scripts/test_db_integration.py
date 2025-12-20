"""
Test Script: Database Integration

테스트 항목:
1. 뉴스 기사 저장 및 조회
2. 분석 결과 저장
3. 트레이딩 시그널 저장
4. 백테스트 결과 저장
5. 시그널 성과 기록
6. Repository 쿼리 테스트

Usage:
    python scripts/test_db_integration.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.database.repository import (
    NewsRepository,
    AnalysisRepository,
    SignalRepository,
    BacktestRepository,
    PerformanceRepository,
    get_sync_session
)
from backend.database.models import NewsArticle as DBNewsArticle
from backend.news.rss_crawler import NewsArticle
from backend.ai.reasoning.deep_reasoning import DeepReasoningResult


def test_news_repository():
    """뉴스 저장 및 조회 테스트"""
    print("\n" + "=" * 80)
    print("TEST 1: News Repository")
    print("=" * 80)

    with get_sync_session() as session:
        news_repo = NewsRepository(session)

        # Create test article
        test_article = NewsArticle(
            title="Test Article: Nvidia announces new H200 GPU",
            content="Nvidia Corporation announced today the launch of H200, the next generation AI accelerator with improved HBM3e memory bandwidth.",
            url=f"https://test.com/nvidia-h200-{datetime.now().timestamp()}",
            source="TestSource",
            published_date=datetime.now(),
            content_hash=f"test_hash_{datetime.now().timestamp()}"
        )

        # Save article
        db_article = news_repo.create_article(test_article)
        print(f"\n[OK] Article saved: ID={db_article.id}")
        print(f"     Title: {db_article.title}")
        print(f"     Source: {db_article.source}")

        # Test duplicate check
        duplicate = news_repo.get_by_hash(test_article.content_hash)
        assert duplicate is not None, "Duplicate check failed"
        print(f"[OK] Duplicate detection working: Found ID={duplicate.id}")

        # Get recent articles
        recent = news_repo.get_recent_articles(hours=24)
        print(f"[OK] Found {len(recent)} articles in last 24 hours")

        # Count by source
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        counts = news_repo.count_by_source(start_date, end_date)
        print(f"[OK] Articles by source (last 7 days): {dict(counts)}")

        return db_article


def test_analysis_repository(article_id: int):
    """분석 결과 저장 테스트"""
    print("\n" + "=" * 80)
    print("TEST 2: Analysis Repository")
    print("=" * 80)

    with get_sync_session() as session:
        analysis_repo = AnalysisRepository(session)

        # Create mock analysis result
        mock_result = DeepReasoningResult(
            theme="AI Chip Competition Intensifies",
            primary_beneficiary={
                'ticker': 'NVDA',
                'action': 'BUY',
                'confidence': 0.95,
                'reasoning': 'Leading AI GPU provider with H200 launch'
            },
            hidden_beneficiary={
                'ticker': 'TSM',
                'action': 'BUY',
                'confidence': 0.88,
                'reasoning': 'Exclusive foundry for Nvidia advanced nodes'
            },
            loser={
                'ticker': 'AMD',
                'action': 'TRIM',
                'confidence': 0.70,
                'reasoning': 'Losing market share to Nvidia in AI datacenter'
            },
            bull_case="Strong demand for AI accelerators continues to grow...",
            bear_case="Potential inventory buildup and pricing pressure...",
            reasoning_trace={
                'step1': 'Direct impact on Nvidia',
                'step2': 'Supply chain benefits to TSMC',
                'step3': 'Competitive pressure on AMD'
            },
            entities_detected=['Nvidia', 'H200', 'AI'],
            confidence_score=0.90
        )

        # Save analysis
        db_analysis = analysis_repo.create_analysis(
            article_id=article_id,
            result=mock_result,
            model_name="gemini-2.5-pro",
            duration_seconds=3.45
        )
        print(f"\n[OK] Analysis saved: ID={db_analysis.id}")
        print(f"     Theme: {db_analysis.theme}")
        print(f"     Duration: {db_analysis.analysis_duration_seconds:.2f}s")

        # Get recent analyses
        recent = analysis_repo.get_recent_analyses(hours=24)
        print(f"[OK] Found {len(recent)} analyses in last 24 hours")

        # Avg duration
        avg_duration = analysis_repo.get_avg_analysis_duration()
        print(f"[OK] Average analysis duration: {avg_duration:.2f}s")

        return db_analysis


def test_signal_repository(analysis_id: int):
    """시그널 저장 및 조회 테스트"""
    print("\n" + "=" * 80)
    print("TEST 3: Signal Repository")
    print("=" * 80)

    with get_sync_session() as session:
        signal_repo = SignalRepository(session)

        # Create signals
        signals = [
            ('NVDA', 'BUY', 'PRIMARY', 0.95, 'Leading AI GPU provider'),
            ('TSM', 'BUY', 'HIDDEN', 0.88, 'Exclusive foundry partner'),
            ('AMD', 'TRIM', 'LOSER', 0.70, 'Losing market share')
        ]

        db_signals = []
        for ticker, action, signal_type, confidence, reasoning in signals:
            db_signal = signal_repo.create_signal(
                analysis_id=analysis_id,
                ticker=ticker,
                action=action,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=reasoning,
                entry_price=100.0 if ticker == 'NVDA' else None
            )
            db_signals.append(db_signal)
            print(f"\n[OK] Signal saved: ID={db_signal.id}")
            print(f"     {signal_type:8} | {ticker:6} | {action:6} | {confidence:.0%}")

        # Test queries
        recent_hidden = signal_repo.get_recent_signals(hours=24, signal_type='HIDDEN')
        print(f"\n[OK] Found {len(recent_hidden)} HIDDEN signals in last 24 hours")

        high_conf = signal_repo.get_recent_signals(hours=24, min_confidence=0.85)
        print(f"[OK] Found {len(high_conf)} high-confidence (>=85%) signals")

        # Count by type
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        counts = signal_repo.count_by_type(start_date, end_date)
        print(f"[OK] Signals by type (last 7 days): {counts}")

        # Top tickers
        top_tickers = signal_repo.get_top_tickers(days=7, limit=5)
        print(f"\n[OK] Top 5 tickers (last 7 days):")
        for ticker, count, avg_conf in top_tickers:
            print(f"     {ticker:6} | {count:3} signals | {avg_conf:.0%} avg confidence")

        # Test alert marking
        if db_signals:
            signal_repo.mark_alert_sent(db_signals[0].id)
            print(f"\n[OK] Marked signal ID={db_signals[0].id} as alert sent")

        return db_signals


def test_backtest_repository():
    """백테스트 저장 및 조회 테스트"""
    print("\n" + "=" * 80)
    print("TEST 4: Backtest Repository")
    print("=" * 80)

    with get_sync_session() as session:
        backtest_repo = BacktestRepository(session)

        # Create backtest run
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        db_backtest = backtest_repo.create_backtest_run(
            strategy_name="CoT+RAG",
            start_date=start_date,
            end_date=end_date,
            total_trades=12,
            winning_trades=10,
            losing_trades=2,
            win_rate=83.3,
            avg_return=12.4,
            total_return=148.8,
            sharpe_ratio=1.12,
            max_drawdown=-7.8,
            hidden_beneficiaries_found=6
        )
        print(f"\n[OK] Backtest saved: ID={db_backtest.id}")
        print(f"     Strategy: {db_backtest.strategy_name}")
        print(f"     Total Return: {db_backtest.total_return:.1f}%")
        print(f"     Win Rate: {db_backtest.win_rate:.1f}%")
        print(f"     Sharpe Ratio: {db_backtest.sharpe_ratio:.2f}")

        # Add trades
        trades = [
            ('NVDA', 'BUY', 'PRIMARY', 100.0, 115.0, 15.0, 'H200 GPU launch'),
            ('TSM', 'BUY', 'HIDDEN', 85.0, 98.0, 15.3, 'Foundry demand increase'),
            ('AMD', 'TRIM', 'LOSER', 120.0, 110.0, -8.3, 'Market share loss'),
        ]

        for ticker, action, signal_type, entry, exit, return_pct, reason in trades:
            db_trade = backtest_repo.add_trade_to_backtest(
                backtest_run_id=db_backtest.id,
                ticker=ticker,
                action=action,
                signal_type=signal_type,
                entry_date=start_date + timedelta(days=5),
                entry_price=entry,
                exit_date=start_date + timedelta(days=12),
                exit_price=exit,
                return_pct=return_pct,
                reason=reason,
                news_headline="Test headline"
            )
            print(f"[OK] Trade added: {ticker} {return_pct:+.1f}%")

        # Get recent backtests
        recent = backtest_repo.get_recent_backtests(limit=5)
        print(f"\n[OK] Found {len(recent)} recent backtests")

        # Compare strategies
        strategy1, strategy2 = backtest_repo.compare_strategies("Keyword-Only", "CoT+RAG", days=30)
        if strategy1 and strategy2:
            print(f"\n[OK] Strategy comparison:")
            print(f"     Keyword-Only: {strategy1.total_return:.1f}%")
            print(f"     CoT+RAG: {strategy2.total_return:.1f}%")
        elif strategy2:
            print(f"\n[INFO] Only CoT+RAG found: {strategy2.total_return:.1f}%")

        return db_backtest


def test_performance_repository(signal_ids: list):
    """시그널 성과 기록 테스트"""
    print("\n" + "=" * 80)
    print("TEST 5: Performance Repository")
    print("=" * 80)

    with get_sync_session() as session:
        perf_repo = PerformanceRepository(session)

        # Record performance
        performances = [
            (signal_ids[0], 15.0, 2.5, 3.0),  # WIN
            (signal_ids[1], 12.0, 2.5, 2.8),  # WIN
            (signal_ids[2], -8.0, 2.5, -1.2),  # LOSS
        ]

        for signal_id, actual_return, spy_return, sector_return in performances:
            db_perf = perf_repo.record_signal_performance(
                signal_id=signal_id,
                evaluation_date=datetime.now(),
                days_held=7,
                actual_return_pct=actual_return,
                spy_return_pct=spy_return,
                sector_return_pct=sector_return
            )
            print(f"\n[OK] Performance recorded: Signal ID={signal_id}")
            print(f"     Return: {actual_return:+.1f}%")
            print(f"     Alpha: {db_perf.alpha:+.1f}%")
            print(f"     Outcome: {db_perf.outcome}")

        # Win rate by type
        win_rates = perf_repo.get_win_rate_by_signal_type(days=30)
        print(f"\n[OK] Win rates by signal type (last 30 days):")
        for signal_type, win_rate in win_rates.items():
            print(f"     {signal_type:8} | {win_rate:.1%}")

        # Avg return by type
        avg_returns = perf_repo.get_avg_return_by_signal_type(days=30)
        print(f"\n[OK] Average returns by signal type (last 30 days):")
        for signal_type, avg_return in avg_returns.items():
            print(f"     {signal_type:8} | {avg_return:+.1f}%")

        # Hidden beneficiary outperformance
        outperf = perf_repo.get_hidden_beneficiary_outperformance(days=30)
        print(f"\n[OK] Hidden beneficiary outperformance:")
        print(f"     Hidden avg: {outperf['hidden_avg']:+.1f}%")
        print(f"     Primary avg: {outperf['primary_avg']:+.1f}%")
        print(f"     Outperformance ratio: {outperf['outperformance_ratio']:.2f}x")


def main():
    """전체 테스트 실행"""
    print("=" * 80)
    print("Database Integration Test")
    print("=" * 80)

    try:
        # Test 1: News
        db_article = test_news_repository()

        # Test 2: Analysis
        db_analysis = test_analysis_repository(db_article.id)

        # Test 3: Signals
        db_signals = test_signal_repository(db_analysis.id)

        # Test 4: Backtest
        db_backtest = test_backtest_repository()

        # Test 5: Performance
        signal_ids = [sig.id for sig in db_signals]
        test_performance_repository(signal_ids)

        # Summary
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        print("\nDatabase integration is working correctly!")
        print("\nCreated:")
        print(f"  - 1 News article (ID={db_article.id})")
        print(f"  - 1 Analysis result (ID={db_analysis.id})")
        print(f"  - {len(db_signals)} Trading signals")
        print(f"  - 1 Backtest run (ID={db_backtest.id})")
        print(f"  - {len(signal_ids)} Performance records")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
