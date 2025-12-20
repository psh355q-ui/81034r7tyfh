"""
V2 API Router

Enhanced Trading Agent V2 API 엔드포인트
- Screener
- Macro
- Skeptic
- Briefing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# V2 모듈 임포트
from backend.ai.enhanced_trading_agent import EnhancedTradingAgent
from backend.services.market_scanner import DynamicScreener, get_universe, UniverseType
from backend.services.market_scanner.massive_api_client import get_massive_client
from backend.ai.macro import MacroDataCollector
from backend.ai.reasoning.macro_consistency_checker import MacroConsistencyChecker
from backend.intelligence import DailyBriefingGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["V2 Trading System"])

# 싱글톤 인스턴스
_enhanced_agent: Optional[EnhancedTradingAgent] = None
_macro_collector: Optional[MacroDataCollector] = None
_macro_checker: Optional[MacroConsistencyChecker] = None
_briefing_generator: Optional[DailyBriefingGenerator] = None


def get_enhanced_agent() -> EnhancedTradingAgent:
    """Enhanced Trading Agent 싱글톤"""
    global _enhanced_agent
    if _enhanced_agent is None:
        _enhanced_agent = EnhancedTradingAgent()
    return _enhanced_agent


def get_macro_collector() -> MacroDataCollector:
    """Macro Collector 싱글톤"""
    global _macro_collector
    if _macro_collector is None:
        _macro_collector = MacroDataCollector()
    return _macro_collector


def get_macro_checker() -> MacroConsistencyChecker:
    """Macro Checker 싱글톤"""
    global _macro_checker
    if _macro_checker is None:
        _macro_checker = MacroConsistencyChecker()
    return _macro_checker


def get_briefing_generator() -> DailyBriefingGenerator:
    """Briefing Generator 싱글톤"""
    global _briefing_generator
    if _briefing_generator is None:
        _briefing_generator = DailyBriefingGenerator()
    return _briefing_generator


# ==================== Macro Endpoints ====================

@router.get("/macro/snapshot")
async def get_macro_snapshot():
    """
    현재 매크로 스냅샷 조회
    
    VIX, 금리, Credit Spread, 시장 국면 등
    """
    try:
        collector = get_macro_collector()
        snapshot = await collector.get_snapshot()
        return collector.to_dict(snapshot)
    except Exception as e:
        logger.error(f"매크로 스냅샷 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/consistency")
async def check_macro_consistency():
    """
    매크로 정합성 체크
    
    경제 지표 간 모순 탐지
    """
    try:
        collector = get_macro_collector()
        checker = get_macro_checker()
        
        snapshot = await collector.get_snapshot()
        
        macro_data = {
            "vix": snapshot.vix,
            "credit_spread": snapshot.credit_spread,
            "sp500_return_1m": snapshot.sp500_return_1m,
        }
        
        contradictions = await checker.detect_contradictions(macro_data)
        
        return {
            "contradictions_found": len(contradictions),
            "contradictions": [
                {
                    "type": c.anomaly_type.value,
                    "severity": c.severity.value,
                    "description": c.contradiction_description,
                    "implication": c.market_implication,
                }
                for c in contradictions
            ],
            "report": checker.format_report_korean(contradictions),
        }
    except Exception as e:
        logger.error(f"매크로 정합성 체크 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analysis Endpoints ====================

@router.post("/analyze/{ticker}")
async def analyze_enhanced(ticker: str):
    """
    강화된 종목 분석
    
    매크로 체크 + AI 분석 + Skeptic 검토
    """
    try:
        agent = get_enhanced_agent()
        result = await agent.analyze_enhanced(ticker)
        
        return {
            "ticker": result["ticker"],
            "timestamp": result["timestamp"],
            "decision": {
                "action": result["decision"].action if result["decision"] else "ERROR",
                "conviction": result["decision"].conviction if result["decision"] else 0,
                "reasoning": result["decision"].reasoning if result["decision"] else "",
            },
            "macro_snapshot": result.get("macro_snapshot"),
            "macro_warnings": result.get("macro_warnings", []),
            "skeptic_analysis": result.get("skeptic_analysis"),
            "final_recommendation": result.get("final_recommendation"),
        }
    except Exception as e:
        logger.error(f"강화 분석 실패 {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Briefing Endpoints ====================

@router.get("/briefing/daily")
async def get_daily_briefing():
    """
    일일 시황 브리핑 생성 (한국어)
    """
    try:
        generator = get_briefing_generator()
        briefing = await generator.generate_daily_briefing()
        markdown = generator.to_markdown(briefing)
        
        return {
            "briefing": markdown,
            "timestamp": briefing.timestamp.isoformat(),
            "index_changes": briefing.index_changes,
        }
    except Exception as e:
        logger.error(f"일일 브리핑 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Workflow Endpoints ====================

@router.post("/workflow/daily")
async def run_daily_workflow(background_tasks: BackgroundTasks):
    """
    일일 워크플로우 전체 실행
    
    1. 브리핑 생성
    2. 매크로 체크
    3. 종목 스크리닝
    4. 상위 종목 분석
    """
    try:
        agent = get_enhanced_agent()
        result = await agent.run_daily_workflow()
        
        return result
    except Exception as e:
        logger.error(f"일일 워크플로우 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_v2_metrics():
    """
    V2 시스템 메트릭스 조회
    """
    try:
        agent = get_enhanced_agent()
        return agent.get_v2_metrics()
    except Exception as e:
        logger.error(f"메트릭스 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
