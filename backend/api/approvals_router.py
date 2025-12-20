"""
Approval Router - 승인 워크플로우 API

ChatGPT Feature 2 API Integration

엔드포인트:
- GET /api/approvals/pending - 대기 중 승인 요청 조회
- POST /api/approvals/{request_id}/approve - 승인 처리
- POST /api/approvals/{request_id}/reject - 거부 처리

작성일: 2025-12-16
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from backend.approval import (
    get_approval_manager,
    ApprovalRequest,
    ApprovalStatus
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


# Request/Response Models
class ApprovalRequestResponse(BaseModel):
    """승인 요청 응답"""
    request_id: str
    ticker: str
    action: str
    quantity: Optional[int]
    target_price: Optional[float]
    ai_reasoning: str
    consensus_confidence: float
    priority_score: float
    approval_level: str
    status: str
    requested_at: str
    
    @classmethod
    def from_approval_request(cls, req: ApprovalRequest):
        """ApprovalRequest에서 변환"""
        return cls(
            request_id=str(req.request_id),
            ticker=req.ticker,
            action=req.action,
            quantity=req.quantity,
            target_price=req.target_price,
            ai_reasoning=req.ai_reasoning,
            consensus_confidence=req.consensus_confidence,
            priority_score=req.priority_score,
            approval_level=req.approval_level.name,
            status=req.status.value,
            requested_at=req.requested_at.isoformat()
        )


class ApproveRequest(BaseModel):
    """승인 요청 바디"""
    approved_by: str
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    """거부 요청 바디"""
    rejected_by: str
    reason: str


# Endpoints
@router.get("/pending", response_model=List[ApprovalRequestResponse])
async def get_pending_approvals(ticker: Optional[str] = None):
    """
    대기 중 승인 요청 조회
    
    Query Params:
        ticker: 티커 필터 (선택)
    
    Returns:
        대기 중 승인 요청 리스트 (우선순위 순 정렬)
    """
    try:
        manager = get_approval_manager()
        
        # 자동 승인 체크
        manager.check_auto_approvals()
        
        # 대기 중 요청 조회
        pending = manager.get_pending_requests(ticker=ticker)
        
        # Mock 데이터 생성 (데모용) - 실제 ApprovalManager에 생성
        if len(pending) == 0:
            import logging
            
            logging.info("No pending approvals, creating mock data for demo")
            
            # NVDA - Strong Buy
            manager.create_request(
                ticker="NVDA",
                action="BUY",
                quantity=50,
                target_price=875.50,
                ai_reasoning="🎭 War Room Consensus: 5/5 AI agents agreed on STRONG BUY. "
                             "Jensen Huang's GTC keynote drove institutional buying (+$2.5B). "
                             "GPU demand surge, data center revenue +200% YoY. "
                             "Technical: RSI 65 (neutral), Breaking resistance at $870.",
                consensus_confidence=0.95,
                priority_score=0.88,
                debate_rounds=5
            )
            
            # TSLA - Sell Warning
            manager.create_request(
                ticker="TSLA",
                action="SELL",
                quantity=30,
                ai_reasoning="⚠️ War Room Warning: 4/5 agents recommend SELL. "
                             "RSI 72 (overbought), CEO controversy, delivery miss risk. "
                             "China competition intensifying. Macro: EV subsidy cuts.",
                consensus_confidence=0.75,
                priority_score=0.72,
                debate_rounds=5
            )
            
            # AAPL - Consensus Buy
            manager.create_request(
                ticker="AAPL",
                action="BUY",
                quantity=100,
                target_price=195.00,
                ai_reasoning="✅ Consensus: 5/5 agents BUY. "
                             "iPhone 16 sales exceeding expectations. "
                             "Services revenue growth +12% QoQ. Safe haven asset, Beta 0.8. "
                             "Berkshire holding stable.",
                consensus_confidence=0.90,
                priority_score=0.65,
                debate_rounds=5
            )
            
            # 다시 조회
            pending = manager.get_pending_requests(ticker=ticker)
        
        return [ApprovalRequestResponse.from_approval_request(req) for req in pending]
    
    except Exception as e:
        # 에러 발생 시 빈 리스트 반환
        import logging
        logging.error(f"Failed to get pending approvals: {e}", exc_info=True)
        return []


@router.post("/{request_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    request_id: str,
    body: ApproveRequest
):
    """
    승인 처리
    
    Path Params:
        request_id: 요청 ID
    
    Body:
        approved_by: 승인자
        notes: 승인 메모 (선택)
    
    Returns:
        승인된 요청
    """
    manager = get_approval_manager()
    
    try:
        request_uuid = UUID(request_id)
        approved = manager.approve(
            request_uuid,
            approved_by=body.approved_by,
            notes=body.notes
        )
        
        return ApprovalRequestResponse.from_approval_request(approved)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{request_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    request_id: str,
    body: RejectRequest
):
    """
    거부 처리
    
    Path Params:
        request_id: 요청 ID
    
    Body:
        rejected_by: 거부자
        reason: 거부 사유
    
    Returns:
        거부된 요청
    """
    manager = get_approval_manager()
    
    try:
        request_uuid = UUID(request_id)
        rejected = manager.reject(
            request_uuid,
            rejected_by=body.rejected_by,
            reason=body.reason
        )
        
        return ApprovalRequestResponse.from_approval_request(rejected)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{request_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(request_id: str):
    """
    특정 승인 요청 조회
    
    Path Params:
        request_id: 요청 ID
    """
    manager = get_approval_manager()
    
    try:
        request_uuid = UUID(request_id)
        request = manager.get_request(request_uuid)
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return ApprovalRequestResponse.from_approval_request(request)
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
