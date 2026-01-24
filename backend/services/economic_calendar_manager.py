"""
Economic Calendar Manager

경제 캘더 정보를 1년치 DB로 저장하고 캐싱하는 시스템

Features:
- FRED API에서 1년치 경제 캘더 데이터 수집
- DB에 저장 및 캐싱
- 매주 토요일에 다음달의 일정 확인
- 캐싱 데이터 대비 추가되는 내용 업데이트

Usage:
    from backend.services.economic_calendar_manager import EconomicCalendarManager
    
    manager = EconomicCalendarManager()
    await manager.initialize_calendar()  # 1년치 데이터 초기화
    await manager.update_calendar()  # 주간 업데이트
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.services.fred_economic_calendar import FREDEconomicCalendar
from backend.database.db_service import get_db_service
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EconomicCalendarManager:
    """
    경제 캘더 관리자
    
    Features:
    - 1년치 경제 캘더 데이터 수집 및 저장
    - 캐싱 로직
    - 주간 업데이트 (매주 토요일)
    - 다음달 일정 확인 및 업데이트
    """
    
    def __init__(self):
        self.fred_calendar = FREDEconomicCalendar()
        self.cache_duration_days = 365  # 1년치 캐싱
    
    async def initialize_calendar(self) -> Dict:
        """
        1년치 경제 캘더 데이터 초기화
        
        Returns:
            초기화 결과 딕셔너리
        """
        logger.info("Initializing economic calendar (1 year data)...")
        
        try:
            # FRED API에서 1년치 데이터 수집
            # limit을 52로 설정 (주간 데이터 * 52주)
            events = await self.fred_calendar.fetch_all_indicators(days_back=365)
            
            if not events:
                logger.warning("No events fetched from FRED API")
                return {
                    'success': False,
                    'message': 'No events fetched from FRED API',
                    'events_count': 0
                }
            
            # DB에 저장
            saved_count = await self.fred_calendar.save_to_db(events)
            
            logger.info(f"✓ Initialized {saved_count} economic events (1 year data)")
            
            return {
                'success': True,
                'message': f'Initialized {saved_count} economic events',
                'events_count': saved_count
            }
            
        except Exception as e:
            logger.error(f"Error initializing economic calendar: {e}")
            return {
                'success': False,
                'message': f'Error initializing calendar: {e}',
                'events_count': 0
            }
    
    async def update_calendar(self) -> Dict:
        """
        주간 업데이트 (매주 토요일)
        
        - 다음달의 일정 확인
        - 캐싱 데이터 대비 추가되는 내용 업데이트
        
        Returns:
            업데이트 결과 딕셔너리
        """
        logger.info("Updating economic calendar (weekly update)...")
        
        try:
            # 오늘이 토요일인지 확인
            today = datetime.now()
            is_saturday = today.weekday() == 5  # 5 = 토요일
            
            if not is_saturday:
                logger.info("Today is not Saturday. Skipping weekly update.")
                return {
                    'success': True,
                    'message': 'Today is not Saturday. Skipping weekly update.',
                    'events_count': 0
                }
            
            # 다음달의 시작일과 종료일 계산
            if today.month == 12:
                next_month_start = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month_start = today.replace(month=today.month + 1, day=1)
            
            if next_month_start.month == 12:
                next_month_end = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1)
            else:
                next_month_end = next_month_start.replace(month=next_month_start.month + 1, day=1)
            
            logger.info(f"Checking events for next month: {next_month_start.strftime('%Y-%m')} to {next_month_end.strftime('%Y-%m')}")
            
            # 다음달의 이벤트 확인 (DB에서)
            db_service = await get_db_service()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM economic_events "
                         f"WHERE event_time >= '{next_month_start}' "
                         f"AND event_time < '{next_month_end}'")
                )
                
                existing_count = result.fetchone()[0]
            
            logger.info(f"Existing events for next month: {existing_count}")
            
            # FRED API에서 다음달 데이터 수집
            # 최근 데이터를 가져오기 위해 limit을 10으로 설정
            events = await self.fred_calendar.fetch_all_indicators(days_back=30)
            
            # 다음달 이벤트 필터링
            next_month_events = [
                event for event in events
                if next_month_start <= event['event_time'] < next_month_end
            ]
            
            logger.info(f"Next month events from FRED API: {len(next_month_events)}")
            
            # DB에 저장 (중복 제외)
            saved_count = await self.fred_calendar.save_to_db(next_month_events)
            
            logger.info(f"✓ Updated {saved_count} events for next month")
            
            return {
                'success': True,
                'message': f'Updated {saved_count} events for next month',
                'events_count': saved_count,
                'next_month': next_month_start.strftime('%Y-%m')
            }
            
        except Exception as e:
            logger.error(f"Error updating economic calendar: {e}")
            return {
                'success': False,
                'message': f'Error updating calendar: {e}',
                'events_count': 0
            }
    
    async def get_cached_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        캐싱된 이벤트 조회
        
        Args:
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            이벤트 리스트
        """
        try:
            db_service = await get_db_service()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text(f"SELECT * FROM economic_events "
                         f"WHERE event_time >= '{start_date}' "
                         f"AND event_time < '{end_date}' "
                         f"ORDER BY event_time")
                )
                
                events = []
                for row in result.fetchall():
                    events.append({
                        'id': row[0],
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
                        'processed_at': row[13],
                        'created_at': row[14]
                    })
                
                logger.info(f"Loaded {len(events)} cached events from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                return events
                
        except Exception as e:
            logger.error(f"Error loading cached events: {e}")
            return []
    
    async def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """
        다가오는 이벤트 조회
        
        Args:
            days: 조회할 일수 (기본값: 30일)
            
        Returns:
            이벤트 리스트
        """
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today + timedelta(days=days)
            
            events = await self.get_cached_events(today, end_date)
            
            # 중요도 순으로 정렬 (★★★ 먼저)
            events.sort(key=lambda x: x['importance'], reverse=True)
            
            return events
            
        except Exception as e:
            logger.error(f"Error loading upcoming events: {e}")
            return []
    
    async def get_today_events(self) -> List[Dict]:
        """
        오늘의 이벤트 조회
        
        Returns:
            오늘의 이벤트 리스트
        """
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            events = await self.get_cached_events(today, tomorrow)
            
            return events
            
        except Exception as e:
            logger.error(f"Error loading today's events: {e}")
            return []
    
    async def get_monthly_events(self, year: int, month: int) -> List[Dict]:
        """
        월별 이벤트 조회
        
        Args:
            year: 연도
            month: 월
            
        Returns:
            해당 월의 이벤트 리스트
        """
        try:
            start_date = datetime(year, month, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            
            if month == 12:
                end_date = datetime(year + 1, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                end_date = datetime(year, month + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            
            events = await self.get_cached_events(start_date, end_date)
            
            return events
            
        except Exception as e:
            logger.error(f"Error loading monthly events: {e}")
            return []


async def main():
    """메인 함수 - 테스트용"""
    manager = EconomicCalendarManager()
    
    print("=" * 60)
    print("Economic Calendar Manager Test")
    print("=" * 60)
    print()
    
    # 1년치 데이터 초기화
    print("1. Initializing calendar (1 year data)...")
    init_result = await manager.initialize_calendar()
    print(f"   Result: {init_result['message']}")
    print()
    
    # 주간 업데이트
    print("2. Updating calendar (weekly update)...")
    update_result = await manager.update_calendar()
    print(f"   Result: {update_result['message']}")
    print()
    
    # 다가오는 이벤트 조회
    print("3. Loading upcoming events (30 days)...")
    upcoming_events = await manager.get_upcoming_events(days=30)
    print(f"   Found {len(upcoming_events)} upcoming events")
    print()
    
    if upcoming_events:
        print("Upcoming Economic Events (Top 10):")
        print("-" * 60)
        for event in upcoming_events[:10]:
            importance_stars = '★' * event['importance']
            print(f"{importance_stars} {event['event_name']}")
            print(f"  Time: {event['event_time']}")
            if event['actual']:
                print(f"  Actual: {event['actual']}")
            if event['previous']:
                print(f"  Previous: {event['previous']}")
            if event['surprise_pct'] is not None:
                print(f"  Surprise: {event['surprise_pct']:.2f}%")
                print(f"  Impact: {event['impact_direction']} (Score: {event['impact_score']})")
            print()


if __name__ == "__main__":
    asyncio.run(main())
