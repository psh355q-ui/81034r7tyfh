"""
Market Indicators Router

주요 시장 지표 조회 API
- S&P 500 (^GSPC)
- NASDAQ (^IXIC)
- VIX (^VIX)
- US 10Y Treasury (^TNX)
- DXY Dollar Index (DX-Y.NYB)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import yfinance as yf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

# 시장 지표 심볼 정의
MARKET_SYMBOLS = {
    "sp500": {"symbol": "^GSPC", "name": "S&P 500"},
    "nasdaq": {"symbol": "^IXIC", "name": "NASDAQ"},
    "vix": {"symbol": "^VIX", "name": "VIX"},
    "us10y": {"symbol": "^TNX", "name": "US 10Y"},
    "dxy": {"symbol": "DX-Y.NYB", "name": "DXY"},
    # Currency Exchange Rates (vs USD)
    "krw": {"symbol": "KRW=X", "name": "USD/KRW"},
    "jpy": {"symbol": "JPY=X", "name": "USD/JPY"},
    "eur": {"symbol": "EURUSD=X", "name": "EUR/USD"},
    "cny": {"symbol": "CNY=X", "name": "USD/CNY"}
}


def get_indicator_data(symbol: str) -> Dict[str, Any]:
    """
    단일 지표 데이터 조회
    
    Args:
        symbol: Yahoo Finance 심볼 (예: ^GSPC)
        
    Returns:
        현재가, 변동, 변동률 데이터
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        
        if hist.empty or len(hist) < 2:
            logger.warning(f"No data for {symbol}")
            return {
                "price": 0.0,
                "change": 0.0,
                "change_pct": 0.0,
                "error": "No data available"
            }
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100 if prev_price != 0 else 0.0
        
        return {
            "price": round(float(current_price), 2),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return {
            "price": 0.0,
            "change": 0.0,
            "change_pct": 0.0,
            "error": str(e)
        }


@router.get("/indicators")
async def get_market_indicators():
    """
    주요 시장 지표 조회
    
    Returns:
        S&P500, NASDAQ, VIX, US10Y, DXY, KRW, JPY, EUR, CNY 데이터
    """
    try:
        indicators = {}
        
        for key, info in MARKET_SYMBOLS.items():
            symbol = info["symbol"]
            name = info["name"]
            
            data = get_indicator_data(symbol)
            
            indicators[key] = {
                "symbol": symbol,
                "name": name,
                **data
            }
            
            # US10Y와 환율은 basis points/pips 추가
            if key in ["us10y", "krw", "jpy", "eur", "cny"]:
                indicators[key]["change_bp"] = round(data["change"] * 100, 1)
        
        return {
            "success": True,
            "data": indicators,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch market indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators/{indicator_name}")
async def get_single_indicator(indicator_name: str):
    """
    단일 지표 조회
    
    Args:
        indicator_name: sp500, nasdaq, vix, us10y, dxy 중 하나
        
    Returns:
        해당 지표 데이터
    """
    if indicator_name not in MARKET_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Indicator '{indicator_name}' not found. Available: {list(MARKET_SYMBOLS.keys())}"
        )
    
    try:
        info = MARKET_SYMBOLS[indicator_name]
        data = get_indicator_data(info["symbol"])
        
        result = {
            "symbol": info["symbol"],
            "name": info["name"],
            **data
        }
        
        if indicator_name == "us10y":
            result["change_bp"] = round(data["change"] * 100, 1)
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch {indicator_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
