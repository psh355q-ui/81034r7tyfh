"""
Financial Times Stealth Monitor

백악관 연설 등 중요 뉴스를 실시간 모니터링

사용법:
    # 단일 URL 모니터링
    python backend/scripts/monitor_ft.py

    # 백그라운드 실행 (Windows)
    start /B python backend/scripts/monitor_ft.py

    # 로그 파일로 출력
    python backend/scripts/monitor_ft.py > logs/ft_monitor.log 2>&1

작성일: 2026-01-21
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

load_dotenv()

from backend.data.collectors.stealth_web_crawler import StealthWebCrawler, MultiSiteMonitor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ft_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def on_new_content(data: dict):
    """
    새 콘텐츠 발견 시 호출되는 콜백

    여기서 추가 처리를 할 수 있습니다:
    - AI 분석 트리거
    - 알림 전송
    - 트레이딩 시그널 생성 등
    """
    logger.info("=" * 70)
    logger.info("🔔 NEW CONTENT DETECTED!")
    logger.info("=" * 70)
    logger.info(f"Title: {data['title']}")
    logger.info(f"Content Length: {len(data['content'])} chars")
    logger.info(f"Hash: {data['content_hash'][:16]}...")
    logger.info("=" * 70)

    # TODO: 여기서 AI 분석 파이프라인 트리거
    # from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsPipeline
    # pipeline = EnhancedNewsPipeline()
    # await pipeline.process_urgent_news(data)


async def monitor_single_url():
    """단일 URL 모니터링"""
    logger.info("=" * 70)
    logger.info("FT Stealth Monitor Starting...")
    logger.info("=" * 70)

    # 백악관 연설 관련 FT 기사
    url = "https://www.ft.com/content/1369a45e-e39b-4aaa-a347-b1800da7fd31"

    crawler = StealthWebCrawler(
        url=url,
        interval_minutes=3.0,      # 3분 간격
        variance_minutes=0.5,      # ±30초 랜덤
        callback=on_new_content
    )

    logger.info(f"Monitoring URL: {url}")
    logger.info(f"Interval: 3±0.5 minutes (stealth mode)")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    try:
        await crawler.start_monitoring()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Monitoring stopped by user")
        crawler.stop_monitoring()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        crawler.stop_monitoring()


async def monitor_multiple_urls():
    """여러 URL 동시 모니터링"""
    logger.info("=" * 70)
    logger.info("Multi-Site Stealth Monitor Starting...")
    logger.info("=" * 70)

    monitor = MultiSiteMonitor()

    # 백악관 연설 관련 FT 기사
    monitor.add_site(
        url="https://www.ft.com/content/1369a45e-e39b-4aaa-a347-b1800da7fd31",
        interval_minutes=3.0,
        variance_minutes=0.5,
        callback=on_new_content
    )

    # 필요시 다른 URL 추가
    # monitor.add_site(
    #     url="https://www.reuters.com/...",
    #     interval_minutes=5.0,
    #     callback=on_new_content
    # )

    logger.info(f"Monitoring {len(monitor.crawlers)} sites")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    try:
        await monitor.start_all()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  All monitoring stopped by user")
        monitor.stop_all()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        monitor.stop_all()


if __name__ == "__main__":
    # logs 디렉토리 생성
    os.makedirs('logs', exist_ok=True)

    # 단일 URL 모니터링 (기본)
    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        asyncio.run(monitor_multiple_urls())
    else:
        asyncio.run(monitor_single_url())
