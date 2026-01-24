"""
Phase 4 검증 테스트 - Risk/Trader Conflict Resolution
"""

from backend.ai.mvp.conflict_resolver import (
    TraderSignal,
    RiskAssessment,
    resolve_trade,
    determine_execution_intent,
    calculate_risk_level,
    create_risk_assessment,
)

print('=' * 60)
print('Phase 4 검증 #1: Risk 30 이하 → 100% 진입')
print('=' * 60)

# 테스트 케이스 1: LOW Risk
trader = TraderSignal(
    direction="BUY",
    suggested_size=0.25,
    confidence=0.80,
    rationale="강한 매수 시그널",
    target_asset="QQQ"
)
risk = create_risk_assessment(risk_score=25)

resolved = resolve_trade(trader, risk)

print(f'\n입력: Risk={risk.risk_score} (LOW), Confidence={trader.confidence:.2f}')
print(f'결과: Size={resolved.size:.2%} (조정비율: {resolved.adjustment_ratio:.0%})')
print(f'기대: 25% (100% 진입)')
print(f'판정: {"✅ PASS" if resolved.size == 0.25 and resolved.adjustment_ratio == 1.0 else "❌ FAIL"}')

print('\n' + '=' * 60)
print('Phase 4 검증 #2: Risk 31-70 → 50% 진입')
print('=' * 60)

# 테스트 케이스 2: MEDIUM Risk
trader = TraderSignal(
    direction="BUY",
    suggested_size=0.30,
    confidence=0.75,
    rationale="중간 매수 시그널",
    target_asset="SPY"
)
risk = create_risk_assessment(risk_score=50)

resolved = resolve_trade(trader, risk)

print(f'\n입력: Risk={risk.risk_score} (MEDIUM), Confidence={trader.confidence:.2f}')
print(f'결과: Size={resolved.size:.2%} (조정비율: {resolved.adjustment_ratio:.0%})')
print(f'기대: 15% (50% 진입 = 30% × 0.5)')
print(f'판정: {"✅ PASS" if resolved.size == 0.15 and resolved.adjustment_ratio == 0.5 else "❌ FAIL"}')

print('\n' + '=' * 60)
print('Phase 4 검증 #3: Risk 70 초과 + Confidence < 0.9 → 거부')
print('=' * 60)

# 테스트 케이스 3: HIGH Risk + LOW Confidence
trader = TraderSignal(
    direction="BUY",
    suggested_size=0.20,
    confidence=0.60,
    rationale="약한 매수 시그널",
    target_asset="TSLA"
)
risk = create_risk_assessment(risk_score=80)

resolved = resolve_trade(trader, risk)

print(f'\n입력: Risk={risk.risk_score} (HIGH), Confidence={trader.confidence:.2f} < 0.9')
print(f'결과: Action={resolved.action}, Size={resolved.size:.2%}')
print(f'기대: REJECT, 0%')
print(f'판정: {"✅ PASS" if resolved.action == "REJECT" and resolved.size == 0.0 else "❌ FAIL"}')

print('\n' + '=' * 60)
print('Phase 4 검증 추가: Risk 70 초과 + Confidence ≥ 0.9 → 20% 정찰병')
print('=' * 60)

# 테스트 케이스 4: HIGH Risk + HIGH Confidence
trader = TraderSignal(
    direction="BUY",
    suggested_size=0.25,
    confidence=0.92,
    rationale="고위험 고신뢰 시그널",
    target_asset="NVDA"
)
risk = create_risk_assessment(risk_score=75)

resolved = resolve_trade(trader, risk)

print(f'\n입력: Risk={risk.risk_score} (HIGH), Confidence={trader.confidence:.2f} ≥ 0.9')
print(f'결과: Size={resolved.size:.2%} (조정비율: {resolved.adjustment_ratio:.0%})')
print(f'기대: 5% (20% 진입 = 25% × 0.2)')
print(f'판정: {"✅ PASS" if resolved.size == 0.05 and resolved.adjustment_ratio == 0.2 else "❌ FAIL"}')

print('\n' + '=' * 60)
print('Phase 4 검증 추가: AUTO 실행 조건')
print('=' * 60)

# 테스트 케이스 5: AUTO 조건
test_cases = [
    (0.90, "LOW", "AUTO"),
    (0.85, "LOW", "HUMAN_APPROVAL"),  # 경계값 (0.85는 포함 안 됨)
    (0.86, "LOW", "AUTO"),  # 0.85 초과
    (0.95, "MEDIUM", "HUMAN_APPROVAL"),
    (0.95, "HIGH", "HUMAN_APPROVAL"),
]

print('\n테스트 케이스:')
for confidence, risk_level, expected in test_cases:
    result = determine_execution_intent(confidence, risk_level)
    status = "✅" if result == expected else "❌"
    print(f'  {status} Confidence={confidence:.2f}, Risk={risk_level:6s} → {result:14s} (기대: {expected})')

print('\n' + '=' * 60)
print('✅ Phase 4 전체 검증 완료')
print('=' * 60)
