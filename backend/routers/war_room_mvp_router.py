"""
War Room MVP API Router

Phase: MVP Consolidation
Date: 2025-12-31

API Endpoints:
    - POST /api/war-room-mvp/deliberate - MVP 전쟁실 심의
    - GET /api/war-room-mvp/info - War Room 정보
    - GET /api/war-room-mvp/history - 결정 이력
    - GET /api/war-room-mvp/performance - 성과 측정
    - POST /api/war-room-mvp/shadow/start - Shadow Trading 시작
    - POST /api/war-room-mvp/shadow/execute - Shadow Trade 실행
    - GET /api/war-room-mvp/shadow/status - Shadow Trading 상태
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.mvp.war_room_mvp import WarRoomMVP
from execution.shadow_trading_mvp import ShadowTradingMVP

# Initialize router
router = APIRouter(prefix="/api/war-room-mvp", tags=["War Room MVP"])

# Initialize War Room MVP (singleton)
war_room = WarRoomMVP()

# Initialize Shadow Trading (singleton)
shadow_trading = ShadowTradingMVP(initial_capital=100000.0)


# ============================================================================
# Request/Response Models
# ============================================================================

class DeliberationRequest(BaseModel):
    """심의 요청"""
    symbol: str
    action_context: str  # "new_position", "stop_loss_check", "rebalancing"
    market_data: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    additional_data: Optional[Dict[str, Any]] = None


class ShadowTradeRequest(BaseModel):
    """Shadow Trade 요청"""
    symbol: str
    action: str  # "buy" | "sell"
    quantity: int
    price: float
    stop_loss_pct: Optional[float] = 0.02


# ============================================================================
# War Room MVP Endpoints
# ============================================================================

@router.post("/deliberate")
async def deliberate(request: DeliberationRequest) -> Dict[str, Any]:
    """
    MVP 전쟁실 심의

    3+1 Agent 시스템:
    - Trader Agent MVP (35%)
    - Risk Agent MVP (35%)
    - Analyst Agent MVP (30%)
    - PM Agent MVP (Final Decision)

    Returns:
        - final_decision: approve/reject/reduce_size/silence
        - recommended_action: buy/sell/hold
        - confidence: 최종 confidence
        - agent_opinions: 각 Agent 의견
        - validation_result: Hard Rules 검증 결과
    """
    try:
        result = war_room.deliberate(
            symbol=request.symbol,
            action_context=request.action_context,
            market_data=request.market_data,
            portfolio_state=request.portfolio_state,
            additional_data=request.additional_data
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deliberation failed: {str(e)}")


@router.get("/info")
async def get_info() -> Dict[str, Any]:
    """
    War Room MVP 정보 조회

    Returns:
        - agent_structure: 3+1 구조
        - agents: Agent 정보
        - improvement_vs_legacy: Legacy 대비 개선 사항
    """
    try:
        return war_room.get_war_room_info()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get info: {str(e)}")


@router.get("/history")
async def get_history(limit: int = 20) -> Dict[str, Any]:
    """
    결정 이력 조회

    Args:
        limit: 최대 조회 개수 (default: 20)

    Returns:
        - decisions: 결정 이력
        - total_count: 전체 결정 수
    """
    try:
        history = war_room.decision_history[-limit:]
        return {
            'decisions': history,
            'total_count': len(war_room.decision_history),
            'retrieved_count': len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/performance")
async def get_performance() -> Dict[str, Any]:
    """
    War Room 성과 측정

    Returns:
        - total_decisions: 총 결정 수
        - decision_breakdown: 결정 유형별 분포
        - average_confidence: 평균 confidence
    """
    try:
        decisions = war_room.decision_history

        if not decisions:
            return {
                'total_decisions': 0,
                'decision_breakdown': {},
                'average_confidence': 0.0
            }

        # Count decision types
        decision_counts = {}
        total_confidence = 0.0

        for decision in decisions:
            final_decision = decision.get('final_decision', 'unknown')
            decision_counts[final_decision] = decision_counts.get(final_decision, 0) + 1
            total_confidence += decision.get('confidence', 0.0)

        avg_confidence = total_confidence / len(decisions) if decisions else 0.0

        return {
            'total_decisions': len(decisions),
            'decision_breakdown': decision_counts,
            'average_confidence': avg_confidence,
            'session_id': war_room.session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


# ============================================================================
# Shadow Trading Endpoints
# ============================================================================

@router.post("/shadow/start")
async def start_shadow_trading(reason: str = "MVP validation") -> Dict[str, Any]:
    """
    Shadow Trading 시작

    Args:
        reason: 시작 이유 (default: "MVP validation")

    Returns:
        - success: 시작 성공 여부
        - message: 시작 메시지
        - start_date: 시작 일시
    """
    try:
        result = shadow_trading.start(reason=reason)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start shadow trading: {str(e)}")


@router.post("/shadow/execute")
async def execute_shadow_trade(request: ShadowTradeRequest) -> Dict[str, Any]:
    """
    Shadow Trade 실행

    Args:
        request: Shadow Trade 요청

    Returns:
        - success: 실행 성공 여부
        - message: 실행 메시지
        - trade_id: Trade ID
        - pnl: PnL (sell일 경우)
    """
    try:
        result = shadow_trading.execute_trade(
            symbol=request.symbol,
            action=request.action,
            quantity=request.quantity,
            price=request.price,
            stop_loss_pct=request.stop_loss_pct
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute shadow trade: {str(e)}")


@router.get("/shadow/status")
async def get_shadow_status() -> Dict[str, Any]:
    """
    Shadow Trading 상태 조회

    Returns:
        - status: active/paused/completed/failed
        - performance: 성과 지표
        - success_criteria_check: 성공 기준 체크
        - failure_conditions_check: 실패 조건 체크
    """
    try:
        info = shadow_trading.get_shadow_info()
        performance = shadow_trading.get_performance()
        success_check = shadow_trading.check_success_criteria()
        failure_check = shadow_trading.check_failure_conditions()

        return {
            'info': info,
            'performance': performance,
            'success_criteria_check': success_check,
            'failure_conditions_check': failure_check
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shadow status: {str(e)}")


@router.post("/shadow/update")
async def update_shadow_positions(market_prices: Dict[str, float]) -> Dict[str, Any]:
    """
    Shadow Trading 포지션 업데이트

    Args:
        market_prices: {symbol: current_price}

    Returns:
        - total_equity: 총 자산
        - available_cash: 가용 현금
        - positions_value: 포지션 가치
        - stop_loss_triggered: Stop Loss 발동 내역
    """
    try:
        result = shadow_trading.update_positions(market_prices=market_prices)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update positions: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    War Room MVP 헬스 체크

    Returns:
        - status: healthy/degraded
        - war_room_active: War Room 활성 여부
        - shadow_trading_active: Shadow Trading 활성 여부
    """
    return {
        'status': 'healthy',
        'war_room_active': True,
        'shadow_trading_active': shadow_trading.status.value == 'active',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }


# Export router
__all__ = ['router']
