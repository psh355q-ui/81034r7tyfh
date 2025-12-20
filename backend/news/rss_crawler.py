"""
Phase 16: Real-time RSS News Crawler

자동 뉴스 크롤링 및 Deep Reasoning 분석 시스템

Features:
- RSS feed 자동 크롤링 (TechCrunch, Reuters, Bloomberg 등)
- 뉴스 중복 제거 (SHA256 해시)
- Deep Reasoning 자동 분석
- Trading signal 생성 및 DB 저장
- 실시간 모니터링

Usage:
    crawler = RSSNewsCrawler()
    await crawler.start_monitoring(interval_seconds=300)  # 5분마다
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import feedparser
import aiohttp
from dataclasses import dataclass
from urllib.parse import urlparse

from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy, DeepReasoningResult


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    content: str
    url: str
    source: str
    published_date: datetime
    content_hash: str  # 중복 체크용


class RSSNewsCrawler:
    """
    RSS Feed 크롤러 및 자동 분석 시스템

    주요 기능:
    - 다수의 RSS 피드 모니터링
    - 뉴스 중복 제거
    - Deep Reasoning 자동 분석
    - Trading signal 생성
    """

    # 주요 AI/Tech RSS 피드
    RSS_FEEDS = {
        # Tech News
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",

        # Financial News
        "Reuters Tech": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "Bloomberg Tech": "https://feeds.bloomberg.com/technology/news.rss",
        "CNBC Tech": "https://www.cnbc.com/id/19854910/device/rss/rss.html",

        # AI Specific
        "MIT Tech Review": "https://www.technologyreview.com/feed/",
        "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",

        # Business
        "WSJ Tech": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
        "FT Tech": "https://www.ft.com/technology?format=rss",
    }

    # AI/반도체 관련 키워드 필터
    KEYWORDS = {
        # Companies
        "nvidia", "amd", "intel", "tsmc", "samsung", "sk hynix", "micron",
        "broadcom", "qualcomm", "asml", "marvell", "arista",
        "microsoft", "google", "aws", "amazon", "meta", "apple",
        "openai", "anthropic", "coreweave",

        # Tech terms
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "gpu", "tpu", "chip", "semiconductor", "foundry",
        "data center", "cloud computing",
        "llm", "large language model", "generative ai",

        # Products
        "h100", "h200", "mi300", "tpu v6", "blackwell",
        "azure", "aws", "gcp", "chatgpt", "claude", "gemini",
    }

    def __init__(self, reasoning_strategy: Optional[DeepReasoningStrategy] = None):
        """
        Args:
            reasoning_strategy: Deep Reasoning 전략 (None이면 자동 생성)
        """
        self.reasoning_strategy = reasoning_strategy or DeepReasoningStrategy()
        self.seen_hashes: Set[str] = set()  # 중복 체크용 해시 저장
        self.last_check_time = datetime.now() - timedelta(days=1)

    def _calculate_content_hash(self, title: str, content: str) -> str:
        """뉴스 컨텐츠 해시 계산 (중복 체크용)"""
        combined = f"{title}{content}".lower()
        return hashlib.sha256(combined.encode()).hexdigest()

    def _is_relevant(self, article: NewsArticle) -> bool:
        """AI/반도체 관련 뉴스인지 판단"""
        text = f"{article.title} {article.content}".lower()
        return any(keyword in text for keyword in self.KEYWORDS)

    async def fetch_rss_feed(self, feed_url: str, source_name: str) -> List[NewsArticle]:
        """
        단일 RSS 피드 크롤링

        Args:
            feed_url: RSS feed URL
            source_name: 소스 이름

        Returns:
            NewsArticle 리스트
        """
        articles = []

        try:
            # feedparser는 동기 함수이므로 executor에서 실행
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)

            for entry in feed.entries[:10]:  # 최근 10개만
                # 발행일 파싱
                published_date = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    from time import mktime
                    published_date = datetime.fromtimestamp(mktime(entry.published_parsed))

                # 최근 뉴스만 (last_check_time 이후)
                if published_date < self.last_check_time:
                    continue

                title = entry.get('title', '')
                content = entry.get('summary', entry.get('description', ''))
                url = entry.get('link', '')

                # 해시 계산
                content_hash = self._calculate_content_hash(title, content)

                # 중복 체크
                if content_hash in self.seen_hashes:
                    continue

                article = NewsArticle(
                    title=title,
                    content=content,
                    url=url,
                    source=source_name,
                    published_date=published_date,
                    content_hash=content_hash
                )

                # 관련성 체크
                if self._is_relevant(article):
                    articles.append(article)
                    self.seen_hashes.add(content_hash)

            return articles

        except Exception as e:
            print(f"[ERROR] Failed to fetch {source_name}: {e}")
            return []

    async def fetch_all_feeds(self) -> List[NewsArticle]:
        """모든 RSS 피드를 동시에 크롤링"""
        tasks = [
            self.fetch_rss_feed(url, name)
            for name, url in self.RSS_FEEDS.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 모든 결과 합치기
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)

        # 발행일 기준 정렬 (최신순)
        all_articles.sort(key=lambda x: x.published_date, reverse=True)

        return all_articles

    async def analyze_article(self, article: NewsArticle) -> Optional[Dict]:
        """
        뉴스 기사를 Deep Reasoning으로 분석

        Returns:
            {
                'article': NewsArticle,
                'analysis': DeepReasoningResult,
                'signals': List[Dict]  # Trading signals
            }
        """
        try:
            # 뉴스 텍스트 준비
            news_text = f"{article.title}. {article.content}"

            # Deep Reasoning 분석
            result = await self.reasoning_strategy.analyze_news(news_text)

            # Trading signals 추출
            signals = []

            if result.primary_beneficiary:
                signals.append({
                    'type': 'PRIMARY',
                    'ticker': result.primary_beneficiary.get('ticker'),
                    'action': result.primary_beneficiary.get('action'),
                    'confidence': result.primary_beneficiary.get('confidence'),
                    'reasoning': result.primary_beneficiary.get('reasoning')
                })

            if result.hidden_beneficiary:
                signals.append({
                    'type': 'HIDDEN',
                    'ticker': result.hidden_beneficiary.get('ticker'),
                    'action': result.hidden_beneficiary.get('action'),
                    'confidence': result.hidden_beneficiary.get('confidence'),
                    'reasoning': result.hidden_beneficiary.get('reasoning')
                })

            if result.loser:
                signals.append({
                    'type': 'LOSER',
                    'ticker': result.loser.get('ticker'),
                    'action': result.loser.get('action'),
                    'confidence': result.loser.get('confidence'),
                    'reasoning': result.loser.get('reasoning', 'N/A')
                })

            return {
                'article': article,
                'analysis': result,
                'signals': signals,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"[ERROR] Analysis failed for '{article.title[:50]}...': {e}")
            return None

    async def run_single_cycle(self) -> List[Dict]:
        """
        단일 크롤링 사이클 실행

        Returns:
            분석 완료된 기사 리스트
        """
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting news crawl cycle")
        print(f"{'='*80}")

        # 1. RSS 피드 크롤링
        print("\n[STEP 1] Fetching RSS feeds...")
        articles = await self.fetch_all_feeds()
        print(f"  Found {len(articles)} relevant articles")

        if not articles:
            print("  No new articles found")
            return []

        # 2. 기사 분석
        print(f"\n[STEP 2] Analyzing articles with Deep Reasoning...")
        analyzed_results = []

        for i, article in enumerate(articles[:5], 1):  # 최대 5개만 분석
            print(f"\n  [{i}/{min(len(articles), 5)}] Analyzing: {article.title[:60]}...")
            result = await self.analyze_article(article)

            if result and result['signals']:
                analyzed_results.append(result)
                print(f"    → {len(result['signals'])} signals generated")
                for signal in result['signals']:
                    print(f"      {signal['type']}: {signal['ticker']} ({signal['action']}, {signal['confidence']:.0%})")
            else:
                print(f"    → No significant signals")

        # 3. Update last check time
        self.last_check_time = datetime.now()

        print(f"\n{'='*80}")
        print(f"Cycle complete: {len(analyzed_results)} articles with signals")
        print(f"{'='*80}")

        return analyzed_results

    async def start_monitoring(self, interval_seconds: int = 300):
        """
        실시간 모니터링 시작

        Args:
            interval_seconds: 크롤링 간격 (초), 기본 5분
        """
        print(f"\n{'='*80}")
        print("Phase 16: Real-time News Crawler Started")
        print(f"{'='*80}")
        print(f"  Monitoring {len(self.RSS_FEEDS)} RSS feeds")
        print(f"  Check interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
        print(f"  Keywords: {len(self.KEYWORDS)} filters")
        print(f"{'='*80}\n")

        cycle_count = 0

        while True:
            try:
                cycle_count += 1
                print(f"\n[CYCLE #{cycle_count}]")

                # 크롤링 & 분석
                results = await self.run_single_cycle()

                # 다음 사이클까지 대기
                print(f"\n[WAITING] Next check in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n\n[STOPPED] Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n[ERROR] Cycle failed: {e}")
                print(f"Retrying in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)


# ============================================
# Demo & Testing
# ============================================

async def demo():
    """RSS 크롤러 데모"""
    print("=" * 80)
    print("Phase 16: RSS News Crawler Demo")
    print("=" * 80)

    crawler = RSSNewsCrawler()

    # 단일 사이클 실행
    results = await crawler.run_single_cycle()

    # 결과 요약
    print("\n" + "=" * 80)
    print("DEMO RESULTS")
    print("=" * 80)

    if results:
        print(f"\nTotal articles with signals: {len(results)}")

        for i, result in enumerate(results, 1):
            article = result['article']
            analysis = result['analysis']
            signals = result['signals']

            print(f"\n[Article {i}]")
            print(f"  Title: {article.title}")
            print(f"  Source: {article.source}")
            print(f"  Theme: {analysis.theme}")
            print(f"  Signals: {len(signals)}")
            for signal in signals:
                print(f"    - {signal['type']}: {signal['ticker']} {signal['action']} ({signal['confidence']:.0%})")
    else:
        print("\nNo articles with signals found in this cycle")

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    # 데모 실행
    asyncio.run(demo())

    # 실시간 모니터링 (주석 해제하여 사용)
    # crawler = RSSNewsCrawler()
    # asyncio.run(crawler.start_monitoring(interval_seconds=300))  # 5분마다
