"""
Persona Router API - Dynamic Investment Mode Switching

Phase: Phase 4 API Integration
Date: 2026-01-05
Updated: 2026-01-25 (Phase 3: Persona-based Trading)

Endpoints:
    GET  /api/persona/modes          - 사용 가능한 모든 모드 조회
    GET  /api/persona/current        - 현재 모드 조회
    POST /api/persona/switch         - 모드 전환
    GET  /api/persona/config/{mode}  - 특정 모드의 설정 조회
    
    Phase 3 CRUD Endpoints:
    GET  /api/persona/personas       - 모든 페르소나 조회
    GET  /api/persona/personas/{id}  - 특정 페르소나 조회
    POST /api/persona/personas       - 페르소나 생성
    PUT  /api/persona/personas/{id}  - 페르소나 수정
    DELETE /api/persona/personas/{id} - 페르소나 삭제
    GET  /api/persona/user/{user_id} - 사용자 페르소나 조회
    POST /api/persona/user/{user_id}/switch - 사용자 페르소나 전환
    POST /api/persona/allocation     - 포트폴리오 배분 계산
    POST /api/persona/position-size - 포지션 사이즈 계산
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.ai.router.persona_router import (
    PersonaRouter,
    PersonaMode,
    PersonaConfig,
    get_persona_router,
    PERSONA_WEIGHTS,
    PERSONA_FEATURES,
)
from backend.services.persona_trading_service import (
    PersonaTradingService,
    get_persona_trading_service,
)
from backend.database.models import Persona

router = APIRouter(prefix="/api/persona", tags=["Persona Router"])


# ============================================================================
# Database Dependency
# ============================================================================

def get_db():
    """Database session dependency"""
    from backend.database.db_service import get_db
    return get_db()


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


# ============================================================================
# Phase 3: Persona CRUD Endpoints
# ============================================================================

# Request/Response Models for CRUD

class PersonaResponse(BaseModel):
    """페르소나 응답 모델"""
    id: int
    name: str
    display_name: str
    description: str
    risk_tolerance: str
    investment_horizon: str
    return_expectation: str
    trader_weight: float
    risk_weight: float
    analyst_weight: float
    stock_allocation: float
    bond_allocation: float
    cash_allocation: float
    max_position_size: float
    max_sector_exposure: float
    stop_loss_pct: float
    leverage_allowed: bool
    max_leverage_pct: float
    yield_trap_detector: bool
    dividend_calendar: bool
    noise_filter: bool
    thesis_violation: bool
    max_agent_disagreement: float
    min_avg_confidence: float
    is_active: bool
    is_default: bool
    
    class Config:
        from_attributes = True


class PersonaCreateRequest(BaseModel):
    """페르소나 생성 요청 모델"""
    name: str = Field(..., description="페르소나 이름 (CONSERVATIVE, AGGRESSIVE, GROWTH, BALANCED)")
    display_name: str = Field(..., description="표시 이름 (보수형, 공격형, 성장형, 밸런스형)")
    description: str = Field(..., description="페르소나 설명")
    risk_tolerance: str = Field(..., description="리스크 허용도 (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)")
    investment_horizon: str = Field(..., description="투자 기간 (SHORT, MEDIUM, LONG)")
    return_expectation: str = Field(..., description="수익 기대 (LOW, MODERATE, HIGH, VERY_HIGH)")
    trader_weight: float = Field(..., ge=0.0, le=1.0, description="기술적 분석 가중치")
    risk_weight: float = Field(..., ge=0.0, le=1.0, description="리스크 관리 가중치")
    analyst_weight: float = Field(..., ge=0.0, le=1.0, description="펀더멘털 분석 가중치")
    stock_allocation: float = Field(..., ge=0.0, le=1.0, description="주식 배분 비율")
    bond_allocation: float = Field(..., ge=0.0, le=1.0, description="채권 배분 비율")
    cash_allocation: float = Field(..., ge=0.0, le=1.0, description="현금 배분 비율")
    max_position_size: float = Field(default=0.10, ge=0.0, le=1.0, description="최대 포지션 비중")
    max_sector_exposure: float = Field(default=0.30, ge=0.0, le=1.0, description="최대 섹터 노출")
    stop_loss_pct: float = Field(default=0.05, ge=0.0, le=1.0, description="손절가 비율")
    leverage_allowed: bool = Field(default=False, description="레버리지 허용 여부")
    max_leverage_pct: float = Field(default=0.0, ge=0.0, le=1.0, description="최대 레버리지 비중")
    yield_trap_detector: bool = Field(default=False, description="Yield Trap 감지기 활성화")
    dividend_calendar: bool = Field(default=False, description="배당 캘린더 활성화")
    noise_filter: bool = Field(default=False, description="노이즈 필터 활성화")
    thesis_violation: bool = Field(default=False, description="투자 아이디어 훼손 감지 활성화")
    max_agent_disagreement: float = Field(default=0.67, ge=0.0, le=1.0, description="최대 에이전트 불일치")
    min_avg_confidence: float = Field(default=0.50, ge=0.0, le=1.0, description="최소 평균 확신도")
    is_active: bool = Field(default=True, description="활성화 여부")
    is_default: bool = Field(default=False, description="기본 페르소나 여부")


class PersonaUpdateRequest(BaseModel):
    """페르소나 수정 요청 모델"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    risk_tolerance: Optional[str] = None
    investment_horizon: Optional[str] = None
    return_expectation: Optional[str] = None
    trader_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    analyst_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    stock_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    bond_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    cash_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_position_size: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_sector_exposure: Optional[float] = Field(None, ge=0.0, le=1.0)
    stop_loss_pct: Optional[float] = Field(None, ge=0.0, le=1.0)
    leverage_allowed: Optional[bool] = None
    max_leverage_pct: Optional[float] = Field(None, ge=0.0, le=1.0)
    yield_trap_detector: Optional[bool] = None
    dividend_calendar: Optional[bool] = None
    noise_filter: Optional[bool] = None
    thesis_violation: Optional[bool] = None
    max_agent_disagreement: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_avg_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PortfolioAllocationRequest(BaseModel):
    """포트폴리오 배분 계산 요청"""
    persona_id: int = Field(..., description="페르소나 ID")
    total_value: float = Field(..., gt=0, description="총 포트폴리오 가치")
    current_allocations: Optional[Dict[str, float]] = Field(None, description="현재 자산별 배분")


class PositionSizeRequest(BaseModel):
    """포지션 사이즈 계산 요청"""
    persona_id: int = Field(..., description="페르소나 ID")
    total_value: float = Field(..., gt=0, description="총 포트폴리오 가치")
    confidence: float = Field(..., ge=0.0, le=1.0, description="시그널 확신도")
    risk_level: str = Field(default="MEDIUM", description="리스크 레벨 (LOW, MEDIUM, HIGH)")


class SwitchUserPersonaRequest(BaseModel):
    """사용자 페르소나 전환 요청"""
    persona_name: str = Field(..., description="전환할 페르소나 이름 (CONSERVATIVE, AGGRESSIVE, GROWTH, BALANCED)")


# CRUD Endpoints

@router.get("/personas", response_model=List[PersonaResponse])
async def get_all_personas(db: Session = Depends(get_db)):
    """
    모든 활성 페르소나 조회
    
    Returns:
        List of all active personas
    """
    service = get_persona_trading_service(db)
    personas = service.get_all_active_personas()
    return personas


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    특정 페르소나 조회
    
    Args:
        persona_id: 페르소나 ID
    
    Returns:
        Persona details
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona not found: {persona_id}")
    return persona


@router.post("/personas", response_model=PersonaResponse)
async def create_persona(request: PersonaCreateRequest, db: Session = Depends(get_db)):
    """
    새 페르소나 생성
    
    Args:
        request: 페르소나 생성 요청
    
    Returns:
        Created persona
    """
    # 기본 페르소나 중복 확인
    if request.is_default:
        existing_default = db.query(Persona).filter(Persona.is_default == True).first()
        if existing_default:
            existing_default.is_default = False
    
    # 가중치 합이 1.0인지 확인
    total_weight = request.trader_weight + request.risk_weight + request.analyst_weight
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Agent weights must sum to 1.0, got {total_weight}"
        )
    
    # 배분 비율 합이 1.0인지 확인
    total_allocation = request.stock_allocation + request.bond_allocation + request.cash_allocation
    if abs(total_allocation - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Asset allocations must sum to 1.0, got {total_allocation}"
        )
    
    persona = Persona(**request.model_dump())
    db.add(persona)
    db.commit()
    db.refresh(persona)
    
    return persona


@router.put("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: int,
    request: PersonaUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    페르소나 수정
    
    Args:
        persona_id: 페르소나 ID
        request: 페르소나 수정 요청
    
    Returns:
        Updated persona
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona not found: {persona_id}")
    
    # 기본 페르소나 중복 확인
    if request.is_default is True:
        existing_default = db.query(Persona).filter(
            and_(Persona.is_default == True, Persona.id != persona_id)
        ).first()
        if existing_default:
            existing_default.is_default = False
    
    # 필드 업데이트
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)
    
    persona.updated_at = datetime.now()
    db.commit()
    db.refresh(persona)
    
    return persona


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    페르소나 삭제
    
    Args:
        persona_id: 페르소나 ID
    
    Returns:
        Deletion result
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona not found: {persona_id}")
    
    # 기본 페르소나는 삭제 불가
    if persona.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default persona"
        )
    
    db.delete(persona)
    db.commit()
    
    return {"success": True, "message": f"Persona {persona_id} deleted successfully"}


@router.get("/user/{user_id}", response_model=PersonaResponse)
async def get_user_persona(user_id: str, db: Session = Depends(get_db)):
    """
    사용자의 페르소나 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        User's persona
    """
    service = get_persona_trading_service(db)
    persona = service.get_user_persona(user_id)
    
    if not persona:
        raise HTTPException(
            status_code=404,
            detail=f"No persona found for user: {user_id}"
        )
    
    return persona


@router.post("/user/{user_id}/switch")
async def switch_user_persona(
    user_id: str,
    request: SwitchUserPersonaRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 페르소나 전환
    
    Args:
        user_id: 사용자 ID
        request: 페르소나 전환 요청
    
    Returns:
        Switch result
    """
    service = get_persona_trading_service(db)
    success, message, new_persona = service.switch_persona(user_id, request.persona_name)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": success,
        "message": message,
        "new_persona": {
            "id": new_persona.id,
            "name": new_persona.name,
            "display_name": new_persona.display_name
        }
    }


@router.post("/allocation")
async def calculate_portfolio_allocation(
    request: PortfolioAllocationRequest,
    db: Session = Depends(get_db)
):
    """
    포트폴리오 배분 계산
    
    Args:
        request: 포트폴리오 배분 계산 요청
    
    Returns:
        Portfolio allocation details
    """
    persona = db.query(Persona).filter(Persona.id == request.persona_id).first()
    if not persona:
        raise HTTPException(
            status_code=404,
            detail=f"Persona not found: {request.persona_id}"
        )
    
    service = get_persona_trading_service(db)
    allocation = service.calculate_portfolio_allocation(
        persona,
        request.total_value,
        request.current_allocations
    )
    
    return {
        "persona_id": request.persona_id,
        "persona_name": persona.display_name,
        "total_value": request.total_value,
        "allocation": allocation
    }


@router.post("/position-size")
async def calculate_position_size(
    request: PositionSizeRequest,
    db: Session = Depends(get_db)
):
    """
    포지션 사이즈 계산
    
    Args:
        request: 포지션 사이즈 계산 요청
    
    Returns:
        Position size details
    """
    persona = db.query(Persona).filter(Persona.id == request.persona_id).first()
    if not persona:
        raise HTTPException(
            status_code=404,
            detail=f"Persona not found: {request.persona_id}"
        )
    
    service = get_persona_trading_service(db)
    position_size = service.calculate_position_size(
        persona,
        request.total_value,
        request.confidence,
        request.risk_level
    )
    
    return {
        "persona_id": request.persona_id,
        "persona_name": persona.display_name,
        "total_value": request.total_value,
        "confidence": request.confidence,
        "risk_level": request.risk_level,
        "position_size": position_size,
        "position_pct": position_size / request.total_value if request.total_value > 0 else 0
    }
