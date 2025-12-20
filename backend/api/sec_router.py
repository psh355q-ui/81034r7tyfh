"""
SEC API Router

SEC 모니터링 관련 API 엔드포인트

Endpoints:
- GET  /api/sec/status          - 모니터 상태 확인
- GET  /api/sec/alerts          - 최근 알림 조회
- POST /api/sec/watchlist       - Watchlist 업데이트
- GET  /api/sec/insider/{ticker} - 내부자 거래 조회

Author: AI Trading System
Date: 2025-11-21
Phase: 14
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sec", tags=["SEC Monitor"])


# ============================================================================
# Request/Response Models
# ============================================================================

class WatchlistUpdate(BaseModel):
    """Watchlist 업데이트 요청"""
    tickers: List[str]


class SECAlertResponse(BaseModel):
    """SEC 알림 응답"""
    alert_type: str
    ticker: str
    form_type: str
    severity: str
    reason: str
    filing_url: str
    timestamp: str


class MonitorStatus(BaseModel):
    """모니터 상태"""
    is_running: bool
    watchlist: List[str]
    last_check: Optional[str]
    alerts_today: int
    total_filings_checked: int


# ============================================================================
# Global State (실제로는 Redis나 DB 사용)
# ============================================================================

class SECMonitorState:
    """SEC 모니터 전역 상태"""
    
    def __init__(self):
        self.is_running = False
        self.watchlist = []
        self.last_check = None
        self.alerts_cache = []  # 최근 100개 알림 캐시
        self.total_filings_checked = 0
        
    def add_alert(self, alert: dict):
        """알림 추가"""
        self.alerts_cache.append(alert)
        
        # 최근 100개만 유지
        if len(self.alerts_cache) > 100:
            self.alerts_cache = self.alerts_cache[-100:]
    
    def get_alerts_today(self) -> int:
        """오늘 발생한 알림 수"""
        today = datetime.now().date()
        count = sum(
            1 for alert in self.alerts_cache
            if datetime.fromisoformat(alert['timestamp']).date() == today
        )
        return count


# Global instance
monitor_state = SECMonitorState()


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=MonitorStatus)
async def get_monitor_status():
    """
    SEC 모니터 상태 조회
    
    Returns:
        현재 모니터 상태
    """
    return MonitorStatus(
        is_running=monitor_state.is_running,
        watchlist=monitor_state.watchlist,
        last_check=monitor_state.last_check.isoformat() if monitor_state.last_check else None,
        alerts_today=monitor_state.get_alerts_today(),
        total_filings_checked=monitor_state.total_filings_checked
    )


@router.post("/start")
async def start_monitor(background_tasks: BackgroundTasks):
    """
    SEC 모니터 시작
    
    백그라운드에서 모니터링 시작
    """
    if monitor_state.is_running:
        raise HTTPException(status_code=400, detail="Monitor is already running")
    
    # 백그라운드 태스크로 모니터 실행
    background_tasks.add_task(run_sec_monitor)
    
    monitor_state.is_running = True
    
    return {
        "status": "started",
        "message": "SEC monitor started in background",
        "watchlist": monitor_state.watchlist
    }


@router.post("/stop")
async def stop_monitor():
    """SEC 모니터 중지"""
    if not monitor_state.is_running:
        raise HTTPException(status_code=400, detail="Monitor is not running")
    
    monitor_state.is_running = False
    
    return {
        "status": "stopped",
        "message": "SEC monitor stopped"
    }


@router.post("/watchlist")
async def update_watchlist(request: WatchlistUpdate):
    """
    Watchlist 업데이트
    
    Args:
        request: 새로운 ticker 리스트
    """
    # 티커 검증
    tickers = [t.upper().strip() for t in request.tickers]
    
    if not tickers:
        raise HTTPException(status_code=400, detail="Watchlist cannot be empty")
    
    monitor_state.watchlist = tickers
    
    logger.info(f"Watchlist updated: {tickers}")
    
    return {
        "status": "updated",
        "watchlist": tickers,
        "count": len(tickers)
    }


@router.get("/alerts", response_model=List[SECAlertResponse])
async def get_recent_alerts(
    limit: int = 20,
    severity: Optional[str] = None,
    ticker: Optional[str] = None
):
    """
    최근 SEC 알림 조회
    
    Args:
        limit: 최대 반환 개수 (기본 20)
        severity: 심각도 필터 (INFO, WARNING, HIGH, CRITICAL)
        ticker: 특정 종목 필터
        
    Returns:
        알림 리스트
    """
    alerts = monitor_state.alerts_cache
    
    # 필터링
    if severity:
        alerts = [a for a in alerts if a['severity'] == severity.upper()]
    
    if ticker:
        ticker_upper = ticker.upper()
        alerts = [a for a in alerts if a['ticker'] == ticker_upper]
    
    # 최신순 정렬 및 제한
    alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    alerts = alerts[:limit]
    
    return [
        SECAlertResponse(
            alert_type=a['alert_type'],
            ticker=a['ticker'],
            form_type=a['form_type'],
            severity=a['severity'],
            reason=a['reason'],
            filing_url=a['filing']['filing_url'],
            timestamp=a['timestamp']
        )
        for a in alerts
    ]


@router.get("/insider/{ticker}")
async def get_insider_trades(ticker: str, days: int = 30):
    """
    특정 종목의 내부자 거래 조회
    
    Args:
        ticker: 종목 티커
        days: 조회 기간 (기본 30일)
        
    Returns:
        내부자 거래 리스트
    """
    ticker_upper = ticker.upper()
    
    # Form 4 알림만 필터링
    since = datetime.now() - timedelta(days=days)
    
    insider_alerts = [
        a for a in monitor_state.alerts_cache
        if a['ticker'] == ticker_upper
        and a['form_type'] == '4'
        and datetime.fromisoformat(a['timestamp']) >= since
    ]
    
    if not insider_alerts:
        return {
            "ticker": ticker_upper,
            "period_days": days,
            "trades": [],
            "message": "No insider trades found in the specified period"
        }
    
    return {
        "ticker": ticker_upper,
        "period_days": days,
        "trades": insider_alerts,
        "count": len(insider_alerts)
    }


@router.get("/test")
async def test_sec_api():
    """SEC API 연결 테스트"""
    from sec_monitor import load_company_tickers
    
    try:
        # SEC Company Tickers 다운로드 테스트
        cik_mapping = await load_company_tickers()
        
        return {
            "status": "success",
            "message": "SEC API connection successful",
            "companies_loaded": len(cik_mapping),
            "sample_companies": dict(list(cik_mapping.items())[:5])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SEC API connection failed: {str(e)}"
        )


# ============================================================================
# Background Task
# ============================================================================

async def run_sec_monitor():
    """
    백그라운드에서 실행되는 SEC 모니터
    """
    from sec_monitor import SECRealtimeMonitor
    from notifications.sec_alerts import send_sec_alert
    
    logger.info("Starting SEC monitor background task")
    
    # 모니터 생성
    monitor = SECRealtimeMonitor(monitor_state.watchlist)
    
    try:
        await monitor.start()
        
        # 모니터링 루프 (1분마다)
        async for alert in monitor.monitor_loop(interval=60):
            # 상태 업데이트
            monitor_state.last_check = datetime.now()
            monitor_state.total_filings_checked += 1
            
            # 알림 캐시에 추가
            alert_dict = alert.to_dict()
            monitor_state.add_alert(alert_dict)
            
            # Telegram/Slack 알림 전송
            await send_sec_alert(alert)
            
            # 중지 신호 확인
            if not monitor_state.is_running:
                logger.info("Stop signal received, exiting monitor loop")
                break
    
    except Exception as e:
        logger.error(f"Error in SEC monitor background task: {e}")
        monitor_state.is_running = False
    
    finally:
        await monitor.stop()
        logger.info("SEC monitor background task stopped")


# ============================================================================
# Initialization
# ============================================================================

def init_sec_monitor(watchlist: List[str]):
    """
    애플리케이션 시작 시 호출
    
    Args:
        watchlist: 초기 watchlist
    """
    monitor_state.watchlist = [t.upper() for t in watchlist]
    logger.info(f"SEC Monitor initialized with watchlist: {monitor_state.watchlist}")
