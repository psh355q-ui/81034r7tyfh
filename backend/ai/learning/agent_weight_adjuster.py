"""
Agent Weight Adjuster - 에이전트 성과 기반 가중치 자동 조정

Phase 25.4: Self-Learning Feedback Loop
Date: 2025-12-25

Features:
- 에이전트 성과 데이터 기반 가중치 계산
- 오버컨피던트/언더컨피던트 탐지
- 가중치 변경 이력 저장
- 점진적 가중치 업데이트 (급격한 변화 방지)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncpg
import os

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Weight Calculation
# ============================================================================

class AgentWeightAdjuster:
    """에이전트 성과 기반 가중치 자동 조정"""
    
    # 기본 에이전트 가중치 (War Room)
    DEFAULT_WEIGHTS = {
        'trader': 0.18,
        'analyst': 0.15,
        'risk': 0.14,
        'macro': 0.16,
        'institutional': 0.15,
        'news': 0.14,
        'chip_war': 0.08,  # ChipWarAgent (필요시 활성화)
    }
    
    # 가중치 조정 규칙
    WEIGHT_RULES = {
        'excellent': {'min_accuracy': 0.70, 'multiplier': 1.2},   # 70%+ → 1.2x boost
        'good': {'min_accuracy': 0.60, 'multiplier': 1.0},        # 60-70% → baseline
        'fair': {'min_accuracy': 0.50, 'multiplier': 0.8},        # 50-60% → reduce
        'poor': {'min_accuracy': 0.0, 'multiplier': 0.5},         # <50% → penalty
    }
    
    # 가중치 변화 제한 (단일 업데이트당 최대 변화)
    MAX_WEIGHT_CHANGE = 0.30  # 30%
    
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
        
        Args:
            agent_name: 에이전트 이름
            lookback_days: 조회 기간 (일)
        
        Returns:
            {
                'total_votes': int,
                'correct_votes': int,
                'accuracy': float,
                'avg_return': float,
                'avg_confidence': float,
                'best_action': str,
                'best_action_accuracy': float
            }
        """
        conn = await self.get_db_connection()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            # 전체 성과
            query = """
                SELECT 
                    COUNT(*) as total_votes,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_votes,
                    AVG(return_pct) as avg_return,
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
            
            # 액션별 성과 (최고 액션 찾기)
            action_query = """
                SELECT 
                    vote_action,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM agent_vote_tracking
                WHERE agent_name = $1
                  AND status = 'COMPLETED'
                  AND initial_timestamp >= $2
                GROUP BY vote_action
                ORDER BY correct DESC
                LIMIT 1
            """
            
            action_row = await conn.fetchrow(action_query, agent_name, cutoff_date)
            
            best_action = None
            best_action_accuracy = 0.0
            
            if action_row:
                best_action = action_row['vote_action']
                action_total = int(action_row['total'])
                action_correct = int(action_row['correct'] or 0)
                best_action_accuracy = action_correct / action_total if action_total > 0 else 0.0
            
            return {
                'total_votes': total,
                'correct_votes': correct,
                'accuracy': accuracy,
                'avg_return': float(row['avg_return'] or 0.0),
                'avg_confidence': float(row['avg_confidence'] or 0.0),
                'best_action': best_action,
                'best_action_accuracy': best_action_accuracy
            }
        
        finally:
            await conn.close()
    
    def calculate_weight_from_accuracy(self, accuracy: float) -> float:
        """
        정확도 기반 가중치 계산
        
        Args:
            accuracy: 정확도 (0.0 ~ 1.0)
        
        Returns:
            가중치 배율 (0.5 ~ 1.2)
        """
        for tier, rule in self.WEIGHT_RULES.items():
            if accuracy >= rule['min_accuracy']:
                logger.info(f"Accuracy {accuracy:.1%} → tier {tier} → weight {rule['multiplier']:.1f}x")
                return rule['multiplier']
        
        # 최저 등급 (poor)
        return self.WEIGHT_RULES['poor']['multiplier']
    
    async def calculate_agent_weight(
        self,
        agent_name: str,
        lookback_days: int = 30
    ) -> Tuple[float, str]:
        """
        에이전트 가중치 계산
        
        Args:
            agent_name: 에이전트 이름
            lookback_days: 조회 기간
        
        Returns:
            (new_weight, reason)
        """
        # 1. 성과 데이터 조회
        performance = await self.get_agent_performance(agent_name, lookback_days)
        
        if performance is None or performance['total_votes'] < 10:
            # 샘플 부족 → 기본 가중치 유지
            default_weight = self.DEFAULT_WEIGHTS.get(agent_name, 0.15)
            return default_weight, f"Insufficient data ({performance['total_votes'] if performance else 0} votes)"
        
        # 2. 정확도 기반 배율 계산
        accuracy = performance['accuracy']
        multiplier = self.calculate_weight_from_accuracy(accuracy)
        
        # 3. 기본 가중치 × 배율
        default_weight = self.DEFAULT_WEIGHTS.get(agent_name, 0.15)
        new_weight = default_weight * multiplier
        
        # 4. 가중치 범위 제한 (0.05 ~ 0.30)
        new_weight = max(0.05, min(0.30, new_weight))
        
        reason = f"Accuracy {accuracy:.1%} ({performance['correct_votes']}/{performance['total_votes']}) → {multiplier:.1f}x"
        
        return new_weight, reason
    
    async def recalculate_all_weights(
        self,
        lookback_days: int = 30,
        save_to_db: bool = True
    ) -> Dict[str, Dict]:
        """
        모든 에이전트 가중치 재계산
        
        Args:
            lookback_days: 조회 기간
            save_to_db: DB 저장 여부
        
        Returns:
            {
                'agent_name': {
                    'old_weight': float,
                    'new_weight': float,
                    'change': float,
                    'reason': str
                }
            }
        """
        results = {}
        
        # 기존 가중치 조회 (DB 또는 기본값)
        old_weights = await self.get_current_weights()
        
        for agent_name in self.DEFAULT_WEIGHTS.keys():
            old_weight = old_weights.get(agent_name, self.DEFAULT_WEIGHTS[agent_name])
            new_weight, reason = await self.calculate_agent_weight(agent_name, lookback_days)
            
            # 점진적 업데이트 (최대 변화 제한)
            weight_change = new_weight - old_weight
            if abs(weight_change) > self.MAX_WEIGHT_CHANGE:
                logger.warning(
                    f"{agent_name}: Weight change {weight_change:+.0%} exceeds limit {self.MAX_WEIGHT_CHANGE:.0%}"
                )
                # 변화를 MAX_WEIGHT_CHANGE로 제한
                if weight_change > 0:
                    new_weight = old_weight + self.MAX_WEIGHT_CHANGE
                else:
                    new_weight = old_weight - self.MAX_WEIGHT_CHANGE
                
                reason += f" (capped at {self.MAX_WEIGHT_CHANGE:.0%} change)"
            
            results[agent_name] = {
                'old_weight': old_weight,
                'new_weight': new_weight,
                'change': new_weight - old_weight,
                'reason': reason
            }
            
            logger.info(f"{agent_name}: {old_weight:.3f} → {new_weight:.3f} ({reason})")
        
        # DB 저장
        if save_to_db:
            await self.save_weights_to_db(results)
        
        return results
    
    async def get_current_weights(self) -> Dict[str, float]:
        """
        현재 에이전트 가중치 조회 (DB 또는 기본값)
        
        Returns:
            {'agent_name': weight}
        """
        conn = await self.get_db_connection()
        
        try:
            # 가장 최근 가중치 조회
            query = """
                SELECT DISTINCT ON (agent_name)
                    agent_name,
                    weights->>'new_weight' as weight
                FROM agent_weights_history
                ORDER BY agent_name, created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            if rows:
                return {row['agent_name']: float(row['weight']) for row in rows}
            else:
                # DB에 없으면 기본값 반환
                return self.DEFAULT_WEIGHTS.copy()
        
        except Exception as e:
            # 테이블 없거나 에러 → 기본값
            logger.warning(f"Failed to get current weights: {e}")
            return self.DEFAULT_WEIGHTS.copy()
        
        finally:
            await conn.close()
    
    async def save_weights_to_db(self, results: Dict[str, Dict]):
        """
        가중치 변경 이력 저장
        
        Table: agent_weights_history
        Columns: agent_name, date, weights (JSONB), created_at
        """
        conn = await self.get_db_connection()
        
        try:
            # 테이블 존재 확인 및 생성
            create_table_query = """
                CREATE TABLE IF NOT EXISTS agent_weights_history (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(50) NOT NULL,
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    weights JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_weights_agent_date 
                ON agent_weights_history(agent_name, date DESC);
            """
            await conn.execute(create_table_query)
            
            # 각 에이전트 가중치 저장
            for agent_name, data in results.items():
                insert_query = """
                    INSERT INTO agent_weights_history (agent_name, weights)
                    VALUES ($1, $2)
                """
                await conn.execute(insert_query, agent_name, data)
            
            logger.info(f"✅ Saved {len(results)} agent weight updates to DB")
        
        except Exception as e:
            logger.error(f"Failed to save weights to DB: {e}")
        
        finally:
            await conn.close()
    
    def detect_overconfidence(
        self,
        avg_confidence: float,
        accuracy: float,
        gap_threshold: float = 0.20
    ) -> bool:
        """
        오버컨피던트 탐지
        
        Args:
            avg_confidence: 평균 신뢰도
            accuracy: 실제 정확도
            gap_threshold: 임계값 (기본 20%)
        
        Returns:
            True if overconfident (신뢰도 >> 정확도)
        """
        gap = avg_confidence - accuracy
        is_overconfident = gap > gap_threshold
        
        if is_overconfident:
            logger.warning(
                f"Overconfident detected: confidence {avg_confidence:.1%} vs accuracy {accuracy:.1%} "
                f"(gap {gap:.1%})"
            )
        
        return is_overconfident
    
    def detect_underconfidence(
        self,
        avg_confidence: float,
        accuracy: float,
        gap_threshold: float = 0.20
    ) -> bool:
        """
        언더컨피던트 탐지
        
        Args:
            avg_confidence: 평균 신뢰도
            accuracy: 실제 정확도
            gap_threshold: 임계값 (기본 20%)
        
        Returns:
            True if underconfident (정확도 >> 신뢰도)
        """
        gap = accuracy - avg_confidence
        is_underconfident = gap > gap_threshold
        
        if is_underconfident:
            logger.info(
                f"Underconfident detected: accuracy {accuracy:.1%} vs confidence {avg_confidence:.1%} "
                f"(gap {gap:.1%})"
            )
        
        return is_underconfident


# ============================================================================
# CLI 실행
# ============================================================================

async def main():
    """가중치 재계산 실행"""
    adjuster = AgentWeightAdjuster()
    
    logger.info("========== Agent Weight Recalculation ==========")
    logger.info(f"Lookback period: 30 days")
    logger.info("")
    
    results = await adjuster.recalculate_all_weights(lookback_days=30, save_to_db=True)
    
    logger.info("")
    logger.info("========== Summary ==========")
    for agent, data in results.items():
        change_pct = data['change'] * 100 /  data['old_weight'] if data['old_weight'] > 0 else 0
        logger.info(
            f"{agent:15s}: {data['old_weight']:.3f} → {data['new_weight']:.3f} "
            f"({change_pct:+.1f}%) - {data['reason']}"
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
