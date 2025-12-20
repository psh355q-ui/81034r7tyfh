"""
Adaptive Weight Manager

Agent 가중치를 성과에 따라 동적 조정
- 정확도 높은 Agent의 가중치 증가
- 최근 30일 성과 기반
- 최소/최대 가중치 제한 (0.15 ~ 0.50)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class AgentWeight:
    """에이전트 가중치"""
    agent_name: str
    base_weight: float  # 기본 가중치
    current_weight: float  # 현재 가중치
    accuracy_30d: float  # 30일 정확도
    total_predictions: int  # 총 예측 수
    correct_predictions: int  # 맞은 예측 수
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class WeightAdjustmentLog:
    """가중치 조정 로그"""
    timestamp: datetime
    agent_name: str
    old_weight: float
    new_weight: float
    reason: str
    accuracy: float


class AdaptiveWeightManager:
    """
    Adaptive Weight Manager
    
    AI Council의 Agent 가중치를 성과에 따라 동적으로 조정합니다.
    
    조정 원칙:
    1. 정확도가 높은 Agent의 가중치 증가
    2. 최근 30일 성과 기반 (최신 데이터 가중)
    3. 최소 0.15, 최대 0.50으로 제한
    4. 급격한 변동 방지 (최대 ±0.05/주)
    """
    
    # 기본 가중치
    DEFAULT_WEIGHTS = {
        "fundamental": 0.30,
        "insider": 0.40,
        "macro": 0.30,
    }
    
    def __init__(
        self,
        min_weight: float = 0.15,
        max_weight: float = 0.50,
        max_adjustment_per_week: float = 0.05,
        min_predictions_for_adjust: int = 10,
    ):
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.max_adjustment_per_week = max_adjustment_per_week
        self.min_predictions_for_adjust = min_predictions_for_adjust
        
        # 현재 가중치
        self._weights: Dict[str, AgentWeight] = {}
        self._initialize_weights()
        
        # 조정 로그
        self._adjustment_logs: List[WeightAdjustmentLog] = []
        
        # 예측 히스토리 (agent_name -> list of (timestamp, correct))
        self._prediction_history: Dict[str, List[tuple]] = {}
    
    def _initialize_weights(self):
        """가중치 초기화"""
        for agent_name, weight in self.DEFAULT_WEIGHTS.items():
            self._weights[agent_name] = AgentWeight(
                agent_name=agent_name,
                base_weight=weight,
                current_weight=weight,
                accuracy_30d=0.0,
                total_predictions=0,
                correct_predictions=0,
            )
    
    def record_prediction(
        self,
        agent_name: str,
        correct: bool,
        timestamp: datetime = None,
    ):
        """
        예측 결과 기록
        
        Args:
            agent_name: 에이전트 이름
            correct: 예측 정확 여부
            timestamp: 예측 시간
        """
        if agent_name not in self._prediction_history:
            self._prediction_history[agent_name] = []
        
        ts = timestamp or datetime.now()
        self._prediction_history[agent_name].append((ts, correct))
        
        # 가중치 객체 업데이트
        if agent_name in self._weights:
            agent = self._weights[agent_name]
            agent.total_predictions += 1
            if correct:
                agent.correct_predictions += 1
    
    async def get_adjusted_weights(self) -> Dict[str, float]:
        """
        조정된 가중치 반환
        
        Returns:
            Dict[str, float]: agent_name -> weight
        """
        await self._recalculate_weights()
        
        return {
            name: agent.current_weight
            for name, agent in self._weights.items()
        }
    
    async def _recalculate_weights(self):
        """가중치 재계산"""
        now = datetime.now()
        cutoff_30d = now - timedelta(days=30)
        
        accuracies = {}
        
        for agent_name, agent in self._weights.items():
            # 30일 이내 예측만 필터링
            history = self._prediction_history.get(agent_name, [])
            recent = [(ts, correct) for ts, correct in history if ts >= cutoff_30d]
            
            if len(recent) < self.min_predictions_for_adjust:
                # 데이터 부족 시 기본 가중치 유지
                accuracies[agent_name] = None
                continue
            
            # 정확도 계산 (최신 데이터 가중)
            accuracy = self._calculate_weighted_accuracy(recent)
            accuracies[agent_name] = accuracy
            agent.accuracy_30d = accuracy
        
        # 가중치 조정
        self._adjust_weights(accuracies)
    
    def _calculate_weighted_accuracy(
        self,
        history: List[tuple],
    ) -> float:
        """
        가중 정확도 계산
        
        최신 예측에 더 높은 가중치 부여
        """
        if not history:
            return 0.0
        
        # 시간순 정렬
        sorted_history = sorted(history, key=lambda x: x[0])
        
        total_weight = 0
        weighted_correct = 0
        
        for i, (ts, correct) in enumerate(sorted_history):
            # 최신일수록 가중치 증가 (1 ~ 2)
            weight = 1 + (i / len(sorted_history))
            total_weight += weight
            if correct:
                weighted_correct += weight
        
        return weighted_correct / total_weight if total_weight > 0 else 0.0
    
    def _adjust_weights(self, accuracies: Dict[str, Optional[float]]):
        """가중치 조정 실행"""
        # 유효한 정확도를 가진 에이전트만
        valid_agents = {k: v for k, v in accuracies.items() if v is not None}
        
        if not valid_agents:
            return
        
        # 평균 정확도
        avg_accuracy = sum(valid_agents.values()) / len(valid_agents)
        
        for agent_name, accuracy in valid_agents.items():
            agent = self._weights[agent_name]
            old_weight = agent.current_weight
            
            # 정확도가 평균보다 높으면 가중치 증가
            if accuracy > avg_accuracy:
                adjustment = min(
                    self.max_adjustment_per_week,
                    (accuracy - avg_accuracy) * 0.2
                )
                new_weight = old_weight + adjustment
            else:
                adjustment = min(
                    self.max_adjustment_per_week,
                    (avg_accuracy - accuracy) * 0.2
                )
                new_weight = old_weight - adjustment
            
            # 범위 제한
            new_weight = max(self.min_weight, min(self.max_weight, new_weight))
            
            # 변경 사항 기록
            if abs(new_weight - old_weight) > 0.001:
                agent.current_weight = new_weight
                agent.last_updated = datetime.now()
                
                self._adjustment_logs.append(WeightAdjustmentLog(
                    timestamp=datetime.now(),
                    agent_name=agent_name,
                    old_weight=old_weight,
                    new_weight=new_weight,
                    reason=f"정확도 {accuracy:.1%} (평균 {avg_accuracy:.1%})",
                    accuracy=accuracy,
                ))
                
                logger.info(
                    f"가중치 조정: {agent_name} {old_weight:.2f} → {new_weight:.2f} "
                    f"(정확도: {accuracy:.1%})"
                )
        
        # 가중치 합이 1이 되도록 정규화
        self._normalize_weights()
    
    def _normalize_weights(self):
        """가중치 정규화 (합이 1이 되도록)"""
        total = sum(a.current_weight for a in self._weights.values())
        
        if total > 0:
            for agent in self._weights.values():
                agent.current_weight = agent.current_weight / total
    
    def get_weight_summary(self) -> Dict[str, Any]:
        """가중치 요약 반환"""
        return {
            "weights": {
                name: {
                    "base": round(agent.base_weight, 3),
                    "current": round(agent.current_weight, 3),
                    "change": round(agent.current_weight - agent.base_weight, 3),
                    "accuracy_30d": round(agent.accuracy_30d, 3),
                    "total_predictions": agent.total_predictions,
                    "correct_predictions": agent.correct_predictions,
                }
                for name, agent in self._weights.items()
            },
            "last_adjustments": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "agent": log.agent_name,
                    "old": round(log.old_weight, 3),
                    "new": round(log.new_weight, 3),
                    "reason": log.reason,
                }
                for log in self._adjustment_logs[-10:]  # 최근 10개
            ],
        }
    
    def get_agent_report(self, agent_name: str) -> Optional[Dict]:
        """개별 에이전트 리포트"""
        if agent_name not in self._weights:
            return None
        
        agent = self._weights[agent_name]
        history = self._prediction_history.get(agent_name, [])
        
        # 최근 30일 통계
        cutoff = datetime.now() - timedelta(days=30)
        recent = [h for h in history if h[0] >= cutoff]
        recent_correct = sum(1 for _, c in recent if c)
        
        return {
            "agent_name": agent_name,
            "current_weight": round(agent.current_weight, 3),
            "base_weight": round(agent.base_weight, 3),
            "weight_change": round(agent.current_weight - agent.base_weight, 3),
            "total_predictions": agent.total_predictions,
            "correct_predictions": agent.correct_predictions,
            "accuracy_all_time": round(
                agent.correct_predictions / agent.total_predictions, 3
            ) if agent.total_predictions > 0 else 0,
            "predictions_30d": len(recent),
            "correct_30d": recent_correct,
            "accuracy_30d": round(
                recent_correct / len(recent), 3
            ) if recent else 0,
            "last_updated": agent.last_updated.isoformat(),
        }
    
    def reset_weights(self):
        """가중치 초기화"""
        self._initialize_weights()
        self._adjustment_logs.clear()
        logger.info("가중치가 초기화되었습니다.")
