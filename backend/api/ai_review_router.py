"""
AI Review API Router

FastAPI endpoints for AI Review Tab
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from backend.ai.ai_review_models import (
    AIReviewRepository,
    create_ai_review_record,
    AIReviewRecord
)
from backend.ai.trading_terms_parser import TradingTermsParser

router = APIRouter(prefix="/ai-reviews", tags=["AI Review"])

# Repository instance
repo = AIReviewRepository()

# Trading terms parser
terms_parser = TradingTermsParser()


# ============================================================================
# Pydantic Models for API
# ============================================================================

class AnalysisResultInput(BaseModel):
    action: str = Field(..., description="BUY, SELL, or HOLD")
    conviction: float = Field(..., ge=0, le=1, description="Confidence level 0-1")
    reasoning: str = Field(..., description="Main reasoning")
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: float = Field(default=0.0, ge=0, le=1)
    risk_factors: List[str] = Field(default_factory=list)


class DetailedReasoningInput(BaseModel):
    technical_analysis: str = ""
    fundamental_analysis: str = ""
    sentiment_analysis: str = ""
    risk_assessment: str = ""


class ModelInfoInput(BaseModel):
    model_name: str
    tokens_used: int
    response_time_ms: int
    cost_usd: float = 0.0


class CreateAIReviewRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    analysis: AnalysisResultInput
    detailed_reasoning: DetailedReasoningInput
    model_info: ModelInfoInput


class AIReviewSummaryResponse(BaseModel):
    analysis_id: str
    ticker: str
    timestamp: str
    action: str
    conviction: float
    reasoning_preview: str
    has_changes: bool
    model_name: str


class AIReviewListResponse(BaseModel):
    total_count: int
    today_count: int
    avg_conviction: float
    changed_count: int
    reviews: List[dict]


class AIReviewDetailResponse(BaseModel):
    analysis_id: str
    ticker: str
    timestamp: str
    analysis: dict
    detailed_reasoning: dict
    model_info: dict
    diff_from_previous: Optional[dict] = None


class TradingTermResponse(BaseModel):
    term: str
    term_kr: str
    definition: str
    example: str
    category: str
    related_terms: List[str]


class TradingTermsResponse(BaseModel):
    terms: List[TradingTermResponse]
    categories: List[str]
    total_count: int


class StatisticsResponse(BaseModel):
    total: int
    by_action: dict
    by_ticker: dict
    avg_conviction: float
    changed_rate: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=AIReviewListResponse)
async def get_ai_reviews(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Get list of AI reviews with summary statistics
    """
    result = repo.list_all(limit=limit, offset=offset)
    return AIReviewListResponse(**result)


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Get AI review statistics
    """
    stats = repo.get_statistics()
    return StatisticsResponse(**stats)


@router.get("/search")
async def search_reviews(
    ticker: Optional[str] = None,
    action: Optional[str] = None,
    min_conviction: Optional[float] = Query(None, ge=0, le=1),
    has_changes_only: bool = False,
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search AI reviews with filters
    """
    results = repo.search(
        ticker=ticker,
        action=action,
        min_conviction=min_conviction,
        has_changes_only=has_changes_only,
        days_back=days_back,
        limit=limit
    )
    return {
        "count": len(results),
        "reviews": results
    }


@router.get("/{analysis_id}", response_model=AIReviewDetailResponse)
async def get_ai_review_detail(analysis_id: str):
    """
    Get detailed AI review by ID
    """
    record = repo.get(analysis_id)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Review {analysis_id} not found")
    
    return AIReviewDetailResponse(
        analysis_id=record.analysis_id,
        ticker=record.ticker,
        timestamp=record.timestamp,
        analysis=record.to_dict()["analysis"],
        detailed_reasoning=record.to_dict()["detailed_reasoning"],
        model_info=record.to_dict()["model_info"],
        diff_from_previous=record.to_dict()["diff_from_previous"]
    )


@router.get("/ticker/{ticker}/history")
async def get_ticker_history(
    ticker: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get analysis history for a specific ticker
    """
    records = repo.get_history_by_ticker(ticker, limit=limit)
    
    return {
        "ticker": ticker,
        "count": len(records),
        "history": [r.to_dict() for r in records]
    }


@router.get("/ticker/{ticker}/latest")
async def get_latest_for_ticker(ticker: str):
    """
    Get latest analysis for a specific ticker
    """
    record = repo.get_latest_by_ticker(ticker)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"No analysis found for {ticker}")
    
    return record.to_dict()


@router.post("", response_model=dict)
async def create_ai_review(request: CreateAIReviewRequest):
    """
    Create a new AI review record
    
    This endpoint is typically called by the AI Trading Agent after analysis.
    """
    record = create_ai_review_record(
        ticker=request.ticker,
        analysis_result=request.analysis.dict(),
        detailed_reasoning=request.detailed_reasoning.dict(),
        model_name=request.model_info.model_name,
        tokens_used=request.model_info.tokens_used,
        response_time_ms=request.model_info.response_time_ms,
        cost_usd=request.model_info.cost_usd
    )
    
    analysis_id = repo.save(record)
    
    return {
        "success": True,
        "analysis_id": analysis_id,
        "message": f"AI review for {request.ticker} saved successfully"
    }


@router.delete("/{analysis_id}")
async def delete_ai_review(analysis_id: str):
    """
    Delete an AI review record
    """
    success = repo.delete(analysis_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Review {analysis_id} not found")
    
    return {
        "success": True,
        "message": f"Review {analysis_id} deleted"
    }


# ============================================================================
# Trading Terms Dictionary Endpoints
# ============================================================================

@router.get("/terms/all", response_model=TradingTermsResponse)
async def get_trading_terms():
    """
    Get all trading terms from MASTER_GUIDE.md
    """
    terms = terms_parser.get_all_terms()
    categories = terms_parser.get_categories()
    
    return TradingTermsResponse(
        terms=terms,
        categories=categories,
        total_count=len(terms)
    )


@router.get("/terms/search")
async def search_trading_terms(
    query: str = Query(..., min_length=1),
    category: Optional[str] = None
):
    """
    Search trading terms
    """
    results = terms_parser.search_terms(query, category=category)
    
    return {
        "query": query,
        "category": category,
        "count": len(results),
        "terms": results
    }


@router.get("/terms/categories")
async def get_term_categories():
    """
    Get all term categories
    """
    categories = terms_parser.get_categories()
    
    return {
        "categories": categories,
        "count": len(categories)
    }


# ============================================================================
# Integration with Trading Agent
# ============================================================================

@router.post("/from-agent")
async def save_from_trading_agent(
    ticker: str,
    agent_response: dict
):
    """
    Save AI review directly from Trading Agent response
    
    This is a convenience endpoint that parses the Trading Agent's
    response format and saves it as an AI Review.
    """
    try:
        # Extract data from agent response
        analysis_result = {
            "action": agent_response.get("action", "HOLD"),
            "conviction": agent_response.get("conviction", 0.5),
            "reasoning": agent_response.get("reasoning", ""),
            "target_price": agent_response.get("target_price"),
            "stop_loss": agent_response.get("stop_loss"),
            "position_size": agent_response.get("position_size", 0.0),
            "risk_factors": agent_response.get("risk_factors", [])
        }
        
        # Detailed reasoning (if available)
        detailed = agent_response.get("detailed_reasoning", {})
        detailed_reasoning = {
            "technical_analysis": detailed.get("technical", ""),
            "fundamental_analysis": detailed.get("fundamental", ""),
            "sentiment_analysis": detailed.get("sentiment", ""),
            "risk_assessment": detailed.get("risk", "")
        }
        
        # Model info
        model_info = agent_response.get("model_info", {})
        model_name = model_info.get("model", "unknown")
        tokens_used = model_info.get("tokens", 0)
        response_time_ms = model_info.get("response_time_ms", 0)
        cost_usd = model_info.get("cost_usd", 0.0)
        
        # Create and save record
        record = create_ai_review_record(
            ticker=ticker,
            analysis_result=analysis_result,
            detailed_reasoning=detailed_reasoning,
            model_name=model_name,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            cost_usd=cost_usd
        )
        
        analysis_id = repo.save(record)
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "ticker": ticker,
            "action": analysis_result["action"],
            "conviction": analysis_result["conviction"],
            "has_changes": record.diff_from_previous.has_changes if record.diff_from_previous else False
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save agent response: {str(e)}"
        )
