"""
Phase 5 검증 테스트 - 3단 깔때기 구조
"""

from backend.ai.reporters.funnel_generator import (
    FunnelGenerator,
    MarketSignal,
    TrendDirection,
)

print('=' * 60)
print('Phase 5 검증 #1: 신호등 출력 (🟢🟡🔴)')
print('=' * 60)

# VIX 시나리오별 신호등 테스트
test_cases = [
    {
        'name': 'LOW Risk (VIX=14)',
        'indicators': {
            'vix': {'value': 14.0},
            'us10y': {'day_change_bp': 2.0},
            'sector_leadership': ['Technology', 'Healthcare']
        },
        'expected_signal': '🟢',
        'expected_trend': 'UP'
    },
    {
        'name': 'MEDIUM Risk (VIX=20)',
        'indicators': {
            'vix': {'value': 20.0},
            'us10y': {'day_change_bp': 5.0},
            'sector_leadership': ['Energy', 'Financials']
        },
        'expected_signal': '🟡',
        'expected_trend': 'SIDE'
    },
    {
        'name': 'HIGH Risk (VIX=32)',
        'indicators': {
            'vix': {'value': 32.0},
            'us10y': {'day_change_bp': -8.0},
            'sector_leadership': ['Utilities', 'Healthcare']
        },
        'expected_signal': '🔴',
        'expected_trend': 'DOWN'
    }
]

generator = FunnelGenerator()

for tc in test_cases:
    funnel = generator.generate(tc['indicators'], [])
    ms = funnel['market_state']
    
    signal_match = ms['signal'] == tc['expected_signal']
    trend_match = ms['trend'] == tc['expected_trend']
    
    print(f"\n{tc['name']}")
    print(f"  결과: {ms['signal']} {ms['trend']} (Risk={ms['risk_score']})")
    print(f"  기대: {tc['expected_signal']} {tc['expected_trend']}")
    print(f"  판정: {'✅ PASS' if signal_match and trend_match else '❌ FAIL'}")

print('\n✅ 신호등 출력 검증 완료')

print('\n' + '=' * 60)
print('Phase 5 검증 #2: IF-THEN 시나리오 4개 이하')
print('=' * 60)

# 시나리오 5개 입력 → 4개만 출력
scenarios = [
    {'condition': 'A', 'action': 'BUY', 'asset': 'QQQ', 'size_pct': 0.1, 'rationale': 'R1', 'priority': 1},
    {'condition': 'B', 'action': 'SELL', 'asset': 'SPY', 'size_pct': 0.1, 'rationale': 'R2', 'priority': 2},
    {'condition': 'C', 'action': 'HOLD', 'asset': 'DIA', 'size_pct': 0.0, 'rationale': 'R3', 'priority': 3},
    {'condition': 'D', 'action': 'BUY', 'asset': 'IWM', 'size_pct': 0.1, 'rationale': 'R4', 'priority': 4},
    {'condition': 'E', 'action': 'BUY', 'asset': 'NVDA', 'size_pct': 0.05, 'rationale': 'R5', 'priority': 5},
]

funnel = generator.generate({'vix': {'value': 15}}, scenarios)
output_scenarios = funnel['actionable_scenarios']

print(f"\n입력: {len(scenarios)}개 시나리오")
print(f"출력: {len(output_scenarios)}개 시나리오")
print(f"기대: 최대 4개")
print(f"판정: {'✅ PASS' if len(output_scenarios) <= 4 else '❌ FAIL'}")

# Case ID 확인
case_ids = [s['case'] for s in output_scenarios]
print(f"\nCase IDs: {', '.join(case_ids)}")
print(f"기대: A, B, C, D")
print(f"판정: {'✅ PASS' if case_ids == ['A', 'B', 'C', 'D'] else '❌ FAIL'}")

print('\n✅ 시나리오 제한 검증 완료')

print('\n' + '=' * 60)
print('Phase 5 검증 #3: 포트폴리오 영향 분석')
print('=' * 60)

# 매수/매도 시나리오로 비중 변화 테스트
buy_sell_scenarios = [
    {'condition': 'C1', 'action': 'BUY', 'asset': 'QQQ', 'size_pct': 0.15, 'rationale': 'R1'},
    {'condition': 'C2', 'action': 'SELL', 'asset': 'SPY', 'size_pct': -0.10, 'rationale': 'R2'},
    {'condition': 'C3', 'action': 'INCREASE_EXPOSURE', 'asset': 'NVDA', 'size_pct': 0.05, 'rationale': 'R3'},
]

funnel = generator.generate({'vix': {'value': 18}}, buy_sell_scenarios)
pi = funnel['portfolio_impact']

print(f"\n입력:")
print(f"  BUY QQQ 15%")
print(f"  SELL SPY 10%")
print(f"  INCREASE NVDA 5%")

print(f"\n결과:")
print(f"  Focus Assets: {', '.join(pi['focus_assets'])}")
print(f"  Cash Change: {pi['cash_change_pct']*100:+.1f}%")
print(f"  Equity Change: {pi['equity_change_pct']*100:+.1f}%")
print(f"  Commentary: {pi['commentary']}")

# 검증: 매수 20% - 매도 10% = 순 매수 10% → 현금 -10%, 주식 +10%
expected_cash = -0.10  # 순 매수이므로 현금 감소
expected_equity = 0.10  # 주식 증가

cash_correct = abs(pi['cash_change_pct'] - expected_cash) < 0.01
equity_correct = abs(pi['equity_change_pct'] - expected_equity) < 0.01

print(f"\n기대:")
print(f"  Cash: {expected_cash*100:+.1f}%")
print(f"  Equity: {expected_equity*100:+.1f}%")
print(f"판정: {'✅ PASS' if cash_correct and equity_correct else '❌ FAIL'}")

print('\n✅ 포트폴리오 영향 분석 검증 완료')

print('\n' + '=' * 60)
print('✅ Phase 5 전체 검증 완료')
print('=' * 60)
