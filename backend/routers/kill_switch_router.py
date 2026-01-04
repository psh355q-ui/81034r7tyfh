"""
Kill Switch API Router

Kill Switch 상태 조회 및 제어 API 엔드포인트

Endpoints:
- GET /api/kill-switch/status - 상태 조회
- POST /api/kill-switch/activate - 수동 활성화
- POST /api/kill-switch/deactivate - 해제 (수동 승인 필요)
- POST /api/kill-switch/check - 트리거 조건 체크
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from backend.execution.kill_switch import get_kill_switch, TriggerType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kill-switch", tags=["kill-switch"])


class ActivateRequest(BaseModel):
    reason: str
    details: Optional[Dict] = {}


class DeactivateRequest(BaseModel):
    manual_override_code: str  # 보안: 수동 승인 코드
    reason: str


class CheckRequest(BaseModel):
    trading_state: Dict  # current_capital, initial_capital, open_positions, etc.


@router.get("/status")
async def get_status():
    """
    Kill Switch 현재 상태 조회
    
    Returns:
        {
            "status": "active" | "triggered" | "paused" | "disabled",
            "can_trade": bool,
            "triggered_at": str | null,
            "trigger_reason": str | null,
            "config": {...}
        }
    """
    kill_switch = get_kill_switch()
    return kill_switch.get_status()


@router.post("/activate")
async def activate_kill_switch(request: ActivateRequest):
    """
    Kill Switch 수동 활성화 (긴급 정지)
    
    Args:
        reason: 활성화 사유
        details: 추가 상세 정보
    
    Returns:
        {"success": true, "message": "...", "status": {...}}
    """
    kill_switch = get_kill_switch()
    
    # 수동 트리거 발동
    kill_switch.trigger(
        reason=TriggerType.MANUAL,
        details={
            "manual_reason": request.reason,
            **request.details
        }
    )
    
    logger.warning(f"🚨 Kill Switch manually activated: {request.reason}")
    
    return {
        "success": True,
        "message": f"Kill Switch activated: {request.reason}",
        "status": kill_switch.get_status()
    }


@router.post("/deactivate")
async def deactivate_kill_switch(request: DeactivateRequest):
    """
    Kill Switch 해제 (수동 승인 필요)
    
    Args:
        manual_override_code: 수동 승인 코드  (예: "OVERRIDE_2026")
        reason: 해제 사유
    
    Returns:
        {"success": bool, "message": str}
    """
    kill_switch = get_kill_switch()
    
    # 보안: 승인 코드 검증
    # TODO: 환경 변수에서 승인 코드 로드
    VALID_OVERRIDE_CODE = "OVERRIDE_2026"  # 임시
    
    if request.manual_override_code != VALID_OVERRIDE_CODE:
        logger.error("❌ Invalid manual override code")
        raise HTTPException(status_code=403, detail="Invalid manual override code")
    
    # Kill Switch 해제
    success = kill_switch.reset(manual_override=True)
    
    if not success:
        raise HTTPException(status_code=400, detail="Cannot deactivate: Kill Switch not triggered")
    
    logger.warning(f"🔓 Kill Switch manually deactivated: {request.reason}")
    
    return {
        "success": True,
        "message": f"Kill Switch deactivated: {request.reason}",
        "status": kill_switch.get_status()
    }


@router.post("/check")
async def check_triggers(request: CheckRequest):
    """
    Kill Switch 트리거 조건 체크
    
    Args:
        trading_state: 현재 거래 상태
            {
                "current_capital": float,
                "initial_capital": float,
                "open_positions": [...],
                "daily_pnl": float,
                "daily_trades": int
            }
    
    Returns:
        {
            "should_trigger": bool,
            "triggers": [str, ...],
            "details": {...}
        }
    """
    kill_switch = get_kill_switch()
    
    result = kill_switch.check_triggers(request.trading_state)
    
    # 트리거 발동 필요시 자동 활성화
    if result["should_trigger"] and kill_switch.can_trade():
        first_trigger = result["triggers"][0]
        kill_switch.trigger(
            reason=first_trigger,
            details=result["details"]
        )
        
        logger.critical(f"🚨 AUTO-TRIGGERED: {first_trigger.value}")
    
    return {
        "should_trigger": result["should_trigger"],
        "triggers": [t.value for t in result["triggers"]],
        "details": result["details"],
        "current_status": kill_switch.get_status()
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    kill_switch = get_kill_switch()
    return {
        "healthy": True,
        "can_trade": kill_switch.can_trade(),
        "status": kill_switch.status.value
    }
