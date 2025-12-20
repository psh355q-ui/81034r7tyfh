"""
Universe Module
S&P 500 및 NASDAQ 100 종목 리스트 관리
"""

from enum import Enum
from typing import List, Set
import aiohttp
import pandas as pd
from functools import lru_cache


class UniverseType(Enum):
    SP500 = "sp500"
    NASDAQ100 = "nasdaq100"
    COMBINED = "combined"


# 하드코딩된 주요 종목 (백업용)
_MAJOR_TICKERS = [
    # 기술
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC", "CRM",
    "ORCL", "ADBE", "CSCO", "AVGO", "QCOM", "TXN", "NOW", "IBM", "INTU", "AMAT",
    # 금융
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB",
    # 헬스케어
    "UNH", "JNJ", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "BMY", "AMGN",
    # 소비재
    "WMT", "HD", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "TGT",
    # 에너지
    "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "OXY", "PSX",
    # 산업재
    "CAT", "BA", "HON", "UPS", "RTX", "GE", "LMT", "DE", "MMM", "UNP",
    # 통신
    "VZ", "T", "TMUS", "CMCSA", "DIS", "NFLX", "CHTR", "WBD", "PARA", "FOX",
    # 반도체 (AI 관련)
    "NVDA", "AMD", "AVGO", "QCOM", "TXN", "MU", "LRCX", "AMAT", "KLAC", "MRVL",
]


async def fetch_sp500_tickers() -> List[str]:
    """위키피디아에서 S&P 500 종목 목록 가져오기"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_df = tables[0]
        return sp500_df['Symbol'].str.replace('.', '-', regex=False).tolist()
    except Exception as e:
        print(f"S&P 500 목록 가져오기 실패: {e}")
        return []


async def fetch_nasdaq100_tickers() -> List[str]:
    """위키피디아에서 NASDAQ 100 종목 목록 가져오기"""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        # NASDAQ 100 테이블 찾기
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                return table[col].str.replace('.', '-', regex=False).tolist()
        return []
    except Exception as e:
        print(f"NASDAQ 100 목록 가져오기 실패: {e}")
        return []


def get_universe(universe_type: UniverseType = UniverseType.COMBINED) -> List[str]:
    """
    종목 유니버스 반환 (동기 버전, 캐시된 목록 사용)
    
    실제 사용 시에는 fetch_* 함수를 사용하여 최신 목록을 가져옴
    """
    # 중복 제거 후 반환
    return list(set(_MAJOR_TICKERS))


async def get_universe_async(universe_type: UniverseType = UniverseType.COMBINED) -> List[str]:
    """
    종목 유니버스 반환 (비동기 버전)
    
    Args:
        universe_type: 유니버스 타입 (SP500, NASDAQ100, COMBINED)
        
    Returns:
        종목 티커 리스트
    """
    tickers: Set[str] = set()
    
    if universe_type in [UniverseType.SP500, UniverseType.COMBINED]:
        sp500 = await fetch_sp500_tickers()
        tickers.update(sp500)
    
    if universe_type in [UniverseType.NASDAQ100, UniverseType.COMBINED]:
        nasdaq100 = await fetch_nasdaq100_tickers()
        tickers.update(nasdaq100)
    
    # 백업: 빈 결과면 하드코딩된 목록 사용
    if not tickers:
        tickers = set(_MAJOR_TICKERS)
    
    return list(tickers)


# 섹터 매핑
SECTOR_MAP = {
    # 기술
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "AMZN": "Consumer Discretionary", "NVDA": "Technology", "META": "Technology",
    "TSLA": "Consumer Discretionary", "AMD": "Technology", "INTC": "Technology",
    # AI 반도체
    "AVGO": "Semiconductors", "QCOM": "Semiconductors", "TXN": "Semiconductors",
    "MU": "Semiconductors", "LRCX": "Semiconductors", "AMAT": "Semiconductors",
    # 금융
    "JPM": "Financials", "BAC": "Financials", "WFC": "Financials", "GS": "Financials",
    # 헬스케어
    "UNH": "Healthcare", "JNJ": "Healthcare", "PFE": "Healthcare",
    # 에너지
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
}


def get_sector(ticker: str) -> str:
    """종목의 섹터 반환"""
    return SECTOR_MAP.get(ticker, "Unknown")
