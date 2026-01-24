"""
3단 깔때기 구조 생성기 - v2.3

ChatGPT/Gemini 합의 기반:
1. Market State (신호등) - 🟢🟡🔴
2. Actionable Scenarios (IF-THEN)
3. Portfolio Impact (내 포트폴리오 영향)

작성일: 2026-01-24
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class MarketSignal(str, Enum):
    """시장 신호등"""
    GREEN = "🟢"   # Bullish / Risk-On
    YELLOW = "🟡"  # Neutral / Mixed
    RED = "🔴"     # Bearish / Risk-Off


class TrendDirection(str, Enum):
    """추세 방향"""
    UP = "UP"
    SIDE = "SIDE"
    DOWN = "DOWN"


@dataclass
class MarketState:
    """시장 상태 신호등"""
    signal: MarketSignal
    trend: TrendDirection
    risk_score: int  # 0-100
    top_action: str  # 한 줄 결론


@dataclass
class ActionableScenario:
    """IF-THEN 시나리오"""
    case_id: str  # A, B, C, D
    condition: str  # IF 조건
    action: str  # THEN 행동
    asset: str  # 대상 자산
    size_pct: float  # 비중 (0.0 ~ 1.0)
    rationale: str  # 근거
    priority: int  # 우선순위 (1-4)


@dataclass
class PortfolioImpact:
    """포트폴리오 영향"""
    focus_assets: List[str]  # 주목 자산
    commentary: str  # 코멘터리
    cash_change_pct: float  # 현금 비중 변화
    equity_change_pct: float  # 주식 비중 변화


# ============================================================================
# Funnel Generator
# ============================================================================

class FunnelGenerator:
    """
    3단 깔때기 생성기
    
    입력: 원시 데이터 (지표, 뉴스, 시그널)
    출력: 3단 깔때기 구조 (State → Scenarios → Impact)
    """
    
    def __init__(self):
        self.max_scenarios = 4  # 최대 시나리오 개수
    
    def generate(
        self,
        indicators: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        portfolio: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        3단 깔때기 구조 생성
        
        Args:
            indicators: 핵심 지표 (us10y, vix, dxy, sector_leadership)
            scenarios: 시나리오 리스트 (condition, action, asset, size_pct, rationale)
            portfolio: 포트폴리오 정보 (선택)
        
        Returns:
            {
                "market_state": {...},
                "actionable_scenarios": [...],
                "portfolio_impact": {...}
            }
        """
        logger.info("Generating 3-level funnel structure")
        
        # 1. Market State (신호등)
        market_state = self._generate_market_state(indicators)
        logger.info(f"Market State: {market_state.signal.value} {market_state.trend.value}")
        
        # 2. Actionable Scenarios (IF-THEN)
        actionable = self._format_scenarios(scenarios)
        logger.info(f"Actionable Scenarios: {len(actionable)} scenarios")
        
        # 3. Portfolio Impact (포트폴리오 영향)
        impact = self._analyze_portfolio_impact(portfolio or {}, scenarios)
        logger.info(f"Portfolio Impact: {impact.commentary}")
        
        return {
            "market_state": {
                "signal": market_state.signal.value,
                "trend": market_state.trend.value,
                "risk_score": market_state.risk_score,
                "top_action": market_state.top_action
            },
            "actionable_scenarios": [
                {
                    "case": s.case_id,
                    "condition": s.condition,
                    "action": s.action,
                    "asset": s.asset,
                    "size_pct": s.size_pct,
                    "rationale": s.rationale,
                    "priority": s.priority
                }
                for s in actionable
            ],
            "portfolio_impact": {
                "focus_assets": impact.focus_assets,
                "commentary": impact.commentary,
                "cash_change_pct": impact.cash_change_pct,
                "equity_change_pct": impact.equity_change_pct
            }
        }
    
    def _generate_market_state(self, indicators: Dict[str, Any]) -> MarketState:
        """
        시장 상태 판단 (신호등)
        
        Args:
            indicators: 핵심 지표
        
        Returns:
            MarketState 객체
        """
        # 지표 추출
        vix = indicators.get('vix', {}).get('value', 20.0)
        us10y_change = indicators.get('us10y', {}).get('day_change_bp', 0.0)
        dxy = indicators.get('dxy', {}).get('value', 103.0)
        sector_leadership = indicators.get('sector_leadership', [])
        
        # 리스크 점수 계산
        risk_score = self._calculate_risk_score(vix, us10y_change)
        
        # 신호등 및 추세 결정
        if risk_score <= 30:
            # GREEN: 낮은 리스크
            signal = MarketSignal.GREEN
            trend = TrendDirection.UP
            
            # Technology가 리더인지 확인
            if sector_leadership and 'Technology' in sector_leadership[:2]:
                action = "기술주 비중 확대"
            else:
                action = "성장주 매수 기회"
        
        elif risk_score <= 60:
            # YELLOW: 중간 리스크
            signal = MarketSignal.YELLOW
            trend = TrendDirection.SIDE
            action = "현금 비중 유지, 선별적 매수"
        
        else:
            # RED: 높은 리스크
            signal = MarketSignal.RED
            trend = TrendDirection.DOWN
            
            if vix > 30:
                action = "방어 포지션 전환 (현금/채권)"
            else:
                action = "방어주로 로테이션 (헬스케어, 유틸리티)"
        
        logger.debug(
            f"Market State: VIX={vix:.1f}, US10Y_chg={us10y_change:.1f}bp → "
            f"Risk={risk_score}, Signal={signal.value}"
        )
        
        return MarketState(
            signal=signal,
            trend=trend,
            risk_score=risk_score,
            top_action=action
        )
    
    def _calculate_risk_score(self, vix: float, rate_change: float) -> int:
        """
        리스크 점수 계산 (0-100)
        
        공식:
        - VIX 기여 (최대 50점): (VIX - 12) × 2.5
        - 금리 변동 기여 (최대 30점): |rate_change| × 3
        - 기본 점수: 20점
        
        Args:
            vix: VIX 값
            rate_change: 금리 변화 (bp)
        
        Returns:
            리스크 점수 (0-100)
        """
        # VIX 기여 (VIX 12 이하는 0점, 32 이상은 50점)
        vix_score = min(50, max(0, (vix - 12) * 2.5))
        
        # 금리 변동 기여 (±10bp 이상은 30점)
        rate_score = min(30, abs(rate_change) * 3)
        
        # 기본 점수 (시장은 항상 어느 정도 리스크가 있음)
        base_score = 10
        
        total = int(min(100, vix_score + rate_score + base_score))
        
        logger.debug(
            f"Risk Score breakdown: VIX={vix_score:.0f} + Rate={rate_score:.0f} + Base={base_score} = {total}"
        )
        
        return total
    
    def _format_scenarios(self, scenarios: List[Dict[str, Any]]) -> List[ActionableScenario]:
        """
        시나리오 포맷팅 (최대 4개)
        
        Args:
            scenarios: 원시 시나리오 리스트
        
        Returns:
            ActionableScenario 리스트 (최대 4개)
        """
        formatted = []
        
        # 우선순위 정렬 (없으면 입력 순서)
        sorted_scenarios = sorted(
            scenarios,
            key=lambda s: s.get('priority', 999)
        )
        
        for i, s in enumerate(sorted_scenarios[:self.max_scenarios]):
            formatted.append(
                ActionableScenario(
                    case_id=chr(65 + i),  # A, B, C, D
                    condition=s.get('condition', ''),
                    action=s.get('action', ''),
                    asset=s.get('asset', ''),
                    size_pct=s.get('size_pct', 0.0),
                    rationale=s.get('rationale', ''),
                    priority=s.get('priority', i + 1)
                )
            )
        
        logger.debug(f"Formatted {len(formatted)} scenarios (max {self.max_scenarios})")
        return formatted
    
    def _analyze_portfolio_impact(
        self,
        portfolio: Dict[str, Any],
        scenarios: List[Dict[str, Any]]
    ) -> PortfolioImpact:
        """
        포트폴리오 영향 분석
        
        Args:
            portfolio: 포트폴리오 정보
            scenarios: 시나리오 리스트
        
        Returns:
            PortfolioImpact 객체
        """
        # 시나리오에서 언급된 자산 추출 (중복 제거)
        focus_assets = list(set(
            s.get('asset', '') for s in scenarios if s.get('asset')
        ))
        
        # 상위 5개만
        focus_assets = focus_assets[:5]
        
        # 현금/주식 비중 변화 계산
        buy_scenarios = [
            s for s in scenarios
            if 'BUY' in s.get('action', '').upper() or 'INCREASE' in s.get('action', '').upper()
        ]
        sell_scenarios = [
            s for s in scenarios
            if 'SELL' in s.get('action', '').upper() or 'REDUCE' in s.get('action', '').upper()
        ]
        
        # 비중 변화 합계 (절대값 사용)
        buy_total = sum(abs(s.get('size_pct', 0.0)) for s in buy_scenarios)
        sell_total = sum(abs(s.get('size_pct', 0.0)) for s in sell_scenarios)
        
        cash_change = sell_total - buy_total  # 팔면 현금 증가, 사면 현금 감소
        equity_change = -cash_change  # 반대
        
        # 코멘터리 생성
        if abs(cash_change) < 0.01:
            commentary = "현재 포지션 유지 권장"
        elif cash_change > 0.05:
            commentary = f"현금 비중 {cash_change*100:.0f}% 확대 (방어적)"
        elif cash_change < -0.05:
            commentary = f"주식 비중 {equity_change*100:.0f}% 확대 (공격적)"
        else:
            commentary = "포트폴리오 미세 조정"
        
        logger.debug(
            f"Portfolio Impact: Buy={buy_total:.2%}, Sell={sell_total:.2%}, "
            f"Cash_chg={cash_change:.2%}"
        )
        
        return PortfolioImpact(
            focus_assets=focus_assets,
            commentary=commentary,
            cash_change_pct=round(cash_change, 4),
            equity_change_pct=round(equity_change, 4)
        )


# ============================================================================
# Helper Functions
# ============================================================================

def create_sample_funnel() -> Dict[str, Any]:
    """샘플 깔때기 생성 (테스트용)"""
    generator = FunnelGenerator()
    
    # 샘플 지표
    indicators = {
        'vix': {'value': 15.5, 'change': -1.2},
        'us10y': {'value': 4.15, 'day_change_bp': 3.5},
        'dxy': {'value': 103.2},
        'sector_leadership': ['Technology', 'Communication Services', 'Healthcare']
    }
    
    # 샘플 시나리오
    scenarios = [
        {
            'condition': 'US10Y < 4.20%',
            'action': 'INCREASE_EXPOSURE',
            'asset': 'QQQ',
            'size_pct': 0.10,
            'rationale': '금리 안정 시 기술주 선호',
            'priority': 1
        },
        {
            'condition': 'VIX > 20',
            'action': 'REDUCE_EXPOSURE',
            'asset': 'QQQ',
            'size_pct': -0.15,
            'rationale': '변동성 급등 시 비중 축소',
            'priority': 2
        }
    ]
    
    return generator.generate(indicators, scenarios)


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("3단 깔때기 구조 생성기 테스트")
    print("=" * 60)
    
    # 샘플 깔때기 생성
    funnel = create_sample_funnel()
    
    print("\n1️⃣ Market State (신호등)")
    print("-" * 60)
    ms = funnel['market_state']
    print(f"  Signal: {ms['signal']}")
    print(f"  Trend: {ms['trend']}")
    print(f"  Risk Score: {ms['risk_score']}/100")
    print(f"  Top Action: {ms['top_action']}")
    
    print("\n2️⃣ Actionable Scenarios (IF-THEN)")
    print("-" * 60)
    for scenario in funnel['actionable_scenarios']:
        print(f"\n  Case {scenario['case']}:")
        print(f"    IF: {scenario['condition']}")
        print(f"    THEN: {scenario['action']} {scenario['asset']} ({scenario['size_pct']*100:.0f}%)")
        print(f"    Rationale: {scenario['rationale']}")
    
    print("\n3️⃣ Portfolio Impact")
    print("-" * 60)
    pi = funnel['portfolio_impact']
    print(f"  Focus Assets: {', '.join(pi['focus_assets'])}")
    print(f"  Cash Change: {pi['cash_change_pct']*100:+.1f}%")
    print(f"  Equity Change: {pi['equity_change_pct']*100:+.1f}%")
    print(f"  Commentary: {pi['commentary']}")
    
    print("\n" + "=" * 60)
    print("✅ 3단 깔때기 테스트 완료")
    print("=" * 60)
