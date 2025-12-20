"""
Forex Factory 스크래퍼
경제 지표를 가장 빠르게 수집 (발표 후 20초-1분!)
"""
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


class ForexFactoryScraper:
    """
    Forex Factory 경제 캘린더 스크래퍼
    
    장점:
    - 가장 빠른 업데이트 (발표 후 20초-1분!)
    - 무료
    - 모든 주요 경제 지표 포함
    
    단점:
    - 웹 스크래핑 (HTML 변경 시 수정 필요)
    - Rate limit 주의
    """
    
    BASE_URL = "https://www.forexfactory.com"
    CALENDAR_URL = f"{BASE_URL}/calendar"
    
    # User-Agent (봇 차단 방지)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    async def get_latest_result(self, event_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 이벤트의 최신 결과 가져오기
        
        Args:
            event_name: 이벤트 이름 (e.g., "CPI", "GDP", "NFP")
        
        Returns:
            {
                'actual': 실제값,
                'forecast': 예상값,
                'previous': 이전값,
                'time': 발표 시각,
                'unit': 단위
            }
        """
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                async with session.get(self.CALENDAR_URL) as resp:
                    if resp.status != 200:
                        logger.error(f"Forex Factory returned {resp.status}")
                        return None
                    
                    html = await resp.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 캘린더 행 찾기
            calendar_rows = soup.find_all('tr', class_='calendar__row')
            
            for row in calendar_rows:
                # 이벤트 이름 추출
                event_elem = row.find('span', class_='calendar__event-title')
                if not event_elem:
                    continue
                
                row_event_name = event_elem.text.strip()
                
                # 이벤트 이름 매칭 (부분 매칭)
                if not self._match_event_name(event_name, row_event_name):
                    continue
                
                # 실제값 추출
                actual_elem = row.find('span', class_='calendar__actual')
                if not actual_elem or not actual_elem.text.strip():
                    continue  # 아직 발표 안 됨
                
                actual_text = actual_elem.text.strip()
                
                # 예상값
                forecast_elem = row.find('span', class_='calendar__forecast')
                forecast_text = forecast_elem.text.strip() if forecast_elem else None
                
                # 이전값
                previous_elem = row.find('span', class_='calendar__previous')
                previous_text = previous_elem.text.strip() if previous_elem else None
                
                # 시간
                time_elem = row.find('td', class_='calendar__time')
                time_text = time_elem.text.strip() if time_elem else None
                
                # 숫자로 변환
                actual = self._parse_value(actual_text)
                forecast = self._parse_value(forecast_text) if forecast_text else None
                previous = self._parse_value(previous_text) if previous_text else None
                
                if actual is None:
                    continue
                
                # 시간 파싱
                event_time = self._parse_time(time_text) if time_text else datetime.now()
                
                return {
                    'actual': actual,
                    'forecast': forecast,
                    'previous': previous,
                    'time': event_time,
                    'unit': self._extract_unit(actual_text),
                    'event_name': row_event_name
                }
        
        except Exception as e:
            logger.error(f"Forex Factory scraping error: {e}", exc_info=True)
        
        return None
    
    async def get_upcoming_events(
        self, 
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """
        향후 N시간 내 예정된 이벤트 목록
        
        Returns:
            이벤트 딕셔너리 리스트
        """
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                async with session.get(self.CALENDAR_URL) as resp:
                    if resp.status != 200:
                        return []
                    
                    html = await resp.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            events = []
            cutoff = datetime.now() + timedelta(hours=hours_ahead)
            
            calendar_rows = soup.find_all('tr', class_='calendar__row')
            
            for row in calendar_rows:
                # 이벤트 이름
                event_elem = row.find('span', class_='calendar__event-title')
                if not event_elem:
                    continue
                
                event_name = event_elem.text.strip()
                
                # 시간
                time_elem = row.find('td', class_='calendar__time')
                if not time_elem:
                    continue
                
                time_text = time_elem.text.strip()
                event_time = self._parse_time(time_text)
                
                # 향후 이벤트만
                if event_time > cutoff:
                    continue
                
                # 중요도 (별표)
                impact_elem = row.find('span', class_='calendar__impact')
                importance = self._parse_importance(impact_elem)
                
                # 예상값
                forecast_elem = row.find('span', class_='calendar__forecast')
                forecast_text = forecast_elem.text.strip() if forecast_elem else None
                forecast = self._parse_value(forecast_text) if forecast_text else None
                
                events.append({
                    'event_name': event_name,
                    'scheduled_at': event_time,
                    'importance': importance,
                    'forecast': forecast,
                    'source': 'ForexFactory'
                })
            
            return events
        
        except Exception as e:
            logger.error(f"Forex Factory upcoming events error: {e}")
            return []
    
    def _match_event_name(self, target: str, candidate: str) -> bool:
        """이벤트 이름 매칭 (유연한 매칭)"""
        target_lower = target.lower()
        candidate_lower = candidate.lower()
        
        # 정확히 일치
        if target_lower == candidate_lower:
            return True
        
        # 부분 매칭
        if target_lower in candidate_lower:
            return True
        
        # 약어 매칭
        abbreviations = {
            'cpi': 'consumer price index',
            'ppi': 'producer price index',
            'gdp': 'gross domestic product',
            'nfp': 'non-farm payrolls',
            'pmi': 'purchasing managers index',
        }
        
        if target_lower in abbreviations:
            if abbreviations[target_lower] in candidate_lower:
                return True
        
        return False
    
    def _parse_value(self, text: str) -> Optional[float]:
        """텍스트에서 숫자 추출"""
        if not text:
            return None
        
        try:
            # 숫자와 소수점, 음수 부호만 추출
            cleaned = re.sub(r'[^0-9.\-]', '', text)
            
            if not cleaned or cleaned == '-':
                return None
            
            return float(cleaned)
        
        except ValueError:
            return None
    
    def _extract_unit(self, text: str) -> str:
        """단위 추출 (%, K, M, B 등)"""
        if '%' in text:
            return '%'
        elif 'K' in text:
            return 'K'
        elif 'M' in text:
            return 'M'
        elif 'B' in text:
            return 'B'
        return ''
    
    def _parse_time(self, time_text: str) -> datetime:
        """시간 텍스트 파싱"""
        # Forex Factory 시간 형식: "12:30am" 또는 "All Day"
        if not time_text or time_text.lower() == 'all day':
            return datetime.now().replace(hour=0, minute=0, second=0)
        
        try:
            # "12:30pm" 형식
            time_obj = datetime.strptime(time_text.lower(), '%I:%M%p')
            
            # 오늘 날짜로 설정
            now = datetime.now()
            return now.replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=0,
                microsecond=0
            )
        
        except ValueError:
            return datetime.now()
    
    def _parse_importance(self, impact_elem) -> int:
        """중요도 파싱 (1=최고, 5=낮음)"""
        if not impact_elem:
            return 3
        
        # Forex Factory는 색상으로 표시
        # red = high (1), orange = medium (3), yellow = low (5)
        impact_class = impact_elem.get('class', [])
        
        if 'high' in impact_class or 'red' in ' '.join(impact_class):
            return 1
        elif 'medium' in impact_class or 'orange' in ' '.join(impact_class):
            return 3
        else:
            return 5
