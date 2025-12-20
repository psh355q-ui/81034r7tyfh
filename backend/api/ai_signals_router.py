"""
AI-Powered Trading Signals Router with Semantic Router

Skill Layer와 Semantic Router를 사용한 지능형 신호 생성 시스템

Features:
- Semantic Router 기반 Intent 분류
- Skill Layer 동적 도구 로딩
- Optimized Signal Pipeline 통합
- 토큰 비용 최적화 (83% 감소)

Author: AI Trading System
Date: 2025-12-05
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-signals", tags=["AI Signals"])

# Global instances (lazy loading)
_semantic_router = None
_skill_registry = None
_signal_pipeline = None
_metrics_collector = None


def get_semantic_router():
    """Semantic Router 인스턴스 가져오기"""
    global _semantic_router
    if _semantic_router is None:
        try:
            from backend.routing.semantic_router import get_semantic_router
            _semantic_router = get_semantic_router()
            logger.info("Semantic Router initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Router: {e}")
            raise HTTPException(status_code=500, detail=f"Semantic Router initialization failed: {e}")
    return _semantic_router


def get_skill_registry():
    """Skill Registry 인스턴스 가져오기"""
    global _skill_registry
    if _skill_registry is None:
        try:
            from backend.skills.skill_initializer import initialize_all_skills
            _skill_registry = initialize_all_skills()
            logger.info("Skill Registry initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Skill Registry: {e}")
            raise HTTPException(status_code=500, detail=f"Skill Registry initialization failed: {e}")
    return _skill_registry


def get_signal_pipeline():
    """Optimized Signal Pipeline 인스턴스 가져오기"""
    global _signal_pipeline
    if _signal_pipeline is None:
        try:
            from backend.services.optimized_signal_pipeline import OptimizedSignalPipeline
            _signal_pipeline = OptimizedSignalPipeline()
            logger.info("Optimized Signal Pipeline initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Signal Pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"Signal Pipeline initialization failed: {e}")
    return _signal_pipeline


def get_metrics_collector():
    """메트릭 수집기 인스턴스 가져오기"""
    global _metrics_collector
    if _metrics_collector is None:
        try:
            from backend.monitoring.skill_metrics_collector import get_metrics_collector as _get_collector
            _metrics_collector = _get_collector()
            logger.info("Metrics Collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Metrics Collector: {e}")
            raise HTTPException(status_code=500, detail=f"Metrics Collector initialization failed: {e}")
    return _metrics_collector


# ============================================================================
# Request/Response Models
# ============================================================================

class SignalGenerationRequest(BaseModel):
    """신호 생성 요청"""
    ticker: str
    context: Optional[str] = None
    strategy: Optional[str] = "news_analysis"  # news_analysis, technical, fundamental
    use_optimization: bool = True


class SignalGenerationResponse(BaseModel):
    """신호 생성 응답"""
    success: bool
    ticker: str
    signal: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    tools_used: int = 0
    tokens_saved_pct: float = 0.0
    cost_usd: float = 0.0
    processing_time_ms: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None


class SkillRegistryInfo(BaseModel):
    """Skill Registry 정보"""
    total_skills: int
    categories: Dict[str, int]
    skills: List[Dict[str, Any]]


class RouterStatusResponse(BaseModel):
    """Router 상태"""
    semantic_router_active: bool
    skill_registry_active: bool
    signal_pipeline_active: bool
    registered_skills: int
    available_tools: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=RouterStatusResponse)
async def get_router_status():
    """
    AI Signals Router 상태 확인

    Returns:
        Router 상태 정보
    """
    try:
        router_instance = get_semantic_router()
        registry = get_skill_registry()
        pipeline = get_signal_pipeline()

        info = registry.get_registry_info()

        return RouterStatusResponse(
            semantic_router_active=router_instance is not None,
            skill_registry_active=registry is not None,
            signal_pipeline_active=pipeline is not None,
            registered_skills=info['total_skills'],
            available_tools=sum(skill['tool_count'] for skill in info['skills'])
        )
    except Exception as e:
        logger.error(f"Error getting router status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills", response_model=SkillRegistryInfo)
async def get_skills_info():
    """
    등록된 Skill 정보 조회

    Returns:
        Skill Registry 정보
    """
    try:
        registry = get_skill_registry()
        info = registry.get_registry_info()

        return SkillRegistryInfo(
            total_skills=info['total_skills'],
            categories=info['categories'],
            skills=info['skills']
        )
    except Exception as e:
        logger.error(f"Error getting skills info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=SignalGenerationResponse)
async def generate_signal(request: SignalGenerationRequest):
    """
    AI 기반 거래 신호 생성

    Semantic Router를 사용하여 최적의 Skill을 선택하고 신호를 생성합니다.

    Args:
        request: 신호 생성 요청

    Returns:
        생성된 거래 신호
    """
    start_time = datetime.now()

    try:
        # Semantic Router로 Intent 분류
        semantic_router = get_semantic_router()

        # 사용자 입력 구성
        user_input = f"Generate trading signal for {request.ticker}"
        if request.context:
            user_input += f". Context: {request.context}"

        # 라우팅 실행
        routing_result = await semantic_router.route(user_input)

        logger.info(
            f"Routed to intent: {routing_result.intent}, "
            f"tools: {len(routing_result.tools)}, "
            f"model: {routing_result.provider}"
        )

        # Signal Pipeline으로 신호 생성
        pipeline = get_signal_pipeline()

        signal_result = await pipeline.generate_signal_with_routing(
            ticker=request.ticker,
            routing_result=routing_result,
            context=request.context
        )

        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # 토큰 절감율 계산 (기존 30 tools 대비)
        baseline_tools = 30
        tools_used = len(routing_result.tools)
        tokens_saved_pct = ((baseline_tools - tools_used) / baseline_tools) * 100

        return SignalGenerationResponse(
            success=True,
            ticker=request.ticker,
            signal=signal_result.get('signal'),
            intent=routing_result.intent,
            tools_used=tools_used,
            tokens_saved_pct=tokens_saved_pct,
            cost_usd=signal_result.get('cost_usd', 0.0),
            processing_time_ms=processing_time,
            message="Signal generated successfully"
        )

    except Exception as e:
        logger.error(f"Error generating signal: {e}", exc_info=True)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SignalGenerationResponse(
            success=False,
            ticker=request.ticker,
            processing_time_ms=processing_time,
            error=str(e),
            message="Signal generation failed"
        )


@router.post("/analyze-news")
async def analyze_news_for_signal(
    ticker: str,
    max_news: int = Query(default=10, ge=1, le=50)
):
    """
    뉴스 기반 신호 생성

    NewsSkill과 GeminiSkill을 사용하여 최신 뉴스를 분석하고 거래 신호를 생성합니다.

    Args:
        ticker: 종목 티커
        max_news: 분석할 뉴스 개수

    Returns:
        뉴스 분석 결과 및 거래 신호
    """
    try:
        registry = get_skill_registry()

        # NewsSkill로 뉴스 수집
        news_skill = registry.get_skill("MarketData.News")
        if not news_skill:
            raise HTTPException(status_code=500, detail="NewsSkill not available")

        news_result = await news_skill.execute(
            "search_news",
            keyword=ticker,
            max_results=max_news
        )

        # GeminiSkill로 감성 분석
        gemini_skill = registry.get_skill("Intelligence.Gemini")
        if not gemini_skill:
            raise HTTPException(status_code=500, detail="GeminiSkill not available")

        # 뉴스 제목들을 텍스트로 결합
        news_text = "\n".join([
            f"- {article['title']}"
            for article in news_result.get('articles', [])
        ])

        sentiment_result = await gemini_skill.execute(
            "analyze_sentiment",
            text=news_text
        )

        # 신호 생성
        sentiment = sentiment_result.get('sentiment', 'NEUTRAL')
        confidence = sentiment_result.get('confidence', 0.0)

        signal = {
            "ticker": ticker,
            "action": "BUY" if sentiment == "POSITIVE" and confidence > 0.7 else
                     "SELL" if sentiment == "NEGATIVE" and confidence > 0.7 else
                     "HOLD",
            "confidence": confidence,
            "sentiment": sentiment,
            "news_count": len(news_result.get('articles', [])),
            "generated_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "ticker": ticker,
            "signal": signal,
            "news": news_result,
            "sentiment_analysis": sentiment_result
        }

    except Exception as e:
        logger.error(f"Error analyzing news: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing-demo")
async def routing_demo(user_input: str):
    """
    Semantic Router 데모

    사용자 입력에 대한 라우팅 결과를 보여줍니다.

    Args:
        user_input: 사용자 입력 텍스트

    Returns:
        라우팅 결과 (Intent, Tool Groups, Model)
    """
    try:
        semantic_router = get_semantic_router()
        routing_result = await semantic_router.route(user_input)

        return {
            "success": True,
            "user_input": user_input,
            "routing": {
                "intent": routing_result.intent,
                "confidence": routing_result.intent_confidence,
                "tool_groups": routing_result.selected_tool_groups,
                "tools_count": len(routing_result.tools),
                "model": {
                    "provider": routing_result.provider,
                    "model": routing_result.model,
                    "reason": routing_result.model_reason
                }
            },
            "tools": [
                {
                    "name": tool.get('function', {}).get('name', 'Unknown'),
                    "description": tool.get('function', {}).get('description', '')[:100]
                }
                for tool in routing_result.tools[:5]  # 처음 5개만
            ]
        }

    except Exception as e:
        logger.error(f"Error in routing demo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health Check"""
    return {
        "status": "healthy",
        "service": "AI Signals Router",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Monitoring & Metrics Endpoints
# ============================================================================

@router.get("/metrics/cost-summary")
async def get_cost_summary(period_hours: int = Query(default=24, ge=1, le=168)):
    """
    비용 요약 조회

    Args:
        period_hours: 조회 기간 (시간), 기본값 24시간

    Returns:
        비용 요약 정보
    """
    try:
        metrics_collector = get_metrics_collector()
        summary = await metrics_collector.get_cost_summary(period_hours=period_hours)

        return {
            "success": True,
            "period": {
                "start": summary.period_start.isoformat(),
                "end": summary.period_end.isoformat(),
                "hours": period_hours
            },
            "summary": {
                "total_invocations": summary.total_invocations,
                "total_cost_usd": round(summary.total_cost_usd, 4),
                "total_tokens": summary.total_tokens,
                "avg_cost_per_invocation": (
                    round(summary.total_cost_usd / summary.total_invocations, 4)
                    if summary.total_invocations > 0 else 0
                ),
                "avg_tokens_saved_pct": round(summary.avg_tokens_saved_pct, 2),
                "estimated_monthly_cost": round(summary.total_cost_usd * (720 / period_hours), 2)
            },
            "by_provider": summary.cost_by_provider,
            "by_skill": summary.cost_by_skill,
            "top_skills": {
                "most_used": summary.most_used_skills[:5],
                "most_expensive": summary.most_expensive_skills[:5]
            }
        }
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/real-time")
async def get_real_time_metrics():
    """
    실시간 메트릭 조회

    Returns:
        최근 5분간의 실시간 통계
    """
    try:
        metrics_collector = get_metrics_collector()
        stats = await metrics_collector.get_real_time_stats()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "metrics": stats
        }
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Prometheus 메트릭 export

    Returns:
        Prometheus 형식의 메트릭
    """
    try:
        metrics_collector = get_metrics_collector()
        from prometheus_client import CONTENT_TYPE_LATEST
        from fastapi.responses import Response

        metrics_data = metrics_collector.export_prometheus_metrics()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
