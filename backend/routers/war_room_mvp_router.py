"""
War Room MVP API Router

Phase: MVP Consolidation
Date: 2025-12-31

API Endpoints:
    - POST /api/war-room-mvp/deliberate - MVP 전쟁실 심의
    - GET /api/war-room-mvp/info - War Room 정보
    - GET /api/war-room-mvp/history - 결정 이력
    - GET /api/war-room-mvp/performance - 성과 측정
    - POST /api/war-room-mvp/shadow/start - Shadow Trading 시작
    - POST /api/war-room-mvp/shadow/execute - Shadow Trade 실행
    - GET /api/war-room-mvp/shadow/status - Shadow Trading 상태
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.mvp.war_room_mvp import WarRoomMVP
from execution.shadow_trading_mvp import ShadowTradingMVP, ShadowTradingStatus
import yfinance as yf

# Initialize router
router = APIRouter(prefix="/api/war-room-mvp", tags=["War Room MVP"])

# Initialize War Room MVP (singleton)
war_room = WarRoomMVP()

# Initialize Shadow Trading (singleton) - DB에서 활성 세션 복원 시도
shadow_trading = ShadowTradingMVP.load_active_session_from_db()

# 활성 세션이 없으면 새로 생성
if shadow_trading is None:
    print("ℹ️  No active Shadow Trading session found in DB. Creating new instance...")
    shadow_trading = ShadowTradingMVP(initial_capital=100000.0)
else:
    print(f"✅ Shadow Trading session restored from DB: {shadow_trading.session_id}")


# ============================================================================
# Request/Response Models
# ============================================================================

class DeliberationRequest(BaseModel):
    """심의 요청"""
    symbol: str
    action_context: str = Field(default="new_position", description="new_position | stop_loss_check | rebalancing")
    market_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional - 자동으로 yfinance에서 가져옴")
    portfolio_state: Optional[Dict[str, Any]] = Field(default=None, description="Optional - Shadow Trading에서 가져옴")
    additional_data: Optional[Dict[str, Any]] = Field(default=None, description="추가 데이터")


class ShadowTradeRequest(BaseModel):
    """Shadow Trade 요청"""
    symbol: str
    action: str  # "buy" | "sell"
    quantity: int
    price: float
    stop_loss_pct: Optional[float] = 0.02


# ============================================================================
# Helper Functions
# ============================================================================

def fetch_market_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch real-time market data for a symbol using yfinance

    Returns:
        market_data dict with price_data and market_conditions
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="5d")

        if hist.empty:
            # Fallback to minimal data
            return {
                "price_data": {
                    "current_price": 0,
                    "open": 0,
                    "high": 0,
                    "low": 0,
                    "volume": 0,
                    "week_52_high": 0,
                    "week_52_low": 0
                },
                "market_conditions": {
                    "is_market_open": False,
                    "volatility": 0
                }
            }

        latest = hist.iloc[-1]
        current_price = float(latest['Close'])

        # Calculate volatility from 5-day history
        volatility = float(hist['Close'].pct_change().std() * 100) if len(hist) > 1 else 0

        return {
            "price_data": {
                "current_price": current_price,
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "volume": int(latest['Volume']),
                "week_52_high": float(info.get('fiftyTwoWeekHigh', current_price * 1.2)),
                "week_52_low": float(info.get('fiftyTwoWeekLow', current_price * 0.8))
            },
            "market_conditions": {
                "is_market_open": True,
                "volatility": round(volatility, 2),
                "market_cap": info.get('marketCap', 0),
                "sector": info.get('sector', 'Unknown'),
                "industry": info.get('industry', 'Unknown')
            }
        }
    except Exception as e:
        print(f"⚠️  Failed to fetch market data for {symbol}: {e}")
        # Return minimal fallback data
        return {
            "price_data": {
                "current_price": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "week_52_high": 0,
                "week_52_low": 0
            },
            "market_conditions": {
                "is_market_open": False,
                "volatility": 0
            }
        }


# ============================================================================
# War Room MVP Endpoints
# ============================================================================

@router.post("/deliberate")
async def deliberate(request: DeliberationRequest) -> Dict[str, Any]:
    """
    MVP 전쟁실 심의

    3+1 Agent 시스템:
    - Trader Agent MVP (35%)
    - Risk Agent MVP (35%)
    - Analyst Agent MVP (30%)
    - PM Agent MVP (Final Decision)

    Parameters:
        - symbol: 종목 심볼 (필수)
        - action_context: 액션 컨텍스트 (기본값: "new_position")
        - market_data: 시장 데이터 (옵셔널 - 자동으로 yfinance에서 가져옴)
        - portfolio_state: 포트폴리오 상태 (옵셔널 - Shadow Trading에서 가져옴)

    Returns:
        - final_decision: approve/reject/reduce_size/silence
        - recommended_action: buy/sell/hold
        - confidence: 최종 confidence
        - agent_opinions: 각 Agent 의견
        - validation_result: Hard Rules 검증 결과
    """
    try:
        # 1. Fetch market data if not provided
        market_data = request.market_data
        if not market_data:
            print(f"📊 Fetching real-time market data for {request.symbol}...")
            market_data = fetch_market_data(request.symbol)

        # 2. Get portfolio state from Shadow Trading if not provided
        portfolio_state = request.portfolio_state
        if not portfolio_state:
            if shadow_trading and shadow_trading.status == ShadowTradingStatus.ACTIVE:
                # Calculate position value from open positions
                position_value = sum(
                    trade.quantity * trade.entry_price
                    for trade in shadow_trading.open_positions.values()
                )
                total_value = shadow_trading.available_cash + position_value

                portfolio_state = {
                    "total_value": total_value,
                    "available_cash": shadow_trading.available_cash,
                    "total_risk": position_value / total_value if total_value > 0 else 0.0,
                    "position_count": len(shadow_trading.open_positions),
                    "current_positions": [
                        {
                            "symbol": trade.symbol,
                            "quantity": trade.quantity,
                            "current_price": trade.entry_price,
                            "unrealized_pnl_pct": 0.0  # Will be calculated during update
                        }
                        for trade in shadow_trading.open_positions.values()
                    ]
                }
            else:
                # Default portfolio state for non-shadow trading
                portfolio_state = {
                    "total_value": 100000.0,
                    "available_cash": 100000.0,
                    "total_risk": 0.0,
                    "position_count": 0,
                    "current_positions": []
                }

        # 3. Run deliberation
        result = war_room.deliberate(
            symbol=request.symbol,
            action_context=request.action_context,
            market_data=market_data,
            portfolio_state=portfolio_state,
            additional_data=request.additional_data
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deliberation failed: {str(e)}")


@router.get("/info")
async def get_info() -> Dict[str, Any]:
    """
    War Room MVP 정보 조회

    Returns:
        - agent_structure: 3+1 구조
        - agents: Agent 정보
        - improvement_vs_legacy: Legacy 대비 개선 사항
    """
    try:
        info = war_room.get_war_room_info()
        # Add HARD_RULES for debugging
        if hasattr(war_room, 'pm_agent') and hasattr(war_room.pm_agent, 'HARD_RULES'):
            info['hard_rules'] = war_room.pm_agent.HARD_RULES
            info['hard_rules_loaded'] = True
        else:
            info['hard_rules'] = None
            info['hard_rules_loaded'] = False
            info['debug'] = {
                'has_pm_agent': hasattr(war_room, 'pm_agent'),
                'pm_agent_type': type(war_room.pm_agent).__name__ if hasattr(war_room, 'pm_agent') else None
            }
        return info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get info: {str(e)}")


@router.get("/history")
async def get_history(limit: int = 20) -> Dict[str, Any]:
    """
    결정 이력 조회

    Args:
        limit: 최대 조회 개수 (default: 20)

    Returns:
        - decisions: 결정 이력
        - total_count: 전체 결정 수
    """
    try:
        history = war_room.decision_history[-limit:]
        return {
            'decisions': history,
            'total_count': len(war_room.decision_history),
            'retrieved_count': len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/performance")
async def get_performance() -> Dict[str, Any]:
    """
    War Room 성과 측정

    Returns:
        - total_decisions: 총 결정 수
        - decision_breakdown: 결정 유형별 분포
        - average_confidence: 평균 confidence
    """
    try:
        decisions = war_room.decision_history

        if not decisions:
            return {
                'total_decisions': 0,
                'decision_breakdown': {},
                'average_confidence': 0.0
            }

        # Count decision types
        decision_counts = {}
        total_confidence = 0.0

        for decision in decisions:
            final_decision = decision.get('final_decision', 'unknown')
            decision_counts[final_decision] = decision_counts.get(final_decision, 0) + 1
            total_confidence += decision.get('confidence', 0.0)

        avg_confidence = total_confidence / len(decisions) if decisions else 0.0

        return {
            'total_decisions': len(decisions),
            'decision_breakdown': decision_counts,
            'average_confidence': avg_confidence,
            'session_id': war_room.session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


# ============================================================================
# Shadow Trading Endpoints
# ============================================================================

@router.post("/shadow/start")
async def start_shadow_trading(reason: str = "MVP validation") -> Dict[str, Any]:
    """
    Shadow Trading 시작

    Args:
        reason: 시작 이유 (default: "MVP validation")

    Returns:
        - success: 시작 성공 여부
        - message: 시작 메시지
        - start_date: 시작 일시
    """
    try:
        result = shadow_trading.start(reason=reason)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start shadow trading: {str(e)}")


@router.post("/shadow/execute")
async def execute_shadow_trade(request: ShadowTradeRequest) -> Dict[str, Any]:
    """
    Shadow Trade 실행

    Args:
        request: Shadow Trade 요청

    Returns:
        - success: 실행 성공 여부
        - message: 실행 메시지
        - trade_id: Trade ID
        - pnl: PnL (sell일 경우)
    """
    try:
        result = shadow_trading.execute_trade(
            symbol=request.symbol,
            action=request.action,
            quantity=request.quantity,
            price=request.price,
            stop_loss_pct=request.stop_loss_pct
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute shadow trade: {str(e)}")


@router.get("/shadow/status")
async def get_shadow_status() -> Dict[str, Any]:
    """
    Shadow Trading 상태 조회

    Returns:
        - status: active/paused/completed/failed
        - performance: 성과 지표
        - success_criteria_check: 성공 기준 체크
        - failure_conditions_check: 실패 조건 체크
    """
    try:
        info = shadow_trading.get_shadow_info()
        performance = shadow_trading.get_performance()
        success_check = shadow_trading.check_success_criteria()
        failure_check = shadow_trading.check_failure_conditions()

        return {
            'info': info,
            'performance': performance,
            'success_criteria_check': success_check,
            'failure_conditions_check': failure_check
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shadow status: {str(e)}")


@router.post("/shadow/update")
async def update_shadow_positions(market_prices: Dict[str, float]) -> Dict[str, Any]:
    """
    Shadow Trading 포지션 업데이트

    Args:
        market_prices: {symbol: current_price}

    Returns:
        - total_equity: 총 자산
        - available_cash: 가용 현금
        - positions_value: 포지션 가치
        - stop_loss_triggered: Stop Loss 발동 내역
    """
    try:
        result = shadow_trading.update_positions(market_prices=market_prices)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update positions: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    War Room MVP 헬스 체크

    Returns:
        - status: healthy/degraded
        - war_room_active: War Room 활성 여부
        - shadow_trading_active: Shadow Trading 활성 여부
    """
    return {
        'status': 'healthy',
        'war_room_active': True,
        'shadow_trading_active': shadow_trading.status.value == 'active',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }


# Export router
__all__ = ['router']
