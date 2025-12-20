"""
Financial Forensics API Router

재무 포렌식 분석 API 엔드포인트

Endpoints:
- POST /api/forensics/analyze/{ticker}  - 종목 분석
- GET  /api/forensics/report/{ticker}   - 최근 리포트 조회
- GET  /api/forensics/batch             - 다중 종목 일괄 분석
- GET  /api/forensics/alerts            - Red Flag 알림 조회

Author: AI Trading System
Date: 2025-11-21
Phase: 14 Task 2
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forensics", tags=["Financial Forensics"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ForensicsRequest(BaseModel):
    """분석 요청"""
    ticker: str


class BatchForensicsRequest(BaseModel):
    """일괄 분석 요청"""
    tickers: List[str]


class RedFlagResponse(BaseModel):
    """Red Flag 응답"""
    flag_name: str
    severity: str
    current_value: float
    threshold: float
    is_triggered: bool
    description: str
    recommendation: str


class ForensicsReportResponse(BaseModel):
    """포렌식 리포트 응답"""
    ticker: str
    analysis_date: str
    overall_verdict: str
    confidence_score: float
    recommendation: str
    summary: str
    red_flags: List[RedFlagResponse]
    critical_count: int
    high_count: int


# ============================================================================
# Cache (실제로는 Redis 사용)
# ============================================================================

class ForensicsCache:
    """분석 결과 캐시"""
    
    def __init__(self):
        self.reports = {}  # ticker -> report
        self.alerts = []   # Red Flag 알림 리스트
    
    def save_report(self, ticker: str, report: dict):
        """리포트 저장"""
        self.reports[ticker] = {
            'report': report,
            'cached_at': datetime.now()
        }
        
        # Red Flag 있으면 알림 추가
        if report['overall_verdict'] in ['CRITICAL', 'HIGH_RISK', 'SUSPICIOUS']:
            self.alerts.append({
                'ticker': ticker,
                'verdict': report['overall_verdict'],
                'recommendation': report['recommendation'],
                'critical_count': report['critical_count'],
                'high_count': report['high_count'],
                'timestamp': datetime.now().isoformat()
            })
            
            # 최근 100개만 유지
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def get_report(self, ticker: str, max_age_hours: int = 24) -> Optional[dict]:
        """캐시된 리포트 조회"""
        if ticker not in self.reports:
            return None
        
        cached_data = self.reports[ticker]
        age = datetime.now() - cached_data['cached_at']
        
        # 24시간 이상 지난 캐시는 무효
        if age.total_seconds() > max_age_hours * 3600:
            return None
        
        return cached_data['report']


# Global cache
forensics_cache = ForensicsCache()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/analyze/{ticker}", response_model=ForensicsReportResponse)
async def analyze_ticker(ticker: str, force_refresh: bool = False):
    """
    종목 재무 포렌식 분석
    
    Args:
        ticker: 종목 티커
        force_refresh: 캐시 무시하고 새로 분석 (기본 False)
        
    Returns:
        분석 리포트
    """
    ticker_upper = ticker.upper()
    
    # 캐시 확인
    if not force_refresh:
        cached_report = forensics_cache.get_report(ticker_upper)
        if cached_report:
            logger.info(f"Returning cached forensics report for {ticker_upper}")
            return ForensicsReportResponse(**cached_report)
    
    # 새로 분석
    from financial_forensics import FinancialForensicsAnalyzer
    
    try:
        analyzer = FinancialForensicsAnalyzer()
        report = analyzer.analyze(ticker_upper)
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to fetch financial data for {ticker_upper}"
            )
        
        # 응답 생성
        report_dict = report.to_dict()
        
        # 캐시에 저장
        forensics_cache.save_report(ticker_upper, report_dict)
        
        return ForensicsReportResponse(**report_dict)
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker_upper}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/report/{ticker}", response_model=ForensicsReportResponse)
async def get_report(ticker: str):
    """
    최근 분석 리포트 조회 (캐시만)
    
    Args:
        ticker: 종목 티커
        
    Returns:
        캐시된 리포트 (없으면 404)
    """
    ticker_upper = ticker.upper()
    
    cached_report = forensics_cache.get_report(ticker_upper)
    
    if not cached_report:
        raise HTTPException(
            status_code=404,
            detail=f"No recent report found for {ticker_upper}. Run /analyze first."
        )
    
    return ForensicsReportResponse(**cached_report)


@router.post("/batch")
async def analyze_batch(
    request: BatchForensicsRequest,
    background_tasks: BackgroundTasks
):
    """
    다중 종목 일괄 분석
    
    백그라운드에서 분석 실행
    
    Args:
        request: 티커 리스트
        
    Returns:
        작업 시작 확인
    """
    tickers = [t.upper() for t in request.tickers]
    
    if not tickers:
        raise HTTPException(status_code=400, detail="Ticker list is empty")
    
    if len(tickers) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tickers per batch")
    
    # 백그라운드 태스크 추가
    background_tasks.add_task(run_batch_analysis, tickers)
    
    return {
        "status": "started",
        "message": f"Batch analysis started for {len(tickers)} tickers",
        "tickers": tickers
    }


@router.get("/alerts")
async def get_forensics_alerts(
    limit: int = 20,
    severity: Optional[str] = None
):
    """
    Red Flag 알림 조회
    
    Args:
        limit: 최대 반환 개수
        severity: 필터 (CRITICAL, HIGH_RISK, SUSPICIOUS)
        
    Returns:
        알림 리스트
    """
    alerts = forensics_cache.alerts
    
    # 필터링
    if severity:
        alerts = [a for a in alerts if a['verdict'] == severity.upper()]
    
    # 최신순 정렬
    alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    alerts = alerts[:limit]
    
    return {
        "alerts": alerts,
        "count": len(alerts)
    }


@router.get("/summary")
async def get_portfolio_forensics_summary(tickers: str):
    """
    포트폴리오 전체 재무 건강도 요약
    
    Args:
        tickers: 쉼표로 구분된 티커 (예: NVDA,TSLA,AAPL)
        
    Returns:
        요약 통계
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    
    summary = {
        "total_tickers": len(ticker_list),
        "analyzed": 0,
        "clean": 0,
        "suspicious": 0,
        "high_risk": 0,
        "critical": 0,
        "tickers_by_verdict": {}
    }
    
    for ticker in ticker_list:
        report = forensics_cache.get_report(ticker)
        
        if report:
            summary["analyzed"] += 1
            verdict = report['overall_verdict']
            
            if verdict == "CLEAN":
                summary["clean"] += 1
            elif verdict == "SUSPICIOUS":
                summary["suspicious"] += 1
            elif verdict == "HIGH_RISK":
                summary["high_risk"] += 1
            elif verdict == "CRITICAL":
                summary["critical"] += 1
            
            summary["tickers_by_verdict"][ticker] = verdict
    
    # 전체 건강도 평가
    if summary["critical"] > 0:
        summary["overall_health"] = "CRITICAL"
    elif summary["high_risk"] > 0:
        summary["overall_health"] = "HIGH_RISK"
    elif summary["suspicious"] >= summary["analyzed"] * 0.5:
        summary["overall_health"] = "SUSPICIOUS"
    else:
        summary["overall_health"] = "HEALTHY"
    
    return summary


@router.get("/compare")
async def compare_tickers(tickers: str):
    """
    종목 간 재무 건강도 비교
    
    Args:
        tickers: 쉼표로 구분된 티커
        
    Returns:
        비교 테이블
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    
    comparison = []
    
    for ticker in ticker_list:
        report = forensics_cache.get_report(ticker)
        
        if report:
            comparison.append({
                "ticker": ticker,
                "verdict": report['overall_verdict'],
                "confidence": report['confidence_score'],
                "recommendation": report['recommendation'],
                "critical_flags": report['critical_count'],
                "high_flags": report['high_count']
            })
        else:
            comparison.append({
                "ticker": ticker,
                "verdict": "NOT_ANALYZED",
                "confidence": 0.0,
                "recommendation": "N/A",
                "critical_flags": 0,
                "high_flags": 0
            })
    
    # 위험도 순 정렬
    verdict_order = {"CRITICAL": 0, "HIGH_RISK": 1, "SUSPICIOUS": 2, "CLEAN": 3, "NOT_ANALYZED": 4}
    comparison.sort(key=lambda x: verdict_order.get(x['verdict'], 99))
    
    return {
        "comparison": comparison,
        "count": len(comparison)
    }


# ============================================================================
# Background Tasks
# ============================================================================

async def run_batch_analysis(tickers: List[str]):
    """백그라운드 일괄 분석"""
    from financial_forensics import FinancialForensicsAnalyzer
    
    analyzer = FinancialForensicsAnalyzer()
    
    for ticker in tickers:
        try:
            logger.info(f"Analyzing {ticker} in batch...")
            report = analyzer.analyze(ticker)
            
            if report:
                report_dict = report.to_dict()
                forensics_cache.save_report(ticker, report_dict)
                logger.info(f"✅ {ticker}: {report.overall_verdict}")
            else:
                logger.warning(f"❌ {ticker}: Failed to analyze")
                
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
        
        # Rate limiting (Yahoo Finance)
        import asyncio
        await asyncio.sleep(1)
    
    logger.info(f"Batch analysis complete for {len(tickers)} tickers")


# ============================================================================
# Integration with Constitution Rules
# ============================================================================

async def check_forensics_for_ticker(ticker: str) -> dict:
    """
    Constitution Rules에서 호출하는 함수
    
    Args:
        ticker: 종목 티커
        
    Returns:
        {"verdict": str, "recommendation": str, "critical_count": int}
    """
    # 캐시된 리포트 조회
    report = forensics_cache.get_report(ticker)
    
    if not report:
        # 캐시 없으면 새로 분석
        from financial_forensics import FinancialForensicsAnalyzer
        analyzer = FinancialForensicsAnalyzer()
        report_obj = analyzer.analyze(ticker)
        
        if report_obj:
            report = report_obj.to_dict()
            forensics_cache.save_report(ticker, report)
        else:
            return {
                "verdict": "UNKNOWN",
                "recommendation": "HOLD",
                "critical_count": 0
            }
    
    return {
        "verdict": report['overall_verdict'],
        "recommendation": report['recommendation'],
        "critical_count": report['critical_count'],
        "high_count": report['high_count']
    }
