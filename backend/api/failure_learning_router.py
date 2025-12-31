"""
Failure Learning API Router

Phase 29 확장: 자동 학습 API
Date: 2025-12-30

Endpoints:
- POST /api/learning/run - 학습 사이클 수동 실행
- GET /api/learning/nia - NIA 점수 조회
- GET /api/learning/history - 가중치 조정 히스토리
- GET /api/learning/recommendations - 가중치 조정 제안
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from backend.database.repository import SessionLocal
from backend.database.models import AgentWeightsHistory
from backend.schedulers.failure_learning_scheduler import FailureLearningScheduler
from backend.ai.agents.failure_learning_agent import FailureLearningAgent

router = APIRouter(prefix="/api/learning", tags=["Failure Learning"])


# ============================================================================
# Helper Functions
# ============================================================================

def decimal_to_float(value):
    """Convert Decimal to float for JSON serialization"""
    if value is None:
        return None
    return float(value)


# ============================================================================
# POST /api/learning/run - Run Learning Cycle
# ============================================================================

@router.post("/run")
async def run_learning_cycle():
    """
    학습 사이클 수동 실행

    매일 자동으로 실행되지만, 수동으로도 트리거 가능

    **Returns**:
    - timestamp: 실행 시각
    - success: 성공 여부
    - nia_score: NIA 점수 (0.0 ~ 1.0)
    - weight_adjusted: 가중치 조정 여부
    - failure_analysis: 실패 분석 결과
    """
    try:
        scheduler = FailureLearningScheduler()
        results = scheduler.run_daily_learning_cycle()

        return {
            "timestamp": results["timestamp"],
            "success": results["success"],
            "nia_score": results.get("nia_score"),
            "weight_adjusted": results.get("weight_adjusted", False),
            "failure_analysis": results.get("failure_analysis"),
            "message": "Learning cycle completed successfully" if results["success"] else "Learning cycle failed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run learning cycle: {str(e)}")


# ============================================================================
# GET /api/learning/nia - Get NIA Score
# ============================================================================

@router.get("/nia")
async def get_nia_score(
    lookback_days: int = Query(30, ge=1, le=365, description="조회 기간 (일)")
):
    """
    NIA (News Interpretation Accuracy) 점수 조회

    **Query Parameters**:
    - lookback_days: 조회 기간 (1-365일, 기본 30일)

    **Returns**:
    - nia_score: NIA 점수 (0.0 ~ 1.0)
    - total_predictions: 전체 예측 수
    - period_start: 조회 시작일
    - period_end: 조회 종료일
    """
    try:
        scheduler = FailureLearningScheduler()
        nia_score = scheduler.calculate_nia_score(lookback_days=lookback_days)

        if nia_score is None:
            return {
                "nia_score": None,
                "total_predictions": 0,
                "period_start": (datetime.now() - timedelta(days=lookback_days)).isoformat(),
                "period_end": datetime.now().isoformat(),
                "message": "No verified predictions found"
            }

        # Get prediction count
        session = SessionLocal()
        try:
            from backend.database.models import NewsMarketReaction
            from sqlalchemy import and_

            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            count = session.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.accuracy_1d.isnot(None),
                    NewsMarketReaction.verified_at_1d >= cutoff_date
                )
            ).count()

        finally:
            session.close()

        return {
            "nia_score": nia_score,
            "total_predictions": count,
            "period_start": (datetime.now() - timedelta(days=lookback_days)).isoformat(),
            "period_end": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NIA score: {str(e)}")


# ============================================================================
# GET /api/learning/history - Get Weight Adjustment History
# ============================================================================

@router.get("/history")
async def get_weight_history(
    limit: int = Query(50, ge=1, le=500, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="오프셋")
):
    """
    가중치 조정 히스토리 조회

    **Query Parameters**:
    - limit: 최대 결과 수 (1-500, 기본 50)
    - offset: 오프셋 (페이지네이션)

    **Returns**:
    - total: 전체 히스토리 수
    - count: 반환된 결과 수
    - history: 가중치 조정 히스토리 리스트
    """
    session = SessionLocal()

    try:
        # Get total count
        total_count = session.query(AgentWeightsHistory).count()

        # Get history with pagination
        history_records = session.query(AgentWeightsHistory).order_by(
            AgentWeightsHistory.changed_at.desc()
        ).offset(offset).limit(limit).all()

        # Format response
        history = []
        for record in history_records:
            history.append({
                "id": record.id,
                "changed_at": record.changed_at.isoformat() if record.changed_at else None,
                "changed_by": record.changed_by,
                "reason": record.reason,
                "weights": {
                    "trader_agent": decimal_to_float(record.trader_agent),
                    "risk_agent": decimal_to_float(record.risk_agent),
                    "analyst_agent": decimal_to_float(record.analyst_agent),
                    "macro_agent": decimal_to_float(record.macro_agent),
                    "institutional_agent": decimal_to_float(record.institutional_agent),
                    "news_agent": decimal_to_float(record.news_agent),
                    "chip_war_agent": decimal_to_float(record.chip_war_agent),
                    "dividend_risk_agent": decimal_to_float(record.dividend_risk_agent),
                    "pm_agent": decimal_to_float(record.pm_agent)
                }
            })

        return {
            "total": total_count,
            "count": len(history),
            "offset": offset,
            "limit": limit,
            "history": history
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weight history: {str(e)}")

    finally:
        session.close()


# ============================================================================
# GET /api/learning/recommendations - Get Weight Recommendations
# ============================================================================

@router.get("/recommendations")
async def get_weight_recommendations():
    """
    가중치 조정 제안 조회

    실패율 기반으로 War Room 가중치 조정 제안 생성

    **Returns**:
    - recommendations: 에이전트별 조정 제안
    - timestamp: 생성 시각
    """
    try:
        agent = FailureLearningAgent()
        recommendations = agent.generate_weight_adjustment_recommendation()

        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# ============================================================================
# GET /api/learning/current-weights - Get Current Weights
# ============================================================================

@router.get("/current-weights")
async def get_current_weights():
    """
    현재 War Room 가중치 조회

    **Returns**:
    - weights: 현재 에이전트 가중치
    - last_updated: 마지막 업데이트 시각
    - updated_by: 업데이트 주체
    """
    session = SessionLocal()

    try:
        # Get latest weights
        latest = session.query(AgentWeightsHistory).order_by(
            AgentWeightsHistory.changed_at.desc()
        ).first()

        if not latest:
            # Return default weights
            return {
                "weights": {
                    "trader_agent": 0.15,
                    "risk_agent": 0.15,
                    "analyst_agent": 0.12,
                    "macro_agent": 0.14,
                    "institutional_agent": 0.14,
                    "news_agent": 0.14,
                    "chip_war_agent": 0.14,
                    "dividend_risk_agent": 0.02,
                    "pm_agent": 0.00
                },
                "last_updated": None,
                "updated_by": "system_default",
                "reason": "No adjustment history"
            }

        return {
            "weights": {
                "trader_agent": decimal_to_float(latest.trader_agent),
                "risk_agent": decimal_to_float(latest.risk_agent),
                "analyst_agent": decimal_to_float(latest.analyst_agent),
                "macro_agent": decimal_to_float(latest.macro_agent),
                "institutional_agent": decimal_to_float(latest.institutional_agent),
                "news_agent": decimal_to_float(latest.news_agent),
                "chip_war_agent": decimal_to_float(latest.chip_war_agent),
                "dividend_risk_agent": decimal_to_float(latest.dividend_risk_agent),
                "pm_agent": decimal_to_float(latest.pm_agent)
            },
            "last_updated": latest.changed_at.isoformat() if latest.changed_at else None,
            "updated_by": latest.changed_by,
            "reason": latest.reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current weights: {str(e)}")

    finally:
        session.close()
