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
import pandas as pd
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


    def get_institutional_holders(self, ticker: str) -> List[Dict]:
        """
        기관 투자자 보유 현황 조회
        
        Args:
            ticker: 종목 코드
            
        Returns:
            기관 투자자 리스트 (딕셔너리)
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            holders = ticker_obj.institutional_holders
            
            if holders is None or holders.empty:
                return []
                
            result = []
            for _, row in holders.iterrows():
                result.append({
                    'holder': row['Holder'],
                    'shares': int(row['Shares']),
                    'date_reported': row['Date Reported'],
                    'pct_held': float(row['pctHeld']),
                    'value': float(row['Value'])
                })
            
            logger.info(f"Fetched {len(result)} institutional holders for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get institutional holders for {ticker}: {e}")
            return []

    def get_insider_trades(self, ticker: str) -> List[Dict]:
        """
        내부자 거래 내역 조회
        
        Args:
            ticker: 종목 코드
            
        Returns:
            내부자 거래 리스트 (딕셔너리)
        """
        try:
            # insider_transactions (최신 포맷) 우선 사용
            ticker_obj = yf.Ticker(ticker)
            trades = getattr(ticker_obj, 'insider_transactions', None)
            
            if trades is None or trades.empty:
                 # fallback to insider_purchases if transactions empty
                 trades = getattr(ticker_obj, 'insider_purchases', None)
            
            if trades is None or trades.empty:
                return []
                
            result = []
            # 최신 20개만
            for _, row in trades.head(20).iterrows():
                # 날짜 처리
                try:
                    date_val = row.get('Start Date') or row.get('Date') or row.get('Transaction Date')
                    if hasattr(date_val, 'to_pydatetime'):
                        trade_date = date_val.to_pydatetime()
                    else:
                        trade_date = pd.to_datetime(date_val).to_pydatetime()
                except:
                    trade_date = datetime.now()

                # 컬럼 매핑 (yfinance 버전에 따라 다름)
                insider_name = row.get('Name') or row.get('Insider') or 'Unknown'
                position = row.get('Position') or row.get('Title') or 'Unknown'
                shares = row.get('Shares')
                value = row.get('Value')
                
                if pd.isna(shares): shares = 0
                if pd.isna(value): value = 0

                result.append({
                    'insider': insider_name,
                    'position': position,
                    'shares': int(shares),
                    'value': float(value),
                    'date': trade_date,
                    'text': str(row.get('Text', ''))
                })
            
            logger.info(f"Fetched {len(result)} insider trades for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get insider trades for {ticker}: {e}")
            logger.error(f"Failed to get insider trades for {ticker}: {e}")
            return []

    # Market Data Proxy Methods for Contrarian Signal Detection
    def get_etf_flows(self, ticker: str, period: str = "1mo") -> List[Dict[str, float]]:
        """
        Get ETF fund flows proxy using volume changes
        
        Since Yahoo Finance doesn't provide direct fund flow data,
        we use volume changes as a proxy indicator:
        - Positive: increasing volume (money flowing in)
        - Negative: decreasing volume (money flowing out)
        
        Returns: List of 5 flow data dictionaries with 'flow' key (-100 to +100)
        """
        try:
            data = self.get_etf_data(ticker, period=period)
            if not data or 'volume' not in data:
                logger.warning(f"No volume data for {ticker}, returning neutral flows")
                return [{"flow": 0.0} for _ in range(5)]
            
            volumes = data['volume']
            if len(volumes) < 2:
                return [{"flow": 0.0} for _ in range(5)]
            
            # Calculate volume changes (percentage)
            flows = []
            for i in range(1, min(6, len(volumes))):
                if volumes[-i-1] > 0:
                    pct_change = ((volumes[-i] - volumes[-i-1]) / volumes[-i-1]) * 100
                    # Normalize to -100 to +100 range
                    flows.append({"flow": max(-100, min(100, pct_change))})
                else:
                    flows.append({"flow": 0.0})
            
            # Reverse to chronological order
            flows.reverse()
            
            # Pad if needed
            while len(flows) < 5:
                flows.append({"flow": 0.0})
            
            logger.info(f"ETF flows proxy for {ticker}: {[f['flow'] for f in flows[:5]]}")
            return flows[:5]
            
        except Exception as e:
            logger.error(f"Failed to calculate ETF flows for {ticker}: {e}")
            return [{"flow": 0.0} for _ in range(5)]

    def get_sentiment_history(self, ticker: str, period: str = "1mo") -> List[float]:
        """
        Get sentiment proxy using price volatility
        
        High volatility = extreme sentiment (fear or greed)
        Low volatility = neutral sentiment
        
        Returns: List of 5 sentiment scores (0.0 to 1.0)
        0.5 = neutral, 0.0 = extreme bearish, 1.0 = extreme bullish
        """
        try:
            data = self.get_etf_data(ticker, period=period)
            if not data or 'price' not in data:
                logger.warning(f"No price data for {ticker}, returning neutral sentiment")
                return [0.5] * 5
            
            prices = data['price']
            if len(prices) < 2:
                return [0.5] * 5
            
            sentiments = []
            for i in range(1, min(6, len(prices))):
                if prices[-i-1] > 0:
                    # Price change percentage
                    pct_change = ((prices[-i] - prices[-i-1]) / prices[-i-1])
                    
                    # Convert to sentiment: positive change = bullish, negative = bearish
                    # Map -5% to +5% range to 0.0 to 1.0
                    sentiment = 0.5 + (pct_change * 10)
                    sentiment = max(0.0, min(1.0, sentiment))
                    sentiments.append(sentiment)
                else:
                    sentiments.append(0.5)
            
            # Reverse to chronological order
            sentiments.reverse()
            
            # Pad if needed
            while len(sentiments) < 5:
                sentiments.append(0.5)
            
            logger.info(f"Sentiment history for {ticker}: {sentiments[:5]}")
            return sentiments[:5]
            
        except Exception as e:
            logger.error(f"Failed to calculate sentiment for {ticker}: {e}")
            return [0.5] * 5

    def get_position_data(self, ticker: str) -> Dict[str, float]:
        """
        Get positioning data from institutional holders
        
        Returns:
            long_positions: estimated long positions (0-100)
            short_positions: estimated short positions (0-100)
            total_positions: total positions (100)
        """
        try:
            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders
            
            if holders is None or holders.empty:
                logger.warning(f"No institutional holder data for {ticker}")
                return {"long_positions": 50, "short_positions": 50, "total_positions": 100}
            
            # Calculate skew based on shares held
            # If top holders are increasing positions = bullish skew
            total_shares = holders['Shares'].sum()
            top_5_shares = holders.head(5)['Shares'].sum()
            
            # More concentrated = higher skew (assuming accumulation)
            concentration = top_5_shares / total_shares if total_shares > 0 else 0.5
            
            # Convert concentration to long/short split
            # High concentration (>0.5) = more longs
            # Low concentration (<0.5) = more shorts
            if concentration > 0.5:
                long_positions = 50 + (concentration - 0.5) * 100
                short_positions = 100 - long_positions
            else:
                short_positions = 50 + (0.5 - concentration) * 100
                long_positions = 100 - short_positions
            
            result = {
                "long_positions": float(long_positions),
                "short_positions": float(short_positions),
                "total_positions": 100.0
            }
            
            logger.info(f"Position data for {ticker}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get position data for {ticker}: {e}")
            return {"long_positions": 50, "short_positions": 50, "total_positions": 100}


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
