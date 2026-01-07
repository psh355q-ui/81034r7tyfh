"""
Automation Scheduler

시스템 자동화 작업 스케줄러:
- Macro Context 업데이트 (매일 09:00 KST)
- Daily Report 생성 (매일 16:30 KST)
- Weekly Report 생성 (금요일 17:00 KST)
- Price Tracking 검증 (1시간마다)

사용법:
    python backend/automation/scheduler.py

또는 백그라운드 실행:
    nohup python backend/automation/scheduler.py &
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file (override shell variables)
load_dotenv(override=True)

from backend.automation.macro_context_updater import MacroContextUpdater
from backend.automation.price_tracking_verifier import PriceTrackingVerifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomationScheduler:
    """자동화 작업 스케줄러"""

    def __init__(self):
        self.macro_updater = MacroContextUpdater()
        self.price_verifier = PriceTrackingVerifier()

    def setup_schedules(self):
        """스케줄 설정"""

        # 1. Macro Context 업데이트 (매일 09:00 KST)
        schedule.every().day.at("09:00").do(self.run_macro_context_update)
        logger.info("✅ Scheduled: Macro Context Update at 09:00 daily")


        # 2. Daily Report 생성 (매일 07:10 KST - 미국 장 종료 후)
        schedule.every().day.at("07:10").do(self.run_daily_report_generation)
        logger.info("✅ Scheduled: Daily Report Generation at 07:10 daily")

        # 3. Weekly Report 생성 (금요일 17:00 KST)
        schedule.every().friday.at("17:00").do(self.run_weekly_report_generation)
        logger.info("✅ Scheduled: Weekly Report Generation on Fridays at 17:00")

        # 4. Monthly/Quarterly Check (매일 08:00 KST 체크 -> 1일이면 실행)
        schedule.every().day.at("08:00").do(self.run_monthly_check)
        logger.info("✅ Scheduled: Monthly/Quarterly Check at 08:00 daily")

        # 5. Price Tracking 검증 (1시간마다)
        schedule.every().hour.do(self.run_price_tracking_verification)
        logger.info("✅ Scheduled: Price Tracking Verification every hour")

    def run_macro_context_update(self):
        """Macro Context 업데이트 실행"""
        try:
            logger.info("="*60)
            logger.info(f"🕐 Starting Macro Context Update - {datetime.now()}")
            logger.info("="*60)

            snapshot = self.macro_updater.update_daily_snapshot()

            logger.info("="*60)
            logger.info(f"✅ Macro Context Update Complete")
            logger.info(f"   Date: {snapshot.snapshot_date}")
            logger.info(f"   Regime: {snapshot.regime}")
            logger.info(f"   Fed Stance: {snapshot.fed_stance}")
            logger.info(f"   VIX: {snapshot.vix_level} ({snapshot.vix_category})")
            logger.info(f"   Market Sentiment: {snapshot.market_sentiment}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Macro Context Update failed: {e}", exc_info=True)

    def run_daily_report_generation(self):
        """Daily Report 생성 실행"""
        try:
            logger.info("="*60)
            logger.info(f"📊 Starting Daily Report Generation - {datetime.now()}")
            logger.info("="*60)

            from backend.ai.reporters.report_orchestrator import ReportOrchestrator

            async def generate():
                orchestrator = ReportOrchestrator()
                return await orchestrator.generate_daily_briefing()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            filename = loop.run_until_complete(generate())
            loop.close()

            logger.info(f"✅ Daily Report Generated: {filename}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Daily Report Generation failed: {e}", exc_info=True)

    def run_weekly_report_generation(self):
        """Weekly Report 생성 실행"""
        try:
            logger.info("="*60)
            logger.info(f"📊 Starting Weekly Report Generation - {datetime.now()}")
            logger.info("="*60)

            from backend.ai.reporters.weekly_reporter import WeeklyReporter

            async def generate():
                reporter = WeeklyReporter()
                return await reporter.generate_weekly_report()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            filename = loop.run_until_complete(generate())
            loop.close()

            logger.info(f"✅ Weekly Report Generated: {filename}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Weekly Report Generation failed: {e}", exc_info=True)

    def run_monthly_check(self):
        """매일 실행되어 월간/분기 리포트 생성 여부를 확인"""
        today = datetime.now()
        
        # 매월 1일에 월간 리포트 생성 (이전 달 기준)
        if today.day == 1:
            self.run_monthly_report_generation()
            
            # 분기 시작월(1, 4, 7, 10) 1일에 분기 리포트 생성 (이전 분기 기준)
            if today.month in [1, 4, 7, 10]:
                self.run_quarterly_report_generation()

    def run_monthly_report_generation(self):
        """Monthly Report 생성 실행"""
        try:
            logger.info("="*60)
            logger.info(f"📅 Starting Monthly Report Generation - {datetime.now()}")
            logger.info("="*60)

            from backend.ai.reporters.monthly_reporter import MonthlyReporter

            async def generate():
                reporter = MonthlyReporter()
                # 1일이므로 지난 달 데이터를 리포팅 (year, month 자동 계산 로직이 reporter 내부에 있다고 가정하거나 여기서 전달)
                # reporter.generate_monthly_report()가 인자를 받지 않으면 내부에서 '지난 달'을 계산해야 함.
                # 현재 구현된 API는 year, month를 받음. 
                # 따라서 계산해서 넘겨줘야 함.
                today = datetime.now()
                last_month_date = today.replace(day=1) - timedelta(days=1)
                return await reporter.generate_monthly_report(last_month_date.year, last_month_date.month)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            filename = loop.run_until_complete(generate())
            loop.close()

            logger.info(f"✅ Monthly Report Generated: {filename}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Monthly Report Generation failed: {e}", exc_info=True)

    def run_quarterly_report_generation(self):
        """Quarterly Report 생성 실행"""
        try:
            logger.info("="*60)
            logger.info(f"📆 Starting Quarterly Report Generation - {datetime.now()}")
            logger.info("="*60)

            from backend.ai.reporters.quarterly_reporter import QuarterlyReporter

            async def generate():
                reporter = QuarterlyReporter()
                today = datetime.now()
                # 1월(1) -> 작년 4분기(4), 4월(4) -> 1분기(1) ...
                current_month = today.month
                prev_quarter_map = {1: 4, 4: 1, 7: 2, 10: 3}
                target_quarter = prev_quarter_map.get(current_month)
                target_year = today.year if current_month != 1 else today.year - 1
                
                if target_quarter:
                    return await reporter.generate_quarterly_report(target_year, target_quarter)
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            filename = loop.run_until_complete(generate())
            loop.close()

            if filename:
                logger.info(f"✅ Quarterly Report Generated: {filename}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Quarterly Report Generation failed: {e}", exc_info=True)

    def run_price_tracking_verification(self):
        """Price Tracking 검증 실행"""
        try:
            logger.info("="*60)
            logger.info(f"📈 Starting Price Tracking Verification - {datetime.now()}")
            logger.info("="*60)

            # Run async verification
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.price_verifier.verify_all_horizons())
            loop.close()

            logger.info("="*60)
            logger.info(f"✅ Price Tracking Verification Complete")

            for horizon, result in results.items():
                logger.info(f"   {horizon}: {result['correct_count']}/{result['verified_count']} correct ({result['accuracy']*100:.1f}%)")

            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Price Tracking Verification failed: {e}", exc_info=True)

    def start(self):
        """스케줄러 시작"""
        logger.info("🚀 Automation Scheduler Starting...")
        self.setup_schedules()

        logger.info("")
        logger.info("📅 Active Schedules:")
        for job in schedule.get_jobs():
            logger.info(f"   - {job}")
        logger.info("")

        logger.info("⏰ Scheduler running... (Press Ctrl+C to stop)")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("\n⏹️  Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}", exc_info=True)


if __name__ == "__main__":
    scheduler = AutomationScheduler()
    scheduler.start()
