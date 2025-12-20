"""
Yahoo Finance API Client

실시간 ETF 데이터를 Yahoo Finance에서 가져오는 클라이언트

기능:
- ETF 가격 및 거래량 조회
- 여러 ETF 동시 조회
- 캐싱 지원

작성일: 2025-12-15
"""

import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """
    Yahoo Finance API 클라이언트
    
    yfinance 라이브러리를 사용하여 ETF 데이터를 가져옵니다.
    
    Usage:
        client = YahooFinanceClient()
        
        # 단일 ETF
        data = client.get_etf_data("QQQ", period="5d")
        print(data['volume'])  # [50000000, 48000000, ...]
        
        # 여러 ETF
        data = client.get_multiple_etfs(["QQQ", "SPY", "XLF"])
    """
    
    def __init__(self):
        logger.info("YahooFinanceClient initialized")
    
    def get_etf_data(
        self,
        ticker: str,
        period: str = "5d"
    ) -> Optional[Dict]:
        """
        ETF 데이터 가져오기
        
        Args:
            ticker: ETF 티커 (예: QQQ, SPY)
            period: 기간 (1d, 5d, 1mo, 3mo, 1y 등)
            
        Returns:
            {
                'ticker': str,
                'volume': List[float],
                'price': List[float],
                'dates': List[datetime],
                'aum': float  # Assets Under Management (추정)
            }
        """
        try:
            logger.info(f"Fetching data for {ticker} (period={period})")
            
            # yfinance Ticker 객체
            ticker_obj = yf.Ticker(ticker)
            
            # 과거 데이터
            hist = ticker_obj.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data found for {ticker}")
                return None
            
            # 정보 가져오기
            info = ticker_obj.info
            
            # AUM 계산 (시가총액 기반 추정)
            market_cap = info.get('totalAssets', 0)
            if market_cap == 0:
                # 대체: 가격 × 발행 주식 수
                market_cap = info.get('marketCap', 0)
            
            result = {
                'ticker': ticker,
                'volume': hist['Volume'].tolist(),
                'price': hist['Close'].tolist(),
                'dates': [d.to_pydatetime() for d in hist.index],
                'aum': float(market_cap) if market_cap else 0.0
            }
            
            logger.info(
                f"Retrieved {len(result['volume'])} data points for {ticker}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def get_multiple_etfs(
        self,
        tickers: List[str],
        period: str = "5d"
    ) -> Dict[str, Dict]:
        """
        여러 ETF 동시 조회
        
        Args:
            tickers: ETF 티커 리스트
            period: 기간
            
        Returns:
            {
                'QQQ': {...},
                'SPY': {...},
                ...
            }
        """
        logger.info(f"Fetching data for {len(tickers)} ETFs")
        
        result = {}
        
        for ticker in tickers:
            data = self.get_etf_data(ticker, period)
            if data:
                result[ticker] = data
        
        logger.info(f"Successfully fetched {len(result)}/{len(tickers)} ETFs")
        
        return result
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        현재가 조회 (실시간)
        
        Args:
            ticker: ETF 티커
            
        Returns:
            현재가 (float)
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # 실시간 데이터
            data = ticker_obj.history(period="1d", interval="1m")
            
            if data.empty:
                return None
            
            current_price = float(data['Close'].iloc[-1])
            
            logger.info(f"{ticker} current price: ${current_price:.2f}")
            
            return current_price
            
        except Exception as e:
            logger.error(f"Failed to get current price for {ticker}: {e}")
            return None
    
    def get_info(self, ticker: str) -> Dict:
        """
        ETF 상세 정보
        
        Args:
            ticker: ETF 티커
            
        Returns:
            ETF 정보 딕셔너리
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            return {
                'name': info.get('longName', ticker),
                'category': info.get('category', 'Unknown'),
                'total_assets': info.get('totalAssets', 0),
                'ytd_return': info.get('ytdReturn', 0.0),
                'expense_ratio': info.get('annualReportExpenseRatio', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get info for {ticker}: {e}")
            return {}


# 전역 인스턴스
_yahoo_client = None


def get_yahoo_client() -> YahooFinanceClient:
    """전역 YahooFinanceClient 인스턴스 반환"""
    global _yahoo_client
    if _yahoo_client is None:
        _yahoo_client = YahooFinanceClient()
    return _yahoo_client


# 테스트
if __name__ == "__main__":
    import asyncio
    
    print("=== Yahoo Finance Client Test ===\n")
    
    client = YahooFinanceClient()
    
    # Test 1: 단일 ETF
    print("Test 1: Single ETF (QQQ)")
    data = client.get_etf_data("QQQ", period="5d")
    
    if data:
        print(f"Ticker: {data['ticker']}")
        print(f"Data points: {len(data['volume'])}")
        print(f"Latest price: ${data['price'][-1]:.2f}")
        print(f"Latest volume: {data['volume'][-1]:,.0f}")
        print(f"AUM: ${data['aum']:,.0f}")
    
    # Test 2: 여러 ETF
    print("\n\nTest 2: Multiple ETFs")
    tickers = ["QQQ", "SPY", "XLF"]
    multi_data = client.get_multiple_etfs(tickers)
    
    print(f"Fetched {len(multi_data)} ETFs:")
    for ticker, data in multi_data.items():
        print(f"  {ticker}: ${data['price'][-1]:.2f}")
    
    # Test 3: 현재가
    print("\n\nTest 3: Current Price")
    current = client.get_current_price("QQQ")
    if current:
        print(f"QQQ current price: ${current:.2f}")
    
    print("\n✅ Yahoo Finance Client test completed!")
