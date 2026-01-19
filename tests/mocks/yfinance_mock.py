"""
YFinance API Mock

Yahoo Finance API 호출을 위한 Mock 클래스입니다.
FactChecker에서 실적 데이터와 가격 데이터를 검증할 때 사용합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class EarningsData:
    """실적 데이터"""
    ticker: str
    fiscal_date: str
    eps_actual: float
    eps_estimated: float
    revenue_actual: float
    revenue_estimated: float
    report_date: str


@dataclass
class PriceData:
    """가격 데이터"""
    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


class MockYFinanceClient:
    """
    YFinance API Mock 클래스

    실제 YFinance API를 호출하지 않고 테스트용 데이터를 반환합니다.
    """

    def __init__(self):
        """Mock 초기화"""
        # 테스트용 실적 데이터
        self._earnings_data = {
            "AAPL": EarningsData(
                ticker="AAPL",
                fiscal_date="2025-01-25",
                eps_actual=2.18,
                eps_estimated=2.10,
                revenue_actual=119.575,  # Billion
                revenue_estimated=118.0,
                report_date="2025-01-25"
            ),
            "NVDA": EarningsData(
                ticker="NVDA",
                fiscal_date="2025-02-26",
                eps_actual=5.16,
                eps_estimated=4.60,
                revenue_actual=22.1,  # Billion
                revenue_estimated=20.4,
                report_date="2025-02-26"
            ),
            "TSLA": EarningsData(
                ticker="TSLA",
                fiscal_date="2025-01-29",
                eps_actual=0.73,
                eps_estimated=0.74,
                revenue_actual=25.17,  # Billion
                revenue_estimated=25.64,
                report_date="2025-01-29"
            ),
        }

        # 테스트용 가격 데이터
        self._price_data = self._generate_sample_prices()

    async def get_latest_earnings(self, ticker: str) -> Optional[EarningsData]:
        """
        최신 실적 데이터 조회

        Args:
            ticker: 종목 코드

        Returns:
            EarningsData: 실적 데이터 (없으면 None)
        """
        return self._earnings_data.get(ticker.upper())

    async def get_price_history(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> List[PriceData]:
        """
        가격 이력 조회

        Args:
            ticker: 종목 코드
            period: 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
            interval: 간격 (1m, 5m, 15m, 1h, 1d, etc.)

        Returns:
            List[PriceData]: 가격 데이터 리스트
        """
        if ticker.upper() not in self._price_data:
            return []

        # 기간에 따라 필터링
        days_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
        }

        days = days_map.get(period, 30)
        cutoff_date = datetime.now() - timedelta(days=days)

        return [
            p for p in self._price_data[ticker.upper()]
            if datetime.strptime(p.date, "%Y-%m-%d") >= cutoff_date
        ]

    async def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        최신 가격 조회

        Args:
            ticker: 종목 코드

        Returns:
            float: 최신 종가 (없으면 None)
        """
        prices = await self.get_price_history(ticker, period="5d")
        if prices:
            return prices[-1].close
        return None

    def _generate_sample_prices(self) -> Dict[str, List[PriceData]]:
        """
        샘플 가격 데이터 생성

        Returns:
            Dict[str, List[PriceData]]: 종목별 가격 데이터
        """
        result = {}
        base_prices = {
            "AAPL": 195.0,
            "NVDA": 880.0,
            "TSLA": 380.0,
            "MSFT": 420.0,
            "GOOGL": 150.0,
        }

        for ticker, base_price in base_prices.items():
            prices = []
            for i in range(60):  # 60일 데이터
                date = (datetime.now() - timedelta(days=60 - i)).strftime("%Y-%m-%d")

                # 랜덤 변동 (±3%)
                import random
                random.seed(hash(f"{ticker}{date}") % 10000)  # 재현 가능한 랜덤
                change_pct = (random.random() - 0.5) * 0.06
                day_change = base_price * change_pct

                open_price = base_price + day_change * 0.5
                close_price = open_price + day_change * 0.5
                high_price = max(open_price, close_price) * (1 + abs(random.random() * 0.01))
                low_price = min(open_price, close_price) * (1 - abs(random.random() * 0.01))
                volume = int(random.random() * 50000000) + 10000000

                prices.append(PriceData(
                    ticker=ticker,
                    date=date,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume,
                ))

                base_price = close_price  # 다음 날의 기준

            result[ticker] = prices

        return result


# 싱글톤 인스턴스
_mock_yfinance_instance = None


def get_mock_yfinance_client() -> MockYFinanceClient:
    """Mock YFinance 클라이언트 싱글톤 반환"""
    global _mock_yfinance_instance
    if _mock_yfinance_instance is None:
        _mock_yfinance_instance = MockYFinanceClient()
    return _mock_yfinance_instance


# 테스트 헬퍼 함수
async def verify_earnings_from_mock(
    ticker: str,
    extracted_eps: float,
    tolerance: float = 0.05
) -> Dict[str, any]:
    """
    Mock 데이터로 실적 검증

    Args:
        ticker: 종목 코드
        extracted_eps: LLM이 추출한 EPS
        tolerance: 허용 오차 (기본 5%)

    Returns:
        Dict: 검증 결과
    """
    client = get_mock_yfinance_client()
    actual = await client.get_latest_earnings(ticker)

    if actual is None:
        return {
            "verified": False,
            "reason": "No earnings data found",
            "extracted": extracted_eps,
            "actual": None,
        }

    diff_pct = abs(extracted_eps - actual.eps_actual) / actual.eps_actual
    verified = diff_pct <= tolerance

    return {
        "verified": verified,
        "reason": f"Difference: {diff_pct:.1%}",
        "extracted": extracted_eps,
        "actual": actual.eps_actual,
        "estimated": actual.eps_estimated,
        "tolerance": tolerance,
    }
