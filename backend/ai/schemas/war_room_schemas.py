"""
War Room MVP - Pydantic Schema Definitions

Structured Outputs를 위한 응답 스키마 정의
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime


class TraderOpinion(BaseModel):
    """Trader Agent MVP 응답 스키마"""
    agent: Literal['trader_mvp'] = 'trader_mvp'
    action: Literal['buy', 'sell', 'hold', 'pass']
    confidence: float = Field(ge=0.0, le=1.0, description="결정 신뢰도")
    opportunity_score: float = Field(ge=0.0, le=100.0, description="기회 점수")
    reasoning: str = Field(min_length=10, description="추천 근거")
    entry_price: Optional[float] = Field(default=None, gt=0)
    exit_price: Optional[float] = Field(default=None, gt=0, description="목표 청산가")
    stop_loss: Optional[float] = Field(default=None, gt=0)
    timeframe: Optional[str] = Field(default=None, description="예상 보유기간")
    momentum_strength: Literal['weak', 'moderate', 'strong'] = Field(default='weak')
    technical_indicators: Optional[Dict[str, Any]] = None
    catalysts: List[str] = Field(default_factory=list)
    
    # Enhanced Fields (Phase 1)
    risk_reward_ratio: Optional[float] = Field(default=None, description="손익비")
    support_levels: List[float] = Field(default_factory=list, description="지지 라인")
    resistance_levels: List[float] = Field(default_factory=list, description="저항 라인")
    volume_analysis: Optional[Dict[str, Any]] = Field(default=None, description="거래량 분석")
    timeframe_details: Optional[Dict[str, Any]] = Field(default=None, description="상세 타임프레임")

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "trader_mvp",
                "action": "buy",
                "confidence": 0.85,
                "opportunity_score": 75.0,
                "reasoning": "Strong uptrend with RSI confirmation and volume breakout",
                "entry_price": 140.50,
                "exit_price": 155.00,
                "timeframe": "1w",
                "momentum_strength": "strong"
            }
        }


class RiskOpinion(BaseModel):
    """Risk Agent MVP 응답 스키마"""
    agent: Literal['risk_mvp'] = 'risk_mvp'
    action: Literal['approve', 'reject', 'reduce_size']
    confidence: float = Field(ge=0.0, le=1.0, description="결정 신뢰도")
    position_size: float = Field(ge=0.0, le=100.0, description="포지션 크기 %")
    risk_level: Literal['low', 'medium', 'moderate', 'high', 'extreme']
    stop_loss: float = Field(gt=0, description="Stop loss 가격")
    stop_loss_pct: Optional[float] = Field(default=None, description="Stop loss %")
    take_profit_pct: Optional[float] = Field(default=None, description="Take profit %")
    reasoning: str = Field(min_length=10, description="리스크 분석 근거")
    sentiment_score: Optional[float] = Field(default=0.0, ge=-1.0, le=1.0)
    volatility_risk: Optional[float] = Field(default=None)
    dividend_risk: Optional[str] = Field(default='none')
    dividend_risk: Optional[str] = Field(default='none')
    kelly_calculation: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)

    # Enhanced Fields (Phase 1)
    position_sizing_recommendation: Optional[Dict[str, Any]] = None
    var_95: Optional[float] = Field(default=None, description="VaR 95%")
    beta: Optional[float] = Field(default=None, description="Portfolio Beta")
    max_loss_scenario: Optional[Dict[str, Any]] = None
    risk_decomposition: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "risk_mvp",
                "action": "approve",
                "confidence": 0.80,
                "position_size": 5.0,
                "risk_level": "medium",
                "stop_loss": 135.00,
                "stop_loss_pct": 0.02,
                "reasoning": "Position sized at 5% based on Kelly Criterion",
                "warnings": ["High volatility expected"]
            }
        }


class AnalystOpinion(BaseModel):
    """Analyst Agent MVP 응답 스키마"""
    agent: Literal['analyst_mvp'] = 'analyst_mvp'
    action: Literal['buy', 'sell', 'hold', 'pass']
    confidence: float = Field(ge=0.0, le=1.0, description="분석 신뢰도")
    overall_score: float = Field(ge=-10.0, le=10.0, description="종합 정보 점수")
    reasoning: str = Field(min_length=10, description="분석 근거")
    
    # Detailed Context
    news_impact: Optional[Dict[str, Any]] = None
    macro_impact: Optional[Dict[str, Any]] = None
    institutional_flow: Optional[Dict[str, Any]] = None
    chipwar_risk: Optional[Dict[str, Any]] = None
    
    red_flags: List[str] = Field(default_factory=list, description="위험 신호")
    key_catalysts: List[str] = Field(default_factory=list, description="주요 촉매제")
    data_sources: List[str] = Field(default_factory=list, description="데이터 출처")

    # Enhanced Fields (Phase 1)
    valuation_analysis: Optional[Dict[str, Any]] = Field(default=None, description="밸류에이션 분석")
    catalyst_analysis: Optional[Dict[str, Any]] = Field(default=None, description="상세 촉매제 분석")
    evidence_grades: Optional[Dict[str, Any]] = Field(default=None, description="증거 신뢰도 등급")

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "analyst_mvp",
                "action": "buy",
                "confidence": 0.75,
                "overall_score": 7.5,
                "reasoning": "Strong fundamental data supported by positive news flow",
                "key_catalysts": ["Revenue growth 20% YoY", "Expanding margins"],
                "red_flags": [],
                "news_impact": {"sentiment": "positive", "impact_score": 8.0},
                "data_sources": ["10-Q filing", "Analyst reports"]
            }
        }


class PMDecision(BaseModel):
    """PM Agent MVP 최종 결정 스키마"""
    agent: Literal['pm_mvp'] = 'pm_mvp'
    # Updated to include 'hold' for existing_position context
    final_decision: Literal['approve', 'reject', 'reduce_size', 'silence', 'conditional', 'hold']
    confidence: float = Field(ge=0.0, le=1.0, description="최종 결정 신뢰도")
    reasoning: str = Field(min_length=10, description="결정 근거")
    hard_rules_passed: bool = Field(description="Hard Rules 통과 여부")
    recommended_action: str = Field(description="권장 액션")
    approved_params: Optional[Dict[str, Any]] = Field(default=None, description="승인된 파라미터")
    risk_warnings: List[str] = Field(default_factory=list, description="리스크 경고")
    approval_conditions: List[str] = Field(default_factory=list, description="승인 조건")

    # NEW: Portfolio Action Guide fields (Phase 1)
    portfolio_action: Optional[str] = Field(
        default="hold",
        description="Portfolio-level action: sell | buy_more | hold | do_not_buy"
    )
    action_reason: Optional[str] = Field(
        default="",
        description="Reasoning for the portfolio action (Korean)"
    )
    action_strength: Optional[str] = Field(
        default="moderate",
        description="Strength: weak | moderate | strong"
    )
    position_adjustment_pct: Optional[float] = Field(
        default=0.0,
        description="Suggested adjustment (+0.2 = add 20%, -0.5 = sell 50%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "pm_mvp",
                "final_decision": "approve",
                "confidence": 0.82,
                "reasoning": "All agents agree, risk is manageable, no hard rule violations",
                "hard_rules_passed": True,
                "recommended_action": "Buy 100 shares at market",
                "approved_params": {
                    "symbol": "NVDA",
                    "action": "buy",
                    "quantity": 100,
                    "stop_loss": 135.00
                },
                "risk_warnings": []
            }
        }


class WarRoomResult(BaseModel):
    """War Room 전체 결과 스키마"""
    source: str = Field(default='war_room_mvp', description="결과 출처")
    symbol: str = Field(description="종목 심볼")
    execution_mode: Literal['fast_track', 'deep_dive'] = Field(description="실행 모드")
    agent_opinions: Dict[str, Any] = Field(description="각 Agent 의견")
    pm_decision: PMDecision = Field(description="PM 최종 결정")
    # Updated to include 'hold'
    final_decision: Literal['approve', 'reject', 'reduce_size', 'silence', 'conditional', 'hold']
    approved_params: Optional[Dict[str, Any]] = Field(default=None)
    processing_time_ms: int = Field(ge=0, description="처리 시간 (ms)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "source": "war_room_mvp",
                "symbol": "NVDA",
                "execution_mode": "fast_track",
                "agent_opinions": {
                    "trader": {"action": "buy", "confidence": 0.85},
                    "risk": {"action": "approve", "confidence": 0.80},
                    "analyst": {"action": "recommend", "confidence": 0.75}
                },
                "pm_decision": {
                    "final_decision": "approve",
                    "confidence": 0.82
                },
                "final_decision": "approve",
                "processing_time_ms": 5000
            }
        }


# Type helpers for backward compatibility
TraderOpinionDict = Dict[str, Any]
RiskOpinionDict = Dict[str, Any]
AnalystOpinionDict = Dict[str, Any]
PMDecisionDict = Dict[str, Any]
WarRoomResultDict = Dict[str, Any]
