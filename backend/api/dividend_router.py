"""
Dividend Router - 배당 API 엔드포인트

Phase 21: Dividend Intelligence Module - Step 1.6
Date: 2025-12-25

Endpoints:
- GET  /api/dividend/calendar - 배당 캘린더
- GET  /api/dividend/portfolio - 내 배당 현황
- POST /api/dividend/simulate/drip - DRIP 복리 시뮬레이션
- POST /api/dividend/simulate/injection - 예수금 추가 시뮬레이션
- GET  /api/dividend/risk/{ticker} - 리스크 점수
- GET  /api/dividend/aristocrats - 배당 귀족주 목록
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.data.collectors.dividend_collector import DividendCollector
from backend.analytics.dividend_analyzer import DividendAnalyzer
from backend.intelligence.dividend_risk_agent import DividendRiskAgent
from backend.analytics.tax_engine import TaxEngine

router = APIRouter(prefix="/api/dividend", tags=["dividend"])

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
async def simulate_cash_injection(
    request: CashInjectionRequest,
    positions: List[PortfolioPosition]
):
    """
    예수금 추가 시뮬레이션
    
    Request Body:
        {
            "inject_amount_usd": 10000,
            "exchange_rate": 1300
        }
    
    Positions:
        [{"ticker": "JNJ", "shares": 100, "avg_price": 150}, ...]
    
    Returns:
        {
            "before": {...},
            "after": {...},
            "increase": {...}
        }
    """
    
    analyzer = DividendAnalyzer()
    
    try:
        positions_dict = [p.dict() for p in positions]
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


@router.get("/aristocrats")
async def list_dividend_aristocrats(
    min_years: int = Query(25, description="최소 연속 배당 증가 연수"),
    sector: Optional[str] = Query(None, description="섹터 필터")
):
    """
    배당 귀족주 목록 (25년+ 연속 배당 증가)
    
    Args:
        min_years: 최소 연속 증가 연수 (기본 25년)
        sector: 섹터 필터 (예: "Healthcare")
    
    Returns:
        [
            {
                "ticker": "JNJ",
                "company_name": "Johnson & Johnson",
                "sector": "Healthcare",
                "consecutive_years": 61,
                "current_yield": 2.85
            },
            ...
        ]
    """
    
    # TODO: DB에서 조회
    # 현재는 하드코딩된 샘플 데이터 반환
    
    aristocrats = [
        {
            "ticker": "JNJ",
            "company_name": "Johnson & Johnson",
            "sector": "Healthcare",
            "consecutive_years": 61,
            "current_yield": 2.85
        },
        {
            "ticker": "PG",
            "company_name": "Procter & Gamble",
            "sector": "Consumer Staples",
            "consecutive_years": 67,
            "current_yield": 2.45
        },
        {
            "ticker": "KO",
            "company_name": "Coca-Cola",
            "sector": "Consumer Staples",
            "consecutive_years": 61,
            "current_yield": 3.02
        }
    ]
    
    # 필터링
    results = [a for a in aristocrats if a['consecutive_years'] >= min_years]
    
    if sector:
        results = [a for a in results if a['sector'] == sector]
    
    return {
        "count": len(results),
        "min_years": min_years,
        "sector": sector,
        "aristocrats": results
    }


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
    
    collector = DividendCollector()
    
    try:
        result = await collector.calculate_ttm_yield(ticker.upper())
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "dividend",
        "timestamp": datetime.now().isoformat()
    }
