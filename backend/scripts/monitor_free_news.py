"""
Free News Monitor - 무료 뉴스 실시간 모니터링

백악관 연설 등 중요 뉴스를 무료로 모니터링

사용법:
    # 백악관 공식 사이트만 (가장 신뢰도 높음)
    python backend/scripts/monitor_free_news.py

    # 속보 중심 (Reuters + AP + CNBC)
    python backend/scripts/monitor_free_news.py breaking

    # 모든 무료 소스
    python backend/scripts/monitor_free_news.py all

    # RSS 피드만 (가장 가볍고 빠름)
    python backend/scripts/monitor_free_news.py rss

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

from backend.data.collectors.free_news_monitor import FreeNewsMonitor, RSSFeedMonitor
from backend.database.repository import get_sync_session, NewsRepository

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/free_news_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def save_to_db(data: dict):
    """
    새 콘텐츠를 DB에 저장

    Args:
        data: {
            'title': str,
            'content': str,
            'url': str (or 'link'),
            'source': str (optional)
        }
    """
    try:
        session = get_sync_session()
        repo = NewsRepository(session)

        try:
            # URL 추출 (dict key가 'url' 또는 'link'일 수 있음)
            url = data.get('url') or data.get('link')
            if not url:
                logger.warning("No URL found in data, skipping save")
                return

            # 중복 체크
            if repo.exists_by_url(url):
                logger.debug(f"Article already exists: {url}")
                return

            # DB 저장
            news_data = {
                'title': data.get('title', 'No Title'),
                'summary': data.get('summary', data.get('description', '')),
                'content': data.get('content', ''),
                'url': url,
                'source': data.get('source', 'Unknown'),
                'published_at': data.get('published', datetime.now()),
                'author': None,
                'tags': [],
                'processed_at': None
            }

            saved = repo.save_processed_article(news_data)
            if saved:
                logger.info(f"✅ Saved: {saved.title[:60]}...")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"DB save error: {e}")


def on_new_content(data: dict):
    """
    새 콘텐츠 발견 시 호출되는 콜백

    - DB에 저장
    - 로그 출력
    - (TODO) AI 분석 트리거
    """
    logger.info("=" * 70)
    logger.info("🔔 NEW CONTENT DETECTED!")
    logger.info("=" * 70)
    logger.info(f"Title: {data.get('title', 'No Title')[:80]}")
    logger.info(f"Source: {data.get('source', 'Unknown')}")

    url = data.get('url') or data.get('link')
    if url:
        logger.info(f"URL: {url[:100]}")

    content_length = len(data.get('content', ''))
    if content_length > 0:
        logger.info(f"Content Length: {content_length} chars")

    logger.info("=" * 70)

    # DB 저장
    save_to_db(data)

    # TODO: AI 분석 파이프라인 트리거
    # from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsPipeline
    # pipeline = EnhancedNewsPipeline()
    # await pipeline.process_urgent_news(data)


async def monitor_whitehouse_only():
    """백악관 공식 사이트만 모니터링 (가장 신뢰도 높음)"""
    logger.info("=" * 70)
    logger.info("White House Official Site Monitor")
    logger.info("=" * 70)
    logger.info("Monitoring:")
    logger.info("  - https://www.whitehouse.gov/briefing-room/speeches-remarks/")
    logger.info("  - https://www.whitehouse.gov/briefing-room/statements-releases/")
    logger.info("")
    logger.info("Interval: 2±0.5 minutes")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    monitor = FreeNewsMonitor()
    monitor.add_whitehouse_only(callback=on_new_content)

    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Monitoring stopped by user")
        monitor.stop()


async def monitor_breaking_news():
    """속보 중심 소스 모니터링 (Reuters + AP + CNBC)"""
    logger.info("=" * 70)
    logger.info("Breaking News Monitor (Free Sources)")
    logger.info("=" * 70)
    logger.info("Sources:")
    logger.info("  - Reuters (reuters.com)")
    logger.info("  - AP News (apnews.com)")
    logger.info("  - CNBC (cnbc.com)")
    logger.info("")
    logger.info("Interval: 3±0.5 minutes per source")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    monitor = FreeNewsMonitor()
    monitor.add_breaking_news_sources(callback=on_new_content)

    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Monitoring stopped by user")
        monitor.stop()


async def monitor_all_free_sources():
    """모든 무료 소스 모니터링"""
    logger.info("=" * 70)
    logger.info("All Free Sources Monitor")
    logger.info("=" * 70)
    logger.info("Sources:")
    logger.info("  - White House Official (whitehouse.gov)")
    logger.info("  - Reuters (reuters.com)")
    logger.info("  - AP News (apnews.com)")
    logger.info("  - CNBC (cnbc.com)")
    logger.info("  - C-SPAN (c-span.org)")
    logger.info("  - Bloomberg (bloomberg.com - free articles)")
    logger.info("")
    logger.info("Interval: 2~5 minutes per source")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    monitor = FreeNewsMonitor()
    monitor.add_all_sources(callback=on_new_content)

    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Monitoring stopped by user")
        monitor.stop()


async def monitor_rss_only():
    """RSS 피드만 사용 (가장 가볍고 빠름)"""
    logger.info("=" * 70)
    logger.info("RSS Feed Monitor (Lightweight)")
    logger.info("=" * 70)
    logger.info("RSS Feeds:")
    logger.info("  - White House (whitehouse.gov/feed/)")
    logger.info("  - Reuters (reuters.com/rssfeed/businessNews)")
    logger.info("  - AP News (apnews.com/rss)")
    logger.info("  - CNBC (cnbc.com/...rss)")
    logger.info("")
    logger.info("Interval: 2~3 minutes per feed")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    logger.info("\nPress Ctrl+C to stop\n")

    def on_new_rss_article(article):
        """RSS 기사 콜백"""
        logger.info(f"\n📡 RSS Article: {article['title'][:80]}")
        logger.info(f"   Link: {article['link'][:100]}")

        # source 추가
        article['source'] = 'RSS Feed'

        # DB 저장
        save_to_db(article)

    rss_monitor = RSSFeedMonitor()

    # 여러 RSS 피드 동시 모니터링
    tasks = [
        rss_monitor.monitor_rss(
            "https://www.whitehouse.gov/feed/",
            interval_minutes=2.0,
            callback=on_new_rss_article
        ),
        rss_monitor.monitor_rss(
            "https://www.reuters.com/rssfeed/businessNews",
            interval_minutes=3.0,
            callback=on_new_rss_article
        ),
        rss_monitor.monitor_rss(
            "https://apnews.com/rss",
            interval_minutes=3.0,
            callback=on_new_rss_article
        ),
        rss_monitor.monitor_rss(
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            interval_minutes=3.0,
            callback=on_new_rss_article
        ),
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  RSS monitoring stopped by user")


if __name__ == "__main__":
    # logs 디렉토리 생성
    os.makedirs('logs', exist_ok=True)

    # 모드 선택
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = 'whitehouse'  # 기본: 백악관 공식 사이트만

    # 실행
    try:
        if mode == 'whitehouse':
            asyncio.run(monitor_whitehouse_only())
        elif mode == 'breaking':
            asyncio.run(monitor_breaking_news())
        elif mode == 'all':
            asyncio.run(monitor_all_free_sources())
        elif mode == 'rss':
            asyncio.run(monitor_rss_only())
        else:
            print("Usage: python backend/scripts/monitor_free_news.py [whitehouse|breaking|all|rss]")
            print("")
            print("Modes:")
            print("  whitehouse - White House official site only (most reliable)")
            print("  breaking   - Reuters + AP + CNBC (fast breaking news)")
            print("  all        - All free sources (comprehensive)")
            print("  rss        - RSS feeds only (lightweight, fastest)")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
