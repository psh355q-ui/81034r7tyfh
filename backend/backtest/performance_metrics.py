"""
Performance Metrics - 백테스트 성과 지표

Sharpe Ratio, Max Drawdown, Win Rate 등 계산

작성일: 2025-12-15
"""

import numpy as np
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """성과 지표"""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    profit_factor: float


def calculate_returns(portfolio_values: List[float]) -> List[float]:
    """
    일별 수익률 계산
    
    Args:
        portfolio_values: 포트폴리오 가치 리스트
        
    Returns:
        일별 수익률 리스트
    """
    if len(portfolio_values) < 2:
        return []
    
    returns = []
    for i in range(1, len(portfolio_values)):
        daily_return = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
        returns.append(daily_return)
    
    return returns


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.04
) -> float:
    """
    Sharpe Ratio 계산
    
    Args:
        returns: 일별 수익률
        risk_free_rate: 무위험 이자율 (연 4%)
        
    Returns:
        Sharpe Ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # 일별 무위험 수익률
    daily_rf = risk_free_rate / 252
    
    # 초과 수익률
    excess_returns = [r - daily_rf for r in returns]
    
    avg_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)
    
    if std_excess == 0:
        return 0.0
    
    # 연환산
    sharpe = (avg_excess / std_excess) * np.sqrt(252)
    
    return sharpe


def calculate_max_drawdown(portfolio_values: List[float]) -> float:
    """
    Max Drawdown 계산
    
    Args:
        portfolio_values: 포트폴리오 가치 리스트
        
    Returns:
        Max Drawdown (음수)
    """
    if len(portfolio_values) == 0:
        return 0.0
    
    peak = portfolio_values[0]
    max_dd = 0.0
    
    for value in portfolio_values:
        if value > peak:
            peak = value
        
        dd = (value - peak) / peak
        if dd < max_dd:
            max_dd = dd
    
    return max_dd


def calculate_volatility(returns: List[float]) -> float:
    """
    변동성 계산 (연환산)
    
    Args:
        returns: 일별 수익률
        
    Returns:
        연환산 변동성
    """
    if len(returns) == 0:
        return 0.0
    
    std_daily = np.std(returns, ddof=1)
    
    # 연환산
    annual_vol = std_daily * np.sqrt(252)
    
    return annual_vol


def calculate_win_rate(trades: List[Dict]) -> tuple[float, int, int]:
    """
    승률 계산
    
    Args:
        trades: 거래 리스트
        
    Returns:
        (승률, 승리 횟수, 패배 횟수)
    """
    if len(trades) == 0:
        return 0.0, 0, 0
    
    # 매수-매도 쌍 찾기
    buy_trades = {}
    wins = 0
    losses = 0
    
    for trade in trades:
        ticker = trade.ticker
        action = trade.action
        
        if action.name == "BUY":
            if ticker not in buy_trades:
                buy_trades[ticker] = []
            buy_trades[ticker].append(trade.price)
        
        elif action.name == "SELL" and ticker in buy_trades and len(buy_trades[ticker]) > 0:
            buy_price = buy_trades[ticker].pop(0)
            
            if trade.price > buy_price:
                wins += 1
            else:
                losses += 1
    
    total = wins + losses
    if total == 0:
        return 0.0, 0, 0
    
    win_rate = wins / total
    
    return win_rate, wins, losses


def calculate_profit_factor(trades: List[Dict]) -> float:
    """
    Profit Factor 계산
    
    Args:
        trades: 거래 리스트
        
    Returns:
        Profit Factor (총 이익 / 총 손실)
    """
    if len(trades) == 0:
        return 0.0
    
    total_profit = 0.0
    total_loss = 0.0
    
    buy_trades = {}
    
    for trade in trades:
        ticker = trade.ticker
        action = trade.action
        
        if action.name == "BUY":
            if ticker not in buy_trades:
                buy_trades[ticker] = []
            buy_trades[ticker].append(trade.price)
        
        elif action.name == "SELL" and ticker in buy_trades and len(buy_trades[ticker]) > 0:
            buy_price = buy_trades[ticker].pop(0)
            pnl = trade.price - buy_price
            
            if pnl > 0:
                total_profit += pnl
            else:
                total_loss += abs(pnl)
    
    if total_loss == 0:
        return float('inf') if total_profit > 0 else 0.0
    
    return total_profit / total_loss


def calculate_all_metrics(
    initial_capital: float,
    final_value: float,
    portfolio_values: List[float],
    trades: List[Dict],
    days: int
) -> PerformanceMetrics:
    """
    모든 성과 지표 계산
    
    Args:
        initial_capital: 초기 자본
        final_value: 최종 가치
        portfolio_values: 포트폴리오 가치 리스트
        trades: 거래 리스트
        days: 거래일 수
        
    Returns:
        PerformanceMetrics
    """
    # 총 수익률
    total_return = (final_value - initial_capital) / initial_capital
    
    # 연환산 수익률
    if days > 0:
        annualized_return = (1 + total_return) ** (252 / days) - 1
    else:
        annualized_return = 0.0
    
    # 일별 수익률
    returns = calculate_returns(portfolio_values)
    
    # 지표 계산
    sharpe = calculate_sharpe_ratio(returns)
    max_dd = calculate_max_drawdown(portfolio_values)
    vol = calculate_volatility(returns)
    win_rate, wins, losses = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)
    
    # 평균 승/패
    winning_returns = [r for r in returns if r > 0]
    losing_returns = [r for r in returns if r < 0]
    
    avg_win = np.mean(winning_returns) if winning_returns else 0.0
    avg_loss = np.mean(losing_returns) if losing_returns else 0.0
    
    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        volatility=vol,
        win_rate=win_rate,
        total_trades=wins + losses,
        winning_trades=wins,
        losing_trades=losses,
        average_win=avg_win,
        average_loss=avg_loss,
        profit_factor=profit_factor
    )


if __name__ == "__main__":
    # 테스트
    print("=== Performance Metrics Test ===\n")
    
    # 샘플 데이터
    portfolio_values = [
        10_000_000,
        10_100_000,
        10_050_000,
        10_200_000,
        10_150_000,
        10_300_000
    ]
    
    # 수익률
    returns = calculate_returns(portfolio_values)
    print(f"Returns: {[f'{r:.2%}' for r in returns]}")
    
    # Sharpe Ratio
    sharpe = calculate_sharpe_ratio(returns)
    print(f"Sharpe Ratio: {sharpe:.2f}")
    
    # Max Drawdown
    max_dd = calculate_max_drawdown(portfolio_values)
    print(f"Max Drawdown: {max_dd:.2%}")
    
    # 변동성
    vol = calculate_volatility(returns)
    print(f"Volatility: {vol:.2%}")
    
    print("\n✅ Performance Metrics test completed!")
