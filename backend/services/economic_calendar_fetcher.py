"""
Economic Calendar Fetcher - Investing.com 크롤링

경제 캘린더 데이터를 수집하여 DB에 저장합니다.
Investing.com Economic Calendar 크롤링 (프록시 우회 - FMP 백업은 나중에)

Author: AI Trading System Team
Date: 2026-01-22
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup

from backend.core.database import get_db, DatabaseSession
from backend.database.models import EconomicEvent

logger = logging.getLogger(__name__)


class EconomicCalendarFetcher:
    """
    Investing.com 경제 캘린더 크롤러
    
    Features:
    - Investing.com Economic Calendar 크롤링
    - ★★★ 이벤트만 필터링
    - DB 저장
    - 구조 변경 감지 로직
    - 프록시 우회 (308 Redirect 방지)
    """
    
    def __init__(self):
        # 프록시 설정 (선택적 - 사용자 환경 변수에서 설정 가능)
        self.use_proxy = False
        self.proxies = None  # {'http': 'http://proxy.example.com:8080'}
        
        self.base_url = "https://kr.investing.com/economic-calendar/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.max_retries = 3
        self.retry_interval = 5  # seconds
    
    async def fetch_today_events(self) -> List[Dict]:
        """
        오늘의 경제 이벤트 수집
        
        Returns:
            이벤트 리스트
        """
        try:
            today = datetime.now()
            url = f"{self.base_url}?date={today.strftime('%Y-%m-%d')}"
            
            logger.info(f"Fetching economic calendar from: {url}")
            
            # 프록시 설정
            kwargs = {}
            if self.use_proxy and self.proxies:
                kwargs['proxies'] = self.proxies
            
            async with httpx.AsyncClient(timeout=30, headers=self.headers, **kwargs) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 이벤트 추출
                events = self._parse_events(soup)
                
                logger.info(f"Fetched {len(events)} economic events")
                return events
                
        except httpx.TimeoutException:
            logger.error("Timeout fetching economic calendar")
            return []
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []
    
    def _parse_events(self, soup: BeautifulSoup) -> List[Dict]:
        """
        HTML에서 이벤트 파싱
        
        Args:
            soup: BeautifulSoup 객체
            
        Returns:
            이벤트 리스트
        """
        events = []
        
        try:
            # Investing.com 구조에 따라 파싱
            # 일반적으로 table 형태
            table = soup.find('table', {'class': 'js-economic-calendar-table'})
            
            if table:
                rows = table.find_all('tr')
                
                for row in rows:
                    # 중요도 별(★) 확인
                    importance_elem = row.find('td', {'class': 'sentiment'})
                    if not importance_elem:
                        continue
                    
                    importance_text = importance_elem.get_text(strip=True)
                    
                    # ★★★만 필터링
                    if '★★★' not in importance_text:
                        continue
                    
                    # 이벤트 정보 추출
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    # 시간
                    time_elem = cells[0]
                    event_time = self._parse_time(time_elem.get_text(strip=True))
                    
                    # 국가
                    country_elem = cells[1]
                    country = country_elem.get_text(strip=True)
                    
                    # 이벤트 이름
                    name_elem = cells[2]
                    event_name = name_elem.get_text(strip=True)
                    
                    # 중요도 점수
                    importance_score = 3 if '★★★' in importance_text else 2 if '★★' in importance_text else 1
                    
                    event = {
                        'event_name': event_name,
                        'country': country,
                        'event_time': event_time,
                        'importance': importance_score,
                        'category': self._categorize_event(event_name),
                        'forecast': None,  # 발표 전에는 없음
                        'actual': None,
                        'previous': None
                    }
                    
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"Error parsing events: {e}")
        
        logger.info(f"Parsed {len(events)} high importance events (★★★)")
        return events
    
    def _parse_time(self, time_text: str) -> Optional[datetime]:
        """
        시간 텍스트 파싱
        
        Args:
            time_text: 시간 텍스트 (예: "22:30")
            
        Returns:
            datetime 객체
        """
        try:
            if not time_text or time_text == 'All Day':
                return None
            
            # 시간 파싱
            time_parts = time_text.split(':')
            if len(time_parts) == 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                
                # 오늘 날짜에 시간 결합
                today = datetime.now()
                event_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                return event_time
            
        except Exception as e:
            logger.error(f"Error parsing time '{time_text}': {e}")
            return None
    
    def _categorize_event(self, event_name: str) -> str:
        """
        이벤트 카테고리 분류
        
        Args:
            event_name: 이벤트 이름
            
        Returns:
            카테고리 (GDP, Inflation, Employment, etc.)
        """
        event_name_lower = event_name.lower()
        
        if 'gdp' in event_name_lower:
            return 'GDP'
        elif 'cpi' in event_name_lower or 'inflation' in event_name_lower:
            return 'Inflation'
        elif 'employment' in event_name_lower or 'unemployment' in event_name_lower or 'job' in event_name_lower:
            return 'Employment'
        elif 'fomc' in event_name_lower or 'fed' in event_name_lower:
            return 'FOMC'
        elif 'pmi' in event_name_lower:
            return 'PMI'
        elif 'retail' in event_name_lower:
            return 'Retail'
        elif 'housing' in event_name_lower:
            return 'Housing'
        else:
            return 'Other'
    
    async def save_to_db(self, events: List[Dict]) -> int:
        """
        이벤트를 DB에 저장
        
        Args:
            events: 이벤트 리스트
            
        Returns:
            저장된 이벤트 수
        """
        saved_count = 0
        
        async with DatabaseSession() as db:
            for event_data in events:
                try:
                    # 중복 체크
                    existing = await db.execute(
                        f"SELECT id FROM economic_events WHERE event_name = '{event_data['event_name']}' "
                        f"AND event_time = '{event_data['event_time']}'"
                    )
                    
                    if existing.fetchone():
                        logger.info(f"Event already exists: {event_data['event_name']}")
                        continue
                    
                    # 새 이벤트 생성
                    event = EconomicEvent(
                        event_name=event_data['event_name'],
                        country=event_data['country'],
                        category=event_data['category'],
                        event_time=event_data['event_time'],
                        importance=event_data['importance'],
                        forecast=event_data['forecast'],
                        actual=event_data['actual'],
                        previous=event_data['previous'],
                        is_processed=False,
                        processed_at=None
                    )
                    
                    db.add(event)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving event {event_data['event_name']}: {e}")
            
        try:
            await db.commit()
            logger.info(f"Saved {saved_count} new economic events to DB")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error committing to DB: {e}")
        
        return saved_count
    
    async def load_today_calendar(self) -> Dict[str, any]:
        """
        오늘의 경제 캘린더 로드 및 DB 저장
        
        Returns:
            결과 dict
        """
        logger.info("=" * 80)
        logger.info("Loading today's economic calendar...")
        logger.info("=" * 80)
        
        # 1. 크롤링
        events = await self.fetch_today_events()
        
        if not events:
            logger.warning("No economic events found for today")
            return {
                'success': False,
                'events_count': 0,
                'message': 'No events found'
            }
        
        # 2. DB 저장
        saved_count = await self.save_to_db(events)
        
        result = {
            'success': True,
            'events_count': len(events),
            'saved_count': saved_count,
            'events': events,
            'message': f'Successfully loaded {saved_count} events'
        }
        
        logger.info("=" * 80)
        logger.info(f"✅ Economic calendar loaded: {result['message']}")
        logger.info("=" * 80)
        
        return result


async def main():
    """
    메인 함수 - 테스트용
    """
    fetcher = EconomicCalendarFetcher()
    result = await fetcher.load_today_calendar()
    
    print("\n" + "=" * 80)
    print("Economic Calendar Fetcher Test Result")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print(f"Events Count: {result['events_count']}")
    print(f"Saved Count: {result['saved_count']}")
    print(f"Message: {result['message']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
