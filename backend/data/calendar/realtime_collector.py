"""
실시간 이벤트 결과 수집기
다층 폴링 전략으로 최대한 빠르게 결과 수집
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RealtimeEventCollector:
    """
    실시간 이벤트 결과 수집기
    
    전략:
    - T-15분: 5분마다 체크 (준비)
    - T-5분: 1분마다 체크 (대기)
    - T-0분: 10초마다 체크 (발표!) ⚡
    - T+5분: 30초마다 체크
    - T+30분: 종료
    """
    
    def __init__(self, db_session, collectors: dict):
        self.db = db_session
        self.collectors = collectors  # {source_name: collector_instance}
        self.active_watches = {}  # event_id -> asyncio.Task
    
    async def start_watching(self, event: Dict[str, Any]):
        """
        이벤트 감시 시작
        
        Args:
            event: economic_calendar_events 레코드
        """
        event_id = event['id']
        
        # 이미 감시 중이면 스킵
        if event_id in self.active_watches:
            logger.info(f"Already watching event {event_id}")
            return
        
        # 비동기 태스크 시작
        task = asyncio.create_task(self._watch_event(event))
        self.active_watches[event_id] = task
        
        logger.info(f"⏰ Started watching: {event['event_name']} at {event['scheduled_at']}")
    
    async def _watch_event(self, event: Dict[str, Any]):
        """이벤트를 실시간으로 감시"""
        event_id = event['id']
        event_name = event['event_name']
        event_time = event['scheduled_at']
        event_type = event['event_type']
        
        try:
            while True:
                now = datetime.now(tz=event_time.tzinfo)
                time_diff = (event_time - now).total_seconds()
                
                # 종료 조건: T+10분 경과 (3분 집중 모니터링 + 7분 여유)
                if time_diff < -600:  # 10분 지남
                    logger.info(f"⏱️ Watch timeout for {event_name} (10min)")
                    break
                
                # T-15분이 되기 전에는 대기
                if time_diff > 900:
                    await asyncio.sleep(300)  # 5분 대기
                    continue
                
                # 폴링 간격 결정
                interval = self._get_polling_interval(time_diff)
                
                # 로그
                if time_diff > 0:
                    logger.debug(f"⏳ T-{int(time_diff/60)}m for {event_name}, polling every {interval}s")
                else:
                    logger.debug(f"⚡ T+{int(abs(time_diff)/60)}m for {event_name}, polling every {interval}s")
                
                # 결과 체크
                result = await self._fetch_result(event_type, event)
                
                if result:
                    logger.info(f"✅ Result found for {event_name}! ⚡")
                    
                    # DB에 저장
                    await self._store_result(event_id, result)
                    
                    # 알림 발송
                    await self._notify_result(event, result)
                    
                    break
                
                # 다음 폴링까지 대기
                await asyncio.sleep(interval)
        
        except Exception as e:
            logger.error(f"Error watching {event_name}: {e}", exc_info=True)
        
        finally:
            # 완료 후 제거
            if event_id in self.active_watches:
                del self.active_watches[event_id]
    
    def _get_polling_interval(self, time_diff_seconds: float) -> int:
        """
        시간 차이에 따른 폴링 간격 결정
        
        전략 (Forex Factory bot 차단 회피):
        - 발표 후 3분까지만 집중 모니터링
        - 이후에는 5분 간격으로 느리게 (rate limit 회피)
        
        Returns:
            초 단위 폴링 간격
        """
        # 발표 후 3분 경과 시 5분 간격으로 변경 (bot 차단 회피)
        if time_diff_seconds < -180:  # T+3분 이후
            return 300  # 5분마다 (느리게)
        
        # 집중 모니터링 구간 (발표 전후 3분)
        elif time_diff_seconds < 0:  # T ~ T+3분 (발표 직후)
            return 30   # 30초마다 ⚡
        elif time_diff_seconds < 180:  # T-3분 ~ T (발표 직전)
            return 10   # 10초마다 ⚡⚡⚡ (가장 집중!)
        elif time_diff_seconds < 300:  # T-5분 ~ T-3분
            return 30   # 30초마다
        elif time_diff_seconds < 900:  # T-15분 ~ T-5분
            return 60   # 1분마다
        else:  # T-15분 이전
            return 300  # 5분마다
    
    async def _fetch_result(
        self, 
        event_type: str, 
        event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        이벤트 타입별 최적 API 사용하여 결과 가져오기
        
        Returns:
            결과 딕셔너리 또는 None
        """
        
        if event_type == 'EARNINGS':
            # 실적: FMP (가장 빠름, 2-5분)
            result = await self._fetch_from_fmp_earnings(event)
            if result:
                return result
            
            # Fallback: Finnhub
            if 'finnhub' in self.collectors:
                result = await self._fetch_from_finnhub(event)
                if result:
                    return result
        
        elif event_type in ['CPI', 'GDP', 'NFP', 'UNEMPLOYMENT']:
            # 경제 지표: Forex Factory (가장 빠름, 20초-1분!)
            result = await self._fetch_from_forex_factory(event)
            if result:
                return result
            
            # Fallback: FMP
            result = await self._fetch_from_fmp_economic(event)
            if result:
                return result
        
        elif event_type == 'FED_SPEECH':
            # 연준 발언: YouTube Live (실시간)
            if event.get('live_stream_url'):
                result = await self._fetch_from_youtube_live(event)
                if result:
                    return result
            
            # Fallback: Twitter/뉴스
            result = await self._fetch_from_news(event)
            if result:
                return result
        
        elif event_type == 'FOMC':
            # FOMC: Federal Reserve 공식 (즉시)
            result = await self._fetch_from_fed_official(event)
            if result:
                return result
        
        return None
    
    async def _fetch_from_fmp_earnings(self, event: Dict) -> Optional[Dict]:
        """FMP에서 실적 결과 가져오기"""
        if 'fmp' not in self.collectors:
            return None
        
        try:
            ticker = event.get('ticker')
            if not ticker:
                return None
            
            result = await self.collectors['fmp'].get_earnings_surprise(ticker)
            
            if result and result.get('actual_eps') is not None:
                return {
                    'actual_value': {
                        'eps': result['actual_eps'],
                        'revenue': result.get('actual_revenue'),
                    },
                    'consensus_estimate': event.get('consensus_estimate', {}),
                    'beat_consensus': result.get('actual_eps', 0) > result.get('estimated_eps', 0),
                    'surprise_percent': (
                        (result['actual_eps'] - result.get('estimated_eps', 0)) / 
                        result.get('estimated_eps', 1) * 100
                    ) if result.get('estimated_eps') else None,
                    'data_source': 'FMP',
                    'result_announced_at': datetime.now()
                }
        
        except Exception as e:
            logger.error(f"FMP earnings fetch error: {e}")
        
        return None
    
    async def _fetch_from_forex_factory(self, event: Dict) -> Optional[Dict]:
        """Forex Factory에서 경제 지표 결과 가져오기 (가장 빠름!)"""
        if 'forex_factory' not in self.collectors:
            return None
        
        try:
            event_name = event['event_name']
            result = await self.collectors['forex_factory'].get_latest_result(event_name)
            
            if result and result.get('actual') is not None:
                return {
                    'actual_value': {
                        'value': result['actual'],
                        'unit': result.get('unit', '')
                    },
                    'consensus_estimate': event.get('consensus_estimate', {}),
                    'beat_consensus': result.get('actual', 0) > result.get('forecast', 0),
                    'surprise_percent': (
                        (result['actual'] - result.get('forecast', 0)) / 
                        result.get('forecast', 1) * 100
                    ) if result.get('forecast') else None,
                    'data_source': 'ForexFactory',
                    'result_announced_at': result.get('time', datetime.now())
                }
        
        except Exception as e:
            logger.error(f"Forex Factory fetch error: {e}")
        
        return None
    
    async def _fetch_from_fmp_economic(self, event: Dict) -> Optional[Dict]:
        """FMP에서 경제 지표 가져오기"""
        # FMP economic calendar API 사용
        # 구현 예정
        return None
    
    async def _fetch_from_youtube_live(self, event: Dict) -> Optional[Dict]:
        """YouTube Live에서 연준 발언 가져오기"""
        # YouTube Transcript API 사용
        # 구현 예정
        return None
    
    async def _fetch_from_news(self, event: Dict) -> Optional[Dict]:
        """뉴스에서 이벤트 결과 가져오기"""
        if 'google_news' not in self.collectors:
            return None
        
        try:
            event_name = event['event_name']
            
            # Fed 발언인 경우
            if event.get('event_type') == 'FED_SPEECH':
                # 의원 이름 추출 (예: "Williams" from "John Williams - NY Fed President Speech")
                official_name = event_name.split()[0]
                
                result = await self.collectors['google_news'].search_fed_speech(
                    official_name=official_name,
                    speech_topic=event.get('speech_topic')
                )
                
                if result:
                    return {
                        'actual_value': {
                            'title': result['title'],
                            'summary': result.get('description', ''),
                            'link': result['link']
                        },
                        'data_source': 'GoogleNews',
                        'result_announced_at': result['published_at']
                    }
            
            # 경제 지표인 경우
            elif event.get('event_type') in ['CPI', 'GDP', 'NFP', 'UNEMPLOYMENT']:
                articles = await self.collectors['google_news'].search_economic_event(
                    event_name
                )
                
                if articles:
                    latest = articles[0]
                    return {
                        'actual_value': {
                            'title': latest['title'],
                            'summary': latest.get('description', ''),
                            'link': latest['link']
                        },
                        'data_source': 'GoogleNews',
                        'result_announced_at': latest['published_at']
                    }
        
        except Exception as e:
            logger.error(f"Google News fetch error: {e}")
        
        return None
    
    async def _fetch_from_fed_official(self, event: Dict) -> Optional[Dict]:
        """Federal Reserve 공식 사이트에서 FOMC 결정 가져오기"""
        # Fed RSS 또는 공식 API 사용
        # 구현 예정
        return None
    
    async def _store_result(self, event_id: int, result: Dict[str, Any]):
        """결과를 DB에 저장"""
        try:
            await self.db.execute(
                """
                INSERT INTO economic_event_results (
                    event_id,
                    actual_value,
                    beat_consensus,
                    surprise_percent,
                    data_source,
                    result_announced_at,
                    data_collected_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                event_id,
                result['actual_value'],
                result.get('beat_consensus'),
                result.get('surprise_percent'),
                result['data_source'],
                result.get('result_announced_at')
            )
            
            logger.info(f"✅ Stored result for event {event_id}")
        
        except Exception as e:
            logger.error(f"Failed to store result: {e}", exc_info=True)
    
    async def _notify_result(self, event: Dict, result: Dict):
        """결과 알림 발송 (Telegram 등)"""
        # Telegram 알림 구현 예정
        logger.info(f"📢 Notification: {event['event_name']} result received")
    
    async def schedule_upcoming_events(self):
        """
        향후 24시간 내 이벤트를 자동으로 감시 예약
        """
        cutoff = datetime.now() + timedelta(hours=24)
        
        events = await self.db.fetch(
            """
            SELECT * FROM economic_calendar_events
            WHERE scheduled_at BETWEEN NOW() AND $1
            AND id NOT IN (
                SELECT event_id FROM economic_event_results
            )
            ORDER BY scheduled_at
            """,
            cutoff
        )
        
        logger.info(f"📅 Scheduling {len(events)} events for next 24 hours")
        
        for event in events:
            await self.start_watching(dict(event))
    
    async def stop_all_watches(self):
        """모든 감시 중지"""
        for task in self.active_watches.values():
            task.cancel()
        
        self.active_watches.clear()
        logger.info("🛑 Stopped all event watches")
