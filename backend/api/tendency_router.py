"""
Trading Tendency API Router

ChatGPT Feature 6: 거래 성향 API

GET /api/tendency/analyze - 거래 성향 분석

작성일: 2025-12-16
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from backend.metrics.trading_tendency_analyzer import (
    get_tendency_analyzer,
    TradeAction,
    TendencyResult
)

router = APIRouter(prefix="/api/tendency", tags=["tendency"])


# Request Models
class TradeActionRequest(BaseModel):
    ticker: str
    action: str
    quantity: int
    price: float
    timestamp: str
    portfolio_percentage: float


class TendencyAnalysisRequest(BaseModel):
    user_id: str
    trade_history: List[TradeActionRequest]
    current_portfolio: Dict[str, Any]


# Response Models
class TendencyMetricsResponse(BaseModel):
    position_size_score: float
    holding_period_score: float
    risk_level_score: float
    diversification_score: float
    reaction_speed_score: float
    overall_score: float


class TendencyAnalysisResponse(BaseModel):
    tendency_score: float
    tendency_level: str
    metrics: TendencyMetricsResponse
    insights: List[str]
    recommendations: List[str]
    analyzed_at: str


@router.post("/analyze", response_model=TendencyAnalysisResponse)
async def analyze_tendency(request: TendencyAnalysisRequest):
    """
    거래 성향 분석
    
    사용자의 거래 내역과 포트폴리오를 분석하여
    보수적 ↔ 공격적 성향 점수 제공
    
    Returns:
        - tendency_score: 0~100 (0: 보수적, 100: 공격적)
        - tendency_level: 성향 레벨
        - metrics: 세부 지표
        - insights: 인사이트
        - recommendations: 추천사항
    """
    try:
        # Convert request to TradeAction objects
        trade_history = [
            TradeAction(
                ticker=t.ticker,
                action=t.action,
                quantity=t.quantity,
                price=t.price,
                timestamp=datetime.fromisoformat(t.timestamp),
                portfolio_percentage=t.portfolio_percentage
            )
            for t in request.trade_history
        ]
        
        # Analyze
        analyzer = get_tendency_analyzer()
        result = analyzer.analyze_tendency(trade_history, request.current_portfolio)
        
        # Build response
        return TendencyAnalysisResponse(
            tendency_score=result.tendency_score,
            tendency_level=result.tendency_level.value,
            metrics=TendencyMetricsResponse(
                position_size_score=result.metrics.position_size_score,
                holding_period_score=result.metrics.holding_period_score,
                risk_level_score=result.metrics.risk_level_score,
                diversification_score=result.metrics.diversification_score,
                reaction_speed_score=result.metrics.reaction_speed_score,
                overall_score=result.metrics.overall_score()
            ),
            insights=result.insights,
            recommendations=result.recommendations,
            analyzed_at=result.analyzed_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sample")
async def get_sample_analysis():
    """
    샘플 성향 분석 결과
    
    테스트용
    """
    from datetime import datetime, timedelta
    
    # Sample trades
    trades = [
        TradeAction(
            ticker="AAPL",
            action="BUY",
            quantity=10,
            price=180,
            timestamp=datetime.now() - timedelta(days=30),
            portfolio_percentage=5.0
        ),
        TradeAction(
            ticker="MSFT",
            action="BUY",
            quantity=10,
            price=420,
            timestamp=datetime.now() - timedelta(days=20),
            portfolio_percentage=7.0
        ),
        TradeAction(
            ticker="GOOGL",
            action="BUY",
            quantity=5,
            price=140,
            timestamp=datetime.now() - timedelta(days=10),
            portfolio_percentage=4.0
        )
    ]
    
    portfolio = {
        'positions': [
            {'ticker': 'AAPL'},
            {'ticker': 'MSFT'},
            {'ticker': 'GOOGL'},
            {'ticker': 'AMZN'},
            {'ticker': 'META'}
        ]
    }
    
    analyzer = get_tendency_analyzer()
    result = analyzer.analyze_tendency(trades, portfolio)
    
    return {
        "tendency_score": result.tendency_score,
        "tendency_level": result.tendency_level.value,
        "metrics": {
            "position_size": result.metrics.position_size_score,
            "holding_period": result.metrics.holding_period_score,
            "risk_level": result.metrics.risk_level_score,
            "diversification": result.metrics.diversification_score,
            "reaction_speed": result.metrics.reaction_speed_score
        },
        "insights": result.insights,
        "recommendations": result.recommendations
    }
