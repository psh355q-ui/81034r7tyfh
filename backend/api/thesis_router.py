"""
Thesis Violation API - Investment Thesis Health Check

Phase: Phase 4 API Integration
Date: 2026-01-05

Endpoints:
    POST /api/thesis/check           - 투자 아이디어 위반 검사
    GET  /api/thesis/violation-types - 위반 유형 목록 조회
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.ai.analysis.thesis_violation_detector import (
    ThesisViolationDetector,
    ThesisType,
    ViolationType,
    ViolationSeverity,
    get_thesis_detector,
)

router = APIRouter(prefix="/api/thesis", tags=["Thesis Violation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ThesisCheckRequest(BaseModel):
    """투자 아이디어 검사 요청"""
    ticker: str = Field(..., description="종목 티커")
    thesis_type: str = Field(..., description="투자 아이디어 유형: moat | growth | dividend | value | turnaround")
    fundamental_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="재무 데이터 (market_share_history, operating_margin_history, etc.)"
    )
    news_events: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="관련 뉴스 이벤트"
    )


class ViolationDetail(BaseModel):
    """위반 상세"""
    type: str
    severity: str
    message: str
    data: Dict[str, Any]


class ThesisCheckResponse(BaseModel):
    """투자 아이디어 검사 응답"""
    ticker: str
    thesis_type: str
    thesis_intact: bool
    violations: List[ViolationDetail]
    recommendation: str
    confidence: float
    checked_at: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/check", response_model=ThesisCheckResponse)
async def check_thesis(request: ThesisCheckRequest):
    """
    투자 아이디어 위반 검사
    
    투자의 근본적인 이유(Thesis)가 여전히 유효한지 확인합니다.
    가격 하락이 아닌, 실제 사업/재무 악화를 감지합니다.
    
    Args:
        ticker: 종목 티커
        thesis_type: 투자 아이디어 유형
        fundamental_data: 재무 데이터
    
    Returns:
        Thesis health check result with violations and recommendation
    """
    detector = get_thesis_detector()
    
    try:
        result = detector.check_thesis(
            ticker=request.ticker,
            thesis_type=request.thesis_type,
            fundamental_data=request.fundamental_data,
            news_events=request.news_events
        )
        
        return ThesisCheckResponse(
            ticker=result.ticker,
            thesis_type=result.thesis_type.value,
            thesis_intact=result.thesis_intact,
            violations=[
                ViolationDetail(
                    type=v.violation_type.value,
                    severity=v.severity.value,
                    message=v.message,
                    data=v.data
                )
                for v in result.violations
            ],
            recommendation=result.recommendation,
            confidence=result.confidence,
            checked_at=result.checked_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/violation-types")
async def get_violation_types():
    """
    위반 유형 목록 조회
    
    Returns:
        All available violation types with descriptions
    """
    return {
        "thesis_types": [
            {"value": t.value, "name": t.name} 
            for t in ThesisType
        ],
        "violation_types": [
            {
                "value": v.value, 
                "name": v.name,
                "description": _get_violation_description(v)
            }
            for v in ViolationType
        ],
        "severity_levels": [
            {"value": s.value, "name": s.name}
            for s in ViolationSeverity
        ]
    }


@router.get("/thresholds")
async def get_thresholds():
    """
    현재 적용 중인 위반 감지 임계값 조회
    
    Returns:
        Current threshold settings
    """
    detector = get_thesis_detector()
    return {
        "thresholds": detector.thresholds,
        "description": {
            "market_share_decline_pct": "시장 점유율 하락 임계치 (%)",
            "margin_decline_quarters": "연속 마진 하락 분기 수",
            "margin_decline_threshold": "마진 하락폭 임계치 (%p)",
            "insider_selling_pct": "내부자 매도 비율 임계치 (%)",
            "dividend_cut_pct": "배당 삭감 임계치 (%)",
            "debt_ratio_increase_pct": "부채비율 상승 임계치 (%)",
        }
    }


def _get_violation_description(violation_type: ViolationType) -> str:
    """위반 유형 설명"""
    descriptions = {
        ViolationType.MARKET_SHARE_DECLINE: "시장 점유율 하락 - 경쟁 우위 약화",
        ViolationType.MARGIN_DETERIORATION: "영업이익률 악화 - 사업 모델 훼손",
        ViolationType.INSIDER_SELLING: "내부자 매도 - 경영진 신뢰 이슈",
        ViolationType.DIVIDEND_CUT: "배당 삭감/중단 - 현금흐름 악화",
        ViolationType.DEBT_SURGE: "부채 급증 - 재무 건전성 악화",
        ViolationType.MANAGEMENT_CHANGE: "경영진 변동 - 전략 불확실성",
        ViolationType.COMPETITIVE_THREAT: "경쟁 위협 - 시장 지위 위험",
        ViolationType.REGULATORY_RISK: "규제 리스크 - 사업 환경 변화",
    }
    return descriptions.get(violation_type, "Unknown")
