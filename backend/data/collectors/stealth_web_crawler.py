"""
Stealth Web Crawler for Premium News Sites

실시간 뉴스 모니터링을 위한 스텔스 크롤러:
- User-Agent 로테이션
- 랜덤 딜레이 (2.5~3.5분)
- 브라우저 헤더 스푸핑
- 프록시 지원
- Rate Limiting

사용법:
    crawler = StealthWebCrawler(
        url="https://www.ft.com/content/xxxxx",
        interval_minutes=3
    )
    await crawler.start_monitoring()

작성일: 2026-01-21
"""

import os
import logging
import asyncio
import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse

# HTTP 클라이언트
import aiohttp
from bs4 import BeautifulSoup

# Database
from backend.database.repository import get_sync_session, NewsRepository

logger = logging.getLogger(__name__)


class StealthWebCrawler:
    """
    스텔스 웹 크롤러 - 특정 URL을 주기적으로 모니터링

    특징:
    - 실제 브라우저처럼 행동
    - 랜덤 딜레이로 패턴 숨기기
    - User-Agent 로테이션
    - 콘텐츠 변경 감지
    """

    # 실제 브라우저 User-Agent 목록
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    def __init__(
        self,
        url: str,
        interval_minutes: float = 3.0,
        variance_minutes: float = 0.5,
        proxy: Optional[str] = None,
        callback: Optional[Callable] = None
    ):
        """
        Args:
            url: 모니터링할 URL
            interval_minutes: 기본 간격 (분)
            variance_minutes: 랜덤 편차 (분) - ±값
            proxy: 프록시 서버 (예: "http://proxy.example.com:8080")
            callback: 새 콘텐츠 발견 시 호출할 함수
        """
        self.url = url
        self.interval_minutes = interval_minutes
        self.variance_minutes = variance_minutes
        self.proxy = proxy
        self.callback = callback

        # 상태 관리
        self.is_running = False
        self.last_content_hash = None
        self.fetch_count = 0
        self.last_fetch_time = None

        # 도메인 추출 (소스명으로 사용)
        parsed_url = urlparse(url)
        self.source_name = parsed_url.netloc.replace('www.', '').upper()

        logger.info(f"StealthWebCrawler initialized for {self.source_name}")
        logger.info(f"Interval: {interval_minutes}±{variance_minutes} minutes")

    def _get_random_headers(self) -> Dict[str, str]:
        """실제 브라우저처럼 보이는 랜덤 헤더 생성"""
        user_agent = random.choice(self.USER_AGENTS)

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        # Referer 추가 (도메인에서 온 것처럼)
        parsed_url = urlparse(self.url)
        headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        return headers

    def _calculate_next_delay(self) -> float:
        """다음 크롤링까지 대기 시간 계산 (초 단위)"""
        # 기본 간격 ± 랜덤 편차
        base_seconds = self.interval_minutes * 60
        variance_seconds = self.variance_minutes * 60

        delay = base_seconds + random.uniform(-variance_seconds, variance_seconds)

        # 최소 1분 보장
        return max(delay, 60)

    def _calculate_content_hash(self, content: str) -> str:
        """콘텐츠 해시 계산 (변경 감지용)"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def _fetch_content(self) -> Optional[Dict[str, Any]]:
        """
        URL에서 콘텐츠 가져오기

        Returns:
            {
                'title': str,
                'content': str,
                'html': str,
                'content_hash': str
            }
        """
        try:
            headers = self._get_random_headers()

            # 프록시 설정
            connector = None
            if self.proxy:
                connector = aiohttp.TCPConnector()

            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                proxy_url = self.proxy if self.proxy else None

                async with session.get(
                    self.url,
                    headers=headers,
                    proxy=proxy_url,
                    ssl=True  # SSL 검증
                ) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} from {self.url}")
                        return None

                    html = await response.text()

                    # BeautifulSoup으로 파싱
                    soup = BeautifulSoup(html, 'html.parser')

                    # 메타 태그 우선 추출
                    title = None
                    description = None

                    # Open Graph 태그
                    og_title = soup.find('meta', property='og:title')
                    og_description = soup.find('meta', property='og:description')

                    if og_title:
                        title = og_title.get('content')
                    if og_description:
                        description = og_description.get('content')

                    # 메타 description
                    if not description:
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc:
                            description = meta_desc.get('content')

                    # <title> 태그
                    if not title and soup.title:
                        title = soup.title.string

                    # 본문 추출 (article, main 태그 우선)
                    content = ""
                    article = soup.find('article')
                    if article:
                        # script, style 태그 제거
                        for tag in article(['script', 'style', 'nav', 'header', 'footer']):
                            tag.decompose()
                        content = article.get_text(separator='\n', strip=True)
                    else:
                        # article 없으면 main 태그
                        main = soup.find('main')
                        if main:
                            for tag in main(['script', 'style', 'nav', 'header', 'footer']):
                                tag.decompose()
                            content = main.get_text(separator='\n', strip=True)

                    # 콘텐츠가 비어있으면 전체 body
                    if not content:
                        body = soup.find('body')
                        if body:
                            for tag in body(['script', 'style', 'nav', 'header', 'footer']):
                                tag.decompose()
                            content = body.get_text(separator='\n', strip=True)

                    # 해시 계산
                    content_hash = self._calculate_content_hash(content)

                    return {
                        'title': title or 'No Title',
                        'description': description or '',
                        'content': content,
                        'html': html,
                        'content_hash': content_hash
                    }

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {self.url}")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching {self.url}: {e}")
        except Exception as e:
            logger.error(f"Error fetching {self.url}: {e}")

        return None

    async def _save_to_db(self, data: Dict[str, Any]) -> bool:
        """
        DB에 저장

        Args:
            data: _fetch_content()의 결과

        Returns:
            성공 여부
        """
        try:
            session = get_sync_session()
            repo = NewsRepository(session)

            try:
                # URL로 중복 체크
                if repo.exists_by_url(self.url):
                    # 이미 있으면 업데이트 (content_hash 다르면)
                    existing = repo.get_by_url(self.url)
                    if existing and existing.content_hash != data['content_hash']:
                        logger.info(f"Content changed, updating article: {self.url}")
                        # Update logic would go here, but repo doesn't have update method
                        # For now, we'll skip if already exists
                        return False
                    else:
                        logger.debug(f"Article unchanged: {self.url}")
                        return False

                # 새 기사 저장
                news_data = {
                    'title': data['title'],
                    'summary': data['description'],
                    'content': data['content'],
                    'url': self.url,
                    'source': self.source_name,
                    'published_at': datetime.now(),  # 크롤링 시간을 발행 시간으로
                    'author': None,
                    'tags': [],
                    'processed_at': None,
                    'content_hash': data['content_hash']
                }

                saved_article = repo.save_processed_article(news_data)

                if saved_article:
                    logger.info(f"✅ New article saved: {saved_article.title[:50]}...")
                    return True
                else:
                    logger.warning(f"Failed to save article (duplicate?): {self.url}")
                    return False

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error saving to DB: {e}")
            return False

    async def _monitor_once(self) -> bool:
        """
        한 번 크롤링 실행

        Returns:
            새 콘텐츠가 발견되었는지 여부
        """
        self.fetch_count += 1
        self.last_fetch_time = datetime.now()

        logger.info(f"🔍 Fetching [{self.fetch_count}]: {self.url}")

        # 콘텐츠 가져오기
        data = await self._fetch_content()

        if not data:
            logger.warning(f"Failed to fetch content from {self.url}")
            return False

        # 콘텐츠 변경 체크
        content_hash = data['content_hash']

        if self.last_content_hash is None:
            # 첫 크롤링
            self.last_content_hash = content_hash
            logger.info(f"📝 Initial content captured (hash: {content_hash[:8]}...)")

            # DB 저장
            saved = await self._save_to_db(data)

            # 콜백 호출
            if saved and self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(data)
                    else:
                        self.callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            return saved

        elif content_hash != self.last_content_hash:
            # 콘텐츠 변경됨!
            logger.info(f"🆕 Content CHANGED! (old: {self.last_content_hash[:8]}... -> new: {content_hash[:8]}...)")
            self.last_content_hash = content_hash

            # DB 저장
            saved = await self._save_to_db(data)

            # 콜백 호출
            if saved and self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(data)
                    else:
                        self.callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            return saved

        else:
            # 변경 없음
            logger.debug(f"No content change (hash: {content_hash[:8]}...)")
            return False

    async def start_monitoring(self):
        """모니터링 시작 (무한 루프)"""
        if self.is_running:
            logger.warning("Crawler already running")
            return

        self.is_running = True
        logger.info(f"🚀 Starting stealth monitoring: {self.url}")
        logger.info(f"   Interval: {self.interval_minutes}±{self.variance_minutes} minutes")

        try:
            while self.is_running:
                # 크롤링 실행
                new_content = await self._monitor_once()

                if new_content:
                    logger.info(f"✨ New content detected and saved!")

                # 다음 크롤링까지 대기
                delay = self._calculate_next_delay()
                next_time = datetime.now() + timedelta(seconds=delay)

                logger.info(f"⏰ Next fetch in {delay/60:.1f} minutes (at {next_time.strftime('%H:%M:%S')})")

                await asyncio.sleep(delay)

        except asyncio.CancelledError:
            logger.info("Monitoring cancelled")
        except Exception as e:
            logger.error(f"Monitoring error: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("🛑 Monitoring stopped")

    def stop_monitoring(self):
        """모니터링 중지"""
        if self.is_running:
            self.is_running = False
            logger.info("Stopping monitoring...")


class MultiSiteMonitor:
    """
    여러 사이트를 동시에 모니터링
    """

    def __init__(self):
        self.crawlers: List[StealthWebCrawler] = []
        self.tasks: List[asyncio.Task] = []

    def add_site(
        self,
        url: str,
        interval_minutes: float = 3.0,
        variance_minutes: float = 0.5,
        callback: Optional[Callable] = None
    ):
        """사이트 추가"""
        crawler = StealthWebCrawler(
            url=url,
            interval_minutes=interval_minutes,
            variance_minutes=variance_minutes,
            callback=callback
        )
        self.crawlers.append(crawler)
        logger.info(f"Added site: {url}")

    async def start_all(self):
        """모든 사이트 모니터링 시작"""
        logger.info(f"🚀 Starting monitoring for {len(self.crawlers)} sites")

        # 각 크롤러를 별도 태스크로 실행
        for crawler in self.crawlers:
            task = asyncio.create_task(crawler.start_monitoring())
            self.tasks.append(task)

        # 모든 태스크 완료 대기 (실제로는 무한 루프)
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("All monitoring cancelled")

    def stop_all(self):
        """모든 모니터링 중지"""
        logger.info("Stopping all crawlers...")
        for crawler in self.crawlers:
            crawler.stop_monitoring()

        for task in self.tasks:
            task.cancel()


# ============================================================================
# 테스트 및 사용 예시
# ============================================================================

async def test_ft_monitoring():
    """Financial Times 모니터링 테스트"""
    print("=" * 70)
    print("Stealth Web Crawler Test - Financial Times")
    print("=" * 70)

    # 콜백 함수 (새 콘텐츠 발견 시)
    def on_new_content(data: Dict[str, Any]):
        print("\n🔔 NEW CONTENT DETECTED!")
        print(f"   Title: {data['title'][:80]}...")
        print(f"   Length: {len(data['content'])} chars")
        print(f"   Hash: {data['content_hash'][:16]}...")

    # 크롤러 초기화
    crawler = StealthWebCrawler(
        url="https://www.ft.com/content/1369a45e-e39b-4aaa-a347-b1800da7fd31",
        interval_minutes=3.0,
        variance_minutes=0.5,
        callback=on_new_content
    )

    # 모니터링 시작 (Ctrl+C로 중지)
    try:
        await crawler.start_monitoring()
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        crawler.stop_monitoring()


async def test_multi_site():
    """여러 사이트 동시 모니터링 테스트"""
    print("=" * 70)
    print("Multi-Site Monitoring Test")
    print("=" * 70)

    monitor = MultiSiteMonitor()

    # 여러 사이트 추가
    monitor.add_site(
        url="https://www.ft.com/content/1369a45e-e39b-4aaa-a347-b1800da7fd31",
        interval_minutes=3.0
    )

    # 다른 사이트도 추가 가능
    # monitor.add_site(
    #     url="https://www.reuters.com/markets/...",
    #     interval_minutes=5.0
    # )

    # 모든 사이트 모니터링 시작
    try:
        await monitor.start_all()
    except KeyboardInterrupt:
        print("\n\n⏹️  All monitoring stopped by user")
        monitor.stop_all()


if __name__ == "__main__":
    import sys

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 테스트 실행
    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        asyncio.run(test_multi_site())
    else:
        asyncio.run(test_ft_monitoring())
