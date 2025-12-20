"""
Backtesting Module

Historical trading simulation and strategy testing.

Components:
- BacktestSimulator: Core simulation engine
- AIStrategyBacktest: AI strategy integration
- Performance analysis tools

Author: AI Trading System Team
Date: 2025-11-14
"""

from .backtest_simulator import (
    BacktestSimulator,
    BacktestConfig,
    BacktestResult,
    Trade,
    PortfolioSnapshot,
)

from .ai_strategy_backtest import (
    AIStrategyBacktest,
    AIStrategyConfig,
    run_full_backtest,
)

__all__ = [
    "BacktestSimulator",
    "BacktestConfig",
    "BacktestResult",
    "Trade",
    "PortfolioSnapshot",
    "AIStrategyBacktest",
    "AIStrategyConfig",
    "run_full_backtest",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
