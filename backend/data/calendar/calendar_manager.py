"""
경제 캘린더 통합 관리자
실시간 수집기와 여러 수집기를 통합 관리
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from .realtime_collector import RealtimeEventCollector
from .forex_factory_scraper import ForexFactoryScraper
from .fmp_collector import FMPCollector

logger = logging.getLogger(__name__)


class EconomicCalendarManager:
    """
    경제 캘린더 통합 관리자
    
    역할:
    1. 여러 소스에서 이벤트 수집
    2. 실시간 결과 감시 시작
    3. DB에 저장
    """
    
    def __init__(self, db_session, settings):
        self.db = db_session
        self.settings = settings
        
        # 수집기 초기화
        self.collectors = {
            'forex_factory': ForexFactoryScraper(),
            'fmp': FMPCollector(api_key=settings.FMP_API_KEY) if hasattr(settings, 'FMP_API_KEY') else None,
        }
        
        # 실시간 수집기
        self.realtime_collector = RealtimeEventCollector(
            db_session=db_session,
            collectors=self.collectors
        )
    
    async def update_calendar(self, days_ahead: int = 90) -> Dict[str, int]:
        """
        경제 캘린더 업데이트 (여러 소스에서)
        
        Returns:
            통계: {"collected": X, "updated": Y}
        """
        logger.info(f"📅 Updating calendar for next {days_ahead} days")
        
        stats = {
            "collected": 0,
            "updated": 0,
            "skipped": 0
        }
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        # 1. FMP에서 실적 캘린더 수집
        if self.collectors['fmp']:
            fmp_events = await self.collectors['fmp'].get_earnings_calendar(
                start_date, end_date
            )
            logger.info(f"  FMP: {len(fmp_events)} earnings events")
            
            for event in fmp_events:
                if await self._store_or_update_event(event):
                    stats["collected"] += 1
                else:
                    stats["updated"] += 1
        
        # 2. FMP에서 경제 캘린더 수집
        if self.collectors['fmp']:
            fmp_econ = await self.collectors['fmp'].get_economic_calendar()
            logger.info(f"  FMP: {len(fmp_econ)} economic events")
            
            for event in fmp_econ:
                if await self._store_or_update_event(event):
                    stats["collected"] += 1
                else:
                    stats["updated"] += 1
        
        # 3. Forex Factory에서 예정 이벤트 수집
        ff_events = await self.collectors['forex_factory'].get_upcoming_events(
            hours_ahead=24
        )
        logger.info(f"  Forex Factory: {len(ff_events)} events (24h)")
        
        for event in ff_events:
            if await self._store_or_update_event(event):
                stats["collected"] += 1
            else:
                stats["skipped"] += 1  # Forex Factory는 업데이트 안 함
        
        logger.info(f"✅ Calendar update complete: {stats}")
        
        return stats
    
    async def _store_or_update_event(self, event: Dict[str, Any]) -> bool:
        """
        이벤트 저장 또는 업데이트
        
        Returns:
            True if new event created, False if updated
        """
        try:
            # 중복 체크 (같은 날짜 + 같은 이벤트명)
            existing = await self.db.fetchrow(
                """
                SELECT id FROM economic_calendar_events
                WHERE event_name = $1
                AND DATE(scheduled_at) = DATE($2::timestamptz)
                AND event_type = $3
                """,
                event['event_name'],
                event['scheduled_at'],
                event.get('event_type', 'ECONOMIC_INDICATOR')
            )
            
            if existing:
                # 업데이트
                await self.db.execute(
                    """
                    UPDATE economic_calendar_events
                    SET consensus_estimate = $1,
                        importance = $2,
                        updated_at = NOW()
                    WHERE id = $3
                    """,
                    event.get('consensus_estimate'),
                    event.get('importance', 3),
                    existing['id']
                )
                return False
            else:
                # 신규 생성
                await self.db.execute(
                    """
                    INSERT INTO economic_calendar_events (
                        event_name,
                        event_type,
                        ticker,
                        scheduled_at,
                        fiscal_quarter,
                        importance,
                        consensus_estimate,
                        data_source,
                        expected_news_burst
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    event['event_name'],
                    event.get('event_type', 'ECONOMIC_INDICATOR'),
                    event.get('ticker'),
                    event['scheduled_at'],
                    event.get('fiscal_quarter'),
                    event.get('importance', 3),
                    event.get('consensus_estimate'),
                    event.get('data_source', 'Unknown'),
                    True
                )
                return True
        
        except Exception as e:
            logger.error(f"Failed to store event: {e}")
            return False
    
    async def start_realtime_monitoring(self):
        """
        향후 24시간 내 이벤트의 실시간 모니터링 시작
        """
        logger.info("🚀 Starting realtime event monitoring")
        
        await self.realtime_collector.schedule_upcoming_events()
    
    async def stop_realtime_monitoring(self):
        """실시간 모니터링 중지"""
        logger.info("🛑 Stopping realtime event monitoring")
        
        await self.realtime_collector.stop_all_watches()
