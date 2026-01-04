"""
Deep Reasoning API Endpoints (Phase 14)
=======================================

REST API for Deep Reasoning Strategy

Endpoints:
- POST /api/v1/reasoning/analyze - 심층 추론 분석
- GET /api/v1/reasoning/knowledge/{entity} - Knowledge Graph 조회
- POST /api/v1/reasoning/verify - 관계 검증
- GET /api/v1/reasoning/backtest - A/B 백테스트 실행
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

# 프로젝트 모듈
from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy, DeepReasoningResult
from backend.ai.ai_client_factory import AIClientFactory, MockAIClient
from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
from backend.config_phase14 import settings, AIRole, get_model_config
from backend.database.repository import get_sync_session, DeepReasoningRepository


router = APIRouter(prefix="/api/reasoning", tags=["Deep Reasoning"])


# ============================================
# Request/Response Models
# ============================================

class AnalyzeRequest(BaseModel):
    """분석 요청"""
    news_text: str = Field(..., description="분석할 뉴스 텍스트")
    model: Optional[str] = Field(None, description="사용할 AI 모델 (기본: 설정값)")
    enable_verification: bool = Field(True, description="실시간 관계 검증 활성화")
    
    class Config:
        json_schema_extra = {
            "example": {
                "news_text": "Google announced TPU v6 with 2x efficiency improvement",
                "model": None,
                "enable_verification": True
            }
        }


class AnalyzeResponse(BaseModel):
    """분석 응답"""
    success: bool
    theme: str
    primary_beneficiary: Optional[Dict[str, Any]]
    hidden_beneficiary: Optional[Dict[str, Any]]
    loser: Optional[Dict[str, Any]]
    bull_case: str
    bear_case: str
    reasoning_trace: List[str]
    model_used: str
    analyzed_at: str
    processing_time_ms: float


class KnowledgeQueryRequest(BaseModel):
    """Knowledge Graph 쿼리"""
    entity: str
    relation_type: Optional[str] = None
    direction: str = "both"  # outgoing, incoming, both


class RelationshipResponse(BaseModel):
    """관계 응답"""
    subject: str
    relation: str
    object: str
    confidence: float
    evidence: Optional[str]
    source: Optional[str]


class VerifyRequest(BaseModel):
    """관계 검증 요청"""
    subject: str
    relation: str
    object: str


class BacktestRequest(BaseModel):
    """백테스트 요청"""
    events: Optional[List[Dict]] = None  # 커스텀 이벤트
    use_mock: bool = False  # 실제 데이터 사용 (Mock은 테스트용)


class HistoryItemResponse(BaseModel):
    """분석 이력 항목"""
    id: int
    news_text: str
    theme: str
    primary_beneficiary_ticker: Optional[str]
    primary_beneficiary_action: Optional[str]
    primary_beneficiary_confidence: Optional[float]
    primary_beneficiary_reasoning: Optional[str]
    hidden_beneficiary_ticker: Optional[str]
    hidden_beneficiary_action: Optional[str]
    hidden_beneficiary_confidence: Optional[float]
    hidden_beneficiary_reasoning: Optional[str]
    loser_ticker: Optional[str]
    loser_action: Optional[str]
    loser_confidence: Optional[float]
    loser_reasoning: Optional[str]
    bull_case: str
    bear_case: str
    reasoning_trace: List[Dict[str, Any]]
    model_used: str
    processing_time_ms: int
    created_at: str


class HistoryListResponse(BaseModel):
    """분석 이력 목록 응답"""
    total: int
    items: List[HistoryItemResponse]


# ============================================
# Singleton Instances
# ============================================

_strategy: Optional[DeepReasoningStrategy] = None
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_strategy() -> DeepReasoningStrategy:
    """전략 인스턴스 획득"""
    global _strategy
    if _strategy is None:
        # 실제 AI 클라이언트 사용 (.env의 GEMINI_MODEL 사용)
        try:
            import os
            # .env에서 모델명 가져오기 (기본값: gemini-2.0-flash)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            client = AIClientFactory.create(model_name)
            _strategy = DeepReasoningStrategy(ai_client=client)
            print(f"✅ DeepReasoningStrategy initialized with REAL client: {client.model_name}")
        except Exception as e:
            print(f"⚠️ Failed to create real AI client, falling back to MOCK: {e}")
            mock_client = MockAIClient("mock-api")
            _strategy = DeepReasoningStrategy(ai_client=mock_client)
    return _strategy


def get_knowledge_graph() -> KnowledgeGraph:
    """Knowledge Graph 인스턴스 획득"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph


# ============================================
# Endpoints
# ============================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_news(request: AnalyzeRequest):
    """
    뉴스에 대한 심층 추론 분석

    3단계 CoT (Chain of Thought) 분석:
    1. Direct Impact - 직접 영향
    2. Secondary Impact - 파생 효과 (꼬리 물기)
    3. Strategic Conclusion - 투자 전략

    분석 결과는 자동으로 DB에 저장됩니다.
    """
    start_time = datetime.now()

    try:
        strategy = get_strategy()

        # 모델 변경 (선택사항)
        if request.model:
            client = AIClientFactory.create(request.model)
            strategy.ai_client = client

        # 분석 실행
        result = await strategy.analyze_news(request.news_text)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # DB에 저장 (Repository 사용)
        try:
            session = next(get_sync_session())
            repo = DeepReasoningRepository(session)

            analysis_data = {
                'news_text': request.news_text,
                'theme': result.theme,
                'primary_beneficiary_ticker': result.primary_beneficiary.get('ticker') if result.primary_beneficiary else None,
                'primary_beneficiary_action': result.primary_beneficiary.get('action') if result.primary_beneficiary else None,
                'primary_beneficiary_confidence': result.primary_beneficiary.get('confidence') if result.primary_beneficiary else None,
                'primary_beneficiary_reasoning': result.primary_beneficiary.get('reasoning') if result.primary_beneficiary else None,
                'hidden_beneficiary_ticker': result.hidden_beneficiary.get('ticker') if result.hidden_beneficiary else None,
                'hidden_beneficiary_action': result.hidden_beneficiary.get('action') if result.hidden_beneficiary else None,
                'hidden_beneficiary_confidence': result.hidden_beneficiary.get('confidence') if result.hidden_beneficiary else None,
                'hidden_beneficiary_reasoning': result.hidden_beneficiary.get('reasoning') if result.hidden_beneficiary else None,
                'loser_ticker': result.loser.get('ticker') if result.loser else None,
                'loser_action': result.loser.get('action') if result.loser else None,
                'loser_confidence': result.loser.get('confidence') if result.loser else None,
                'loser_reasoning': result.loser.get('reasoning') if result.loser else None,
                'bull_case': result.bull_case,
                'bear_case': result.bear_case,
                'reasoning_trace': result.reasoning_trace,
                'model_used': result.model_used,
                'processing_time_ms': int(processing_time)
            }

            repo.create_analysis(analysis_data)
            print(f"✅ Analysis saved to DB")
        except Exception as db_error:
            print(f"⚠️ Failed to save analysis to DB: {db_error}")
            # 저장 실패해도 분석 결과는 반환

        return AnalyzeResponse(
            success=True,
            theme=result.theme,
            primary_beneficiary=result.primary_beneficiary,
            hidden_beneficiary=result.hidden_beneficiary,
            loser=result.loser,
            bull_case=result.bull_case,
            bear_case=result.bear_case,
            reasoning_trace=result.reasoning_trace,
            model_used=result.model_used,
            analyzed_at=result.analyzed_at.isoformat(),
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=HistoryListResponse)
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0
):
    """
    Deep Reasoning 분석 이력 조회 (최신순)

    Args:
        limit: 최대 조회 개수 (default: 50, max: 100)
        offset: 시작 위치 (default: 0)

    Returns:
        HistoryListResponse with analysis history
    """
    try:
        # Limit 제한
        limit = min(limit, 100)

        session = next(get_sync_session())
        repo = DeepReasoningRepository(session)

        # 전체 개수 조회
        total = repo.count_total()

        # 이력 조회
        analyses = repo.get_all(limit=limit, offset=offset)

        # Response 변환
        items = []
        for analysis in analyses:
            items.append(HistoryItemResponse(
                id=analysis.id,
                news_text=analysis.news_text,
                theme=analysis.theme,
                primary_beneficiary_ticker=analysis.primary_beneficiary_ticker,
                primary_beneficiary_action=analysis.primary_beneficiary_action,
                primary_beneficiary_confidence=analysis.primary_beneficiary_confidence,
                primary_beneficiary_reasoning=analysis.primary_beneficiary_reasoning,
                hidden_beneficiary_ticker=analysis.hidden_beneficiary_ticker,
                hidden_beneficiary_action=analysis.hidden_beneficiary_action,
                hidden_beneficiary_confidence=analysis.hidden_beneficiary_confidence,
                hidden_beneficiary_reasoning=analysis.hidden_beneficiary_reasoning,
                loser_ticker=analysis.loser_ticker,
                loser_action=analysis.loser_action,
                loser_confidence=analysis.loser_confidence,
                loser_reasoning=analysis.loser_reasoning,
                bull_case=analysis.bull_case,
                bear_case=analysis.bear_case,
                reasoning_trace=analysis.reasoning_trace,
                model_used=analysis.model_used,
                processing_time_ms=analysis.processing_time_ms,
                created_at=analysis.created_at.isoformat()
            ))

        return HistoryListResponse(
            total=total,
            items=items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{analysis_id}", response_model=HistoryItemResponse)
async def get_analysis_by_id(analysis_id: int):
    """
    특정 분석 이력 조회

    Args:
        analysis_id: 분석 ID

    Returns:
        HistoryItemResponse with specific analysis
    """
    try:
        session = next(get_sync_session())
        repo = DeepReasoningRepository(session)

        analysis = repo.get_by_id(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        return HistoryItemResponse(
            id=analysis.id,
            news_text=analysis.news_text,
            theme=analysis.theme,
            primary_beneficiary_ticker=analysis.primary_beneficiary_ticker,
            primary_beneficiary_action=analysis.primary_beneficiary_action,
            primary_beneficiary_confidence=analysis.primary_beneficiary_confidence,
            primary_beneficiary_reasoning=analysis.primary_beneficiary_reasoning,
            hidden_beneficiary_ticker=analysis.hidden_beneficiary_ticker,
            hidden_beneficiary_action=analysis.hidden_beneficiary_action,
            hidden_beneficiary_confidence=analysis.hidden_beneficiary_confidence,
            hidden_beneficiary_reasoning=analysis.hidden_beneficiary_reasoning,
            loser_ticker=analysis.loser_ticker,
            loser_action=analysis.loser_action,
            loser_confidence=analysis.loser_confidence,
            loser_reasoning=analysis.loser_reasoning,
            bull_case=analysis.bull_case,
            bear_case=analysis.bear_case,
            reasoning_trace=analysis.reasoning_trace,
            model_used=analysis.model_used,
            processing_time_ms=analysis.processing_time_ms,
            created_at=analysis.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: int):
    """
    분석 이력 삭제

    Args:
        analysis_id: 삭제할 분석 ID

    Returns:
        Success message
    """
    try:
        session = next(get_sync_session())
        repo = DeepReasoningRepository(session)

        success = repo.delete_analysis(analysis_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        return {
            "success": True,
            "message": f"Analysis {analysis_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{entity}")
async def get_entity_knowledge(
    entity: str,
    relation_type: Optional[str] = None,
    direction: str = "both"
):
    """
    특정 엔티티의 Knowledge Graph 관계 조회
    
    Parameters:
    - entity: 조회할 엔티티 (예: Google, Nvidia)
    - relation_type: 관계 타입 필터 (partner, competitor, supplier 등)
    - direction: outgoing (나가는), incoming (들어오는), both
    """
    try:
        kg = get_knowledge_graph()
        
        relationships = await kg.get_relationships(
            entity=entity,
            relation_type=relation_type,
            direction=direction
        )
        
        return {
            "entity": entity,
            "relationship_count": len(relationships),
            "relationships": relationships
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_relationship(request: VerifyRequest):
    """
    관계의 현재 유효성을 실시간 검증
    
    웹 검색을 통해 파트너십/경쟁 관계가 여전히 유효한지 확인
    """
    try:
        kg = get_knowledge_graph()
        strategy = get_strategy()
        
        result = await kg.verify_relationship(
            subject=request.subject,
            relation=request.relation,
            obj=request.object,
            ai_client=strategy.ai_client
        )
        
        return {
            "relationship": f"{request.subject} --[{request.relation}]--> {request.object}",
            "verification": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest")
async def run_backtest_endpoint(use_mock: bool = False):
    """
    A/B 백테스트 실행
    
    Keyword-only vs CoT+RAG 방법 비교
    """
    try:
        from backend.backtesting.ab_backtest import ABBacktestEngine
        
        engine = ABBacktestEngine()
        
        # 일부 이벤트만 (빠른 응답)
        test_events = engine.HISTORICAL_EVENTS[:3]
        
        report = await engine.run_comparison(test_events)
        
        return {
            "summary": {
                "keyword_avg_car": report.keyword_avg_car,
                "cot_rag_avg_car": report.cot_rag_avg_car,
                "keyword_hit_rate": report.keyword_hit_rate,
                "cot_rag_hit_rate": report.cot_rag_hit_rate,
                "winner": "CoT+RAG" if report.cot_rag_avg_car > report.keyword_avg_car else "Keyword"
            },
            "keyword_results": [
                {
                    "event": r.event_name,
                    "ticker": r.ticker,
                    "action": r.action,
                    "return": r.return_pct,
                    "abnormal_return": r.abnormal_return
                }
                for r in report.keyword_results
            ],
            "cot_rag_results": [
                {
                    "event": r.event_name,
                    "ticker": r.ticker,
                    "action": r.action,
                    "return": r.return_pct,
                    "abnormal_return": r.abnormal_return
                }
                for r in report.cot_rag_results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """전략 및 Knowledge Graph 통계"""
    try:
        strategy = get_strategy()
        kg = get_knowledge_graph()
        
        return {
            "strategy_stats": strategy.get_stats(),
            "knowledge_graph_stats": kg.get_stats(),
            "config": {
                "reasoning_model": settings.REASONING_MODEL_NAME,
                "live_verification_enabled": settings.ENABLE_LIVE_KNOWLEDGE_CHECK,
                "reasoning_steps": settings.REASONING_STEPS,
                "daily_limit": settings.DAILY_REASONING_LIMIT
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/seed")
async def seed_knowledge_graph(background_tasks: BackgroundTasks):
    """
    Knowledge Graph에 초기 지식 시드 데이터 import
    
    백그라운드에서 실행됨
    """
    try:
        from backend.config_phase14 import SEED_KNOWLEDGE
        
        kg = get_knowledge_graph()
        
        async def import_task():
            await kg.import_seed_knowledge(SEED_KNOWLEDGE)
        
        background_tasks.add_task(asyncio.create_task, import_task())
        
        return {
            "status": "started",
            "message": "Seed knowledge import started in background",
            "entity_count": len(SEED_KNOWLEDGE)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def health_check():
    """Deep Reasoning API 상태 확인"""
    return {
        "status": "healthy",
        "service": "Deep Reasoning API",
        "version": "14.0.0",
        "model": settings.REASONING_MODEL_NAME,
        "features": {
            "deep_reasoning": True,
            "knowledge_graph": True,
            "live_verification": settings.ENABLE_LIVE_KNOWLEDGE_CHECK,
            "ab_backtest": True
        }
    }


# ============================================
# Main Router Registration Helper
# ============================================

def register_routes(app):
    """메인 앱에 라우터 등록"""
    app.include_router(router)
    return app
