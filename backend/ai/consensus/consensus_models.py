"""
Consensus Engine Data Models

Consensus 투표 결과 및 관련 데이터 구조

작성일: 2025-12-06
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class VoteDecision(str, Enum):
    """개별 AI의 투표 결정"""
    APPROVE = "approve"       # 찬성
    REJECT = "reject"         # 반대
    ABSTAIN = "abstain"       # 기권 (불확실)


class ConsensusStrength(str, Enum):
    """Consensus 강도"""
    UNANIMOUS = "unanimous"           # 만장일치 (3/3)
    STRONG = "strong"                 # 강한 합의 (2/3)
    WEAK = "weak"                     # 약한 합의 (1/3)
    NO_CONSENSUS = "no_consensus"     # 합의 없음 (0/3)


class AIVote(BaseModel):
    """개별 AI의 투표 결과"""
    ai_model: str = Field(..., description="AI 모델명 (claude/chatgpt/gemini)")
    decision: VoteDecision = Field(..., description="투표 결정")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0~1)")
    reasoning: str = Field(..., description="투표 근거")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="리스크 점수")
    timestamp: datetime = Field(default_factory=datetime.now, description="투표 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "ai_model": "claude",
                "decision": "approve",
                "confidence": 0.85,
                "reasoning": "Strong fundamentals support this position",
                "risk_score": 0.25,
                "timestamp": "2025-12-06T10:30:00Z"
            }
        }


class ConsensusResult(BaseModel):
    """
    Consensus 투표 최종 결과

    3개 AI의 투표를 집계하여 최종 승인 여부 결정
    """
    # 최종 결정
    approved: bool = Field(..., description="최종 승인 여부")
    action: str = Field(..., description="투표 대상 액션 (BUY/SELL/DCA/STOP_LOSS)")

    # 투표 상세
    votes: Dict[str, AIVote] = Field(..., description="AI별 투표 결과")
    approve_count: int = Field(..., ge=0, le=3, description="찬성 수 (0~3)")
    reject_count: int = Field(..., ge=0, le=3, description="반대 수 (0~3)")
    total_votes: int = Field(default=3, ge=0, le=3, description="총 투표 수 (기본 3)")

    # Consensus 메트릭
    consensus_strength: ConsensusStrength = Field(..., description="합의 강도")
    confidence_avg: float = Field(..., ge=0.0, le=1.0, description="평균 신뢰도")
    risk_score_avg: Optional[float] = Field(None, ge=0.0, le=1.0, description="평균 리스크 점수")

    # 메타데이터
    ticker: Optional[str] = Field(None, description="종목 티커")
    vote_requirement: str = Field(..., description="투표 요구사항 (1/3, 2/3, 3/3)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Consensus 시각")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "action": "BUY",
                "votes": {
                    "claude": {
                        "ai_model": "claude",
                        "decision": "approve",
                        "confidence": 0.85,
                        "reasoning": "Strong fundamentals"
                    },
                    "chatgpt": {
                        "ai_model": "chatgpt",
                        "decision": "approve",
                        "confidence": 0.78,
                        "reasoning": "Positive market regime"
                    },
                    "gemini": {
                        "ai_model": "gemini",
                        "decision": "reject",
                        "confidence": 0.65,
                        "reasoning": "High volatility risk"
                    }
                },
                "approve_count": 2,
                "reject_count": 1,
                "consensus_strength": "strong",
                "confidence_avg": 0.76,
                "risk_score_avg": 0.30,
                "ticker": "NVDA",
                "vote_requirement": "2/3",
                "timestamp": "2025-12-06T10:30:00Z"
            }
        }


class VoteRequest(BaseModel):
    """
    Consensus 투표 요청

    특정 액션에 대해 3개 AI에게 투표 요청
    """
    ticker: str = Field(..., description="종목 티커")
    action: str = Field(..., description="투표 대상 액션")
    current_price: Optional[float] = Field(None, description="현재 가격")
    target_price: Optional[float] = Field(None, description="목표 가격")
    stop_loss: Optional[float] = Field(None, description="손절가")
    position_size: Optional[float] = Field(None, ge=0.0, le=1.0, description="포지션 크기")

    # MarketContext 요약 (전체 전달은 내부적으로)
    market_context_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="시장 컨텍스트 요약"
    )

    # DCA 관련 (DCA 액션일 경우)
    avg_entry_price: Optional[float] = Field(None, description="평균 매수가")
    dca_count: Optional[int] = Field(None, ge=0, description="현재 DCA 횟수")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "action": "BUY",
                "current_price": 145.50,
                "target_price": 165.00,
                "stop_loss": 135.00,
                "position_size": 0.15,
                "market_context_summary": {
                    "segment": "training",
                    "sentiment": 0.85,
                    "risk_level": "moderate"
                }
            }
        }


class ConsensusStats(BaseModel):
    """Consensus Engine 통계"""
    total_votes: int = Field(0, description="총 투표 수")
    approved_votes: int = Field(0, description="승인된 투표 수")
    rejected_votes: int = Field(0, description="거부된 투표 수")
    approval_rate: float = Field(0.0, ge=0.0, le=1.0, description="승인율")

    votes_by_action: Dict[str, int] = Field(
        default_factory=dict,
        description="액션별 투표 수"
    )

    ai_agreement_rate: Dict[str, float] = Field(
        default_factory=dict,
        description="AI별 다수 의견 일치율"
    )

    avg_consensus_time_ms: float = Field(0.0, description="평균 Consensus 시간 (ms)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_votes": 150,
                "approved_votes": 95,
                "rejected_votes": 55,
                "approval_rate": 0.633,
                "votes_by_action": {
                    "BUY": 80,
                    "SELL": 30,
                    "DCA": 25,
                    "STOP_LOSS": 15
                },
                "ai_agreement_rate": {
                    "claude": 0.72,
                    "chatgpt": 0.68,
                    "gemini": 0.65
                },
                "avg_consensus_time_ms": 1250.5
            }
        }
