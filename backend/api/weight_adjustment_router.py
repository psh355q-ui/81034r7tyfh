"""
Weight Adjustment API Router - 가중치 조정 및 경고 API

Phase 25.4: Self-Learning Feedback Loop
Date: 2025-12-25

API Endpoints:
- GET /api/weights/current - 현재 에이전트 가중치
- POST /api/weights/recalculate - 가중치 재계산 (수동 트리거)
- GET /api/weights/history - 가중치 변경 이력
- GET /api/alerts/recent - 최근 경고 목록
- GET /api/alerts/summary - 경고 요약
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

# Import learning modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.learning.agent_weight_adjuster import AgentWeightAdjuster
from ai.learning.agent_alert_system import AgentAlertSystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weights", tags=["weights"])


# ============================================================================
# Response Models
# ============================================================================

class AgentWeight(BaseModel):
    """에이전트 가중치"""
    agent_name: str
    weight: float
    last_updated: Optional[str] = None


class WeightRecalculationResult(BaseModel):
    """가중치 재계산 결과"""
    agent_name: str
    old_weight: float
    new_weight: float
    change: float
    reason: str


class Alert(BaseModel):
    """경고"""
    id: int
    agent_name: str
    alert_type: str
    message: str
    severity: str
    created_at: str
    metadata: Optional[Dict] = None


class AlertSummary(BaseModel):
    """경고 요약"""
    total_alerts: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    recent_high_severity: List[Alert]


# ============================================================================
# Weight Endpoints
# ============================================================================

@router.get("/current", response_model=List[AgentWeight])
async def get_current_weights():
    """
    현재 에이전트 가중치 조회
    
    Returns:
        List of agent weights
    """
    try:
        adjuster = AgentWeightAdjuster()
        weights = await adjuster.get_current_weights()
        
        return [
            AgentWeight(agent_name=agent, weight=weight)
            for agent, weight in weights.items()
        ]
    
    except Exception as e:
        logger.error(f"Failed to get current weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recalculate", response_model=List[WeightRecalculationResult])
async def recalculate_weights(
    lookback_days: int = Query(30, ge=1, le=365, description="Lookback period in days"),
    save_to_db: bool = Query(True, description="Save results to database")
):
    """
    가중치 재계산 (수동 트리거)
    
    Args:
        lookback_days: 조회 기간 (일)
        save_to_db: DB 저장 여부
    
    Returns:
        Weight recalculation results for all agents
    """
    try:
        adjuster = AgentWeightAdjuster()
        results = await adjuster.recalculate_all_weights(lookback_days, save_to_db)
        
        return [
            WeightRecalculationResult(
                agent_name=agent,
                old_weight=data['old_weight'],
                new_weight=data['new_weight'],
                change=data['change'],
                reason=data['reason']
            )
            for agent, data in results.items()
        ]
    
    except Exception as e:
        logger.error(f"Failed to recalculate weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_weight_history(
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    days: int = Query(30, ge=1, le=365, description="Number of days")
):
    """
    가중치 변경 이력 조회
    
    Args:
        agent: 에이전트 필터 (선택)
        days: 조회 기간
    
    Returns:
        Weight change history
    """
    try:
        from datetime import timedelta
        import asyncpg
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'trading_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        conn = await asyncpg.connect(**db_config)
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT agent_name, weights, created_at
                FROM agent_weights_history
                WHERE created_at >= $1
            """
            params = [cutoff_date]
            
            if agent:
                query += " AND agent_name = $2"
                params.append(agent)
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            return [
                {
                    'agent_name': row['agent_name'],
                    'weights': row['weights'],
                    'created_at': row['created_at'].isoformat()
                }
                for row in rows
            ]
        
        finally:
            await conn.close()
    
    except Exception as e:
        logger.error(f"Failed to get weight history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Alert Endpoints
# ============================================================================

alerts_router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@alerts_router.get("/recent", response_model=List[Alert])
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    최근 경고 조회
    
    Args:
        hours: 조회 시간 (시간)
        agent: 에이전트 필터
        alert_type: 경고 타입 필터
        severity: 심각도 필터
    
    Returns:
        List of recent alerts
    """
    try:
        alert_system = AgentAlertSystem()
        alerts = await alert_system.get_recent_alerts(hours, agent, alert_type)
        
        # Severity 필터링 (DB 쿼리에 추가하지 않고 후처리)
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return [
            Alert(
                id=alert['id'],
                agent_name=alert['agent_name'],
                alert_type=alert['alert_type'],
                message=alert['message'],
                severity=alert['severity'],
                created_at=alert['created_at'],
                metadata=alert.get('metadata')
            )
            for alert in alerts
        ]
    
    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@alerts_router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """
    경고 요약
    
    Args:
        hours: 조회 시간
    
    Returns:
        Alert summary statistics
    """
    try:
        alert_system = AgentAlertSystem()
        alerts = await alert_system.get_recent_alerts(hours)
        
        # 통계 계산
        total = len(alerts)
        
        by_type = {}
        by_severity = {}
        
        for alert in alerts:
            # Type 통계
            alert_type = alert['alert_type']
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            # Severity 통계
            severity = alert['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # High severity 최근 경고 (최대 5개)
        high_severity_alerts = [
            Alert(
                id=alert['id'],
                agent_name=alert['agent_name'],
                alert_type=alert['alert_type'],
                message=alert['message'],
                severity=alert['severity'],
                created_at=alert['created_at'],
                metadata=alert.get('metadata')
            )
            for alert in alerts
            if alert['severity'] == 'HIGH'
        ][:5]
        
        return AlertSummary(
            total_alerts=total,
            by_type=by_type,
            by_severity=by_severity,
            recent_high_severity=high_severity_alerts
        )
    
    except Exception as e:
        logger.error(f"Failed to get alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@alerts_router.post("/check")
async def trigger_alert_check(
    lookback_days: int = Query(30, ge=1, le=365, description="Lookback period")
):
    """
    경고 체크 수동 트리거
    
    Args:
        lookback_days: 조회 기간
    
    Returns:
        Alert check results
    """
    try:
        alert_system = AgentAlertSystem()
        results = await alert_system.check_all_alerts(lookback_days)
        
        return {
            'underperformance_count': len(results['underperformance']),
            'overconfidence_count': len(results['overconfidence']),
            'underperformance': results['underperformance'],
            'overconfidence': results['overconfidence']
        }
    
    except Exception as e:
        logger.error(f"Failed to trigger alert check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
