"""
Trading Protocol Schema (Pydantic v2) - v2.3

ChatGPT/Gemini 합의 기반 JSON 스키마
- Closing/Morning 공용
- 자동매매/백테스트 연동 가능
- Human-in-the-loop 최소화

작성일: 2026-01-24
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class TrendDirection(str, Enum):
    """시장 추세 방향"""
    UP = "UP"
    SIDE = "SIDE"
    DOWN = "DOWN"


class RiskLevel(str, Enum):
    """리스크 레벨"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionType(str, Enum):
    """액션 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    INCREASE_EXPOSURE = "INCREASE_EXPOSURE"
    REDUCE_EXPOSURE = "REDUCE_EXPOSURE"


class ExecutionIntent(str, Enum):
    """실행 의도"""
    AUTO = "AUTO"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


# ============================================================================
# Sub-Models
# ============================================================================

class IndicatorValue(BaseModel):
    """개별 지표 값"""
    value: float = Field(description="현재 값")
    change: Optional[float] = Field(default=None, description="변화량 (절대값)")
    change_pct: Optional[float] = Field(default=None, description="변화율 (%)")
    signal: Optional[str] = Field(default=None, description="해석 (예: Bullish, Bearish)")


class CoreIndicators(BaseModel):
    """핵심 4대 지표 (불변)"""
    us10y: IndicatorValue = Field(description="10년물 국채 금리")
    vix: IndicatorValue = Field(description="변동성 지수")
    dxy: IndicatorValue = Field(description="달러 인덱스")
    sector_leadership: List[str] = Field(
        default_factory=list,
        description="섹터 로테이션 리더 (예: ['Technology', 'Healthcare'])"
    )


class MarketState(BaseModel):
    """시장 상태 (신호등)"""
    signal: Literal["🟢", "🟡", "🔴"] = Field(description="신호등")
    trend: TrendDirection = Field(description="추세 방향")
    risk_score: int = Field(ge=0, le=100, description="리스크 점수 (0-100)")
    risk_level: RiskLevel = Field(description="리스크 레벨")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도 (0-1)")
    top_action: str = Field(description="한 줄 결론/핵심 액션")


class ActionableScenario(BaseModel):
    """IF-THEN 시나리오"""
    case_id: str = Field(description="시나리오 ID (A, B, C, D)")
    condition: str = Field(description="조건 (예: US10Y < 4.10)")
    action: ActionType = Field(description="액션 타입")
    asset: str = Field(description="대상 자산 (예: QQQ, Technology)")
    size_pct: float = Field(ge=-1.0, le=1.0, description="비중 변화 (-1.0 ~ 1.0)")
    rationale: str = Field(description="근거")
    priority: Optional[int] = Field(default=None, ge=1, le=4, description="우선순위 (1-4)")


class PortfolioImpact(BaseModel):
    """포트폴리오 영향"""
    focus_assets: List[str] = Field(default_factory=list, description="주목 자산")
    cash_change_pct: float = Field(default=0.0, description="현금 비중 변화 (%)")
    equity_change_pct: float = Field(default=0.0, description="주식 비중 변화 (%)")
    commentary: str = Field(default="", description="포트폴리오 코멘터리")


class RiskManagement(BaseModel):
    """리스크 관리"""
    max_position_pct: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="최대 포지션 비중 (0-1)"
    )
    stop_loss_rule: str = Field(description="손절 규칙 (예: INDEX < 4950)")
    hedge_required: bool = Field(default=False, description="헷지 필요 여부")
    hedge_suggestion: Optional[str] = Field(default=None, description="헷지 제안")


class BacktestData(BaseModel):
    """백테스트 및 AI 고도화용 데이터"""
    model_version: str = Field(description="모델/프롬프트 버전")
    prompt_version: str = Field(default="v2.3", description="프롬프트 버전")
    predicted_horizon: str = Field(description="예상 유효 기간 (1D, 1W, 1M)")
    reasoning_hash: Optional[str] = Field(default=None, description="근거 데이터 스냅샷 해시")
    expected_reward_risk_ratio: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="기대 손익비"
    )
    data_sources: List[str] = Field(default_factory=list, description="사용된 데이터 소스")


class HumanCheckFlags(BaseModel):
    """Human Check 필요 항목"""
    rationale_check: bool = Field(default=True, description="논리 검증 필요")
    sizing_check: bool = Field(default=True, description="사이징 검증 필요")
    exit_plan_check: bool = Field(default=True, description="Exit Plan 검증 필요")


class ProtocolMeta(BaseModel):
    """프로토콜 메타데이터"""
    mode: str = Field(description="브리핑 모드 (CLOSING, MORNING, INTRADAY, KOREAN)")
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow, description="생성 시간 (UTC)")
    timestamp_kst: Optional[str] = Field(default=None, description="생성 시간 (KST)")
    market: str = Field(default="US", description="시장 (US, KR)")
    version: str = Field(default="2.3", description="프로토콜 버전")


class Narrative(BaseModel):
    """시장 내러티브"""
    market_story: str = Field(description="시장 스토리 (한 문장)")
    dominant_driver: str = Field(description="주요 동인 (예: Fed Policy, Earnings)")
    key_events: List[str] = Field(default_factory=list, description="주요 이벤트")


# ============================================================================
# Main Protocol
# ============================================================================

class TradingProtocol(BaseModel):
    """
    트레이딩 프로토콜 (최종 JSON 스키마) - v2.3

    특징:
    - Closing/Morning 공용
    - 자동매매/백테스트 연동 가능
    - Human-in-the-loop 최소화 (3가지만 체크)
    """

    # 메타데이터
    meta: ProtocolMeta = Field(description="프로토콜 메타데이터")

    # 시장 상태 (신호등)
    market_state: MarketState = Field(description="시장 상태")

    # 핵심 4대 지표
    core_indicators: CoreIndicators = Field(description="핵심 지표")

    # 시장 내러티브
    narrative: Narrative = Field(description="시장 내러티브")

    # 실행 시나리오 (IF-THEN)
    actionable_scenarios: List[ActionableScenario] = Field(
        default_factory=list,
        max_length=4,
        description="실행 시나리오 (최대 4개)"
    )

    # 포트폴리오 영향
    portfolio_impact: PortfolioImpact = Field(description="포트폴리오 영향")

    # 리스크 관리
    risk_management: RiskManagement = Field(description="리스크 관리")

    # 백테스트 데이터 (선택)
    backtest_data: Optional[BacktestData] = Field(default=None, description="백테스트 데이터")

    # Human 체크 필요 여부
    human_check_required: HumanCheckFlags = Field(
        default_factory=HumanCheckFlags,
        description="Human Check 항목"
    )

    # 실행 의도 (AUTO vs HUMAN_APPROVAL)
    execution_intent: ExecutionIntent = Field(
        default=ExecutionIntent.HUMAN_APPROVAL,
        description="실행 의도"
    )

    # 원본 브리핑 (마크다운)
    raw_briefing: Optional[str] = Field(default=None, description="원본 마크다운 브리핑")

    @field_validator('actionable_scenarios')
    @classmethod
    def validate_scenarios_count(cls, v):
        """시나리오는 최대 4개"""
        if len(v) > 4:
            raise ValueError("actionable_scenarios must have at most 4 items")
        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """DB 저장용 딕셔너리 변환"""
        return {
            "mode": self.meta.mode,
            "execution_intent": self.execution_intent.value,
            "market_trend": self.market_state.trend.value,
            "risk_level": self.market_state.risk_level.value,
            "risk_score": self.market_state.risk_score,
            "full_report_json": self.model_dump(mode='json'),
            "target_asset": self.actionable_scenarios[0].asset if self.actionable_scenarios else None,
            "suggested_action": self.actionable_scenarios[0].action.value if self.actionable_scenarios else None,
            "suggested_size_pct": self.actionable_scenarios[0].size_pct if self.actionable_scenarios else None,
            "expected_rr_ratio": self.backtest_data.expected_reward_risk_ratio if self.backtest_data else None,
            "model_version": self.backtest_data.model_version if self.backtest_data else None,
            "prompt_version": self.backtest_data.prompt_version if self.backtest_data else "v2.3",
        }

    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "mode": "CLOSING",
                    "timestamp_utc": "2026-01-24T00:40:00Z",
                    "market": "US",
                    "version": "2.3"
                },
                "market_state": {
                    "signal": "🟢",
                    "trend": "UP",
                    "risk_score": 35,
                    "risk_level": "MEDIUM",
                    "confidence": 0.78,
                    "top_action": "기술주 비중 확대 유지"
                },
                "core_indicators": {
                    "us10y": {"value": 4.15, "change": 0.05, "change_pct": 1.2, "signal": "Neutral"},
                    "vix": {"value": 14.5, "change": -0.8, "change_pct": -5.2, "signal": "Bullish"},
                    "dxy": {"value": 103.2, "change": 0.3, "change_pct": 0.29, "signal": "Neutral"},
                    "sector_leadership": ["Technology", "Communication Services"]
                },
                "narrative": {
                    "market_story": "실적 시즌 호조로 기술주 상승 지속",
                    "dominant_driver": "Earnings",
                    "key_events": ["NVDA 실적 발표", "Fed 의사록 공개"]
                },
                "actionable_scenarios": [
                    {
                        "case_id": "A",
                        "condition": "US10Y < 4.20",
                        "action": "INCREASE_EXPOSURE",
                        "asset": "QQQ",
                        "size_pct": 0.05,
                        "rationale": "금리 안정 시 기술주 선호",
                        "priority": 1
                    }
                ],
                "portfolio_impact": {
                    "focus_assets": ["QQQ", "NVDA", "MSFT"],
                    "cash_change_pct": -5.0,
                    "equity_change_pct": 5.0,
                    "commentary": "기술주 비중 5% 확대"
                },
                "risk_management": {
                    "max_position_pct": 0.25,
                    "stop_loss_rule": "QQQ < 480",
                    "hedge_required": False
                },
                "execution_intent": "HUMAN_APPROVAL"
            }
        }


# ============================================================================
# Factory Functions
# ============================================================================

def create_empty_protocol(mode: str) -> TradingProtocol:
    """빈 프로토콜 생성 (기본값)"""
    return TradingProtocol(
        meta=ProtocolMeta(mode=mode),
        market_state=MarketState(
            signal="🟡",
            trend=TrendDirection.SIDE,
            risk_score=50,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.5,
            top_action="데이터 부족 - 관망"
        ),
        core_indicators=CoreIndicators(
            us10y=IndicatorValue(value=0.0),
            vix=IndicatorValue(value=0.0),
            dxy=IndicatorValue(value=0.0),
            sector_leadership=[]
        ),
        narrative=Narrative(
            market_story="데이터 수집 중",
            dominant_driver="Unknown",
            key_events=[]
        ),
        actionable_scenarios=[],
        portfolio_impact=PortfolioImpact(
            focus_assets=[],
            cash_change_pct=0.0,
            equity_change_pct=0.0,
            commentary=""
        ),
        risk_management=RiskManagement(
            max_position_pct=0.1,
            stop_loss_rule="None",
            hedge_required=False
        ),
        execution_intent=ExecutionIntent.HUMAN_APPROVAL
    )


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TradingProtocol Schema Test")
    print("=" * 60)

    # 빈 프로토콜 생성
    protocol = create_empty_protocol("CLOSING")
    print(f"\n✅ Empty protocol created: {protocol.meta.mode}")

    # JSON 스키마 출력
    import json
    schema = TradingProtocol.model_json_schema()
    print(f"\n📋 JSON Schema (first 500 chars):")
    print(json.dumps(schema, indent=2, ensure_ascii=False)[:500] + "...")

    # DB 딕셔너리 변환
    db_dict = protocol.to_db_dict()
    print(f"\n💾 DB Dict keys: {list(db_dict.keys())}")

    # 예제 프로토콜 생성
    from datetime import datetime

    example_protocol = TradingProtocol(
        meta=ProtocolMeta(mode="CLOSING", market="US"),
        market_state=MarketState(
            signal="🟢",
            trend=TrendDirection.UP,
            risk_score=35,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.78,
            top_action="기술주 비중 확대"
        ),
        core_indicators=CoreIndicators(
            us10y=IndicatorValue(value=4.15, change=0.05, signal="Neutral"),
            vix=IndicatorValue(value=14.5, change=-0.8, signal="Bullish"),
            dxy=IndicatorValue(value=103.2, change=0.3, signal="Neutral"),
            sector_leadership=["Technology", "Healthcare"]
        ),
        narrative=Narrative(
            market_story="실적 시즌 호조로 상승 지속",
            dominant_driver="Earnings",
            key_events=["NVDA 실적 발표"]
        ),
        actionable_scenarios=[
            ActionableScenario(
                case_id="A",
                condition="US10Y < 4.20",
                action=ActionType.INCREASE_EXPOSURE,
                asset="QQQ",
                size_pct=0.05,
                rationale="금리 안정 시 기술주 선호",
                priority=1
            )
        ],
        portfolio_impact=PortfolioImpact(
            focus_assets=["QQQ", "NVDA"],
            cash_change_pct=-5.0,
            equity_change_pct=5.0,
            commentary="기술주 비중 5% 확대"
        ),
        risk_management=RiskManagement(
            max_position_pct=0.25,
            stop_loss_rule="QQQ < 480",
            hedge_required=False
        ),
        execution_intent=ExecutionIntent.HUMAN_APPROVAL
    )

    print(f"\n✅ Example protocol created successfully")
    print(f"   Market State: {example_protocol.market_state.signal} {example_protocol.market_state.trend.value}")
    print(f"   Execution Intent: {example_protocol.execution_intent.value}")
    print(f"   Scenarios: {len(example_protocol.actionable_scenarios)}")
