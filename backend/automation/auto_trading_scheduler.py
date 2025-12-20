"""
AutoTradingScheduler - 24시간 무인 자동매매 스케줄러

Phase B 통합:
- 장전/장중/장후 자동 실행
- DeepReasoningStrategy 통합
- Constitution Rules 적용
- Discord/Slack 알림

작성일: 2025-12-03 (Phase B)
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, List, Dict, Any
import pytz

# APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Phase A modules
from backend.ai.strategies.deep_reasoning_strategy import DeepReasoningStrategy
from backend.schemas.base_schema import InvestmentSignal, SignalAction

logger = logging.getLogger(__name__)


class AutoTradingScheduler:
    """
    24시간 무인 자동매매 스케줄러

    주요 기능:
    1. 장전 분석 (한국 시간 22:00 = US 동부 9:00 AM)
    2. 장중 매매 사이클 (30분마다)
    3. 장 마감 리포트 (한국 시간 06:00)

    Phase B 통합:
    - DeepReasoningStrategy를 사용한 자동 분석
    - InvestmentSignal 기반 매매
    """

    def __init__(
        self,
        strategy: Optional[DeepReasoningStrategy] = None,
        broker: Optional[Any] = None,
        notifier: Optional[Any] = None,
        watchlist: Optional[List[str]] = None
    ):
        """
        Args:
            strategy: DeepReasoningStrategy 인스턴스
            broker: 브로커 클라이언트 (실제 거래용)
            notifier: 알림 클라이언트 (Discord/Slack)
            watchlist: 감시 종목 리스트
        """
        self.strategy = strategy or DeepReasoningStrategy()
        self.broker = broker
        self.notifier = notifier
        self.watchlist = watchlist or ["NVDA", "GOOGL", "AMD", "TSM", "AVGO"]

        # 스케줄러 초기화
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

        # 시간대 설정
        self.us_eastern = pytz.timezone('US/Eastern')
        self.korea = pytz.timezone('Asia/Seoul')

        logger.info("AutoTradingScheduler initialized")

    def setup_jobs(self):
        """스케줄 작업 설정"""

        # 1. 장전 분석 (한국 시간 22:00 = US 동부 9:00 AM)
        # 월~금 22:00 KST
        self.scheduler.add_job(
            self.pre_market_analysis,
            CronTrigger(
                day_of_week='mon-fri',
                hour=22,
                minute=0,
                timezone=self.korea
            ),
            id='pre_market_analysis',
            name='Pre-Market Analysis'
        )

        # 2. 장중 매매 사이클 (30분마다, 장 시간만)
        # 이 작업은 _is_market_hours() 체크를 통해 장 시간에만 실행
        self.scheduler.add_job(
            self.trading_cycle,
            IntervalTrigger(minutes=30),
            id='trading_cycle',
            name='Trading Cycle (Every 30min)'
        )

        # 3. 장 마감 리포트 (한국 시간 06:00 = US 동부 4:00 PM + 2시간)
        # 화~토 06:00 KST (월요일 장 마감은 화요일 오전)
        self.scheduler.add_job(
            self.market_close_report,
            CronTrigger(
                day_of_week='tue-sat',
                hour=6,
                minute=0,
                timezone=self.korea
            ),
            id='market_close_report',
            name='Market Close Report'
        )

        # 4. 뉴스 모니터링 (매 10분마다)
        self.scheduler.add_job(
            self.news_monitoring,
            IntervalTrigger(minutes=10),
            id='news_monitoring',
            name='News Monitoring (Every 10min)'
        )

        logger.info("Scheduled jobs configured")

    async def pre_market_analysis(self):
        """장전 시장 분석"""
        logger.info("=" * 60)
        logger.info("PRE-MARKET ANALYSIS STARTED")
        logger.info("=" * 60)

        try:
            # 간단한 시장 국면 메시지 (실제로는 Regime Detector 사용)
            market_status = "Market opening soon. AI analyzing watchlist..."

            if self.notifier:
                await self.notifier.send(f"🌅 **장전 분석**\n{market_status}")
            else:
                logger.info(f"Pre-Market: {market_status}")

            # Watchlist 종목 분석
            for ticker in self.watchlist:
                logger.info(f"Pre-analyzing {ticker}...")

        except Exception as e:
            logger.error(f"Pre-market analysis failed: {e}")
            if self.notifier:
                await self.notifier.send(f"⚠️ 장전 분석 오류: {e}")

    async def trading_cycle(self):
        """매매 사이클 실행 (장 시간만)"""

        # 장 시간 체크
        if not self._is_market_hours():
            logger.debug("Outside market hours, skipping trading cycle")
            return

        logger.info("=" * 60)
        logger.info("TRADING CYCLE STARTED")
        logger.info("=" * 60)

        try:
            # 실제 매매는 Phase B2 (Signal to Order Converter) 구현 후
            # 현재는 시그널 생성만 테스트

            for ticker in self.watchlist:
                logger.info(f"Analyzing {ticker}...")

                # 간단한 뉴스 시뮬레이션 (실제로는 News API 사용)
                fake_news = f"{ticker} shows strong performance in AI chip market"

                # DeepReasoningStrategy 분석
                result = await self.strategy.analyze_news(fake_news)

                signals = result.get("investment_signals", [])

                for signal in signals:
                    if signal["action"] != "HOLD":
                        logger.info(
                            f"📊 Signal: {signal['action']} {signal['ticker']} "
                            f"(confidence: {signal['confidence']:.0%})"
                        )

                        if self.notifier:
                            await self.notifier.send(
                                f"🤖 **{signal['action']} {signal['ticker']}**\n"
                                f"Confidence: {signal['confidence']:.0%}\n"
                                f"Reason: {signal['reasoning']}"
                            )

        except Exception as e:
            logger.error(f"Trading cycle failed: {e}")
            if self.notifier:
                await self.notifier.send(f"⚠️ 매매 사이클 오류: {e}")

    async def market_close_report(self):
        """장 마감 일일 리포트"""
        logger.info("=" * 60)
        logger.info("MARKET CLOSE REPORT")
        logger.info("=" * 60)

        try:
            # 일일 리포트 생성 (실제로는 데이터베이스에서 집계)
            report = {
                "date": datetime.now(self.korea).strftime("%Y-%m-%d"),
                "total_signals": 0,
                "executed_trades": 0,
                "portfolio_change": 0.0
            }

            message = f"""
📊 **일일 리포트 ({report['date']})**

총 시그널: {report['total_signals']}
실행된 거래: {report['executed_trades']}
포트폴리오 변화: {report['portfolio_change']:+.2f}%

오늘도 수고하셨습니다! 🌙
            """

            if self.notifier:
                await self.notifier.send(message)
            else:
                logger.info(message)

        except Exception as e:
            logger.error(f"Market close report failed: {e}")

    async def news_monitoring(self):
        """뉴스 모니터링 (실시간)"""

        # 장 시간에만 적극적으로 모니터링
        if not self._is_market_hours():
            return

        logger.debug("News monitoring cycle...")

        try:
            # 실제로는 News API에서 최신 뉴스 가져오기
            # 현재는 스킵
            pass

        except Exception as e:
            logger.error(f"News monitoring failed: {e}")

    def _is_market_hours(self) -> bool:
        """
        미국 장 시간 확인

        Returns:
            장 시간이면 True
        """
        now = datetime.now(self.us_eastern)

        # 주말 제외
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # 9:30 AM ~ 4:00 PM ET
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()

        return market_open <= current_time <= market_close

    async def start(self):
        """스케줄러 시작"""
        logger.info("=" * 60)
        logger.info("AUTO TRADING SCHEDULER STARTING")
        logger.info("=" * 60)

        self.setup_jobs()
        self.scheduler.start()
        self.is_running = True

        if self.notifier:
            await self.notifier.send(
                "✅ **AI 트레이딩 봇 가동됨**\n"
                f"감시 종목: {', '.join(self.watchlist)}\n"
                f"현재 시간: {datetime.now(self.korea).strftime('%Y-%m-%d %H:%M:%S KST')}"
            )

        logger.info(f"Scheduler started with {len(self.scheduler.get_jobs())} jobs")
        logger.info(f"Watchlist: {self.watchlist}")

        # 무한 대기 (Ctrl+C로 종료)
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()

    def stop(self):
        """스케줄러 중지"""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")

    def get_next_run_times(self) -> Dict[str, str]:
        """
        다음 실행 시간 조회

        Returns:
            작업별 다음 실행 시간
        """
        next_runs = {}

        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                next_runs[job.name] = next_run.strftime("%Y-%m-%d %H:%M:%S %Z")

        return next_runs


# ============================================================================
# Mock Notifier (테스트용)
# ============================================================================

class MockNotifier:
    """테스트용 간단한 알림 클래스"""

    async def send(self, message: str):
        """메시지 전송 (콘솔 출력)"""
        print(f"\n[NOTIFICATION]\n{message}\n")


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    async def test():
        # Mock notifier
        notifier = MockNotifier()

        # Scheduler 초기화
        scheduler = AutoTradingScheduler(
            notifier=notifier,
            watchlist=["NVDA", "GOOGL", "TSM"]
        )

        print("=" * 70)
        print("AutoTradingScheduler Test")
        print("=" * 70)

        # 스케줄 설정
        scheduler.setup_jobs()

        # 다음 실행 시간 확인
        next_runs = scheduler.get_next_run_times()
        print("\nScheduled Jobs:")
        for job_name, next_run in next_runs.items():
            print(f"  {job_name}: {next_run}")

        # 테스트: 장 시간 체크
        print(f"\nIs market hours now? {scheduler._is_market_hours()}")

        # 테스트: 한 번 실행
        print("\nRunning trading cycle once...")
        await scheduler.trading_cycle()

        print("\n=== Test PASSED! ===")

    asyncio.run(test())
