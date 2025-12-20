"""
FMP (Financial Modeling Prep) API 수집기
실적 발표 결과를 빠르게 수집 (발표 후 2-5분)
"""
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FMPCollector:
    """
    Financial Modeling Prep API 수집기
    
    무료 플랜: 250 requests/day
    
    제공 데이터:
    - 실적 캘린더 (earnings calendar)
    - 실적 서프라이즈 (earnings surprise)
    - 경제 캘린더 (economic calendar)
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def get_earnings_surprise(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        실적 서프라이즈 데이터 가져오기
        
        Args:
            ticker: 종목 심볼
        
        Returns:
            {
                'actual_eps': 실제 EPS,
                'estimated_eps': 예상 EPS,
                'actual_revenue': 실제 매출,
                'estimated_revenue': 예상 매출
            }
        """
        url = f"{self.BASE_URL}/earnings-surprises/{ticker}"
        params = {'apikey': self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        logger.error(f"FMP returned {resp.status} for {ticker}")
                        return None
                    
                    data = await resp.json()
            
            if not data:
                return None
            
            # 가장 최근 데이터
            latest = data[0] if isinstance(data, list) else data
            
            return {
                'actual_eps': latest.get('actualEarningResult'),
                'estimated_eps': latest.get('estimatedEarning'),
                'date': latest.get('date'),
                'ticker': ticker
            }
        
        except Exception as e:
            logger.error(f"FMP earnings surprise error for {ticker}: {e}")
            return None
    
    async def get_earnings_calendar(
        self, 
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        실적 캘린더 가져오기
        
        Returns:
            실적 발표 일정 리스트
        """
        url = f"{self.BASE_URL}/earning_calendar"
        params = {
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'apikey': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
            
            events = []
            for item in data:
                events.append({
                    'ticker': item.get('symbol'),
                    'event_name': f"{item.get('symbol')} Earnings",
                    'scheduled_at': self._parse_datetime(item.get('date'), item.get('time')),
                    'fiscal_quarter': item.get('fiscalDateEnding'),
                    'consensus_estimate': {
                        'eps': item.get('epsEstimate'),
                        'revenue': item.get('revenueEstimate')
                    },
                    'event_type': 'EARNINGS',
                    'data_source': 'FMP'
                })
            
            return events
        
        except Exception as e:
            logger.error(f"FMP earnings calendar error: {e}")
            return []
    
    async def get_economic_calendar(self) -> List[Dict[str, Any]]:
        """
        경제 캘린더 가져오기 (CPI, GDP 등)
        
        Returns:
            경제 이벤트 리스트
        """
        url = f"{self.BASE_URL}/economic_calendar"
        params = {'apikey': self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
            
            events = []
            for item in data:
                # 미래 이벤트만
                event_date = datetime.fromisoformat(item.get('date', ''))
                if event_date < datetime.now():
                    continue
                
                event_type = self._classify_economic_event(item.get('event'))
                
                events.append({
                    'event_name': item.get('event'),
                    'scheduled_at': event_date,
                    'event_type': event_type,
                    'country': item.get('country'),
                    'consensus_estimate': {
                        'value': item.get('estimate')
                    },
                    'importance': self._parse_impact(item.get('impact')),
                    'data_source': 'FMP'
                })
            
            return events
        
        except Exception as e:
            logger.error(f"FMP economic calendar error: {e}")
            return []
    
    def _parse_datetime(self, date_str: str, time_str: str = None) -> datetime:
        """날짜/시간 파싱"""
        try:
            if time_str:
                dt_str = f"{date_str} {time_str}"
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return datetime.now()
    
    def _classify_economic_event(self, event_name: str) -> str:
        """경제 이벤트 타입 분류"""
        event_lower = event_name.lower()
        
        if 'cpi' in event_lower or 'consumer price' in event_lower:
            return 'CPI'
        elif 'gdp' in event_lower or 'gross domestic' in event_lower:
            return 'GDP'
        elif 'nfp' in event_lower or 'non-farm' in event_lower:
            return 'NFP'
        elif 'unemployment' in event_lower or 'jobless' in event_lower:
            return 'UNEMPLOYMENT'
        elif 'fomc' in event_lower or 'fed rate' in event_lower:
            return 'FOMC'
        else:
            return 'ECONOMIC_INDICATOR'
    
    def _parse_impact(self, impact_str: str) -> int:
        """중요도 파싱 (1=높음, 5=낮음)"""
        if not impact_str:
            return 3
        
        impact_lower = impact_str.lower()
        
        if 'high' in impact_lower:
            return 1
        elif 'medium' in impact_lower:
            return 3
        else:
            return 5
