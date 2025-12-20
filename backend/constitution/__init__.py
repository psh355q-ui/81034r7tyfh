"""
Constitution Package - 시스템 헌법

AI Trading System의 불변 기초 규칙

모든 규칙은 Pure Python으로 작성되며,
외부 라이브러리 의존성이 없습니다.

작성일: 2025-12-15
버전: 1.0.0
"""

from .risk_limits import RiskLimits
from .allocation_rules import AllocationRules
from .trading_constraints import TradingConstraints
from .constitution import Constitution
from .portfolio_phase import PortfolioPhase, BootstrapExitConditions
from .check_integrity import (
    verify_constitution_integrity,
    verify_on_startup,
    SystemFreeze
)

__version__ = "1.0.0"
__all__ = [
    "RiskLimits",
    "AllocationRules",
    "TradingConstraints",
    "Constitution",
    "PortfolioPhase",
    "BootstrapExitConditions",
    "verify_constitution_integrity",
    "verify_on_startup",
    "SystemFreeze"
]

# 시스템 시작 시 자동 검증 (프로덕션 모드)
# 개발 중에는 해시가 없어서 스킵됨
try:
    verify_on_startup()
except SystemFreeze:
    # 검증 실패 시 시스템 중단
    raise
