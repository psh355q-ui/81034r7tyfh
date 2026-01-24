"""
Intelligence API Router

Market Intelligence v2.0 API 엔드포인트

API Endpoints:
- POST /api/intelligence/contrary-signal - 시장 쏠림 분석
- POST /api/intelligence/pipeline/process - 뉴스 파이프라인 처리
- POST /api/intelligence/chart/generate - 차트 생성
- GET  /api/intelligence/statistics - 인텔리전스 통계

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Intelligence components
from backend.ai.intelligence.contrary_signal import (
    ContrarySignal,
    create_contrary_signal,
)
from backend.ai.intelligence.enhanced_news_pipeline import (
    EnhancedNewsProcessingPipeline,
    create_enhanced_pipeline,
)
from backend.ai.intelligence.chart_generator import (
    ChartGenerator,
    ChartType,
    ChartConfig,
    create_chart_generator,
)
from backend.ai.llm_providers import get_llm_provider
from backend.data.collectors.api_clients.yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

# ============================================================================
# Singleton Instances
# ============================================================================

_contrary_signal_detector: Optional[ContrarySignal] = None
_enhanced_pipeline: Optional[EnhancedNewsProcessingPipeline] = None
_chart_generator: Optional[ChartGenerator] = None


def get_contrary_signal_detector() -> ContrarySignal:
    """Get ContrarySignal singleton"""
    global _contrary_signal_detector
    if _contrary_signal_detector is None:
        llm = get_llm_provider()
        market_data = YahooFinanceClient()
        _contrary_signal_detector = create_contrary_signal(
            llm_provider=llm,
            market_data_client=market_data
        )
    return _contrary_signal_detector


def get_enhanced_pipeline() -> EnhancedNewsProcessingPipeline:
    """Get EnhancedNewsProcessingPipeline singleton"""
    global _enhanced_pipeline
    if _enhanced_pipeline is None:
        llm = get_llm_provider()
        market_data = YahooFinanceClient()

        # Initialize intelligence components
        from backend.ai.intelligence.news_filter import NewsFilter
        from backend.ai.intelligence.narrative_state_engine import NarrativeStateEngine
        from backend.ai.intelligence.fact_checker import FactChecker
        from backend.ai.intelligence.market_confirmation import MarketConfirmation
        from backend.ai.intelligence.horizon_tagger import HorizonTagger

        # Create GLM-4.7 config
        from backend.ai.llm_providers import ModelConfig, ModelProvider
        glm_config = ModelConfig(
            model="GLM-4.7",
            provider=ModelProvider.GLM,
            max_tokens=1000,
            temperature=0.7,
        )

        # Initialize components
        intelligence_components = {
            "news_filter": NewsFilter(
                llm_provider=llm,
                stage1_config=glm_config,
                stage2_config=glm_config,
            ),
            "narrative_engine": NarrativeStateEngine(
                llm_provider=llm,
                analysis_config=glm_config,
            ),
            "fact_checker": FactChecker(
                llm_provider=llm,
            ),
            "market_confirmation": MarketConfirmation(
                llm_provider=llm,
                market_data_client=market_data,
            ),
            "horizon_tagger": HorizonTagger(
                llm_provider=llm,
                market_data_client=market_data,
            ),
        }

        _enhanced_pipeline = create_enhanced_pipeline(
            llm_provider=llm,
            intelligence_components=intelligence_components,
        )
    return _enhanced_pipeline


def get_chart_generator() -> ChartGenerator:
    """Get ChartGenerator singleton"""
    global _chart_generator
    if _chart_generator is None:
        llm = get_llm_provider()
        _chart_generator = create_chart_generator(llm_provider=llm)
    return _chart_generator


# ============================================================================
# Request/Response Models
# ============================================================================

class ContrarySignalRequest(BaseModel):
    """Contrary signal analysis request"""
    symbol: str
    days: int = 30


class ContrarySignalResponse(BaseModel):
    """Contrary signal analysis response"""
    symbol: str
    crowding_level: str
    flow_z_score: float
    sentiment_extreme: bool
    sentiment_direction: str
    position_skew: float
    contrarian_action: str
    reasoning: str
    confidence: float


class PipelineProcessRequest(BaseModel):
    """Enhanced news pipeline process request"""
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None


class PipelineProcessResponse(BaseModel):
    """Enhanced news pipeline process response"""
    success: bool
    final_insight: Optional[str]
    contrarian_view: Optional[Dict[str, Any]]
    invalidation_conditions: List[str]
    failure_triggers: List[str]
    processing_time_ms: int
    stages: Dict[str, Any]


class ChartGenerateRequest(BaseModel):
    """Chart generation request"""
    chart_type: str  # THEME_BUBBLE, GEOPOLITICAL_TIMELINE, SECTOR_PERFORMANCE
    title: Optional[str] = ""
    width: int = 800
    height: int = 600
    # Chart-specific data
    themes: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    events: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None


class ChartGenerateResponse(BaseModel):
    """Chart generation response"""
    success: bool
    chart_type: str
    file_path: str
    metadata: Dict[str, Any]


class StatisticsResponse(BaseModel):
    """Intelligence statistics response"""
    contrary_signal: Dict[str, Any]
    pipeline: Dict[str, Any]
    chart_generator: Dict[str, Any]


# ============================================================================
# Contrary Signal Endpoints
# ============================================================================

@router.post("/contrary-signal", response_model=ContrarySignalResponse)
async def analyze_contrary_signal(request: ContrarySignalRequest):
    """
    시장 쏠림 분석 (Contrary Signal)

    종목별 시장 쏠림 정도를 분석하고 역발상 매매 신호를 생성합니다.

    Args:
        request: symbol (종목), days (분석 기간)

    Returns:
        crowding_level: LOW, MEDIUM, HIGH, EXTREME
        contrarian_action: ACCUMULATE, HOLD, WATCH_FOR_PULLBACK, EXIT
    """
    try:
        detector = get_contrary_signal_detector()
        result = await detector.analyze_contrary_signal(
            symbol=request.symbol,
            days=request.days,
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.get_errors())

        return ContrarySignalResponse(
            symbol=request.symbol,
            crowding_level=result.data.get("crowding_level", "UNKNOWN"),
            flow_z_score=result.data.get("flow_z_score", 0.0),
            sentiment_extreme=result.data.get("sentiment_extreme", False),
            sentiment_direction=result.data.get("sentiment_direction", "NEUTRAL"),
            position_skew=result.data.get("position_skew", 0.0),
            contrarian_action=result.data.get("contrarian_action", "HOLD"),
            reasoning=result.reasoning,
            confidence=result.confidence,
        )

    except Exception as e:
        logger.error(f"Contrary signal analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhanced Pipeline Endpoints
# ============================================================================

@router.post("/pipeline/process", response_model=PipelineProcessResponse)
async def process_news_article(request: PipelineProcessRequest):
    """
    뉴스 기사 파이프라인 처리 (Enhanced News Pipeline)

    6단계 파이프라인을 통해 뉴스 기사를 분석하고 종합 인사이트를 생성합니다.

    Stages:
        1. Filter (관련성 필터링)
        2. Narrative (내러티브 분석)
        3. Fact Check (사실 검증)
        4. Market Confirm (시장 검증)
        5. Horizon (시간축 태깅)
        6. Policy (정책 실현 확률)

    Args:
        request: title, content, source, published_at

    Returns:
        final_insight: 종합 인사이트
        contrarian_view: 반대 시나리오 (bull_case, bear_case, key_risks)
        invalidation_conditions: 무효화 조건 목록
        failure_triggers: 실패 트리거 목록
    """
    try:
        pipeline = get_enhanced_pipeline()

        article = {
            "title": request.title,
            "content": request.content or "",
            "source": request.source or "Unknown",
            "published_at": request.published_at or datetime.now().isoformat(),
        }

        result = await pipeline.process_article(article)

        # Convert ContrarianView to dict
        contrarian_view_dict = None
        if result.contrarian_view:
            contrarian_view_dict = result.contrarian_view.to_dict()

        # Convert stages to dict
        stages_dict = {}
        for stage_name, stage_result in result.stages.items():
            stages_dict[stage_name] = {
                "success": stage_result.success,
                "data": stage_result.data,
                "reasoning": stage_result.reasoning,
            }

        return PipelineProcessResponse(
            success=result.success,
            final_insight=result.final_insight,
            contrarian_view=contrarian_view_dict,
            invalidation_conditions=result.invalidation_conditions,
            failure_triggers=result.failure_triggers,
            processing_time_ms=result.processing_time_ms,
            stages=stages_dict,
        )

    except Exception as e:
        logger.error(f"Pipeline processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chart Generator Endpoints
# ============================================================================

@router.post("/chart/generate", response_model=ChartGenerateResponse)
async def generate_chart(request: ChartGenerateRequest):
    """
    차트 생성 (Chart Generator)

    소수몽키 스타일의 시각화 차트를 자동 생성합니다.

    Chart Types:
        - THEME_BUBBLE: 테마 버블 차트
        - GEOPOLITICAL_TIMELINE: 지정학 타임라인
        - SECTOR_PERFORMANCE: 섹터 성과 바 차트

    Args:
        request: chart_type, title, width, height, data

    Returns:
        file_path: 생성된 차트 파일 경로
        metadata: 차트 메타데이터
    """
    try:
        generator = get_chart_generator()

        # Map string to ChartType enum
        chart_type_map = {
            "THEME_BUBBLE": ChartType.THEME_BUBBLE,
            "GEOPOLITICAL_TIMELINE": ChartType.GEOPOLITICAL_TIMELINE,
            "SECTOR_PERFORMANCE": ChartType.SECTOR_PERFORMANCE,
        }

        chart_type = chart_type_map.get(request.chart_type)
        if not chart_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid chart_type. Must be one of: {list(chart_type_map.keys())}"
            )

        # Build chart config
        config = ChartConfig(
            chart_type=chart_type,
            title=request.title,
            width=request.width,
            height=request.height,
            themes=request.themes,
            sectors=request.sectors,
            events=request.events,
            metrics=request.metrics,
        )

        result = await generator.generate_chart(config)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.get_errors())

        return ChartGenerateResponse(
            success=result.success,
            chart_type=result.data.get("chart_type", ""),
            file_path=result.data.get("file_path", ""),
            metadata=result.data.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/statistics", response_model=StatisticsResponse)
async def get_intelligence_statistics():
    """
    인텔리전스 컴포넌트 통계 조회

    모든 Market Intelligence v2.0 컴포넌트의 통계를 반환합니다.
    """
    try:
        contrary_detector = get_contrary_signal_detector()
        enhanced_pipeline = get_enhanced_pipeline()
        chart_gen = get_chart_generator()

        return StatisticsResponse(
            contrary_signal=contrary_detector.get_statistics(),
            pipeline=enhanced_pipeline.get_statistics(),
            chart_generator=chart_gen.get_statistics(),
        )

    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def intelligence_health():
    """Intelligence 시스템 헬스 체크"""
    try:
        return {
            "status": "healthy",
            "components": {
                "contrary_signal": _contrary_signal_detector is not None,
                "enhanced_pipeline": _enhanced_pipeline is not None,
                "chart_generator": _chart_generator is not None,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
