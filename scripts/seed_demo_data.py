"""
Demo Data Seed Script

프론트엔드 대시보드에서 실제 데이터를 표시하기 위한
테스트 데이터 생성 스크립트

사용법:
    python scripts/seed_demo_data.py

기능:
    1. TradingSignal 테이블에 데모 포지션 추가
    2. 활성 포지션 (entry_price 있고, exit_price 없음)
    3. 청산된 포지션 (entry/exit 모두 있음)
    4. 다양한 수익률 (상승/하락 혼합)

작성일: 2025-12-10
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.repository import get_sync_session
from backend.database.models import TradingSignal, NewsArticle, AnalysisResult


def create_demo_positions(db):
    """활성 포지션 데모 데이터 생성"""
    
    # AI 칩 관련 종목들
    active_positions = [
        {
            "ticker": "NVDA",
            "signal_type": "PRIMARY",
            "action": "BUY",
            "confidence": 0.92,
            "entry_price": 480.00,
            "reasoning": "AI chip demand surge from cloud providers. Blackwell architecture showing strong adoption.",
            "days_ago": 5,
            "quantity": 20
        },
        {
            "ticker": "AMD",
            "signal_type": "HIDDEN",
            "action": "BUY",
            "confidence": 0.85,
            "entry_price": 125.00,
            "reasoning": "Hidden beneficiary of AI chip supply shortage. MI300X gaining market share.",
            "days_ago": 7,
            "quantity": 50
        },
        {
            "ticker": "AAPL",
            "signal_type": "PRIMARY",
            "action": "BUY",
            "confidence": 0.78,
            "entry_price": 180.00,
            "reasoning": "Apple Intelligence rollout expected to boost iPhone sales. Edge AI leader.",
            "days_ago": 3,
            "quantity": 30
        },
        {
            "ticker": "GOOGL",
            "signal_type": "PRIMARY",
            "action": "BUY",
            "confidence": 0.88,
            "entry_price": 142.00,
            "reasoning": "Gemini 2.0 performing well. TPU v5 deployment accelerating.",
            "days_ago": 10,
            "quantity": 15
        },
        {
            "ticker": "MSFT",
            "signal_type": "HIDDEN",
            "action": "BUY",
            "confidence": 0.82,
            "entry_price": 375.00,
            "reasoning": "Azure AI services growth. Copilot adoption driving cloud revenue.",
            "days_ago": 4,
            "quantity": 25
        }
    ]
    
    print("\n=== Creating Active Positions ===")
    
    for pos in active_positions:
        signal = TradingSignal(
            ticker=pos["ticker"],
            signal_type=pos["signal_type"],
            action=pos["action"],
            confidence=pos["confidence"],
            entry_price=pos["entry_price"],
            exit_price=None,  # 활성 포지션 (청산 안 함)
            exit_date=None,
            reasoning=pos["reasoning"],
            generated_at=datetime.now() - timedelta(days=pos["days_ago"]),
            alert_sent=True
        )
        
        db.add(signal)
        print(f"  [+] {pos['ticker']}: ${pos['entry_price']:.2f} (confidence: {pos['confidence']:.0%})")
    
    db.commit()
    print(f"\n  Total active positions: {len(active_positions)}")


def create_closed_positions(db):
    """청산된 포지션 (거래 내역) 데모 데이터 생성"""
    
    closed_positions = [
        {
            "ticker": "TSLA",
            "signal_type": "PRIMARY",
            "action": "BUY",
            "confidence": 0.75,
            "entry_price": 245.00,
            "exit_price": 268.50,
            "reasoning": "Robotaxi announcement catalyst. Delivery numbers beat estimates.",
            "days_held": 15,
            "days_ago_closed": 2
        },
        {
            "ticker": "META",
            "signal_type": "HIDDEN",
            "action": "BUY",
            "confidence": 0.80,
            "entry_price": 490.00,
            "exit_price": 525.30,
            "reasoning": "AI ad targeting improvements. Reality Labs losses reducing.",
            "days_held": 12,
            "days_ago_closed": 5
        },
        {
            "ticker": "AVGO",
            "signal_type": "PRIMARY",
            "action": "BUY",
            "confidence": 0.88,
            "entry_price": 135.00,
            "exit_price": 148.20,
            "reasoning": "VMware integration synergies. AI ASIC demand strong.",
            "days_held": 20,
            "days_ago_closed": 8
        },
        {
            "ticker": "INTC",
            "signal_type": "LOSER",
            "action": "BUY",
            "confidence": 0.62,
            "entry_price": 38.50,
            "exit_price": 35.80,
            "reasoning": "Foundry business struggles. AI chip market share declining.",
            "days_held": 10,
            "days_ago_closed": 3
        },
        {
            "ticker": "QCOM",
            "signal_type": "HIDDEN",
            "action": "BUY",
            "confidence": 0.73,
            "entry_price": 168.00,
            "exit_price": 175.60,
            "reasoning": "Edge AI chip demand. Snapdragon Elite X gaining traction.",
            "days_held": 8,
            "days_ago_closed": 1
        }
    ]
    
    print("\n=== Creating Closed Positions (Trade History) ===")
    
    for pos in closed_positions:
        exit_date = datetime.now() - timedelta(days=pos["days_ago_closed"])
        entry_date = exit_date - timedelta(days=pos["days_held"])
        
        return_pct = ((pos["exit_price"] - pos["entry_price"]) / pos["entry_price"]) * 100
        
        signal = TradingSignal(
            ticker=pos["ticker"],
            signal_type=pos["signal_type"],
            action=pos["action"],
            confidence=pos["confidence"],
            entry_price=pos["entry_price"],
            exit_price=pos["exit_price"],
            exit_date=exit_date,
            actual_return_pct=return_pct,
            reasoning=pos["reasoning"],
            generated_at=entry_date,
            alert_sent=True
        )
        
        db.add(signal)
        print(f"  [✓] {pos['ticker']}: ${pos['entry_price']:.2f} → ${pos['exit_price']:.2f} ({return_pct:+.2f}%)")
    
    db.commit()
    print(f"\n  Total closed positions: {len(closed_positions)}")


def clear_existing_signals(db):
    """기존 시그널 삭제 (선택사항)"""
    count = db.query(TradingSignal).count()
    
    if count > 0:
        print(f"\n⚠️  Found {count} existing signals in database")
        response = input("Clear existing signals? (y/N): ").strip().lower()
        
        if response == 'y':
            db.query(TradingSignal).delete()
            db.commit()
            print("  ✓ Cleared existing signals")
        else:
            print("  Keeping existing signals")


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("AI Trading System - Demo Data Seeder")
    print("=" * 60)
    
    try:
        # 데이터베이스 세션
        db = get_sync_session()
        
        # 기존 데이터 확인
        clear_existing_signals(db)
        
        # 활성 포지션 생성
        create_demo_positions(db)
        
        # 청산된 포지션 생성
        create_closed_positions(db)
        
        # 최종 확인
        total_signals = db.query(TradingSignal).count()
        active_count = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).count()
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Total Signals in DB: {total_signals}")
        print(f"  Active Positions:    {active_count}")
        print(f"  Closed Positions:    {total_signals - active_count}")
        print("\n✅ Demo data seeded successfully!")
        print("\n💡 Next Steps:")
        print("  1. Start backend: python -m uvicorn backend.api.main:app --reload --port 8000")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Open: http://localhost:3000/dashboard")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("  1. PostgreSQL is running (Docker or local)")
        print("  2. Database connection string is correct in .env")
        print("  3. Database tables are created (alembic upgrade head)")
        raise


if __name__ == "__main__":
    main()
