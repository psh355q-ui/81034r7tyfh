"""
War Room Analytics API Router

API endpoints for debate visualization and shadow trading performance

Author: AI Trading System
Date: 2025-12-28
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from backend.ai.war_room.debate_visualizer import DebateVisualizer
from backend.ai.war_room.shadow_trading_tracker import UnifiedShadowTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/war-room", tags=["War Room Analytics"])

# Global instances (production에서는 dependency injection 사용)
debate_visualizer = DebateVisualizer()
shadow_tracker = UnifiedShadowTracker()


@router.get("/debate/{session_id}")
async def get_debate_analysis(session_id: str):
    """
    전 세션의 토론 분석 결과 조회
    
    Returns:
        - Agent별 투표 분포
        - 의견 충돌 패턴
        - Confidence 통계
        - Agent 기여도
    """
    try:
        # TODO: DB에서 session 데이터 조회
        # 현재는 mock 데이터
        mock_session_data = {
            "session_id": session_id,
            "ticker": "AAPL",
            "timestamp": "2025-12-28T10:00:00",
            "agent_votes": {
                "trader": {"action": "BUY", "confidence": 0.85, "reasoning": "골든크로스 발생"},
                "news": {"action": "BUY", "confidence": 0.75, "reasoning": "긍정적 뉴스"},
                "risk": {"action": "HOLD", "confidence": 0.60, "reasoning": "변동성 증가"},
                "macro": {"action": "BUY", "confidence": 0.70, "reasoning": "금리 인하 기대"},
                "analyst": {"action": "BUY", "confidence": 0.80, "reasoning": "실적 양호"},
                "institutional": {"action": "SELL", "confidence": 0.65, "reasoning": "내부자 매도"}
            },
            "final_decision": {
                "action": "BUY",
                "confidence": 0.78,
                "vote_weights": {
                    "trader": 0.15,
                    "news": 0.12,
                    "risk": 0.18,
                    "macro": 0.15,
                    "analyst": 0.20,
                    "institutional": 0.20
                }
            }
        }
        
        result = await debate_visualizer.analyze_debate_session(mock_session_data)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debate/timeline")
async def get_debate_timeline(
    ticker: str = Query(..., description="Ticker symbol"),
    days: int = Query(30, ge=1, le=90, description="Number of days to retrieve")
):
    """
    티커별 토론 타임라인 조회
    
    Returns:
        일별 토론 요약 (세션 수, 합의도, 주요 액션)
    """
    try:
        # TODO: DB에서 sessions 조회
        # 현재는 빈 리스트
        sessions = []
        
        timeline = await debate_visualizer.get_debate_timeline(ticker, sessions, days)
        return {
            "ticker": ticker,
            "days": days,
            "timeline": timeline
        }
        
    except Exception as e:
        logger.error(f"Error getting debate timeline for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_name}/patterns")
async def get_agent_voting_patterns(
    agent_name: str,
    days: int = Query(30, ge=1, le=90, description="Number of days")
):
    """
    특정 Agent의 투표 패턴 분석
    
    Returns:
        - Action 분포
        - 평균 confidence
        - 최종 결정 일치율
        - Action별 confidence
    """
    try:
        # TODO: DB에서 agent sessions 조회
        sessions = []
        
        patterns = await debate_visualizer.get_agent_voting_patterns(agent_name, sessions, days)
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting patterns for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadow-trading/performance")
async def get_shadow_trading_performance(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    days: int = Query(30, ge=1, le=365, description="Number of days")
):
    """
    Shadow Trading 성과 조회
    
    Returns:
        - Win rate, Sharpe ratio
        - Max drawdown
        - Action별 성과
    """
    try:
        performance = await shadow_tracker.calculate_performance(ticker, days)
        return performance
        
    except Exception as e:
        logger.error(f"Error calculating shadow trading performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadow-trading/trades")
async def get_shadow_trades(
    status: Optional[str] = Query(None, description="Filter by status (OPEN|CLOSED)"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    limit: int = Query(20, ge=1, le=100, description="Number of trades to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Shadow Trade 목록 조회
    
    Returns:
        Paginated trade list
    """
    try:
        if status == "OPEN":
            trades = await shadow_tracker.get_open_trades(ticker)
            return {
                "trades": trades,
                "total": len(trades),
                "limit": limit,
                "offset": offset
            }
        else:
            result = await shadow_tracker.get_closed_trades(ticker, status, limit, offset)
            return result
        
    except Exception as e:
        logger.error(f"Error getting shadow trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadow-trading/trade/{trade_id}")
async def get_shadow_trade_detail(trade_id: int):
    """특정 Shadow Trade 상세 조회"""
    try:
        trade = await shadow_tracker.get_trade_by_id(trade_id)
        
        if not trade:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shadow-trading/execute")
async def execute_shadow_trade(war_room_result: dict):
    """
    War Room 결정을 Shadow Trade로 실행
    
    Request body:
    {
        "session_id": str,
        "ticker": str,
        "action": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "price": float,
        "size_usd": float (optional)
    }
    """
    try:
        result = await shadow_tracker.execute_shadow_trade(war_room_result)
        return result
        
    except Exception as e:
        logger.error(f"Error executing shadow trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shadow-trading/close/{trade_id}")
async def close_shadow_trade(trade_id: int, exit_price: float):
    """
    Shadow Trade 청산
    
    Args:
        trade_id: Trade ID
        exit_price: 청산가
    """
    try:
        result = await shadow_tracker.close_shadow_trade(trade_id, exit_price)
        
        if result.get("status") == "ERROR":
            raise HTTPException(status_code=400, detail=result.get("reason"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
