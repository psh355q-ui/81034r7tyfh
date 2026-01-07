from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
import logging

from backend.ai.reasoning.engine import reasoning_engine
from backend.ai.reasoning.models import MarketThesis
from backend.ai.skills.common.logging_decorator import log_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reasoning", tags=["Deep Reasoning"])

class AnalyzeRequest(BaseModel):
    ticker: str
    news_context: str
    technical_summary: dict = {"rsi": 50, "trend": "Unknown"} # Placeholder default
    use_mock: bool = False  # Add mock mode support
    enable_macro_check: bool = False  # 매크로 정합성 체크
    enable_skeptic: bool = False  # 반박논리추가

@router.post("/analyze")
@log_endpoint("reasoning", "system")
async def analyze_ticker_manually(request: AnalyzeRequest):
    """
    Trigger Deep Reasoning on a ticker with provided context (Manual/Dev Mode).
    
    Now includes auto-save to database with source='deep_reasoning'
    
    Optional advanced features:
    - enable_macro_check: Add macro consistency check
    - enable_skeptic: Add skeptic challenge (반박논리)
    """
    if not reasoning_engine:
        raise HTTPException(status_code=503, detail="Reasoning Engine not initialized (Check API Key)")

    # Base analysis
    thesis = await reasoning_engine.analyze_ticker(
        ticker=request.ticker,
        news_context=request.news_context,
        technical_data=request.technical_summary,
        use_mock=request.use_mock
    )
    
    if not thesis:
        raise HTTPException(status_code=500, detail="Failed to generate thesis")
    
    # 💾 Save to database (Phase 2: Signal Generator Integration)
    if thesis.direction in ["BUY", "SELL", "HOLD"]:  # Save ALL for history
        try:
            from backend.database.models import TradingSignal as DBTradingSignal
            from backend.database.repository import get_sync_session
            from datetime import datetime
            import inspect
            
            db = get_sync_session()
            
            # Handle if get_sync_session returns a generator (safety check)
            if inspect.isgenerator(db):
                db = next(db)
            
            try:
                # Ensure we have a valid session
                if not hasattr(db, "add"):
                     logger.error(f"Invalid DB session object type: {type(db)}")
                     raise ValueError("Invalid DB session")

                signal = DBTradingSignal(
                    analysis_id=None,  # Deep Reasoning is independent
                    ticker=request.ticker,
                    action=thesis.direction,
                    signal_type="DEEP_REASONING",  # Correct signal type
                    confidence=thesis.final_confidence_score,
                    reasoning=thesis.summary,
                    source="deep_reasoning",  # 🆕 Source tracking
                    generated_at=datetime.now()
                )
                db.add(signal)
                db.commit()
                db.refresh(signal)
                
                logger.info(f"📊 Deep Reasoning signal saved: {request.ticker} {thesis.direction} (ID: {signal.id})")
            
            except Exception as db_error:
                logger.error(f"Failed to save Deep Reasoning signal: {db_error}")
                # Don't fail the request if DB save fails
            finally:
                if hasattr(db, "close"):
                    db.close()
        
        except Exception as import_error:
            logger.error(f"Failed to import DB models or session: {import_error}")
    
    # Prepare response
    response = thesis.dict()
    
    # Optional: Macro Consistency Check
    if request.enable_macro_check:
        if request.use_mock:
            # Mock macro warning
            response["macro_warning"] = """# 📊 매크로 정합성 체크 리포트 (Mock)

## 1. 🟡 정책 모순 (Policy Contradiction)

**심각도**: MEDIUM (점수: 60%)

**모순 설명**: GDP 전망은 상향되었으나 금리 경로는 하향되었습니다.

**데이터**:
- gdp_forecast_change: 0.5 (UP)
- rate_path_change: -0.3 (DOWN)

**가능한 설명**:
- Fed의 정책 커뮤니케이션 혼란
- 선거를 앞둔 정치적 압력
- 글로벌 요인 (다른 중앙은행 완화)

**역사적 선례**:
- 2023년 SVB 사태: 긴축과 유동성 공급 동시 진행

**시장 영향**: 정책 불확실성 증가, 달러 약세

---
"""
            response["macro_contradictions_count"] = 1
        else:
            try:
                from backend.ai.reasoning.macro_consistency_checker import MacroConsistencyChecker
                
                macro_checker = MacroConsistencyChecker()
                # Dummy macro data for now (in production, fetch real data)
                macro_data = {
                    "gdp_growth": 2.3,
                    "fed_rate_change": -0.25,
                    "unemployment_rate": 3.7,
                    "cpi_yoy": 3.2,
                    "vix": 13.5,
                    "credit_spread": 1.2,
                }
                
                contradictions = await macro_checker.detect_contradictions(macro_data)
                
                if contradictions:
                    macro_report = macro_checker.format_report_korean(contradictions)
                    response["macro_warning"] = macro_report
                    response["macro_contradictions_count"] = len(contradictions)
                    logger.info(f"Macro check: {len(contradictions)} contradictions found")
                else:
                    response["macro_warning"] = "✅ 현재 감지된 매크로 모순이 없습니다."
                    response["macro_contradictions_count"] = 0
            except Exception as e:
                logger.error(f"Macro check failed: {e}")
                response["macro_warning"] = f"매크로 체크 실패: {str(e)}"
    
    # Optional: Skeptic Challenge
    if request.enable_skeptic:
        if request.use_mock:
            # Mock skeptic challenge
            ticker_name = request.ticker
            response["skeptic_challenge"] = f"""# 😈 회의론적 분석 (Skeptic Challenge) - Mock

## {ticker_name}에 대한 반대 의견

### 🔴 주요 약점 (Critical Weaknesses)

1. **과대평가된 성장 기대**
   - 현재 밸류에이션은 완벽한 실행을 전제로 함
   - 경쟁자들의 기술 추격 속도가 예상보다 빠름
   - 시장이 간과한 실행 리스크 존재

2. **매크로 환경 악화 가능성**
   - 금리 인하 지연 시 성장주 전반 타격
   - 경기 둔화 시 소비자 지출 감소
   - 달러 강세 시 해외 매출 타격

3. **숨겨진 구조적 문제**
   - 규제 리스크 과소평가
   - 경영진의 과신 가능성
   - 단기 실적 압박 증가

### 💡 회의적 시나리오

만약 다음 분기 실적이 기대치를 10% 밑돌면:
- 주가 20% 조정 가능
- 시장 센티먼트 급격히 악화
- 기술적 지지선 붕괴 위험

### 🎯 추천사항: 🟡 CAUTION (신중 접근)

**이유**: Bull Case는 타당하나, 시장이 간과한 리스크가 존재합니다.
"""
            response["skeptic_recommendation"] = "CAUTION"
        else:
            try:
                from backend.ai.reasoning.skeptic_agent import SkepticAgent
                
                skeptic = SkepticAgent()
                
                # Prepare consensus analysis dict for SkepticAgent
                consensus_analysis = {
                    "action": thesis.direction,
                    "confidence": thesis.final_confidence_score,
                    "reasoning": thesis.summary
                }
                
                skeptic_analysis = await skeptic.analyze(
                    ticker=request.ticker,
                    consensus_analysis=consensus_analysis,
                    market_data={}
                )
                
                skeptic_report = skeptic.format_report_korean(skeptic_analysis)
                response["skeptic_challenge"] = skeptic_report
                response["skeptic_recommendation"] = skeptic_analysis.recommendation.value
                logger.info(f"Skeptic analysis: {skeptic_analysis.recommendation}")
            except Exception as e:
                logger.error(f"Skeptic analysis failed: {e}")
                response["skeptic_challenge"] = f"회의론적 분석 실패: {str(e)}"
        
    return response

@router.get("/health")
@log_endpoint("reasoning", "system")
def health_check():
    return {"status": "active", "engine": "ready" if reasoning_engine else "disabled"}


@router.get("/history")
@log_endpoint("reasoning", "history")
def get_analysis_history(limit: int = 20):
    """
    Get recent Deep Reasoning analysis history from database.
    """
    try:
        from backend.database.repository import get_sync_session
        from backend.database.models import TradingSignal as DBTradingSignal
        from sqlalchemy import desc
        import inspect
        
        db = get_sync_session()
        if inspect.isgenerator(db):
            db = next(db)
            
        try:
            # Fetch signals created by deep_reasoning
            signals = (
                db.query(DBTradingSignal)
                .filter(DBTradingSignal.source == "deep_reasoning")
                .order_by(desc(DBTradingSignal.generated_at))
                .limit(limit)
                .all()
            )
            
            # Format response
            history = []
            for s in signals:
                history.append({
                    "id": s.id,
                    "ticker": s.ticker,
                    "action": s.action,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning,
                    "date": s.generated_at.isoformat() if s.generated_at else None,
                    "type": s.signal_type
                })
                
            return history
            
        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if hasattr(db, "close"):
                db.close()
                
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []
