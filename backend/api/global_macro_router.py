"""
Global Macro API Router
========================
글로벌 매크로 전략 및 국가 리스크 분석 API

Endpoints:
- GET /api/global-macro/market-map - 글로벌 시장 상관관계 그래프
- GET /api/global-macro/country-risks - 국가별 리스크 점수
- POST /api/global-macro/analyze-event - 이벤트 나비효과 분석
- GET /api/global-macro/theme-risks/{ticker} - 테마주 리스크 분석
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os
from backend.ai.skills.common.logging_decorator import log_endpoint

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/api/global-macro", tags=["Global Macro"])


# ============================================
# Pydantic Models
# ============================================

class EventAnalysisRequest(BaseModel):
    event_type: str  # "fed_rate_hike", "china_pmi_drop", etc.
    magnitude: float = 1.0  # 1.0 = normal, 2.0 = severe


class CountryRisk(BaseModel):
    country: str
    score: float
    components: Dict[str, float]
    trend: str  # "improving", "stable", "deteriorating"


class MarketNode(BaseModel):
    id: str
    label: str
    type: str  # "index", "commodity", "currency", "crypto"


class MarketCorrelation(BaseModel):
    source: str
    target: str
    weight: float
    relationship: str  # "positive", "negative", "inverse"


class ThemeRisk(BaseModel):
    ticker: str
    risk_score: float
    risk_level: str  # "low", "medium", "high", "extreme"
    flags: List[str]


# ============================================
# API Endpoints
# ============================================

@router.get("/market-map")
@log_endpoint("global_macro", "system")
async def get_market_map() -> Dict:
    """글로벌 시장 상관관계 그래프 데이터 반환"""
    try:
        from backend.ai.macro.global_market_map import get_global_market_map
        market_map = get_global_market_map()
        
        # Trigger real data update (non-blocking if possible, but here we wait for MVP)
        await market_map.update_market_data()
        
        nodes = []
        for node_id, node in market_map.nodes.items():
            nodes.append({
                "id": node.id,
                "label": node.name,
                "type": node.asset_type.value,
                "change_pct": node.change_pct,
                "current_value": node.current_value
            })
        
        correlations = []
        for source, targets in market_map.correlations.items():
            for corr in targets:
                correlations.append({
                    "source": corr.source,
                    "target": corr.target,
                    "weight": corr.coefficient,
                    "relationship": "positive" if corr.coefficient > 0 else "negative"
                })
        
        return {
            "nodes": nodes,
            "correlations": correlations,
            "total_nodes": len(nodes),
            "total_correlations": len(correlations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Global macro map error: {e}")
        # Fallback with mock data if everything fails
        return {
            "nodes": [
                {"id": "US_SPX", "label": "S&P 500", "type": "index"},
                {"id": "US_NDX", "label": "Nasdaq 100", "type": "index"},
                {"id": "KR_KOSPI", "label": "KOSPI", "type": "index"},
            ],
            "correlations": [],
            "total_nodes": 3,
            "total_correlations": 0,
            "timestamp": datetime.now().isoformat()
        }


@router.get("/country-risks")
@log_endpoint("global_macro", "system")
async def get_country_risks() -> Dict:
    """국가별 리스크 점수 반환"""
    try:
        from backend.ai.macro.country_risk_engine import CountryRiskEngine, Country
        engine = CountryRiskEngine()
        
        country_codes = ["US", "JP", "CN", "EU", "KR"]
        risks = []
        
        for code in country_codes:
            try:
                c_enum = Country(code)
                score_obj = engine.calculate_risk_score(c_enum)
                
                # components dictionary construction
                components = {
                    "interest": score_obj.interest_rate_risk,
                    "inflation": score_obj.inflation_risk,
                    "currency": score_obj.currency_risk,
                    "growth": score_obj.growth_risk,
                    "stock": score_obj.equity_risk
                }
                
                risks.append({
                    "country": code,
                    "score": round(score_obj.composite_score, 2),
                    "components": components,
                    "trend": "stable" # Trend logic to be implemented later
                })
            except Exception as e:
                logger.error(f"Error calculating risk for {code}: {e}")
                continue
        
        return {
            "risks": risks,
            "average_score": round(sum(r["score"] for r in risks) / len(risks), 2),
            "highest_risk": max(risks, key=lambda x: x["score"]),
            "lowest_risk": min(risks, key=lambda x: x["score"]),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        # Fallback with mock data
        risks = [
            {"country": "US", "score": 45.5, "components": {"interest": 60, "inflation": 55, "currency": 30, "growth": 35, "stock": 50}, "trend": "improving"},
            {"country": "JP", "score": 52.3, "components": {"interest": 20, "inflation": 45, "currency": 75, "growth": 55, "stock": 65}, "trend": "stable"},
            {"country": "CN", "score": 68.7, "components": {"interest": 50, "inflation": 40, "currency": 80, "growth": 85, "stock": 90}, "trend": "deteriorating"},
            {"country": "EU", "score": 55.2, "components": {"interest": 65, "inflation": 60, "currency": 45, "growth": 55, "stock": 50}, "trend": "stable"},
            {"country": "KR", "score": 48.9, "components": {"interest": 55, "inflation": 50, "currency": 55, "growth": 40, "stock": 45}, "trend": "improving"}
        ]
        
        return {
            "risks": risks,
            "average_score": round(sum(r["score"] for r in risks) / len(risks), 2),
            "highest_risk": max(risks, key=lambda x: x["score"]),
            "lowest_risk": min(risks, key=lambda x: x["score"]),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/analyze-event")
@log_endpoint("global_macro", "system")
async def analyze_event(request: EventAnalysisRequest) -> Dict:
    """이벤트 나비효과 분석"""
    try:
        from ai.strategies.global_macro_strategy import GlobalMacroStrategy
        strategy = GlobalMacroStrategy()
        
        result = strategy.analyze_event(
            event_type=request.event_type,
            magnitude=request.magnitude
        )
        
        return {
            "event": request.event_type,
            "magnitude": request.magnitude,
            "impact_chain": result.get("impact_chain", []),
            "affected_assets": result.get("affected_assets", []),
            "risk_adjustment": result.get("risk_adjustment", 1.0),
            "recommendation": result.get("recommendation", "hold"),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        # Fallback with mock analysis
        event_impacts = {
            "fed_rate_hike": {
                "impact_chain": ["US_RATES ↑", "USD ↑", "GOLD ↓", "EM_STOCKS ↓"],
                "affected_assets": ["SPY", "GLD", "EEM", "TLT"],
                "risk_adjustment": 1.3,
                "recommendation": "reduce_equity_exposure"
            },
            "china_pmi_drop": {
                "impact_chain": ["CN_PMI ↓", "COMMODITIES ↓", "AUD ↓", "MINING_STOCKS ↓"],
                "affected_assets": ["FXI", "EWA", "COPX", "VALE"],
                "risk_adjustment": 1.5,
                "recommendation": "avoid_china_exposure"
            }
        }
        
        default_impact = {
            "impact_chain": ["Unknown event - monitoring"],
            "affected_assets": [],
            "risk_adjustment": 1.0,
            "recommendation": "hold"
        }
        
        impact = event_impacts.get(request.event_type, default_impact)
        
        return {
            "event": request.event_type,
            "magnitude": request.magnitude,
            **impact,
            "timestamp": datetime.now().isoformat()
        }


@router.get("/theme-risks/{ticker}")
@log_endpoint("global_macro", "system")
async def get_theme_risks(ticker: str) -> Dict:
    """특정 종목의 테마주 리스크 분석"""
    try:
        from ai.risk.theme_risk_detector import ThemeRiskDetector
        detector = ThemeRiskDetector()
        
        result = detector.analyze(ticker)
        
        return {
            "ticker": ticker,
            "risk_score": result.get("risk_score", 0),
            "risk_level": result.get("risk_level", "unknown"),
            "flags": result.get("flags", []),
            "recommendation": result.get("recommendation", ""),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        # Fallback with mock data
        return {
            "ticker": ticker,
            "risk_score": 35.0,
            "risk_level": "low",
            "flags": [],
            "recommendation": "No significant theme risk detected",
            "timestamp": datetime.now().isoformat()
        }


@router.get("/subscription-status")
@log_endpoint("global_macro", "system")
async def get_subscription_status() -> Dict:
    """AI 구독 상태 및 비용 최적화 현황"""
    try:
        from ai.cost.subscription_manager import SubscriptionManager
        manager = SubscriptionManager()
        
        status = manager.get_status()
        
        return {
            "active_subscriptions": status.get("subscriptions", []),
            "monthly_cost": status.get("monthly_cost", 0),
            "cost_savings": status.get("cost_savings", 0),
            "recommended_model": status.get("recommended_model", "gemini-flash"),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "active_subscriptions": [
                {"provider": "anthropic", "plan": "claude-pro", "monthly_cost": 20},
                {"provider": "google", "plan": "gemini-advanced", "monthly_cost": 20}
            ],
            "monthly_cost": 40,
            "cost_savings": 150,
            "recommended_model": "gemini-2.0-flash-exp",
            "timestamp": datetime.now().isoformat()
        }
