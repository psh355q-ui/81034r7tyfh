"""
Agent Weight Trainer - AI 에이전트 성과 기반 가중치 자동 조정

Phase F1: AI 집단지성 고도화

각 AI 에이전트의 과거 성과를 분석하여 투표 가중치를 동적으로 조정
성과가 좋은 에이전트에게 더 높은 영향력 부여

가중치 조정 공식:
new_weight = (win_rate * 0.5) + (avg_return * 0.3) - (max_drawdown * 0.2)

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 성과 메트릭 구조
# ═══════════════════════════════════════════════════════════════

@dataclass
class TradeOutcome:
    """개별 거래 결과"""
    timestamp: datetime
    ticker: str
    agent_vote: str  # BUY, SELL, HOLD
    actual_outcome: str  # PROFIT, LOSS, NEUTRAL
    pnl_amount: float
    pnl_percentage: float
    confidence_at_vote: float
    
    def was_correct(self) -> bool:
        """예측이 맞았는지 판정"""
        if self.agent_vote == "BUY" and self.actual_outcome == "PROFIT":
            return True
        if self.agent_vote == "SELL" and self.actual_outcome == "LOSS":
            return True  # 매도 후 하락 = 올바른 판단
        if self.agent_vote == "HOLD" and self.actual_outcome == "NEUTRAL":
            return True
        return False


@dataclass
class AgentPerformanceMetrics:
    """에이전트 성과 메트릭"""
    agent_name: str
    period_start: datetime
    period_end: datetime
    
    # 거래 통계
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # 성과 지표
    win_rate: float = 0.5
    avg_return: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    
    # 예측 정확도
    prediction_accuracy: float = 0.5
    
    # 신뢰도 보정
    avg_confidence: float = 0.5
    confidence_calibration: float = 1.0  # 예측 정확도 / 평균 신뢰도
    
    # 현재 가중치
    current_weight: float = 1.0
    recommended_weight: float = 1.0
    
    # 메타 정보
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "trades": {
                "total": self.total_trades,
                "winning": self.winning_trades,
                "losing": self.losing_trades
            },
            "metrics": {
                "win_rate": self.win_rate,
                "avg_return": self.avg_return,
                "total_return": self.total_return,
                "max_drawdown": self.max_drawdown,
                "sharpe_ratio": self.sharpe_ratio,
                "prediction_accuracy": self.prediction_accuracy
            },
            "confidence": {
                "average": self.avg_confidence,
                "calibration": self.confidence_calibration
            },
            "weight": {
                "current": self.current_weight,
                "recommended": self.recommended_weight
            },
            "last_updated": self.last_updated.isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# Agent Weight Trainer 클래스
# ═══════════════════════════════════════════════════════════════

class AgentWeightTrainer:
    """
    AI 에이전트 성과 기반 가중치 조정 시스템
    
    Usage:
        trainer = AgentWeightTrainer()
        
        # 거래 결과 기록
        trainer.record_outcome(
            agent_name="claude",
            ticker="NVDA",
            vote="BUY",
            outcome="PROFIT",
            pnl_amount=500,
            pnl_percentage=5.0,
            confidence=0.75
        )
        
        # 가중치 재계산
        weights = trainer.recalculate_weights()
        
        # 에이전트별 성과 조회
        metrics = trainer.get_agent_metrics("claude")
    """
    
    # 가중치 조정 상수
    WIN_RATE_WEIGHT = 0.5
    AVG_RETURN_WEIGHT = 0.3
    MAX_DRAWDOWN_PENALTY = 0.2
    
    # 가중치 범위
    MIN_WEIGHT = 0.1
    MAX_WEIGHT = 3.0
    DEFAULT_WEIGHT = 1.0
    
    # EMA 학습률
    LEARNING_RATE = 0.1
    
    def __init__(
        self,
        agents: Optional[List[str]] = None,
        storage_path: Optional[Path] = None,
        lookback_days: int = 30
    ):
        """
        Args:
            agents: 관리할 에이전트 목록
            storage_path: 데이터 저장 경로
            lookback_days: 성과 분석 기간 (일)
        """
        self.agents = agents or ["claude", "chatgpt", "gemini"]
        self.storage_path = storage_path
        self.lookback_days = lookback_days
        
        # 거래 기록
        self._outcomes: Dict[str, List[TradeOutcome]] = {
            agent: [] for agent in self.agents
        }
        
        # 성과 메트릭
        self._metrics: Dict[str, AgentPerformanceMetrics] = {}
        
        # 현재 가중치
        self._weights: Dict[str, float] = {
            agent: self.DEFAULT_WEIGHT for agent in self.agents
        }
        
        # 가중치 변경 히스토리
        self._weight_history: List[Dict[str, Any]] = []
        
        # 저장 경로 초기화
        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)
            self._load_existing_data()
        
        logger.info(
            f"AgentWeightTrainer initialized: agents={self.agents}, "
            f"lookback={lookback_days}days"
        )
    
    def record_outcome(
        self,
        agent_name: str,
        ticker: str,
        vote: str,
        outcome: str,
        pnl_amount: float,
        pnl_percentage: float,
        confidence: float
    ):
        """
        거래 결과 기록
        
        Args:
            agent_name: 에이전트 이름
            ticker: 종목 티커
            vote: 투표 (BUY, SELL, HOLD)
            outcome: 결과 (PROFIT, LOSS, NEUTRAL)
            pnl_amount: 손익 금액
            pnl_percentage: 손익률
            confidence: 투표 시 신뢰도
        """
        if agent_name not in self._outcomes:
            self._outcomes[agent_name] = []
        
        trade = TradeOutcome(
            timestamp=datetime.now(),
            ticker=ticker,
            agent_vote=vote.upper(),
            actual_outcome=outcome.upper(),
            pnl_amount=pnl_amount,
            pnl_percentage=pnl_percentage,
            confidence_at_vote=confidence
        )
        
        self._outcomes[agent_name].append(trade)
        
        logger.debug(
            f"Recorded outcome for {agent_name}: {ticker} {vote} -> {outcome} "
            f"(PnL: {pnl_percentage:.2f}%)"
        )
        
        # 저장
        if self.storage_path:
            self._save_outcomes()
    
    def recalculate_weights(
        self,
        apply_immediately: bool = True
    ) -> Dict[str, float]:
        """
        모든 에이전트의 가중치 재계산
        
        Args:
            apply_immediately: 즉시 적용 여부
            
        Returns:
            새로운 가중치 딕셔너리
        """
        new_weights = {}
        
        for agent in self.agents:
            metrics = self._calculate_metrics(agent)
            self._metrics[agent] = metrics
            
            # 새 가중치 계산
            new_weight = self._calculate_weight(metrics)
            new_weights[agent] = new_weight
            metrics.recommended_weight = new_weight
            
            logger.info(
                f"[{agent}] Weight: {self._weights[agent]:.3f} -> {new_weight:.3f} "
                f"(win_rate={metrics.win_rate:.2%}, avg_return={metrics.avg_return:.2%})"
            )
        
        if apply_immediately:
            old_weights = self._weights.copy()
            self._weights = new_weights
            
            # 히스토리 기록
            self._weight_history.append({
                "timestamp": datetime.now().isoformat(),
                "old_weights": old_weights,
                "new_weights": new_weights
            })
            
            # 저장
            if self.storage_path:
                self._save_weights()
        
        return new_weights
    
    def _calculate_metrics(self, agent_name: str) -> AgentPerformanceMetrics:
        """에이전트 성과 메트릭 계산"""
        outcomes = self._outcomes.get(agent_name, [])
        
        # 기간 필터링
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        recent_outcomes = [o for o in outcomes if o.timestamp >= cutoff]
        
        metrics = AgentPerformanceMetrics(
            agent_name=agent_name,
            period_start=cutoff,
            period_end=datetime.now(),
            current_weight=self._weights.get(agent_name, self.DEFAULT_WEIGHT)
        )
        
        if not recent_outcomes:
            return metrics
        
        # 기본 통계
        metrics.total_trades = len(recent_outcomes)
        metrics.winning_trades = sum(1 for o in recent_outcomes if o.pnl_amount > 0)
        metrics.losing_trades = sum(1 for o in recent_outcomes if o.pnl_amount < 0)
        
        # 승률
        if metrics.total_trades > 0:
            metrics.win_rate = metrics.winning_trades / metrics.total_trades
        
        # 수익률 통계
        returns = [o.pnl_percentage for o in recent_outcomes]
        if returns:
            metrics.avg_return = sum(returns) / len(returns)
            metrics.total_return = sum(returns)
            
            # 최대 손실 (Max Drawdown 근사)
            negative_returns = [r for r in returns if r < 0]
            metrics.max_drawdown = abs(min(negative_returns)) if negative_returns else 0.0
            
            # 샤프 비율 (간소화)
            if len(returns) > 1:
                import statistics
                try:
                    std_dev = statistics.stdev(returns)
                    if std_dev > 0:
                        metrics.sharpe_ratio = metrics.avg_return / std_dev
                except:
                    pass
        
        # 예측 정확도
        correct = sum(1 for o in recent_outcomes if o.was_correct())
        metrics.prediction_accuracy = correct / len(recent_outcomes)
        
        # 신뢰도 보정
        confidences = [o.confidence_at_vote for o in recent_outcomes]
        if confidences:
            metrics.avg_confidence = sum(confidences) / len(confidences)
            if metrics.avg_confidence > 0:
                metrics.confidence_calibration = (
                    metrics.prediction_accuracy / metrics.avg_confidence
                )
        
        return metrics
    
    def _calculate_weight(self, metrics: AgentPerformanceMetrics) -> float:
        """
        성과 기반 가중치 계산
        
        공식:
        base_weight = (win_rate * 0.5) + (normalized_return * 0.3) - (drawdown_penalty * 0.2)
        final_weight = clip(base_weight, MIN_WEIGHT, MAX_WEIGHT)
        """
        # 수익률 정규화 (-10% ~ +10% -> 0 ~ 1)
        normalized_return = max(0, min(1, (metrics.avg_return + 10) / 20))
        
        # 드로다운 패널티 정규화 (0% ~ 20% -> 0 ~ 1)
        drawdown_penalty = min(1, metrics.max_drawdown / 20)
        
        # 기본 가중치 계산
        base_weight = (
            (metrics.win_rate * self.WIN_RATE_WEIGHT) +
            (normalized_return * self.AVG_RETURN_WEIGHT) -
            (drawdown_penalty * self.MAX_DRAWDOWN_PENALTY)
        )
        
        # 신뢰도 보정 적용
        # 과신하는 에이전트 (calibration < 1) 패널티
        # 보수적인 에이전트 (calibration > 1) 보너스
        calibration_factor = min(1.2, max(0.8, metrics.confidence_calibration))
        base_weight *= calibration_factor
        
        # EMA 방식으로 기존 가중치와 혼합
        current = metrics.current_weight
        new_weight = (
            (1 - self.LEARNING_RATE) * current +
            self.LEARNING_RATE * (base_weight * 2)  # 2를 곱해 1.0 기준으로 스케일링
        )
        
        # 범위 제한
        return max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, new_weight))
    
    def get_weight(self, agent_name: str) -> float:
        """에이전트 현재 가중치 조회"""
        return self._weights.get(agent_name, self.DEFAULT_WEIGHT)
    
    def get_all_weights(self) -> Dict[str, float]:
        """모든 에이전트 가중치 조회"""
        return self._weights.copy()
    
    def set_weight(self, agent_name: str, weight: float):
        """수동 가중치 설정"""
        clamped = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, weight))
        old_weight = self._weights.get(agent_name, self.DEFAULT_WEIGHT)
        self._weights[agent_name] = clamped
        
        logger.info(f"Manual weight update: {agent_name} {old_weight:.3f} -> {clamped:.3f}")
        
        if self.storage_path:
            self._save_weights()
    
    def get_agent_metrics(
        self, 
        agent_name: str
    ) -> Optional[AgentPerformanceMetrics]:
        """에이전트 성과 메트릭 조회"""
        if agent_name not in self._metrics:
            self._metrics[agent_name] = self._calculate_metrics(agent_name)
        return self._metrics.get(agent_name)
    
    def get_all_metrics(self) -> Dict[str, AgentPerformanceMetrics]:
        """모든 에이전트 메트릭 조회"""
        for agent in self.agents:
            if agent not in self._metrics:
                self._metrics[agent] = self._calculate_metrics(agent)
        return self._metrics.copy()
    
    def get_ranking(self) -> List[Tuple[str, float]]:
        """성과 기반 에이전트 순위"""
        metrics_list = [(agent, self.get_agent_metrics(agent)) for agent in self.agents]
        
        # 정렬 기준: 추천 가중치 (높을수록 좋음)
        sorted_agents = sorted(
            metrics_list,
            key=lambda x: x[1].recommended_weight if x[1] else 0,
            reverse=True
        )
        
        return [(agent, m.recommended_weight) for agent, m in sorted_agents]
    
    def get_summary(self) -> Dict[str, Any]:
        """전체 요약"""
        all_metrics = self.get_all_metrics()
        
        return {
            "agents": {
                agent: {
                    "current_weight": self._weights.get(agent, 1.0),
                    "win_rate": m.win_rate if m else None,
                    "avg_return": m.avg_return if m else None,
                    "total_trades": m.total_trades if m else 0
                }
                for agent, m in all_metrics.items()
            },
            "ranking": self.get_ranking(),
            "lookback_days": self.lookback_days,
            "weight_updates": len(self._weight_history)
        }
    
    def _save_weights(self):
        """가중치 저장"""
        if not self.storage_path:
            return
        
        weights_file = self.storage_path / "agent_weights.json"
        with open(weights_file, "w", encoding="utf-8") as f:
            json.dump({
                "weights": self._weights,
                "history": self._weight_history[-100:],  # 최근 100개만
                "updated_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def _save_outcomes(self):
        """거래 결과 저장"""
        if not self.storage_path:
            return
        
        for agent, outcomes in self._outcomes.items():
            file_path = self.storage_path / f"outcomes_{agent}.jsonl"
            with open(file_path, "w", encoding="utf-8") as f:
                for outcome in outcomes:
                    record = {
                        "timestamp": outcome.timestamp.isoformat(),
                        "ticker": outcome.ticker,
                        "vote": outcome.agent_vote,
                        "outcome": outcome.actual_outcome,
                        "pnl_amount": outcome.pnl_amount,
                        "pnl_percentage": outcome.pnl_percentage,
                        "confidence": outcome.confidence_at_vote
                    }
                    f.write(json.dumps(record) + "\n")
    
    def _load_existing_data(self):
        """기존 데이터 로드"""
        if not self.storage_path:
            return
        
        # 가중치 로드
        weights_file = self.storage_path / "agent_weights.json"
        if weights_file.exists():
            with open(weights_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._weights = data.get("weights", self._weights)
                self._weight_history = data.get("history", [])
            logger.info(f"Loaded weights: {self._weights}")
        
        # 거래 결과 로드
        for agent in self.agents:
            file_path = self.storage_path / f"outcomes_{agent}.jsonl"
            if file_path.exists():
                outcomes = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        record = json.loads(line.strip())
                        outcomes.append(TradeOutcome(
                            timestamp=datetime.fromisoformat(record["timestamp"]),
                            ticker=record["ticker"],
                            agent_vote=record["vote"],
                            actual_outcome=record["outcome"],
                            pnl_amount=record["pnl_amount"],
                            pnl_percentage=record["pnl_percentage"],
                            confidence_at_vote=record["confidence"]
                        ))
                self._outcomes[agent] = outcomes
                logger.info(f"Loaded {len(outcomes)} outcomes for {agent}")


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_weight_trainer: Optional[AgentWeightTrainer] = None


def get_weight_trainer(storage_path: Optional[Path] = None) -> AgentWeightTrainer:
    """AgentWeightTrainer 싱글톤 인스턴스"""
    global _weight_trainer
    if _weight_trainer is None:
        _weight_trainer = AgentWeightTrainer(storage_path=storage_path)
    return _weight_trainer


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random
    
    trainer = AgentWeightTrainer()
    
    print("=== Agent Weight Trainer Test ===\n")
    
    # 시뮬레이션 데이터 생성
    print("Generating simulation data...")
    
    tickers = ["NVDA", "AAPL", "GOOGL", "MSFT", "TSM"]
    
    # Claude: 높은 승률, 보수적
    for _ in range(20):
        is_win = random.random() < 0.65
        trainer.record_outcome(
            agent_name="claude",
            ticker=random.choice(tickers),
            vote="BUY" if random.random() > 0.3 else "HOLD",
            outcome="PROFIT" if is_win else "LOSS",
            pnl_amount=100 if is_win else -80,
            pnl_percentage=5.0 if is_win else -4.0,
            confidence=0.65 + random.random() * 0.1
        )
    
    # ChatGPT: 중간 성과
    for _ in range(20):
        is_win = random.random() < 0.55
        trainer.record_outcome(
            agent_name="chatgpt",
            ticker=random.choice(tickers),
            vote="BUY" if random.random() > 0.4 else "SELL",
            outcome="PROFIT" if is_win else "LOSS",
            pnl_amount=120 if is_win else -100,
            pnl_percentage=6.0 if is_win else -5.0,
            confidence=0.70 + random.random() * 0.15
        )
    
    # Gemini: 낮은 승률, 공격적
    for _ in range(20):
        is_win = random.random() < 0.45
        trainer.record_outcome(
            agent_name="gemini",
            ticker=random.choice(tickers),
            vote="BUY",
            outcome="PROFIT" if is_win else "LOSS",
            pnl_amount=150 if is_win else -120,
            pnl_percentage=8.0 if is_win else -6.0,
            confidence=0.80 + random.random() * 0.1
        )
    
    # 가중치 재계산
    print("\nRecalculating weights...")
    new_weights = trainer.recalculate_weights()
    
    print("\n" + "="*60)
    print("Results:")
    print("="*60)
    
    for agent in trainer.agents:
        metrics = trainer.get_agent_metrics(agent)
        print(f"\n[{agent}]")
        print(f"  Trades: {metrics.total_trades}")
        print(f"  Win Rate: {metrics.win_rate:.1%}")
        print(f"  Avg Return: {metrics.avg_return:.2f}%")
        print(f"  Max Drawdown: {metrics.max_drawdown:.2f}%")
        print(f"  Prediction Accuracy: {metrics.prediction_accuracy:.1%}")
        print(f"  Confidence Calibration: {metrics.confidence_calibration:.2f}")
        print(f"  New Weight: {new_weights[agent]:.3f}")
    
    print("\n" + "="*60)
    print("Ranking:")
    for rank, (agent, weight) in enumerate(trainer.get_ranking(), 1):
        print(f"  {rank}. {agent}: {weight:.3f}")
