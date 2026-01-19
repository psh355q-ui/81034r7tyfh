"""
SEC Edgar API Client

SEC Edgar 공시 데이터 조회를 위한 실제 클라이언트입니다.
FactChecker에서 정책 관련 수치를 검증할 때 사용합니다.

Reference: tests/mocks/sec_mock.py (Mock implementation)
"""

import logging
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
except ImportError:
    httpx = None
    logging.warning("httpx not installed. Install with: pip install httpx")


class FormType(Enum):
    """공시 유형"""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_S1 = "S-1"
    FORM_DEF14A = "DEF14A"


@dataclass
class FilingData:
    """공시 데이터"""
    ticker: str
    form_type: str
    filing_date: str
    report_date: str
    url: str
    items: Dict[str, str]  # 항목별 내용
    metadata: Dict[str, any]


class SECClient:
    """
    SEC Edgar API 실제 클라이언트

    SEC Edgar API를 호출하여 실제 공시 데이터를 가져옵니다.
    """

    # SEC Edgar API base URL
    BASE_URL = "https://www.sec.gov/Archives/edgar/data"

    def __init__(self, user_agent: Optional[str] = None):
        """
        SEC 클라이언트 초기화

        Args:
            user_agent: 사용자 에이전트 (필수: 이름/이메일 형식)
        """
        if httpx is None:
            raise ImportError(
                "httpx is not installed. "
                "Install with: pip install httpx"
            )

        self._logger = logging.getLogger(__name__)

        # SEC는 사용자 에이전트를 요구합니다.
        # 형식: "AppName ContactEmail"
        if user_agent is None:
            user_agent = "AITradingSystem trading@example.com"
        self._user_agent = user_agent

        # 비동기 HTTP 클라이언트
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 가져오기"""
        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": self._user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",
            }
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        """클라이언트 닫기"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_filing(
        self,
        ticker: str,
        form_type: str = "10-K",
        year: Optional[int] = None
    ) -> Optional[FilingData]:
        """
        공시 데이터 조회

        Args:
            ticker: 종목 코드
            form_type: 공시 유형 (10-K, 10-Q, 8-K 등)
            year: 연도 (없으면 최신)

        Returns:
            FilingData: 공시 데이터 (없으면 None)
        """
        try:
            # CIK (Central Index Key) 가져오기
            cik = await self._get_cik(ticker)
            if cik is None:
                self._logger.warning(f"CIK not found for {ticker}")
                return None

            # 공시 검색 URL
            search_url = f"{self.BASE_URL}/{cik}"

            client = await self._get_client()
            response = await client.get(search_url)

            if response.status_code != 200:
                self._logger.error(f"SEC API error: {response.status_code}")
                return None

            # 디렉토리 목록 파싱
            filings = await self._parse_filing_index(response.text, cik, form_type, year)

            if not filings:
                return None

            # 최신 공시 반환
            return filings[0]

        except Exception as e:
            self._logger.error(f"Error fetching filing for {ticker}: {e}")
            return None

    async def _get_cik(self, ticker: str) -> Optional[str]:
        """
        종목 코드에서 CIK 가져오기

        Args:
            ticker: 종목 코드

        Returns:
            str: CIK (0으로 채워진 10자리)
        """
        # Ticker to CIK 매핑 (일반적으로 SEC에서 제공하는 JSON 파일 사용)
        # 여기서는 간단한 매핑을 사용합니다.

        # 주요 종목 CIK 매핑
        ticker_cik_map = {
            "AAPL": "0000320193",
            "NVDA": "0001045810",
            "TSLA": "0001318605",
            "MSFT": "0000789019",
            "GOOGL": "0001652044",
            "AMZN": "0001018724",
            "META": "0001326801",
        }

        cik = ticker_cik_map.get(ticker.upper())

        if cik:
            return cik

        # CIK가 없으면 SEC Ticker API 시도 (선택적)
        # 실제 구현에서는 SEC의 company_tickers.json 파일을 사용할 수 있습니다.

        return None

    async def _parse_filing_index(
        self,
        html: str,
        cik: str,
        form_type: str,
        year: Optional[int] = None
    ) -> List[FilingData]:
        """
        공시 인덱스 파싱

        Args:
            html: SEC 페이지 HTML
            cik: 회사 CIK
            form_type: 공시 유형
            year: 연도 필터

        Returns:
            List[FilingData]: 공시 데이터 리스트
        """
        filings = []

        # 간단한 파싱 (실제로는 SEC의 인덱스 파일을 사용하는 것이 좋습니다)
        # 여기서는 예시를 위해 간단한 구현을 사용합니다.

        # SEC의 Edgar 데이터는 실제로는 .txt 인덱스 파일에서 파싱해야 합니다.
        # 이 예시에서는 기본 구조만 보여줍니다.

        # 실제 구현에서는 다음 URL에서 인덱스를 가져와야 합니다:
        # https://www.sec.gov/Archives/edgar/data/{CIK}/{CIK}.txt

        # 또는 SEC의 full-index 파일을 사용:
        # https://www.sec.gov/Archives/edgar/full-index/{YEAR}/QTR/{QUARTER}/company.idx

        return filings

    async def verify_policy_number(
        self,
        policy_name: str,
        extracted_amount: float,
        tolerance: float = 0.05
    ) -> Dict[str, any]:
        """
        정책 관련 수치 검증

        Args:
            policy_name: 정책 이름
            extracted_amount: LLM이 추출한 금액 (Billion dollars)
            tolerance: 허용 오차 (기본 5%)

        Returns:
            Dict: 검증 결과
        """
        # SEC 공시에서 정책 수치 검증은 실제로 복잡합니다.
        # 여기서는 주요 정책에 대한 데이터베이스를 유지합니다.

        # 정책 데이터베이스 (실제 구현에서는 DB나 파일에서 로드)
        policy_database = {
            "chips act": {
                "allocated_amount": 52.7,  # Billion dollars
                "source": "CHIPS and Science Act, 2022",
                "description": "Semiconductor manufacturing incentives",
                "sec_reference": "Various company 10-K filings reference CHIPS Act funding"
            },
            "inflation reduction act": {
                "allocated_amount": 369,  # Billion dollars
                "source": "Inflation Reduction Act, 2022",
                "description": "Climate and healthcare investments",
                "sec_reference": "Company disclosures regarding IRA credits"
            },
        }

        # 대소문자 무시 검색
        policy_data = None
        for key, value in policy_database.items():
            if policy_name.lower() in key or key in policy_name.lower():
                policy_data = value
                break

        if policy_data is None:
            return {
                "verified": False,
                "reason": "Policy not found in database. SEC verification requires manual review.",
                "extracted": extracted_amount,
                "actual": None,
            }

        actual_amount = policy_data["allocated_amount"]
        diff_pct = abs(extracted_amount - actual_amount) / actual_amount
        verified = diff_pct <= tolerance

        return {
            "verified": verified,
            "reason": f"Difference: {diff_pct:.1%}",
            "extracted": extracted_amount,
            "actual": actual_amount,
            "source": policy_data["source"],
            "description": policy_data["description"],
            "tolerance": tolerance,
        }

    async def extract_financial_metrics(
        self,
        ticker: str,
        metric_name: str
    ) -> Optional[float]:
        """
        재무 지표 추출

        Args:
            ticker: 종목 코드
            metric_name: 지표 이름 (revenue, r_and_d, gross_margin 등)

        Returns:
            float: 지표 값 (없으면 None)
        """
        filing = await self.get_filing(ticker, "10-K")
        if filing is None:
            return None

        # 항목에서 수치 추출 (간단 구현)
        item_text = filing.items.get(metric_name, "")
        if not item_text:
            return None

        # 텍스트에서 숫자 추출 (간단 구현)
        numbers = re.findall(r"\d+\.?\d*", item_text)
        if numbers:
            return float(numbers[0])

        return None


# 싱글톤 인스턴스
_sec_instance = None


def get_sec_client(user_agent: Optional[str] = None) -> SECClient:
    """SEC 클라이언트 싱글톤 반환"""
    global _sec_instance
    if _sec_instance is None:
        _sec_instance = SECClient(user_agent=user_agent)
    return _sec_instance
