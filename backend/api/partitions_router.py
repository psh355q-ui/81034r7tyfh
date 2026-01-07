"""
Account Partitioning API - Virtual Wallet Management

Phase: Phase 6 API Integration
Date: 2026-01-05

Endpoints:
    GET  /api/partitions/summary          - 전체 지갑 요약
    GET  /api/partitions/wallet/{wallet}  - 특정 지갑 상세
    POST /api/partitions/allocate         - 지갑에 포지션 할당
    POST /api/partitions/sell             - 지갑에서 포지션 매도
    GET  /api/partitions/positions        - 전체 포지션 조회
    GET  /api/partitions/rebalance        - 리밸런싱 추천
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from backend.ai.portfolio.account_partitioning import (
    AccountPartitionManager,
    WalletType,
    get_partition_manager,
    DEFAULT_WALLET_CONFIGS,
)

router = APIRouter(prefix="/api/partitions", tags=["Account Partitioning"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AllocateRequest(BaseModel):
    """포지션 할당 요청"""
    user_id: str = Field(default="default_user", description="사용자 ID")
    wallet: str = Field(..., description="지갑 유형: core | income | satellite")
    ticker: str = Field(..., description="종목 티커")
    quantity: int = Field(..., description="수량")
    price: float = Field(..., description="가격")


class SellRequest(BaseModel):
    """포지션 매도 요청"""
    user_id: str = Field(default="default_user", description="사용자 ID")
    wallet: str = Field(..., description="지갑 유형: core | income | satellite")
    ticker: str = Field(..., description="종목 티커")
    quantity: int = Field(..., description="수량")
    price: float = Field(..., description="가격")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/summary")
async def get_summary(
    user_id: str = Query(default="default_user", description="사용자 ID"),
    total_capital: float = Query(default=100000, description="초기 자본금")
):
    """
    전체 지갑 요약 조회
    
    Returns:
        각 지갑의 가치, 비율, 편차, 리밸런싱 필요 여부
    """
    manager = get_partition_manager(user_id, total_capital)
    return manager.get_all_summaries()


@router.get("/wallet/{wallet}")
async def get_wallet_detail(
    wallet: str,
    user_id: str = Query(default="default_user", description="사용자 ID")
):
    """
    특정 지갑 상세 조회
    
    Args:
        wallet: 지갑 유형 (core, income, satellite)
    
    Returns:
        지갑 상세 정보 및 포지션 목록
    """
    try:
        manager = get_partition_manager(user_id)
        wallet_type = WalletType(wallet.lower())
        
        summary = manager.get_wallet_summary(wallet)
        positions = [p.to_dict() for p in manager.positions[wallet_type]]
        config = manager.configs[wallet_type]
        
        return {
            "wallet": wallet_type.value,
            "description": config.description,
            "allowed_leverage": config.allowed_leverage,
            "target_pct": config.target_pct,
            "current_value": summary.current_value,
            "current_pct": summary.current_pct,
            "deviation": summary.deviation,
            "cash": manager.wallet_cash[wallet_type],
            "positions_count": summary.positions_count,
            "positions": positions,
            "unrealized_pnl": summary.unrealized_pnl,
            "unrealized_pnl_pct": summary.unrealized_pnl_pct,
            "needs_rebalance": summary.needs_rebalance
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Invalid wallet: {wallet}")


@router.post("/allocate")
async def allocate_to_wallet(request: AllocateRequest):
    """
    지갑에 포지션 할당 (매수)
    
    레버리지 상품은 SATELLITE 지갑에만 허용됩니다.
    
    Returns:
        할당 결과
    """
    manager = get_partition_manager(request.user_id)
    result = manager.allocate_to_wallet(
        wallet=request.wallet,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/sell")
async def sell_from_wallet(request: SellRequest):
    """
    지갑에서 포지션 매도
    
    Returns:
        매도 결과 및 실현손익
    """
    manager = get_partition_manager(request.user_id)
    result = manager.sell_from_wallet(
        wallet=request.wallet,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/positions")
async def get_all_positions(
    user_id: str = Query(default="default_user", description="사용자 ID")
):
    """
    전체 포지션 조회
    
    Returns:
        모든 지갑의 포지션 목록
    """
    manager = get_partition_manager(user_id)
    return {
        "positions": manager.get_all_positions(),
        "total_count": len(manager.get_all_positions())
    }


@router.get("/rebalance")
async def get_rebalance_recommendations(
    user_id: str = Query(default="default_user", description="사용자 ID")
):
    """
    리밸런싱 추천 조회
    
    목표 비율에서 5% 이상 벗어난 지갑에 대한 조정 추천
    
    Returns:
        리밸런싱이 필요한 지갑 및 권장 조정액
    """
    manager = get_partition_manager(user_id)
    recommendations = manager.get_rebalance_recommendations()
    
    return {
        "needs_rebalance": len(recommendations) > 0,
        "recommendations": recommendations,
        "explanation": {
            "core": "장기 투자 (60% 목표)",
            "income": "배당/현금흐름 (30% 목표)",
            "satellite": "공격적 투자 (10% 목표)"
        }
    }


@router.get("/configs")
async def get_wallet_configs():
    """
    지갑 설정 조회
    
    Returns:
        각 지갑의 목표 비율, 허용 범위, 레버리지 허용 여부
    """
    configs = {}
    for wallet_type, config in DEFAULT_WALLET_CONFIGS.items():
        configs[wallet_type.value] = {
            "description": config.description,
            "target_pct": config.target_pct,
            "min_pct": config.min_pct,
            "max_pct": config.max_pct,
            "allowed_leverage": config.allowed_leverage
        }
    return configs


@router.get("/leverage/{ticker}")
async def check_leverage(ticker: str):
    """
    레버리지 상품 확인
    
    Args:
        ticker: 종목 티커
        
    Returns:
        레버리지 여부 및 허용 가능한 지갑
    """
    from backend.ai.safety.leverage_guardian import get_leverage_guardian
    
    guardian = get_leverage_guardian()
    is_lev = guardian.is_leveraged(ticker)
    if is_lev:
        category = guardian.get_category(ticker)
        # 3x 레버리지/인버스 여부에 따라 비율 설정 (기본값 3.0으로 가정)
        # 실제로는 카테고리나 메타데이터에 비율 정보가 있어야 하지만, 현재는 3x 위주이므로 3.0으로 설정
        ratio = 3.0 if "3x" in str(category) or category.value in ["leveraged_long", "leveraged_short"] else 1.0
    else:
        ratio = 1.0
    
    allowed_wallets = ["core", "income", "satellite"]
    if is_lev:
        allowed_wallets = ["satellite"]
        
    return {
        "ticker": ticker.upper(),
        "is_leveraged": is_lev,
        "leverage_ratio": ratio,
        "allowed_wallets": allowed_wallets,
        "note": "레버리지 상품은 SATELLITE 지갑에만 허용됩니다." if is_lev else "레버리지 DB에 없는 티커입니다. 일반 종목으로 간주됩니다."
    }
