"""
AI Collective Intelligence Module

Phase F1: AI 집단지성 고도화

AI 에이전트 간 협업과 집단 의사결정을 위한 모듈

Components:
- ai_role_manager: AI 역할 계층화 관리
- collective_decision_engine: 집단 의사결정 엔진 (예정)
"""

from backend.ai.collective.ai_role_manager import (
    AIRole,
    AIAgentType,
    RoleConfig,
    AgentAssignment,
    AIRoleManager,
    get_role_manager
)

__all__ = [
    # Enums
    "AIRole",
    "AIAgentType",
    
    # Data Classes
    "RoleConfig",
    "AgentAssignment",
    
    # Classes
    "AIRoleManager",
    
    # Functions
    "get_role_manager"
]
