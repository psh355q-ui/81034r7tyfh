"""
Phase 6: Smart Execution Engine

Complete execution system for AI Trading Agent.
Converts trading decisions into optimal order execution.

Components:
- SmartExecutionEngine: Main execution engine with algorithm selection
- SmartExecutor: Complete workflow orchestrator
- SimplePortfolioManager: Position tracking
- SimpleRiskManager: Risk controls

Cost: $0/month (all local computation)
Author: AI Trading System Team
Date: 2025-11-14
"""

# Phase 6: Smart Execution (NEW)
from .execution_engine import (
    SmartExecutionEngine,
    ExecutionRequest,
    ExecutionResult,
)

from .smart_executor import (
    SmartExecutor,
    SimplePortfolioManager,
    SimpleRiskManager,
)

# Legacy executors (keep for backward compatibility)
from .executors import (
    execute_twap,
    execute_vwap,
    OrderExecutor,
    TWAPExecutor,
    VWAPExecutor,
)

__all__ = [
    # Phase 6: Smart Execution
    "SmartExecutionEngine",
    "ExecutionRequest",
    "ExecutionResult",
    "SmartExecutor",
    "SimplePortfolioManager",
    "SimpleRiskManager",
    # Legacy
    "execute_twap",
    "execute_vwap",
    "OrderExecutor",
    "TWAPExecutor",
    "VWAPExecutor",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
__phase__ = 6

# MVP Execution Layer (NEW - 2025-12-31)
try:
    from .execution_router import ExecutionRouter, ExecutionMode
    from .order_validator import OrderValidator, ValidationResult
    
    # Add to __all__
    __all__.extend([
        "ExecutionRouter",
        "ExecutionMode",
        "OrderValidator",
        "ValidationResult",
    ])
except ImportError:
    pass
