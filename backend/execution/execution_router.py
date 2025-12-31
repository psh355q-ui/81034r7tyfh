"""
Execution Router - Fast Track vs Deep Dive

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    실행 경로 결정 - 즉시 실행 vs 심층 분석
    - Fast Track: 긴급 상황 (Stop Loss, 급락, 데이터 장애 등)
    - Deep Dive: 신규 진입, 포트폴리오 리밸런싱 등

Fast Track Triggers (즉시 실행):
    1. Stop Loss 도달
    2. 일일 손실 -5% 이상
    3. 데이터 장애 (market data outage)
    4. 극단적 변동성 (VIX > 40)
    5. 배당락일 당일 (dividend ex-date)

Deep Dive Required (심층 분석):
    1. 신규 포지션 진입
    2. 포트폴리오 리밸런싱
    3. 대형 포지션 (> 10% portfolio)
    4. 고위험 상품 (옵션, 레버리지 ETF)

Gemini's Key Insight:
    "Fast decisions (stop loss) vs slow decisions (new positions)를 분리하면
     비용 절감 + 속도 향상. Fast Track은 단순 룰 기반으로 처리."
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ExecutionMode(Enum):
    """실행 모드"""
    FAST_TRACK = "fast_track"  # 즉시 실행 (룰 기반)
    DEEP_DIVE = "deep_dive"    # 심층 분석 (AI 기반)


class ExecutionRouter:
    """실행 경로 결정 라우터"""

    def __init__(self):
        """Initialize Execution Router"""

        # ===================================================================
        # FAST TRACK TRIGGERS (즉시 실행)
        # ===================================================================
        self.FAST_TRACK_TRIGGERS = {
            'stop_loss_hit': True,              # Stop Loss 도달
            'daily_loss_threshold': -0.05,      # 일일 -5% 손실
            'vix_extreme': 40.0,                # VIX > 40
            'data_outage': True,                # 데이터 장애
            'ex_dividend_today': True,          # 배당락일 당일
            'circuit_breaker': True,            # 서킷브레이커 발동
            'portfolio_drawdown': -0.10         # 포트폴리오 -10% 손실
        }

        # ===================================================================
        # DEEP DIVE REQUIREMENTS (심층 분석 필요)
        # ===================================================================
        self.DEEP_DIVE_REQUIREMENTS = {
            'new_position': True,               # 신규 포지션
            'portfolio_rebalancing': True,      # 리밸런싱
            'large_position_pct': 0.10,         # 포지션 > 10%
            'high_risk_product': True,          # 고위험 상품
            'sector_rotation': True,            # 섹터 로테이션
            'earnings_event': True              # 어닝 이벤트 전후
        }

    def route(
        self,
        action: str,
        symbol: str,
        current_state: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        실행 경로 결정

        Args:
            action: 요청 액션 (buy/sell/hold)
            symbol: 종목 심볼
            current_state: 현재 상태
                {
                    'position_exists': bool,
                    'position_value': float,
                    'current_price': float,
                    'entry_price': float (if exists),
                    'stop_loss_price': float (if exists),
                    'daily_pnl_pct': float
                }
            market_conditions: 시장 상황 (optional)
                {
                    'vix': float,
                    'market_status': str,
                    'data_quality': str
                }
            portfolio_context: 포트폴리오 맥락 (optional)
                {
                    'total_value': float,
                    'total_pnl_pct': float,
                    'position_count': int
                }

        Returns:
            Dict containing:
                - execution_mode: FAST_TRACK | DEEP_DIVE
                - reasoning: 경로 결정 근거
                - triggered_by: 트리거 조건
                - urgency: low/medium/high/critical
                - estimated_processing_time: seconds
                - bypass_ai: bool (Fast Track일 때 True)
        """
        # ================================================================
        # STEP 1: Check Fast Track Triggers
        # ================================================================
        fast_track_check = self._check_fast_track_triggers(
            action=action,
            symbol=symbol,
            current_state=current_state,
            market_conditions=market_conditions,
            portfolio_context=portfolio_context
        )

        if fast_track_check['triggered']:
            return {
                'execution_mode': ExecutionMode.FAST_TRACK.value,
                'reasoning': fast_track_check['reasoning'],
                'triggered_by': fast_track_check['triggers'],
                'urgency': fast_track_check['urgency'],
                'estimated_processing_time': 1.0,  # 1초 이내 (룰 기반)
                'bypass_ai': True,  # AI 우회 - 코드만으로 실행
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'action': action
            }

        # ================================================================
        # STEP 2: Check Deep Dive Requirements
        # ================================================================
        deep_dive_check = self._check_deep_dive_requirements(
            action=action,
            symbol=symbol,
            current_state=current_state,
            portfolio_context=portfolio_context
        )

        if deep_dive_check['required']:
            return {
                'execution_mode': ExecutionMode.DEEP_DIVE.value,
                'reasoning': deep_dive_check['reasoning'],
                'triggered_by': deep_dive_check['requirements'],
                'urgency': 'low',
                'estimated_processing_time': 30.0,  # 30초 (AI 분석 포함)
                'bypass_ai': False,  # AI 분석 필요
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'action': action
            }

        # ================================================================
        # STEP 3: Default to Deep Dive (안전한 기본값)
        # ================================================================
        return {
            'execution_mode': ExecutionMode.DEEP_DIVE.value,
            'reasoning': 'Default to Deep Dive for safety',
            'triggered_by': ['default'],
            'urgency': 'medium',
            'estimated_processing_time': 30.0,
            'bypass_ai': False,
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'action': action
        }

    def _check_fast_track_triggers(
        self,
        action: str,
        symbol: str,
        current_state: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]],
        portfolio_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fast Track 트리거 체크

        Returns:
            {
                'triggered': bool,
                'triggers': List[str],
                'reasoning': str,
                'urgency': str
            }
        """
        triggers = []
        urgency = 'medium'

        # Trigger 1: Stop Loss Hit
        if current_state.get('position_exists', False):
            current_price = current_state.get('current_price', 0)
            stop_loss_price = current_state.get('stop_loss_price', 0)

            if stop_loss_price > 0 and current_price <= stop_loss_price:
                triggers.append('stop_loss_hit')
                urgency = 'critical'

        # Trigger 2: Daily Loss > -5%
        daily_pnl_pct = current_state.get('daily_pnl_pct', 0.0)
        if daily_pnl_pct <= self.FAST_TRACK_TRIGGERS['daily_loss_threshold']:
            triggers.append('daily_loss_threshold')
            if urgency != 'critical':
                urgency = 'high'

        # Trigger 3: VIX > 40 (Extreme Volatility)
        if market_conditions:
            vix = market_conditions.get('vix', 0)
            if vix >= self.FAST_TRACK_TRIGGERS['vix_extreme']:
                triggers.append('vix_extreme')
                if urgency not in ['critical', 'high']:
                    urgency = 'high'

            # Trigger 4: Data Outage
            data_quality = market_conditions.get('data_quality', 'good')
            if data_quality in ['poor', 'outage']:
                triggers.append('data_outage')
                urgency = 'critical'

            # Trigger 5: Circuit Breaker
            market_status = market_conditions.get('market_status', 'normal')
            if market_status == 'circuit_breaker':
                triggers.append('circuit_breaker')
                urgency = 'critical'

        # Trigger 6: Portfolio Drawdown > -10%
        if portfolio_context:
            total_pnl_pct = portfolio_context.get('total_pnl_pct', 0.0)
            if total_pnl_pct <= self.FAST_TRACK_TRIGGERS['portfolio_drawdown']:
                triggers.append('portfolio_drawdown')
                urgency = 'critical'

        # Reasoning
        if triggers:
            reasoning = f"Fast Track triggered: {', '.join(triggers)}"
        else:
            reasoning = 'No Fast Track triggers'

        return {
            'triggered': len(triggers) > 0,
            'triggers': triggers,
            'reasoning': reasoning,
            'urgency': urgency
        }

    def _check_deep_dive_requirements(
        self,
        action: str,
        symbol: str,
        current_state: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deep Dive 요구사항 체크

        Returns:
            {
                'required': bool,
                'requirements': List[str],
                'reasoning': str
            }
        """
        requirements = []

        # Requirement 1: New Position (Buy action + no existing position)
        if action == 'buy' and not current_state.get('position_exists', False):
            requirements.append('new_position')

        # Requirement 2: Large Position (> 10% of portfolio)
        if portfolio_context:
            position_value = current_state.get('position_value', 0)
            total_value = portfolio_context.get('total_value', 1)
            position_pct = position_value / total_value if total_value > 0 else 0

            if position_pct > self.DEEP_DIVE_REQUIREMENTS['large_position_pct']:
                requirements.append('large_position')

        # Requirement 3: Portfolio Rebalancing
        # (현재는 명시적으로 전달되지 않음 - 향후 확장 가능)

        # Requirement 4: High Risk Product
        # 종목 심볼로 판단 (간단한 휴리스틱)
        high_risk_patterns = ['TQQQ', 'SQQQ', 'SPXL', 'SPXS', 'UVXY']  # 3x 레버리지 ETF
        if any(pattern in symbol.upper() for pattern in high_risk_patterns):
            requirements.append('high_risk_product')

        # Reasoning
        if requirements:
            reasoning = f"Deep Dive required: {', '.join(requirements)}"
        else:
            reasoning = 'No specific Deep Dive requirements'

        return {
            'required': len(requirements) > 0,
            'requirements': requirements,
            'reasoning': reasoning
        }

    def get_router_info(self) -> Dict[str, Any]:
        """Get router information"""
        return {
            'name': 'ExecutionRouter',
            'execution_modes': [
                'FAST_TRACK (즉시 실행 - 룰 기반)',
                'DEEP_DIVE (심층 분석 - AI 기반)'
            ],
            'fast_track_triggers': self.FAST_TRACK_TRIGGERS,
            'deep_dive_requirements': self.DEEP_DIVE_REQUIREMENTS,
            'estimated_time': {
                'fast_track': '< 1 second',
                'deep_dive': '~ 30 seconds'
            },
            'gemini_insight': 'Fast decisions (stop loss) vs slow decisions (new positions) 분리'
        }


# Example usage
if __name__ == "__main__":
    router = ExecutionRouter()

    # Test 1: Stop Loss Hit (Fast Track)
    print("=== Test 1: Stop Loss Hit ===")
    result1 = router.route(
        action='sell',
        symbol='AAPL',
        current_state={
            'position_exists': True,
            'current_price': 148.0,
            'stop_loss_price': 150.0,  # Stop loss hit!
            'daily_pnl_pct': -0.03
        }
    )
    print(f"Mode: {result1['execution_mode']}")
    print(f"Reasoning: {result1['reasoning']}")
    print(f"Urgency: {result1['urgency']}")
    print(f"Processing Time: {result1['estimated_processing_time']}s")
    print()

    # Test 2: New Position (Deep Dive)
    print("=== Test 2: New Position ===")
    result2 = router.route(
        action='buy',
        symbol='NVDA',
        current_state={
            'position_exists': False,
            'current_price': 500.0,
            'daily_pnl_pct': 0.01
        }
    )
    print(f"Mode: {result2['execution_mode']}")
    print(f"Reasoning: {result2['reasoning']}")
    print(f"Processing Time: {result2['estimated_processing_time']}s")
    print()

    # Test 3: Extreme Volatility (Fast Track)
    print("=== Test 3: Extreme Volatility ===")
    result3 = router.route(
        action='sell',
        symbol='SPY',
        current_state={
            'position_exists': True,
            'current_price': 450.0,
            'daily_pnl_pct': -0.02
        },
        market_conditions={
            'vix': 45.0,  # Extreme!
            'market_status': 'volatile'
        }
    )
    print(f"Mode: {result3['execution_mode']}")
    print(f"Reasoning: {result3['reasoning']}")
    print(f"Urgency: {result3['urgency']}")
    print()

    # Print router info
    print("=== Router Info ===")
    info = router.get_router_info()
    print(f"Fast Track Triggers: {info['fast_track_triggers']}")
    print(f"Deep Dive Requirements: {info['deep_dive_requirements']}")
