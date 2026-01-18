"""
System & Risk Status Router

Previously mock data - now using real implementations.
Uses RiskSkill and actual system metrics.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import psutil
import os

from sqlalchemy.orm import Session
from backend.database.repository import get_sync_session
from backend.database.models import TradingSignal
from backend.ai.skills.common.logging_decorator import log_endpoint

router = APIRouter()
logger = logging.getLogger(__name__)

# ==========================================
# Dependency Injection
# ==========================================

def get_db():
    """Database session dependency"""
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()



# ==========================================
# Risk Status API - Real Implementation
# ==========================================

@router.get("/api/risk/status")
@log_endpoint("unknown", "system")
async def get_risk_status(db: Session = Depends(get_db)):
    """
    Get real risk status from portfolio positions
    """
    try:
        # Get active positions
        active_signals = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).all()
        
        # Calculate exposure
        total_exposure = 0.0
        position_count = len(active_signals)
        
        for signal in active_signals:
            quantity = getattr(signal, 'quantity', 10)
            position_value = (signal.entry_price or 0) * quantity
            total_exposure += position_value
        
        INITIAL_CAPITAL = 100000.0
        exposure_pct = total_exposure / INITIAL_CAPITAL if INITIAL_CAPITAL > 0 else 0
        
        # Determine risk level
        if exposure_pct > 0.8:
            risk_level = "HIGH"
        elif exposure_pct > 0.5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "status": "normal" if risk_level != "HIGH" else "warning",
            "risk_level": risk_level,
            "exposure_pct": round(exposure_pct, 4),
            "active_positions": position_count,
            "total_exposure": round(total_exposure, 2),
            "available_capital": round(INITIAL_CAPITAL - total_exposure, 2),
            "active_alerts": 0 if risk_level == "LOW" else (1 if risk_level == "MEDIUM" else 2),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting risk status: {e}")
        return {
            "status": "unknown",
            "risk_level": "UNKNOWN",
            "exposure_pct": 0.0,
            "active_alerts": 0,
            "updated_at": datetime.now().isoformat(),
            "error": str(e)
        }


# ==========================================
# System Info API - Real Implementation
# ==========================================

@router.get("/api/system/info")
@log_endpoint("unknown", "system")
async def get_system_info():
    """
    Get real system information
    """
    try:
        # Get process info
        process = psutil.Process()
        
        # Calculate uptime
        start_time = datetime.fromtimestamp(process.create_time())
        uptime = (datetime.now() - start_time).total_seconds()
        
        return {
            "version": "1.0.0",
            "status": "operational",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime_seconds": int(uptime),
            "start_time": start_time.isoformat(),
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "memory_usage": process.memory_percent(),
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "active_threads": process.num_threads(),
            "components": {
                "database": True,
                "redis": True,  # TODO: Check actual Redis connection
                "kis_broker": os.getenv("KIS_APP_KEY") is not None,
                "ai_models": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "version": "1.0.0",
            "status": "operational",
            "uptime_seconds": 0,
            "error": str(e)
        }


# ==========================================
# Alerts API - Real Implementation
# ==========================================

@router.get("/api/alerts")
@log_endpoint("unknown", "system")
async def get_alerts(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get real alerts from system monitoring
    """
    alerts = []
    
    try:
        # Check for positions with significant losses
        active_signals = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).all()
        
        for signal in active_signals:
            # This would need current prices in production
            # For now, just log position age alerts
            days_held = (datetime.now() - signal.generated_at).days
            
            if days_held > 30:
                alerts.append({
                    "id": f"position-age-{signal.id}",
                    "type": "WARNING",
                    "ticker": signal.ticker,
                    "message": f"{signal.ticker} position held for {days_held} days",
                    "timestamp": datetime.now().isoformat(),
                    "read": False
                })
        
        # System health alerts
        memory_pct = psutil.virtual_memory().percent
        if memory_pct > 80:
            alerts.append({
                "id": "system-memory",
                "type": "WARNING",
                "message": f"High memory usage: {memory_pct:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "read": False
            })
        
        cpu_pct = psutil.cpu_percent(interval=0.1)
        if cpu_pct > 80:
            alerts.append({
                "id": "system-cpu",
                "type": "WARNING",
                "message": f"High CPU usage: {cpu_pct:.1f}%",
                "timestamp": datetime.now().isoformat(),
                "read": False
            })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        alerts.append({
            "id": "error",
            "type": "ERROR",
            "message": f"Error fetching alerts: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "read": False
        })
    
    return {"recent": alerts[:limit], "total": len(alerts)}


# ==========================================
# Analysis APIs - Connect to Real AI Pipeline
# ==========================================

@router.post("/api/analyze")
@log_endpoint("unknown", "system")
async def analyze_ticker(request: Dict[str, Any]):
    """
    Hybrid Analysis: TradingAgent (price) + War Room (3+1 agents with news)

    Returns ALL agent opinions for transparency:
    - TradingAgent: Price-based technical analysis
    - Trader Agent MVP: Price action & momentum
    - Risk Agent MVP: Risk assessment & position sizing
    - Analyst Agent MVP: News & fundamentals
    - PM Agent MVP: Final decision maker

    This ensures consistent results even during market holidays when news is still available.
    """
    ticker = request.get("ticker", "").upper()

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    start_time = datetime.now()

    try:
        # Import agents
        from backend.ai.trading_agent import TradingAgent
        from backend.ai.mvp.war_room_mvp import WarRoomMVP
        from backend.database.models import TradingSignal as DBTradingSignal
        from backend.database.repository import get_sync_session

        # Initialize War Room
        war_room = WarRoomMVP()

        # Step 1: Fetch recent news for this ticker
        logger.info(f"🔍 Starting hybrid analysis for {ticker}")

        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.database.models import NewsArticle, NewsTickerRelevance, NewsAnalysis
        from datetime import timedelta

        db = get_sync_session()
        news_headlines = []
        news_sentiment = []

        try:
            # Get recent news (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)

            stmt = (
                select(NewsTickerRelevance)
                .options(
                    selectinload(NewsTickerRelevance.article).selectinload(NewsArticle.analysis)
                )
                .join(NewsArticle)
                .filter(
                    NewsTickerRelevance.ticker == ticker,
                    NewsArticle.published_date >= cutoff_date
                )
                .order_by(NewsTickerRelevance.relevance_score.desc())
                .limit(10)
            )

            result = db.execute(stmt)
            ticker_news = result.scalars().all()

            for rel in ticker_news:
                article = rel.article
                if article:
                    news_headlines.append(article.title)
                    if article.analysis:
                        news_sentiment.append(article.analysis.sentiment_overall)

            logger.info(f"📰 Found {len(news_headlines)} news articles for {ticker}")

        except Exception as news_error:
            logger.warning(f"Failed to fetch news for {ticker}: {news_error}")
        finally:
            db.close()

        # Step 2: Call War Room for full analysis (all 3+1 agents)
        logger.info(f"📊 Calling War Room for {ticker} (3+1 agents)")

        # Extract context and persona
        context = request.get("context", "new_position")
        persona_mode = request.get("persona_mode", "trading")
        
        # Portfolio State (Mock for now, should be real)
        # TODO: Fetch real portfolio state if context is existing_position
        portfolio_state = {"total_value": 100000}
        
        war_room_result = await war_room.deliberate(
            symbol=ticker,
            action_context=context,
            market_data={
                "news_headlines": news_headlines,
                "news_sentiment": news_sentiment,
                "price_data": {},  # Will be populated by agents internally
                "news_count": len(news_headlines)
            },
            portfolio_state=portfolio_state,
            additional_data={
                "news_count": len(news_headlines),
                "analysis_source": "portfolio_api"
            },
            persona_mode=persona_mode
        )

        # Step 3: Extract individual agent opinions
        # War Room returns detailed opinions from all agents
        agent_opinions = war_room_result.get("agent_opinions", {})
        pm_decision_data = war_room_result.get("pm_decision", {})

        logger.info(f"🔍 DEBUG: PM Decision Data Keys: {pm_decision_data.keys()}")
        logger.info(f"🔍 DEBUG: Risk Agent Keys: {agent_opinions.get('risk', {}).keys()}")

        # Risk Position Size Logic
        # RiskAgentMVP returns 'max_position_pct' (e.g. 0.05), frontend expects 'position_size' (5)
        risk_op = agent_opinions.get("risk", {})
        position_size_raw = risk_op.get("position_size_pct") or risk_op.get("max_position_pct") or 0.0

        agents_analysis = {
            "trader_agent": {
                "action": agent_opinions.get("trader", {}).get("action", "HOLD"),
                "confidence": agent_opinions.get("trader", {}).get("confidence", 0.5),
                "reasoning": agent_opinions.get("trader", {}).get("reasoning", ""),
                "weight": agent_opinions.get("trader", {}).get("weight", 0.35),
                "latency_seconds": agent_opinions.get("trader", {}).get("latency_seconds", 0)
            },
            "risk_agent": {
                "action": "HOLD",  # Risk agent returns recommendation, not action
                "recommendation": risk_op.get("recommendation", "hold"),
                "risk_level": risk_op.get("risk_level", "medium"),
                "confidence": risk_op.get("confidence", 0.5),
                "reasoning": risk_op.get("reasoning", ""),
                "weight": risk_op.get("weight", 0.30),
                "position_size_pct": position_size_raw,
                "latency_seconds": risk_op.get("latency_seconds", 0)
            },
            "analyst_agent": {
                "action": agent_opinions.get("analyst", {}).get("action", "HOLD"),
                "overall_score": agent_opinions.get("analyst", {}).get("overall_information_score", 0.5),
                "confidence": agent_opinions.get("analyst", {}).get("confidence", 0.5),
                "reasoning": agent_opinions.get("analyst", {}).get("reasoning", ""),
                "weight": agent_opinions.get("analyst", {}).get("weight", 0.35),
                "latency_seconds": agent_opinions.get("analyst", {}).get("latency_seconds", 0),
                "news_count": len(news_headlines)
            },
            "pm_agent": {
                "action": pm_decision_data.get("final_decision", "hold"),
                "recommended_action": pm_decision_data.get("recommended_action", "HOLD"),
                "confidence": pm_decision_data.get("confidence", 0.5),
                "reasoning": pm_decision_data.get("reasoning", ""),
                "hard_rules_passed": pm_decision_data.get("hard_rules_passed", []),
                "hard_rules_violations": pm_decision_data.get("hard_rules_violations", [])
            }
        }

        # Convert risk_agent recommendation to action
        if agents_analysis["risk_agent"]["recommendation"] == "buy":
            agents_analysis["risk_agent"]["action"] = "BUY"
        elif agents_analysis["risk_agent"]["recommendation"] == "sell":
            agents_analysis["risk_agent"]["action"] = "SELL"
        else:
            agents_analysis["risk_agent"]["action"] = "HOLD"

        # Calculate analysis time
        end_time = datetime.now()
        analysis_duration = (end_time - start_time).total_seconds()

        logger.info(f"🔍 DEBUG: Extracted PM Reasoning: {agents_analysis['pm_agent']['reasoning'][:50]}...")
        logger.info(f"🔍 DEBUG: Extracted PM Confidence: {agents_analysis['pm_agent']['confidence']}")
        logger.info(f"🔍 DEBUG: PM Agent Keys: {list(agents_analysis['pm_agent'].keys())}")
        logger.info(f"🔍 DEBUG: Extracted Risk Position: {agents_analysis['risk_agent']['position_size_pct']}")

        # Create final response with all agent opinions
        final_response = {
            "ticker": ticker,
            "analysis_timestamp": start_time.isoformat(),
            "analysis_duration_seconds": round(analysis_duration, 2),
            "data_sources": {
                "price_data": True,
                "news_data": len(news_headlines) > 0,
                "news_count": len(news_headlines)
            },
            "agents_analysis": agents_analysis,
            "final_decision": {
                "action": agents_analysis["pm_agent"].get("action") or agents_analysis["pm_agent"].get("final_decision", "hold"),
                "recommended_action": agents_analysis["pm_agent"].get("recommended_action", "hold"),
                "confidence": agents_analysis["pm_agent"].get("confidence", 0.0),
                "reasoning": agents_analysis["pm_agent"].get("reasoning", "")
            },
            # --- Frontend Compatibility Fields (AIDecision interface) ---
            "action": agents_analysis["pm_agent"].get("action") or agents_analysis["pm_agent"].get("final_decision", "hold"),
            "conviction": agents_analysis["pm_agent"].get("confidence", 0.0),
            "reasoning": agents_analysis["pm_agent"].get("reasoning", ""),
            "position_size": agents_analysis["risk_agent"].get("position_size_pct", 0) * 100,  # Convert to %
            "risk_factors": agents_analysis["pm_agent"].get("hard_rules_violations", []) or ["None"],
            
            # Context-Aware Fields
            "portfolio_action": agents_analysis["pm_agent"].get("portfolio_action"),
            "action_reason": agents_analysis["pm_agent"].get("action_reason"),
            "action_strength": agents_analysis["pm_agent"].get("action_strength"),
            "position_adjustment_pct": agents_analysis["pm_agent"].get("position_adjustment_pct"),
            "target_price": 0,  # Not currently provided by agents
            "stop_loss": 0,     # Provided in risk agent opinion but not top level standard yet
            # -----------------------------------------------------------
            "news_summary": {
                "total_articles": len(news_headlines),
                "recent_headlines": news_headlines[:5],  # Top 5 headlines
                "sentiment_summary": news_sentiment[:5] if news_sentiment else []
            },
            "timestamp": end_time.isoformat()
        }

        # Save to database for BUY/SELL signals
        if final_response["final_decision"]["action"] in ["BUY", "SELL"]:
            db = get_sync_session()
            try:
                signal = DBTradingSignal(
                    analysis_id=None,
                    ticker=ticker,
                    action=final_response["final_decision"]["action"],
                    signal_type="PRIMARY",
                    confidence=final_response["final_decision"]["confidence"],
                    reasoning=final_response["final_decision"]["reasoning"],
                    source="war_room_analysis",  # 3+1 agents
                    generated_at=datetime.now()
                )
                db.add(signal)
                db.commit()
                logger.info(f"📊 War Room signal saved: {ticker} {final_response['final_decision']['action']} (3+1 agents)")
            except Exception as db_error:
                logger.error(f"Failed to save signal to DB: {db_error}")
            finally:
                db.close()

        logger.info(f"✅ Hybrid analysis complete for {ticker}: {final_response['final_decision']['action']} ({analysis_duration:.2f}s)")
        return final_response

    except Exception as e:
        logger.error(f"Hybrid analysis failed for {ticker}: {str(e)}", exc_info=True)

        # Fallback: Simple HOLD with explanation
        return {
            "ticker": ticker,
            "analysis_timestamp": start_time.isoformat(),
            "analysis_duration_seconds": 0.0,
            "error": str(e),
            "agents_analysis": {
                "trader_agent": {"action": "HOLD", "confidence": 0.0, "reasoning": "Analysis failed", "weight": 0.35},
                "risk_agent": {"action": "HOLD", "recommendation": "hold", "risk_level": "unknown", "confidence": 0.0, "reasoning": "Analysis failed", "weight": 0.30},
                "analyst_agent": {"action": "HOLD", "overall_score": 0.0, "confidence": 0.0, "reasoning": "Analysis failed", "weight": 0.35},
                "pm_agent": {"action": "HOLD", "confidence": 0.0, "reasoning": "Analysis failed", "hard_rules_passed": [], "hard_rules_violations": []}
            },
            "final_decision": {
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": f"분석 시스템 오류: {str(e)}"
            },
            "data_sources": {
                "price_data": False,
                "news_data": False
            },
            "timestamp": datetime.now().isoformat()
        }




@router.get("/api/history/{ticker}")
@log_endpoint("unknown", "system")
async def get_analysis_history(ticker: str, limit: int = 10):
    """
    Get analysis history for a specific ticker.
    """
    try:
        from backend.ai.trading_agent import TradingAgent
        agent = TradingAgent()
        history = await agent.get_decision_history(ticker.upper(), limit)
        return history
    except Exception as e:
        logger.error(f"Failed to fetch history for {ticker}: {e}")
        return []


@router.get("/api/analysis/history")
@log_endpoint("unknown", "system")
async def get_global_analysis_history(limit: int = 50, ticker: Optional[str] = None):
    """
    Get global analysis history (all tickers).
    """
    try:
        from backend.ai.trading_agent import TradingAgent
        agent = TradingAgent()
        history = await agent.get_global_history(limit, ticker)
        return history
    except Exception as e:
        logger.error(f"Failed to fetch global history: {e}")
        return []


@router.post("/api/analyze/batch")
@log_endpoint("unknown", "system")
async def analyze_batch(request: Dict[str, Any]):
    """
    Batch analyze multiple tickers
    """
    tickers = request.get("tickers", [])
    
    if not tickers:
        raise HTTPException(status_code=400, detail="Tickers list is required")
    
    results = []
    for ticker in tickers[:10]:  # Limit to 10 tickers
        try:
            result = await analyze_ticker({"ticker": ticker})
            results.append(result)
        except Exception as e:
            results.append({
                "ticker": ticker,
                "error": str(e),
                "status": "error"
            })
    
    return {"results": results, "count": len(results)}


# ==========================================
# Deep Reasoning APIs
# ==========================================

@router.post("/api/reasoning/analyze")
@log_endpoint("unknown", "system")
async def reasoning_analyze(request: Dict[str, Any]):
    """
    Deep reasoning analysis using AI
    """
    try:
        from backend.ai.strategies.deep_reasoning_strategy import DeepReasoningStrategy
        
        strategy = DeepReasoningStrategy()
        context = request.get("context", "")
        ticker = request.get("ticker", "")
        
        if context:
            result = await strategy.analyze_context(context, ticker)
            return result
        else:
            return {
                "conclusion": "No context provided for analysis",
                "reasoning_steps": [],
                "confidence": 0.0
            }
    except ImportError as e:
        logger.warning(f"DeepReasoningStrategy not available: {e}")
        return {
            "conclusion": "Deep reasoning module not configured",
            "reasoning_steps": ["AI models need to be configured"],
            "confidence": 0.0,
            "status": "not_configured"
        }
    except Exception as e:
        logger.error(f"Error in reasoning analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reasoning/knowledge/{ticker}")
@log_endpoint("unknown", "system")
async def get_knowledge(ticker: str):
    """
    Get knowledge base information for ticker
    """
    try:
        from backend.data.vector_store.store import VectorStore
        
        store = VectorStore()
        facts = await store.search_ticker(ticker, limit=10)
        
        return {
            "ticker": ticker.upper(),
            "facts": [f.content for f in facts] if facts else [],
            "graph_nodes": len(facts) if facts else 0,
            "last_updated": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "ticker": ticker.upper(),
            "facts": [],
            "graph_nodes": 0,
            "status": "vector_store_not_configured"
        }
    except Exception as e:
        logger.error(f"Error getting knowledge for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "facts": [],
            "error": str(e)
        }


# ==========================================
# Advanced Analytics APIs - Real Implementation
# ==========================================

@router.get("/api/reports/advanced/performance-attribution")
@log_endpoint("unknown", "system")
async def get_performance_attribution(
    start_date: str,
    end_date: str,
    dimension: str = "sector",
    db: Session = Depends(get_db)
):
    """
    Get real performance attribution from closed positions
    """
    try:
        from datetime import datetime
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Get closed positions in date range
        closed_signals = db.query(TradingSignal).filter(
            TradingSignal.exit_price.isnot(None),
            TradingSignal.exit_date >= start,
            TradingSignal.exit_date <= end
        ).all()
        
        total_return = 0.0
        attribution = {}
        
        for signal in closed_signals:
            ret = signal.actual_return_pct or 0
            total_return += ret
            
            # Simple sector mapping (in production, use proper sector data)
            sector = "Technology"  # Default
            if signal.ticker in ["AAPL", "MSFT", "GOOGL", "META"]:
                sector = "Technology"
            elif signal.ticker in ["JPM", "GS", "BAC"]:
                sector = "Finance"
            elif signal.ticker in ["JNJ", "PFE", "UNH"]:
                sector = "Healthcare"
            
            if sector not in attribution:
                attribution[sector] = 0
            attribution[sector] += ret
        
        return {
            "total_return": round(total_return, 2),
            "trade_count": len(closed_signals),
            "attribution": [
                {"sector": k, "contribution": round(v, 2)}
                for k, v in attribution.items()
            ],
            "period": {"start": start_date, "end": end_date}
        }
    except Exception as e:
        logger.error(f"Error getting performance attribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/advanced/risk-metrics")
@log_endpoint("unknown", "system")
async def get_risk_metrics(
    start_date: str,
    end_date: str,
    metric: str = "var",
    db: Session = Depends(get_db)
):
    """
    Get real risk metrics from portfolio
    """
    try:
        from backend.skills.trading.risk_skill import RiskSkill
        
        risk_skill = RiskSkill()
        
        # Get portfolio positions
        positions = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).all()
        
        portfolio_data = [
            {"ticker": p.ticker, "value": (p.entry_price or 0) * 10}
            for p in positions
        ]
        
        result = await risk_skill.calculate_portfolio_risk(portfolio_data)
        
        return {
            "metric": metric,
            "value": result.get(metric, 0),
            "all_metrics": result,
            "period": {"start": start_date, "end": end_date}
        }
    except ImportError:
        return {
            "metric": metric,
            "value": 0.05 if metric == "var" else 1.2,
            "status": "using_defaults"
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/reports/advanced/trade-insights")
@log_endpoint("unknown", "system")
async def get_trade_insights(
    start_date: str,
    end_date: str,
    analysis: str = "performance",
    db: Session = Depends(get_db)
):
    """
    Get real trade insights from historical data
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Get closed positions
        closed_signals = db.query(TradingSignal).filter(
            TradingSignal.exit_price.isnot(None),
            TradingSignal.exit_date >= start,
            TradingSignal.exit_date <= end
        ).all()
        
        if not closed_signals:
            return {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "trade_count": 0,
                "insights": ["No trades in selected period"]
            }
        
        # Calculate metrics
        winners = [s for s in closed_signals if (s.actual_return_pct or 0) > 0]
        losers = [s for s in closed_signals if (s.actual_return_pct or 0) < 0]
        
        win_rate = len(winners) / len(closed_signals)
        
        total_profit = sum(s.actual_return_pct or 0 for s in winners)
        total_loss = abs(sum(s.actual_return_pct or 0 for s in losers))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # Generate insights
        insights = []
        if win_rate > 0.6:
            insights.append("Strong win rate above 60%")
        if profit_factor > 2:
            insights.append("Excellent profit factor indicates quality trades")
        if len(winners) > len(losers):
            insights.append("More winning trades than losing trades")
        
        return {
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 2),
            "trade_count": len(closed_signals),
            "winners": len(winners),
            "losers": len(losers),
            "insights": insights if insights else ["Continue monitoring performance"],
            "period": {"start": start_date, "end": end_date}
        }
    except Exception as e:
        logger.error(f"Error getting trade insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
