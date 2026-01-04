"""
Shadow Trading Analytics - 고급 통계 분석 도구

Date: 2026-01-03
Phase: Performance & Analytics (P5)
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ShadowTradingAnalyzer:
    """Shadow Trading 성과에 대한 고급 통계 분석을 수행합니다."""

    def __init__(self, trades: List[Dict]):
        """
        Args:
            trades: 거래 기록 리스트 (딕셔너리 형태)
                   필수 키: 'pnl', 'pnl_pct', 'entry_date', 'exit_date' (optional)
        """
        self.trades = trades
        self.df = pd.DataFrame(trades)
        self._preprocess()

    def _preprocess(self):
        """데이터 전처리"""
        if self.df.empty:
            return
            
        # 필수 컬럼 확인 및 기본값 설정
        if 'pnl' not in self.df.columns:
            self.df['pnl'] = 0.0
        if 'pnl_pct' not in self.df.columns:
            self.df['pnl_pct'] = 0.0
            
        # 날짜 변환
        if 'entry_date' in self.df.columns:
            self.df['entry_date'] = pd.to_datetime(self.df['entry_date'])

    def generate_report(self) -> Dict:
        """종합 분석 리포트 생성"""
        if self.df.empty:
            return {"error": "No trades to analyze"}

        return {
            'basic_metrics': self.calculate_basic_metrics(),
            'risk_metrics': self.calculate_risk_metrics(),
            'streak_analysis': self.analyze_streaks(),
            'statistical_test': self.perform_significance_test()
        }

    def calculate_basic_metrics(self) -> Dict:
        """기본 성과 지표"""
        total_trades = len(self.df)
        winning_trades = self.df[self.df['pnl'] > 0]
        losing_trades = self.df[self.df['pnl'] <= 0]
        
        return {
            'total_trades': total_trades,
            'win_count': len(winning_trades),
            'loss_count': len(losing_trades),
            'win_rate': len(winning_trades) / total_trades if total_trades > 0 else 0,
            'total_pnl': float(self.df['pnl'].sum()),
            'avg_pnl': float(self.df['pnl'].mean()),
            'avg_win': float(winning_trades['pnl'].mean()) if not winning_trades.empty else 0,
            'avg_loss': float(losing_trades['pnl'].mean()) if not losing_trades.empty else 0,
            'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if losing_trades['pnl'].sum() != 0 else float('inf')
        }

    def calculate_risk_metrics(self, risk_free_rate: float = 0.02) -> Dict:
        """리스크 조정 지표 (Sharpe, Sortino, MDD)"""
        if len(self.df) < 2:
            return {}

        returns = self.df['pnl_pct'].values
        # 일별 변동성 추정을 위해 거래 간격을 고려해아 하나, 여기선 단순화하여 거래 단위로 계산 후 연율화 가정
        # 실제로는 일별 수익률 시계열로 변환 필요. (여기선 간이 계산)
        
        excess_returns = returns - (risk_free_rate / 252)
        std_dev = np.std(excess_returns, ddof=1)
        
        sharpe = 0.0
        if std_dev > 0:
            sharpe = (np.mean(excess_returns) / std_dev) * np.sqrt(252)

        # Sortino Ratio (Downside Deviation)
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = np.std(downside_returns, ddof=1) if len(downside_returns) > 0 else 0
        sortino = 0.0
        if downside_std > 0:
            sortino = (np.mean(excess_returns) / downside_std) * np.sqrt(252)

        return {
            'sharpe_ratio': 0.0 if np.isnan(sharpe) else float(sharpe),
            'sortino_ratio': 0.0 if np.isnan(sortino) else float(sortino),
            'max_drawdown': self._calculate_max_drawdown()
        }

    def _calculate_max_drawdown(self) -> float:
        """최대 낙폭(MDD) 계산"""
        if self.df.empty:
            return 0.0
            
        # 누적 수익 곡선 생성 (초기 자본 1.0 가정)
        cumulative_returns = (1 + self.df['pnl_pct']).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        return float(drawdown.min())

    def analyze_streaks(self) -> Dict:
        """연승/연패 분석"""
        metrics = {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0}
        
        if self.df.empty:
            return metrics

        wins = (self.df['pnl'] > 0).values.astype(int)
        
        current_streak = 0
        max_win = 0
        max_loss = 0
        
        for is_win in wins:
            if is_win:
                current_streak = current_streak + 1 if current_streak > 0 else 1
                max_win = max(max_win, current_streak)
            else:
                current_streak = current_streak - 1 if current_streak < 0 else -1
                max_loss = max(max_loss, abs(current_streak)) # loss streak는 음수로 계산되므로 절대값

        metrics['max_win_streak'] = max_win
        metrics['max_loss_streak'] = max_loss
        metrics['current_streak'] = current_streak
        return metrics

    def perform_significance_test(self) -> Dict:
        """통계적 유의성 검정 (Win Rate vs 50%)"""
        total = len(self.df)
        wins = len(self.df[self.df['pnl'] > 0])
        
        if total == 0:
            return {'significant': False, 'p_value': 1.0}

        # 이항 검정 (Binomial Test)
        # 귀무가설: 승률 = 0.5, 대립가설: 승률 > 0.5
        p_value = stats.binomtest(wins, total, p=0.5, alternative='greater').pvalue
        
        return {
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'confidence_level': (1 - p_value) * 100
        }

# 사용 예시
if __name__ == "__main__":
    # Mock Data Test
    mock_trades = [
        {'pnl': 100, 'pnl_pct': 0.01},
        {'pnl': -50, 'pnl_pct': -0.005},
        {'pnl': 120, 'pnl_pct': 0.012},
        {'pnl': 80, 'pnl_pct': 0.008},
    ]
    analyzer = ShadowTradingAnalyzer(mock_trades)
    print(analyzer.generate_report())
