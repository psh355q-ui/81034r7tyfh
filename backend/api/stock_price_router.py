"""
Stock Price Management API Router

Endpoints:
- GET /api/stock-prices/list - 저장된 종목 목록
- GET /api/stock-prices/{ticker} - 특정 종목 히스토리
- POST /api/stock-prices/sync - 종목 동기화
- GET /api/stock-prices/sectors - 섹터별 현황 (상승/하락 Top 3)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from backend.core.database import get_db
from backend.core.models.stock_price_models import StockPrice, PriceSyncStatus
from backend.data.sp500_universe import (
    SP500_SECTORS, SP500_TICKERS, TICKER_TO_SECTOR,
    get_sector, get_all_sectors, TOTAL_STOCKS
)
from backend.data.stock_price_storage import StockPriceStorage
from backend.ai.skills.common.logging_decorator import log_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock-prices", tags=["Stock Prices"])


@router.get("/list")
@log_endpoint("stock_prices", "system")
async def get_stock_list(
    sector: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    저장된 종목 목록 조회
    
    Returns:
        - 동기화된 종목 리스트
        - 각 종목의 마지막 동기화 날짜
    """
    query = select(PriceSyncStatus).order_by(PriceSyncStatus.ticker)
    
    if sector:
        sector_tickers = SP500_SECTORS.get(sector, [])
        query = query.where(PriceSyncStatus.ticker.in_(sector_tickers))
    
    result = await db.execute(query)
    synced = result.scalars().all()
    
    stocks = []
    for s in synced:
        stocks.append({
            "ticker": s.ticker,
            "sector": get_sector(s.ticker),
            "last_sync_date": s.last_sync_date.isoformat() if s.last_sync_date else None,
            "last_price_date": s.last_price_date.isoformat() if s.last_price_date else None,
            "total_rows": s.total_rows,
        })
    
    return {
        "success": True,
        "count": len(stocks),
        "total_sp500": TOTAL_STOCKS,
        "stocks": stocks,
    }


@router.get("/stats")
@log_endpoint("stock_prices", "system")
async def get_stock_stats(db: AsyncSession = Depends(get_db)):
    """
    주가 DB 통계
    """
    # 총 row 수
    total_query = select(func.count()).select_from(StockPrice)
    total_result = await db.execute(total_query)
    total_rows = total_result.scalar() or 0
    
    # 동기화된 종목 수
    synced_query = select(func.count()).select_from(PriceSyncStatus)
    synced_result = await db.execute(synced_query)
    synced_count = synced_result.scalar() or 0
    
    # 섹터별 동기화 현황
    sector_stats = {}
    for sector, tickers in SP500_SECTORS.items():
        synced_in_sector = select(func.count()).select_from(PriceSyncStatus).where(
            PriceSyncStatus.ticker.in_(tickers)
        )
        result = await db.execute(synced_in_sector)
        count = result.scalar() or 0
        sector_stats[sector] = {
            "total": len(tickers),
            "synced": count,
            "percent": round(count / len(tickers) * 100, 1) if tickers else 0
        }
    
    return {
        "success": True,
        "total_rows": total_rows,
        "synced_stocks": synced_count,
        "total_sp500": TOTAL_STOCKS,
        "coverage_percent": round(synced_count / TOTAL_STOCKS * 100, 1),
        "sectors": sector_stats,
    }


@router.get("/sectors/top-movers")
@log_endpoint("stock_prices", "system")
async def get_sector_top_movers(
    db: AsyncSession = Depends(get_db)
):
    """
    섹터별 상승/하락 Top 3 종목
    
    Daily Briefing에서 사용
    """
    result = {}
    
    for sector, tickers in SP500_SECTORS.items():
        # 최근 2일 데이터 조회
        yesterday = date.today() - timedelta(days=1)
        day_before = date.today() - timedelta(days=2)
        
        query = select(StockPrice).where(
            StockPrice.ticker.in_(tickers),
            StockPrice.time >= datetime.combine(day_before, datetime.min.time()),
        ).order_by(StockPrice.ticker, StockPrice.time)
        
        prices_result = await db.execute(query)
        prices = prices_result.scalars().all()
        
        # 종목별 변동률 계산
        changes = {}
        ticker_prices = {}
        
        for p in prices:
            if p.ticker not in ticker_prices:
                ticker_prices[p.ticker] = []
            ticker_prices[p.ticker].append(float(p.close))
        
        for ticker, price_list in ticker_prices.items():
            if len(price_list) >= 2:
                old_price = price_list[-2]
                new_price = price_list[-1]
                if old_price > 0:
                    change_pct = (new_price - old_price) / old_price * 100
                    changes[ticker] = {
                        "ticker": ticker,
                        "price": new_price,
                        "change_pct": round(change_pct, 2),
                    }
        
        # Top 3 상승/하락
        sorted_changes = sorted(changes.values(), key=lambda x: x["change_pct"], reverse=True)
        
        result[sector] = {
            "gainers": sorted_changes[:3] if len(sorted_changes) >= 3 else sorted_changes,
            "losers": sorted_changes[-3:][::-1] if len(sorted_changes) >= 3 else [],
        }
    
    return {
        "success": True,
        "date": date.today().isoformat(),
        "sectors": result,
    }


@router.get("/{ticker}")
@log_endpoint("stock_prices", "system")
async def get_stock_prices(
    ticker: str,
    days: int = Query(default=30, ge=1, le=365*5),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 종목 가격 히스토리 조회
    """
    storage = StockPriceStorage(db)
    
    try:
        df = await storage.get_stock_prices(ticker, days=days)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"{ticker} 데이터 없음. 먼저 동기화 필요.")
        
        records = df.reset_index().to_dict(orient="records")
        
        return {
            "success": True,
            "ticker": ticker,
            "sector": get_sector(ticker),
            "count": len(records),
            "data": records,
        }
    except Exception as e:
        logger.error(f"Get stock prices error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
@log_endpoint("stock_prices", "system")
async def sync_stock_prices(
    tickers: Optional[List[str]] = None,
    sector: Optional[str] = None,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    주가 데이터 동기화
    
    Args:
        tickers: 동기화할 종목 리스트 (없으면 전체)
        sector: 동기화할 섹터
        force: 강제 재다운로드
    """
    storage = StockPriceStorage(db)
    
    # 대상 종목 결정
    if tickers:
        target_tickers = tickers
    elif sector:
        target_tickers = SP500_SECTORS.get(sector, [])
    else:
        target_tickers = SP500_TICKERS[:10]  # 기본값: 상위 10개만
    
    results = {
        "success": True,
        "requested": len(target_tickers),
        "completed": 0,
        "errors": 0,
        "details": [],
    }
    
    for ticker in target_tickers:
        try:
            # 이미 데이터가 있으면 incremental update
            existing = await storage._check_existing_data(ticker)
            
            if existing and not force:
                stats = await storage.update_stock_prices_incremental(ticker)
            else:
                stats = await storage.backfill_stock_prices(ticker, years=5, force=force)
            
            results["completed"] += 1
            results["details"].append({
                "ticker": ticker,
                "status": "success",
                **stats
            })
        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "ticker": ticker,
                "status": "error",
                "error": str(e)
            })
    
    return results


@router.get("/quotes")
@log_endpoint("stock_prices", "system")
async def get_realtime_quotes(
    tickers: str = Query(..., description="Comma separated list of tickers, e.g. AAPL,MSFT,TSLA"),
):
    """
    실시간(지연) 시세 조회 (Yahoo Finance)
    """
    try:
        import yfinance as yf
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        
        if not ticker_list:
            return {"success": False, "data": []}
            
        # yfinance allows fetching multiple tickers at once
        data = yf.Tickers(" ".join(ticker_list))
        
        results = []
        for ticker in ticker_list:
            try:
                info = data.tickers[ticker].fast_info
                # fast_info provides faster access to latest price
                price = info.last_price
                prev_close = info.previous_close
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0.0
                volume = info.last_volume

                results.append({
                    "ticker": ticker,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": volume,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {ticker}: {e}")
                # Fallback to simple None or error indication
                results.append({
                    "ticker": ticker,
                    "error": "Data unavailable"
                })
                
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Quote fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors/performance")
@log_endpoint("stock_prices", "system")
async def get_sector_performance_realtime():
    """
    실시간 섹터 ETF 성과 조회 (Yahoo Finance)
    Uses Sector ETFs as proxies:
    - XLK: Technology
    - XLF: Financials
    - XLV: Healthcare
    - XLY: Consumer Disc
    - XLP: Consumer Staples
    - XLE: Energy
    - XLI: Industrials
    - XLB: Materials
    - XLU: Utilities
    - XLRE: Real Estate
    - XLC: Communication
    """
    SECTOR_ETFS = {
        "Technology": "XLK",
        "Financials": "XLF",
        "Healthcare": "XLV",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication": "XLC"
    }
    
    try:
        import yfinance as yf
        tickers = list(SECTOR_ETFS.values())
        data = yf.Tickers(" ".join(tickers))
        
        performance = []
        
        for sector, ticker in SECTOR_ETFS.items():
            try:
                info = data.tickers[ticker].fast_info
                price = info.last_price
                prev_close = info.previous_close
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
                
                performance.append({
                    "name": sector,
                    "ticker": ticker,
                    "change_pct": round(change_pct, 2),
                    "price": round(price, 2)
                })
            except Exception as e:
                logger.warning(f"Failed to fetch sector {sector} ({ticker}): {e}")
        
        # Sort by performance
        performance.sort(key=lambda x: x["change_pct"], reverse=True)
        
        return {
            "success": True,
            "data": performance,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Sector performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe/info")
@log_endpoint("stock_prices", "system")
async def get_universe_info():
    """
    S&P500 유니버스 정보
    """
    return {
        "success": True,
        "total_stocks": TOTAL_STOCKS,
        "sectors": get_all_sectors(),
        "sector_counts": {
            sector: len(tickers) for sector, tickers in SP500_SECTORS.items()
        },
    }
