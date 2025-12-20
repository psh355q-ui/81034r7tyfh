"""
Shield Metrics - 방패 성과 지표

"방어 가치"를 측정하는 핵심 지표

작성일: 2025-12-15
철학: "수익률"이 아닌 "자본 보존율"을 측정
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ShieldMetrics:
    """
    Shield Metrics (방패 지표)
    
    시스템의 방어 성과를 측정하는 핵심 지표
    """
    
    # 기본 정보
    period_days: int
    """측정 기간 (일)"""
    
    start_date: datetime
    """시작일"""
    
    end_date: datetime
    """종료일"""
    
    # 자본 보존
    capital_preserved_rate: float
    """자본 보존율 (%)"""
    
    initial_capital: float
    """초기 자본"""
    
    final_capital: float
    """최종 자본"""
    
    # 방어 성과
    total_avoided_loss: float
    """총 방어한 손실 ($)"""
    
    defensive_wins: int
    """방어 성공 건수"""
    
    total_rejected_proposals: int
    """총 거부한 제안 수"""
    
    defensive_win_rate: float
    """방어 성공률 (%)"""
    
    # 리스크 비교
    market_volatility: float
    """시장 변동성 (연환산 %)"""
    
    portfolio_volatility: float
    """포트폴리오 변동성 (연환산 %)"""
    
    volatility_reduction: float
    """변동성 감소율 (%)"""
    
    # Drawdown
    max_drawdown: float
    """최대 낙폭 (%)"""
    
    market_max_drawdown: float
    """시장 최대 낙폭 (%)"""
    
    drawdown_protection: float
    """낙폭 보호율 (%)"""
    
    def get_stress_index_diff(self) -> float:
        """
        스트레스 지수 차이
        
        시장 vs 내 계좌의 변동성 차이
        
        Returns:
            양수 = 시장보다 안정적
        """
        return self.market_volatility - self.portfolio_volatility
    
    def get_capital_preservation_grade(self) -> str:
        """
        자본 보존 등급
        
        Returns:
            S/A/B/C/D 등급
        """
        if self.capital_preserved_rate >= 99.0:
            return "S"  # Exceptional
        elif self.capital_preserved_rate >= 97.0:
            return "A"  # Excellent
        elif self.capital_preserved_rate >= 95.0:
            return "B"  # Good
        elif self.capital_preserved_rate >= 90.0:
            return "C"  # Fair
        else:
            return "D"  # Poor
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'period_days': self.period_days,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'capital_preserved_rate': self.capital_preserved_rate,
            'capital_preservation_grade': self.get_capital_preservation_grade(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_avoided_loss': self.total_avoided_loss,
            'defensive_wins': self.defensive_wins,
            'total_rejected_proposals': self.total_rejected_proposals,
            'defensive_win_rate': self.defensive_win_rate,
            'market_volatility': self.market_volatility,
            'portfolio_volatility': self.portfolio_volatility,
            'volatility_reduction': self.volatility_reduction,
            'stress_index_diff': self.get_stress_index_diff(),
            'max_drawdown': self.max_drawdown,
            'market_max_drawdown': self.market_max_drawdown,
            'drawdown_protection': self.drawdown_protection
        }


class ShieldMetricsCalculator:
    """
    Shield Metrics 계산기
    
    포트폴리오 데이터와 Shadow Trades로부터
    방어 성과 지표를 계산합니다.
    """
    
    def __init__(self):
        pass
    
    def calculate_capital_preserved_rate(
        self,
        initial_capital: float,
        final_capital: float
    ) -> float:
        """
        자본 보존율 계산
        
        Args:
            initial_capital: 초기 자본
            final_capital: 최종 자본
            
        Returns:
            보존율 (%)
        """
        if initial_capital == 0:
            return 0.0
        
        preserved_rate = (final_capital / initial_capital) * 100
        return preserved_rate
    
    def calculate_volatility_reduction(
        self,
        market_vol: float,
        portfolio_vol: float
    ) -> float:
        """
        변동성 감소율 계산
        
        Args:
            market_vol: 시장 변동성
            portfolio_vol: 포트폴리오 변동성
            
        Returns:
            감소율 (%)
        """
        if market_vol == 0:
            return 0.0
        
        reduction = ((market_vol - portfolio_vol) / market_vol) * 100
        return reduction
    
    def calculate_drawdown_protection(
        self,
        market_dd: float,
        portfolio_dd: float
    ) -> float:
        """
        낙폭 보호율 계산
        
        Args:
            market_dd: 시장 최대 낙폭 (음수)
            portfolio_dd: 포트폴리오 최대 낙폭 (음수)
            
        Returns:
            보호율 (%)
        """
        if market_dd == 0:
            return 0.0
        
        protection = ((abs(market_dd) - abs(portfolio_dd)) / abs(market_dd)) * 100
        return protection
    
    def calculate_metrics(
        self,
        period_days: int,
        initial_capital: float,
        final_capital: float,
        shadow_trade_report: Dict[str, Any],
        market_data: Optional[Dict[str, float]] = None
    ) -> ShieldMetrics:
        """
        Shield Metrics 계산
        
        Args:
            period_days: 측정 기간
            initial_capital: 초기 자본
            final_capital: 최종 자본
            shadow_trade_report: Shadow Trade 리포트
            market_data: 시장 데이터 (선택)
                {
                    'volatility': 시장 변동성,
                    'max_drawdown': 시장 최대 낙폭
                }
        
        Returns:
            ShieldMetrics
        """
        # 기본값
        if market_data is None:
            market_data = {
                'volatility': 0.20,  # 20%
                'max_drawdown': -0.10  # -10%
            }
        
        # 자본 보존율
        capital_preserved_rate = self.calculate_capital_preserved_rate(
            initial_capital,
            final_capital
        )
        
        # 포트폴리오 변동성 (간단히 자본 변화로 추정)
        pnl_pct = ((final_capital - initial_capital) / initial_capital) if initial_capital > 0 else 0
        portfolio_vol = abs(pnl_pct) * 3  # 간단한 추정 (실제로는 일별 변동성 계산 필요)
        
        # 변동성 감소
        volatility_reduction = self.calculate_volatility_reduction(
            market_data.get('volatility', 0.20),
            portfolio_vol
        )
        
        # Drawdown
        max_dd = pnl_pct if pnl_pct < 0 else 0
        drawdown_protection = self.calculate_drawdown_protection(
            market_data.get('max_drawdown', -0.10),
            max_dd
        )
        
        # 날짜
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        return ShieldMetrics(
            period_days=period_days,
            start_date=start_date,
            end_date=end_date,
            capital_preserved_rate=capital_preserved_rate,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_avoided_loss=shadow_trade_report.get('total_avoided_loss', 0),
            defensive_wins=shadow_trade_report.get('defensive_wins', 0),
            total_rejected_proposals=shadow_trade_report.get('total_rejected_proposals', 0),
            defensive_win_rate=shadow_trade_report.get('defensive_win_rate', 0),
            market_volatility=market_data.get('volatility', 0.20),
            portfolio_volatility=portfolio_vol,
            volatility_reduction=volatility_reduction,
            max_drawdown=max_dd,
            market_max_drawdown=market_data.get('max_drawdown', -0.10),
            drawdown_protection=drawdown_protection
        )


if __name__ == "__main__":
    # 테스트
    print("=== Shield Metrics Test ===\n")
    
    calculator = ShieldMetricsCalculator()
    
    # 샘플 데이터
    shadow_report = {
        'total_avoided_loss': 1200.0,
        'defensive_wins': 5,
        'total_rejected_proposals': 8,
        'defensive_win_rate': 0.625
    }
    
    market_data = {
        'volatility': 0.25,  # 25%
        'max_drawdown': -0.12  # -12%
    }
    
    # 계산
    metrics = calculator.calculate_metrics(
        period_days=7,
        initial_capital=10000000,
        final_capital=9985000,
        shadow_trade_report=shadow_report,
        market_data=market_data
    )
    
    print("Shield Metrics:")
    print(f"  자본 보존율: {metrics.capital_preserved_rate:.2f}% (등급: {metrics.get_capital_preservation_grade()})")
    print(f"  방어한 손실: ${metrics.total_avoided_loss:,.0f}")
    print(f"  방어 성공: {metrics.defensive_wins}건 / {metrics.total_rejected_proposals}건")
    print(f"  방어 성공률: {metrics.defensive_win_rate:.1%}")
    print(f"\n변동성:")
    print(f"  시장: {metrics.market_volatility:.1%}")
    print(f"  내 계좌: {metrics.portfolio_volatility:.1%}")
    print(f"  스트레스 감소: {metrics.get_stress_index_diff():.1%}p")
    print(f"\nDrawdown:")
    print(f"  시장: {metrics.market_max_drawdown:.1%}")
    print(f"  내 계좌: {metrics.max_drawdown:.1%}")
    print(f"  보호율: {metrics.drawdown_protection:.1%}")
    
    print("\n✅ Shield Metrics 계산 완료!")
