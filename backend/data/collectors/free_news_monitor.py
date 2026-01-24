"""
Free News Monitor - 무료 뉴스 소스 실시간 모니터링

백악관 연설 등 중요 뉴스를 무료로 모니터링:
- Reuters (무료)
- AP News (무료)
- Bloomberg 일부 (무료)
- CNBC (무료)
- White House 공식 사이트 (무료)
- C-SPAN (무료)

작성일: 2026-01-21
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

# 기존 스텔스 크롤러 재사용
from backend.data.collectors.stealth_web_crawler import StealthWebCrawler, MultiSiteMonitor

logger = logging.getLogger(__name__)


class FreeNewsMonitor:
    """
    무료 뉴스 소스 모니터링

    특징:
    - 구독료 없음
    - RSS 피드 + 웹 크롤링 병행
    - 백악관 공식 사이트 모니터링
    """

    # 무료 뉴스 소스 목록
    FREE_SOURCES = {
        # 백악관 공식
        'whitehouse': {
            'name': 'White House',
            'urls': [
                'https://www.whitehouse.gov/briefing-room/speeches-remarks/',
                'https://www.whitehouse.gov/briefing-room/statements-releases/',
            ],
            'rss': 'https://www.whitehouse.gov/feed/',
            'interval': 2.0  # 2분 간격
        },

        # Reuters (무료)
        'reuters': {
            'name': 'Reuters',
            'urls': [
                'https://www.reuters.com/world/us/',
                'https://www.reuters.com/markets/',
            ],
            'rss': 'https://www.reuters.com/rssfeed/businessNews',
            'interval': 3.0
        },

        # AP News (무료)
        'ap': {
            'name': 'AP News',
            'urls': [
                'https://apnews.com/hub/politics',
                'https://apnews.com/hub/business',
            ],
            'rss': 'https://apnews.com/rss',
            'interval': 3.0
        },

        # CNBC (무료)
        'cnbc': {
            'name': 'CNBC',
            'urls': [
                'https://www.cnbc.com/politics/',
                'https://www.cnbc.com/world/',
            ],
            'rss': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
            'interval': 3.0
        },

        # C-SPAN (무료, 의회/백악관 생중계)
        'cspan': {
            'name': 'C-SPAN',
            'urls': [
                'https://www.c-span.org/congress/',
                'https://www.c-span.org/video/?517831-1/president-trump-speaks-white-house',
            ],
            'rss': None,
            'interval': 2.0
        },

        # Bloomberg (일부 무료)
        'bloomberg': {
            'name': 'Bloomberg',
            'urls': [
                'https://www.bloomberg.com/politics',
            ],
            'rss': None,
            'interval': 5.0
        }
    }

    def __init__(self):
        self.monitor = MultiSiteMonitor()
        self.active_sources = []

    def add_source(
        self,
        source_key: str,
        callback: Optional[callable] = None,
        custom_interval: Optional[float] = None
    ):
        """
        무료 뉴스 소스 추가

        Args:
            source_key: 'whitehouse', 'reuters', 'ap', 'cnbc', 'cspan', 'bloomberg'
            callback: 새 콘텐츠 발견 시 호출할 함수
            custom_interval: 커스텀 간격 (분)
        """
        if source_key not in self.FREE_SOURCES:
            logger.error(f"Unknown source: {source_key}")
            return

        source = self.FREE_SOURCES[source_key]
        interval = custom_interval or source['interval']

        # 각 URL마다 크롤러 추가
        for url in source['urls']:
            self.monitor.add_site(
                url=url,
                interval_minutes=interval,
                variance_minutes=0.5,
                callback=callback
            )
            logger.info(f"Added {source['name']}: {url}")

        self.active_sources.append(source_key)

    def add_all_sources(self, callback: Optional[callable] = None):
        """모든 무료 소스 추가"""
        for source_key in self.FREE_SOURCES.keys():
            self.add_source(source_key, callback)

    def add_whitehouse_only(self, callback: Optional[callable] = None):
        """백악관 공식 사이트만 추가 (가장 신뢰도 높음)"""
        self.add_source('whitehouse', callback)

    def add_breaking_news_sources(self, callback: Optional[callable] = None):
        """속보 중심 소스만 추가 (Reuters, AP, CNBC)"""
        self.add_source('reuters', callback)
        self.add_source('ap', callback)
        self.add_source('cnbc', callback)

    async def start(self):
        """모니터링 시작"""
        if not self.active_sources:
            logger.warning("No sources added. Call add_source() first.")
            return

        logger.info(f"Starting free news monitoring for {len(self.active_sources)} sources")
        await self.monitor.start_all()

    def stop(self):
        """모니터링 중지"""
        self.monitor.stop_all()


class RSSFeedMonitor:
    """
    RSS 피드 모니터링 (더 가볍고 빠름)

    장점:
    - 서버 부담 없음 (RSS는 크롤링용으로 제공됨)
    - 빠른 업데이트 감지
    - 구조화된 데이터
    """

    def __init__(self):
        try:
            import feedparser
            self.feedparser = feedparser
            self.enabled = True
        except ImportError:
            logger.warning("feedparser not installed. RSS monitoring disabled.")
            logger.warning("Install: pip install feedparser")
            self.enabled = False

    async def fetch_rss(self, rss_url: str) -> List[Dict[str, Any]]:
        """
        RSS 피드 가져오기

        Returns:
            [{
                'title': str,
                'link': str,
                'published': datetime,
                'summary': str
            }]
        """
        if not self.enabled:
            return []

        try:
            # feedparser는 동기 함수 (asyncio에서 실행)
            import asyncio
            loop = asyncio.get_event_loop()

            feed = await loop.run_in_executor(
                None,
                self.feedparser.parse,
                rss_url
            )

            articles = []
            for entry in feed.entries[:20]:  # 최신 20개
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': self._parse_published(entry),
                    'summary': entry.get('summary', ''),
                    'content': entry.get('content', [{}])[0].get('value', '')
                })

            return articles

        except Exception as e:
            logger.error(f"RSS fetch error: {e}")
            return []

    def _parse_published(self, entry) -> Optional[datetime]:
        """RSS published 날짜 파싱"""
        import time

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])

        return None

    async def monitor_rss(
        self,
        rss_url: str,
        interval_minutes: float = 5.0,
        callback: Optional[callable] = None
    ):
        """
        RSS 피드 주기적 모니터링

        Args:
            rss_url: RSS 피드 URL
            interval_minutes: 체크 간격 (분)
            callback: 새 기사 발견 시 호출할 함수
        """
        logger.info(f"Starting RSS monitoring: {rss_url}")
        seen_links = set()

        try:
            while True:
                articles = await self.fetch_rss(rss_url)

                new_articles = []
                for article in articles:
                    if article['link'] not in seen_links:
                        seen_links.add(article['link'])
                        new_articles.append(article)

                        if callback:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(article)
                            else:
                                callback(article)

                if new_articles:
                    logger.info(f"Found {len(new_articles)} new articles from RSS")

                # 다음 체크까지 대기
                await asyncio.sleep(interval_minutes * 60)

        except asyncio.CancelledError:
            logger.info("RSS monitoring cancelled")
        except Exception as e:
            logger.error(f"RSS monitoring error: {e}")


# ============================================================================
# 사용 예시 및 테스트
# ============================================================================

async def test_whitehouse_only():
    """백악관 공식 사이트만 모니터링 (가장 신뢰도 높음)"""
    print("=" * 70)
    print("White House Official Site Monitor")
    print("=" * 70)

    def on_new_content(data):
        print("\n🔔 NEW CONTENT!")
        print(f"   Title: {data['title'][:80]}")
        print(f"   Source: White House Official")

    monitor = FreeNewsMonitor()
    monitor.add_whitehouse_only(callback=on_new_content)

    await monitor.start()


async def test_breaking_news():
    """속보 중심 소스 모니터링 (Reuters, AP, CNBC)"""
    print("=" * 70)
    print("Breaking News Monitor (Free Sources)")
    print("=" * 70)

    def on_new_content(data):
        print("\n📰 NEW ARTICLE!")
        print(f"   Title: {data['title'][:80]}")

    monitor = FreeNewsMonitor()
    monitor.add_breaking_news_sources(callback=on_new_content)

    await monitor.start()


async def test_all_free_sources():
    """모든 무료 소스 모니터링"""
    print("=" * 70)
    print("All Free Sources Monitor")
    print("=" * 70)

    def on_new_content(data):
        print(f"\n✨ {data['title'][:80]}")

    monitor = FreeNewsMonitor()
    monitor.add_all_sources(callback=on_new_content)

    await monitor.start()


async def test_rss_only():
    """RSS 피드만 사용 (가장 가볍고 빠름)"""
    print("=" * 70)
    print("RSS Feed Monitor (Lightweight)")
    print("=" * 70)

    def on_new_article(article):
        print(f"\n📡 RSS: {article['title'][:80]}")
        print(f"   Link: {article['link']}")

    rss_monitor = RSSFeedMonitor()

    # 여러 RSS 피드 동시 모니터링
    tasks = [
        rss_monitor.monitor_rss(
            "https://www.whitehouse.gov/feed/",
            interval_minutes=2.0,
            callback=on_new_article
        ),
        rss_monitor.monitor_rss(
            "https://www.reuters.com/rssfeed/businessNews",
            interval_minutes=3.0,
            callback=on_new_article
        ),
        rss_monitor.monitor_rss(
            "https://apnews.com/rss",
            interval_minutes=3.0,
            callback=on_new_article
        ),
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 테스트 모드 선택
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'whitehouse'  # 기본: 백악관 공식 사이트만

    if mode == 'whitehouse':
        asyncio.run(test_whitehouse_only())
    elif mode == 'breaking':
        asyncio.run(test_breaking_news())
    elif mode == 'all':
        asyncio.run(test_all_free_sources())
    elif mode == 'rss':
        asyncio.run(test_rss_only())
    else:
        print("Usage: python free_news_monitor.py [whitehouse|breaking|all|rss]")
