"""
KIS Auto Trading Scheduler - Enhanced News + RAG 통합

실시간 뉴스 → 4-way Filter → RAG → KIS 자동매매 파이프라인

파이프라인:
1. Enhanced News Crawler (30분마다) + 키워드 태깅
2. 4-way 필터링 (70% 노이즈 제거)
   - 위험 클러스터 (30%)
   - 섹터별 벡터 (20%)
   - 폭락 패턴 (30%)
   - 감성 시계열 (20%)
3. RAG-Enhanced Analysis (SEC 문서 참조)
4. Phase Pipeline (Security → Phase A/B/C)
5. KIS: 실제 주문 실행

작성일: 2025-12-03 (Updated with 4-way filter)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

# Enhanced News Crawler with 4-way Filter
try:
    from backend.news.enhanced_news_crawler import EnhancedNewsCrawler
    ENHANCED_CRAWLER_AVAILABLE = True
except ImportError:
    from backend.news.news_crawler import NewsAPICrawler as EnhancedNewsCrawler
    ENHANCED_CRAWLER_AVAILABLE = False
    logging.warning("Enhanced News Crawler not available, using basic crawler")

# RAG-Enhanced Analysis
try:
    from backend.ai.rag_enhanced_analysis import RAGEnhancedAnalysis
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG-Enhanced Analysis not available")

# KIS Integration
try:
    from backend.api.kis_integration_router import (
        KISAutoTradeRequest,
        kis_auto_trade,
        get_kis_broker
    )
    KIS_AVAILABLE = True
except ImportError:
    KIS_AVAILABLE = False
    logging.warning("KIS integration not available")

logger = logging.getLogger(__name__)


class KISAutoScheduler:
    """
    KIS 자동매매 스케줄러 (Enhanced + RAG)
    
    Enhanced News Crawler → 4-way Filter → RAG → Phase Pipeline → KIS Trading
    """
    
    def __init__(
        self,
        news_api_key: Optional[str] = None,
        kis_account_no: Optional[str] = None,
        is_virtual: bool = True,
        dry_run: bool = False,
        notifier: Optional[Any] = None,
        filter_threshold: float = 0.7,  # 4-way 필터 임계값
        db_session: Optional[Any] = None  # RAG용 DB 세션
    ):
        """
        Args:
            news_api_key: NewsAPI 키
            kis_account_no: KIS 계좌번호
            is_virtual: 모의투자 여부
            dry_run: Dry Run 모드 (주문 안 함)
            notifier: 알림 클라이언트
            filter_threshold: 4-way 필터 임계값 (0.7 = 70%)
            db_session: RAG용 DB 세션
        """
        self.is_virtual = is_virtual
        self.dry_run = dry_run
        self.kis_account_no = kis_account_no or os.getenv('KIS_ACCOUNT_NUMBER')
        self.notifier = notifier
        self.filter_threshold = filter_threshold
        
        # Enhanced News Crawler 초기화 (4-way filter 포함)
        self.news_crawler = EnhancedNewsCrawler(api_key=news_api_key)
        
        # RAG-Enhanced Analysis (선택적)
        if RAG_AVAILABLE and db_session:
            self.rag_analyzer = RAGEnhancedAnalysis(db_session)
            logger.info("RAG-Enhanced Analysis enabled")
        else:
            self.rag_analyzer = None
        
        # 스케줄러 초기화
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # 시간대
        self.us_eastern = pytz.timezone('US/Eastern')
        self.korea = pytz.timezone('Asia/Seoul')
        
        # 통계 (enhanced)
        self.stats = {
            'total_news_crawled': 0,
            'total_news_filtered': 0,  # 4-way 필터 통과
            'total_signals_generated': 0,
            'total_orders_executed': 0,
            'start_time': None
        }
        
        logger.info(
            f"KISAutoScheduler initialized "
            f"(enhanced={ENHANCED_CRAWLER_AVAILABLE}, rag={RAG_AVAILABLE}, "
            f"kis={KIS_AVAILABLE}, filter={filter_threshold})"
        )
    
    def setup_jobs(self):
        """스케줄 작업 설정"""
        
        # 1. 뉴스 크롤링 + 매매 사이클 (30분마다, 장 시간만)
        self.scheduler.add_job(
            self.trading_cycle,
            IntervalTrigger(minutes=30),
            id='trading_cycle',
            name='News Crawling + Trading (Every 30min)'
        )
        
        # 2. 장전 분석 (한국 시간 22:00 = US 9:00 AM)
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
        
        # 3. 장 마감 리포트 (한국 시간 06:00)
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
        
        logger.info("Scheduled jobs configured")
    
    async def trading_cycle(self):
        """매매 사이클: Enhanced 크롤링 + 4-way 필터링 + RAG"""
        
        # 장 시간 체크
        if not self._is_market_hours():
            logger.debug("Outside market hours, skipping trading cycle")
            return
        
        logger.info("=" * 70)
        logger.info("TRADING CYCLE STARTED (Enhanced + 4-way Filter)")
        logger.info("=" * 70)
        
        try:
            # Step 1: Enhanced 크롤링 + 태깅 + 4-way 필터링
            logger.info("Step 1: Crawling + Tagging + Filtering...")
            
            if ENHANCED_CRAWLER_AVAILABLE and hasattr(self.news_crawler, 'crawl_and_filter'):
                # 4-way 필터 사용
                articles = await self.news_crawler.crawl_and_filter(
                    hours=0.5,
                    filter_threshold=self.filter_threshold
                )
                logger.info(f"Filtered: {len(articles)} articles passed 4-way filter")
                self.stats['total_news_filtered'] += len(articles)
            else:
                # fallback: 기본 크롤러
                articles = await self.news_crawler.crawl_and_tag(hours=0.5)
                logger.info(f"Found {len(articles)} articles (no filter)")
            
            if not articles:
                logger.info("No articles after filtering")
                return
            
            self.stats['total_news_crawled'] += len(articles)
            
            # Step 2: 각 뉴스 → RAG 분석 → KIS auto-trade
            for article in articles:
                await self._process_article(article)
            
            logger.info(
                f"Trading cycle completed: {len(articles)} articles processed "
                f"(filter pass rate: {100 * len(articles) / max(self.stats['total_news_crawled'], 1):.1f}%)"
            )
        
        except Exception as e:
            logger.error(f"Trading cycle failed: {e}", exc_info=True)
            if self.notifier:
                await self.notifier.send(f"⚠️ Trading cycle error: {e}")
    
    async def _process_article(self, article: Dict[str, Any]):
        """
        단일 기사 처리: Phase Pipeline → KIS Order
        
        Args:
            article: 뉴스 기사 dict
        """
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            url = article.get('url', '')
            source = article.get('source', 'Unknown')
            
            logger.info(f"Processing: {title[:60]}...")
            
            # KIS Auto Trade 요청 생성
            request = KISAutoTradeRequest(
                headline=title,
                body=description or '',
                url=url,
                is_virtual=self.is_virtual,
                dry_run=self.dry_run
            )
            
            # Phase Pipeline 실행
            if KIS_AVAILABLE:
                result = await kis_auto_trade(request)
                
                # 결과 분석
                analysis = result.analysis
                
                logger.info(
                    f"[{source}] {analysis.final_ticker} {analysis.final_action} "
                    f"(confidence: {analysis.final_confidence:.0%})"
                )
                
                # 주문 실행 여부
                if result.kis_order_executed:
                    self.stats['total_orders_executed'] += 1
                    order_result = result.kis_order_result
                    
                    logger.info(
                        f"✅ ORDER EXECUTED: {order_result.side} {order_result.symbol} "
                        f"x{order_result.quantity}"
                    )
                    
                    # 알림 전송
                    if self.notifier:
                        await self.notifier.send(
                            f"🤖 **KIS Auto Trade**\n\n"
                            f"📰 {title[:80]}\n"
                            f"📊 {order_result.side} {order_result.symbol} x{order_result.quantity}\n"
                            f"💰 Confidence: {analysis.final_confidence:.0%}\n"
                            f"🔗 {url[:50]}"
                        )
                else:
                    logger.info(f"No order executed (confidence or filters)")
                
                self.stats['total_signals_generated'] += 1
            
            else:
                logger.warning("KIS not available, skipping order execution")
            
            # 기사 처리 완료 표시
            news_id = article.get('id')
            if news_id:
                self.news_crawler.mark_as_processed(news_id)
        
        except Exception as e:
            logger.error(f"Failed to process article: {e}", exc_info=True)
    
    async def pre_market_analysis(self):
        """장전 분석"""
        logger.info("=" * 70)
        logger.info("PRE-MARKET ANALYSIS")
        logger.info("=" * 70)
        
        try:
            # 지난 12시간 뉴스 크롤링
            logger.info("Crawling overnight news...")
            articles = await self.news_crawler.crawl_latest(hours=12)
            
            if articles:
                logger.info(f"Found {len(articles)} overnight articles")
                
                # 간단한 요약
                summary = f"🌅 **장전 분석**\n\n"
                summary += f"📰 Overnight News: {len(articles)}건\n"
                summary += f"🕐 Market opens in 30 minutes\n\n"
                
                # 상위 3개 헤드라인
                for i, article in enumerate(articles[:3], 1):
                    summary += f"{i}. {article['title'][:60]}...\n"
                
                if self.notifier:
                    await self.notifier.send(summary)
                else:
                    logger.info(summary)
        
        except Exception as e:
            logger.error(f"Pre-market analysis failed: {e}")
    
    async def market_close_report(self):
        """장 마감 리포트"""
        logger.info("=" * 70)
        logger.info("MARKET CLOSE REPORT")
        logger.info("=" * 70)
        
        try:
            # 오늘의 통계
            report = f"""
📊 **일일 리포트 ({datetime.now(self.korea).strftime('%Y-%m-%d')})**

📰 뉴스 크롤링: {self.stats['total_news_crawled']}건
🤖 시그널 생성: {self.stats['total_signals_generated']}건
💼 주문 실행: {self.stats['total_orders_executed']}건

모드: {'모의투자' if self.is_virtual else '실전투자'}
Dry Run: {'ON' if self.dry_run else 'OFF'}

오늘도 수고하셨습니다! 🌙
            """
            
            if self.notifier:
                await self.notifier.send(report)
            else:
                logger.info(report)
            
            # 통계 리셋 (일일)
            self.stats['total_news_crawled'] = 0
            self.stats['total_signals_generated'] = 0
            self.stats['total_orders_executed'] = 0
        
        except Exception as e:
            logger.error(f"Market close report failed: {e}")
    
    def _is_market_hours(self) -> bool:
        """미국 장 시간 확인"""
        now = datetime.now(self.us_eastern)
        
        # 주말 제외
        if now.weekday() >= 5:
            return False
        
        # 9:30 AM ~ 4:00 PM ET
        from datetime import time
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    async def start(self):
        """스케줄러 시작"""
        logger.info("=" * 70)
        logger.info("KIS AUTO TRADING SCHEDULER STARTING")
        logger.info("=" * 70)
        
        self.stats['start_time'] = datetime.now()
        
        self.setup_jobs()
        self.scheduler.start()
        self.is_running = True
        
        # 시작 알림
        start_message = f"""
✅ **KIS 자동매매 봇 가동됨**

📅 {datetime.now(self.korea).strftime('%Y-%m-%d %H:%M:%S KST')}
📊 모드: {'모의투자 (Virtual)' if self.is_virtual else '실전투자 (Real)'}
🧪 Dry Run: {'ON (분석만)' if self.dry_run else 'OFF (주문 실행)'}
📰 NewsAPI: {'Enabled' if self.news_crawler.enabled else 'Disabled (Mock)'}
💼 KIS: {'Available' if KIS_AVAILABLE else 'Not Available'}

스케줄:
• 뉴스 크롤링: 30분마다 (장 시간)
• 장전 분석: 22:00 KST
• 장 마감: 06:00 KST
        """
        
        if self.notifier:
            await self.notifier.send(start_message)
        
        logger.info(start_message)
        logger.info(f"Scheduled {len(self.scheduler.get_jobs())} jobs")
        
        # 무한 대기
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
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'is_running': self.is_running,
            'is_virtual': self.is_virtual,
            'dry_run': self.dry_run
        }


# ============================================================================
# Mock Notifier
# ============================================================================

class MockNotifier:
    """테스트용 알림 클래스"""
    
    async def send(self, message: str):
        print(f"\n[NOTIFICATION]\n{message}\n")


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("KIS Auto Scheduler Test")
        print("=" * 70)
        
        # Mock notifier
        notifier = MockNotifier()
        
        # Scheduler 초기화
        scheduler = KISAutoScheduler(
            is_virtual=True,
            dry_run=True,  # 테스트 모드
            notifier=notifier
        )
        
        print(f"\nNewsAPI enabled: {scheduler.news_crawler.enabled}")
        print(f"KIS available: {KIS_AVAILABLE}")
        print(f"Is market hours: {scheduler._is_market_hours()}")
        
        # 한 번 실행 테스트
        print("\nRunning single trading cycle...")
        await scheduler.trading_cycle()
        
        # 통계 조회
        print("\nStats:")
        stats = scheduler.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n=== Test PASSED! ===")
    
    asyncio.run(test())
