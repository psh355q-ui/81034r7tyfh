"""
Approval Package - 인간 승인 워크플로우 시스템

ChatGPT Feature 2: Human Approval Workflow

Approval system module for ChatGPT Feature 2.
"""
from backend.approval.approval_models import (
    ApprovalRequest,
    ApprovalLevel,
    ApprovalStatus,
    determine_approval_level
)
from backend.approval.approval_manager import ApprovalManager


# Global instance
_approval_manager_instance = None


def get_approval_manager(storage_path: str = "data/approvals") -> ApprovalManager:
    """
    Get or create ApprovalManager instance.
    
    Args:
        storage_path: Path to store approval data
    
    Returns:
        ApprovalManager instance
    """
    global _approval_manager_instance
    
    if _approval_manager_instance is None:
        _approval_manager_instance = ApprovalManager(storage_path=storage_path)
    
    return _approval_manager_instance


__all__ = [
    "ApprovalRequest",
    "ApprovalLevel", 
    "ApprovalStatus",
    "determine_approval_level",
    "ApprovalManager"
]
