"""
Chart Data Router - OHLC 데이터 제공 API

Phase: Z.AI MCP Integration
Date: 2026-01-18

Features:
    - 1시간봉, 4시간봉, 일봉, 주봉 데이터 제공
    - yfinance 기반 실시간 데이터
    - 캐싱으로 API 호출 최소화
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chart", tags=["Chart Data"])


# ============================================================================
# Schemas
# ============================================================================

class OHLCData(BaseModel):
    """OHLC 캔들스틱 데이터"""
    time: str  # ISO date string
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartDataResponse(BaseModel):
    """차트 데이터 응답"""
    symbol: str
    timeframe: str
    data: List[OHLCData]
    last_updated: str


# ============================================================================
# In-Memory Cache
# ============================================================================

_chart_cache: dict = {}
_cache_ttl = {
    '1h': 300,    # 5분
    '4h': 600,    # 10분
    '1d': 3600,   # 1시간
    '1w': 7200,   # 2시간
}


def get_cache_key(symbol: str, timeframe: str) -> str:
    return f"{symbol.upper()}:{timeframe}"


def is_cache_valid(cache_key: str, ttl_seconds: int) -> bool:
    if cache_key not in _chart_cache:
        return False
    cached_time = _chart_cache[cache_key].get('cached_at')
    if not cached_time:
        return False
    return (datetime.now() - cached_time).total_seconds() < ttl_seconds


# ============================================================================
# Helper Functions
# ============================================================================

def get_yfinance_interval(timeframe: str) -> str:
    """Convert our timeframe to yfinance interval"""
    mapping = {
        '1h': '1h',
        '4h': '1h',  # yfinance doesn't support 4h, we'll resample
        '1d': '1d',
        '1w': '1wk',
    }
    return mapping.get(timeframe, '1h')


def get_period_for_timeframe(timeframe: str) -> str:
    """Get appropriate period for each timeframe"""
    mapping = {
        '1h': '7d',    # 1주일 데이터
        '4h': '30d',   # 1달 데이터
        '1d': '6mo',   # 6개월 데이터
        '1w': '2y',    # 2년 데이터
    }
    return mapping.get(timeframe, '7d')


def resample_to_4h(df):
    """Resample 1h data to 4h"""
    import pandas as pd
    
    df_resampled = df.resample('4h').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum',
    }).dropna()
    
    return df_resampled


def fetch_ohlc_data(symbol: str, timeframe: str) -> List[OHLCData]:
    """
    yfinance로 OHLC 데이터 가져오기
    """
    try:
        ticker = yf.Ticker(symbol)
        interval = get_yfinance_interval(timeframe)
        period = get_period_for_timeframe(timeframe)
        
        # Fetch data
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data found for {symbol}")
            return []
        
        # Resample if needed (4h)
        if timeframe == '4h':
            df = resample_to_4h(df)
        
        # Convert to OHLCData list
        result = []
        for idx, row in df.iterrows():
            # Format time based on timeframe
            if timeframe in ['1h', '4h']:
                time_str = idx.strftime('%Y-%m-%d %H:%M')
            else:
                time_str = idx.strftime('%Y-%m-%d')
            
            result.append(OHLCData(
                time=time_str,
                open=round(row['Open'], 2),
                high=round(row['High'], 2),
                low=round(row['Low'], 2),
                close=round(row['Close'], 2),
                volume=int(row['Volume']),
            ))
        
        logger.info(f"Fetched {len(result)} candles for {symbol} ({timeframe})")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching OHLC data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/ohlc/{symbol}", response_model=ChartDataResponse)
async def get_ohlc_data(
    symbol: str,
    timeframe: str = Query("1h", pattern="^(1h|4h|1d|1w)$", description="Timeframe: 1h, 4h, 1d, 1w"),
    force_refresh: bool = Query(False, description="Force cache refresh"),
):
    """
    OHLC 캔들스틱 데이터 조회
    
    Args:
        symbol: 주식 심볼 (예: AAPL, NVDA)
        timeframe: 시간 프레임 (1h, 4h, 1d, 1w)
        force_refresh: 캐시 무시하고 새로 조회
    
    Returns:
        ChartDataResponse: OHLC 데이터 배열
    """
    symbol = symbol.upper()
    cache_key = get_cache_key(symbol, timeframe)
    ttl = _cache_ttl.get(timeframe, 300)
    
    # Check cache
    if not force_refresh and is_cache_valid(cache_key, ttl):
        cached = _chart_cache[cache_key]
        logger.debug(f"Cache hit for {cache_key}")
        return ChartDataResponse(
            symbol=symbol,
            timeframe=timeframe,
            data=cached['data'],
            last_updated=cached['cached_at'].isoformat(),
        )
    
    # Fetch fresh data
    data = fetch_ohlc_data(symbol, timeframe)
    
    # Update cache
    _chart_cache[cache_key] = {
        'data': data,
        'cached_at': datetime.now(),
    }
    
    return ChartDataResponse(
        symbol=symbol,
        timeframe=timeframe,
        data=data,
        last_updated=datetime.now().isoformat(),
    )


@router.get("/multi/{symbols}", response_model=dict)
async def get_multi_ohlc_data(
    symbols: str,
    timeframe: str = Query("1h", pattern="^(1h|4h|1d|1w)$"),
):
    """
    여러 심볼의 OHLC 데이터 한번에 조회
    
    Args:
        symbols: 쉼표로 구분된 심볼 목록 (예: AAPL,NVDA,MSFT)
        timeframe: 시간 프레임
    
    Returns:
        dict: { symbol: ChartDataResponse }
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    result = {}
    
    for symbol in symbol_list[:10]:  # Max 10 symbols
        try:
            data = await get_ohlc_data(symbol=symbol, timeframe=timeframe)
            result[symbol] = data
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            result[symbol] = {"error": str(e)}
    
    return result


@router.get("/latest/{symbol}")
async def get_latest_price(symbol: str):
    """
    최신 가격 정보 조회 (캐싱 없음)
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.fast_info
        
        return {
            "symbol": symbol.upper(),
            "price": round(info['lastPrice'], 2) if info.get('lastPrice') else None,
            "change": round(info.get('regularMarketChange', 0), 2),
            "change_percent": round(info.get('regularMarketChangePercent', 0), 2),
            "volume": info.get('regularMarketVolume', 0),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get latest price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_chart_cache():
    """
    차트 캐시 초기화 (디버깅용)
    """
    global _chart_cache
    count = len(_chart_cache)
    _chart_cache = {}
    return {"message": f"Cleared {count} cached items"}
