"""
Persona System Test Script

Phase 3: Persona-based Trading
Date: 2026-01-25

Purpose:
    Persona 시스템의 기능을 테스트합니다.
    - 데이터베이스 모델 테스트
    - Persona Trading Service 테스트
    - Persona Integration Service 테스트
    - API 엔드포인트 테스트
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    Persona,
    PortfolioAllocation,
    UserPersonaPreference,
    Base,
)
from backend.services.persona_trading_service import PersonaTradingService
from backend.services.persona_integration_service import PersonaIntegrationService
from backend.ai.router.persona_router import PersonaMode, get_persona_router


# ============================================================================
# Test Configuration
# ============================================================================

# Use test database
TEST_DATABASE_URL = "sqlite:///test_persona.db"

# Create engine
engine = create_engine(TEST_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# Test Functions
# ============================================================================

def setup_database():
    """테스트 데이터베이스 설정"""
    print("\n=== Setting up test database ===")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    return SessionLocal()


def teardown_database(db: Session):
    """테스트 데이터베이스 정리"""
    print("\n=== Cleaning up test database ===")
    
    db.close()
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("✅ Database tables dropped")


def test_persona_models(db: Session):
    """Persona 모델 테스트"""
    print("\n=== Testing Persona Models ===")
    
    # 1. Persona 생성 테스트
    print("\n1. Testing Persona creation...")
    try:
        persona = Persona(
            name="TEST_CONSERVATIVE",
            display_name="테스트 보수형",
            description="테스트용 보수형 페르소나",
            risk_tolerance="LOW",
            investment_horizon="LONG",
            return_expectation="MODERATE",
            trader_weight=0.10,
            risk_weight=0.40,
            analyst_weight=0.50,
            stock_allocation=0.50,
            bond_allocation=0.40,
            cash_allocation=0.10,
            max_position_size=0.08,
            max_sector_exposure=0.25,
            stop_loss_pct=0.03,
            leverage_allowed=False,
            max_leverage_pct=0.0,
            yield_trap_detector=True,
            dividend_calendar=True,
            noise_filter=True,
            thesis_violation=False,
            max_agent_disagreement=0.40,
            min_avg_confidence=0.60,
            is_active=True,
            is_default=False,
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        print(f"✅ Persona created: {persona.display_name} (ID: {persona.id})")
    except Exception as e:
        print(f"❌ Persona creation failed: {e}")
        return False
    
    # 2. Portfolio Allocation 생성 테스트
    print("\n2. Testing Portfolio Allocation creation...")
    try:
        allocation = PortfolioAllocation(
            persona_id=persona.id,
            asset_class="STOCK",
            target_allocation=0.50,
            current_allocation=0.45,
            deviation=0.05,
            rebalance_threshold=0.05,
        )
        db.add(allocation)
        db.commit()
        db.refresh(allocation)
        print(f"✅ Portfolio Allocation created: {allocation.asset_class} (ID: {allocation.id})")
    except Exception as e:
        print(f"❌ Portfolio Allocation creation failed: {e}")
        return False
    
    # 3. User Persona Preference 생성 테스트
    print("\n3. Testing User Persona Preference creation...")
    try:
        preference = UserPersonaPreference(
            user_id="test_user_001",
            persona_id=persona.id,
            last_switched_at=datetime.now(),
            switch_count=1,
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)
        print(f"✅ User Persona Preference created: {preference.user_id} (ID: {preference.id})")
    except Exception as e:
        print(f"❌ User Persona Preference creation failed: {e}")
        return False
    
    return True


def test_persona_trading_service(db: Session):
    """Persona Trading Service 테스트"""
    print("\n=== Testing Persona Trading Service ===")
    
    service = PersonaTradingService(db)
    
    # 1. Persona 조회 테스트
    print("\n1. Testing Persona retrieval...")
    try:
        persona = service.get_persona_by_name("TEST_CONSERVATIVE")
        if persona:
            print(f"✅ Persona retrieved: {persona.display_name}")
        else:
            print("❌ Persona not found")
            return False
    except Exception as e:
        print(f"❌ Persona retrieval failed: {e}")
        return False
    
    # 2. 포트폴리오 배분 계산 테스트
    print("\n2. Testing portfolio allocation calculation...")
    try:
        total_value = 100000.0
        current_allocations = {
            "STOCK": 0.45,
            "BOND": 0.35,
            "CASH": 0.20
        }
        
        allocation = service.calculate_portfolio_allocation(
            persona,
            total_value,
            current_allocations
        )
        
        print(f"✅ Portfolio allocation calculated:")
        for asset_class, info in allocation.items():
            print(f"   {asset_class}: target={info['target']:.1%}, current={info['current']:.1%}, rebalance={info['rebalance']}")
    except Exception as e:
        print(f"❌ Portfolio allocation calculation failed: {e}")
        return False
    
    # 3. 포지션 사이즈 계산 테스트
    print("\n3. Testing position size calculation...")
    try:
        confidence = 0.75
        risk_level = "MEDIUM"
        
        position_size = service.calculate_position_size(
            persona,
            total_value,
            confidence,
            risk_level
        )
        
        print(f"✅ Position size calculated: ${position_size:,.2f} ({position_size/total_value:.1%})")
    except Exception as e:
        print(f"❌ Position size calculation failed: {e}")
        return False
    
    # 4. 손절가 계산 테스트
    print("\n4. Testing stop loss calculation...")
    try:
        entry_price = 100.0
        
        stop_loss = service.calculate_stop_loss(persona, entry_price)
        
        print(f"✅ Stop loss calculated: ${stop_loss:.2f} (entry: ${entry_price:.2f})")
    except Exception as e:
        print(f"❌ Stop loss calculation failed: {e}")
        return False
    
    # 5. 포지션 제한 확인 테스트
    print("\n5. Testing position limit check...")
    try:
        position_value = 8000.0
        ticker = "AAPL"
        
        allowed, message = service.check_position_limit(
            persona,
            ticker,
            position_value,
            total_value
        )
        
        print(f"✅ Position limit check: allowed={allowed}, message={message}")
    except Exception as e:
        print(f"❌ Position limit check failed: {e}")
        return False
    
    # 6. 시그널 검증 테스트
    print("\n6. Testing signal validation...")
    try:
        signal_confidence = 0.75
        agent_disagreement = 0.33
        avg_confidence = 0.75
        
        allowed, message = service.validate_signal_with_persona(
            persona,
            signal_confidence,
            agent_disagreement,
            avg_confidence
        )
        
        print(f"✅ Signal validation: allowed={allowed}, message={message}")
    except Exception as e:
        print(f"❌ Signal validation failed: {e}")
        return False
    
    return True


def test_persona_router():
    """Persona Router 테스트"""
    print("\n=== Testing Persona Router ===")
    
    router = get_persona_router()
    
    # 1. 모드 전환 테스트
    print("\n1. Testing mode switching...")
    try:
        previous_mode = router.get_current_mode()
        print(f"   Current mode: {previous_mode.value}")
        
        new_mode = router.set_mode("dividend")
        print(f"   New mode: {new_mode.value}")
        
        weights = router.get_weights("dividend")
        print(f"   Weights: {weights}")
        
        print("✅ Mode switching successful")
    except Exception as e:
        print(f"❌ Mode switching failed: {e}")
        return False
    
    # 2. 설정 조회 테스트
    print("\n2. Testing config retrieval...")
    try:
        config = router.get_config("dividend")
        print(f"✅ Config retrieved: {config.description}")
    except Exception as e:
        print(f"❌ Config retrieval failed: {e}")
        return False
    
    # 3. 레버리지 확인 테스트
    print("\n3. Testing leverage check...")
    try:
        is_allowed = router.is_leverage_allowed("dividend")
        leverage_cap = router.get_leverage_cap("dividend")
        
        print(f"✅ Leverage check: allowed={is_allowed}, cap={leverage_cap:.1%}")
    except Exception as e:
        print(f"❌ Leverage check failed: {e}")
        return False
    
    return True


def test_persona_integration_service(db: Session):
    """Persona Integration Service 테스트"""
    print("\n=== Testing Persona Integration Service ===")
    
    service = PersonaIntegrationService(db)
    
    # 1. War Room 결정에 Persona 적용 테스트
    print("\n1. Testing War Room decision with Persona...")
    try:
        user_id = "test_user_001"
        ticker = "AAPL"
        action = "BUY"
        confidence = 0.75
        agent_votes = {
            "trader_mvp": {"action": "BUY", "confidence": 0.8, "reasoning": "Momentum positive"},
            "risk_mvp": {"action": "HOLD", "confidence": 0.7, "reasoning": "Risk elevated"},
            "analyst_mvp": {"action": "BUY", "confidence": 0.9, "reasoning": "Fundamentals strong"},
        }
        
        allowed, message, result = service.apply_persona_to_war_room_decision(
            user_id,
            ticker,
            action,
            confidence,
            agent_votes
        )
        
        print(f"✅ War Room decision with Persona: allowed={allowed}")
        print(f"   Message: {message}")
        print(f"   Persona: {result['persona_name']}")
        print(f"   Weighted decision: {result['weighted_decision']}")
    except Exception as e:
        print(f"❌ War Room decision with Persona failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. 주문 사이즈 계산 테스트
    print("\n2. Testing order size calculation...")
    try:
        user_id = "test_user_001"
        ticker = "AAPL"
        portfolio_value = 100000.0
        confidence = 0.75
        risk_level = "MEDIUM"
        
        order_size, result = service.calculate_order_size_with_persona(
            user_id,
            ticker,
            portfolio_value,
            confidence,
            risk_level
        )
        
        print(f"✅ Order size calculated: ${order_size:,.2f}")
        print(f"   Persona: {result['persona_name']}")
        print(f"   Position %: {result['position_pct']:.1%}")
    except Exception as e:
        print(f"❌ Order size calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 주문 검증 테스트
    print("\n3. Testing order validation...")
    try:
        user_id = "test_user_001"
        ticker = "AAPL"
        order_value = 8000.0
        portfolio_value = 100000.0
        
        allowed, message, result = service.validate_order_with_persona(
            user_id,
            ticker,
            order_value,
            portfolio_value
        )
        
        print(f"✅ Order validation: allowed={allowed}")
        print(f"   Message: {message}")
        print(f"   Position %: {result['position_pct']:.1%}")
    except Exception as e:
        print(f"❌ Order validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Persona System Test Suite")
    print("=" * 60)
    
    # Setup
    db = setup_database()
    
    # Run tests
    test_results = []
    
    # Test 1: Persona Models
    try:
        result = test_persona_models(db)
        test_results.append(("Persona Models", result))
    except Exception as e:
        print(f"\n❌ Persona Models test crashed: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Persona Models", False))
    
    # Test 2: Persona Trading Service
    try:
        result = test_persona_trading_service(db)
        test_results.append(("Persona Trading Service", result))
    except Exception as e:
        print(f"\n❌ Persona Trading Service test crashed: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Persona Trading Service", False))
    
    # Test 3: Persona Router
    try:
        result = test_persona_router()
        test_results.append(("Persona Router", result))
    except Exception as e:
        print(f"\n❌ Persona Router test crashed: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Persona Router", False))
    
    # Test 4: Persona Integration Service
    try:
        result = test_persona_integration_service(db)
        test_results.append(("Persona Integration Service", result))
    except Exception as e:
        print(f"\n❌ Persona Integration Service test crashed: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("Persona Integration Service", False))
    
    # Teardown
    teardown_database(db)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    # Overall result
    all_passed = all(result for _, result in test_results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
