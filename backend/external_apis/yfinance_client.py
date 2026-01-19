"""
YFinance API Client

Yahoo Finance API 실제 호출을 위한 클라이언트입니다.
FactChecker에서 실적 데이터와 가격 데이터를 검증할 때 사용합니다.

Reference: tests/mocks/yfinance_mock.py (Mock implementation)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import yfinance as yf
except ImportError:
    yf = None
    logging.warning("yfinance not installed. Install with: pip install yfinance")


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


class YFinanceClient:
    """
    YFinance API 실제 클라이언트

    Yahoo Finance API를 호출하여 실제 시장 데이터를 가져옵니다.
    """

    def __init__(self):
        """YFinance 클라이언트 초기화"""
        if yf is None:
            raise ImportError(
                "yfinance is not installed. "
                "Install with: pip install yfinance"
            )
        self._logger = logging.getLogger(__name__)

    async def get_latest_earnings(self, ticker: str) -> Optional[EarningsData]:
        """
        최신 실적 데이터 조회

        Args:
            ticker: 종목 코드

        Returns:
            EarningsData: 실적 데이터 (없으면 None)
        """
        try:
            stock = yf.Ticker(ticker.upper())

            # 재무 정보 가져오기
            info = stock.info

            # 실적 데이터 추출
            earnings_data = None

            # EPS 데이터
            eps_actual = info.get("epsTrailingTwelveMonths")
            eps_estimated = info.get("epsForward")

            # 매출 데이터
            revenue_actual = info.get("totalRevenue")
            revenue_estimated = info.get("revenueEstimate")

            # 보고서 날짜
            fiscal_date = info.get("lastFiscalYearEnd")
            report_date = info.get("lastQuarterEnd")

            # 필수 데이터가 있는지 확인
            if eps_actual is not None or revenue_actual is not None:
                earnings_data = EarningsData(
                    ticker=ticker.upper(),
                    fiscal_date=self._format_date(fiscal_date) if fiscal_date else "",
                    eps_actual=eps_actual or 0.0,
                    eps_estimated=eps_estimated or 0.0,
                    revenue_actual=(revenue_actual or 0.0) / 1_000_000_000 if revenue_actual else 0.0,  # Convert to billions
                    revenue_estimated=(revenue_estimated or 0.0) / 1_000_000_000 if revenue_estimated else 0.0,
                    report_date=self._format_date(report_date) if report_date else "",
                )

            return earnings_data

        except Exception as e:
            self._logger.error(f"Error fetching earnings for {ticker}: {e}")
            return None

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
        try:
            stock = yf.Ticker(ticker.upper())

            # 기간 매핑
            period_map = {
                "1d": "1d",
                "5d": "5d",
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
            }

            actual_period = period_map.get(period, "1mo")

            # 가격 데이터 조회
            hist = stock.history(period=actual_period, interval=interval)

            if hist.empty:
                return []

            # PriceData로 변환
            price_data = []
            for date, row in hist.iterrows():
                price_data.append(PriceData(
                    ticker=ticker.upper(),
                    date=date.strftime("%Y-%m-%d"),
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=int(row.get("Volume", 0)),
                    adjusted_close=float(row.get("Adj Close", row.get("Close", 0))),
                ))

            return price_data

        except Exception as e:
            self._logger.error(f"Error fetching price history for {ticker}: {e}")
            return []

    async def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        최신 가격 조회

        Args:
            ticker: 종목 코드

        Returns:
            float: 최신 종가 (없으면 None)
        """
        try:
            stock = yf.Ticker(ticker.upper())

            # 오늘 가격 조회
            hist = stock.history(period="1d")

            if hist.empty:
                return None

            return float(hist["Close"].iloc[-1])

        except Exception as e:
            self._logger.error(f"Error fetching latest price for {ticker}: {e}")
            return None

    def _format_date(self, date_input) -> str:
        """날짜 포맷팅"""
        if isinstance(date_input, str):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.strftime("%Y-%m-%d")
        elif isinstance(date_input, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(date_input).strftime("%Y-%m-%d")
        return ""


# 싱글톤 인스턴스
_yfinance_instance = None


def get_yfinance_client() -> YFinanceClient:
    """YFinance 클라이언트 싱글톤 반환"""
    global _yfinance_instance
    if _yfinance_instance is None:
        _yfinance_instance = YFinanceClient()
    return _yfinance_instance
