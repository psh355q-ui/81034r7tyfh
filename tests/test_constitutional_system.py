"""
Constitutional System Integration Test

Constitution + Shadow Trade + Shield Report 통합 테스트

작성일: 2025-12-15
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.constitution import Constitution, verify_on_startup
from backend.constitution.risk_limits import RiskLimits
from backend.constitution.allocation_rules import AllocationRules
from backend.constitution.trading_constraints import TradingConstraints


def test_constitution_integrity():
    """헌법 무결성 검증"""
    print("=== 1. Constitution Integrity Test ===\n")
    
    try:
        is_valid = verify_on_startup()
        print("✅ 헌법 무결성 검증 성공\n")
        return True
    except Exception as e:
        print(f"❌ 헌법 무결성 검증 실패: {e}\n")
        return False


def test_constitution_validation():
    """헌법 검증 로직 테스트"""
    print("=== 2. Constitution Validation Test ===\n")
    
    const = Constitution()
    
    # 헌법 요약
    print(const.get_constitution_summary())
    
    # 테스트 케이스 1: 정상 제안
    print("케이스 1: 정상 제안")
    proposal = {
        'ticker': 'AAPL',
        'action': 'BUY',
        'position_value': 15000,
        'order_value_usd': 15000,
        'is_approved': False
    }
    
    context = {
        'total_capital': 100000,
        'current_allocation': {'stock': 0.75, 'cash': 0.25},
        'market_regime': 'risk_on',
        'daily_trades': 2,
        'weekly_trades': 5,
        'daily_volume_usd': 5000000
    }
    
    is_valid, violations, violated_articles = const.validate_proposal(proposal, context)
    
    if is_valid:
        print("  ✅ 통과 (헌법 준수)\n")
    else:
        print(f"  ❌ 실패")
        for v in violations:
            print(f"     - {v}")
        print()
    
    # 테스트 케이스 2: 포지션 과다 (위반)
    print("케이스 2: 포지션 과다 (위반)")
    proposal_bad = {
        'ticker': 'TSLA',
        'action': 'BUY',
        'position_value': 25000,  # 25% > 20% 제한
        'order_value_usd': 25000,
        'is_approved': False
    }
    
    is_valid, violations, violated_articles = const.validate_proposal(proposal_bad, context)
    
    if not is_valid:
        print("  ✅ 정상 감지 (헌법 위반)")
        for v in violations:
            print(f"     - {v}")
        print(f"\n  위반 조항:")
        for article in violated_articles:
            print(f"     - {article}")
        print()
    else:
        print("  ❌ 위반을 감지하지 못함\n")
    
    # Circuit Breaker 테스트
    print("케이스 3: Circuit Breaker")
    should_trigger, reason = const.validate_circuit_breaker_trigger(
        daily_loss=-0.04,  # -4%
        total_drawdown=-0.08,
        vix=22
    )
    
    if should_trigger:
        print(f"  ✅ Circuit Breaker 발동: {reason}\n")
    else:
        print("  ✅ Circuit Breaker 미발동 (정상)\n")
    
    return True


def test_risk_limits():
    """Risk Limits 테스트"""
    print("=== 3. Risk Limits Test ===\n")
    
    print("손실 제한:")
    print(f"  일 최대 손실: {RiskLimits.MAX_DAILY_LOSS:.1%}")
    print(f"  최대 낙폭: {RiskLimits.MAX_DRAWDOWN:.1%}")
    print(f"  Circuit Breaker: {RiskLimits.DAILY_LOSS_CIRCUIT_BREAKER:.1%}")
    
    print("\n포지션 제한:")
    print(f"  단일 종목: {RiskLimits.MAX_POSITION_SIZE:.1%}")
    print(f"  섹터 노출: {RiskLimits.MAX_SECTOR_EXPOSURE:.1%}")
    
    print("\n변동성 제한:")
    print(f"  VIX 주의: {RiskLimits.VIX_CAUTION_THRESHOLD}")
    print(f"  VIX 위험: {RiskLimits.VIX_DANGER_THRESHOLD}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, violations = RiskLimits.validate_loss(-0.03, -0.08)
    print(f"  손실 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    is_valid, violations = RiskLimits.validate_position_size(15000, 100000)
    print(f"  포지션 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    print()
    return True


def test_allocation_rules():
    """Allocation Rules 테스트"""
    print("=== 4. Allocation Rules Test ===\n")
    
    print("체제별 배분:")
    for regime in ['risk_on', 'neutral', 'risk_off']:
        rules = AllocationRules.get_regime_allocation(regime)
        print(f"  {regime}: 주식 {rules['stock_min']:.1%}-{rules['stock_max']:.1%}, "
              f"현금 최소 {rules['cash_min']:.1%}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, violations = AllocationRules.validate_allocation(0.75, 0.25, 'risk_on')
    print(f"  Risk On 배분: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    # 리밸런싱
    current = {'stock': 0.65, 'cash': 0.35}
    target = {'stock': 0.75, 'cash': 0.25}
    needs, reasons = AllocationRules.needs_rebalancing(current, target)
    print(f"  리밸런싱 필요: {'✅ Yes' if needs else '❌ No'}")
    
    print()
    return True


def test_trading_constraints():
    """Trading Constraints 테스트"""
    print("=== 5. Trading Constraints Test ===\n")
    
    print("거래 제약:")
    print(f"  일 최대 거래: {TradingConstraints.MAX_DAILY_TRADES}회")
    print(f"  주 최대 거래: {TradingConstraints.MAX_WEEKLY_TRADES}회")
    print(f"  최소 보유: {TradingConstraints.MIN_HOLD_PERIOD_HOURS}시간")
    
    print("\n주문 크기:")
    print(f"  최소: ${TradingConstraints.MIN_ORDER_SIZE_USD:,}")
    print(f"  최대: ${TradingConstraints.MAX_ORDER_SIZE_USD:,}")
    
    print("\n안전 장치:")
    print(f"  인간 승인: {TradingConstraints.REQUIRE_HUMAN_APPROVAL}")
    print(f"  공매도 금지: {not TradingConstraints.ALLOW_SHORT_SELLING}")
    print(f"  레버리지 금지: {not TradingConstraints.ALLOW_LEVERAGE}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, _ = TradingConstraints.validate_order_timing(True, 10, 20)
    print(f"  시간 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    is_valid, _ = TradingConstraints.validate_order_size(10000, 100000, 5000000)
    print(f"  크기 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    is_valid, _ = TradingConstraints.validate_trade_frequency(2, 5)
    print(f"  빈도 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    print()
    return True


def run_all_tests():
    """모든 테스트 실행"""
    print("="*60)
    print(" "*15 + "🏛️ Constitutional System Test 🏛️")
    print("="*60)
    print()
    
    results = []
    
    # 1. 무결성
    results.append(("Constitution Integrity", test_constitution_integrity()))
    
    # 2. 검증
    results.append(("Constitution Validation", test_constitution_validation()))
    
    # 3. Risk Limits
    results.append(("Risk Limits", test_risk_limits()))
    
    # 4. Allocation Rules
    results.append(("Allocation Rules", test_allocation_rules()))
    
    # 5. Trading Constraints
    results.append(("Trading Constraints", test_trading_constraints()))
    
    # 결과 요약
    print("="*60)
    print(" "*20 + "📊 Test Results 📊")
    print("="*60)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print()
    print(f"Total: {passed}/{total} passed ({passed/total*100:.0f}%)")
    print()
    
    if passed == total:
        print("🎉 All tests passed! Constitutional System is ready!")
    else:
        print("⚠️ Some tests failed. Please review.")
    
    print()
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
