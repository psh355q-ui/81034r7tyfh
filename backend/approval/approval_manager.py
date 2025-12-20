"""
Approval Manager - 승인 요청 관리 시스템

ChatGPT Feature 2: Human Approval Workflow

기능:
- 승인 요청 생성 및 저장
- 승인/거부 처리
- 자동 승인 체크
- 대기 중 요청 조회

작성일: 2025-12-16
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from .approval_models import (
    ApprovalRequest,
    ApprovalLevel,
    ApprovalStatus,
    determine_approval_level
)

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    승인 요청 관리 시스템
    
    Usage:
        manager = ApprovalManager()
        
        # 승인 요청 생성
        request = manager.create_request(
            ticker="NVDA",
            action="BUY",
            ai_reasoning="Strong buy signal...",
            priority_score=0.85
        )
        
        # 승인 처리
        manager.approve(request.request_id, approved_by="user@example.com")
        
        # 대기 중 요청 조회
        pending = manager.get_pending_requests()
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 승인 요청 저장 경로
        """
        self.storage_path = storage_path or Path("data/approvals")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 메모리 캐시
        self.pending_requests: Dict[UUID, ApprovalRequest] = {}
        self.decided_requests: Dict[UUID, ApprovalRequest] = {}
        
        # 기존 요청 로드
        self._load_existing_requests()
        
        logger.info(f"ApprovalManager initialized: {len(self.pending_requests)} pending")
    
    def create_request(
        self,
        ticker: str,
        action: str,
        ai_reasoning: str,
        priority_score: float,
        consensus_confidence: float = 0.0,
        debate_rounds: int = 0,
        quantity: Optional[int] = None,
        target_price: Optional[float] = None,
        position_size_pct: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        승인 요청 생성
        
        Args:
            ticker: 종목 티커
            action: 액션 (BUY, SELL, HOLD)
            ai_reasoning: AI 분석 근거
            priority_score: 우선순위 점수
            consensus_confidence: 합의 신뢰도
            debate_rounds: 토론 라운드 수
            quantity: 수량
            target_price: 목표 가격
            position_size_pct: 포지션 크기 (%)
            metadata: 추가 메타데이터
        
        Returns:
            ApprovalRequest
        """
        # 승인 레벨 결정
        approval_level = determine_approval_level(
            "trade",
            priority_score,
            position_size_pct
        )
        
        # 요청 생성
        request = ApprovalRequest(
            ticker=ticker,
            action=action,
            quantity=quantity,
            target_price=target_price,
            ai_reasoning=ai_reasoning,
            consensus_confidence=consensus_confidence,
            priority_score=priority_score,
            debate_rounds=debate_rounds,
            approval_level=approval_level,
            metadata=metadata or {}
        )
        
        # Soft Approval이면 24시간 후 자동 승인 설정
        if approval_level == ApprovalLevel.SOFT_APPROVAL:
            request.auto_approve_after = datetime.now() + timedelta(hours=24)
        
        # 저장
        self.pending_requests[request.request_id] = request
        self._save_request(request)
        
        logger.info(
            f"Approval request created: {request.request_id} "
            f"{ticker} {action} (priority={priority_score:.2f}, level={approval_level.name})"
        )
        
        return request
    
    def approve(
        self,
        request_id: UUID,
        approved_by: str,
        notes: Optional[str] = None
    ) -> ApprovalRequest:
        """
        승인 처리
        
        Args:
            request_id: 요청 ID
            approved_by: 승인자
            notes: 승인 메모
        
        Returns:
            업데이트된 ApprovalRequest
        """
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found or already decided")
        
        request.status = ApprovalStatus.APPROVED
        request.decided_at = datetime.now()
        request.decided_by = approved_by
        
        if notes:
            request.metadata["approval_notes"] = notes
        
        # 캐시 이동
        self.decided_requests[request_id] = request
        del self.pending_requests[request_id]
        
        # 저장
        self._save_request(request)
        
        logger.info(f"Request {request_id} APPROVED by {approved_by}")
        
        return request
    
    def reject(
        self,
        request_id: UUID,
        rejected_by: str,
        reason: str
    ) -> ApprovalRequest:
        """
        거부 처리
        
        Args:
            request_id: 요청 ID
            rejected_by: 거부자
            reason: 거부 사유
        
        Returns:
            업데이트된 ApprovalRequest
        """
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found or already decided")
        
        request.status = ApprovalStatus.REJECTED
        request.decided_at = datetime.now()
        request.decided_by = rejected_by
        request.rejection_reason = reason
        
        # 캐시 이동
        self.decided_requests[request_id] = request
        del self.pending_requests[request_id]
        
        # 저장
        self._save_request(request)
        
        logger.info(f"Request {request_id} REJECTED by {rejected_by}: {reason}")
        
        return request
    
    def check_auto_approvals(self) -> List[ApprovalRequest]:
        """
        자동 승인 가능한 요청 체크 및 처리
        
        Returns:
            자동 승인된 요청 리스트
        """
        auto_approved = []
        
        for request_id, request in list(self.pending_requests.items()):
            if request.can_auto_approve():
                request.status = ApprovalStatus.AUTO_APPROVED
                request.decided_at = datetime.now()
                request.decided_by = "system"
                
                # 캐시 이동
                self.decided_requests[request_id] = request
                del self.pending_requests[request_id]
                
                # 저장
                self._save_request(request)
                
                auto_approved.append(request)
                logger.info(f"Request {request_id} AUTO-APPROVED (24h elapsed)")
        
        return auto_approved
    
    def get_pending_requests(self, ticker: Optional[str] = None) -> List[ApprovalRequest]:
        """
        대기 중 요청 조회
        
        Args:
            ticker: 티커 필터 (선택)
        
        Returns:
            대기 중 요청 리스트
        """
        requests = list(self.pending_requests.values())
        
        if ticker:
            requests = [r for r in requests if r.ticker == ticker]
        
        # 우선순위 순 정렬
        requests.sort(key=lambda r: r.priority_score, reverse=True)
        
        return requests
    
    def get_request(self, request_id: UUID) -> Optional[ApprovalRequest]:
        """요청 조회"""
        return (
            self.pending_requests.get(request_id) or
            self.decided_requests.get(request_id)
        )
    
    def _save_request(self, request: ApprovalRequest):
        """요청 저장"""
        if not self.storage_path:
            return
        
        filename = f"{request.requested_at.strftime('%Y%m%d')}_{request.request_id}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(request.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_existing_requests(self):
        """기존 요청 로드"""
        if not self.storage_path.exists():
            return
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                request = ApprovalRequest.from_dict(data)
                
                if request.is_decided():
                    self.decided_requests[request.request_id] = request
                else:
                    self.pending_requests[request.request_id] = request
            
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")
        
        logger.info(
            f"Loaded {len(self.pending_requests)} pending, "
            f"{len(self.decided_requests)} decided requests"
        )


# Singleton instance
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """승인 매니저 싱글톤 인스턴스"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
