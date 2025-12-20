"""
KIS Portfolio Auto-Sync Scheduler
주기적으로 KIS 계좌를 자동 동기화

Features:
- 시장 개장 시간에만 동작
- 설정 가능한 동기화 주기 (기본 5분)
- APScheduler 사용
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import logging
import os

from backend.database.repository import get_sync_session
from backend.api.kis_sync_router import sync_kis_portfolio_task

logger = logging.getLogger(__name__)

# 스케줄러 인스턴스
scheduler = BackgroundScheduler()


def is_trading_hours() -> bool:
    """
    현재 미국 주식 시장 거래 시간인지 확인

    US Market Hours (ET):
    - Regular: 9:30 AM - 4:00 PM
    - Pre-market: 4:00 AM - 9:30 AM
    - After-hours: 4:00 PM - 8:00 PM

    한국 시간 (KST = ET + 14시간):
    - Regular: 23:30 - 06:00 (다음날)
    - Extended: 18:00 - 10:00 (다음날)
    """
    now = datetime.now()
    current_hour = now.hour

    # 간단히 오전 6시 ~ 오후 11시는 동기화 중단 (한국 시간 기준)
    # 실제 거래 시간(23:30-06:00)만 동기화
    if 6 <= current_hour < 23:
        return False

    return True


def auto_sync_kis_portfolio():
    """
    자동 KIS 포트폴리오 동기화 작업
    """
    try:
        # 거래 시간 체크
        if not is_trading_hours():
            logger.info("Not trading hours, skipping auto-sync")
            return

        logger.info("Starting scheduled KIS portfolio sync...")

        db = get_sync_session()
        try:
            result = sync_kis_portfolio_task(db)

            if result.get("success"):
                logger.info(
                    f"Auto-sync completed: {result.get('positions_count')} positions"
                )
            else:
                logger.error(f"Auto-sync failed: {result.get('error')}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Auto-sync error: {e}", exc_info=True)


def start_kis_auto_sync(interval_minutes: int = 5):
    """
    KIS 자동 동기화 스케줄러 시작

    Args:
        interval_minutes: 동기화 주기 (분 단위, 기본 5분)
    """
    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    # 주기적 동기화 작업 추가
    scheduler.add_job(
        auto_sync_kis_portfolio,
        'interval',
        minutes=interval_minutes,
        id='kis_auto_sync',
        replace_existing=True,
        next_run_time=datetime.now()  # 즉시 한 번 실행
    )

    # 시작 시 한 번 실행 (장 시간에만)
    scheduler.add_job(
        auto_sync_kis_portfolio,
        'date',
        run_date=datetime.now(),
        id='kis_startup_sync'
    )

    scheduler.start()
    logger.info(f"KIS auto-sync scheduler started (interval: {interval_minutes} min)")


def stop_kis_auto_sync():
    """KIS 자동 동기화 스케줄러 중지"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("KIS auto-sync scheduler stopped")


# 환경 변수에서 설정 읽기
AUTO_SYNC_ENABLED = os.getenv("KIS_AUTO_SYNC_ENABLED", "true").lower() == "true"
AUTO_SYNC_INTERVAL = int(os.getenv("KIS_AUTO_SYNC_INTERVAL", "5"))  # 기본 5분

if AUTO_SYNC_ENABLED:
    # 자동 시작 (import 시)
    start_kis_auto_sync(interval_minutes=AUTO_SYNC_INTERVAL)
