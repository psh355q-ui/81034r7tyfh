"""
Position API Router

Phase E3: Position Tracking System

포지션 관리 및 조회를 위한 REST API 엔드포인트

작성일: 2025-12-06
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.data.position_tracker import (
    get_position_tracker,
    Position,
    PositionStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/positions", tags=["Positions"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreatePositionRequest(BaseModel):
    """포지션 생성 요청"""
    ticker: str = Field(..., description="종목 티커")
    company_name: str = Field(..., description="회사명")
    initial_price: float = Field(..., gt=0, description="초기 매수가")
    initial_amount: float = Field(..., gt=0, description="초기 투자액")
    reasoning: str = Field(default="", description="매수 사유")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "company_name": "NVIDIA",
                "initial_price": 150.0,
                "initial_amount": 10000.0,
                "reasoning": "Strong AI fundamentals and market leadership"
            }
        }


class AddDCARequest(BaseModel):
    """DCA 추가 요청"""
    ticker: str = Field(..., description="종목 티커")
    price: float = Field(..., gt=0, description="DCA 가격")
    amount: float = Field(..., gt=0, description="DCA 투자액")
    reasoning: str = Field(default="", description="DCA 사유")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "price": 135.0,
                "amount": 5000.0,
                "reasoning": "10% price drop, fundamentals still intact"
            }
        }


class ClosePositionRequest(BaseModel):
    """포지션 청산 요청"""
    ticker: str = Field(..., description="종목 티커")
    exit_price: float = Field(..., gt=0, description="청산 가격")
    reason: str = Field(default="manual", description="청산 사유 (manual/stop_loss)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "exit_price": 165.0,
                "reason": "manual"
            }
        }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/create")
async def create_position(request: CreatePositionRequest):
    """
    새 포지션 생성 (초기 매수)

    Returns:
        생성된 포지션 정보
    """
    try:
        logger.info(f"Creating position: {request.ticker} @ ${request.initial_price}")

        tracker = get_position_tracker()
        position = tracker.create_position(
            ticker=request.ticker,
            company_name=request.company_name,
            initial_price=request.initial_price,
            initial_amount=request.initial_amount,
            reasoning=request.reasoning
        )

        return {
            "success": True,
            "position": position.to_dict()
        }

    except ValueError as e:
        logger.warning(f"Failed to create position: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create position: {str(e)}")


@router.post("/add-dca")
async def add_dca(request: AddDCARequest):
    """
    DCA 진입 추가

    Returns:
        업데이트된 포지션 정보
    """
    try:
        logger.info(f"Adding DCA: {request.ticker} @ ${request.price}")

        tracker = get_position_tracker()
        position = tracker.add_dca_entry(
            ticker=request.ticker,
            price=request.price,
            amount=request.amount,
            reasoning=request.reasoning
        )

        return {
            "success": True,
            "position": position.to_dict()
        }

    except ValueError as e:
        logger.warning(f"Failed to add DCA: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding DCA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add DCA: {str(e)}")


@router.post("/close")
async def close_position(request: ClosePositionRequest):
    """
    포지션 청산

    Returns:
        청산 결과 및 실현 손익
    """
    try:
        logger.info(f"Closing position: {request.ticker} @ ${request.exit_price}")

        tracker = get_position_tracker()
        result = tracker.close_position(
            ticker=request.ticker,
            exit_price=request.exit_price,
            reason=request.reason
        )

        position = tracker.get_position(request.ticker)

        return {
            "success": True,
            "pnl": result,
            "position": position.to_dict() if position else None
        }

    except ValueError as e:
        logger.warning(f"Failed to close position: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")


@router.get("/{ticker}")
async def get_position(ticker: str, current_price: Optional[float] = Query(None)):
    """
    특정 포지션 조회

    Args:
        ticker: 종목 티커
        current_price: 현재 가격 (미실현 손익 계산용, optional)

    Returns:
        포지션 상세 정보
    """
    try:
        tracker = get_position_tracker()
        position = tracker.get_position(ticker)

        if not position:
            raise HTTPException(status_code=404, detail=f"Position not found: {ticker}")

        pos_dict = position.to_dict()

        # 현재가 제공 시 미실현 손익 추가
        if current_price and position.status == PositionStatus.OPEN:
            pnl_info = position.get_unrealized_pnl(current_price)
            pos_dict["unrealized_pnl"] = pnl_info

        return pos_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")


@router.get("/")
async def list_positions(
    status: Optional[str] = Query(None, description="Filter by status (open/closed/stopped)"),
    current_prices: Optional[str] = Query(None, description="Current prices as JSON: {\"NVDA\":150.0}")
):
    """
    포지션 목록 조회

    Args:
        status: 필터링할 상태 (open/closed/stopped)
        current_prices: 현재 가격 JSON (미실현 손익 계산용)

    Returns:
        포지션 목록
    """
    try:
        tracker = get_position_tracker()

        if status:
            if status == "open":
                positions = tracker.get_open_positions()
            else:
                positions = [
                    p for p in tracker.get_all_positions()
                    if p.status.value == status
                ]
        else:
            positions = tracker.get_all_positions()

        # Current prices 파싱
        prices = {}
        if current_prices:
            import json
            prices = json.loads(current_prices)

        # 포지션 변환
        positions_data = []
        for pos in positions:
            pos_dict = pos.to_dict()

            # 미실현 손익 추가
            if pos.status == PositionStatus.OPEN and pos.ticker in prices:
                pnl_info = pos.get_unrealized_pnl(prices[pos.ticker])
                pos_dict["unrealized_pnl"] = pnl_info

            positions_data.append(pos_dict)

        return {
            "count": len(positions_data),
            "positions": positions_data
        }

    except Exception as e:
        logger.error(f"Error listing positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list positions: {str(e)}")


@router.get("/portfolio/summary")
async def get_portfolio_summary(current_prices: str = Query(..., description="Current prices as JSON")):
    """
    포트폴리오 전체 요약

    Args:
        current_prices: 현재 가격 JSON {"NVDA": 150.0, "TSLA": 250.0}

    Returns:
        포트폴리오 요약 정보
    """
    try:
        import json
        prices = json.loads(current_prices)

        tracker = get_position_tracker()
        summary = tracker.get_portfolio_summary(prices)

        return summary

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for current_prices")
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")
