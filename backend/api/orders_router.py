"""
Orders API Router

Phase 27: Frontend UI Integration
Date: 2025-12-23

Phase 5, T5.1: Multi-Strategy Conflict Checking
Date: 2026-01-12

API Endpoints:
- GET /api/orders - 주문 히스토리 조회
- GET /api/orders/{order_id} - 특정 주문 상세
- POST /api/orders/check-conflict - 주문 충돌 검사 (Dry Run, Phase 5 T5.1)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import logging

from backend.database.models import Order
from backend.database.repository import get_sync_session
from backend.ai.skills.common.logging_decorator import log_endpoint

# Phase 5, T5.1: Conflict Detection
from backend.ai.skills.system.conflict_detector import ConflictDetector
from backend.database.repository_multi_strategy import StrategyRepository
from backend.api.schemas.strategy_schemas import (
    ConflictCheckRequest,
    ConflictCheckResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ============================================================================
# Response Models
# ============================================================================

class OrderResponse(BaseModel):
    """주문 응답 모델"""
    id: int
    ticker: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    order_type: str  # MARKET, LIMIT
    status: str  # PENDING, FILLED, CANCELLED, REJECTED
    broker: str
    order_id: str
    signal_id: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None
    filled_at: Optional[str] = None
    filled_quantity: Optional[int] = 0
    order_metadata: Optional[dict] = None
    needs_manual_review: Optional[bool] = False

    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=List[OrderResponse])
@log_endpoint("orders", "system")
async def get_orders(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, FILLED, CANCELLED)"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    limit: int = Query(50, ge=1, le=500, description="Number of orders to return")
):
    """
    Get order history

    Args:
        status: Filter by order status
        ticker: Filter by ticker symbol
        limit: Maximum number of orders to return

    Returns:
        List of orders
    """
    db = get_sync_session()

    try:
        # Build query
        query = db.query(Order)

        # Apply filters
        if status:
            query = query.filter(Order.status == status.upper())

        if ticker:
            query = query.filter(Order.ticker == ticker.upper())

        # Order by created_at descending (newest first)
        query = query.order_by(Order.created_at.desc())

        # Apply limit
        query = query.limit(limit)

        # Execute query
        orders = query.all()

        logger.info(f"📊 Fetched {len(orders)} orders (status={status}, ticker={ticker})")

        # Convert to response models
        result = []
        for order in orders:
            # Use filled_price or limit_price as price
            price = order.filled_price or order.limit_price or 0.0
            result.append(OrderResponse(
                id=order.id,
                ticker=order.ticker,
                action=order.action,
                quantity=order.quantity,
                price=price,
                order_type=order.order_type or "MARKET",
                status=order.status,
                broker="SHADOW",  # Default broker for shadow trading
                order_id=order.order_id or "",
                signal_id=order.signal_id,
                created_at=order.created_at.isoformat() if order.created_at else None,
                updated_at=order.updated_at.isoformat() if order.updated_at else None,
                filled_at=order.filled_at.isoformat() if order.filled_at else None,
                filled_quantity=order.filled_quantity or 0,
                order_metadata=order.order_metadata or {},
                needs_manual_review=order.needs_manual_review or False
            ))

        return result

    except Exception as e:
        logger.error(f"❌ Failed to fetch orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

    finally:
        db.close()


@router.get("/{order_id}", response_model=OrderResponse)
@log_endpoint("orders", "system")
async def get_order(order_id: int):
    """
    Get specific order details

    Args:
        order_id: Order ID

    Returns:
        Order details
    """
    db = get_sync_session()

    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        logger.info(f"📊 Fetched order #{order_id}")

        price = order.filled_price or order.limit_price or 0.0
        return OrderResponse(
            id=order.id,
            ticker=order.ticker,
            action=order.action,
            quantity=order.quantity,
            price=price,
            order_type=order.order_type or "MARKET",
            status=order.status,
            broker="SHADOW",
            order_id=order.order_id or "",
            signal_id=order.signal_id,
            created_at=order.created_at.isoformat() if order.created_at else None,
            updated_at=order.updated_at.isoformat() if order.updated_at else None,
            filled_at=order.filled_at.isoformat() if order.filled_at else None,
            filled_quantity=order.filled_quantity or 0,
            order_metadata=order.order_metadata or {},
            needs_manual_review=order.needs_manual_review or False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

    finally:
        db.close()


# ============================================================================
# Phase 5, T5.1: Multi-Strategy Conflict Checking
# ============================================================================

@router.post("/check-conflict", response_model=ConflictCheckResponse)
@log_endpoint("orders", "system")
async def check_order_conflict(request: ConflictCheckRequest):
    """
    주문 충돌 검사 (Dry Run)

    **Phase 5, T5.1: Multi-Strategy Orchestration**

    실제 주문을 생성하지 않고 충돌 여부만 확인합니다.
    ConflictDetector를 직접 호출하여 OrderManager와 동일한 비즈니스 로직을 사용합니다.

    **Request Body:**
    ```json
    {
        "strategy_id": "uuid-of-strategy",
        "ticker": "AAPL",
        "action": "BUY",
        "quantity": 100
    }
    ```

    **Response:**
    ```json
    {
        "has_conflict": false,
        "resolution": "allowed",
        "can_proceed": true,
        "reasoning": "No current owner. Free to trade.",
        "conflict_detail": null
    }
    ```

    **Resolution Types:**
    - `allowed`: 충돌 없음, 주문 가능
    - `blocked`: 충돌 발생, 우선순위 부족으로 차단
    - `priority_override`: 충돌 발생하지만 우선순위가 높아 소유권 이전 후 주문 가능

    **Use Cases:**
    1. 프론트엔드에서 주문 버튼 활성화/비활성화 결정
    2. 사용자에게 충돌 경고 메시지 표시
    3. 자동 트레이딩 시스템에서 주문 전 검증

    **Raises:**
    - 404: Strategy not found
    - 400: Strategy is inactive
    - 422: Invalid request (missing fields, invalid action type)
    """
    db = get_sync_session()

    try:
        # 1. Validate Strategy Exists and is Active
        strategy_repo = StrategyRepository(db)
        strategy = strategy_repo.get_by_id(request.strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy {request.strategy_id} not found"
            )

        if not strategy.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{strategy.name}' is inactive. Activate it first."
            )

        # 2. Call ConflictDetector (same logic as OrderManager.create_order)
        detector = ConflictDetector(db)

        conflict_response = detector.check_conflict(
            strategy_id=request.strategy_id,
            ticker=request.ticker.upper(),
            action=request.action,
            quantity=request.quantity
        )

        logger.info(
            f"🔍 Conflict check: {request.ticker} | Strategy: {strategy.name} | "
            f"Resolution: {conflict_response.resolution.value} | Can proceed: {conflict_response.can_proceed}"
        )

        # 3. Return ConflictCheckResponse
        # ConflictDetector already returns the correct Pydantic model
        return conflict_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Conflict check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conflict check failed: {str(e)}")

    finally:
        db.close()
