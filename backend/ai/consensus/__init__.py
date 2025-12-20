"""
Consensus Engine - 3-AI 방어적 투표 시스템

Phase E1: Defensive Consensus Engine

비대칭 의사결정 로직:
- STOP_LOSS: 1명 경고 → 즉시 실행
- BUY: 2명 찬성 → 허용
- DCA: 3명 전원 동의 → 허용

작성일: 2025-12-06
"""

from backend.ai.consensus.consensus_engine import ConsensusEngine, get_consensus_engine
from backend.ai.consensus.consensus_models import (
    ConsensusResult,
    VoteDecision,
    ConsensusStrength,
    VoteRequest,
    AIVote,
    ConsensusStats
)
from backend.ai.consensus.voting_rules import VotingRules, VoteRequirement

__all__ = [
    "ConsensusEngine",
    "get_consensus_engine",
    "ConsensusResult",
    "VoteDecision",
    "ConsensusStrength",
    "VoteRequest",
    "AIVote",
    "ConsensusStats",
    "VotingRules",
    "VoteRequirement",
]
