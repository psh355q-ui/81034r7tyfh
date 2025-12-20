"""
Approval System - 인간 승인 워크플로우

ChatGPT Integration Feature 2:
- 제3조 (인간 최종 결정권) 완전 구현
- 고우선순위 제안은 인간 승인 필수
- 승인 레벨별 차등 적용

철학:
"AI는 추천만 할 수 있습니다. 모든 거래는 반드시 인간의 최종 승인이 필요합니다."

작성일: 2025-12-16
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4, UUID


class ApprovalLevel(Enum):
    """승인 레벨"""
    INFO_ONLY = 0       # 정보만 제공 (승인 불필요)
    SOFT_APPROVAL = 1   # 24시간 후 자동 승인
    HARD_APPROVAL = 2   # 명시적 승인 필수
    PHILOSOPHY = 3      # 철학 변경 (문서화된 근거 필요)


class ApprovalStatus(Enum):
    """승인 상태"""
    PENDING = "pending"          # 대기 중
    APPROVED = "approved"        # 승인됨
    REJECTED = "rejected"        # 거부됨
    AUTO_APPROVED = "auto_approved"  # 자동 승인 (24h 경과)
    EXPIRED = "expired"          # 만료됨


@dataclass
class ApprovalRequest:
    """승인 요청"""
    
    # 식별자
    request_id: UUID = field(default_factory=uuid4)
    
    # 제안 정보
    ticker: str = ""
    action: str = ""  # BUY, SELL, HOLD
    quantity: Optional[int] = None
    target_price: Optional[float] = None
    
    # AI 분석
    ai_reasoning: str = ""
    consensus_confidence: float = 0.0
    priority_score: float = 0.0
    debate_rounds: int = 0
    
    # 승인 정보
    approval_level: ApprovalLevel = ApprovalLevel.HARD_APPROVAL
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # 타임스탬프
    requested_at: datetime = field(default_factory=datetime.now)
    decided_at: Optional[datetime] = None
    auto_approve_after: Optional[datetime] = None  # Soft Approval용
    
    # 결정자
    decided_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "request_id": str(self.request_id),
            "ticker": self.ticker,
            "action": self.action,
            "quantity": self.quantity,
            "target_price": self.target_price,
            "ai_reasoning": self.ai_reasoning,
            "consensus_confidence": self.consensus_confidence,
            "priority_score": self.priority_score,
            "debate_rounds": self.debate_rounds,
            "approval_level": self.approval_level.name,
            "status": self.status.value,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "auto_approve_after": self.auto_approve_after.isoformat() if self.auto_approve_after else None,
            "decided_by": self.decided_by,
            "rejection_reason": self.rejection_reason,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRequest':
        """딕셔너리에서 생성"""
        return cls(
            request_id=UUID(data["request_id"]) if isinstance(data["request_id"], str) else data["request_id"],
            ticker=data["ticker"],
            action=data["action"],
            quantity=data.get("quantity"),
            target_price=data.get("target_price"),
            ai_reasoning=data["ai_reasoning"],
            consensus_confidence=data["consensus_confidence"],
            priority_score=data["priority_score"],
            debate_rounds=data["debate_rounds"],
            approval_level=ApprovalLevel[data["approval_level"]],
            status=ApprovalStatus(data["status"]),
            requested_at=datetime.fromisoformat(data["requested_at"]),
            decided_at=datetime.fromisoformat(data["decided_at"]) if data.get("decided_at") else None,
            auto_approve_after=datetime.fromisoformat(data["auto_approve_after"]) if data.get("auto_approve_after") else None,
            decided_by=data.get("decided_by"),
            rejection_reason=data.get("rejection_reason"),
            metadata=data.get("metadata", {})
        )
    
    def is_pending(self) -> bool:
        """승인 대기 중인지"""
        return self.status == ApprovalStatus.PENDING
    
    def is_decided(self) -> bool:
        """결정되었는지"""
        return self.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.AUTO_APPROVED]
    
    def can_auto_approve(self) -> bool:
        """자동 승인 가능한지"""
        if self.approval_level != ApprovalLevel.SOFT_APPROVAL:
            return False
        if not self.auto_approve_after:
            return False
        return datetime.now() >= self.auto_approve_after


# 승인 규칙: 제안 유형별 승인 레벨
APPROVAL_RULES = {
    "trade": ApprovalLevel.SOFT_APPROVAL,        # 일반 거래: 24시간 후 자동
    "large_trade": ApprovalLevel.HARD_APPROVAL,  # 대량 거래: 명시적 승인
    "strategy_change": ApprovalLevel.HARD_APPROVAL,  # 전략 변경
    "philosophy_change": ApprovalLevel.PHILOSOPHY,   # 철학 변경
    "constitution_amendment": ApprovalLevel.PHILOSOPHY  # 헌법 개정
}


def determine_approval_level(
    proposal_type: str,
    priority_score: float,
    position_size_pct: Optional[float] = None
) -> ApprovalLevel:
    """
    제안 유형과 우선순위에 따른 승인 레벨 결정
    
    Args:
        proposal_type: 제안 유형
        priority_score: 우선순위 점수
        position_size_pct: 포지션 크기 (% of portfolio)
    
    Returns:
        ApprovalLevel
    """
    # 철학/헌법 변경은 무조건 PHILOSOPHY
    if proposal_type in ["philosophy_change", "constitution_amendment"]:
        return ApprovalLevel.PHILOSOPHY
    
    # 대량 거래 (포트폴리오의 20% 이상)
    if position_size_pct and position_size_pct > 20:
        return ApprovalLevel.HARD_APPROVAL
    
    # 고우선순위 (0.7 이상)
    if priority_score > 0.7:
        return ApprovalLevel.HARD_APPROVAL
    
    # 중간 우선순위 (0.4 ~ 0.7)
    if priority_score > 0.4:
        return ApprovalLevel.SOFT_APPROVAL
    
    # 낮은 우선순위
    return ApprovalLevel.INFO_ONLY
