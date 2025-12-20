"""
Shield Report Generator - 방패 보고서 생성기

"방어 성과"를 강조하는 리포트 생성

작성일: 2025-12-15
철학: 수익률보다 안전을 강조
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.reporting.shield_metrics import ShieldMetrics, ShieldMetricsCalculator
from backend.backtest.shadow_trade_tracker import ShadowTradeTracker

logger = logging.getLogger(__name__)


class ShieldReportGenerator:
    """
    Shield Report Generator
    
    "방패 보고서"를 생성합니다.
    기존 수익률 중심 리포트와 달리,
    "자본 보존", "방어 성공", "스트레스 감소"를 강조합니다.
    """
    
    def __init__(
        self,
        shadow_tracker: ShadowTradeTracker,
        metrics_calculator: Optional[ShieldMetricsCalculator] = None
    ):
        """
        초기화
        
        Args:
            shadow_tracker: Shadow Trade Tracker
            metrics_calculator: Metrics Calculator (None이면 생성)
        """
        self.shadow_tracker = shadow_tracker
        self.calculator = metrics_calculator or ShieldMetricsCalculator()
    
    def generate_shield_report(
        self,
        period_days: int,
        initial_capital: float,
        final_capital: float,
        market_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Shield Report 생성
        
        Args:
            period_days: 측정 기간 (일)
            initial_capital: 초기 자본
            final_capital: 최종 자본
            market_data: 시장 데이터 (선택)
        
        Returns:
            Shield Report 딕셔너리
        """
        # Shadow Trade 리포트
        shadow_report = self.shadow_tracker.generate_shield_report(period_days)
        
        # Metrics 계산
        metrics = self.calculator.calculate_metrics(
            period_days=period_days,
            initial_capital=initial_capital,
            final_capital=final_capital,
            shadow_trade_report=shadow_report,
            market_data=market_data
        )
        
        # 리포트 조립
        report = {
            'metadata': {
                'title': 'Shield Report (방패 보고서)',
                'subtitle': '자산을 지키는 AI 위원회의 성과',
                'period': f'{period_days}일',
                'generated_at': datetime.utcnow().isoformat()
            },
            
            'headline': self._generate_headline(metrics),
            
            'sections': {
                'capital_preservation': self._section_capital_preservation(metrics),
                'the_graveyard': self._section_graveyard(shadow_report),
                'stress_test': self._section_stress_test(metrics),
                'drawdown_protection': self._section_drawdown(metrics)
            },
            
            'raw_metrics': metrics.to_dict(),
            'raw_shadow_report': shadow_report
        }
        
        return report
    
    def _generate_headline(self, metrics: ShieldMetrics) -> Dict[str, Any]:
        """
        헤드라인 KPI 생성
        
        Args:
            metrics: Shield Metrics
        
        Returns:
            헤드라인 딕셔너리
        """
        return {
            'primary_kpi': {
                'label': '자본 보존율',
                'value': f"{metrics.capital_preserved_rate:.1f}%",
                'grade': metrics.get_capital_preservation_grade(),
                'icon': '🛡️'
            },
            'secondary_kpis': [
                {
                    'label': '방어한 손실',
                    'value': f"${metrics.total_avoided_loss:,.0f}",
                    'icon': '💰'
                },
                {
                    'label': '방어 성공',
                    'value': f"{metrics.defensive_wins}건",
                    'icon': '✅'
                },
                {
                    'label': '스트레스 감소',
                    'value': f"{metrics.get_stress_index_diff():+.1f}%p",
                    'icon': '📉'
                }
            ]
        }
    
    def _section_capital_preservation(self, metrics: ShieldMetrics) -> Dict[str, Any]:
        """
        자본 보존 섹션
        
        Args:
            metrics: Shield Metrics
        
        Returns:
            섹션 딕셔너리
        """
        return {
            'title': '💎 자본 보존',
            'data': {
                'initial_capital': metrics.initial_capital,
                'final_capital': metrics.final_capital,
                'preservation_rate': metrics.capital_preserved_rate,
                'grade': metrics.get_capital_preservation_grade()
            },
            'message': self._get_preservation_message(metrics)
        }
    
    def _section_graveyard(self, shadow_report: Dict) -> Dict[str, Any]:
        """
        The Graveyard (기각된 위험들) 섹션
        
        Args:
            shadow_report: Shadow Trade Report
        
        Returns:
            섹션 딕셔너리
        """
        highlights = shadow_report.get('highlights', [])
        
        return {
            'title': '🪦 The Graveyard (기각된 위험들)',
            'summary': {
                'total_rejected': shadow_report.get('total_rejected_proposals', 0),
                'defensive_wins': shadow_report.get('defensive_wins', 0),
                'defensive_win_rate': shadow_report.get('defensive_win_rate', 0)
            },
            'highlights': [
                {
                    'ticker': h['ticker'],
                    'action': h['action'],
                    'reason': h['rejection_reason'],
                    'result': f"{h['pnl_pct']:+.1%}",
                    'avoided_loss': f"${h['avoided_loss']:,.0f}",
                    'date': h['date']
                }
                for h in highlights
            ],
            'message': self._get_graveyard_message(shadow_report)
        }
    
    def _section_stress_test(self, metrics: ShieldMetrics) -> Dict[str, Any]:
        """
        스트레스 테스트 섹션
        
        Args:
            metrics: Shield Metrics
        
        Returns:
            섹션 딕셔너리
        """
        return {
            'title': '🌊 Stress Test (변동성 비교)',
            'comparison': {
                'market': {
                    'volatility': metrics.market_volatility,
                    'icon': '🌊',
                    'label': '높은 파도'
                },
                'portfolio': {
                    'volatility': metrics.portfolio_volatility,
                    'icon': '⎯',
                    'label': '잔잔한 호수'
                },
                'reduction': metrics.volatility_reduction
            },
            'message': (
                f"시장은 {metrics.market_volatility:.1%} 요동쳤지만, "
                f"귀하의 자산은 {metrics.portfolio_volatility:.1%}로 평온했습니다."
            )
        }
    
    def _section_drawdown(self, metrics: ShieldMetrics) -> Dict[str, Any]:
        """
        Drawdown 보호 섹션
        
        Args:
            metrics: Shield Metrics
        
        Returns:
            섹션 딕셔너리
        """
        return {
            'title': '📊 Drawdown Protection (낙폭 보호)',
            'comparison': {
                'market_dd': metrics.market_max_drawdown,
                'portfolio_dd': metrics.max_drawdown,
                'protection_rate': metrics.drawdown_protection
            },
            'message': (
                f"시장은 최대 {abs(metrics.market_max_drawdown):.1%} 하락했지만, "
                f"귀하의 계좌는 {abs(metrics.max_drawdown):.1%}만 하락했습니다. "
                f"({metrics.drawdown_protection:.0f}% 보호)"
            )
        }
    
    def _get_preservation_message(self, metrics: ShieldMetrics) -> str:
        """자본 보존 메시지"""
        grade = metrics.get_capital_preservation_grade()
        
        messages = {
            'S': "🏆 탁월한 자본 보존! 시스템이 귀하의 자산을 완벽히 지켰습니다.",
            'A': "✨ 우수한 방어 성과! 자본이 안전하게 보존되었습니다.",
            'B': "👍 양호한 보존율입니다. 시스템이 안정적으로 작동 중입니다.",
            'C': "⚠️ 보통 수준입니다. 시장 상황을 주시하고 있습니다.",
            'D': "🚨 주의 필요. 리스크 관리 강화가 필요합니다."
        }
        
        return messages.get(grade, messages['C'])
    
    def _get_graveyard_message(self, shadow_report: Dict) -> str:
        """Graveyard 메시지"""
        wins = shadow_report.get('defensive_wins', 0)
        total = shadow_report.get('total_rejected_proposals', 0)
        avoided = shadow_report.get('total_avoided_loss', 0)
        
        if wins == 0:
            return "이번 기간 동안 거부한 제안이 없습니다."
        
        return (
            f"이번 주 AI 위원회가 귀하의 자산을 지키기 위해 "
            f"{total}건의 제안 중 {wins}건을 거부했습니다. "
            f"그 결과 ${avoided:,.0f}의 손실을 방어했습니다."
        )
    
    def format_telegram_message(self, report: Dict) -> str:
        """
        텔레그램 메시지 포맷
        
        Args:
            report: Shield Report
        
        Returns:
            포맷된 메시지
        """
        headline = report['headline']
        sections = report['sections']
        
        message = f"""
🛡️ **Shield Report (방패 보고서)**
{report['metadata']['subtitle']}

━━━━━━━━━━━━━━━━━━
📊 **핵심 성과**

자본 보존율: **{headline['primary_kpi']['value']}** (등급: {headline['primary_kpi']['grade']})
방어한 손실: **{headline['secondary_kpis'][0]['value']}**
방어 성공: **{headline['secondary_kpis'][1]['value']}**

━━━━━━━━━━━━━━━━━━
{sections['the_graveyard']['title']}

총 거부: {sections['the_graveyard']['summary']['total_rejected']}건
방어 성공: {sections['the_graveyard']['summary']['defensive_wins']}건

{sections['the_graveyard']['message']}

━━━━━━━━━━━━━━━━━━
{sections['stress_test']['title']}

시장 변동성: {sections['stress_test']['comparison']['market']['icon']} {sections['stress_test']['comparison']['market']['volatility']:.1%}
내 계좌: {sections['stress_test']['comparison']['portfolio']['icon']} {sections['stress_test']['comparison']['portfolio']['volatility']:.1%}

{sections['stress_test']['message']}

━━━━━━━━━━━━━━━━━━
💬 **AI 위원회는 당신의 자산을 지키는 것을 최우선으로 합니다.**
"""
        
        return message.strip()


if __name__ == "__main__":
    # 테스트
    print("=== Shield Report Generator Test ===\n")
    
    print("이 모듈은 ShadowTradeTracker가 필요합니다.")
    print("실제 사용 예시:\n")
    
    print("""
    # Shield Report 생성
    from backend.backtest.shadow_trade_tracker import ShadowTradeTracker
    
    tracker = ShadowTradeTracker(db_session)
    generator = ShieldReportGenerator(tracker)
    
    report = generator.generate_shield_report(
        period_days=7,
        initial_capital=10_000_000,
        final_capital=9_985_000,
        market_data={'volatility': 0.25, 'max_drawdown': -0.12}
    )
    
    # 텔레그램 전송
    message = generator.format_telegram_message(report)
    telegram_bot.send_message(message)
    """)
    
    print("\n✅ Shield Report Generator 구현 완료!")
