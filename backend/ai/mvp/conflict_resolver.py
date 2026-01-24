"""
Risk vs Trader Agent Conflict Resolver - v2.3

핵심 원칙: "Risk First, Profit Second"
- Risk Agent = Size(비중) 조절
- Trader Agent = Direction(방향) 결정

ChatGPT/Gemini 합의 기반 충돌 해결 로직

작성일: 2026-01-24
"""

from dataclasses import dataclass
from typing import Literal, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TraderSignal:
    """Trader Agent 시그널"""
    direction: Literal["BUY", "SELL", "HOLD"]
    suggested_size: float  # 0.0 ~ 1.0 (포트폴리오 비중)
    confidence: float  # 0.0 ~ 1.0
    rationale: str
    target_asset: str


@dataclass
class RiskAssessment:
    """Risk Agent 평가"""
    risk_score: int  # 0-100
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    max_size_allowed: float  # 0.0 ~ 1.0
    veto_reason: Optional[str] = None


@dataclass
class ResolvedTrade:
    """최종 결정"""
    action: Literal["BUY", "SELL", "HOLD", "REJECT"]
    size: float  # 최종 포지션 사이즈 (0.0 ~ 1.0)
    execution_intent: Literal["AUTO", "HUMAN_APPROVAL"]
    message: str
    original_trader_signal: TraderSignal
    risk_assessment: RiskAssessment
    adjustment_ratio: float  # 조정 비율 (0.0 ~ 1.0)


def resolve_trade(
    trader_signal: TraderSignal,
    risk_assessment: RiskAssessment
) -> ResolvedTrade:
    """
    Trader Agent와 Risk Agent 충돌 해결
    
    규칙 (ChatGPT/Gemini 합의):
    - Risk Score ≤ 30 (LOW): 100% 진입
    - Risk Score 31-70 (MEDIUM): 50% 진입
    - Risk Score > 70 (HIGH):
        - Confidence ≥ 0.9: 20% 진입 (정찰병)
        - Confidence < 0.9: 진입 거부
    
    Args:
        trader_signal: Trader Agent의 시그널
        risk_assessment: Risk Agent의 평가
    
    Returns:
        ResolvedTrade 객체 (최종 결정)
    """
    base_size = trader_signal.suggested_size
    risk_score = risk_assessment.risk_score
    confidence = trader_signal.confidence
    
    logger.info(
        f"Resolving trade: {trader_signal.direction} {trader_signal.target_asset}, "
        f"Size={base_size:.2%}, Confidence={confidence:.2f}, Risk={risk_score}"
    )
    
    # LOW Risk (≤ 30)
    if risk_score <= 30:
        final_size = base_size
        adjustment_ratio = 1.0
        intent = determine_execution_intent(confidence, "LOW")
        message = f"✅ 적극 매수 (Risk Low={risk_score})"
        action = trader_signal.direction
        
        logger.info(f"LOW Risk: 100% position, intent={intent}")
    
    # MEDIUM Risk (31-70)
    elif risk_score <= 70:
        final_size = base_size * 0.5
        adjustment_ratio = 0.5
        intent = "HUMAN_APPROVAL"
        message = f"⚠️ 비중 축소 진입 ({final_size*100:.0f}% = 50% of {base_size*100:.0f}%)"
        action = trader_signal.direction
        
        logger.info(f"MEDIUM Risk: 50% position reduction")
    
    # HIGH Risk (> 70)
    else:
        if confidence >= 0.9:
            final_size = base_size * 0.2
            adjustment_ratio = 0.2
            intent = "HUMAN_APPROVAL"
            message = f"🔶 초소량 정찰병 투입 ({final_size*100:.0f}% = 20% of {base_size*100:.0f}%)"
            action = trader_signal.direction
            
            logger.warning(f"HIGH Risk + HIGH Confidence: 20% scout position")
        else:
            final_size = 0.0
            adjustment_ratio = 0.0
            intent = "HUMAN_APPROVAL"
            message = f"🚫 리스크 과다로 진입 거부 (Risk={risk_score}, Confidence={confidence:.2f} < 0.9)"
            action = "REJECT"
            
            logger.warning(f"HIGH Risk + LOW Confidence: REJECTED")
    
    return ResolvedTrade(
        action=action,
        size=round(final_size, 4),
        execution_intent=intent,
        message=message,
        original_trader_signal=trader_signal,
        risk_assessment=risk_assessment,
        adjustment_ratio=adjustment_ratio
    )


def determine_execution_intent(
    trader_confidence: float,
    risk_level: str
) -> Literal["AUTO", "HUMAN_APPROVAL"]:
    """
    자동 실행 여부 결정
    
    AUTO 조건 (단 하나):
    Trader_Confidence > 0.85 AND Risk_Level == 'LOW'
    
    Args:
        trader_confidence: Trader의 신뢰도 (0-1)
        risk_level: Risk 레벨 ('LOW', 'MEDIUM', 'HIGH')
    
    Returns:
        'AUTO' 또는 'HUMAN_APPROVAL'
    """
    if trader_confidence > 0.85 and risk_level == "LOW":
        logger.info(f"AUTO execution: Confidence={trader_confidence:.2f} > 0.85 AND Risk=LOW")
        return "AUTO"
    
    logger.info(f"HUMAN_APPROVAL required: Confidence={trader_confidence:.2f}, Risk={risk_level}")
    return "HUMAN_APPROVAL"


def calculate_risk_level(risk_score: int) -> Literal["LOW", "MEDIUM", "HIGH"]:
    """
    Risk Score를 Risk Level로 변환
    
    - 0-30: LOW
    - 31-70: MEDIUM
    - 71-100: HIGH
    
    Args:
        risk_score: 리스크 점수 (0-100)
    
    Returns:
        Risk Level
    """
    if risk_score <= 30:
        return "LOW"
    elif risk_score <= 70:
        return "MEDIUM"
    else:
        return "HIGH"


def create_risk_assessment(risk_score: int, veto_reason: Optional[str] = None) -> RiskAssessment:
    """
    Risk Score로부터 RiskAssessment 생성 (편의 함수)
    
    Args:
        risk_score: 리스크 점수 (0-100)
        veto_reason: 거부 사유 (선택)
    
    Returns:
        RiskAssessment 객체
    """
    risk_level = calculate_risk_level(risk_score)
    
    # Risk Level에 따른 최대 허용 사이즈
    if risk_level == "LOW":
        max_size = 0.30  # 최대 30%
    elif risk_level == "MEDIUM":
        max_size = 0.15  # 최대 15%
    else:
        max_size = 0.05  # 최대 5%
    
    return RiskAssessment(
        risk_score=risk_score,
        risk_level=risk_level,
        max_size_allowed=max_size,
        veto_reason=veto_reason
    )


# ============================================================================
# Bulk Resolution
# ============================================================================

def resolve_multiple_trades(
    signals: list[TraderSignal],
    risk_assessment: RiskAssessment
) -> list[ResolvedTrade]:
    """
    여러 Trader Signal을 한 번에 해결
    
    Args:
        signals: Trader Signal 리스트
        risk_assessment: 공통 Risk Assessment
    
    Returns:
        ResolvedTrade 리스트
    """
    resolved = []
    
    for signal in signals:
        trade = resolve_trade(signal, risk_assessment)
        resolved.append(trade)
    
    logger.info(f"Resolved {len(resolved)} trades")
    return resolved


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Risk/Trader Conflict Resolver Test")
    print("=" * 60)
    
    # 테스트 시나리오
    test_scenarios = [
        {
            "name": "LOW Risk + HIGH Confidence → AUTO",
            "trader": TraderSignal(
                direction="BUY",
                suggested_size=0.25,
                confidence=0.90,
                rationale="강한 매수 시그널",
                target_asset="QQQ"
            ),
            "risk": create_risk_assessment(risk_score=25)
        },
        {
            "name": "MEDIUM Risk → 50% 진입",
            "trader": TraderSignal(
                direction="BUY",
                suggested_size=0.20,
                confidence=0.75,
                rationale="중간 매수 시그널",
                target_asset="SPY"
            ),
            "risk": create_risk_assessment(risk_score=50)
        },
        {
            "name": "HIGH Risk + HIGH Confidence → 20% 정찰병",
            "trader": TraderSignal(
                direction="BUY",
                suggested_size=0.30,
                confidence=0.92,
                rationale="고위험 고신뢰 시그널",
                target_asset="NVDA"
            ),
            "risk": create_risk_assessment(risk_score=75)
        },
        {
            "name": "HIGH Risk + LOW Confidence → REJECT",
            "trader": TraderSignal(
                direction="BUY",
                suggested_size=0.25,
                confidence=0.60,
                rationale="약한 매수 시그널",
                target_asset="TSLA"
            ),
            "risk": create_risk_assessment(risk_score=80)
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"시나리오 {i}: {scenario['name']}")
        print(f"{'='*60}")
        
        trader = scenario['trader']
        risk = scenario['risk']
        
        print(f"\n입력:")
        print(f"  Trader: {trader.direction} {trader.target_asset}")
        print(f"  Suggested Size: {trader.suggested_size:.2%}")
        print(f"  Confidence: {trader.confidence:.2f}")
        print(f"  Risk Score: {risk.risk_score} ({risk.risk_level})")
        
        resolved = resolve_trade(trader, risk)
        
        print(f"\n결과:")
        print(f"  Action: {resolved.action}")
        print(f"  Final Size: {resolved.size:.2%} (조정 비율: {resolved.adjustment_ratio:.0%})")
        print(f"  Execution Intent: {resolved.execution_intent}")
        print(f"  Message: {resolved.message}")
    
    print("\n" + "=" * 60)
    print("✅ Conflict Resolution Test Complete")
    print("=" * 60)
