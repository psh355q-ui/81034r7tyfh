"""
Portfolio Router Extension - FLE 엔드포인트 추가

ChatGPT Feature 3 API Integration

새 엔드포인트:
- GET /api/portfolio/fle - 현재 FLE 계산
- GET /api/portfolio/fle-history - FLE 히스토리

작성일: 2025-12-16
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from backend.metrics import (
    get_fle_calculator,
    Portfolio,
    Position,
    FLEResult
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# Request/Response Models
class PositionInput(BaseModel):
    """포지션 입력"""
    ticker: str
    quantity: int
    current_price: float
    cost_basis: float


class PortfolioInput(BaseModel):
    """포트폴리오 입력"""
    user_id: str
    positions: List[PositionInput]
    cash: float = 0.0


class FLEResponse(BaseModel):
    """FLE 응답"""
    fle: float
    peak_fle: float
    drawdown: float
    drawdown_pct: float
    total_position_value: float
    estimated_fees: float
    estimated_tax: float
    cash_balance: float
    alert_level: str
    safety_message: str
    calculated_at: str
    
    @classmethod
    def from_fle_result(cls, result: FLEResult, safety_message: str):
        """FLEResult에서 변환"""
        return cls(
            fle=result.fle,
            peak_fle=result.peak_fle,
            drawdown=result.drawdown,
            drawdown_pct=result.drawdown_pct,
            total_position_value=result.total_position_value,
            estimated_fees=result.estimated_fees,
            estimated_tax=result.estimated_tax,
            cash_balance=result.cash_balance,
            alert_level=result.alert_level,
            safety_message=safety_message,
            calculated_at=result.calculated_at.isoformat()
        )


# Endpoints
@router.post("/fle", response_model=FLEResponse)
async def calculate_fle(portfolio_input: PortfolioInput):
    """
    FLE (Forced Liquidation Equity) 계산
    
    Body:
        user_id: 사용자 ID
        positions: 포지션 리스트
        cash: 현금 잔고
    
    Returns:
        FLE 계산 결과 + 안전 메시지
    
    Example:
        POST /api/portfolio/fle
        {
            "user_id": "user123",
            "positions": [
                {
                    "ticker": "AAPL",
                    "quantity": 100,
                    "current_price": 180,
                    "cost_basis": 150
                }
            ],
            "cash": 10000
        }
    """
    try:
        # Portfolio 객체 생성
        positions = [
            Position(
                ticker=p.ticker,
                quantity=p.quantity,
                current_price=p.current_price,
                cost_basis=p.cost_basis
            )
            for p in portfolio_input.positions
        ]
        
        portfolio = Portfolio(
            user_id=portfolio_input.user_id,
            positions=positions,
            cash=portfolio_input.cash
        )
        
        # FLE 계산
        calculator = get_fle_calculator()
        result = calculator.calculate_fle(portfolio)
        
        # 안전 메시지 생성
        safety_message = calculator.get_safety_message(result)
        
        return FLEResponse.from_fle_result(result, safety_message)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fle-history")
async def get_fle_history(
    user_id: str,
    days: int = 30
):
    """
    FLE 히스토리 조회
    
    Query Params:
        user_id: 사용자 ID
        days: 조회 일수 (기본 30일)
    
    Returns:
        FLE 히스토리 리스트
    """
    calculator = get_fle_calculator()
    history = calculator.get_fle_history(user_id, days)
    
    return [
        {
            "fle": h.fle,
            "peak_fle": h.peak_fle,
            "drawdown_pct": h.drawdown_pct,
            "alert_level": h.alert_level,
            "calculated_at": h.calculated_at.isoformat()
        }
        for h in history
    ]
