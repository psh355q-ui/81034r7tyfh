"""
Performance Metrics Module for AI Trading System.

This module provides standard functions to calculate financial performance metrics
such as Sharpe Ratio, Drawdown, Returns, and Win Rate.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Union

def calculate_total_return(initial_capital: float, final_equity: float) -> float:
    """Calculate total percentage return."""
    if initial_capital == 0:
        return 0.0
    return (final_equity - initial_capital) / initial_capital

def calculate_cagr(initial_capital: float, final_equity: float, days: int) -> float:
    """Calculate Compound Annual Growth Rate."""
    if initial_capital == 0 or days <= 0:
        return 0.0
    years = days / 365.25
    return (final_equity / initial_capital) ** (1 / years) - 1

def calculate_drawdown_series(equity_curve: List[float]) -> List[float]:
    """Calculate drawdown series from equity curve."""
    if not equity_curve:
        return []
    
    peak = equity_curve[0]
    drawdowns = []
    
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak if peak > 0 else 0.0
        drawdowns.append(drawdown)
        
    return drawdowns

def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate Maximum Drawdown."""
    drawdowns = calculate_drawdown_series(equity_curve)
    return max(drawdowns) if drawdowns else 0.0

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0, periods: int = 252) -> float:
    """
    Calculate Sharpe Ratio.
    Typically assumes daily returns and annualizes with 252 trading days.
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / periods)
    
    mean_excess_return = np.mean(excess_returns)
    std_dev = np.std(returns_array, ddof=1)
    
    if std_dev == 0:
        return 0.0
        
    return (mean_excess_return / std_dev) * np.sqrt(periods)

def calculate_sortino_ratio(returns: List[float], target_return: float = 0.0, periods: int = 252) -> float:
    """
    Calculate Sortino Ratio (uses downside deviation).
    """
    if not returns or len(returns) < 2:
        return 0.0
        
    returns_array = np.array(returns)
    avg_return = np.mean(returns_array)
    
    # Calculate downside deviation (only negative returns relative to target)
    downside_returns = returns_array[returns_array < target_return]
    
    if len(downside_returns) == 0:
        return 0.0
    
    downside_std = np.std(downside_returns, ddof=1)
    
    if downside_std == 0:
        return 0.0
        
    return ((avg_return - target_return) / downside_std) * np.sqrt(periods)

def calculate_win_rate(trades: List[Dict]) -> float:
    """Calculate Win Rate from list of trade dictionaries."""
    closed_trades = [t for t in trades if t.get('pnl') is not None]
    if not closed_trades:
        return 0.0
        
    winning_trades = [t for t in closed_trades if t['pnl'] > 0]
    return len(winning_trades) / len(closed_trades)

def calculate_profit_factor(trades: List[Dict]) -> float:
    """Calculate Profit Factor (Gross Profit / Gross Loss)."""
    closed_trades = [t for t in trades if t.get('pnl') is not None]
    if not closed_trades:
        return 0.0
        
    gross_profit = sum(t['pnl'] for t in closed_trades if t['pnl'] > 0)
    gross_loss = abs(sum(t['pnl'] for t in closed_trades if t['pnl'] < 0))
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
        
    return gross_profit / gross_loss

def calculate_comprehensive_metrics(
    initial_capital: float,
    equity_curve: List[float],
    trades: List[Dict],
    daily_returns: Optional[List[float]] = None
) -> Dict:
    """
    Calculate comprehensive performance report.
    """
    if not equity_curve:
        return {}
        
    final_equity = equity_curve[-1]
    total_return = calculate_total_return(initial_capital, final_equity)
    max_dd = calculate_max_drawdown(equity_curve)
    
    if daily_returns is None:
        # Calculate daily returns from equity curve if not provided
        daily_returns = [
            (equity_curve[i] - equity_curve[i-1])/equity_curve[i-1] 
            for i in range(1, len(equity_curve))
        ]
        
    sharpe = calculate_sharpe_ratio(daily_returns)
    sortino = calculate_sortino_ratio(daily_returns)
    win_rate = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)
    
    return {
        "total_return": total_return,
        "final_equity": final_equity,
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_trades": len([t for t in trades if t.get('pnl') is not None]),
    }
