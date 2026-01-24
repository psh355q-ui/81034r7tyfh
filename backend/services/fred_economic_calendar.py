"""
FRED (Federal Reserve Economic Data) API 기반 경제 캘더 시스템

FRED API를 사용하여 경제 지표 데이터를 수집하고 분석합니다.

Features:
- FRED API에서 경제 지표 데이터 수집
- 발표 일정 및 예상치/실제치 추적
- Surprise 분석 (예상 vs 실제 괴리)
- DB 저장 및 관리

API Documentation:
https://fred.stlouisfed.org/docs/api/fred/

Economic Indicators:
- GDP (Gross Domestic Product): GDPC1, NYGDPMKTPSAKR
- CPI (Consumer Price Index): CPIAUCSL, CPILFESL
- PCE (Personal Consumption Expenditures): PCEPI, PCEPILFE
- Unemployment Rate: UNRATE
- FOMC Meeting: FEDFUNDS
- PMI: NAPM, MANEMP
- Housing: HOUST, PERMIT
"""

import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import os
from sqlalchemy import text

from backend.database.models import EconomicEvent
from backend.database.db_service import get_db_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FREDEconomicCalendar:
    """
    FRED API 기반 경제 캘더
    
    Features:
    - FRED API에서 경제 지표 데이터 수집
    - 발표 일정 및 예상치/실제치 추적
    - Surprise 분석 (예상 vs 실제 괴리)
    - DB 저장 및 관리
    """
    
    def __init__(self):
        self.api_key = os.getenv('FRED_API_KEY')
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.timeout = 30
        self.max_retries = 3
        
        # 경제 지표 시리즈 ID 매핑
        self.series_map = {
            # 미국 경제 지표
            'US_GDP': {
                'series_id': 'GDPC1',
                'name': '미국 실질 GDP',
                'country': 'US',
                'category': 'GDP',
                'importance': 3,
                'frequency': 'quarterly'
            },
            'US_CPI': {
                'series_id': 'CPIAUCSL',
                'name': '미국 소비자물가지수 (CPI)',
                'country': 'US',
                'category': 'Inflation',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_CPI_CORE': {
                'series_id': 'CPILFESL',
                'name': '미국 근원 CPI (Core CPI)',
                'country': 'US',
                'category': 'Inflation',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_PCE': {
                'series_id': 'PCEPI',
                'name': '미국 개인소비지출 (PCE)',
                'country': 'US',
                'category': 'Inflation',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_PCE_CORE': {
                'series_id': 'PCEPILFE',
                'name': '미국 근원 PCE (Core PCE)',
                'country': 'US',
                'category': 'Inflation',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_UNEMPLOYMENT': {
                'series_id': 'UNRATE',
                'name': '미국 실업률',
                'country': 'US',
                'category': 'Employment',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_FEDFUNDS': {
                'series_id': 'FEDFUNDS',
                'name': '미국 연방기금금리 (Fed Funds Rate)',
                'country': 'US',
                'category': 'FOMC',
                'importance': 3,
                'frequency': 'monthly'
            },
            'US_PMI': {
                'series_id': 'NAPM',
                'name': '미국 제조업 PMI',
                'country': 'US',
                'category': 'PMI',
                'importance': 2,
                'frequency': 'monthly'
            },
            'US_HOUSING': {
                'series_id': 'HOUST',
                'name': '미국 주택 착공 수',
                'country': 'US',
                'category': 'Housing',
                'importance': 2,
                'frequency': 'monthly'
            },
            'US_PERMIT': {
                'series_id': 'PERMIT',
                'name': '미국 주택 건축 허가',
                'country': 'US',
                'category': 'Housing',
                'importance': 2,
                'frequency': 'monthly'
            },
            # 한국 경제 지표
            'KR_GDP': {
                'series_id': 'NYGDPMKTPSAKR',
                'name': '한국 실질 GDP',
                'country': 'KR',
                'category': 'GDP',
                'importance': 3,
                'frequency': 'quarterly'
            },
        }
        
        if not self.api_key:
            logger.warning("FRED_API_KEY not found in environment variables")
    
    async def fetch_series_data(self, series_id: str, limit: int = 10) -> List[Dict]:
        """
        FRED 시리즈 데이터 수집
        
        Args:
            series_id: FRED 시리즈 ID
            limit: 가져올 데이터 수
            
        Returns:
            데이터 리스트
        """
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'limit': limit,
                'sort_order': 'desc'
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'observations' not in data:
                    logger.warning(f"No observations found for series {series_id}")
                    return []
                
                observations = data['observations']
                logger.info(f"Fetched {len(observations)} observations for {series_id}")
                
                return observations
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching series data for {series_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching series data for {series_id}: {e}")
            return []
    
    def parse_observation(self, observation: Dict, series_info: Dict) -> Optional[Dict]:
        """
        FRED 관측값 파싱
        
        Args:
            observation: FRED 관측값
            series_info: 시리즈 정보
            
        Returns:
            이벤트 딕셔너리
        """
        try:
            date_str = observation.get('date')
            value_str = observation.get('value')
            
            if not date_str or value_str == '.':
                return None
            
            # 날짜 파싱
            event_time = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 한국 시간으로 변환 (UTC+9)
            event_time = event_time.replace(hour=9, minute=0)  # 오전 9시 발표
            
            # 이전치 (previous) - 바로 이전 관측값
            # 이는 나중에 계산
            
            event = {
                'event_name': series_info['name'],
                'country': series_info['country'],
                'category': series_info['category'],
                'event_time': event_time,
                'importance': series_info['importance'],
                'actual': value_str,
                'forecast': None,  # FRED는 예상치를 제공하지 않음
                'previous': None,  # 나중에 계산
                'surprise_pct': None,
                'impact_direction': None,
                'impact_score': None
            }
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing observation: {e}")
            return None
    
    def calculate_surprise(self, event: Dict, previous_value: Optional[str] = None) -> Dict:
        """
        Surprise 계산 (실제 vs 이전치 비교)
        
        Args:
            event: 이벤트 딕셔너리
            previous_value: 이전치
            
        Returns:
            업데이트된 이벤트 딕셔너리
        """
        try:
            actual_str = event.get('actual')
            if not actual_str or actual_str == '.':
                return event
            
            actual = float(actual_str)
            
            if previous_value and previous_value != '.':
                previous = float(previous_value)
                
                # Surprise 계산 (실제 - 이전) / 이전 * 100
                if previous != 0:
                    surprise_pct = ((actual - previous) / previous) * 100
                    event['surprise_pct'] = round(surprise_pct, 2)
                    
                    # Impact Direction 결정
                    if surprise_pct > 0.5:
                        event['impact_direction'] = 'Bullish'
                        event['impact_score'] = min(int(abs(surprise_pct) * 10), 100)
                    elif surprise_pct < -0.5:
                        event['impact_direction'] = 'Bearish'
                        event['impact_score'] = min(int(abs(surprise_pct) * 10), 100)
                    else:
                        event['impact_direction'] = 'Neutral'
                        event['impact_score'] = 0
            
            return event
            
        except Exception as e:
            logger.error(f"Error calculating surprise: {e}")
            return event
    
    async def fetch_all_indicators(self, days_back: int = 30) -> List[Dict]:
        """
        모든 경제 지표 데이터 수집
        
        Args:
            days_back: 과거 며칠까지 수집할지
            
        Returns:
            이벤트 리스트
        """
        all_events = []
        
        for key, series_info in self.series_map.items():
            logger.info(f"Fetching data for {key}...")
            
            observations = await self.fetch_series_data(series_info['series_id'])
            
            if not observations:
                continue
            
            # 관측값 파싱
            events = []
            for i, obs in enumerate(observations):
                event = self.parse_observation(obs, series_info)
                
                if event:
                    # 이전치 계산
                    if i < len(observations) - 1:
                        previous_obs = observations[i + 1]
                        previous_value = previous_obs.get('value')
                        event['previous'] = previous_value
                        
                        # Surprise 계산
                        event = self.calculate_surprise(event, previous_value)
                    
                    events.append(event)
            
            all_events.extend(events)
        
        logger.info(f"Total events fetched: {len(all_events)}")
        return all_events
    
    async def save_to_db(self, events: List[Dict]) -> int:
        """
        이벤트를 DB에 저장
        
        Args:
            events: 이벤트 리스트
            
        Returns:
            저장된 이벤트 수
        """
        saved_count = 0
        
        try:
            db_service = await get_db_service()
            
            async with db_service.get_session() as session:
                for event_data in events:
                    # 중복 확인
                    result = await session.execute(
                        text(f"SELECT id FROM economic_events WHERE event_name = '{event_data['event_name']}' "
                             f"AND event_time = '{event_data['event_time']}'")
                    )
                    
                    if result.fetchone():
                        logger.info(f"Event already exists: {event_data['event_name']} at {event_data['event_time']}")
                        continue
                    
                    # 이벤트 생성
                    event = EconomicEvent(
                        event_name=event_data['event_name'],
                        country=event_data['country'],
                        category=event_data['category'],
                        event_time=event_data['event_time'],
                        importance=event_data['importance'],
                        forecast=event_data['forecast'],
                        actual=event_data['actual'],
                        previous=event_data['previous'],
                        surprise_pct=event_data['surprise_pct'],
                        impact_direction=event_data['impact_direction'],
                        impact_score=event_data['impact_score'],
                        is_processed=True,  # FRED 데이터는 이미 발표된 데이터이므로 처리 완료
                        processed_at=datetime.utcnow()
                    )
                    
                    session.add(event)
                    saved_count += 1
                
                logger.info(f"Saved {saved_count} new events to database")
                return saved_count
                
        except Exception as e:
            logger.error(f"Error saving events to database: {e}")
            return 0
    
    async def load_today_calendar(self) -> List[Dict]:
        """
        오늘의 경제 캘더 로드 (DB에서)
        
        Returns:
            오늘의 이벤트 리스트
        """
        try:
            db_service = await get_db_service()
            
            async with db_service.get_session() as session:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow = today + timedelta(days=1)
                
                result = await session.execute(
                    text(f"SELECT * FROM economic_events "
                         f"WHERE event_time >= '{today}' AND event_time < '{tomorrow}' "
                         f"ORDER BY event_time")
                )
                
                events = []
                for row in result.fetchall():
                    events.append({
                        'event_name': row[1],
                        'country': row[2],
                        'category': row[3],
                        'event_time': row[4],
                        'importance': row[5],
                        'forecast': row[6],
                        'actual': row[7],
                        'previous': row[8],
                        'surprise_pct': row[9],
                        'impact_direction': row[10],
                        'impact_score': row[11],
                        'is_processed': row[12],
                        'processed_at': row[13]
                    })
                
                logger.info(f"Loaded {len(events)} events for today")
                return events
                
        except Exception as e:
            logger.error(f"Error loading today's calendar: {e}")
            return []
    
    async def update_calendar(self, days_back: int = 30) -> int:
        """
        경제 캘더 업데이트
        
        Args:
            days_back: 과거 며칠까지 업데이트할지
            
        Returns:
            업데이트된 이벤트 수
        """
        logger.info("Updating economic calendar from FRED API...")
        
        # 데이터 수집
        events = await self.fetch_all_indicators(days_back)
        
        if not events:
            logger.warning("No events fetched from FRED API")
            return 0
        
        # DB 저장
        saved_count = await self.save_to_db(events)
        
        return saved_count


async def main():
    """메인 함수 - 테스트용"""
    calendar = FREDEconomicCalendar()
    
    print("=" * 60)
    print("FRED Economic Calendar Test")
    print("=" * 60)
    print()
    
    # 경제 캘더 업데이트
    print("Updating economic calendar...")
    saved_count = await calendar.update_calendar(days_back=30)
    
    print()
    print(f"✓ Updated {saved_count} events")
    print()
    
    # 오늘의 경제 캘더 로드
    print("Loading today's calendar...")
    today_events = await calendar.load_today_calendar()
    
    print()
    print(f"✓ Today's events: {len(today_events)}")
    print()
    
    if today_events:
        print("Today's Economic Events:")
        print("-" * 60)
        for event in today_events:
            importance_stars = '★' * event['importance']
            print(f"{importance_stars} {event['event_name']}")
            print(f"  Time: {event['event_time']}")
            print(f"  Actual: {event['actual']}")
            if event['previous']:
                print(f"  Previous: {event['previous']}")
            if event['surprise_pct'] is not None:
                print(f"  Surprise: {event['surprise_pct']:.2f}%")
                print(f"  Impact: {event['impact_direction']} (Score: {event['impact_score']})")
            print()


if __name__ == "__main__":
    asyncio.run(main())
