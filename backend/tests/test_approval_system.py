"""
Approval System - Unit Tests

Tests for approval_models and approval_manager

작성일: 2025-12-16
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from backend.approval.approval_models import (
    ApprovalRequest,
    ApprovalLevel,
    ApprovalStatus,
    determine_approval_level
)
from backend.approval.approval_manager import ApprovalManager


def test_approval_level_determination():
    """승인 레벨 결정 테스트"""
    # 고우선순위 → Hard Approval
    level = determine_approval_level("trade", priority_score=0.85)
    assert level == ApprovalLevel.HARD_APPROVAL
    
    # 중간 우선순위 → Soft Approval
    level = determine_approval_level("trade", priority_score=0.5)
    assert level == ApprovalLevel.SOFT_APPROVAL
    
    # 낮은 우선순위 → Info Only
    level = determine_approval_level("trade", priority_score=0.3)
    assert level == ApprovalLevel.INFO_ONLY
    
    # 대량 거래 → Hard Approval
    level = determine_approval_level("trade", priority_score=0.5, position_size_pct=25)
    assert level == ApprovalLevel.HARD_APPROVAL
    
    # 철학 변경 → Philosophy
    level = determine_approval_level("philosophy_change", priority_score=0.5)
    assert level == ApprovalLevel.PHILOSOPHY


def test_approval_request_creation():
    """승인 요청 생성 테스트"""
    request = ApprovalRequest(
        ticker="NVDA",
        action="BUY",
        ai_reasoning="Strong buy signal",
        priority_score=0.85
    )
    
    assert request.ticker == "NVDA"
    assert request.action == "BUY"
    assert request.is_pending()
    assert not request.is_decided()


def test_approval_manager_create_request():
    """ApprovalManager 요청 생성 테스트"""
    manager = ApprovalManager(storage_path=None)  # In-memory only
    
    request = manager.create_request(
        ticker="AAPL",
        action="BUY",
        ai_reasoning="Apple ecosystem growth",
        priority_score=0.9,
        consensus_confidence=0.85
    )
    
    assert request.ticker == "AAPL"
    assert request.approval_level == ApprovalLevel.HARD_APPROVAL
    assert len(manager.pending_requests) == 1


def test_approval_manager_approve():
    """ApprovalManager 승인 처리 테스트"""
    manager = ApprovalManager(storage_path=None)
    
    request = manager.create_request(
        ticker="GOOGL",
        action="BUY",
        ai_reasoning="AI leadership",
        priority_score=0.75
    )
    
    # 승인 처리
    approved = manager.approve(request.request_id, approved_by="user@example.com")
    
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.decided_by == "user@example.com"
    assert len(manager.pending_requests) == 0
    assert len(manager.decided_requests) == 1


def test_approval_manager_reject():
    """ApprovalManager 거부 처리 테스트"""
    manager = ApprovalManager(storage_path=None)
    
    request = manager.create_request(
        ticker="TSLA",
        action="BUY",
        ai_reasoning="EV market leader",
        priority_score=0.6
    )
    
    # 거부 처리
    rejected = manager.reject(
        request.request_id,
        rejected_by="user@example.com",
        reason="Too volatile"
    )
    
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.rejection_reason == "Too volatile"


def test_soft_approval_auto_approve():
    """Soft Approval 자동 승인 테스트"""
    manager = ApprovalManager(storage_path=None)
    
    request = manager.create_request(
        ticker="MSFT",
        action="BUY",
        ai_reasoning="Cloud growth",
        priority_score=0.5  # Soft Approval
    )
    
    assert request.approval_level == ApprovalLevel.SOFT_APPROVAL
    assert request.auto_approve_after is not None
    
    # 강제로 24시간 경과 시뮬레이션
    request.auto_approve_after = datetime.now() - timedelta(hours=1)
    
    # 자동 승인 체크
    auto_approved = manager.check_auto_approvals()
    
    assert len(auto_approved) == 1
    assert auto_approved[0].status == ApprovalStatus.AUTO_APPROVED


def test_get_pending_requests():
    """대기 중 요청 조회 테스트"""
    manager = ApprovalManager(storage_path=None)
    
    # 여러 요청 생성
    manager.create_request("NVDA", "BUY", "AI chips", 0.9)
    manager.create_request("AMD", "BUY", "AMD growth", 0.7)
    manager.create_request("INTC", "SELL", "Losing market share", 0.5)
    
    # 전체 조회
    pending = manager.get_pending_requests()
    assert len(pending) == 3
    
    # 우선순위 순 정렬 확인
    assert pending[0].priority_score == 0.9
    assert pending[1].priority_score == 0.7
    
    # 티커 필터
    nvda_requests = manager.get_pending_requests(ticker="NVDA")
    assert len(nvda_requests) == 1
    assert nvda_requests[0].ticker == "NVDA"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
