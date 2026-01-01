"""
dividend_router.py - 배당 인텔리전스 API

📊 Data Sources:
    - DividendCollector: 배당 일정 및 TTM yield
        - Yahoo Finance API (yfinance): 배당 히스토리, 배당률
        - PostgreSQL: 배당 캘린더 캐시
    - DividendAnalyzer: 배당 수익 계산 및 시뮬레이션
        - 포트폴리오 연간 배당 수익 계산
        - DRIP 복리 시뮬레이션
        - 예수금 추가 시뮬레이션
    - DividendRiskAgent: AI 기반 배당 리스크 분석
        - 배당 지속성 평가
        - 섹터별 민감도 분석

🔗 External Dependencies:
    - fastapi: API 라우팅 및 쿼리 파라미터
    - pydantic: 요청/응답 모델 검증
    - backend.data.collectors.dividend_collector: 배당 데이터 수집
    - backend.analytics.dividend_analyzer: 배당 분석 엔진
    - backend.intelligence.dividend_risk_agent: AI 리스크 평가

📤 API Endpoints:
    - GET /api/dividend/calendar: 배당 캘린더 (향후 30일)
    - POST /api/dividend/portfolio: 포트폴리오 배당 현황
    - POST /api/dividend/simulate/drip: DRIP 복리 시뮬레이션
    - POST /api/dividend/simulate/injection: 예수금 추가 시뮬레이션
    - GET /api/dividend/risk/{ticker}: 종목별 배당 리스크
    - GET /api/dividend/aristocrats: 배당 귀족주 목록
    - GET /api/dividend/ttm/{ticker}: TTM Yield 조회
    - GET /api/dividend/health: 헬스 체크

🔄 Called By:
    - frontend/src/pages/DividendDashboard.tsx
    - frontend/src/components/Dividend/DividendCalendar.tsx
    - frontend/src/components/Dividend/DripSimulator.tsx

📝 Notes:
    - 배당 데이터는 Yahoo Finance에서 실시간 조회
    - 귀족주 목록은 현재 하드코딩 (향후 DB화 예정)
    - TTM Yield는 캐시 우선 전략 사용
    - 세금 계산은 TaxEngine 통합 예정

Phase 21: Dividend Intelligence Module - Step 1.6
Date: 2025-12-25
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
import traceback
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 🔍 DEBUG: Print actual file path being loaded
print(f"=" * 80)
print(f"🔍 DIVIDEND_ROUTER LOADED FROM: {Path(__file__).absolute()}")
print(f"=" * 80)

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.data.collectors.dividend_collector import DividendCollector
from backend.analytics.dividend_analyzer import DividendAnalyzer
from backend.intelligence.dividend_risk_agent import DividendRiskAgent
from backend.analytics.tax_engine import TaxEngine

# Agent Logging
from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    ExecutionStatus,
    ErrorImpact
)

router = APIRouter(prefix="/api/dividend", tags=["dividend"])
agent_logger = AgentLogger("dividend-intelligence", "analysis")

# ============================================================================
# Request/Response Models
# ============================================================================

class DripSimulationRequest(BaseModel):
    initial_usd: float
    monthly_contribution_usd: float
    years: int
    cagr: float
    dividend_yield: float
    reinvest: bool = True
    exchange_rate: Optional[float] = None

class CashInjectionRequest(BaseModel):
    inject_amount_usd: float
    positions: List[PortfolioPosition]
    exchange_rate: Optional[float] = None

class PortfolioPosition(BaseModel):
    ticker: str
    shares: int
    avg_price: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/calendar")
async def get_dividend_calendar(month: Optional[str] = None):
    """
    배당 캘린더 (월별 배당락일/지급일)
    
    Args:
        month: YYYY-MM 형식 (예: "2025-01"), None이면 현재 월
    
    Returns:
        [
            {
                "ticker": "JNJ",
                "ex_dividend_date": "2025-01-15",
                "payment_date": "2025-02-01",
                "amount": 1.19,
                "days_until": 5
            },
            ...
        ]
    """
    
    collector = DividendCollector()
    
    try:
        # 향후 30일간의 배당락일 조회
        upcoming = await collector.get_upcoming_ex_dates(days=30)
        
        return {
            "month": month or datetime.now().strftime("%Y-%m"),
            "count": len(upcoming),
            "events": upcoming
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio")
async def get_portfolio_dividends(positions: List[PortfolioPosition], exchange_rate: Optional[float] = None):
    """
    내 포트폴리오 배당 현황
    
    Request Body:
        [
            {"ticker": "JNJ", "shares": 100, "avg_price": 150},
            {"ticker": "PG", "shares": 50, "avg_price": 145},
            ...
        ]
    
    Returns:
        {
            "annual_net_krw": 5200000,
            "monthly_avg_krw": 433333,
            "yoc": 5.2,
            "by_month": {...}
        }
    """
    
    analyzer = DividendAnalyzer()
    
    try:
        positions_dict = [p.dict() for p in positions]
        result = await analyzer.calculate_portfolio_income(positions_dict, exchange_rate)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/drip")
async def simulate_drip(request: DripSimulationRequest):
    """
    DRIP 복리 시뮬레이션
    
    Request Body:
        {
            "initial_usd": 100000,
            "monthly_contribution_usd": 1000,
            "years": 10,
            "cagr": 7.0,
            "dividend_yield": 4.0,
            "reinvest": true,
            "exchange_rate": 1300
        }
    
    Returns:
        [
            {
                "year": 1,
                "portfolio_value_usd": 105000,
                "annual_dividends_usd": 5000,
                "cumulative_dividends_usd": 5000
            },
            ...
        ]
    """
    
    analyzer = DividendAnalyzer()
    
    try:
        results = await analyzer.simulate_drip(
            initial=request.initial_usd,
            monthly_contribution=request.monthly_contribution_usd,
            years=request.years,
            cagr=request.cagr,
            dividend_yield=request.dividend_yield,
            reinvest=request.reinvest,
            exchange_rate=request.exchange_rate
        )
        
        return {
            "request": request.dict(),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/injection")
async def simulate_cash_injection(request: CashInjectionRequest):
    """
    예수금 추가 시뮬레이션
    
    Request Body:
        {
            "inject_amount_usd": 10000,
            "positions": [
                {"ticker": "JNJ", "shares": 100, "avg_price": 150},
                {"ticker": "PG", "shares": 50, "avg_price": 145}
            ],
            "exchange_rate": 1300
        }
    
    Returns:
        {
            "before": {...},
            "after": {...},
            "increase": {...}
        }
    """
    
    analyzer = DividendAnalyzer()
    
    try:
        positions_dict = [p.dict() for p in request.positions]
        result = await analyzer.simulate_cash_injection(
            current_positions=positions_dict,
            inject_amount_usd=request.inject_amount_usd,
            exchange_rate=request.exchange_rate
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{ticker}")
async def get_dividend_risk(ticker: str):
    """
    종목별 리스크 점수
    
    Returns:
        {
            "ticker": "JNJ",
            "risk_score": 25,
            "risk_level": "Safe",
            "warnings": [...],
            "metrics": {...}
        }
    """
    
    agent = DividendRiskAgent()
    
    try:
        risk_assessment = agent.calculate_risk_score(ticker.upper())
        sensitivity = agent.get_sector_sensitivity(risk_assessment['sector'])
        
        return {
            **risk_assessment,
            "sector_sensitivity": sensitivity
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-new-endpoint-12345")
def test_new_endpoint():
    """완전히 새로운 테스트 엔드포인트"""
    return {"message": "This is a NEW endpoint created at 12:34", "test": True}

@router.get("/aristocrats")
def list_dividend_aristocrats(
    min_years: int = 5,
    sector: str = None
):
    """배당 귀족주 목록 - 연속 배당 증가 기업"""
    try:
        logger.info(f"✅ Aristocrats endpoint called with min_years={min_years}, sector={sector}")

        # Hardcoded aristocrats data with correct field names
        aristocrats_data = [
            {"ticker": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "consecutive_years": 62, "current_yield": 3.0},
            {"ticker": "PG", "company_name": "Procter & Gamble", "sector": "Consumer Staples", "consecutive_years": 68, "current_yield": 2.4},
            {"ticker": "KO", "company_name": "Coca-Cola", "sector": "Consumer Staples", "consecutive_years": 62, "current_yield": 3.0},
            {"ticker": "PEP", "company_name": "PepsiCo", "sector": "Consumer Staples", "consecutive_years": 52, "current_yield": 2.7},
            {"ticker": "MCD", "company_name": "McDonald's", "sector": "Consumer Discretionary", "consecutive_years": 48, "current_yield": 2.2},
            {"ticker": "WMT", "company_name": "Walmart", "sector": "Consumer Staples", "consecutive_years": 51, "current_yield": 1.4},
            {"ticker": "CVX", "company_name": "Chevron", "sector": "Energy", "consecutive_years": 37, "current_yield": 3.5},
            {"ticker": "XOM", "company_name": "ExxonMobil", "sector": "Energy", "consecutive_years": 42, "current_yield": 3.2},
            {"ticker": "ABBV", "company_name": "AbbVie", "sector": "Healthcare", "consecutive_years": 8, "current_yield": 3.4},
            {"ticker": "MRK", "company_name": "Merck", "sector": "Healthcare", "consecutive_years": 14, "current_yield": 2.6},
            {"ticker": "LOW", "company_name": "Lowe's", "sector": "Consumer Discretionary", "consecutive_years": 61, "current_yield": 1.9},
            {"ticker": "HD", "company_name": "Home Depot", "sector": "Consumer Discretionary", "consecutive_years": 15, "current_yield": 2.3},
            {"ticker": "TGT", "company_name": "Target", "sector": "Consumer Staples", "consecutive_years": 56, "current_yield": 2.9},
            {"ticker": "COST", "company_name": "Costco", "sector": "Consumer Staples", "consecutive_years": 20, "current_yield": 0.6},
            {"ticker": "MMM", "company_name": "3M", "sector": "Industrials", "consecutive_years": 66, "current_yield": 5.9},
            {"ticker": "CAT", "company_name": "Caterpillar", "sector": "Industrials", "consecutive_years": 30, "current_yield": 1.5},
            {"ticker": "O", "company_name": "Realty Income", "sector": "Real Estate", "consecutive_years": 29, "current_yield": 5.5},
            {"ticker": "AFL", "company_name": "Aflac", "sector": "Financials", "consecutive_years": 41, "current_yield": 2.2},
            {"ticker": "ABT", "company_name": "Abbott Labs", "sector": "Healthcare", "consecutive_years": 52, "current_yield": 1.9},
            {"ticker": "CL", "company_name": "Colgate-Palmolive", "sector": "Consumer Staples", "consecutive_years": 61, "current_yield": 2.3}
        ]

        # Filter by min_years
        filtered = [a for a in aristocrats_data if a["consecutive_years"] >= min_years]

        # Filter by sector if provided
        if sector:
            filtered = [a for a in filtered if a["sector"].lower() == sector.lower()]

        return {
            "count": len(filtered),
            "min_years": min_years,
            "last_updated": datetime.now().isoformat(),
            "next_update": "2026-03-01",
            "data_source": "hardcoded",
            "aristocrats": filtered
        }
    except Exception as e:
        logger.error(f"Aristocrats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ttm/{ticker}")
async def get_ttm_yield(ticker: str):
    """
    TTM Yield 조회 (캐시 우선)
    
    Returns:
        {
            "ticker": "JNJ",
            "ttm_dividends": 4.52,
            "current_price": 158.32,
            "ttm_yield": 2.85,
            "payment_count": 4
        }
    """
    start_time = datetime.now()
    task_id = f"ttm-{ticker}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    collector = DividendCollector()
    
    try:
        result = await collector.calculate_ttm_yield(ticker.upper())
        
        # Log successful execution
        agent_logger.log_execution(ExecutionLog(
            timestamp=datetime.now(),
            agent="analysis/dividend-intelligence",
            task_id=task_id,
            status=ExecutionStatus.SUCCESS,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            input={"ticker": ticker.upper()},
            output={
                "ttm_yield": result.get("ttm_yield"),
                "payment_count": result.get("payment_count")
            }
        ))
        
        return result
    
    except Exception as e:
        # Log error
        agent_logger.log_error(ErrorLog(
            timestamp=datetime.now(),
            agent="analysis/dividend-intelligence",
            task_id=task_id,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "stack": traceback.format_exc(),
                "context": {"ticker": ticker}
            },
            impact=ErrorImpact.MEDIUM,
            recovery_attempted=False
        ))
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rate")
async def get_exchange_rate():
    """
    USD/KRW 환율 조회

    📊 Data Source:
        - 환율 API (실시간)
        - 캐시: 매일 00시에 자동 갱신

    Returns:
        {
            "rate": float,  # 환율 (예: 1320.50)
            "last_updated": str,  # 마지막 업데이트 시각
            "next_update": str,  # 다음 업데이트 예정 시각 (00:00 KST)
            "source": str  # "cache" or "api"
        }
    """
    import requests
    from datetime import datetime, timezone, timedelta

    try:
        # 실시간 환율 API 호출 (예: exchangerate-api.com 무료 API)
        # 참고: 실제 운영에서는 한국은행 API 등 공식 API 사용 권장
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        data = response.json()

        usd_to_krw = data['rates']['KRW']
        last_updated = datetime.now(timezone.utc)

        # 다음 00:00 KST 계산
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        next_midnight = (now_kst + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        return {
            "rate": round(usd_to_krw, 2),
            "last_updated": last_updated.isoformat(),
            "next_update": next_midnight.isoformat(),
            "source": "api"
        }
    except Exception as e:
        # 오류 시 기본값 반환 (1320원)
        agent_logger.log_error(
            error_type="ExchangeRateError",
            message=f"환율 조회 실패: {str(e)}",
            impact=ErrorImpact.LOW,
            context={"error": str(e)}
        )

        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        next_midnight = (now_kst + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        return {
            "rate": 1320.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "next_update": next_midnight.isoformat(),
            "source": "default"
        }


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "dividend",
        "timestamp": datetime.now().isoformat()
    }
# TEST LINE ADDED BY CLAUDE
