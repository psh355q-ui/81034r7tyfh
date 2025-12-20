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


router = APIRouter(prefix="/api/v1/reasoning", tags=["Deep Reasoning"])


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
    use_mock: bool = True  # Mock 데이터 사용 (실제 가격 조회 안 함)


# ============================================
# Singleton Instances
# ============================================

_strategy: Optional[DeepReasoningStrategy] = None
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_strategy() -> DeepReasoningStrategy:
    """전략 인스턴스 획득"""
    global _strategy
    global _strategy
    if _strategy is None:
        # 실제 AI 클라이언트 사용 (설정된 모델 사용)
        try:
            # 기본 모델로 클라이언트 생성 (Gemini or OpenAI)
            client = AIClientFactory.create()
            _strategy = DeepReasoningStrategy(ai_client=client)
            print(f"✅ DeepReasoningStrategy initialized with REAL client: {client.model}")
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
async def run_backtest_endpoint(use_mock: bool = True):
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
