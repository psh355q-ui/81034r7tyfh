"""
Consensus API Router

Phase E1: Defensive Consensus Engine API

3-AI 투표 시스템을 위한 REST API 엔드포인트

작성일: 2025-12-06
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.schemas.base_schema import MarketContext, SignalAction
from backend.ai.consensus import (
    get_consensus_engine,
    ConsensusResult,
    ConsensusStats,
    VotingRules
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consensus", tags=["Consensus"])


# ============================================================================
# Request/Response Models
# ============================================================================

class VoteOnSignalRequest(BaseModel):
    """투표 요청 모델"""
    market_context: MarketContext = Field(..., description="시장 컨텍스트")
    action: str = Field(..., description="투표 대상 액션 (BUY/SELL/DCA/STOP_LOSS)")
    additional_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 정보 (가격, DCA 횟수 등)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "market_context": {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA",
                    "news": {
                        "headline": "NVIDIA announces Blackwell GPU",
                        "segment": "training",
                        "sentiment": 0.85
                    }
                },
                "action": "BUY",
                "additional_info": {
                    "current_price": 145.50,
                    "target_price": 165.00
                }
            }
        }


class VotingRulesResponse(BaseModel):
    """투표 규칙 응답 모델"""
    rules: Dict[str, str] = Field(..., description="액션별 투표 요구사항")
    explanations: Dict[str, str] = Field(..., description="액션별 규칙 설명")

    class Config:
        json_schema_extra = {
            "example": {
                "rules": {
                    "STOP_LOSS": "1/3",
                    "BUY": "2/3",
                    "DCA": "3/3"
                },
                "explanations": {
                    "STOP_LOSS": "1명 이상 찬성 필요 (방어적 - 빠른 대응)",
                    "BUY": "2명 이상 찬성 필요 (과반수 - 신중한 결정)",
                    "DCA": "3명 전원 찬성 필요 (만장일치 - 매우 신중한 결정)"
                }
            }
        }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/vote", response_model=ConsensusResult)
async def vote_on_signal(request: VoteOnSignalRequest):
    """
    특정 액션에 대해 3-AI 투표 실행

    비대칭 의사결정 로직:
    - STOP_LOSS: 1명 경고 → 즉시 실행
    - BUY: 2명 찬성 → 허용
    - DCA: 3명 전원 동의 → 허용
    """
    try:
        logger.info(f"Consensus vote requested for {request.action} on {request.market_context.ticker}")

        # Consensus Engine 가져오기
        engine = get_consensus_engine()

        # 투표 실행
        result = await engine.vote_on_signal(
            context=request.market_context,
            action=request.action,
            additional_info=request.additional_info
        )

        return result

    except Exception as e:
        logger.error(f"Consensus vote failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consensus vote failed: {str(e)}")


@router.get("/rules", response_model=VotingRulesResponse)
async def get_voting_rules():
    """
    투표 규칙 조회

    액션별 투표 요구사항 및 설명 반환
    """
    try:
        rules = VotingRules.get_all_requirements()

        explanations = {}
        for action in rules.keys():
            explanations[action] = VotingRules.explain_rule(action)

        return VotingRulesResponse(
            rules=rules,
            explanations=explanations
        )

    except Exception as e:
        logger.error(f"Failed to get voting rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voting rules: {str(e)}")


@router.get("/stats", response_model=ConsensusStats)
async def get_consensus_stats():
    """
    Consensus Engine 통계 조회

    총 투표 수, 승인율, AI별 일치율 등
    """
    try:
        engine = get_consensus_engine()
        stats = engine.get_stats()

        return stats

    except Exception as e:
        logger.error(f"Failed to get consensus stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get consensus stats: {str(e)}")


@router.get("/recent-votes")
async def get_recent_votes(limit: int = Query(default=10, ge=1, le=100)):
    """
    최근 투표 결과 조회

    Args:
        limit: 조회할 최근 투표 수 (1~100)
    """
    try:
        engine = get_consensus_engine()
        recent_votes = engine.get_recent_votes(limit=limit)

        # ConsensusResult를 딕셔너리로 변환
        results = []
        for vote in recent_votes:
            results.append({
                "ticker": vote.ticker,
                "action": vote.action,
                "approved": vote.approved,
                "approve_count": vote.approve_count,
                "consensus_strength": vote.consensus_strength.value,
                "timestamp": vote.timestamp.isoformat(),
                "vote_requirement": vote.vote_requirement
            })

        return {
            "count": len(results),
            "votes": results
        }

    except Exception as e:
        logger.error(f"Failed to get recent votes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent votes: {str(e)}")


@router.post("/test-vote")
async def test_consensus_vote(
    action: str = Query(..., description="투표 대상 액션"),
    ticker: str = Query(default="NVDA", description="테스트 종목")
):
    """
    테스트용 간단한 투표 실행

    Mock 데이터로 빠르게 Consensus 동작 확인
    """
    try:
        # 간단한 MarketContext 생성
        from backend.schemas.base_schema import NewsFeatures, MarketSegment

        context = MarketContext(
            ticker=ticker,
            company_name=ticker,
            news=NewsFeatures(
                headline=f"Test news for {ticker}",
                segment=MarketSegment.TRAINING,
                sentiment=0.7
            )
        )

        # Consensus Engine 투표
        engine = get_consensus_engine()
        result = await engine.vote_on_signal(context, action)

        return {
            "action": action,
            "ticker": ticker,
            "approved": result.approved,
            "approve_count": result.approve_count,
            "requirement": result.vote_requirement,
            "consensus_strength": result.consensus_strength.value,
            "votes": {
                ai_name: {
                    "decision": vote.decision.value,
                    "confidence": vote.confidence
                }
                for ai_name, vote in result.votes.items()
            }
        }

    except Exception as e:
        logger.error(f"Test vote failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test vote failed: {str(e)}")


# ============================================================================
# DCA Endpoints
# ============================================================================

class DCAEvaluationRequest(BaseModel):
    """DCA 평가 요청 모델"""
    ticker: str = Field(..., description="종목 티커")
    current_price: float = Field(..., gt=0, description="현재 가격")
    avg_entry_price: float = Field(..., gt=0, description="평균 매수가")
    dca_count: int = Field(..., ge=0, le=3, description="현재 DCA 횟수 (0~3)")
    total_invested: float = Field(..., gt=0, description="총 투자액")
    market_context: MarketContext = Field(..., description="시장 컨텍스트")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "current_price": 130.0,
                "avg_entry_price": 150.0,
                "dca_count": 0,
                "total_invested": 10000.0,
                "market_context": {
                    "ticker": "NVDA",
                    "news": {
                        "headline": "NVIDIA maintains strong fundamentals",
                        "segment": "training",
                        "sentiment": 0.3
                    }
                }
            }
        }


@router.post("/dca/evaluate")
async def evaluate_dca(request: DCAEvaluationRequest):
    """
    DCA 실행 종합 평가

    1. DCA 전략으로 기본 조건 확인
    2. 조건 충족 시 3-AI Consensus 투표
    3. 3명 전원 동의 필요 (3/3)

    Returns:
        - dca_recommended: DCA 전략 추천 여부
        - consensus_approved: Consensus 승인 여부
        - final_decision: 최종 결정 (APPROVED/REJECTED)
        - dca_decision: DCA 전략 판단 상세
        - consensus_result: Consensus 투표 결과
    """
    try:
        logger.info(f"DCA evaluation requested for {request.ticker}")

        # Consensus Engine의 evaluate_dca 호출
        engine = get_consensus_engine()
        result = await engine.evaluate_dca(
            ticker=request.ticker,
            current_price=request.current_price,
            avg_entry_price=request.avg_entry_price,
            dca_count=request.dca_count,
            total_invested=request.total_invested,
            context=request.market_context
        )

        # DCADecision을 dict로 변환
        if result.get("dca_decision"):
            from dataclasses import asdict
            result["dca_decision"] = asdict(result["dca_decision"])

        # ConsensusResult를 dict로 변환 (있는 경우)
        if result.get("consensus_result"):
            consensus = result["consensus_result"]
            result["consensus_result"] = {
                "approved": consensus.approved,
                "approve_count": consensus.approve_count,
                "consensus_strength": consensus.consensus_strength.value,
                "votes": {
                    ai_name: {
                        "decision": vote.decision.value,
                        "confidence": vote.confidence,
                        "reasoning": vote.reasoning
                    }
                    for ai_name, vote in consensus.votes.items()
                }
            }

        return result

    except Exception as e:
        logger.error(f"DCA evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DCA evaluation failed: {str(e)}")


@router.post("/dca/test")
async def test_dca_evaluation(
    ticker: str = Query(default="NVDA", description="테스트 종목"),
    current_price: float = Query(default=130.0, gt=0, description="현재 가격"),
    avg_entry_price: float = Query(default=150.0, gt=0, description="평균 매수가")
):
    """
    테스트용 간단한 DCA 평가

    Mock 데이터로 빠르게 DCA + Consensus 동작 확인
    """
    try:
        from backend.schemas.base_schema import NewsFeatures, MarketSegment, MarketRegime

        # 간단한 MarketContext 생성
        context = MarketContext(
            ticker=ticker,
            company_name=ticker,
            news=NewsFeatures(
                headline=f"{ticker} maintains strong fundamentals",
                segment=MarketSegment.TRAINING,
                sentiment=0.3
            ),
            market_regime=MarketRegime.SIDEWAYS
        )

        # DCA 평가
        engine = get_consensus_engine()
        result = await engine.evaluate_dca(
            ticker=ticker,
            current_price=current_price,
            avg_entry_price=avg_entry_price,
            dca_count=0,
            total_invested=10000.0,
            context=context
        )

        # DCADecision을 dict로 변환
        if result.get("dca_decision"):
            from dataclasses import asdict
            result["dca_decision"] = asdict(result["dca_decision"])

        # 간소화된 응답
        response = {
            "ticker": ticker,
            "price_info": {
                "current": current_price,
                "avg_entry": avg_entry_price,
                "drop_pct": ((current_price - avg_entry_price) / avg_entry_price) * 100
            },
            "dca_recommended": result["dca_recommended"],
            "consensus_approved": result["consensus_approved"],
            "final_decision": result["final_decision"]
        }

        if result.get("dca_decision"):
            response["dca_reasoning"] = result["dca_decision"]["reasoning"]

        if result.get("approval_details"):
            response["approval_details"] = result["approval_details"]

        return response

    except Exception as e:
        logger.error(f"Test DCA evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test DCA failed: {str(e)}")
