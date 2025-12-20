"""
Auto Trade API Router
=====================
자동 거래 시스템 API 엔드포인트

Endpoints:
- POST /api/auto-trade/start - 자동 거래 시작
- POST /api/auto-trade/stop - 자동 거래 중지
- GET /api/auto-trade/status - 현재 상태
- POST /api/auto-trade/execute - Consensus 결과로 거래 실행
- POST /api/auto-trade/reset-kill-switch - Kill Switch 리셋
- GET /api/auto-trade/stats - 일일 통계

작성일: 2025-12-09
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-trade", tags=["Auto Trade"])


# ============================================
# Request/Response Models
# ============================================

class StartAutoTradeRequest(BaseModel):
    """자동 거래 시작 요청"""
    is_virtual: bool = Field(default=True, description="모의투자 여부")
    dry_run: bool = Field(default=True, description="Dry Run 모드")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_virtual": True,
                "dry_run": True
            }
        }


class ExecuteTradeRequest(BaseModel):
    """거래 실행 요청"""
    ticker: str = Field(..., description="종목 티커")
    action: str = Field(..., description="액션 (BUY/SELL/DCA/STOP_LOSS)")
    consensus_approved: bool = Field(default=True, description="Consensus 승인 여부")
    dry_run: Optional[bool] = Field(default=None, description="Dry Run 모드")
    is_virtual: Optional[bool] = Field(default=None, description="모의투자 여부")
    consensus_result: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Consensus Engine 투표 결과"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "action": "BUY",
                "consensus_approved": True,
                "dry_run": True,
                "is_virtual": True,
                "consensus_result": {
                    "final_decision": "APPROVED",
                    "votes": {"claude": "BUY", "gemini": "BUY", "gpt": "HOLD"},
                    "consensus_strength": 0.85
                }
            }
        }


class QuickExecuteRequest(BaseModel):
    """빠른 거래 실행 (Consensus 자동 호출)"""
    ticker: str = Field(..., description="종목 티커")
    action: str = Field(..., description="액션 (BUY/SELL/DCA/STOP_LOSS)")
    headline: str = Field(..., description="뉴스 헤드라인")
    dry_run: bool = Field(default=True, description="Dry Run 모드")
    is_virtual: bool = Field(default=True, description="모의투자 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "action": "BUY",
                "headline": "NVIDIA reports record AI chip revenue",
                "dry_run": True,
                "is_virtual": True
            }
        }


# ============================================
# API Endpoints
# ============================================

@router.post("/start")
async def start_auto_trade(request: StartAutoTradeRequest = None) -> Dict:
    """
    자동 거래 시작
    
    Kill Switch가 발동되지 않은 상태에서만 시작 가능
    """
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    
    # 설정 업데이트
    if request:
        service.config.default_is_virtual = request.is_virtual
        service.config.dry_run_mode = request.dry_run
    
    result = service.start()
    
    return {
        **result,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/stop")
async def stop_auto_trade() -> Dict:
    """자동 거래 중지"""
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    result = service.stop()
    
    return {
        **result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status")
async def get_auto_trade_status() -> Dict:
    """현재 자동 거래 상태 조회"""
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    return service.get_status()


@router.post("/execute")
async def execute_trade(request: ExecuteTradeRequest) -> Dict:
    """
    Consensus 결과를 바탕으로 거래 실행
    
    - dry_run=True: 실제 주문 없이 시뮬레이션
    - is_virtual=True: KIS 모의투자 사용
    """
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    
    # Consensus 결과 구성
    consensus_result = request.consensus_result or {
        "final_decision": "APPROVED" if request.consensus_approved else "REJECTED"
    }
    
    execution = await service.execute_from_consensus(
        ticker=request.ticker,
        action=request.action,
        consensus_result=consensus_result,
        dry_run=request.dry_run,
        is_virtual=request.is_virtual
    )
    
    return {
        "ticker": execution.ticker,
        "action": execution.action,
        "approved": execution.approved,
        "executed": execution.executed,
        "dry_run": execution.dry_run,
        "kis_result": execution.kis_result,
        "error": execution.error,
        "timestamp": execution.timestamp
    }


@router.post("/quick-execute")
async def quick_execute_trade(request: QuickExecuteRequest) -> Dict:
    """
    뉴스 기반 빠른 거래 실행
    
    1. Consensus Engine으로 투표 진행
    2. 승인되면 자동으로 거래 실행
    """
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    
    # Consensus 투표 진행 (Mock)
    # 실제로는 ConsensusEngine을 호출해야 함
    try:
        from backend.ai.consensus.consensus_engine import ConsensusEngine
        from backend.ai.consensus.schemas import MarketContext, NewsInfo
        
        engine = ConsensusEngine()
        context = MarketContext(
            ticker=request.ticker,
            company_name=request.ticker,
            news=NewsInfo(
                headline=request.headline,
                segment="general",
                sentiment=0.7
            )
        )
        
        consensus_result = await engine.vote_on_signal(context, request.action)
        
    except ImportError:
        # Fallback: Mock consensus (테스트용)
        consensus_result = {
            "final_decision": "APPROVED",
            "votes": {
                "claude": request.action,
                "gemini": request.action,
                "gpt": "HOLD"
            },
            "consensus_strength": 0.85,
            "mode": "mock"
        }
    
    # 거래 실행
    execution = await service.execute_from_consensus(
        ticker=request.ticker,
        action=request.action,
        consensus_result=consensus_result,
        dry_run=request.dry_run,
        is_virtual=request.is_virtual
    )
    
    return {
        "ticker": execution.ticker,
        "action": execution.action,
        "consensus_result": consensus_result,
        "approved": execution.approved,
        "executed": execution.executed,
        "dry_run": execution.dry_run,
        "kis_result": execution.kis_result,
        "error": execution.error,
        "timestamp": execution.timestamp
    }


@router.post("/reset-kill-switch")
async def reset_kill_switch() -> Dict:
    """Kill Switch 리셋"""
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    result = service.reset_kill_switch()
    
    return {
        **result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_daily_stats() -> Dict:
    """일일 거래 통계 조회"""
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    stats = service.get_daily_stats()
    
    return {
        **stats,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/reset-stats")
async def reset_daily_stats() -> Dict:
    """일일 통계 리셋"""
    from backend.services.auto_trade_service import get_auto_trade_service
    
    service = get_auto_trade_service()
    service.reset_daily_stats()
    
    return {
        "success": True,
        "message": "Daily stats reset",
        "timestamp": datetime.now().isoformat()
    }
