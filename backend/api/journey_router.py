"""
Investment Journey Memory API - User Decision Tracking & Coaching

Phase: Phase 4 API Integration
Date: 2026-01-05

Endpoints:
    POST /api/journey/record         - 투자 결정 기록
    GET  /api/journey/history        - 결정 이력 조회
    GET  /api/journey/coaching       - 현재 상황 코칭 받기
    GET  /api/journey/quality-score  - 의사결정 품질 점수
    POST /api/journey/update-outcome - 결정 결과 업데이트
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.ai.memory.investment_journey_memory import (
    InvestmentJourneyMemory,
    DecisionType,
    MarketCondition,
    get_journey_memory,
)

router = APIRouter(prefix="/api/journey", tags=["Investment Journey"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RecordDecisionRequest(BaseModel):
    """결정 기록 요청"""
    user_id: str = Field(default="default_user", description="사용자 ID")
    ticker: str = Field(..., description="종목 티커")
    decision_type: str = Field(..., description="결정 유형: buy | sell | hold | panic_sell | fomo_buy | stop_loss | take_profit")
    market_condition: str = Field(..., description="시장 상황: fear | greed | neutral | high_vol | trending_up | trending_down")
    entry_price: float = Field(..., description="진입/청산 가격")
    quantity: int = Field(..., description="수량")
    reasoning: str = Field(..., description="결정 근거")
    ai_recommendation: Optional[str] = Field(default=None, description="AI가 추천한 행동")
    followed_ai: bool = Field(default=False, description="AI 추천 따랐는지")


class UpdateOutcomeRequest(BaseModel):
    """결과 업데이트 요청"""
    user_id: str = Field(default="default_user", description="사용자 ID")
    decision_id: str = Field(..., description="결정 ID")
    current_price: float = Field(..., description="현재가")
    days_since: int = Field(..., description="경과 일수")


class CoachingRequest(BaseModel):
    """코칭 요청"""
    user_id: str = Field(default="default_user", description="사용자 ID")
    ticker: str = Field(..., description="현재 고려 중인 티커")
    current_market_condition: str = Field(..., description="현재 시장 상황")
    current_action: Optional[str] = Field(default=None, description="고려 중인 행동")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/record")
async def record_decision(request: RecordDecisionRequest):
    """
    투자 결정 기록
    
    사용자의 투자 결정을 기록하여 나중에 분석 및 코칭에 활용합니다.
    
    Returns:
        생성된 결정 기록
    """
    memory = get_journey_memory(request.user_id)
    
    try:
        decision = memory.record_decision(
            ticker=request.ticker,
            decision_type=request.decision_type,
            market_condition=request.market_condition,
            entry_price=request.entry_price,
            quantity=request.quantity,
            reasoning=request.reasoning,
            ai_recommendation=request.ai_recommendation,
            followed_ai=request.followed_ai
        )
        
        return {
            "success": True,
            "decision_id": decision.decision_id,
            "message": f"{request.ticker} {request.decision_type} 결정이 기록되었습니다.",
            "decision": decision.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    user_id: str = Query(default="default_user", description="사용자 ID"),
    limit: int = Query(default=20, description="조회 개수")
):
    """
    결정 이력 조회
    
    Returns:
        최근 투자 결정 이력
    """
    memory = get_journey_memory(user_id)
    decisions = memory.get_decisions(limit=limit)
    stats = memory.get_statistics()
    
    return {
        "user_id": user_id,
        "decisions": decisions,
        "statistics": stats
    }


@router.post("/coaching")
async def get_coaching(request: CoachingRequest):
    """
    현재 상황에 대한 코칭 조언 받기
    
    과거 유사 상황에서의 결정과 결과를 기반으로 조언합니다.
    
    Returns:
        Coaching advice based on historical patterns
    """
    memory = get_journey_memory(request.user_id)
    
    coaching = memory.get_coaching(
        ticker=request.ticker,
        current_market_condition=request.current_market_condition,
        current_action=request.current_action
    )
    
    return {
        "message": coaching.message,
        "based_on_decisions": coaching.based_on_decisions,
        "confidence": coaching.confidence,
        "historical_success_rate": coaching.historical_success_rate
    }


@router.get("/quality-score")
async def get_quality_score(
    user_id: str = Query(default="default_user", description="사용자 ID")
):
    """
    의사결정 품질 점수 조회
    
    수익률이 아닌 '프로세스'의 품질을 평가합니다.
    
    Returns:
        Decision quality scores and insights
    """
    memory = get_journey_memory(user_id)
    score = memory.get_quality_score()
    
    return {
        "user_id": user_id,
        "scores": {
            "fear_response": score.fear_response_score,
            "greed_response": score.greed_response_score,
            "consistency": score.consistency_score,
            "discipline": score.discipline_score,
            "overall": score.overall_score
        },
        "insights": score.insights,
        "interpretation": {
            "fear_response": "공포 구간(VIX 30+, 급락)에서의 대응 품질",
            "greed_response": "탐욕 구간(급등, 과열)에서의 대응 품질",
            "consistency": "동일 상황에서의 일관된 의사결정",
            "discipline": "AI 추천 또는 규칙 준수율"
        }
    }


@router.post("/update-outcome")
async def update_outcome(request: UpdateOutcomeRequest):
    """
    결정 결과 업데이트 (30일/90일 후)
    
    과거 결정의 결과를 업데이트하여 코칭 정확도를 높입니다.
    
    Returns:
        Updated decision with outcome
    """
    memory = get_journey_memory(request.user_id)
    
    decision = memory.update_outcome(
        decision_id=request.decision_id,
        current_price=request.current_price,
        days_since=request.days_since
    )
    
    if decision:
        return {
            "success": True,
            "decision_id": request.decision_id,
            "outcome_30d": decision.outcome_30d,
            "outcome_90d": decision.outcome_90d,
            "message": f"{request.days_since}일 후 결과가 업데이트되었습니다."
        }
    else:
        raise HTTPException(status_code=404, detail=f"Decision not found: {request.decision_id}")


@router.get("/decision-types")
async def get_decision_types():
    """
    사용 가능한 결정 유형 및 시장 상황 조회
    
    Returns:
        All available decision types and market conditions
    """
    return {
        "decision_types": [
            {"value": t.value, "name": t.name}
            for t in DecisionType
        ],
        "market_conditions": [
            {"value": c.value, "name": c.name}
            for c in MarketCondition
        ]
    }
