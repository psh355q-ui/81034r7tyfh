"""
Agent Alert System - 저성과 에이전트 자동 감지 및 경고

Phase 25.4: Self-Learning Feedback Loop
Date: 2025-12-25

Features:
- 저성과 에이전트 탐지 (정확도 < 50%)
- 오버컨피던트 에이전트 탐지
- 경고 로그 시스템
- 알림 이력 저장
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncpg
import os

logger = logging.getLogger(__name__)


# ============================================================================
# Alert System
# ============================================================================

class AgentAlertSystem:
    """에이전트 성과 모니터링 및 경고 시스템"""
    
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
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'trading_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
    
    async def get_db_connection(self) -> asyncpg.Connection:
        """데이터베이스 연결"""
        return await asyncpg.connect(**self.db_config)
    
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
        conn = await self.get_db_connection()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            query = """
                SELECT 
                    COUNT(*) as total_votes,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_votes,
                    AVG(vote_confidence) as avg_confidence
                FROM agent_vote_tracking
                WHERE agent_name = $1
                  AND status = 'COMPLETED'
                  AND initial_timestamp >= $2
            """
            
            row = await conn.fetchrow(query, agent_name, cutoff_date)
            
            if not row or row['total_votes'] == 0:
                return None
            
            total = int(row['total_votes'])
            correct = int(row['correct_votes'] or 0)
            accuracy = correct / total if total > 0 else 0.0
            
            return {
                'total_votes': total,
                'correct_votes': correct,
                'accuracy': accuracy,
                'avg_confidence': float(row['avg_confidence'] or 0.0)
            }
        
        finally:
            await conn.close()
    
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
        
        Args:
            agent_name: 에이전트 이름
            alert_type: 경고 타입
            message: 경고 메시지
            severity: 심각도 (LOW, MEDIUM, HIGH)
            metadata: 추가 정보
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
        conn = await self.get_db_connection()
        
        try:
            # 테이블 생성
            create_table_query = """
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
            """
            await conn.execute(create_table_query)
            
            # 경고 저장
            insert_query = """
                INSERT INTO agent_alerts (agent_name, alert_type, message, severity, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """
            await conn.execute(insert_query, agent_name, alert_type, message, severity, metadata)
        
        except Exception as e:
            logger.error(f"Failed to save alert to DB: {e}")
        
        finally:
            await conn.close()
    
    async def get_recent_alerts(
        self,
        hours: int = 24,
        agent_name: Optional[str] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict]:
        """
        최근 경고 조회
        
        Args:
            hours: 조회 시간 (시간)
            agent_name: 에이전트 필터 (선택)
            alert_type: 경고 타입 필터 (선택)
        
        Returns:
            [{'id', 'agent_name', 'alert_type', 'message', 'severity', 'created_at'}]
        """
        conn = await self.get_db_connection()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = """
                SELECT id, agent_name, alert_type, message, severity, 
                       metadata, created_at
                FROM agent_alerts
                WHERE created_at >= $1
            """
            params = [cutoff_time]
            
            if agent_name:
                query += " AND agent_name = $2"
                params.append(agent_name)
            
            if alert_type:
                param_idx = len(params) + 1
                query += f" AND alert_type = ${param_idx}"
                params.append(alert_type)
            
            query += " ORDER BY created_at DESC LIMIT 100"
            
            rows = await conn.fetch(query, *params)
            
            return [
                {
                    'id': row['id'],
                    'agent_name': row['agent_name'],
                    'alert_type': row['alert_type'],
                    'message': row['message'],
                    'severity': row['severity'],
                    'metadata': row['metadata'],
                    'created_at': row['created_at'].isoformat()
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
        
        finally:
            await conn.close()


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
