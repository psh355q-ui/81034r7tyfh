"""
SEC EDGAR API 클라이언트

공식 API: https://www.sec.gov/edgar/sec-api-documentation
Rate Limit: 10 requests/second (User-Agent 필수)

Author: AI Trading System
Date: 2025-11-22
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path
import logging

from backend.core.models.sec_models import (
    FilingType,
    FilingMetadata,
    SECCompanyInfo,
    SECSubmission,
    SECError,
    SECRateLimitError,
    SECFilingNotFoundError
)

logger = logging.getLogger(__name__)


class SECClient:
    """
    SEC EDGAR API 클라이언트
    
    Features:
    - CIK 조회 (ticker → CIK 변환)
    - 최신 공시 문서 조회
    - 공시 문서 다운로드
    - Rate limiting (10 req/sec)
    """
    
    BASE_URL = "https://data.sec.gov"
    EDGAR_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    # SEC 요구사항: User-Agent에 이메일 포함 필수
    USER_AGENT = "AI Trading System admin@example.com"
    
    def __init__(
        self,
        user_email: str = "admin@example.com",
        cache_dir: Optional[Path] = None
    ):
        """
        Args:
            user_email: SEC API 접근용 이메일 (User-Agent에 포함)
            cache_dir: 다운로드한 문서 캐시 디렉토리
        """
        self.user_agent = f"AI Trading System {user_email}"
        self.cache_dir = cache_dir or Path("data/sec_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self._last_request_time = 0.0
        self._min_interval = 0.1  # 10 req/sec = 0.1초 간격
        
        # CIK 캐시 (ticker → CIK)
        self._cik_cache: Dict[str, str] = {}
        
        logger.info(f"SEC Client initialized (User-Agent: {self.user_agent})")
    
    async def _rate_limit(self):
        """Rate limiting (10 req/sec)"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def _get(self, url: str, **kwargs) -> Dict:
        """
        HTTP GET 요청 (Rate limiting 적용)
        
        Raises:
            SECRateLimitError: Rate limit 초과
            SECError: 기타 API 에러
        """
        await self._rate_limit()
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, **kwargs) as response:
                    if response.status == 429:
                        raise SECRateLimitError("SEC API rate limit exceeded")
                    
                    if response.status == 404:
                        raise SECFilingNotFoundError(f"Resource not found: {url}")
                    
                    response.raise_for_status()
                    
                    # JSON 응답
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        return await response.json()
                    
                    # HTML/텍스트 응답
                    return {"text": await response.text()}
                    
            except aiohttp.ClientError as e:
                raise SECError(f"SEC API request failed: {e}")
    
    async def get_cik(self, ticker: str) -> str:
        """
        Ticker → CIK 변환
        
        Args:
            ticker: 주식 티커 (예: AAPL, MSFT)
            
        Returns:
            CIK (10자리, 0-padded)
            
        Example:
            >>> cik = await client.get_cik("AAPL")
            >>> print(cik)  # "0000320193"
        """
        ticker = ticker.upper().strip()
        
        # 캐시 확인
        if ticker in self._cik_cache:
            return self._cik_cache[ticker]
        
        # SEC company tickers JSON
        url = f"{self.BASE_URL}/files/company_tickers.json"
        
        try:
            data = await self._get(url)
            
            # 티커 검색
            for entry in data.values():
                if entry.get('ticker', '').upper() == ticker:
                    cik = str(entry['cik_str']).zfill(10)
                    self._cik_cache[ticker] = cik
                    logger.info(f"Found CIK for {ticker}: {cik}")
                    return cik
            
            raise SECFilingNotFoundError(f"CIK not found for ticker: {ticker}")
            
        except SECError:
            raise
        except Exception as e:
            raise SECError(f"Failed to get CIK for {ticker}: {e}")
    
    async def get_company_info(self, ticker: str) -> SECCompanyInfo:
        """
        기업 정보 조회
        
        Args:
            ticker: 주식 티커
            
        Returns:
            SECCompanyInfo
        """
        cik = await self.get_cik(ticker)
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        
        try:
            data = await self._get(url)
            
            return SECCompanyInfo(
                cik=cik,
                ticker=ticker,
                company_name=data.get('name', ''),
                sic_code=data.get('sic', ''),
                sic_description=data.get('sicDescription', ''),
                state_of_incorporation=data.get('stateOfIncorporation', ''),
                fiscal_year_end=data.get('fiscalYearEnd', '')
            )
            
        except SECError:
            raise
        except Exception as e:
            raise SECError(f"Failed to get company info for {ticker}: {e}")
    
    async def get_recent_filings(
        self,
        ticker: str,
        filing_type: FilingType,
        count: int = 5
    ) -> List[FilingMetadata]:
        """
        최근 공시 문서 목록 조회
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형 (10-K, 10-Q 등)
            count: 가져올 개수
            
        Returns:
            List[FilingMetadata]
        """
        cik = await self.get_cik(ticker)
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        
        try:
            data = await self._get(url)
            recent = data.get('filings', {}).get('recent', {})
            
            results = []
            forms = recent.get('form', [])
            dates = recent.get('filingDate', [])
            accessions = recent.get('accessionNumber', [])
            
            for i in range(len(forms)):
                if forms[i] == filing_type.value and len(results) < count:
                    # Accession number에서 하이픈 제거
                    acc_no = accessions[i].replace('-', '')
                    
                    # 문서 URL 생성
                    doc_url = (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik}/{acc_no}/{accessions[i]}.txt"
                    )
                    
                    filing = FilingMetadata(
                        ticker=ticker,
                        cik=cik,
                        company_name=data.get('name', ''),
                        filing_type=filing_type,
                        filing_date=datetime.strptime(dates[i], '%Y-%m-%d'),
                        fiscal_period=self._extract_fiscal_period(
                            filing_type, dates[i]
                        ),
                        accession_number=accessions[i],
                        filing_url=f"https://www.sec.gov/cgi-bin/browse-edgar?"
                                  f"action=getcompany&CIK={cik}&type={filing_type.value}",
                        document_url=doc_url
                    )
                    results.append(filing)
            
            logger.info(f"Found {len(results)} {filing_type.value} filings for {ticker}")
            return results
            
        except SECError:
            raise
        except Exception as e:
            raise SECError(f"Failed to get recent filings for {ticker}: {e}")
    
    async def get_latest_filing(
        self,
        ticker: str,
        filing_type: FilingType
    ) -> Optional[FilingMetadata]:
        """
        최신 공시 문서 1개 조회
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형
            
        Returns:
            FilingMetadata 또는 None
        """
        filings = await self.get_recent_filings(ticker, filing_type, count=1)
        return filings[0] if filings else None
    
    async def download_filing(
        self,
        filing: FilingMetadata,
        force_refresh: bool = False
    ) -> str:
        """
        공시 문서 다운로드
        
        Args:
            filing: 공시 메타데이터
            force_refresh: 캐시 무시하고 새로 다운로드
            
        Returns:
            문서 내용 (텍스트)
        """
        # 캐시 파일 경로
        cache_file = (
            self.cache_dir / 
            f"{filing.ticker}_{filing.filing_type.value}_{filing.fiscal_period}.txt"
        )
        
        # 캐시 확인
        if not force_refresh and cache_file.exists():
            logger.info(f"Loading from cache: {cache_file}")
            return cache_file.read_text(encoding='utf-8')
        
        # SEC에서 다운로드
        try:
            result = await self._get(filing.document_url)
            content = result.get('text', '')
            
            # 캐시 저장
            cache_file.write_text(content, encoding='utf-8')
            logger.info(f"Downloaded and cached: {filing.ticker} {filing.filing_type.value}")
            
            return content
            
        except SECError:
            raise
        except Exception as e:
            raise SECError(f"Failed to download filing: {e}")
    
    def _extract_fiscal_period(
        self,
        filing_type: FilingType,
        filing_date_str: str
    ) -> str:
        """
        공시 날짜로부터 회계 기간 추출
        
        Args:
            filing_type: 공시 유형
            filing_date_str: 공시 날짜 (YYYY-MM-DD)
            
        Returns:
            회계 기간 (예: "FY2024", "Q3 2024")
        """
        date = datetime.strptime(filing_date_str, '%Y-%m-%d')
        year = date.year
        
        if filing_type == FilingType.FORM_10K:
            # 10-K는 보통 회계연도 종료 후 60-90일 내 제출
            # 제출 연도의 전년도를 회계연도로 간주
            return f"FY{year - 1}"
        
        elif filing_type == FilingType.FORM_10Q:
            # 10-Q는 분기 종료 후 40-45일 내 제출
            # 월로부터 분기 추정
            month = date.month
            
            if month <= 5:  # Q1 (1-3월) → 4-5월 제출
                quarter = "Q1"
            elif month <= 8:  # Q2 (4-6월) → 7-8월 제출
                quarter = "Q2"
            elif month <= 11:  # Q3 (7-9월) → 10-11월 제출
                quarter = "Q3"
            else:
                quarter = "Q4"
                year -= 1  # Q4는 다음 해 초에 제출되므로
            
            return f"{quarter} {year}"
        
        return f"{year}"
    
    async def search_filings(
        self,
        ticker: str,
        filing_type: FilingType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FilingMetadata]:
        """
        기간별 공시 문서 검색
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            List[FilingMetadata]
        """
        all_filings = await self.get_recent_filings(ticker, filing_type, count=100)
        
        if not start_date and not end_date:
            return all_filings
        
        filtered = []
        for filing in all_filings:
            if start_date and filing.filing_date < start_date:
                continue
            if end_date and filing.filing_date > end_date:
                continue
            filtered.append(filing)
        
        return filtered


# ============================================
# 유틸리티 함수
# ============================================

async def get_latest_10k(ticker: str) -> Optional[FilingMetadata]:
    """최신 10-K 문서 조회 (편의 함수)"""
    client = SECClient()
    return await client.get_latest_filing(ticker, FilingType.FORM_10K)


async def get_latest_10q(ticker: str) -> Optional[FilingMetadata]:
    """최신 10-Q 문서 조회 (편의 함수)"""
    client = SECClient()
    return await client.get_latest_filing(ticker, FilingType.FORM_10Q)


# ============================================
# 테스트/데모
# ============================================

async def demo():
    """SEC Client 데모"""
    client = SECClient()
    
    # 1. CIK 조회
    print("=== CIK Lookup ===")
    cik = await client.get_cik("AAPL")
    print(f"AAPL CIK: {cik}")
    
    # 2. 기업 정보
    print("\n=== Company Info ===")
    info = await client.get_company_info("AAPL")
    print(f"Company: {info.company_name}")
    print(f"SIC: {info.sic_description}")
    
    # 3. 최신 10-K
    print("\n=== Latest 10-K ===")
    filing_10k = await client.get_latest_filing("AAPL", FilingType.FORM_10K)
    if filing_10k:
        print(f"Period: {filing_10k.fiscal_period}")
        print(f"Filed: {filing_10k.filing_date}")
        print(f"URL: {filing_10k.document_url}")
    
    # 4. 최신 10-Q
    print("\n=== Latest 10-Q ===")
    filing_10q = await client.get_latest_filing("AAPL", FilingType.FORM_10Q)
    if filing_10q:
        print(f"Period: {filing_10q.fiscal_period}")
        print(f"Filed: {filing_10q.filing_date}")
    
    # 5. 문서 다운로드 (샘플만 - 전체 다운로드는 크기가 큼)
    print("\n=== Download Sample ===")
    if filing_10k:
        content = await client.download_filing(filing_10k)
        print(f"Downloaded: {len(content):,} characters")
        print(f"Preview:\n{content[:500]}...")


if __name__ == "__main__":
    asyncio.run(demo())
