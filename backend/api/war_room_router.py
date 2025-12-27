"""
War Room API Router

8-Agent War Room Debate System:
- Trader Agent (16%) - 기술적 분석  
- Risk Agent (16%) - 리스크 관리
- Macro Agent (14%) - 거시경제
- Institutional Agent (14%) - 스마트머니 추적
- News Agent (14%) - 뉴스 분석
- Chip War Agent (14%) - 반도체 경쟁 분석 ✨
- Analyst Agent (12%) - 펀더멘털 분석
- PM Agent (Weighted Voting) - 최종 중재자

API Endpoints:
- POST /api/war-room/debate - War Room 토론 실행
- GET /api/war-room/sessions - 세션 히스토리 조회

Author: AI Trading System
Date: 20 25-12-25 (Phase 24+: ChipWarAgent weight increased to 14%)
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
from backend.intelligence.dividend_risk_agent import DividendRiskAgent

# Constitutional Validator
from backend.constitution.constitution import Constitution

# Agent Logging
from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    ExecutionStatus,
    ErrorImpact
)
import traceback

logger = logging.getLogger(__name__)
agent_logger = AgentLogger("war-room-debate", "war-room")

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
    order_id: Optional[str] = None  # 🆕 REAL MODE


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
        self.chip_war_agent = ChipWarAgent()  # Phase 24
        self.dividend_risk_agent = DividendRiskAgent()  # Phase 21 ✨ NEW
        # PM agent is internal (weighted voting logic)

        self.vote_weights = {
            "trader": 0.15,       # 16% → 15% (technical analysis)
            "risk": 0.15,         # 16% → 15% (risk management)
           "analyst": 0.12,      # 12% → 12% (fundamental analysis)
            "macro": 0.14,        # 14% → 14% (macro economics)
            "institutional": 0.14, # 14% → 14% (smart money tracking)
            "news": 0.14,         # 14% → 14% (news sentiment)
            "chip_war": 0.14,     # 14% → 14% (semiconductor competition)
            "dividend_risk": 0.02, # ✨ NEW: 2% (dividend sustainability)
            "pm": 0.00            # PM uses weighted voting, no direct weight
        }

        logger.info("WarRoomEngine initialized with 9 agents (including ChipWar + DividendRisk)")
    
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

        # 7. Chip War Agent (14%)
        try:
            chip_war_vote = await self.chip_war_agent.analyze(ticker, context)
            votes.append(chip_war_vote)
            logger.info(f"🎮 Chip War Agent: {chip_war_vote['action']} ({chip_war_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Chip War Agent failed: {e}")

        # 8. Dividend Risk Agent (2%) - NEW: Phase 21 ✨
        try:
            dividend_risk_vote = await self.dividend_risk_agent.vote_for_war_room(ticker, context)
            votes.append(dividend_risk_vote)
            logger.info(f"💰 Dividend Risk Agent: {dividend_risk_vote['action']} ({dividend_risk_vote['confidence']:.0%})")
        except Exception as e:
            logger.error(f"❌ Dividend Risk Agent failed: {e}")

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

        # 액션 매핑 (다양한 액션을 표준 BUY/SELL/HOLD로 변환)
        action_mapping = {
            "BUY": "BUY",
            "SELL": "SELL",
            "HOLD": "HOLD",
            "MAINTAIN": "HOLD",  # 유지 = HOLD
            "REDUCE": "SELL",    # 축소 = SELL
            "INCREASE": "BUY",   # 증가 = BUY
            "TRIM": "SELL",      # 정리 = SELL
            "ADD": "BUY"         # 추가 = BUY
        }

        for vote in votes:
            agent = vote["agent"]
            raw_action = vote["action"]
            confidence = vote["confidence"]
            weight = self.vote_weights.get(agent, 0.1)

            # 액션 변환
            action = action_mapping.get(raw_action, "HOLD")

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
# Price Tracking (Phase 25.1: 24h Performance Measurement)
# ============================================================================

async def save_initial_price_tracking(
    session_id: int,
    ticker: str,
    consensus_action: str,
    consensus_confidence: float,
    debate_transcript: List[Dict[str, Any]],
    db: Any
) -> None:
    """
    Save initial price for 24-hour tracking (consensus + individual agent votes)

    Phase 25.1 + 25.3: Price tracking and agent performance tracking

    Args:
        session_id: War Room session ID
        ticker: Stock symbol
        consensus_action: BUY/SELL/HOLD
        consensus_confidence: Consensus confidence
        debate_transcript: List of agent votes with reasoning
        db: Database session
    """
    import os
    from backend.brokers.kis_broker import KISBroker
    import yfinance as yf

    try:
        # Get current price from KIS (Primary) or Yahoo Finance (Fallback)
        account_no = os.environ.get("KIS_ACCOUNT_NUMBER", "")
        is_virtual = os.environ.get("KIS_IS_VIRTUAL", "true").lower() == "true"
        current_price = None

        # Try KIS first
        if account_no:
            try:
                broker = KISBroker(account_no=account_no, is_virtual=is_virtual)
                price_data = broker.get_price(ticker, exchange="NASDAQ")
                if price_data:
                    current_price = price_data["current_price"]
                    logger.info(f"📊 Price from KIS: {ticker} @ ${current_price:.2f}")
            except Exception as e:
                logger.warning(f"KIS price fetch failed: {e}")

        # Fallback to Yahoo Finance
        if current_price is None:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    logger.info(f"📊 Price from Yahoo Finance (fallback): {ticker} @ ${current_price:.2f}")
                else:
                    logger.warning(f"Yahoo Finance returned empty data for {ticker}")
            except Exception as e:
                logger.warning(f"Yahoo Finance price fetch failed: {e}")

        # Skip if no price available
        if current_price is None:
            logger.warning(f"Failed to get price for {ticker} - skipping price tracking")
            return

        # Save consensus to price_tracking table
        from sqlalchemy import text

        insert_sql = text("""
            INSERT INTO price_tracking (
                session_id, ticker, initial_price, initial_timestamp,
                consensus_action, consensus_confidence, status, created_at
            ) VALUES (
                :session_id, :ticker, :initial_price, :initial_timestamp,
                :consensus_action, :consensus_confidence, 'PENDING', NOW()
            )
        """)

        db.execute(insert_sql, {
            "session_id": session_id,
            "ticker": ticker,
            "initial_price": current_price,
            "initial_timestamp": datetime.now(),
            "consensus_action": consensus_action,
            "consensus_confidence": consensus_confidence
        })
        db.commit()

        logger.info(f"💾 Price tracking saved: {ticker} @ ${current_price:.2f} (Session #{session_id})")

        # 🆕 Phase 25.3: Save individual agent votes
        await save_agent_votes_tracking(
            session_id=session_id,
            ticker=ticker,
            debate_transcript=debate_transcript,
            current_price=current_price,
            db=db
        )

    except Exception as e:
        logger.error(f"Failed to save price tracking: {e}", exc_info=True)
        # Don't fail the whole debate if price tracking fails
        pass


async def save_agent_votes_tracking(
    session_id: int,
    ticker: str,
    debate_transcript: List[Dict[str, Any]],
    current_price: float,
    db: Any
) -> None:
    """
    Save individual agent votes for 24-hour tracking

    Phase 25.3: Self-Learning Feedback Loop

    Args:
        session_id: War Room session ID
        ticker: Stock symbol
        debate_transcript: List of agent votes with reasoning
        current_price: Current stock price
        db: Database session
    """
    from sqlalchemy import text

    try:
        logger.info(f"💾 Saving {len(debate_transcript)} agent votes for tracking...")

        for vote in debate_transcript:
            agent_name = vote.get("agent")
            vote_action = vote.get("action")
            vote_confidence = vote.get("confidence", 0.5)
            vote_reasoning = vote.get("reasoning", "")

            # Skip PM agent (consensus is tracked separately in price_tracking)
            if agent_name == "pm":
                continue

            insert_sql = text("""
                INSERT INTO agent_vote_tracking (
                    session_id, agent_name, vote_action, vote_confidence, vote_reasoning,
                    ticker, initial_price, initial_timestamp, status, created_at
                ) VALUES (
                    :session_id, :agent_name, :vote_action, :vote_confidence, :vote_reasoning,
                    :ticker, :initial_price, :initial_timestamp, 'PENDING', NOW()
                )
            """)

            db.execute(insert_sql, {
                "session_id": session_id,
                "agent_name": agent_name,
                "vote_action": vote_action,
                "vote_confidence": vote_confidence,
                "vote_reasoning": vote_reasoning,
                "ticker": ticker,
                "initial_price": current_price,
                "initial_timestamp": datetime.now()
            })

        db.commit()
        logger.info(f"✅ Saved {len(debate_transcript) - 1} agent votes (excluding PM)")

    except Exception as e:
        logger.error(f"Failed to save agent votes tracking: {e}", exc_info=True)
        # Don't fail the whole debate if tracking fails
        pass


# ============================================================================
# KIS Order Execution (REAL MODE)
# ============================================================================

async def execute_kis_order(
    ticker: str,
    action: str,
    confidence: float,
    signal_id: int,
    session_id: int,
    db: Any
) -> Optional[Dict[str, Any]]:
    """
    Execute KIS order based on War Room consensus

    Args:
        ticker: Stock symbol
        action: BUY/SELL/HOLD
        confidence: Consensus confidence
        signal_id: Trading signal ID
        session_id: War Room session ID
        db: Database session

    Returns:
        Order result dictionary or None
    """
    import os
    from backend.brokers.kis_broker import KISBroker
    from backend.database.models import Order

    # HOLD는 주문 실행하지 않음
    if action == "HOLD":
        logger.info(f"⏸️ HOLD action - No order execution for {ticker}")
        return None

    try:
        # 1. Initialize KIS Broker
        account_no = os.environ.get("KIS_ACCOUNT_NUMBER", "")
        is_virtual = os.environ.get("KIS_IS_VIRTUAL", "true").lower() == "true"

        if not account_no:
            logger.error("KIS_ACCOUNT_NUMBER not set in environment")
            return None

        broker = KISBroker(
            account_no=account_no,
            is_virtual=is_virtual
        )

        # 2. Get current price
        price_data = broker.get_price(ticker, exchange="NASDAQ")
        if not price_data:
            logger.error(f"Failed to get price for {ticker}")
            return None

        current_price = price_data["current_price"]

        # 3. Calculate order quantity
        # Risk management: Max 5% of portfolio per position
        balance = broker.get_account_balance()
        if not balance:
            logger.error("Failed to get account balance")
            return None

        total_value = balance.get("total_value", 0) + balance.get("cash", 0)
        max_position_size = total_value * 0.05  # 5% max

        # Adjust by confidence (higher confidence = larger position)
        position_size = max_position_size * confidence
        quantity = int(position_size / current_price)

        if quantity < 1:
            logger.warning(f"Calculated quantity too small: {quantity}")
            return None

        # 4. Execute order
        logger.info(f"📋 Order: {action} {quantity} shares of {ticker} @ ${current_price:.2f}")

        order_result = None
        if action == "BUY":
            order_result = broker.buy_market_order(ticker, quantity)
        elif action == "SELL":
            # Check if we have position
            positions = balance.get("positions", [])
            ticker_position = next((p for p in positions if p["symbol"] == ticker), None)

            if not ticker_position or ticker_position["quantity"] < quantity:
                logger.warning(f"Insufficient {ticker} position for SELL")
                return None

            order_result = broker.sell_market_order(ticker, quantity)

        if not order_result:
            logger.error(f"Order execution failed for {ticker}")
            return None

        # 5. Save order to database
        order_id = order_result.get("order_id") or order_result.get("ODNO", "")

        order = Order(
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=current_price,
            order_type="MARKET",
            status="PENDING",
            broker="KIS",
            order_id=order_id,
            signal_id=signal_id,
            created_at=datetime.now()
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        logger.info(f"✅ Order saved to DB: {order.id}")

        return {
            "order_id": order_id,
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": current_price,
            "status": "PENDING"
        }

    except Exception as e:
        logger.error(f"Failed to execute KIS order: {e}", exc_info=True)
        return None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/debate", response_model=DebateResponse)
async def run_war_room_debate(request: DebateRequest, execute_trade: bool = False):
    """
    War Room 토론 실행 (7 agents)

    Args:
        request: DebateRequest with ticker
        execute_trade: If True, execute KIS order after constitutional validation

    Response:
        {
            "session_id": int,
            "ticker": "AAPL",
            "votes": [...],
            "consensus": {
                "action": "BUY",
                "confidence": 0.75
            },
            "signal_id": int or null,
            "order_id": str or null  # 🆕 REAL MODE
        }
    """
    start_time = datetime.now()
    ticker = request.ticker.upper()
    task_id = f"war-room-{ticker}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(f"🏛️ War Room debate requested for {ticker} (execute_trade={execute_trade})")

    # 1. Debate Engine 실행
    engine = get_war_room_engine()
    votes, pm_decision = await engine.run_debate(ticker)

    # 2. Constitutional 검증
    constitution = Constitution()

    # 제안서 생성
    proposal = {
        "ticker": ticker,
        "action": pm_decision["consensus_action"],
        "confidence": pm_decision["consensus_confidence"],
        "is_approved": True,  # War Room 데이터 축적 모드에서는 자동 승인
        "position_value": 5000,  # 데이터 축적 모드: 임의값 (MIN_POSITION_SIZE_USD $1,000 이상)
    }

    # Context 생성 (간소화 버전)
    context = {
        "total_capital": 100000,  # TODO: 실제 계좌 잔고에서 가져오기
        "daily_trades": 0,  # TODO: 오늘 거래 횟수
        "weekly_trades": 0,  # TODO: 이번주 거래 횟수
    }

    # Constitutional 검증 실행
    # 실전 거래(execute_trade=True)일 때만 엄격한 검증, 데이터 축적 모드에서는 기본 검증만
    is_valid, violations, violated_articles = constitution.validate_proposal(
        proposal=proposal,
        context=context,
        skip_allocation_rules=not execute_trade  # 데이터 축적 모드에서는 배분 규칙 스킵
    )

    logger.info(f"⚖️ Constitutional validation: {is_valid}")
    if not is_valid:
        logger.warning(f"⚠️ Violations: {violations}")
        logger.warning(f"⚠️ Violated articles: {violated_articles}")

    # 3. DB에 세션 저장
    db = get_sync_session()

    try:
        # AIDebateSession에 저장
        # Generate unique debate_id
        debate_id = f"debate-{ticker}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        session = AIDebateSession(
            ticker=ticker,
            debate_id=debate_id,
            votes=votes,  # Store votes as list of dicts (JSONB handles serialization)
            consensus_action=pm_decision["consensus_action"],  # PM output matches DB column
            consensus_confidence=pm_decision["consensus_confidence"],
            constitutional_valid=is_valid,  # Constitutional 검증 결과 저장
            created_at=datetime.now(),
            completed_at=datetime.now()
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"💾 War Room session saved: ID {session.id}")

        # 3. 🆕 Phase 25.1 + 25.3: Save initial price + agent votes for 24h tracking
        await save_initial_price_tracking(
            session_id=session.id,
            ticker=ticker,
            consensus_action=pm_decision["consensus_action"],
            consensus_confidence=pm_decision["consensus_confidence"],
            debate_transcript=votes,  # 🆕 Phase 25.3: Include agent votes
            db=db
        )

        # 4. Signal 생성 (confidence >= 0.7)
        signal_id = None
        order_id = None

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

            signal_id = signal.id
            logger.info(f"📊 Trading signal created: ID {signal_id}")

            # 4. 🆕 REAL MODE: Execute KIS Order
            if execute_trade and is_valid:
                logger.info(f"💼 Executing trade for {ticker}: {pm_decision['consensus_action']}")
                order_result = await execute_kis_order(
                    ticker=ticker,
                    action=pm_decision["consensus_action"],
                    confidence=pm_decision["consensus_confidence"],
                    signal_id=signal_id,
                    session_id=session.id,
                    db=db
                )

                if order_result and "order_id" in order_result:
                    order_id = order_result["order_id"]
                    logger.info(f"✅ Order executed: {order_id}")
                else:
                    logger.warning(f"⚠️ Order execution failed or skipped")

        # 5. Response 생성
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
            constitutional_valid=is_valid,  # Use local variable instead of session attribute
            order_id=order_id  # 🆕 REAL MODE
        )

        # Log successful execution
        agent_logger.log_execution(ExecutionLog(
            timestamp=datetime.now(),
            agent="war-room/war-room-debate",
            task_id=task_id,
            status=ExecutionStatus.SUCCESS,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            input={
                "ticker": ticker,
                "execute_trade": execute_trade
            },
            output={
                "consensus_action": pm_decision["consensus_action"],
                "consensus_confidence": pm_decision["consensus_confidence"],
                "signal_id": signal_id,
                "agent_votes": len(votes),
                "constitutional_valid": is_valid  # Use local variable
            }
        ))

        return response

    except Exception as e:
        logger.error(f"❌ War Room debate failed: {e}", exc_info=True)
        
        # Log error
        agent_logger.log_error(ErrorLog(
            timestamp=datetime.now(),
            agent="war-room/war-room-debate",
            task_id=task_id,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "stack": traceback.format_exc(),
                "context": {"ticker": ticker, "execute_trade": execute_trade}
            },
            impact=ErrorImpact.CRITICAL,
            recovery_attempted=False
        ))
        
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
            # Parse debate_transcript to get full vote details with reasoning
            votes_detail = []
            if s.debate_transcript:
                try:
                    votes_detail = json.loads(s.debate_transcript)
                except:
                    votes_detail = []

            # Parse votes from JSONB (Handle both Dict and List formats)
            # Parse votes from JSONB (Handle both Dict and List formats)
            votes_data = {}
            raw_votes = s.votes

            # 1. Handle stringified JSON (legacy data)
            if isinstance(raw_votes, str):
                try:
                    raw_votes = json.loads(raw_votes)
                except Exception:
                    raw_votes = []
            
            # 2. Handle Dict (already in format)
            if isinstance(raw_votes, dict):
                votes_data = raw_votes
            
            # 3. Handle List (convert to Dict keyed by agent)
            elif isinstance(raw_votes, list):
                for v in raw_votes:
                    if isinstance(v, dict) and "agent" in v:
                        votes_data[v["agent"]] = v
            
            result.append({
                "id": s.id,
                "ticker": s.ticker,
                "consensus_action": s.consensus_action,
                "consensus_confidence": s.consensus_confidence,
                "votes": votes_data,  # Use JSONB votes column
                "votes_detail": votes_detail,  # 🆕 Full vote details with reasoning
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "duration_seconds": s.duration_seconds,
                "constitutional_valid": True  # Default to True for historical records
            })
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        db.close()


@router.post("/debate-and-execute")
async def debate_and_execute_trade(
    request: DebateRequest,
    dry_run: bool = True  # 기본값: 시뮬레이션
):
    """
    War Room 토론 → 실거래 실행

    Args:
        ticker: 종목 코드
        dry_run: True = 시뮬레이션만, False = 실제 주문 (모의투자)

    Returns:
        토론 결과 + 체결 결과
    """
    ticker = request.ticker.upper()

    # Step 1: War Room 토론
    logger.info(f"🎭 War Room 토론 + 실거래 실행: {ticker}")
    debate_result = await run_war_room_debate(request)

    # Step 2: 실거래 실행
    from backend.trading.war_room_executor import WarRoomExecutor

    executor = WarRoomExecutor(kis_broker=None)  # DRY RUN용

    execution_result = await executor.execute_war_room_decision(
        ticker=ticker,
        consensus_action=debate_result.consensus["action"],
        consensus_confidence=debate_result.consensus["confidence"],
        votes=[v.dict() for v in debate_result.votes],
        dry_run=dry_run
    )

    # Step 3: 결과 통합
    result = {
        "debate": debate_result.dict(),
        "execution": execution_result
    }

    logger.info(f"✅ 토론 + 실행 완료: {ticker} {execution_result['status']}")

    return result


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
