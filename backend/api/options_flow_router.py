"""
Options Flow API Router

옵션 흐름 데이터 API 엔드포인트

Endpoints:
- GET /api/options/flow/{ticker}       - 옵션 흐름 조회
- GET /api/options/unusual             - Unusual Activity 조회
- GET /api/options/pcr/{ticker}        - Put/Call Ratio 분석
- POST /api/options/alerts/start       - 알림 모니터링 시작
- GET /api/options/screener            - PCR 기반 스크리너

Author: AI Trading System
Date: 2025-11-21
Phase: 15 Task 1
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/options", tags=["Options Flow"])


# ============================================================================
# Request/Response Models
# ============================================================================

class OptionsFlowResponse(BaseModel):
    """옵션 흐름 응답"""
    ticker: str
    current_price: float
    timestamp: str
    total_call_volume: int
    total_put_volume: int
    put_call_ratio_volume: float
    put_call_ratio_oi: float
    unusual_calls_count: int
    unusual_puts_count: int


class PCRAnalysisResponse(BaseModel):
    """PCR 분석 응답"""
    ticker: str
    pcr_volume: float
    pcr_oi: float
    volume_sentiment: str
    volume_interpretation: str
    oi_sentiment: str
    overall_sentiment: str
    recommendation: str


class UnusualActivityResponse(BaseModel):
    """Unusual Activity 응답"""
    ticker: str
    contract_symbol: str
    option_type: str
    strike: float
    expiration: str
    volume: int
    open_interest: int
    moneyness: str


class WatchlistRequest(BaseModel):
    """Watchlist 요청"""
    tickers: List[str]


# ============================================================================
# Global State
# ============================================================================

class OptionsMonitorState:
    """옵션 모니터 상태"""
    
    def __init__(self):
        self.is_running = False
        self.watchlist = []
        self.alerts = []  # 최근 알림
        self.last_check = None
    
    def add_alert(self, alert: dict):
        """알림 추가"""
        self.alerts.append(alert)
        
        # 최근 100개만 유지
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]


monitor_state = OptionsMonitorState()


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/flow/{ticker}", response_model=OptionsFlowResponse)
async def get_options_flow(ticker: str, force_refresh: bool = False):
    """
    옵션 흐름 데이터 조회
    
    Args:
        ticker: 종목 티커
        force_refresh: 캐시 무시
        
    Returns:
        옵션 흐름 데이터
    """
    from options_flow_tracker import OptionsDataFetcher
    
    fetcher = OptionsDataFetcher()
    
    try:
        flow = fetcher.get_options_flow(ticker.upper(), use_cache=not force_refresh)
        
        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"No options data available for {ticker.upper()}"
            )
        
        flow_dict = flow.to_dict()
        
        return OptionsFlowResponse(**flow_dict)
        
    except Exception as e:
        logger.error(f"Error fetching options flow for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pcr/{ticker}", response_model=PCRAnalysisResponse)
async def analyze_put_call_ratio(ticker: str):
    """
    Put/Call Ratio 분석
    
    Args:
        ticker: 종목 티커
        
    Returns:
        PCR 분석 결과
    """
    from options_flow_tracker import OptionsDataFetcher, PutCallRatioAnalyzer
    
    fetcher = OptionsDataFetcher()
    analyzer = PutCallRatioAnalyzer()
    
    try:
        flow = fetcher.get_options_flow(ticker.upper())
        
        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"No options data available for {ticker.upper()}"
            )
        
        # PCR 분석
        interpretation = analyzer.interpret_pcr(
            flow.put_call_ratio_volume,
            flow.put_call_ratio_oi
        )
        
        return PCRAnalysisResponse(
            ticker=flow.ticker,
            **interpretation
        )
        
    except Exception as e:
        logger.error(f"Error analyzing PCR for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unusual/{ticker}", response_model=List[UnusualActivityResponse])
async def get_unusual_activity(ticker: str):
    """
    Unusual Options Activity 조회
    
    Args:
        ticker: 종목 티커
        
    Returns:
        Unusual 계약 리스트
    """
    from options_flow_tracker import OptionsDataFetcher
    
    fetcher = OptionsDataFetcher()
    
    try:
        flow = fetcher.get_options_flow(ticker.upper())
        
        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"No options data available for {ticker.upper()}"
            )
        
        # Unusual 계약 합치기
        unusual = []
        
        for contract in flow.unusual_calls + flow.unusual_puts:
            unusual.append(UnusualActivityResponse(
                ticker=contract.ticker,
                contract_symbol=contract.contract_symbol,
                option_type=contract.option_type,
                strike=contract.strike,
                expiration=contract.expiration,
                volume=contract.volume,
                open_interest=contract.open_interest,
                moneyness=contract.moneyness
            ))
        
        # 거래량 순 정렬
        unusual.sort(key=lambda x: x.volume, reverse=True)
        
        return unusual
        
    except Exception as e:
        logger.error(f"Error fetching unusual activity for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screener")
async def options_screener(
    min_pcr: Optional[float] = None,
    max_pcr: Optional[float] = None,
    sentiment: Optional[str] = None
):
    """
    PCR 기반 종목 스크리너
    
    Args:
        min_pcr: 최소 PCR
        max_pcr: 최대 PCR
        sentiment: 감정 필터 (BULLISH, BEARISH, NEUTRAL)
        
    Returns:
        필터링된 종목 리스트
    """
    from options_flow_tracker import OptionsDataFetcher, PutCallRatioAnalyzer
    
    # Watchlist에서 스크리닝
    tickers = monitor_state.watchlist if monitor_state.watchlist else ["NVDA", "TSLA", "AAPL", "GOOGL", "MSFT"]
    
    fetcher = OptionsDataFetcher()
    analyzer = PutCallRatioAnalyzer()
    
    results = []
    
    for ticker in tickers:
        try:
            flow = fetcher.get_options_flow(ticker)
            
            if not flow:
                continue
            
            pcr = flow.put_call_ratio_volume
            
            # PCR 필터
            if min_pcr and pcr < min_pcr:
                continue
            if max_pcr and pcr > max_pcr:
                continue
            
            # 분석
            interpretation = analyzer.interpret_pcr(
                flow.put_call_ratio_volume,
                flow.put_call_ratio_oi
            )
            
            # Sentiment 필터
            if sentiment:
                if sentiment.upper() not in interpretation['overall_sentiment']:
                    continue
            
            results.append({
                'ticker': ticker,
                'current_price': flow.current_price,
                'pcr_volume': pcr,
                'pcr_oi': flow.put_call_ratio_oi,
                'sentiment': interpretation['overall_sentiment'],
                'recommendation': interpretation['recommendation'],
                'unusual_activity': len(flow.unusual_calls) + len(flow.unusual_puts)
            })
            
        except Exception as e:
            logger.error(f"Error screening {ticker}: {e}")
            continue
    
    # PCR 순 정렬 (높은 것부터 = 약세)
    results.sort(key=lambda x: x['pcr_volume'], reverse=True)
    
    return {
        'screener_results': results,
        'count': len(results),
        'filters': {
            'min_pcr': min_pcr,
            'max_pcr': max_pcr,
            'sentiment': sentiment
        }
    }


@router.post("/alerts/start")
async def start_options_alerts(
    request: WatchlistRequest,
    background_tasks: BackgroundTasks
):
    """
    옵션 알림 모니터링 시작
    
    Args:
        request: 모니터링할 티커 리스트
        
    Returns:
        시작 확인
    """
    tickers = [t.upper() for t in request.tickers]
    
    if not tickers:
        raise HTTPException(status_code=400, detail="Ticker list is empty")
    
    monitor_state.watchlist = tickers
    monitor_state.is_running = True
    
    # 백그라운드 모니터링 시작
    background_tasks.add_task(run_options_monitor, tickers)
    
    return {
        'status': 'started',
        'message': f'Options flow monitoring started for {len(tickers)} tickers',
        'watchlist': tickers
    }


@router.post("/alerts/stop")
async def stop_options_alerts():
    """옵션 알림 모니터링 중지"""
    monitor_state.is_running = False
    
    return {
        'status': 'stopped',
        'message': 'Options flow monitoring stopped'
    }


@router.get("/alerts")
async def get_options_alerts(limit: int = 20):
    """
    최근 옵션 알림 조회
    
    Args:
        limit: 최대 반환 개수
        
    Returns:
        알림 리스트
    """
    alerts = monitor_state.alerts[-limit:]
    alerts.reverse()  # 최신순
    
    return {
        'alerts': alerts,
        'count': len(alerts)
    }


# ============================================================================
# Background Monitoring
# ============================================================================

async def run_options_monitor(tickers: List[str]):
    """
    백그라운드 옵션 모니터링
    
    체크 항목:
    1. PCR > 2.0 → 강한 약세 신호
    2. PCR < 0.5 → 강한 강세 신호
    3. Unusual Activity 급증
    """
    from options_flow_tracker import OptionsDataFetcher, PutCallRatioAnalyzer
    
    fetcher = OptionsDataFetcher()
    analyzer = PutCallRatioAnalyzer()
    
    logger.info(f"Options monitor started for {len(tickers)} tickers")
    
    while monitor_state.is_running:
        try:
            for ticker in tickers:
                try:
                    # 옵션 흐름 가져오기
                    flow = fetcher.get_options_flow(ticker, use_cache=False)
                    
                    if not flow:
                        continue
                    
                    # PCR 분석
                    interpretation = analyzer.interpret_pcr(
                        flow.put_call_ratio_volume,
                        flow.put_call_ratio_oi
                    )
                    
                    # 알림 조건 체크
                    should_alert = False
                    alert_reason = []
                    severity = "INFO"
                    
                    # 1. 극단적 PCR
                    if flow.put_call_ratio_volume >= 2.0:
                        should_alert = True
                        alert_reason.append(f"Very high PCR: {flow.put_call_ratio_volume:.2f} (bearish)")
                        severity = "HIGH"
                    elif flow.put_call_ratio_volume <= 0.5:
                        should_alert = True
                        alert_reason.append(f"Very low PCR: {flow.put_call_ratio_volume:.2f} (bullish)")
                        severity = "HIGH"
                    
                    # 2. Unusual Activity 많음
                    unusual_count = len(flow.unusual_calls) + len(flow.unusual_puts)
                    if unusual_count >= 5:
                        should_alert = True
                        alert_reason.append(f"High unusual activity: {unusual_count} contracts")
                        severity = "MEDIUM"
                    
                    # 3. 대량 풋 옵션 매수
                    large_puts = [p for p in flow.unusual_puts if p.volume >= 500]
                    if large_puts:
                        should_alert = True
                        alert_reason.append(f"Large put orders detected: {len(large_puts)} contracts >500")
                        severity = "HIGH"
                    
                    # 알림 생성
                    if should_alert:
                        alert = {
                            'ticker': ticker,
                            'timestamp': datetime.now().isoformat(),
                            'severity': severity,
                            'pcr_volume': flow.put_call_ratio_volume,
                            'sentiment': interpretation['overall_sentiment'],
                            'recommendation': interpretation['recommendation'],
                            'reasons': alert_reason,
                            'unusual_count': unusual_count
                        }
                        
                        monitor_state.add_alert(alert)
                        
                        logger.info(
                            f"Options alert: {ticker} - {severity} - {', '.join(alert_reason)}"
                        )
                        
                        # Telegram 알림 전송
                        await send_options_alert(alert)
                    
                    monitor_state.last_check = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Error monitoring {ticker}: {e}")
                    continue
            
            # 10분마다 체크
            await asyncio.sleep(600)
            
        except Exception as e:
            logger.error(f"Error in options monitor loop: {e}")
            await asyncio.sleep(600)
    
    logger.info("Options monitor stopped")


async def send_options_alert(alert: dict):
    """Telegram으로 옵션 알림 전송"""
    try:
        import os
        import aiohttp
        
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not telegram_token or not chat_id:
            return
        
        # 메시지 포맷
        emoji_map = {
            "HIGH": "🚨",
            "MEDIUM": "⚠️",
            "INFO": "ℹ️"
        }
        
        emoji = emoji_map.get(alert['severity'], "📊")
        
        msg = f"{emoji} **Options Flow Alert**\n\n"
        msg += f"**Ticker:** {alert['ticker']}\n"
        msg += f"**PCR:** {alert['pcr_volume']:.2f}\n"
        msg += f"**Sentiment:** {alert['sentiment']}\n"
        msg += f"**Recommendation:** {alert['recommendation']}\n\n"
        msg += f"**Reasons:**\n"
        
        for reason in alert['reasons']:
            msg += f"  • {reason}\n"
        
        # Telegram 전송
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Telegram alert sent for {alert['ticker']}")
                    
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
