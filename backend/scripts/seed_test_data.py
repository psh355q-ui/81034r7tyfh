"""
테스트 데이터 생성 스크립트
실제 거래처럼 보이는 더미 데이터 생성

Usage:
    python backend/scripts/seed_test_data.py
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from backend.database.models import TradingSignal, NewsArticle, AnalysisResult
from backend.database.repository import get_sync_session


def create_test_signals():
    """테스트용 트레이딩 시그널 생성"""

    print("=" * 80)
    print("AI Trading System - Test Data Seeder")
    print("=" * 80)
    print()

    db = get_sync_session()

    # 기존 테스트 데이터 확인
    existing_count = db.query(TradingSignal).count()
    print(f"Existing signals in database: {existing_count}")

    # Create a dummy news article and analysis for the foreign key requirement
    dummy_article = NewsArticle(
        title="Test Article for Seed Data",
        content="This is a test article created for seeding trading signals.",
        url=f"https://test.com/article/{datetime.now().timestamp()}",
        source="TEST_SEED",
        published_date=datetime.now(),
        crawled_at=datetime.now(),
        content_hash=f"test_hash_{datetime.now().timestamp()}"
    )
    db.add(dummy_article)
    db.commit()
    db.refresh(dummy_article)

    dummy_analysis = AnalysisResult(
        article_id=dummy_article.id,
        analyzed_at=datetime.now(),
        model_name="test_model",
        theme="Test Data Seeding",
        bull_case="This is test data",
        bear_case="This is test data"
    )
    db.add(dummy_analysis)
    db.commit()
    db.refresh(dummy_analysis)

    if existing_count > 0:
        response = input("\nDatabase already has signals. Do you want to ADD more? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    print("\nCreating test trading signals...")
    print()

    # 테스트 시그널 데이터 (실제처럼 보이는 데이터)
    test_signals = [
        # 활성 포지션 (exit_price가 없음)
        {
            "ticker": "AAPL",
            "signal_type": "AI_CONSENSUS",
            "action": "BUY",
            "confidence": 0.87,
            "entry_price": 180.50,
            "exit_price": None,
            "quantity": 50,
            "generated_at": datetime.now() - timedelta(days=5),
            "reasoning": "Strong technical indicators with positive earnings beat. Multiple AI models agree on bullish trend continuation.",
            "news_summary": "Apple announces record-breaking iPhone sales in Q4",
            "actual_return_pct": None
        },
        {
            "ticker": "NVDA",
            "signal_type": "AI_CONSENSUS",
            "action": "BUY",
            "confidence": 0.94,
            "entry_price": 480.00,
            "exit_price": None,
            "quantity": 20,
            "generated_at": datetime.now() - timedelta(days=3),
            "reasoning": "AI chip demand surge, beat earnings estimates. Strong momentum in data center business.",
            "news_summary": "NVIDIA secures major AI chip contracts with cloud providers",
            "actual_return_pct": None
        },
        {
            "ticker": "TSLA",
            "signal_type": "TECHNICAL",
            "action": "BUY",
            "confidence": 0.76,
            "entry_price": 245.00,
            "exit_price": None,
            "quantity": 30,
            "generated_at": datetime.now() - timedelta(days=7),
            "reasoning": "Oversold condition after correction. Delivery numbers expected to exceed estimates.",
            "news_summary": "Tesla expands production capacity in Germany",
            "actual_return_pct": None
        },
        {
            "ticker": "MSFT",
            "signal_type": "AI_CONSENSUS",
            "action": "BUY",
            "confidence": 0.89,
            "entry_price": 370.00,
            "exit_price": None,
            "quantity": 25,
            "generated_at": datetime.now() - timedelta(days=10),
            "reasoning": "Azure cloud growth accelerating. AI integration driving revenue growth.",
            "news_summary": "Microsoft AI services see 50% YoY growth",
            "actual_return_pct": None
        },
        {
            "ticker": "GOOGL",
            "signal_type": "FUNDAMENTAL",
            "action": "BUY",
            "confidence": 0.82,
            "entry_price": 140.50,
            "exit_price": None,
            "quantity": 35,
            "generated_at": datetime.now() - timedelta(days=4),
            "reasoning": "Undervalued compared to peers. Strong advertising revenue recovery expected.",
            "news_summary": "Google announces breakthrough in quantum computing",
            "actual_return_pct": None
        },

        # 청산된 포지션 (exit_price가 있음) - 최근 거래 내역
        {
            "ticker": "AMD",
            "signal_type": "TECHNICAL",
            "action": "BUY",
            "confidence": 0.79,
            "entry_price": 150.00,
            "exit_price": 165.00,
            "quantity": 40,
            "generated_at": datetime.now() - timedelta(days=30),
            "exit_date": datetime.now() - timedelta(days=15),
            "reasoning": "Technical breakout above resistance. Data center demand increasing.",
            "news_summary": "AMD gains market share in server processors",
            "actual_return_pct": 10.0
        },
        {
            "ticker": "META",
            "signal_type": "AI_CONSENSUS",
            "action": "BUY",
            "confidence": 0.91,
            "entry_price": 320.00,
            "exit_price": 350.00,
            "quantity": 15,
            "generated_at": datetime.now() - timedelta(days=45),
            "exit_date": datetime.now() - timedelta(days=20),
            "reasoning": "Strong user engagement metrics. AI advertising improvements driving revenue.",
            "news_summary": "Meta exceeds Q3 earnings expectations",
            "actual_return_pct": 9.375
        },
        {
            "ticker": "AMZN",
            "signal_type": "FUNDAMENTAL",
            "action": "BUY",
            "confidence": 0.84,
            "entry_price": 145.00,
            "exit_price": 142.00,
            "quantity": 30,
            "generated_at": datetime.now() - timedelta(days=60),
            "exit_date": datetime.now() - timedelta(days=40),
            "reasoning": "AWS growth offsetting retail slowdown. Prime Day sales strong.",
            "news_summary": "Amazon Web Services reports 12% YoY growth",
            "actual_return_pct": -2.07
        },
        {
            "ticker": "NFLX",
            "signal_type": "TECHNICAL",
            "action": "BUY",
            "confidence": 0.73,
            "entry_price": 410.00,
            "exit_price": 445.00,
            "quantity": 12,
            "generated_at": datetime.now() - timedelta(days=50),
            "exit_date": datetime.now() - timedelta(days=25),
            "reasoning": "Subscriber growth accelerating. Content slate strong for Q4.",
            "news_summary": "Netflix adds 8M subscribers in Q3",
            "actual_return_pct": 8.54
        },
        {
            "ticker": "DIS",
            "signal_type": "FUNDAMENTAL",
            "action": "BUY",
            "confidence": 0.68,
            "entry_price": 95.00,
            "exit_price": 88.00,
            "quantity": 50,
            "generated_at": datetime.now() - timedelta(days=70),
            "exit_date": datetime.now() - timedelta(days=50),
            "reasoning": "Disney+ subscriber growth slowing but park attendance strong.",
            "news_summary": "Disney parks see record attendance in summer",
            "actual_return_pct": -7.37
        }
    ]

    # 데이터베이스에 추가
    created_count = 0
    for signal_data in test_signals:
        # Add analysis_id to all signals
        signal_data['analysis_id'] = dummy_analysis.id
        signal = TradingSignal(**signal_data)
        db.add(signal)
        created_count += 1

    db.commit()

    print(f"✅ Created {created_count} test signals")
    print()
    print("Breakdown:")
    active = len([s for s in test_signals if s['exit_price'] is None])
    closed = len([s for s in test_signals if s['exit_price'] is not None])
    print(f"  - Active positions: {active}")
    print(f"  - Closed positions: {closed}")
    print()

    # 포트폴리오 통계 계산
    total_cost = sum([s['entry_price'] * s['quantity'] for s in test_signals if s['exit_price'] is None])
    print(f"📊 Portfolio Statistics:")
    print(f"  - Total invested: ${total_cost:,.2f}")
    print(f"  - Initial capital: $100,000.00")
    print(f"  - Remaining cash: ${100000 - total_cost:,.2f}")
    print()

    print("=" * 80)
    print("✨ Test data created successfully!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Restart backend: Ctrl+C and run start_backend.bat")
    print("  2. Check API: http://localhost:8001/api/portfolio")
    print("  3. View Dashboard: http://localhost:3002/dashboard")
    print()

    db.close()


if __name__ == "__main__":
    try:
        create_test_signals()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (start_database.bat)")
        print("  2. Database is initialized")
        print("  3. You're running from project root")
        import traceback
        traceback.print_exc()
        sys.exit(1)
