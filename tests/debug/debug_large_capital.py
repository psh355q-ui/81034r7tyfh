"""
Large Capital 디버깅

왜 ₩1B도 거래를 못했을까?
"""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.backtest.constitutional_backtest_engine import ConstitutionalBacktestEngine

print("\n" + "="*70)
print(" "*15 + "🔍 Large Capital 디버깅")
print("="*70 + "\n")

# ₩1B 백테스트 재실행 (상세 로그)
engine = ConstitutionalBacktestEngine(
    initial_capital=1_000_000_000,  # ₩1B
    start_date=datetime(2024, 11, 1),
    end_date=datetime(2024, 11, 30)
)

# 첫 거래 시도 시점의 상태 확인
print("초기 상태:")
print(f"  자본: ₩{engine.initial_capital:,}")
print(f"  10% 주문: ₩{engine.initial_capital * 0.10:,}")
print(f"  USD 환산: ${(engine.initial_capital * 0.10) / 1200:,.0f}")
print()

# 백테스트 실행
report = engine.run()

print("\n결과:")
print(f"  실행 거래: {report['trades']['approved']}건")
print(f"  거부 거래: {report['trades']['rejected']}건")
print()

# Shadow Trades 확인
if engine.shadow_trades:
    print("Shadow Trades (처음 3개):")
    for i, st in enumerate(engine.shadow_trades[:3]):
        print(f"\n  {i+1}. {st['ticker']} {st['action']}")
        print(f"     거부 이유: {st['rejection_reason']}")
        if st.get('violated_articles'):
            print(f"     위반 조항: {st['violated_articles']}")

print("\n" + "="*70 + "\n")
