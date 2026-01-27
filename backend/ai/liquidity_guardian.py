"""
Liquidity Guardian

주문 직전 유동성 체크. 주문량이 일평균 거래량의 5% 초과 시 거부, Bid-Ask Spread 2% 초과 시 경고.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

class LiquidityGuardian:
    """
    주문 직전 유동성 체크 클래스
    """
    
    def __init__(self, volume_threshold: float = 0.05, spread_threshold: float = 0.02):
        """
        초기화
        
        Args:
            volume_threshold: 일평균 거래량 대비 주문량 비율 임계값 (기본값: 5%)
            spread_threshold: Bid-Ask Spread 임계값 (기본값: 2%)
        """
        self.volume_threshold = volume_threshold
        self.spread_threshold = spread_threshold
        self.cache = {}  # 데이터 캐싱 (TTL: 1시간)
    
    def check_liquidity(self, symbol: str, order_shares: int, order_value: float) -> Dict:
        """
        주문 유동성 체크
        
        Args:
            symbol: 종목 심볼
            order_shares: 주문 수량
            order_value: 주문 가치
            
        Returns:
            Dict: 유동성 체크 결과
                - allow: 주문 허용 여부
                - warning: 경고 메시지 (있는 경우)
                - volume_impact: 거래량 영향도 비율
                - spread: Bid-Ask Spread 비율
                - avg_volume: 일평균 거래량
                - reason: 결정 사유
                - timestamp: 체크 시간
        """
        try:
            # 캐시 확인
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H')}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                avg_volume = cached_data['avg_volume']
                spread = cached_data['spread']
            else:
                # 데이터 가져오기
                avg_volume, spread = self._fetch_liquidity_data(symbol)
                
                # 캐싱
                self.cache[cache_key] = {
                    'avg_volume': avg_volume,
                    'spread': spread,
                    'timestamp': datetime.now()
                }
            
            # 거래량 영향도 계산
            volume_impact = order_shares / avg_volume if avg_volume > 0 else float('inf')
            
            # 주문 허용 여부 결정
            allow = True
            warning = None
            reason = "Order approved"
            
            # 거래량 체크
            if volume_impact > self.volume_threshold:
                allow = False
                reason = f"Order size ({order_shares:,} shares) exceeds {self.volume_threshold:.0%} of average daily volume ({avg_volume:,}). Volume impact: {volume_impact:.1%}"
            
            # Bid-Ask Spread 체크
            if spread > self.spread_threshold:
                if allow:  # 거래량 문제가 없는 경우에만 경고
                    warning = f"High bid-ask spread detected: {spread:.2%}. Consider market impact."
                    reason = f"Order approved with warning: {warning}"
            
            # 결과 구성
            result = {
                'allow': allow,
                'warning': warning,
                'volume_impact': volume_impact,
                'spread': spread,
                'avg_volume': avg_volume,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Liquidity check for {symbol}: allow={allow}, volume_impact={volume_impact:.1%}, spread={spread:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in liquidity check for {symbol}: {str(e)}")
            # 에러 시 주문 허용 (보수적 접근)
            return {
                'allow': True,
                'warning': f"Liquidity check failed: {str(e)}",
                'volume_impact': 0.0,
                'spread': 0.0,
                'avg_volume': 0,
                'reason': f"Liquidity check failed: {str(e)}. Order approved by default.",
                'timestamp': datetime.now().isoformat()
            }
    
    def _fetch_liquidity_data(self, symbol: str) -> Tuple[int, float]:
        """
        유동성 데이터 가져오기
        
        Args:
            symbol: 종목 심볼
            
        Returns:
            Tuple[int, float]: (일평균 거래량, Bid-Ask Spread 비율)
        """
        try:
            # yfinance를 통해 데이터 가져오기
            ticker = yf.Ticker(symbol)
            
            # 일평균 거래량 (20일)
            hist = ticker.history(period="21d")  # 21일 데이터 가져오기 (최근 20일 + 오늘)
            if len(hist) < 5:  # 최소 5일 데이터 필요
                return 0, 0.0
                
            avg_volume = int(hist['Volume'].tail(20).mean())
            
            # Bid-Ask Spread 계산
            # yfinance는 직접적인 bid-ask 데이터를 제공하지 않으므로,
            # 종가 대비 고가-저가 차이의 비율로 근사
            today_data = hist.tail(1).iloc[0]
            if today_data['Close'] > 0:
                spread = (today_data['High'] - today_data['Low']) / today_data['Close']
            else:
                spread = 0.0
            
            return avg_volume, spread
            
        except Exception as e:
            logger.error(f"Error fetching liquidity data for {symbol}: {str(e)}")
            return 0, 0.0
    
    def check_order_value_impact(self, symbol: str, order_value: float, market_cap: Optional[float] = None) -> Dict:
        """
        주문 가치가 시가총액에 미치는 영향 체크
        
        Args:
            symbol: 종목 심볼
            order_value: 주문 가치
            market_cap: 시가총액 (선택적, 없으면 yfinance에서 가져옴)
            
        Returns:
            Dict: 주문 가치 영향 분석 결과
        """
        try:
            # 시가총액 가져오기
            if market_cap is None:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                market_cap = info.get('marketCap', 0)
            
            if market_cap <= 0:
                return {
                    'impact_ratio': 0.0,
                    'allow': True,
                    'reason': 'Unable to determine market cap. Order approved by default.',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 영향도 계산
            impact_ratio = order_value / market_cap
            
            # 1% 이상이면 경고
            if impact_ratio > 0.01:
                return {
                    'impact_ratio': impact_ratio,
                    'allow': True,
                    'warning': f"Large order relative to market cap: {impact_ratio:.2%}",
                    'reason': f"Order value represents {impact_ratio:.2%} of market cap. Consider splitting order.",
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'impact_ratio': impact_ratio,
                    'allow': True,
                    'reason': 'Order value impact is acceptable.',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error checking order value impact for {symbol}: {str(e)}")
            return {
                'impact_ratio': 0.0,
                'allow': True,
                'reason': f'Error checking order value impact: {str(e)}. Order approved by default.',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_liquidity_summary(self, symbol: str) -> Dict:
        """
        종목 유동성 요약 정보 반환
        
        Args:
            symbol: 종목 심볼
            
        Returns:
            Dict: 유동성 요약 정보
        """
        try:
            avg_volume, spread = self._fetch_liquidity_data(symbol)
            
            # 시가총액 정보
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            
            # 유동성 등급
            if avg_volume >= 1000000:  # 100만주 이상
                liquidity_grade = 'HIGH'
            elif avg_volume >= 100000:  # 10만주 이상
                liquidity_grade = 'MEDIUM'
            else:
                liquidity_grade = 'LOW'
            
            return {
                'symbol': symbol,
                'avg_daily_volume': avg_volume,
                'bid_ask_spread': spread,
                'market_cap': market_cap,
                'liquidity_grade': liquidity_grade,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting liquidity summary for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'avg_daily_volume': 0,
                'bid_ask_spread': 0.0,
                'market_cap': 0,
                'liquidity_grade': 'UNKNOWN',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }