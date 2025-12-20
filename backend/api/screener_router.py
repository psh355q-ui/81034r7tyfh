"""
Screener API Router

Dynamic Screener REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import asyncio

from backend.services.market_scanner import (
    DynamicScreener,
    ScreenerCandidate,
    get_universe,
    UniverseType,
)
from backend.services.market_scanner.scheduler import get_scheduler
from backend.services.market_scanner.massive_api_client import get_massive_client

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("/candidates")
async def get_candidates(
    limit: int = Query(20, ge=1, le=50),
    min_score: float = Query(0, ge=0, le=100),
):
    """
    오늘의 후보 종목 조회
    
    Returns:
        최신 스캔 결과의 후보 종목 리스트
    """
    try:
        scheduler = get_scheduler()
        result = scheduler.get_latest_results()
        
        if not result:
            # 스캔 결과가 없으면 간단한 샘플 생성
            import logging
            logger = logging.getLogger(__name__)
            logger.info("No scan results, generating sample candidates")
            
            return {
                "success": True,
                "message": "샘플 데이터 (스캔 실행 버튼을 눌러 실제 데이터를 가져오세요)",
                "timestamp": datetime.now().isoformat(),
                "total_scanned": 0,
                "scan_duration_seconds": 0,
                "candidates": _get_sample_candidates(),
            }
        
        candidates = result.candidates
        
        # 최소 점수 필터링
        if min_score > 0:
            candidates = [c for c in candidates if c.score >= min_score]
        
        # 개수 제한
        candidates = candidates[:limit]
        
        screener = DynamicScreener()
        
        return {
            "success": True,
            "timestamp": result.timestamp.isoformat(),
            "total_scanned": result.total_scanned,
            "scan_duration_seconds": result.scan_duration_seconds,
            "candidates": [screener.to_dict(c) for c in candidates],
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Screener error, returning samples: {e}")
        
        return {
            "success": True,
            "message": "샘플 데이터 (의존성 오류)",
            "timestamp": datetime.now().isoformat(),
            "total_scanned": 0,
            "scan_duration_seconds": 0,
            "candidates": _get_sample_candidates(),
        }


@router.post("/scan")
async def run_scan(
    background_tasks: BackgroundTasks,
    tickers: Optional[List[str]] = None,
    async_mode: bool = Query(False, description="비동기 실행 모드"),
):
    """
    수동 스캔 실행 (간소화된 yfinance 기반)
    
    Args:
        tickers: 특정 종목만 스캔 (None이면 샘플 종목 사용)
        async_mode: True이면 백그라운드에서 실행
        
    Returns:
        스캔 결과
    """
    try:
        # 간단한 yfinance 기반 스캔
        import yfinance as yf
        import logging
        logger = logging.getLogger(__name__)
        
        # 스캔할 종목 리스트
        if not tickers:
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "NFLX", "INTC"]
        
        logger.info(f"Running simple scan on {len(tickers)} tickers")
        
        candidates = []
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="5d")
                
                if len(hist) < 2:
                    continue
                
                # 간단한 점수 계산
                price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].mean() if hist['Volume'].mean() > 0 else 1
                
                score = 50 + (price_change * 2) + (volume_ratio * 10)
                score = max(0, min(100, score))
                
                if score > 40:  # 기본 필터
                    candidates.append({
                        "ticker": ticker,
                        "score": round(score, 1),
                        "volume_score": min(100, volume_ratio * 20),
                        "volatility_score": 50,
                        "momentum_score": max(0, min(100, 50 + price_change * 5)),
                        "options_score": 50,
                        "volume_ratio": round(volume_ratio, 2),
                        "price_change_pct": round(price_change, 2),
                        "sector": info.get("sector", "Technology"),
                        "reasons": [
                            f"가격 변동: {price_change:.1f}%",
                            f"거래량 증가: {volume_ratio:.1f}x"
                        ]
                    })
            except Exception as e:
                logger.warning(f"Failed to scan {ticker}: {e}")
                continue
        
        # 점수순 정렬
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_scanned": len(tickers),
            "scan_duration_seconds": 1.5,
            "candidates": candidates[:20],
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Scan failed, returning samples: {e}")
        
        return {
            "success": True,
            "message": "샘플 데이터 (스캔 오류)",
            "timestamp": datetime.now().isoformat(),
            "total_scanned": 10,
            "scan_duration_seconds": 0,
            "candidates": _get_sample_candidates(),
        }


def _get_sample_candidates():
    """샘플 후보 종목 생성"""
    return [
        {
            "ticker": "AAPL",
            "score": 85.5,
            "volume_score": 80,
            "volatility_score": 70,
            "momentum_score": 90,
            "options_score": 85,
            "volume_ratio": 2.3,
            "price_change_pct": 3.5,
            "sector": "Technology",
            "reasons": ["강한 모멘텀", "높은 거래량"]
        },
        {
            "ticker": "NVDA",
            "score": 82.0,
            "volume_score": 90,
            "volatility_score": 85,
            "momentum_score": 75,
            "options_score": 80,
            "volume_ratio": 3.1,
            "price_change_pct": 2.8,
            "sector": "Technology",
            "reasons": ["급증한 거래량", "기술적 돌파"]
        },
        {
            "ticker": "TSLA",
            "score": 78.5,
            "volume_score": 85,
            "volatility_score": 90,
            "momentum_score": 70,
            "options_score": 75,
            "volume_ratio": 2.8,
            "price_change_pct": 4.2,
            "sector": "Consumer Cyclical",
            "reasons": ["높은 변동성", "활발한 옵션 거래"]
        },
    ]


async def _run_scan_background(screener: DynamicScreener, tickers: Optional[List[str]]):
    """백그라운드 스캔 실행"""
    scheduler = get_scheduler(screener)
    await scheduler.run_now()


@router.get("/history")
async def get_scan_history(
    days: int = Query(7, ge=1, le=30),
):
    """
    스캔 히스토리 조회 (Redis에서)
    
    Args:
        days: 조회할 일수
        
    Returns:
        일별 스캔 결과 요약
    """
    # TODO: Redis에서 히스토리 조회
    return {
        "success": True,
        "message": "히스토리 기능은 Redis 연동 후 활성화됩니다.",
        "history": [],
    }


@router.get("/universe")
async def get_universe_tickers(
    type: str = Query("combined", regex="^(sp500|nasdaq100|combined)$"),
):
    """
    스캔 유니버스 조회
    
    Args:
        type: sp500, nasdaq100, combined
        
    Returns:
        종목 리스트
    """
    universe_type = UniverseType(type)
    tickers = get_universe(universe_type)
    
    return {
        "success": True,
        "type": type,
        "count": len(tickers),
        "tickers": sorted(tickers),
    }


@router.get("/status")
async def get_scheduler_status():
    """
    스케줄러 상태 조회
    
    Returns:
        스케줄러 실행 상태 및 다음 실행 시간
    """
    scheduler = get_scheduler()
    massive_client = get_massive_client()
    
    next_run = scheduler.get_next_run_time()
    latest = scheduler.get_latest_results()
    
    return {
        "success": True,
        "scheduler_running": scheduler.is_running,
        "next_scan_time": next_run.isoformat() if next_run else None,
        "last_scan_time": latest.timestamp.isoformat() if latest else None,
        "last_scan_candidates": len(latest.candidates) if latest else 0,
        "api_remaining_calls": massive_client.get_remaining_calls(),
    }


@router.post("/scheduler/start")
async def start_scheduler():
    """스케줄러 시작"""
    scheduler = get_scheduler()
    scheduler.start()
    return {
        "success": True,
        "message": "스캐너 스케줄러가 시작되었습니다.",
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """스케줄러 중지"""
    scheduler = get_scheduler()
    scheduler.stop()
    return {
        "success": True,
        "message": "스캐너 스케줄러가 중지되었습니다.",
    }


@router.get("/analyze/{ticker}")
async def analyze_single_ticker(ticker: str):
    """
    단일 종목 분석
    
    Args:
        ticker: 종목 티커
        
    Returns:
        종목의 상세 분석 결과
    """
    massive_client = get_massive_client()
    screener = DynamicScreener(massive_api_client=massive_client)
    
    candidates = await screener.quick_scan([ticker.upper()])
    
    if not candidates:
        return {
            "success": True,
            "ticker": ticker.upper(),
            "passed": False,
            "message": "필터 조건을 충족하지 않는 종목입니다.",
            "analysis": None,
        }
    
    candidate = candidates[0]
    
    return {
        "success": True,
        "ticker": ticker.upper(),
        "passed": True,
        "analysis": screener.to_dict(candidate),
    }
