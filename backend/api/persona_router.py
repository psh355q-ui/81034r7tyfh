"""
Persona Router API - Dynamic Investment Mode Switching

Phase: Phase 4 API Integration
Date: 2026-01-05

Endpoints:
    GET  /api/persona/modes          - 사용 가능한 모든 모드 조회
    GET  /api/persona/current        - 현재 모드 조회
    POST /api/persona/switch         - 모드 전환
    GET  /api/persona/config/{mode}  - 특정 모드의 설정 조회
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from backend.ai.router.persona_router import (
    PersonaRouter, 
    PersonaMode, 
    PersonaConfig,
    get_persona_router,
    PERSONA_WEIGHTS,
    PERSONA_FEATURES,
)

router = APIRouter(prefix="/api/persona", tags=["Persona Router"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ModeInfo(BaseModel):
    """모드 정보"""
    mode: str
    description: str
    weights: Dict[str, float]
    features: Dict[str, bool]
    leverage_allowed: bool


class SwitchModeRequest(BaseModel):
    """모드 전환 요청"""
    mode: str = Field(..., description="전환할 모드: dividend | long_term | trading | aggressive")


class SwitchModeResponse(BaseModel):
    """모드 전환 응답"""
    success: bool
    previous_mode: str
    current_mode: str
    weights: Dict[str, float]
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/modes", response_model=List[ModeInfo])
async def get_all_modes():
    """
    사용 가능한 모든 투자 모드 조회
    
    Returns:
        List of all available persona modes with their configurations
    """
    persona_router = get_persona_router()
    modes = []
    
    for mode in PersonaMode:
        config = persona_router.get_config(mode.value)
        modes.append(ModeInfo(
            mode=mode.value,
            description=config.description,
            weights=config.weights,
            features=config.features,
            leverage_allowed=persona_router.is_leverage_allowed(mode.value)
        ))
    
    return modes


@router.get("/current")
async def get_current_mode():
    """
    현재 활성화된 투자 모드 조회
    
    Returns:
        Current mode info with weights and features
    """
    persona_router = get_persona_router()
    current = persona_router.get_current_mode()
    config = persona_router.get_config(current.value)
    
    return {
        "mode": current.value,
        "description": config.description,
        "weights": config.weights,
        "features": config.features,
        "leverage_allowed": persona_router.is_leverage_allowed(current.value),
        "leverage_cap": persona_router.get_leverage_cap(current.value)
    }


@router.post("/switch", response_model=SwitchModeResponse)
async def switch_mode(request: SwitchModeRequest):
    """
    투자 모드 전환
    
    Args:
        mode: 전환할 모드 (dividend, long_term, trading, aggressive)
    
    Returns:
        Switch result with new weights
    """
    persona_router = get_persona_router()
    previous = persona_router.get_current_mode()
    
    try:
        new_mode = persona_router.set_mode(request.mode)
        weights = persona_router.get_weights(new_mode.value)
        
        return SwitchModeResponse(
            success=True,
            previous_mode=previous.value,
            current_mode=new_mode.value,
            weights=weights,
            message=f"모드가 {previous.value} → {new_mode.value}로 전환되었습니다."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")


@router.get("/config/{mode}")
async def get_mode_config(mode: str):
    """
    특정 모드의 상세 설정 조회
    
    Args:
        mode: 조회할 모드 이름
    
    Returns:
        Detailed configuration for the specified mode
    """
    persona_router = get_persona_router()
    
    try:
        config = persona_router.get_config(mode)
        return {
            "mode": config.mode.value,
            "description": config.description,
            "weights": config.weights,
            "features": config.features,
            "leverage_allowed": persona_router.is_leverage_allowed(mode),
            "leverage_cap": persona_router.get_leverage_cap(mode),
            "weight_explanation": {
                "trader_mvp": "기술적 분석 가중치 (모멘텀, 차트)",
                "risk_mvp": "리스크 관리 가중치 (손절, 포지션 사이징)",
                "analyst_mvp": "펀더멘털 분석 가중치 (재무제표, 밸류에이션)"
            }
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Mode not found: {mode}")


@router.get("/leverage-check/{ticker}")
async def check_leverage_product(ticker: str, portfolio_value: float = 100000):
    """
    특정 티커가 레버리지 상품인지 확인 및 제한 조회
    
    Args:
        ticker: 종목 티커
        portfolio_value: 포트폴리오 총 가치 (기본 10만)
    
    Returns:
        Leverage product check result with limits
    """
    from backend.ai.safety.leverage_guardian import get_leverage_guardian
    
    guardian = get_leverage_guardian()
    is_leveraged = guardian.is_leveraged(ticker)
    
    if is_leveraged:
        category = guardian.get_category(ticker)
        max_value = portfolio_value * guardian.rules["max_leverage_pct"]
        
        return {
            "ticker": ticker.upper(),
            "is_leveraged": True,
            "category": category.value,
            "max_allowed_value": max_value,
            "max_allowed_pct": guardian.rules["max_leverage_pct"] * 100,
            "max_holding_days": guardian.rules["max_holding_days"],
            "warning": "레버리지 상품은 장기 보유 시 Volatility Drag로 인해 손실 위험이 높습니다."
        }
    else:
        return {
            "ticker": ticker.upper(),
            "is_leveraged": False,
            "category": "normal",
            "message": "일반 상품입니다. 레버리지 제한이 적용되지 않습니다."
        }
