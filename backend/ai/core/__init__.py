"""
AI Core Module - 핵심 AI 기능

Phase F1: AI 집단지성 고도화

AI 시스템의 핵심 프로토콜과 기반 기능

Components:
- decision_protocol: AI 응답 품질 검증
"""

from backend.ai.core.decision_protocol import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    AIDecisionSchema,
    DecisionProtocol,
    get_decision_protocol,
    validate_decision
)

__all__ = [
    # Enums
    "ValidationSeverity",
    
    # Data Classes
    "ValidationIssue",
    "ValidationResult",
    "AIDecisionSchema",
    
    # Classes
    "DecisionProtocol",
    
    # Functions
    "get_decision_protocol",
    "validate_decision"
]
