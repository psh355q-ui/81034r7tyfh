"""
SEC EDGAR Real-time Monitor

SEC 공시를 실시간으로 모니터링하여 중요 이벤트를 감지합니다.

Features:
- Form 8-K: 중요 사건 (실적, CEO 사임, 회계 변경 등)
- Form 4: 내부자 거래
- Form 13D/G: 대량 지분 취득

Author: AI Trading System
Date: 2025-11-21
Phase: 14 (SEC Real-time Intelligence)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncGenerator
import aiohttp
import feedparser
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class SECFiling:
    """SEC 공시 데이터 모델"""
    
    def __init__(self, data: dict):
        self.form_type = data.get('form_type')
        self.company_name = data.get('company_name')
        self.cik = data.get('cik')
        self.ticker = data.get('ticker')
        self.filing_date = data.get('filing_date')
        self.filing_url = data.get('filing_url')
        self.description = data.get('description', '')
        
    def to_dict(self) -> dict:
        return {
            'form_type': self.form_type,
            'company_name': self.company_name,
            'cik': self.cik,
            'ticker': self.ticker,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'filing_url': self.filing_url,
            'description': self.description
        }


class SECAlert:
    """SEC 알림 데이터"""
    
    def __init__(
        self,
        alert_type: str,
        ticker: str,
        form_type: str,
        severity: str,
        reason: str,
        filing: SECFiling,
        metadata: Optional[Dict] = None
    ):
        self.alert_type = alert_type
        self.ticker = ticker
        self.form_type = form_type
        self.severity = severity  # INFO, WARNING, HIGH, CRITICAL
        self.reason = reason
        self.filing = filing
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> dict:
        return {
            'alert_type': self.alert_type,
            'ticker': self.ticker,
            'form_type': self.form_type,
            'severity': self.severity,
            'reason': self.reason,
            'filing': self.filing.to_dict(),
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# SEC EDGAR Monitor
# ============================================================================

class SECRealtimeMonitor:
    """SEC EDGAR 실시간 모니터"""
    
    # SEC EDGAR RSS Feed URLs
    EDGAR_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=exclude&start=0&count=100&output=atom"
    
    # 모니터링할 Form 타입
    CRITICAL_FORMS = [
        "8-K",      # Current Report (중요 사건)
        "4",        # Statement of Changes in Beneficial Ownership (내부자 거래)
        "13D",      # Schedule 13D (5% 이상 지분 취득, 적대적)
        "13G",      # Schedule 13G (5% 이상 지분 취득, 우호적)
        "SC 13D",   # Schedule 13D (변형)
        "SC 13G",   # Schedule 13G (변형)
    ]
    
    # 8-K 중요 이벤트 키워드
    RED_FLAG_KEYWORDS = [
        # 회계 관련
        "restatement", "restate", "revision", "accounting change",
        "material weakness", "internal control",
        
        # 경영진 변동
        "resignation", "termination", "departure", "dismissed",
        "ceo", "cfo", "chief financial officer",
        
        # 법적 이슈
        "investigation", "lawsuit", "litigation", "sec inquiry",
        "subpoena", "regulatory",
        
        # 재무 문제
        "default", "bankruptcy", "delisting", "going concern",
        "covenant breach", "loan default"
    ]
    
    def __init__(self, watchlist: List[str]):
        """
        Args:
            watchlist: 모니터링할 티커 리스트 (예: ['NVDA', 'TSLA', 'AAPL'])
        """
        self.watchlist = [ticker.upper() for ticker in watchlist]
        self.session: Optional[aiohttp.ClientSession] = None
        self.seen_filings: set = set()  # 중복 방지
        
        # CIK to Ticker 매핑 (실제로는 DB에서 로드)
        self.cik_to_ticker = self._load_cik_mapping()
        
    def _load_cik_mapping(self) -> Dict[str, str]:
        """CIK to Ticker 매핑 로드"""
        # 실제로는 SEC Company Tickers JSON 사용
        # https://www.sec.gov/files/company_tickers.json
        
        # 임시 샘플 데이터
        return {
            "0001045810": "NVDA",  # Nvidia
            "0001318605": "TSLA",  # Tesla
            "0000320193": "AAPL",  # Apple
            "0001652044": "GOOGL", # Alphabet
            "0001018724": "AMZN",  # Amazon
            "0000789019": "MSFT",  # Microsoft
            "0001326801": "META",  # Meta
        }
    
    async def start(self):
        """모니터링 시작"""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "AI Trading System contact@example.com"
            }
        )
        logger.info(f"SEC Monitor started. Watching {len(self.watchlist)} tickers.")
        
    async def stop(self):
        """모니터링 종료"""
        if self.session:
            await self.session.close()
        logger.info("SEC Monitor stopped.")
    
    async def fetch_recent_filings(self) -> List[SECFiling]:
        """최근 공시 가져오기"""
        try:
            async with self.session.get(self.EDGAR_RSS_URL, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch SEC RSS: {response.status}")
                    return []
                
                content = await response.text()
                
            # RSS 파싱
            feed = feedparser.parse(content)
            
            filings = []
            for entry in feed.entries:
                filing = self._parse_rss_entry(entry)
                
                if filing and filing.ticker in self.watchlist:
                    # 중복 체크
                    filing_id = f"{filing.ticker}_{filing.form_type}_{filing.filing_date}"
                    
                    if filing_id not in self.seen_filings:
                        self.seen_filings.add(filing_id)
                        filings.append(filing)
            
            if filings:
                logger.info(f"Found {len(filings)} new filings for watchlist tickers")
            
            return filings
            
        except Exception as e:
            logger.error(f"Error fetching SEC filings: {e}")
            return []
    
    def _parse_rss_entry(self, entry) -> Optional[SECFiling]:
        """RSS 엔트리를 SECFiling으로 변환"""
        try:
            # Title format: "4 - NVIDIA CORP (0001045810) (Issuer)"
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            
            # Form type 추출
            form_match = re.match(r'^([\w-]+)\s+-\s+', title)
            if not form_match:
                return None
            
            form_type = form_match.group(1).strip()
            
            # 관심 있는 Form만 처리
            if form_type not in self.CRITICAL_FORMS:
                return None
            
            # CIK 추출
            cik_match = re.search(r'\((\d{10})\)', title)
            if not cik_match:
                return None
            
            cik = cik_match.group(1)
            ticker = self.cik_to_ticker.get(cik)
            
            if not ticker:
                return None  # watchlist에 없는 종목
            
            # 회사명 추출
            company_match = re.search(r'-\s+(.+?)\s+\(\d{10}\)', title)
            company_name = company_match.group(1).strip() if company_match else "Unknown"
            
            # URL
            filing_url = entry.get('link', '')
            
            # 날짜
            published = entry.get('published_parsed')
            filing_date = datetime(*published[:6]) if published else datetime.now()
            
            return SECFiling({
                'form_type': form_type,
                'company_name': company_name,
                'cik': cik,
                'ticker': ticker,
                'filing_date': filing_date,
                'filing_url': filing_url,
                'description': summary
            })
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    async def analyze_filing(self, filing: SECFiling) -> Optional[SECAlert]:
        """공시 내용 분석하여 알림 생성"""
        
        if filing.form_type == "8-K":
            return await self._analyze_8k(filing)
        
        elif filing.form_type == "4":
            return await self._analyze_form4(filing)
        
        elif filing.form_type in ["13D", "13G", "SC 13D", "SC 13G"]:
            return await self._analyze_13d(filing)
        
        return None
    
    async def _analyze_8k(self, filing: SECFiling) -> Optional[SECAlert]:
        """Form 8-K 분석"""
        try:
            # 8-K 전문 다운로드
            async with self.session.get(filing.filing_url, timeout=30) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
            
            # HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text().lower()
            
            # Red Flag 키워드 검색
            detected_flags = []
            for keyword in self.RED_FLAG_KEYWORDS:
                if keyword in text_content:
                    detected_flags.append(keyword)
            
            if not detected_flags:
                # Red Flag 없으면 일반 정보성 알림
                return SECAlert(
                    alert_type="8K_FILED",
                    ticker=filing.ticker,
                    form_type="8-K",
                    severity="INFO",
                    reason="New 8-K filing detected",
                    filing=filing
                )
            
            # Red Flag 발견 시 심각도 판단
            critical_keywords = ["restatement", "bankruptcy", "cfo", "ceo resignation"]
            is_critical = any(kw in detected_flags for kw in critical_keywords)
            
            severity = "CRITICAL" if is_critical else "HIGH"
            
            return SECAlert(
                alert_type="8K_RED_FLAG",
                ticker=filing.ticker,
                form_type="8-K",
                severity=severity,
                reason=f"Red flags detected: {', '.join(detected_flags[:3])}",
                filing=filing,
                metadata={
                    "red_flags": detected_flags,
                    "red_flag_count": len(detected_flags)
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing 8-K for {filing.ticker}: {e}")
            return None
    
    async def _analyze_form4(self, filing: SECFiling) -> Optional[SECAlert]:
        """Form 4 (내부자 거래) 분석"""
        # Day 4에 구현 예정
        logger.info(f"Form 4 analysis for {filing.ticker} (to be implemented)")
        return None
    
    async def _analyze_13d(self, filing: SECFiling) -> Optional[SECAlert]:
        """Form 13D/G (대량 지분 취득) 분석"""
        # 5% 이상 지분 취득은 항상 중요
        return SECAlert(
            alert_type="LARGE_STAKE_ACQUISITION",
            ticker=filing.ticker,
            form_type=filing.form_type,
            severity="HIGH",
            reason="Large shareholder (>5%) filing detected",
            filing=filing
        )
    
    async def monitor_loop(self, interval: int = 60) -> AsyncGenerator[SECAlert, None]:
        """
        메인 모니터링 루프
        
        Args:
            interval: 체크 주기 (초)
            
        Yields:
            SECAlert: 감지된 알림
        """
        logger.info(f"Starting SEC monitor loop (interval: {interval}s)")
        
        while True:
            try:
                # 최근 공시 가져오기
                filings = await self.fetch_recent_filings()
                
                # 각 공시 분석
                for filing in filings:
                    alert = await self.analyze_filing(filing)
                    
                    if alert:
                        logger.info(
                            f"SEC Alert: {alert.ticker} - {alert.form_type} "
                            f"({alert.severity}): {alert.reason}"
                        )
                        yield alert
                
                # 대기
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in SEC monitor loop: {e}")
                await asyncio.sleep(interval)


# ============================================================================
# Helper Functions
# ============================================================================

async def load_company_tickers() -> Dict[str, str]:
    """
    SEC에서 제공하는 Company Tickers JSON 다운로드
    
    Returns:
        CIK to Ticker 매핑
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # CIK를 10자리 문자열로 변환
                    cik_mapping = {}
                    for entry in data.values():
                        cik = str(entry['cik_str']).zfill(10)
                        ticker = entry['ticker'].upper()
                        cik_mapping[cik] = ticker
                    
                    logger.info(f"Loaded {len(cik_mapping)} company tickers from SEC")
                    return cik_mapping
                    
        except Exception as e:
            logger.error(f"Error loading company tickers: {e}")
    
    return {}


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """테스트 실행"""
    
    # Watchlist 설정
    watchlist = ["NVDA", "TSLA", "AAPL", "GOOGL", "MSFT"]
    
    # 모니터 생성
    monitor = SECRealtimeMonitor(watchlist)
    
    try:
        await monitor.start()
        
        # 모니터링 시작 (5분마다 체크)
        async for alert in monitor.monitor_loop(interval=300):
            print("\n" + "="*60)
            print(f"🚨 SEC Alert: {alert.severity}")
            print(f"Ticker: {alert.ticker}")
            print(f"Form: {alert.form_type}")
            print(f"Reason: {alert.reason}")
            print(f"URL: {alert.filing.filing_url}")
            print("="*60)
            
            # 실제로는 여기서 Telegram/Slack 알림 전송
            
    finally:
        await monitor.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
