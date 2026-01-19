"""
FRED API Mock

Federal Reserve Economic Data (FRED) API 조회를 위한 Mock 클래스입니다.
FactChecker에서 경제 지표 데이터를 검증할 때 사용합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EconomicSeries:
    """경제 지표 시계열 데이터"""
    series_id: str
    name: str
    units: str
    frequency: str  # daily, weekly, monthly, quarterly, annual
    data_points: Dict[str, float]  # date -> value


class MockFREDClient:
    """
    FRED API Mock 클래스

    실제 FRED API를 호출하지 않고 테스트용 데이터를 반환합니다.
    """

    def __init__(self):
        """Mock 초기화"""
        # 테스트용 경제 지표 데이터
        self._series = {
            "FEDFUNDS": EconomicSeries(
                series_id="FEDFUNDS",
                name="Federal Funds Effective Rate",
                units="Percent",
                frequency="monthly",
                data_points=self._generate_fed_funds_rate()
            ),
            "UNRATE": EconomicSeries(
                series_id="UNRATE",
                name="Unemployment Rate",
                units="Percent",
                frequency="monthly",
                data_points=self._generate_unemployment_rate()
            ),
            "CPIAUCSL": EconomicSeries(
                series_id="CPIAUCSL",
                name="Consumer Price Index for All Urban Consumers",
                units="Index 1982-1984=100",
                frequency="monthly",
                data_points=self._generate_cpi()
            ),
            "GDP": EconomicSeries(
                series_id="GDP",
                name="Gross Domestic Product",
                units="Billions of Dollars",
                frequency="quarterly",
                data_points=self._generate_gdp()
            ),
        }

    def _generate_fed_funds_rate(self) -> Dict[str, float]:
        """연방기금금리 시계열 생성"""
        data = {}
        base_date = datetime(2024, 1, 1)

        # 기본금리: 4.75% ~ 5.25% 범위
        for i in range(24):  # 24개월
            date = base_date + timedelta(days=30 * i)
            date_str = date.strftime("%Y-%m-%d")

            # 최근 인상 내역 반영
            if i < 6:
                rate = 5.25 + (i % 3) * 0.25
            else:
                rate = 5.25

            data[date_str] = round(rate, 2)

        return data

    def _generate_unemployment_rate(self) -> Dict[str, float]:
        """실업률 시계열 생성"""
        data = {}
        base_date = datetime(2024, 1, 1)

        for i in range(24):
            date = base_date + timedelta(days=30 * i)
            date_str = date.strftime("%Y-%m-%d")

            # 3.7% ~ 4.2% 범위
            import random
            random.seed(i)
            rate = 3.7 + random.random() * 0.5
            data[date_str] = round(rate, 1)

        return data

    def _generate_cpi(self) -> Dict[str, float]:
        """CPI 시계열 생성"""
        data = {}
        base_date = datetime(2024, 1, 1)
        base_value = 310.0

        for i in range(24):
            date = base_date + timedelta(days=30 * i)
            date_str = date.strftime("%Y-%m-%d")

            # 월별 0.2% ~ 0.4% 인상
            import random
            random.seed(i + 100)
            increase = base_value * (0.002 + random.random() * 0.002)
            base_value += increase
            data[date_str] = round(base_value, 3)

        return data

    def _generate_gdp(self) -> Dict[str, float]:
        """GDP 시계열 생성 (분기별)"""
        data = {}
        base_date = datetime(2023, 1, 1)
        base_value = 27000.0

        for i in range(8):  # 8분기
            # 분기 시작일
            q_start = (i // 4) + 2023
            q_num = (i % 4) + 1
            date_str = f"{q_start}-Q{q_num}"

            # 분기별 0.5% ~ 2% 성장
            import random
            random.seed(i + 200)
            growth = base_value * (0.005 + random.random() * 0.015)
            base_value += growth
            data[date_str] = round(base_value, 2)

        return data

    async def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[EconomicSeries]:
        """
        경제 지표 시계열 조회

        Args:
            series_id: 지표 ID (FEDFUNDS, UNRATE 등)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            EconomicSeries: 시계열 데이터 (없으면 None)
        """
        series = self._series.get(series_id)
        if series is None:
            return None

        # 날짜 필터링
        if start_date or end_date:
            filtered_data = {}
            for date_str, value in series.data_points.items():
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                filtered_data[date_str] = value

            # 필터링된 데이터로 새 시리즈 생성
            return EconomicSeries(
                series_id=series.series_id,
                name=series.name,
                units=series.units,
                frequency=series.frequency,
                data_points=filtered_data
            )

        return series

    async def get_latest_value(self, series_id: str) -> Optional[float]:
        """
        최신 값 조회

        Args:
            series_id: 지표 ID

        Returns:
            float: 최신 값 (없으면 None)
        """
        series = await self.get_series(series_id)
        if series and series.data_points:
            # 가장 최근 날짜의 값
            latest_date = max(series.data_points.keys())
            return series.data_points[latest_date]
        return None

    async def get_fed_funds_rate(self) -> Optional[float]:
        """연방기금금리 조회"""
        return await self.get_latest_value("FEDFUNDS")

    async def get_unemployment_rate(self) -> Optional[float]:
        """실업률 조회"""
        return await self.get_latest_value("UNRATE")

    async def verify_economic_indicator(
        self,
        indicator_name: str,
        extracted_value: float,
        tolerance: float = 0.02
    ) -> Dict[str, any]:
        """
        경제 지표 검증

        Args:
            indicator_name: 지표 이름
            extracted_value: LLM이 추출한 값
            tolerance: 허용 오차 (기본 2%)

        Returns:
            Dict: 검증 결과
        """
        # 지표 이름에서 시리즈 ID 매핑
        name_to_id = {
            "fed funds rate": "FEDFUNDS",
            "federal funds rate": "FEDFUNDS",
            "interest rate": "FEDFUNDS",
            "unemployment rate": "UNRATE",
            "cpi": "CPIAUCSL",
            "consumer price index": "CPIAUCSL",
            "gdp": "GDP",
        }

        series_id = name_to_id.get(indicator_name.lower())
        if series_id is None:
            return {
                "verified": False,
                "reason": "Indicator not found in database",
                "extracted": extracted_value,
                "actual": None,
            }

        actual = await self.get_latest_value(series_id)
        if actual is None:
            return {
                "verified": False,
                "reason": "No data available for this indicator",
                "extracted": extracted_value,
                "actual": None,
            }

        # 상대 오차 계산 (GDP 같은 큰 값은 절대 오차 사용)
        if actual > 1000:
            diff = abs(extracted_value - actual)
            verified = diff <= actual * tolerance * 10  # 큰 값은 허용 오차 완화
        else:
            diff_pct = abs(extracted_value - actual) / actual
            verified = diff_pct <= tolerance

        return {
            "verified": verified,
            "reason": f"Difference: {diff:.2f} ({diff_pct:.1%})" if actual <= 1000 else f"Difference: {diff:.2f}",
            "extracted": extracted_value,
            "actual": actual,
            "series_id": series_id,
            "tolerance": tolerance,
        }


# 싱글톤 인스턴스
_mock_fred_instance = None


def get_mock_fred_client() -> MockFREDClient:
    """Mock FRED 클라이언트 싱글톤 반환"""
    global _mock_fred_instance
    if _mock_fred_instance is None:
        _mock_fred_instance = MockFREDClient()
    return _mock_fred_instance


# 테스트 헬퍼 함수
async def verify_economic_from_mock(
    indicator_name: str,
    extracted_value: float,
    tolerance: float = 0.02
) -> Dict[str, any]:
    """
    Mock 데이터로 경제 지표 검증

    Args:
        indicator_name: 지표 이름
        extracted_value: LLM이 추출한 값
        tolerance: 허용 오차

    Returns:
        Dict: 검증 결과
    """
    client = get_mock_fred_client()
    return await client.verify_economic_indicator(indicator_name, extracted_value, tolerance)
