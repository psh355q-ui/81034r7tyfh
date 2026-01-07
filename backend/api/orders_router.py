"""
Orders API Router

Phase 27: Frontend UI Integration
Date: 2025-12-23

API Endpoints:
- GET /api/orders - 주문 히스토리 조회
- GET /api/orders/{order_id} - 특정 주문 상세
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import logging

from backend.database.models import Order
from backend.database.repository import get_sync_session
from backend.ai.skills.common.logging_decorator import log_endpoint

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
                updated_at=None,  # Not in current model
                filled_at=order.filled_at.isoformat() if order.filled_at else None
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
            updated_at=None,
            filled_at=order.filled_at.isoformat() if order.filled_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

    finally:
        db.close()
