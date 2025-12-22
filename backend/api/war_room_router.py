"""
War Room API Router

8-Agent War Room Debate System:
- Trader Agent (14%) - 기술적 분석
- Risk Agent (18%) - 리스크 관리
- Analyst Agent (13%) - 펀더멘털 분석
- Macro Agent (16%) - 거시경제
- Institutional Agent (15%) - 스마트머니 추적
- News Agent (14%) - 뉴스 분석
- Chip War Agent (12%) - 반도체 경쟁 분석 (NEW)
- PM Agent (18%) - 최종 중재자

API Endpoints:
- POST /api/war-room/debate - War Room 토론 실행
- GET /api/war-room/sessions - 세션 히스토리 조회

Author: AI Trading System
Date: 2025-12-23 (Phase 24: ChipWarAgent added)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging

from backend.database.models import AIDebateSession, TradingSignal
from backend.database.repository import get_sync_session

# Import all 8 agents
from backend.ai.debate.news_agent import NewsAgent
from backend.ai.debate.trader_agent import TraderAgent
from backend.ai.debate.risk_agent import RiskAgent
from backend.ai.debate.analyst_agent import AnalystAgent
from backend.ai.debate.macro_agent import MacroAgent
from backend.ai.debate.institutional_agent import InstitutionalAgent
from backend.ai.debate.chip_war_agent import ChipWarAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/war-room", tags=["war-room"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DebateRequest(BaseModel):
    """War Room 토론 요청"""
    ticker: str


class AgentVote(BaseModel):
    """개별 Agent 투표"""
    agent: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str


class DebateResponse(BaseModel):
    """War Room 토론 결과"""
    session_id: int
    ticker: str
    votes: List[AgentVote]
    consensus: Dict[str, Any]
    signal_id: Optional[int] = None
    constitutional_valid: bool = True


# ============================================================================
# War Room Debate Engine
# ============================================================================

class WarRoomEngine:
    """8-Agent War Room Debate Engine"""

    def __init__(self):
        """Initialize all 8 agents"""
        # Initialize real agents
        self.trader_agent = TraderAgent()
        self.risk_agent = RiskAgent()
        self.analyst_agent = AnalystAgent()
        self.macro_agent = MacroAgent()
        self.institutional_agent = InstitutionalAgent()
        self.news_agent = NewsAgent()
        self.chip_war_agent = ChipWarAgent()  # NEW: Phase 24
        # PM agent is internal (weighted voting logic)

        self.vote_weights = {
            "trader": 0.14,
            "risk": 0.18,
            "analyst": 0.13,
            "macro": 0.16,
            "institutional": 0.15,
            "news": 0.14,
            "chip_war": 0.12,  # NEW: Phase 24
            "pm": 0.18  # 중재자
        }

        logger.info("WarRoomEngine initialized with 8 agents (including ChipWarAgent)")
    
    async def run_debate(self, ticker: str, context: Dict[str, Any] = None) -> tuple[List[Dict], Dict]:
        """
        War Room 토론 실행
        
        Args:
            ticker: 분석할 티커
            context: 추가 컨텍스트
        
        Returns:
            (votes, pm_decision)
        """
        logger.info(f"🏛️ War Room debate starting for {ticker}")
        
        votes = []

        # Collect votes from all 7 agents (順서: 중요도 순)
        # 1. Risk Agent (18%)
        try:
            risk_vote = await self.risk_agent.analyze(ticker, context)
            votes.append(risk_vote)
            logger.info(f"🛡️ Risk Agent: {risk_vote['action']} ({risk_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Risk Agent failed: {e}")

        # 2. Macro Agent (16%)
        try:
            macro_vote = await self.macro_agent.analyze(ticker, context)
            votes.append(macro_vote)
            logger.info(f"🌏 Macro Agent: {macro_vote['action']} ({macro_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Macro Agent failed: {e}")

        # 3. Institutional Agent (15%)
        try:
            institutional_vote = await self.institutional_agent.analyze(ticker, context)
            votes.append(institutional_vote)
            logger.info(f"🏦 Institutional Agent: {institutional_vote['action']} ({institutional_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Institutional Agent failed: {e}")

        # 4. Trader Agent (14%)
        try:
            trader_vote = await self.trader_agent.analyze(ticker, context)
            votes.append(trader_vote)
            logger.info(f"📈 Trader Agent: {trader_vote['action']} ({trader_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Trader Agent failed: {e}")

        # 5. News Agent (14%)
        try:
            news_vote = await self.news_agent.analyze(ticker, context)
            votes.append(news_vote)
            logger.info(f"📰 News Agent: {news_vote['action']} ({news_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ News Agent failed: {e}")

        # 6. Analyst Agent (13%)
        try:
            analyst_vote = await self.analyst_agent.analyze(ticker, context)
            votes.append(analyst_vote)
            logger.info(f"📊 Analyst Agent: {analyst_vote['action']} ({analyst_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Analyst Agent failed: {e}")

        # 7. Chip War Agent (12%) - NEW: Phase 24
        try:
            chip_war_vote = await self.chip_war_agent.analyze(ticker, context)
            votes.append(chip_war_vote)
            logger.info(f"🎮 Chip War Agent: {chip_war_vote['action']} ({chip_war_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Chip War Agent failed: {e}")

        # 8. PM Agent 최종 결정 (18%)
        pm_decision = self._pm_arbitrate(votes)
        
        logger.info(f"👔 PM Decision: {pm_decision['consensus_action']} "
                   f"(confidence: {pm_decision['consensus_confidence']:.0%})")
        
        return votes, pm_decision
    

    
    def _pm_arbitrate(self, votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        PM Agent 중재 - 최종 합의 결정
        
        - 가중 투표로 합의 도출
        - 충돌 시 PM이 최종 결정
        """
        if not votes:
            return {
                "consensus_action": "HOLD",
                "consensus_confidence": 0.5,
                "summary": "투표 없음"
            }
        
        # 가중 투표 집계
        action_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        
        for vote in votes:
            agent = vote["agent"]
            action = vote["action"]
            confidence = vote["confidence"]
            weight = self.vote_weights.get(agent, 0.1)
            
            action_scores[action] += weight * confidence
        
        # 최고 점수 액션 선택
        consensus_action = max(action_scores, key=action_scores.get)
        
        # 합의 신뢰도 계산 (최고 점수 / 전체 점수 합)
        total_score = sum(action_scores.values())
        consensus_confidence = action_scores[consensus_action] / total_score if total_score > 0 else 0.5
        
        # 투표 요약
        vote_summary = {a: f"{s:.2f}" for a, s in action_scores.items()}
        
        return {
            "consensus_action": consensus_action,
            "consensus_confidence": consensus_confidence,
            "summary": f"War Room 합의: {vote_summary}",
            "vote_distribution": action_scores
        }


# Global instance
_war_room_engine = None

def get_war_room_engine() -> WarRoomEngine:
    """Get or create War Room Engine"""
    global _war_room_engine
    if _war_room_engine is None:
        _war_room_engine = WarRoomEngine()
    return _war_room_engine


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/debate", response_model=DebateResponse)
async def run_war_room_debate(request: DebateRequest):
    """
    War Room 토론 실행 (7 agents)
    
    Response:
        {
            "session_id": int,
            "ticker": "AAPL",
            "votes": [...],
            "consensus": {
                "action": "BUY",
                "confidence": 0.75
            },
            "signal_id": int or null
        }
    """
    ticker = request.ticker.upper()
    
    logger.info(f"🏛️ War Room debate requested for {ticker}")
    
    # 1. Debate Engine 실행
    engine = get_war_room_engine()
    votes, pm_decision = await engine.run_debate(ticker)
    
    # 2. DB에 세션 저장
    db = get_sync_session()
    
    try:
        # AIDebateSession에 저장
        session = AIDebateSession(
            ticker=ticker,
            consensus_action=pm_decision["consensus_action"],
            consensus_confidence=pm_decision["consensus_confidence"],
            trader_vote=next((v["action"] for v in votes if v["agent"] == "trader"), None),
            risk_vote=next((v["action"] for v in votes if v["agent"] == "risk"), None),
            analyst_vote=next((v["action"] for v in votes if v["agent"] == "analyst"), None),
            macro_vote=next((v["action"] for v in votes if v["agent"] == "macro"), None),
            institutional_vote=next((v["action"] for v in votes if v["agent"] == "institutional"), None),
            news_vote=next((v["action"] for v in votes if v["agent"] == "news"), None),
            chip_war_vote=next((v["action"] for v in votes if v["agent"] == "chip_war"), None),  # 🆕 Phase 24
            pm_vote=pm_decision["consensus_action"],
            debate_transcript=json.dumps(votes, ensure_ascii=False),
            constitutional_valid=True,  # TODO: Constitution Validator 통합
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"💾 War Room session saved: ID {session.id}")
        
        # 3. Signal 생성 (confidence >= 0.7)
        signal_id = None
        if pm_decision["consensus_confidence"] >= 0.7:
            signal = TradingSignal(
                analysis_id=None,  # War Room은 analysis와 독립
                ticker=ticker,
                action=pm_decision["consensus_action"],
                signal_type="CONSENSUS",
                confidence=pm_decision["consensus_confidence"],
                reasoning=pm_decision.get("summary", "War Room 합의"),
                source="war_room",  # 🆕 출처 표시
                generated_at=datetime.now()
            )
            db.add(signal)
            db.commit()
            db.refresh(signal)
            
            # signal_id 연결
            session.signal_id = signal.id
            db.commit()
            
            signal_id = signal.id
            logger.info(f"📊 Trading signal created: ID {signal_id}")
        
        # 4. Response 생성
        response = DebateResponse(
            session_id=session.id,
            ticker=ticker,
            votes=[AgentVote(**v) for v in votes],
            consensus={
                "action": pm_decision["consensus_action"],
                "confidence": pm_decision["consensus_confidence"],
                "summary": pm_decision.get("summary", "")
            },
            signal_id=signal_id,
            constitutional_valid=session.constitutional_valid
        )
        
        return response
    
    except Exception as e:
        logger.error(f"❌ War Room debate failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")
    
    finally:
        db.close()


@router.get("/sessions")
async def get_debate_sessions(
    ticker: str = None,
    limit: int = 20
):
    """War Room 세션 히스토리 조회"""
    db = get_sync_session()
    
    try:
        query = db.query(AIDebateSession)
        
        if ticker:
            query = query.filter(AIDebateSession.ticker == ticker.upper())
        
        sessions = query.order_by(AIDebateSession.created_at.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for s in sessions:
            result.append({
                "id": s.id,
                "ticker": s.ticker,
                "consensus_action": s.consensus_action,
                "consensus_confidence": s.consensus_confidence,
                "votes": {
                    "trader": s.trader_vote,
                    "risk": s.risk_vote,
                    "analyst": s.analyst_vote,
                    "macro": s.macro_vote,
                    "institutional": s.institutional_vote,
                    "news": s.news_vote,
                    "chip_war": s.chip_war_vote,  # 🆕 Phase 24
                    "pm": s.pm_vote
                },
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "signal_id": s.signal_id
            })
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        db.close()


@router.get("/health")
async def war_room_health():
    """War Room 시스템 헬스 체크"""
    try:
        engine = get_war_room_engine()
        return {
            "status": "healthy",
            "agents_loaded": 8,  # Phase 24: ChipWarAgent added
            "agents": ["trader", "risk", "analyst", "macro", "institutional", "news", "chip_war", "pm"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
