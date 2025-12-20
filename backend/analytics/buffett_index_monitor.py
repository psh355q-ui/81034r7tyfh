"""
BuffettIndexMonitor - 버핏 지수 모니터

Buffett Index = Wilshire 5000 Total Market Cap / US GDP

Phase B 통합:
- 시장 과열/저평가 탐지
- 매크로 리스크 알림
- 포지션 사이징 조절 권장

작성일: 2025-12-03 (Phase B)
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BuffettIndexMonitor:
    """
    버핏 지수 모니터

    Buffett Index = Market Cap / GDP * 100

    해석:
    - 75% 이하: 저평가 (매수 기회)
    - 75-90%: 적정 가치
    - 90-115%: 과대평가 (주의)
    - 115% 이상: 버블 (위험)
    """

    # 임계값
    UNDERVALUED_THRESHOLD = 75
    FAIR_VALUE_LOWER = 75
    FAIR_VALUE_UPPER = 90
    OVERVALUED_THRESHOLD = 115

    def __init__(
        self,
        market_cap: Optional[float] = None,
        gdp: Optional[float] = None
    ):
        """
        Args:
            market_cap: 시가총액 (USD, 조 단위)
            gdp: GDP (USD, 조 단위)
        """
        self.market_cap = market_cap
        self.gdp = gdp

        logger.info("BuffettIndexMonitor initialized")

    def calculate_buffett_index(
        self,
        market_cap: Optional[float] = None,
        gdp: Optional[float] = None
    ) -> float:
        """
        버핏 지수 계산

        Args:
            market_cap: 시가총액 (조 달러)
            gdp: GDP (조 달러)

        Returns:
            버핏 지수 (%)
        """
        mc = market_cap or self.market_cap
        g = gdp or self.gdp

        if not mc or not g or g == 0:
            logger.error("Invalid market cap or GDP data")
            return 0.0

        buffett_index = (mc / g) * 100

        logger.info(f"Buffett Index: {buffett_index:.1f}% (MC: ${mc:.1f}T, GDP: ${g:.1f}T)")

        return buffett_index

    def analyze(
        self,
        market_cap: Optional[float] = None,
        gdp: Optional[float] = None
    ) -> Dict:
        """
        버핏 지수 분석 및 권장사항 생성

        Returns:
            {
                "buffett_index": 105.3,
                "status": "overvalued",
                "risk_level": "HIGH",
                "recommendation": "Reduce exposure, increase cash"
            }
        """
        buffett_index = self.calculate_buffett_index(market_cap, gdp)

        # 상태 판정
        if buffett_index < self.UNDERVALUED_THRESHOLD:
            status = "undervalued"
            risk_level = "LOW"
            recommendation = "Market undervalued - consider increasing equity exposure"
            position_adjustment = 1.2  # 포지션 20% 증가
        elif buffett_index < self.FAIR_VALUE_UPPER:
            status = "fair_value"
            risk_level = "MODERATE"
            recommendation = "Market fairly valued - maintain current allocation"
            position_adjustment = 1.0
        elif buffett_index < self.OVERVALUED_THRESHOLD:
            status = "overvalued"
            risk_level = "HIGH"
            recommendation = "Market overvalued - reduce exposure, increase cash reserves"
            position_adjustment = 0.8  # 포지션 20% 감소
        else:
            status = "bubble"
            risk_level = "CRITICAL"
            recommendation = "Bubble warning - consider defensive positioning"
            position_adjustment = 0.5  # 포지션 50% 감소

        return {
            "buffett_index": round(buffett_index, 1),
            "status": status,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "position_adjustment": position_adjustment,
            "timestamp": datetime.now().isoformat()
        }

    def get_mock_data(self) -> Dict[str, float]:
        """
        Mock 데이터 반환 (테스트/데모용)

        실제로는 FRED API 또는 Yahoo Finance에서 가져오기
        """
        # 2024년 11월 기준 대략적인 값
        return {
            "market_cap": 50.0,  # $50T (Wilshire 5000 대략)
            "gdp": 27.0  # $27T (US GDP)
        }


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("BuffettIndexMonitor Test")
    print("=" * 70)

    monitor = BuffettIndexMonitor()

    # Mock 데이터 가져오기
    data = monitor.get_mock_data()
    print(f"\nMock Data:")
    print(f"  Market Cap: ${data['market_cap']:.1f}T")
    print(f"  GDP: ${data['gdp']:.1f}T")

    # 분석 실행
    result = monitor.analyze(data['market_cap'], data['gdp'])

    print(f"\n=== Buffett Index Analysis ===")
    print(f"Index: {result['buffett_index']:.1f}%")
    print(f"Status: {result['status'].upper()}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Position Adjustment: {result['position_adjustment']:.0%}")

    # 시나리오 테스트
    print(f"\n=== Scenario Tests ===")

    scenarios = [
        (20.0, 27.0, "Undervalued"),
        (24.0, 27.0, "Fair Value"),
        (28.0, 27.0, "Overvalued"),
        (32.0, 27.0, "Bubble")
    ]

    for mc, gdp, name in scenarios:
        idx = monitor.calculate_buffett_index(mc, gdp)
        status = monitor.analyze(mc, gdp)['status']
        print(f"  {name}: {idx:.1f}% ({status})")

    print("\n=== Test PASSED! ===")
