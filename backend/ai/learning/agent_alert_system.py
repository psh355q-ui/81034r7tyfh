"""
Agent Alert System - 저성과 에이전트 자동 감지 및 경고

Phase 25.4: Self-Learning Feedback Loop (Repository Pattern)
Date: 2025-12-27

Features:
- 저성과 에이전트 탐지 (정확도 < 50%)
- 오버컨피던트 에이전트 탐지
- 경고 로그 시스템
- 알림 이력 저장
- Repository Pattern 적용
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text

# Repository pattern
from backend.database.repository import get_sync_session

logger = logging.getLogger(__name__)


# ============================================================================
# Alert System
# ============================================================================

class AgentAlertSystem:
    """에이전트 성과 모니터링 및 경고 시스템 (Repository Pattern)"""
    
    # 경고 임계값
    UNDERPERFORMANCE_THRESHOLD = 0.50  # 정확도 50% 미만
    OVERCONFIDENCE_GAP_THRESHOLD = 0.20  # 신뢰도-정확도 갭 20% 이상
    MIN_SAMPLE_SIZE = 10  # 최소 샘플 크기
    
    # 경고 타입
    ALERT_UNDERPERFORMANCE = "UNDERPERFORMANCE"
    ALERT_OVERCONFIDENCE = "OVERCONFIDENCE"
    ALERT_UNDERCONFIDENCE = "UNDERCONFIDENCE"
    ALERT_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    
    def __init__(self):
        # SQLAlchemy session is managed per method
        pass
    
    async def get_agent_performance(
        self,
        agent_name: str,
        lookback_days: int = 30
    ) -> Optional[Dict]:
        """
        에이전트 성과 데이터 조회
        
        Returns:
            {
                'total_votes': int,
                'correct_votes': int,
                'accuracy': float,
                'avg_confidence': float
            }
        """
        session = get_sync_session()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            # Note: Using synchronous session in async method is standard here as simple queries are fast.
            # Ideally this should be async or run in executor if high load, but acceptable for this scheduler.
            
            query = text("""
                SELECT 
                    COUNT(*) as total_votes,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_votes,
                    AVG(vote_confidence) as avg_confidence
                FROM agent_vote_tracking
                WHERE agent_name = :agent_name
                  AND status = 'COMPLETED'
                  AND initial_timestamp >= :cutoff_date
            """)
            
            result = session.execute(query, {'agent_name': agent_name, 'cutoff_date': cutoff_date})
            row = result.fetchone()
            
            if not row or row.total_votes == 0:
                return None
            
            total = int(row.total_votes)
            correct = int(row.correct_votes or 0)
            accuracy = correct / total if total > 0 else 0.0
            
            return {
                'total_votes': total,
                'correct_votes': correct,
                'accuracy': accuracy,
                'avg_confidence': float(row.avg_confidence or 0.0)
            }
        
        finally:
            session.close()
    
    async def check_underperformance(
        self,
        lookback_days: int = 30
    ) -> List[Dict]:
        """
        저성과 에이전트 탐지 (정확도 < 50%)
        
        Returns:
            [{'agent_name': str, 'accuracy': float, 'total_votes': int}]
        """
        agents = ['trader', 'analyst', 'risk', 'macro', 'institutional', 'news', 'chip_war']
        alerts = []
        
        for agent in agents:
            performance = await self.get_agent_performance(agent, lookback_days)
            
            if performance is None:
                continue
            
            # 샘플 크기 체크
            if performance['total_votes'] < self.MIN_SAMPLE_SIZE:
                continue
            
            # 저성과 체크
            if performance['accuracy'] < self.UNDERPERFORMANCE_THRESHOLD:
                alert = {
                    'agent_name': agent,
                    'accuracy': performance['accuracy'],
                    'total_votes': performance['total_votes'],
                    'correct_votes': performance['correct_votes'],
                    'threshold': self.UNDERPERFORMANCE_THRESHOLD
                }
                alerts.append(alert)
                
                await self.send_alert(
                    agent_name=agent,
                    alert_type=self.ALERT_UNDERPERFORMANCE,
                    message=f"{agent} accuracy {performance['accuracy']:.1%} < {self.UNDERPERFORMANCE_THRESHOLD:.0%} "
                            f"({performance['correct_votes']}/{performance['total_votes']} correct)",
                    severity='HIGH',
                    metadata=alert
                )
        
        return alerts
    
    async def check_overconfidence(
        self,
        lookback_days: int = 30,
        gap_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        오버컨피던트 에이전트 탐지 (신뢰도 >> 정확도)
        
        Args:
            lookback_days: 조회 기간
            gap_threshold: 임계값 (기본 20%)
        
        Returns:
            [{'agent_name': str, 'gap': float, 'confidence': float, 'accuracy': float}]
        """
        if gap_threshold is None:
            gap_threshold = self.OVERCONFIDENCE_GAP_THRESHOLD
        
        agents = ['trader', 'analyst', 'risk', 'macro', 'institutional', 'news', 'chip_war']
        alerts = []
        
        for agent in agents:
            performance = await self.get_agent_performance(agent, lookback_days)
            
            if performance is None or performance['total_votes'] < self.MIN_SAMPLE_SIZE:
                continue
            
            # 오버컨피던트 체크
            gap = performance['avg_confidence'] - performance['accuracy']
            
            if gap > gap_threshold:
                alert = {
                    'agent_name': agent,
                    'gap': gap,
                    'avg_confidence': performance['avg_confidence'],
                    'accuracy': performance['accuracy'],
                    'total_votes': performance['total_votes']
                }
                alerts.append(alert)
                
                await self.send_alert(
                    agent_name=agent,
                    alert_type=self.ALERT_OVERCONFIDENCE,
                    message=f"{agent} overconfident: confidence {performance['avg_confidence']:.1%} "
                            f"vs accuracy {performance['accuracy']:.1%} (gap {gap:.1%})",
                    severity='MEDIUM',
                    metadata=alert
                )
        
        return alerts
    
    async def check_all_alerts(self, lookback_days: int = 30) -> Dict[str, List]:
        """
        모든 경고 체크
        
        Returns:
            {
                'underperformance': [...],
                'overconfidence': [...]
            }
        """
        logger.info(f"========== Agent Alert Check (lookback: {lookback_days} days) ==========")
        
        underperformance = await self.check_underperformance(lookback_days)
        overconfidence = await self.check_overconfidence(lookback_days)
        
        logger.info(f"Underperformance alerts: {len(underperformance)}")
        logger.info(f"Overconfidence alerts: {len(overconfidence)}")
        
        return {
            'underperformance': underperformance,
            'overconfidence': overconfidence
        }
    
    async def send_alert(
        self,
        agent_name: str,
        alert_type: str,
        message: str,
        severity: str = 'MEDIUM',
        metadata: Optional[Dict] = None
    ):
        """
        경고 발송 (로그 + DB 저장)
        """
        # 로그 출력
        log_message = f"🚨 ALERT [{severity}] [{alert_type}] {message}"
        
        if severity == 'HIGH':
            logger.error(log_message)
        elif severity == 'MEDIUM':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # DB 저장
        await self.save_alert_to_db(agent_name, alert_type, message, severity, metadata)
    
    async def save_alert_to_db(
        self,
        agent_name: str,
        alert_type: str,
        message: str,
        severity: str,
        metadata: Optional[Dict]
    ):
        """
        경고 이력 DB 저장
        
        Table: agent_alerts
        """
        session = get_sync_session()
        
        try:
            # 테이블 생성
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS agent_alerts (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(50) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_alerts_agent_created 
                ON agent_alerts(agent_name, created_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_alerts_type 
                ON agent_alerts(alert_type);
            """)
            session.execute(create_table_query)
            session.commit()
            
            # 경고 저장
            insert_query = text("""
                INSERT INTO agent_alerts (agent_name, alert_type, message, severity, metadata)
                VALUES (:agent_name, :alert_type, :message, :severity, :metadata)
            """)
            
            import json
            # JSON serialization for metadata if needed, though SQLAlchemy might handle dict for JSON type
            # Using json.dumps ensures it's a string if the driver requires it, or passing dict if driver supports it.
            # psycopg2 (used by sqlalchemy) adapts dict to jsonb automatically usually.
            # But let's be safe and pass the dict, assuming SQLA handles it.
            
            session.execute(insert_query, {
                'agent_name': agent_name,
                'alert_type': alert_type,
                'message': message,
                'severity': severity,
                'metadata': json.dumps(metadata) if metadata else None
            })
            session.commit()
        
        except Exception as e:
            logger.error(f"Failed to save alert to DB: {e}")
            session.rollback()
        
        finally:
            session.close()
    
    async def get_recent_alerts(
        self,
        hours: int = 24,
        agent_name: Optional[str] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict]:
        """
        최근 경고 조회
        """
        session = get_sync_session()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query_str = """
                SELECT id, agent_name, alert_type, message, severity, 
                       metadata, created_at
                FROM agent_alerts
                WHERE created_at >= :cutoff_time
            """
            params = {'cutoff_time': cutoff_time}
            
            if agent_name:
                query_str += " AND agent_name = :agent_name"
                params['agent_name'] = agent_name
            
            if alert_type:
                query_str += " AND alert_type = :alert_type"
                params['alert_type'] = alert_type
            
            query_str += " ORDER BY created_at DESC LIMIT 100"
            
            result = session.execute(text(query_str), params)
            rows = result.fetchall()
            
            return [
                {
                    'id': row.id,
                    'agent_name': row.agent_name,
                    'alert_type': row.alert_type,
                    'message': row.message,
                    'severity': row.severity,
                    'metadata': row.metadata,
                    'created_at': row.created_at.isoformat()
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
        
        finally:
            session.close()


# ============================================================================
# CLI 실행
# ============================================================================

async def main():
    """경고 시스템 실행"""
    alert_system = AgentAlertSystem()
    
    logger.info("========== Agent Alert System ==========")
    logger.info("")
    
    alerts = await alert_system.check_all_alerts(lookback_days=30)
    
    logger.info("")
    logger.info("========== Alert Summary ==========")
    logger.info(f"Underperformance: {len(alerts['underperformance'])}")
    for alert in alerts['underperformance']:
        logger.info(f"  - {alert['agent_name']}: {alert['accuracy']:.1%} "
                   f"({alert['correct_votes']}/{alert['total_votes']})")
    
    logger.info(f"Overconfidence: {len(alerts['overconfidence'])}")
    for alert in alerts['overconfidence']:
        logger.info(f"  - {alert['agent_name']}: gap {alert['gap']:.1%} "
                   f"(conf {alert['avg_confidence']:.1%} vs acc {alert['accuracy']:.1%})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
