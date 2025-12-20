"""
Screener Scheduler

매일 정해진 시간에 Dynamic Screener 실행
- Pre-Market: 08:00 EST (종목 선정)
- Mid-Day: 12:00 EST (재스캔)
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Callable, Awaitable, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from .scanner import DynamicScreener, ScanResult, ScreenerCandidate

logger = logging.getLogger(__name__)

# 동부 표준시
EST = pytz.timezone("America/New_York")


class ScreenerScheduler:
    """
    Dynamic Screener 스케줄러
    
    스케줄러 실행 시간:
    - Pre-Market: 08:00 EST (주요 스캔)
    - Mid-Day: 12:00 EST (추가 스캔)
    
    결과는 Redis에 캐싱하고 콜백으로 알림 가능
    """
    
    def __init__(
        self,
        screener: DynamicScreener = None,
        on_scan_complete: Callable[[ScanResult], Awaitable[None]] = None,
        redis_client=None,
    ):
        self.screener = screener or DynamicScreener()
        self.on_scan_complete = on_scan_complete
        self.redis_client = redis_client
        
        self.scheduler = AsyncIOScheduler(timezone=EST)
        self.is_running = False
        
        # 스캔 결과 저장
        self.latest_results: Optional[ScanResult] = None
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중")
            return
        
        # Pre-Market 스캔 (08:00 EST, 월-금)
        self.scheduler.add_job(
            self._run_scan,
            CronTrigger(hour=8, minute=0, day_of_week="mon-fri"),
            id="premarket_scan",
            name="Pre-Market Scan",
            kwargs={"scan_type": "premarket"},
        )
        
        # Mid-Day 스캔 (12:00 EST, 월-금)
        self.scheduler.add_job(
            self._run_scan,
            CronTrigger(hour=12, minute=0, day_of_week="mon-fri"),
            id="midday_scan",
            name="Mid-Day Scan",
            kwargs={"scan_type": "midday"},
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("스캐너 스케줄러 시작됨")
        logger.info("  - Pre-Market: 08:00 EST (월-금)")
        logger.info("  - Mid-Day: 12:00 EST (월-금)")
    
    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("스캐너 스케줄러 중지됨")
    
    async def _run_scan(self, scan_type: str = "manual"):
        """
        스캔 실행
        
        Args:
            scan_type: premarket, midday, manual
        """
        logger.info(f"스캔 시작: {scan_type}")
        
        try:
            result = await self.screener.scan()
            self.latest_results = result
            
            logger.info(f"스캔 완료: {len(result.candidates)}개 후보 선정")
            
            # Redis에 캐싱
            if self.redis_client:
                await self._cache_results(result, scan_type)
            
            # 콜백 호출
            if self.on_scan_complete:
                await self.on_scan_complete(result)
            
            return result
            
        except Exception as e:
            logger.error(f"스캔 실패: {e}")
            raise
    
    async def _cache_results(self, result: ScanResult, scan_type: str):
        """Redis에 결과 캐싱"""
        try:
            import json
            
            key = f"screener:{scan_type}:{datetime.now().strftime('%Y%m%d')}"
            
            data = {
                "timestamp": result.timestamp.isoformat(),
                "total_scanned": result.total_scanned,
                "candidates": [
                    self.screener.to_dict(c) for c in result.candidates
                ],
                "scan_duration": result.scan_duration_seconds,
            }
            
            await self.redis_client.set(
                key,
                json.dumps(data),
                ex=86400,  # 24시간 TTL
            )
            
            logger.info(f"결과 캐싱: {key}")
            
        except Exception as e:
            logger.error(f"캐싱 실패: {e}")
    
    async def run_now(self) -> ScanResult:
        """즉시 스캔 실행 (수동)"""
        return await self._run_scan(scan_type="manual")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """다음 스캔 예정 시간"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_run = min(job.next_run_time for job in jobs if job.next_run_time)
            return next_run
        return None
    
    def get_latest_results(self) -> Optional[ScanResult]:
        """최신 스캔 결과"""
        return self.latest_results
    
    def get_latest_candidates(self) -> List[ScreenerCandidate]:
        """최신 후보 종목 리스트"""
        if self.latest_results:
            return self.latest_results.candidates
        return []


# 전역 스케줄러 인스턴스
_scheduler_instance: Optional[ScreenerScheduler] = None


def get_scheduler(screener: DynamicScreener = None) -> ScreenerScheduler:
    """스케줄러 싱글톤 가져오기"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScreenerScheduler(screener=screener)
    return _scheduler_instance


def start_scheduler():
    """전역 스케줄러 시작"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """전역 스케줄러 중지"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
