"""
SEC Edgar API Mock

SEC Edgar 공시 데이터 조회를 위한 Mock 클래스입니다.
FactChecker에서 정책 관련 수치를 검증할 때 사용합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


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


class MockSECClient:
    """
    SEC Edgar API Mock 클래스

    실제 SEC API를 호출하지 않고 테스트용 데이터를 반환합니다.
    """

    def __init__(self):
        """Mock 초기화"""
        # 테스트용 공시 데이터
        self._filings = {
            "NVDA": [
                FilingData(
                    ticker="NVDA",
                    form_type="10-K",
                    filing_date="2025-02-26",
                    report_date="2025-01-26",
                    url="https://www.sec.gov/Archives/edgar/data/1045810/000104581025000006/nvda-20250126.htm",
                    items={
                        "revenue": "Annual revenue: $60.9 billion",
                        "r_and_d": "R&D expenses: $10.4 billion",
                        "gross_margin": "Gross margin: 73.8%",
                    },
                    metadata={"fiscal_year": "2025"}
                ),
            ],
            "AAPL": [
                FilingData(
                    ticker="AAPL",
                    form_type="10-K",
                    filing_date="2024-11-01",
                    report_date="2024-09-28",
                    url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
                    items={
                        "revenue": "Annual revenue: $383.3 billion",
                        "r_and_d": "R&D expenses: $31.4 billion",
                        "gross_margin": "Gross margin: 45.9%",
                    },
                    metadata={"fiscal_year": "2024"}
                ),
            ],
        }

        # 정책 관련 키워드 매핑
        self._policy_keywords = {
            "CHIPS Act": {
                "allocated_amount": 52.7,  # Billion dollars
                "source": "CHIPS and Science Act, 2022",
                "description": "Semiconductor manufacturing incentives"
            },
            "Inflation Reduction Act": {
                "allocated_amount": 369,  # Billion dollars
                "source": "Inflation Reduction Act, 2022",
                "description": "Climate and healthcare investments"
            },
        }

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
        filings = self._filings.get(ticker.upper(), [])
        for filing in filings:
            if filing.form_type == form_type:
                if year is None:
                    return filing
                filing_year = int(filing.report_date[:4])
                if filing_year == year:
                    return filing
        return None

    async def search_filings(
        self,
        ticker: str,
        form_type: Optional[str] = None,
        count: int = 10
    ) -> List[FilingData]:
        """
        공시 검색

        Args:
            ticker: 종목 코드
            form_type: 공시 유형 필터
            count: 최대 개수

        Returns:
            List[FilingData]: 공시 데이터 리스트
        """
        filings = self._filings.get(ticker.upper(), [])
        if form_type:
            filings = [f for f in filings if f.form_type == form_type]
        return filings[:count]

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
        # 대소문자 무시 검색
        policy_data = None
        for key, value in self._policy_keywords.items():
            if policy_name.lower() in key.lower() or key.lower() in policy_name.lower():
                policy_data = value
                break

        if policy_data is None:
            return {
                "verified": False,
                "reason": "Policy not found in database",
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
        import re
        numbers = re.findall(r"\d+\.?\d*", item_text)
        if numbers:
            return float(numbers[0])

        return None


# 싱글톤 인스턴스
_mock_sec_instance = None


def get_mock_sec_client() -> MockSECClient:
    """Mock SEC 클라이언트 싱글톤 반환"""
    global _mock_sec_instance
    if _mock_sec_instance is None:
        _mock_sec_instance = MockSECClient()
    return _mock_sec_instance


# 테스트 헬퍼 함수
async def verify_policy_from_mock(
    policy_name: str,
    extracted_amount: float,
    tolerance: float = 0.05
) -> Dict[str, any]:
    """
    Mock 데이터로 정책 수치 검증

    Args:
        policy_name: 정책 이름
        extracted_amount: LLM이 추출한 금액
        tolerance: 허용 오차

    Returns:
        Dict: 검증 결과
    """
    client = get_mock_sec_client()
    return await client.verify_policy_number(policy_name, extracted_amount, tolerance)
