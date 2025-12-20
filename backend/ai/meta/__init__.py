"""
AI Meta Module - 메타 학습 및 자기 개선

Phase F1: AI 집단지성 고도화
Phase F4: 자율 진화 시스템

AI 시스템의 자기 모니터링, 학습, 개선을 위한 모듈

Components:
- debate_logger: 토론 기록 시스템
- agent_weight_trainer: 성과 기반 가중치 조정
- strategy_refiner: 전략 자동 개선
"""

from backend.ai.meta.debate_logger import (
    VoteType,
    AgentVote,
    MarketContextSnapshot,
    DebateOutcome,
    DebateRecord,
    DebateLogger,
    get_debate_logger
)

from backend.ai.meta.agent_weight_trainer import (
    TradeOutcome,
    AgentPerformanceMetrics,
    AgentWeightTrainer,
    get_weight_trainer
)

from backend.ai.meta.strategy_refiner import (
    ReviewPeriod,
    ImprovementType,
    Priority,
    TradeRecord,
    PerformanceSnapshot,
    ImprovementSuggestion,
    ReflectionReport,
    StrategyRefiner,
    get_strategy_refiner
)

__all__ = [
    # Debate Logger
    "VoteType",
    "AgentVote",
    "MarketContextSnapshot",
    "DebateOutcome",
    "DebateRecord",
    "DebateLogger",
    "get_debate_logger",
    
    # Weight Trainer
    "TradeOutcome",
    "AgentPerformanceMetrics",
    "AgentWeightTrainer",
    "get_weight_trainer",
    
    # Strategy Refiner (F4)
    "ReviewPeriod",
    "ImprovementType",
    "Priority",
    "TradeRecord",
    "PerformanceSnapshot",
    "ImprovementSuggestion",
    "ReflectionReport",
    "StrategyRefiner",
    "get_strategy_refiner"
]

