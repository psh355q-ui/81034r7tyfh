"""
FRED API Client

Federal Reserve Economic Data (FRED) API 조회를 위한 실제 클라이언트입니다.
FactChecker에서 경제 지표 데이터를 검증할 때 사용합니다.

Reference: tests/mocks/fred_mock.py (Mock implementation)

API Key: https://fred.stlouisfed.org/docs/api/api_key.html
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None
    logging.warning("httpx not installed. Install with: pip install httpx")


@dataclass
class EconomicSeries:
    """경제 지표 시계열 데이터"""
    series_id: str
    name: str
    units: str
    frequency: str  # daily, weekly, monthly, quarterly, annual
    data_points: Dict[str, float]  # date -> value


class FREDClient:
    """
    FRED API 실제 클라이언트

    Federal Reserve Economic Data API를 호출하여 실제 경제 지표를 가져옵니다.
    """

    # FRED API base URL
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = None):
        """
        FRED 클라이언트 초기화

        Args:
            api_key: FRED API 키 (없으면 환경변수에서 가져옴)
        """
        if httpx is None:
            raise ImportError(
                "httpx is not installed. "
                "Install with: pip install httpx"
            )

        import os
        from dotenv import load_dotenv

        load_dotenv()

        if api_key is None:
            api_key = os.getenv("FRED_API_KEY")

        if api_key is None:
            raise ValueError(
                "FRED API key is required. "
                "Get one from https://fred.stlouisfed.org/docs/api/api_key.html "
                "and set FRED_API_KEY environment variable."
            )

        self._api_key = api_key
        self._logger = logging.getLogger(__name__)

        # 비동기 HTTP 클라이언트
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 가져오기"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        """클라이언트 닫기"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

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
        try:
            # 먼저 시리즈 정보 가져오기
            series_info = await self._get_series_info(series_id)
            if series_info is None:
                return None

            # 데이터 가져오기
            observations = await self._get_observations(
                series_id, start_date, end_date
            )

            if not observations:
                return None

            # EconomicSeries 생성
            return EconomicSeries(
                series_id=series_id,
                name=series_info.get("title", series_id),
                units=series_info.get("units", ""),
                frequency=series_info.get("frequency", ""),
                data_points={obs["date"]: obs["value"] for obs in observations}
            )

        except Exception as e:
            self._logger.error(f"Error fetching series {series_id}: {e}")
            return None

    async def _get_series_info(self, series_id: str) -> Optional[Dict]:
        """시리즈 정보 조회"""
        try:
            client = await self._get_client()

            url = f"{self.BASE_URL}/series"
            params = {
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json"
            }

            response = await client.get(url, params=params)

            if response.status_code != 200:
                self._logger.error(f"FRED API error: {response.status_code}")
                return None

            data = response.json()

            # 시리즈 정보 추출
            if "seriess" in data and len(data["seriess"]) > 0:
                return data["seriess"][0]

            return None

        except Exception as e:
            self._logger.error(f"Error fetching series info: {e}")
            return None

    async def _get_observations(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """관측치 조회"""
        try:
            client = await self._get_client()

            url = f"{self.BASE_URL}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json"
            }

            if start_date:
                params["observation_start"] = start_date
            if end_date:
                params["observation_end"] = end_date

            response = await client.get(url, params=params)

            if response.status_code != 200:
                return []

            data = response.json()

            # 관측치 추출
            if "observations" in data:
                # 값이 문자열로 오므로 float로 변환
                observations = []
                for obs in data["observations"]:
                    try:
                        value = float(obs["value"]) if obs["value"] != "." else None
                        observations.append({
                            "date": obs["date"],
                            "value": value
                        })
                    except (ValueError, TypeError):
                        continue

                return observations

            return []

        except Exception as e:
            self._logger.error(f"Error fetching observations: {e}")
            return []

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
_fred_instance = None


def get_fred_client(api_key: Optional[str] = None) -> FREDClient:
    """FRED 클라이언트 싱글톤 반환"""
    global _fred_instance
    if _fred_instance is None:
        _fred_instance = FREDClient(api_key=api_key)
    return _fred_instance
