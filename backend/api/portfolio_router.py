"""
Portfolio API Router

Phase 27: Frontend UI Integration
Date: 2025-12-23

API Endpoints:
- GET /api/portfolio - 포트폴리오 현황 조회
- GET /api/portfolio/positions - 보유 종목 조회
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import os

from backend.brokers.kis_broker import KISBroker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ============================================================================
# Response Models
# ============================================================================

class PositionResponse(BaseModel):
    """보유 종목 응답 모델"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_pct: float
    daily_pnl: float
    daily_return_pct: float
    # 배당 정보 (옵션 B - KIS API 통합)
    annual_dividend: Optional[float] = 0.0
    dividend_yield: Optional[float] = 0.0
    dividend_frequency: Optional[str] = "Q"
    next_dividend_date: Optional[str] = ""


class PortfolioResponse(BaseModel):
    """포트폴리오 응답 모델"""
    total_value: float
    cash: float
    invested: float
    total_pnl: float
    total_pnl_pct: float
    daily_pnl: float
    daily_return_pct: float
    positions: List[PositionResponse]


# ============================================================================
# Helper Functions
# ============================================================================

def get_kis_broker() -> Optional[KISBroker]:
    """Get KIS Broker instance"""
    try:
        is_virtual = os.environ.get("KIS_IS_VIRTUAL", "true").lower() == "true"
        
        # Select account number based on mode
        if is_virtual:
            account_no = os.environ.get("KIS_PAPER_ACCOUNT") or os.environ.get("KIS_ACCOUNT_NUMBER", "")
        else:
            account_no = os.environ.get("KIS_ACCOUNT_NUMBER", "")

        if not account_no:
            logger.error("KIS_ACCOUNT_NUMBER not set")
            return None

        broker = KISBroker(
            account_no=account_no,
            is_virtual=is_virtual
        )

        return broker

    except Exception as e:
        logger.error(f"Failed to initialize KIS Broker: {e}")
        return None


def _get_mock_portfolio() -> PortfolioResponse:
    """
    Return mock portfolio data when KIS API is unavailable.
    
    This allows the frontend to function even when KIS authentication fails.
    """
    mock_positions = [
        PositionResponse(
            symbol="AAPL",
            quantity=10,
            avg_price=180.50,
            current_price=185.20,
            market_value=1852.0,
            profit_loss=47.0,
            profit_loss_pct=2.60,
            daily_pnl=15.0,
            daily_return_pct=0.81
        ),
        PositionResponse(
            symbol="NVDA",
            quantity=5,
            avg_price=450.00,
            current_price=465.75,
            market_value=2328.75,
            profit_loss=78.75,
            profit_loss_pct=3.50,
            daily_pnl=25.50,
            daily_return_pct=1.11
        ),
        PositionResponse(
            symbol="GOOGL",
            quantity=8,
            avg_price=140.00,
            current_price=138.50,
            market_value=1108.0,
            profit_loss=-12.0,
            profit_loss_pct=-1.07,
            daily_pnl=-8.0,
            daily_return_pct=-0.72
        )
    ]
    
    total_invested = sum(p.avg_price * p.quantity for p in mock_positions)
    total_market_value = sum(p.market_value for p in mock_positions)
    cash = 5000.0
    total_value = total_market_value + cash
    total_pnl = sum(p.profit_loss for p in mock_positions)
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    daily_pnl = sum(p.daily_pnl for p in mock_positions)
    daily_return_pct = (daily_pnl / total_value * 100) if total_value > 0 else 0
    
    logger.info(f"📊 Returning mock portfolio: ${total_value:.2f} total, {len(mock_positions)} positions")
    
    return PortfolioResponse(
        total_value=total_value,
        cash=cash,
        invested=total_market_value,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        daily_pnl=daily_pnl,
        daily_return_pct=daily_return_pct,
        positions=mock_positions
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=PortfolioResponse)
async def get_portfolio():
    """
    Get portfolio overview

    Returns:
        Portfolio summary with positions
    """
    broker = get_kis_broker()

    if not broker:
        logger.error("❌ KIS Broker not available - check KIS credentials in .env")
        raise HTTPException(status_code=500, detail="KIS Broker not available. Check KIS credentials.")

    try:
        # Get account balance from KIS
        balance = broker.get_account_balance()

        if not balance:
            logger.error("❌ Failed to fetch KIS balance")
            raise HTTPException(status_code=500, detail="Failed to fetch account balance from KIS")

        # Calculate total value
        total_value = balance.get("total_value", 0) + balance.get("cash", 0)
        cash = balance.get("cash", 0)
        invested = balance.get("total_value", 0)

        # Calculate total P&L
        total_pnl = sum(p.get("profit_loss", 0) for p in balance.get("positions", []))
        total_pnl_pct = (total_pnl / invested * 100) if invested > 0 else 0

        # Daily P&L
        daily_pnl = balance.get("daily_pnl", 0)
        daily_return_pct = (daily_pnl / total_value * 100) if total_value > 0 else 0


        # Build positions list
        positions = []
        for pos in balance.get("positions", []):
            symbol = pos.get("symbol", "")
            current_price = pos.get("current_price", 0)
            quantity = pos.get("quantity", 0)
            avg_price = pos.get("avg_price", 0)
            
            # 배당 정보 조회 (KIS API → Yahoo Finance fallback)
            dividend_info = {"annual_dividend": 0.0, "dividend_yield": 0.0, "frequency": "Q", "next_ex_date": ""}
            if symbol:
                try:
                    # Try KIS API first
                    from backend.trading import overseas_stock as osf
                    dividend_data = osf.get_dividend_by_ticker(symbol, "US")
                    
                    if dividend_data and dividend_data.get("annual_dividend", 0) > 0:
                        annual_div = dividend_data.get("annual_dividend", 0)
                        # 배당 수익률 계산
                        div_yield = (annual_div / current_price * 100) if current_price > 0 else 0
                        
                        dividend_info = {
                            "annual_dividend": annual_div,
                            "dividend_yield": round(div_yield, 2),
                            "frequency": dividend_data.get("frequency", "Q"),
                            "next_ex_date": dividend_data.get("next_ex_date", "")
                        }
                        logger.info(f"📊 {symbol} 배당 정보 (KIS): ${annual_div:.2f}/year, {div_yield:.2f}% yield")
                    else:
                        # KIS API failed, try Yahoo Finance
                        logger.info(f"KIS API returned no dividend data for {symbol}, trying Yahoo Finance...")
                        from backend.data_sources import yahoo_finance as yf
                        yahoo_data = yf.get_dividend_info(symbol)
                        
                        if yahoo_data and yahoo_data.get("annual_dividend", 0) > 0:
                            dividend_info = {
                                "annual_dividend": yahoo_data.get("annual_dividend", 0),
                                "dividend_yield": yahoo_data.get("dividend_yield", 0),
                                "frequency": yahoo_data.get("frequency", "Q"),
                                "next_ex_date": yahoo_data.get("next_ex_date", "")
                            }
                            logger.info(f"✅ {symbol} 배당 정보 (Yahoo): ${dividend_info['annual_dividend']:.2f}/year, {dividend_info['dividend_yield']:.2f}% yield")
                        else:
                            logger.warning(f"No dividend data found for {symbol} from both KIS and Yahoo Finance")
                except Exception as e:
                    logger.warning(f"배당 정보 조회 실패 ({symbol}): {e}")
            
            positions.append(PositionResponse(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                current_price=current_price,
                market_value=pos.get("market_value", 0),  # Fixed: market_value from KIS broker
                profit_loss=pos.get("profit_loss", 0),
                profit_loss_pct=(pos.get("profit_loss", 0) / (avg_price * quantity) * 100) if avg_price > 0 and quantity > 0 else 0,
                daily_pnl=pos.get("daily_pnl", 0),
                daily_return_pct=pos.get("daily_return_pct", 0),
                # 배당 정보
                annual_dividend=dividend_info["annual_dividend"],
                dividend_yield=dividend_info["dividend_yield"],
                dividend_frequency=dividend_info["frequency"],
                next_dividend_date=dividend_info["next_ex_date"]
            ))

        logger.info(f"💼 Portfolio fetched: ${total_value:.2f} total, {len(positions)} positions")

        return PortfolioResponse(
            total_value=total_value,
            cash=cash,
            invested=invested,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            daily_pnl=daily_pnl,
            daily_return_pct=daily_return_pct,
            positions=positions
        )

    except Exception as e:
        logger.error(f"❌ Failed to fetch portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio: {str(e)}")


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    """
    Get current positions only

    Returns:
        List of positions
    """
    broker = get_kis_broker()

    if not broker:
        raise HTTPException(status_code=500, detail="KIS Broker not available")

    try:
        # Get account balance from KIS
        balance = broker.get_account_balance()

        if not balance:
            raise HTTPException(status_code=500, detail="Failed to fetch account balance")

        # Build positions list
        positions = []
        for pos in balance.get("positions", []):
            positions.append(PositionResponse(
                symbol=pos.get("symbol", ""),
                quantity=pos.get("quantity", 0),
                avg_price=pos.get("avg_price", 0),
                current_price=pos.get("current_price", 0),
                market_value=pos.get("eval_amt", 0),  # Fixed: eval_amt from KIS broker
                profit_loss=pos.get("profit_loss", 0),
                profit_loss_pct=(pos.get("profit_loss", 0) / (pos.get("avg_price", 0) * pos.get("quantity", 1)) * 100) if pos.get("avg_price", 0) > 0 else 0,
                daily_pnl=pos.get("daily_pnl", 0),
                daily_return_pct=pos.get("daily_return_pct", 0)
            ))

        logger.info(f"📊 Fetched {len(positions)} positions")

        return positions

    except Exception as e:
        logger.error(f"❌ Failed to fetch positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")
