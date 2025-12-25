"""
Signal Consolidation Endpoint

Aggregates signals from all sources:
- War Room (war_room)
- Deep Reasoning (deep_reasoning)
- Analysis Lab (manual_analysis)
- News Analysis (news_analysis)

Priority:
1. War Room (highest - 7 agents consensus)
2. Deep Reasoning (high - multi-step analysis)
3. Analysis Lab (medium - manual trigger)
4. News Analysis (low - event-driven)

Author: AI Trading System
Date: 2025-12-21
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import traceback

from backend.database.models import TradingSignal
from backend.database.repository import get_sync_session

# Agent Logging
from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    ExecutionStatus,
    ErrorImpact
)

logger = logging.getLogger(__name__)
agent_logger = AgentLogger("signal-consolidation", "system")

router = APIRouter(prefix="/api/consolidated-signals", tags=["consolidated-signals"])


# Source priority weights
SOURCE_PRIORITY = {
    "war_room": 4,           # Highest: 7-agent consensus
    "deep_reasoning": 3,     # High: Multi-step analysis
    "manual_analysis": 2,    # Medium: Human-triggered
    "news_analysis": 1       # Low: Event-driven
}


@router.get("")
async def get_consolidated_signals(
    ticker: Optional[str] = None,
    source: Optional[str] = Query(None, description="Filter by source (war_room, deep_reasoning, manual_analysis, news_analysis)"),
    action: Optional[str] = Query(None, description="Filter by action (BUY, SELL, HOLD)"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get consolidated signals from all sources with priority ordering.
    
    Returns signals sorted by:
    1. Source priority (war_room > deep_reasoning > manual_analysis > news_analysis)
    2. Confidence score (within same priority level)
    3. Recency (newest first)
    
    Query Parameters:
    - ticker: Filter by specific ticker (optional)
    - source: Filter by source (war_room, deep_reasoning, manual_analysis, news_analysis)
    - action: Filter by action (BUY, SELL, HOLD)
    - hours: Hours to look back (default: 24, max: 168=1week)
    - limit: Maximum signals to return (default: 50, max: 200)
    
    Response:
    [
        {
            "id": int,
            "ticker": "AAPL",
            "action": "BUY|SELL|HOLD",
            "confidence": 0.85,
            "source": "war_room|deep_reasoning|manual_analysis|news_analysis",
            "reasoning": "...",
            "created_at": "2025-12-21T14:00:00",
            "priority": 4  # Source priority weight
        },
        ...
    ]
    """
    start_time = datetime.now()
    task_id = f"consolidate-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    db = get_sync_session()
    
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Build query
        query = db.query(TradingSignal)\
            .filter(TradingSignal.generated_at >= cutoff)
        
        if ticker:
            query = query.filter(TradingSignal.ticker == ticker.upper())
        
        if source:
            query = query.filter(TradingSignal.source == source)
        
        if action:
            query = query.filter(TradingSignal.action == action.upper())
        
        signals = query.all()
        
        # Convert to response format with priority
        result = []
        for signal in signals:
            source = signal.source or "unknown"
            priority = SOURCE_PRIORITY.get(source, 0)
            
            result.append({
                "id": signal.id,
                "ticker": signal.ticker,
                "action": signal.action,
                "confidence": signal.confidence,
                "source": source,
                "reasoning": signal.reasoning,
                "created_at": signal.generated_at.isoformat(),
                "timestamp": signal.generated_at.isoformat(),  # Alias for frontend compatibility
                "priority": priority,
                "signal_type": signal.signal_type
            })
        
        # Sort by priority (desc), confidence (desc), recency (desc)
        result.sort(
            key=lambda x: (
                -x["priority"],                                      # Higher priority first
                -x["confidence"],                                    # Higher confidence first
                -datetime.fromisoformat(x["created_at"]).timestamp() # Newer first
            )
        )
        
        # Apply limit
        result = result[:limit]
        
        logger.info(f"Consolidated {len(result)} signals (ticker={ticker}, hours={hours})")
        
        # Log successful execution
        agent_logger.log_execution(ExecutionLog(
            timestamp=datetime.now(),
            agent="system/signal-consolidation",
            task_id=task_id,
            status=ExecutionStatus.SUCCESS,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            input={
                "ticker": ticker,
                "source": source,
                "action": action,
                "hours": hours,
                "limit": limit
            },
            output={
                "total_count": len(result),
                "sources": list(_count_by_source(result).keys())
            }
        ))
        
        return {
            "signals": result,
            "total_count": len(result),
            "filters": {
                "ticker": ticker,
                "source": source,
                "action": action,
                "hours": hours,
                "limit": limit
            },
            "source_breakdown": _count_by_source(result)
        }
    
    except Exception as e:
        logger.error(f"Failed to consolidate signals: {e}")
        
        # Log error
        agent_logger.log_error(ErrorLog(
            timestamp=datetime.now(),
            agent="system/signal-consolidation",
            task_id=task_id,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "stack": traceback.format_exc(),
                "context": {
                    "ticker": ticker,
                    "hours": hours
                }
            },
            impact=ErrorImpact.HIGH,
            recovery_attempted=False
        ))
        
        return {
            "signals": [],
            "total_count": 0,
            "error": str(e)
        }
    
    finally:
        db.close()


@router.get("/by-ticker/{ticker}")
async def get_consolidated_by_ticker(
    ticker: str,
    hours: int = Query(168, description="Hours lookback"),
    include_all_actions: bool = Query(False, description="Include HOLD signals")
):
    """
    Get all consolidated signals for a specific ticker.
    
    Useful for:
    - Displaying all recent signals for a ticker
    - Conflict detection (e.g., War Room says BUY but Deep Reasoning says SELL)
    - Historical tracking
    """
    db = get_sync_session()
    
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        
        query = db.query(TradingSignal)\
            .filter(
            TradingSignal.ticker == ticker.upper(),
            TradingSignal.generated_at >= cutoff
        )
        
        if not include_all_actions:
            query = query.filter(TradingSignal.action.in_(["BUY", "SELL"]))
        
        signals = query.order_by(TradingSignal.generated_at.desc()).all()
        
        # Group by source
        by_source = {}
        for signal in signals:
            source = signal.source or "unknown"
            if source not in by_source:
                by_source[source] = []
            
            by_source[source].append({
                "id": signal.id,
                "action": signal.action,
                "confidence": signal.confidence,
                "reasoning": signal.reasoning[:100] + "...",  # Truncate
                "created_at": signal.generated_at.isoformat()
            })
        
        # Detect conflicts
        actions_by_source = {}
        for source, sigs in by_source.items():
            if sigs:
                # Get most recent action from each source
                actions_by_source[source] = sigs[0]["action"]
        
        unique_actions = set(actions_by_source.values())
        has_conflict = len(unique_actions) > 1 and "HOLD" not in unique_actions
        
        return {
            "ticker": ticker.upper(),
            "total_signals": len(signals),
            "by_source": by_source,
            "conflict_detected": has_conflict,
            "actions_by_source": actions_by_source,
            "hours": hours
        }
    
    except Exception as e:
        logger.error(f"Failed to get signals for {ticker}: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()


@router.get("/stats")
async def get_consolidation_stats(hours: int = Query(24)):
    """
    Get statistics about signal generation across all sources.
    
    Returns:
    {
        "total_signals": int,
        "by_source": {
            "war_room": 5,
            "deep_reasoning": 12,
            "manual_analysis": 8,
            "news_analysis": 3
        },
        "by_action": {
            "BUY": 15,
            "SELL": 8,
            "HOLD": 5
        },
        "avg_confidence_by_source": {...},
        "period_hours": 24
    }
    """
    db = get_sync_session()
    
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        
        signals = db.query(TradingSignal)\
            .filter(TradingSignal.generated_at >= cutoff)\
            .all()
        
        # Count by source
        by_source = {}
        for signal in signals:
            source = signal.source or "unknown"
            by_source[source] = by_source.get(source, 0) + 1
        
        # Count by action
        by_action = {}
        for signal in signals:
            action = signal.action
            by_action[action] = by_action.get(action, 0) + 1
        
        # Average confidence by source
        confidence_sums = {}
        confidence_counts = {}
        for signal in signals:
            source = signal.source or "unknown"
            if source not in confidence_sums:
                confidence_sums[source] = 0
                confidence_counts[source] = 0
            confidence_sums[source] += signal.confidence
            confidence_counts[source] += 1
        
        avg_confidence = {
            source: confidence_sums[source] / confidence_counts[source]
            for source in confidence_sums
        }
        
        # Calculate global average confidence
        global_avg_confidence = (
            sum(confidence_sums.values()) / sum(confidence_counts.values())
            if sum(confidence_counts.values()) > 0 else 0.0
        )
        
        return {
            "total_signals": len(signals),
            "by_source": by_source,
            "by_action": by_action,
            "avg_confidence": global_avg_confidence,  # Global average for frontend
            "avg_confidence_by_source": avg_confidence,
            "period_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()


def _count_by_source(signals: List[Dict]) -> Dict[str, int]:
    """Helper to count signals by source"""
    counts = {}
    for signal in signals:
        source = signal["source"]
        counts[source] = counts.get(source, 0) + 1
    return counts
