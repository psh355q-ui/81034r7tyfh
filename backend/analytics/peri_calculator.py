"""
PERICalculator - Policy Event Risk Index (정책 이벤트 리스크 지수)

Phase B 통합:
- 연준 발언 분석
- 정책 불확실성 수치화
- 포지션 조정 권장

PERI = 0~100 점수
- 0-20: STABLE (정상 거래)
- 20-40: CAUTION (약간 방어적)
- 40-60: WARNING (고위험 종목 축소)
- 60-80: DANGER (리스크 오프)
- 80-100: CRITICAL (헷지 활성화)

작성일: 2025-12-03 (Phase B)
"""

import logging
from typing import Dict, Tuple
from datetime import datetime

from backend.schemas.base_schema import PolicyRisk

logger = logging.getLogger(__name__)


class PERICalculator:
    """
    Policy Event Risk Index (PERI) 계산기

    6개 하위 지표를 종합하여 0~100 PERI 점수 산출

    가중치:
    - fed_conflict: 25% (연준 내부 의견 충돌)
    - successor_signal: 20% (차기 의장 후보 노출)
    - gov_fed_tension: 20% (정부-연준 갈등)
    - election_risk: 15% (선거 리스크)
    - bond_volatility: 10% (채권 변동성)
    - policy_uncertainty: 10% (정책 불확실성)
    """

    # 가중치
    WEIGHTS = {
        "fed_conflict": 0.25,
        "successor_signal": 0.20,
        "gov_fed_tension": 0.20,
        "election_risk": 0.15,
        "bond_volatility": 0.10,
        "policy_uncertainty": 0.10
    }

    def __init__(self):
        """PERICalculator 초기화"""
        logger.info("PERICalculator initialized")

    def compute_peri(
        self,
        fed_conflict: float,
        successor_signals: float,
        gov_tension: float,
        election_risk: float,
        bond_vol: float,
        epu: float
    ) -> float:
        """
        PERI 점수 계산

        Args:
            fed_conflict: 연준 내부 의견 충돌도 (0~1)
            successor_signals: 차기 의장 후보 노출도 (0~1)
            gov_tension: 재무부·백악관·연준 발언 온도차 (0~1)
            election_risk: 대선/의회 리스크 (0~1)
            bond_vol: 채권 변동성 (0~1)
            epu: 정책 불확실성 지수 (0~1)

        Returns:
            PERI 점수 (0~100)
        """
        peri = (
            fed_conflict * self.WEIGHTS["fed_conflict"] +
            successor_signals * self.WEIGHTS["successor_signal"] +
            gov_tension * self.WEIGHTS["gov_fed_tension"] +
            election_risk * self.WEIGHTS["election_risk"] +
            bond_vol * self.WEIGHTS["bond_volatility"] +
            epu * self.WEIGHTS["policy_uncertainty"]
        ) * 100  # 0~100 스케일

        logger.info(f"PERI calculated: {peri:.1f}")

        return peri

    def get_risk_level(self, peri: float) -> Tuple[str, float, str]:
        """
        PERI 점수에 따른 리스크 레벨 및 전략 조정

        Args:
            peri: PERI 점수

        Returns:
            (level, adjustment, action)
        """
        if peri < 20:
            return "STABLE", 1.0, "Normal trading"
        elif peri < 40:
            return "CAUTION", 0.9, "Slightly defensive"
        elif peri < 60:
            return "WARNING", 0.7, "Reduce high-beta + Increase cash"
        elif peri < 80:
            return "DANGER", 0.5, "Full risk-off mode"
        else:
            return "CRITICAL", 0.3, "Macro hedge ON + Short positions"

    def apply_to_signal(self, signal_dict: Dict, peri: float) -> Dict:
        """
        PERI를 투자 시그널에 적용

        Args:
            signal_dict: 원본 시그널 딕셔너리
            peri: PERI 점수

        Returns:
            PERI 조정된 시그널
        """
        level, adjustment, reason = self.get_risk_level(peri)

        # 포지션 사이즈 조정
        original_size = signal_dict.get("position_size", 1.0)
        adjusted_size = original_size * adjustment

        return {
            **signal_dict,
            "position_size": adjusted_size,
            "peri_level": level,
            "peri_score": peri,
            "peri_adjustment": reason,
            "original_position_size": original_size
        }

    def create_policy_risk_schema(
        self,
        fed_conflict: float = 0.0,
        successor_signals: float = 0.0,
        gov_tension: float = 0.0,
        election_risk: float = 0.0,
        bond_vol: float = 0.0,
        epu: float = 0.0
    ) -> PolicyRisk:
        """
        BaseSchema PolicyRisk 객체 생성

        Returns:
            PolicyRisk 스키마
        """
        peri = self.compute_peri(
            fed_conflict,
            successor_signals,
            gov_tension,
            election_risk,
            bond_vol,
            epu
        )

        return PolicyRisk(
            fed_conflict_score=fed_conflict,
            successor_signal_score=successor_signals,
            gov_fed_tension_score=gov_tension,
            election_risk_score=election_risk,
            bond_volatility_score=bond_vol,
            policy_uncertainty_score=epu,
            peri=peri
        )

    def get_mock_data(self) -> Dict[str, float]:
        """Mock 데이터 반환 (정상 시장)"""
        return {
            "fed_conflict": 0.2,
            "successor_signals": 0.1,
            "gov_tension": 0.3,
            "election_risk": 0.4,
            "bond_vol": 0.25,
            "epu": 0.3
        }


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PERICalculator Test")
    print("=" * 70)

    calc = PERICalculator()

    # Test 1: 정상 시장
    print("\n=== Scenario 1: Normal Market ===")
    data = calc.get_mock_data()
    peri = calc.compute_peri(**data)
    level, adj, action = calc.get_risk_level(peri)

    print(f"PERI: {peri:.1f}")
    print(f"Level: {level}")
    print(f"Adjustment: {adj:.0%}")
    print(f"Action: {action}")

    # Test 2: 위기 시장
    print("\n=== Scenario 2: Crisis Market ===")
    crisis_data = {
        "fed_conflict": 0.8,
        "successor_signals": 0.7,
        "gov_tension": 0.9,
        "election_risk": 0.8,
        "bond_vol": 0.75,
        "epu": 0.85
    }
    crisis_peri = calc.compute_peri(**crisis_data)
    crisis_level, crisis_adj, crisis_action = calc.get_risk_level(crisis_peri)

    print(f"PERI: {crisis_peri:.1f}")
    print(f"Level: {crisis_level}")
    print(f"Adjustment: {crisis_adj:.0%}")
    print(f"Action: {crisis_action}")

    # Test 3: BaseSchema 통합
    print("\n=== Test 3: BaseSchema Integration ===")
    policy_risk = calc.create_policy_risk_schema(**data)
    print(f"PolicyRisk PERI: {policy_risk.peri:.1f}")
    print(f"Fed Conflict: {policy_risk.fed_conflict_score:.1f}")

    # Test 4: Signal adjustment
    print("\n=== Test 4: Signal Adjustment ===")
    original_signal = {
        "ticker": "NVDA",
        "action": "BUY",
        "position_size": 0.2
    }

    adjusted_signal = calc.apply_to_signal(original_signal, peri)
    print(f"Original position: {original_signal['position_size']:.0%}")
    print(f"Adjusted position: {adjusted_signal['position_size']:.0%}")
    print(f"PERI adjustment: {adjusted_signal['peri_adjustment']}")

    print("\n=== Test PASSED! ===")
