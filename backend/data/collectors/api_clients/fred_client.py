"""
FRED API Client

Federal Reserve Economic Data에서 거시경제 지표를 가져오는 클라이언트

기능:
- 국채 금리 조회 (2Y, 10Y, 30Y)
- VIX 변동성 지수
- 달러 지수 (DXY)

작성일: 2025-12-15
"""

from fredapi import Fred
from typing import Optional, Dict
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)


class FREDClient:
    """
    Federal Reserve Economic Data API 클라이언트
    
    FRED API를 사용하여 거시경제 지표를 가져옵니다.
    
    Usage:
        client = FREDClient()
        
        # 국채 금리
        treasury_10y = client.get_treasury_yield("10Y")
        print(f"10Y Treasury: {treasury_10y}%")
        
        # VIX
        vix = client.get_vix()
        print(f"VIX: {vix}")
        
        # 달러 지수
        dxy = client.get_dxy()
        print(f"DXY: {dxy}")
    """
    
    # FRED Series ID 매핑
    SERIES_IDS = {
        # 국채 금리
        "2Y": "GS2",      # 2-Year Treasury Constant Maturity Rate
        "10Y": "GS10",    # 10-Year Treasury Constant Maturity Rate
        "30Y": "GS30",    # 30-Year Treasury Constant Maturity Rate
        
        # 변동성
        "VIX": "VIXCLS",  # CBOE Volatility Index
        
        # 달러
        "DXY": "DTWEXBGS", # Trade Weighted U.S. Dollar Index: Broad, Goods and Services
        
        # 기타
        "SP500": "SP500",  # S&P 500
        "GOLD": "GOLDAMGBD228NLBM",  # Gold Price
        "OIL": "DCOILWTICO"  # Crude Oil Prices: West Texas Intermediate
    }
    
    def __init__(self):
        """
        FRED Client 초기화
        
        Raises:
            ValueError: FRED_API_KEY가 환경변수에 없을 경우
        """
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise ValueError(
                "FRED_API_KEY not found in environment. "
                "Please add it to .env file"
            )
        
        self.fred = Fred(api_key=api_key)
        logger.info("FREDClient initialized")
    
    def get_treasury_yield(self, maturity: str = "10Y") -> Optional[float]:
        """
        국채 금리 조회
        
        Args:
            maturity: 만기 (2Y, 10Y, 30Y)
            
        Returns:
            금리 (%) 또는 None
        """
        try:
            series_id = self.SERIES_IDS.get(maturity)
            if not series_id:
                logger.error(f"Unknown maturity: {maturity}")
                return None
            
            data = self.fred.get_series_latest_release(series_id)
            
            if data.empty:
                logger.warning(f"No data for {maturity} Treasury")
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"{maturity} Treasury: {value}%")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get {maturity} Treasury: {e}")
            return None
    
    def get_vix(self) -> Optional[float]:
        """
        VIX 변동성 지수
        
        Returns:
            VIX 값 또는 None
        """
        try:
            data = self.fred.get_series_latest_release(self.SERIES_IDS["VIX"])
            
            if data.empty:
                logger.warning("No VIX data available")
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"VIX: {value}")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get VIX: {e}")
            return None
    
    def get_dxy(self) -> Optional[float]:
        """
        달러 지수 (DXY)
        
        Returns:
            DXY 값 또는 None
        """
        try:
            data = self.fred.get_series_latest_release(self.SERIES_IDS["DXY"])
            
            if data.empty:
                logger.warning("No DXY data available")
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"DXY: {value}")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get DXY: {e}")
            return None
    
    def get_sp500(self) -> Optional[float]:
        """
        S&P 500 지수
        
        Returns:
            S&P 500 값 또는 None
        """
        try:
            data = self.fred.get_series_latest_release(self.SERIES_IDS["SP500"])
            
            if data.empty:
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"S&P 500: {value}")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get S&P 500: {e}")
            return None
    
    def get_gold_price(self) -> Optional[float]:
        """
        금 가격
        
        Returns:
            금 가격 (USD/oz) 또는 None
        """
        try:
            data = self.fred.get_series_latest_release(self.SERIES_IDS["GOLD"])
            
            if data.empty:
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"Gold: ${value}/oz")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get gold price: {e}")
            return None
    
    def get_oil_price(self) -> Optional[float]:
        """
        원유 가격 (WTI)
        
        Returns:
            원유 가격 (USD/barrel) 또는 None
        """
        try:
            data = self.fred.get_series_latest_release(self.SERIES_IDS["OIL"])
            
            if data.empty:
                return None
            
            value = float(data.iloc[-1])
            logger.info(f"WTI Oil: ${value}/barrel")
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get oil price: {e}")
            return None
    
    def get_all_macro_indicators(self) -> Dict[str, float]:
        """
        모든 거시경제 지표 한 번에 조회
        
        Returns:
            {
                'treasury_2y': float,
                'treasury_10y': float,
                'treasury_30y': float,
                'yield_curve': float,  # 10Y - 2Y
                'vix': float,
                'dxy': float,
                'sp500': float,
                'gold': float,
                'oil': float
            }
        """
        logger.info("Fetching all macro indicators")
        
        # 국채 금리
        treasury_2y = self.get_treasury_yield("2Y") or 0.0
        treasury_10y = self.get_treasury_yield("10Y") or 0.0
        treasury_30y = self.get_treasury_yield("30Y") or 0.0
        
        # 수익률 곡선 (10Y - 2Y)
        yield_curve = treasury_10y - treasury_2y
        
        result = {
            'treasury_2y': treasury_2y,
            'treasury_10y': treasury_10y,
            'treasury_30y': treasury_30y,
            'yield_curve': yield_curve,
            'vix': self.get_vix() or 0.0,
            'dxy': self.get_dxy() or 0.0,
            'sp500': self.get_sp500() or 0.0,
            'gold': self.get_gold_price() or 0.0,
            'oil': self.get_oil_price() or 0.0
        }
        
        logger.info(f"Retrieved {len(result)} macro indicators")
        
        return result


# 전역 인스턴스
_fred_client = None


def get_fred_client() -> FREDClient:
    """전역 FREDClient 인스턴스 반환"""
    global _fred_client
    if _fred_client is None:
        _fred_client = FREDClient()
    return _fred_client


# 테스트
if __name__ == "__main__":
    print("=== FRED Client Test ===\n")
    
    try:
        client = FREDClient()
        
        # Test 1: 국채 금리
        print("Test 1: Treasury Yields")
        treasury_2y = client.get_treasury_yield("2Y")
        treasury_10y = client.get_treasury_yield("10Y")
        yield_curve = treasury_10y - treasury_2y
        
        print(f"2Y Treasury: {treasury_2y}%")
        print(f"10Y Treasury: {treasury_10y}%")
        print(f"Yield Curve: {yield_curve:+.2f}%")
        
        # Test 2: VIX
        print("\nTest 2: VIX")
        vix = client.get_vix()
        print(f"VIX: {vix}")
        
        # Test 3: 달러 지수
        print("\nTest 3: Dollar Index")
        dxy = client.get_dxy()
        print(f"DXY: {dxy}")
        
        # Test 4: 전체 지표
        print("\nTest 4: All Macro Indicators")
        indicators = client.get_all_macro_indicators()
        for key, value in indicators.items():
            print(f"  {key}: {value}")
        
        print("\n✅ FRED Client test completed!")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease add FRED_API_KEY to .env file")
