"""
Massive API Client

Massive (구 Polygon.io) API 클라이언트
분당 5회 호출 제한 적용
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from collections import deque
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """레이트 리밋 설정"""
    calls_per_minute: int = 5
    window_seconds: int = 60


class RateLimiter:
    """
    분당 호출 횟수 제한을 위한 레이트 리미터
    
    Massive API 무료 티어: 분당 5회 호출
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.call_times: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        API 호출 허용 여부 확인 및 대기
        
        Returns:
            bool: 호출 가능 여부
        """
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.config.window_seconds)
            
            # 윈도우 밖의 호출 기록 제거
            while self.call_times and self.call_times[0] < window_start:
                self.call_times.popleft()
            
            # 호출 횟수 확인
            if len(self.call_times) >= self.config.calls_per_minute:
                # 가장 오래된 호출 이후 윈도우 시간만큼 대기
                wait_until = self.call_times[0] + timedelta(seconds=self.config.window_seconds)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"레이트 리밋 대기: {wait_seconds:.1f}초")
                    await asyncio.sleep(wait_seconds)
                
                # 대기 후 다시 정리
                now = datetime.now()
                window_start = now - timedelta(seconds=self.config.window_seconds)
                while self.call_times and self.call_times[0] < window_start:
                    self.call_times.popleft()
            
            # 호출 기록 추가
            self.call_times.append(now)
            return True
    
    def get_remaining_calls(self) -> int:
        """현재 윈도우에서 남은 호출 횟수"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.window_seconds)
        
        # 윈도우 내 호출 수 계산
        recent_calls = sum(1 for t in self.call_times if t >= window_start)
        return max(0, self.config.calls_per_minute - recent_calls)


class MassiveAPIClient:
    """
    Massive API 클라이언트
    
    무료 티어 기능:
    - 모든 미국 옵션 종목 코드
    - 분당 5회 API 호출
    - 2년간의 과거 데이터
    - 100% 시장 커버리지
    - 일일 마감 데이터
    - 참조 데이터
    - 기업 활동
    - 기술적 지표
    - 분 단위 집계
    """
    
    BASE_URL = "https://api.polygon.io"  # Massive는 Polygon.io 기반
    
    def __init__(
        self,
        api_key: str = None,
        rate_limit: RateLimitConfig = None,
    ):
        self.api_key = api_key or os.getenv("MASSIVE_API_KEY") or os.getenv("POLYGON_API_KEY")
        self.rate_limiter = RateLimiter(rate_limit or RateLimitConfig(calls_per_minute=5))
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """aiohttp 세션 가져오기"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """세션 종료"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
    ) -> Optional[Dict]:
        """
        API 요청 (레이트 리밋 적용)
        
        Args:
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            
        Returns:
            API 응답 또는 None
        """
        if not self.api_key:
            logger.warning("Massive/Polygon API 키가 설정되지 않음")
            return None
        
        # 레이트 리밋 확인
        await self.rate_limiter.acquire()
        
        session = await self._get_session()
        
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["apiKey"] = self.api_key
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("레이트 리밋 초과, 재시도 대기")
                    await asyncio.sleep(60)
                    return await self._request(endpoint, params)
                else:
                    logger.error(f"API 오류: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"API 요청 실패: {e}")
            return None
    
    # ============================================
    # 주식 데이터 API
    # ============================================
    
    async def get_stock_aggregates(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "day",
        from_date: str = None,
        to_date: str = None,
    ) -> Optional[Dict]:
        """
        주식 집계 데이터 가져오기
        
        Args:
            ticker: 종목 티커
            multiplier: 시간 단위 배수
            timespan: minute, hour, day, week, month, quarter, year
            from_date: 시작일 (YYYY-MM-DD)
            to_date: 종료일 (YYYY-MM-DD)
        """
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        return await self._request(endpoint)
    
    async def get_stock_quote(self, ticker: str) -> Optional[Dict]:
        """실시간 호가 가져오기"""
        endpoint = f"/v2/last/nbbo/{ticker}"
        return await self._request(endpoint)
    
    async def get_stock_trades(self, ticker: str) -> Optional[Dict]:
        """최근 거래 가져오기"""
        endpoint = f"/v2/last/trade/{ticker}"
        return await self._request(endpoint)
    
    # ============================================
    # 옵션 데이터 API
    # ============================================
    
    async def get_options_chain(
        self,
        ticker: str,
        expiration_date: str = None,
        strike_price: float = None,
        contract_type: str = None,  # call, put
    ) -> Optional[Dict]:
        """
        옵션 체인 가져오기
        
        Args:
            ticker: 기초자산 티커
            expiration_date: 만기일 (YYYY-MM-DD)
            strike_price: 행사가
            contract_type: call 또는 put
            
        Returns:
            옵션 체인 데이터
        """
        endpoint = f"/v3/reference/options/contracts"
        
        params = {
            "underlying_ticker": ticker,
            "limit": 250,
        }
        
        if expiration_date:
            params["expiration_date"] = expiration_date
        if strike_price:
            params["strike_price"] = strike_price
        if contract_type:
            params["contract_type"] = contract_type
        
        result = await self._request(endpoint, params)
        
        if result and "results" in result:
            contracts = result["results"]
            
            # Put/Call 비율 계산
            calls = [c for c in contracts if c.get("contract_type") == "call"]
            puts = [c for c in contracts if c.get("contract_type") == "put"]
            
            put_call_ratio = len(puts) / len(calls) if calls else 1.0
            
            return {
                "ticker": ticker,
                "contracts": contracts,
                "total_count": len(contracts),
                "calls_count": len(calls),
                "puts_count": len(puts),
                "put_call_ratio": put_call_ratio,
            }
        
        return None
    
    async def get_options_aggregate(
        self,
        options_ticker: str,
        from_date: str = None,
        to_date: str = None,
    ) -> Optional[Dict]:
        """
        개별 옵션 집계 데이터
        
        Args:
            options_ticker: 옵션 티커 (예: O:AAPL230616C00150000)
        """
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{options_ticker}/range/1/day/{from_date}/{to_date}"
        return await self._request(endpoint)
    
    # ============================================
    # 참조 데이터 API
    # ============================================
    
    async def get_ticker_details(self, ticker: str) -> Optional[Dict]:
        """종목 상세 정보"""
        endpoint = f"/v3/reference/tickers/{ticker}"
        return await self._request(endpoint)
    
    async def get_ticker_news(
        self,
        ticker: str,
        limit: int = 10,
    ) -> Optional[Dict]:
        """종목 관련 뉴스"""
        endpoint = "/v2/reference/news"
        params = {"ticker": ticker, "limit": limit}
        return await self._request(endpoint, params)
    
    async def get_stock_financials(
        self,
        ticker: str,
        limit: int = 4,
    ) -> Optional[Dict]:
        """재무제표 데이터"""
        endpoint = f"/vX/reference/financials"
        params = {"ticker": ticker, "limit": limit}
        return await self._request(endpoint, params)
    
    async def get_dividends(
        self,
        ticker: str,
        limit: int = 10,
    ) -> Optional[Dict]:
        """배당 데이터"""
        endpoint = "/v3/reference/dividends"
        params = {"ticker": ticker, "limit": limit}
        return await self._request(endpoint, params)
    
    async def get_stock_splits(
        self,
        ticker: str,
        limit: int = 10,
    ) -> Optional[Dict]:
        """주식 분할 데이터"""
        endpoint = "/v3/reference/splits"
        params = {"ticker": ticker, "limit": limit}
        return await self._request(endpoint, params)
    
    # ============================================
    # 기술적 지표 API
    # ============================================
    
    async def get_sma(
        self,
        ticker: str,
        window: int = 50,
        timespan: str = "day",
    ) -> Optional[Dict]:
        """단순 이동평균"""
        endpoint = f"/v1/indicators/sma/{ticker}"
        params = {
            "timespan": timespan,
            "window": window,
            "limit": 100,
        }
        return await self._request(endpoint, params)
    
    async def get_ema(
        self,
        ticker: str,
        window: int = 12,
        timespan: str = "day",
    ) -> Optional[Dict]:
        """지수 이동평균"""
        endpoint = f"/v1/indicators/ema/{ticker}"
        params = {
            "timespan": timespan,
            "window": window,
            "limit": 100,
        }
        return await self._request(endpoint, params)
    
    async def get_rsi(
        self,
        ticker: str,
        window: int = 14,
        timespan: str = "day",
    ) -> Optional[Dict]:
        """RSI"""
        endpoint = f"/v1/indicators/rsi/{ticker}"
        params = {
            "timespan": timespan,
            "window": window,
            "limit": 100,
        }
        return await self._request(endpoint, params)
    
    async def get_macd(
        self,
        ticker: str,
        short_window: int = 12,
        long_window: int = 26,
        signal_window: int = 9,
        timespan: str = "day",
    ) -> Optional[Dict]:
        """MACD"""
        endpoint = f"/v1/indicators/macd/{ticker}"
        params = {
            "timespan": timespan,
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "limit": 100,
        }
        return await self._request(endpoint, params)
    
    # ============================================
    # 유틸리티
    # ============================================
    
    def get_remaining_calls(self) -> int:
        """남은 API 호출 횟수"""
        return self.rate_limiter.get_remaining_calls()


# 싱글톤 인스턴스
_client_instance: Optional[MassiveAPIClient] = None


def get_massive_client() -> MassiveAPIClient:
    """Massive API 클라이언트 싱글톤 가져오기"""
    global _client_instance
    if _client_instance is None:
        _client_instance = MassiveAPIClient()
    return _client_instance
