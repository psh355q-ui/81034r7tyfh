"""
Finviz "The Scout" - Real-time News Collector

Fast news collection from finviz.com/news.ashx with anti-scraping bypass.
Uses curl_cffi to impersonate real Chrome browser and avoid detection.

Features:
- Chrome browser impersonation (TLS fingerprint spoofing)
- Real-time news headlines (10-30 second updates)
- Impact score analysis with Gemini Flash
- Ticker extraction and categorization
- Rate-limiting and error handling

Author: AI Trading System Team
Date: 2025-12-22
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from urllib.parse import urljoin

from curl_cffi import requests
from bs4 import BeautifulSoup

try:
    from backend.config import get_settings
except ImportError:
    class MockSettings:
        gemini_api_key = ""
    def get_settings():
        return MockSettings()


logger = logging.getLogger(__name__)


@dataclass
class FinvizNewsItem:
    """Finviz news item structure."""
    title: str
    url: str
    source: str
    published_at: datetime
    tickers: List[str]
    impact_score: Optional[float] = None
    category: Optional[str] = None
    raw_html: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dict for storage."""
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'tickers': self.tickers,
            'impact_score': self.impact_score,
            'category': self.category
        }


class FinvizScout:
    """
    Finviz Scout - Ultra-fast news collector with anti-scraping bypass.

    Strategy:
    1. Use curl_cffi to impersonate Chrome 110+ (bypass TLS fingerprinting)
    2. Parse news table from finviz.com/news.ashx
    3. Extract tickers from links (e.g. ?t=AAPL)
    4. Score headlines with Gemini Flash for impact
    5. Return only high-impact news (score >= 80)

    Rate Limits:
    - 10-30 second intervals (avoid aggressive scraping)
    - Max 120 requests/hour
    """

    BASE_URL = "https://finviz.com"
    NEWS_URL = "https://finviz.com/news.ashx"

    def __init__(self, min_impact_score: float = 50.0):
        """
        Initialize Finviz Scout.

        Args:
            min_impact_score: Minimum impact score to return (0-100)
        """
        self.logger = logging.getLogger(__name__)
        self.min_impact_score = min_impact_score
        self.settings = get_settings()

        # Anti-scraping headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        self.seen_urls = set()
        self.last_request_time = None

    def fetch_news_page(self) -> Optional[str]:
        """
        Fetch Finviz news page with curl_cffi (anti-scraping bypass).

        Returns:
            HTML content or None if failed
        """
        try:
            # Rate limiting: Wait at least 10 seconds between requests
            if self.last_request_time:
                elapsed = (datetime.now() - self.last_request_time).total_seconds()
                if elapsed < 10:
                    wait_time = 10 - elapsed
                    self.logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s")
                    import time
                    time.sleep(wait_time)

            self.logger.info("🔍 Fetching Finviz news page...")

            # Use curl_cffi to impersonate Chrome 110
            # This bypasses TLS fingerprinting and most bot detection
            response = requests.get(
                self.NEWS_URL,
                headers=self.headers,
                impersonate="chrome110",  # KEY: Impersonate real browser
                timeout=30
            )

            self.last_request_time = datetime.now()

            if response.status_code == 200:
                self.logger.info(f"✅ Successfully fetched Finviz (status: {response.status_code})")
                return response.text
            elif response.status_code == 403:
                self.logger.error("❌ 403 Forbidden - Anti-scraping detected! Try increasing delay.")
                return None
            else:
                self.logger.error(f"❌ HTTP {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to fetch Finviz: {e}")
            return None

    def parse_news_table(self, html: str) -> List[FinvizNewsItem]:
        """
        Parse Finviz news table (2024 structure).

        Finviz structure:
        <tr class="news_table-row" onclick="trackAndOpenNews(event, 9, 'https://...')">
          <td class="news_first-time-cell">Icon</td>
          <td class="news_date-cell">07:15AM</td>
          <td class="news_link-cell"><a href="...">Headline</a></td>
        </tr>

        Args:
            html: HTML content from Finviz

        Returns:
            List of news items
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find news rows with class="news_table-row"
            news_rows = soup.find_all('tr', class_='news_table-row')

            if not news_rows:
                self.logger.warning("⚠️ Could not find news rows in HTML")
                return []

            items = []

            self.logger.info(f"📰 Found {len(news_rows)} news rows")

            for row in news_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue

                    # Cell 0: Icon (source indicator)
                    # Cell 1: Time (e.g. "07:15AM")
                    time_cell = cells[1]
                    time_str = time_cell.get_text(strip=True)

                    # Cell 2: Headline link
                    news_cell = cells[2]
                    link = news_cell.find('a')

                    if not link:
                        continue

                    headline = link.get_text(strip=True)
                    url = link.get('href')

                    # Skip if no headline or URL
                    if not headline or not url:
                        continue

                    # Fix URL if relative
                    if url.startswith('/'):
                        url = urljoin(self.BASE_URL, url)

                    # Skip if already seen
                    if url in self.seen_urls:
                        continue

                    self.seen_urls.add(url)

                    # Extract source from onclick attribute
                    onclick = row.get('onclick', '')
                    source_match = re.search(r'trackAndOpenNews\(event, (\d+|\'[^\']+\'),', onclick)
                    source_id = source_match.group(1) if source_match else None

                    # Map source ID to name (from Finviz's channelIdToLabel)
                    source_map = {
                        '1': 'MarketWatch', '2': 'WSJ', '3': 'Reuters',
                        '4': 'Yahoo Finance', '5': 'CNN', '6': 'NYT',
                        '7': 'Bloomberg', '9': 'BBC', '10': 'CNBC',
                        '11': 'Fox Business', '114': 'Seeking Alpha',
                        '132': 'Zero Hedge'
                    }

                    source = "Unknown"
                    if source_id:
                        source_id = source_id.strip("'\"")
                        source = source_map.get(source_id, source_id)

                    # If source not in map, extract from URL
                    if source == "Unknown" or not source_id:
                        if 'bloomberg' in url.lower():
                            source = "Bloomberg"
                        elif 'reuters' in url.lower():
                            source = "Reuters"
                        elif 'cnbc' in url.lower():
                            source = "CNBC"
                        elif 'wsj' in url.lower():
                            source = "WSJ"
                        elif 'marketwatch' in url.lower():
                            source = "MarketWatch"
                        elif 'seekingalpha' in url.lower():
                            source = "Seeking Alpha"
                        elif 'bbc' in url.lower():
                            source = "BBC"
                        else:
                            # Extract domain
                            import urllib.parse
                            parsed = urllib.parse.urlparse(url)
                            source = parsed.netloc.replace('www.', '')

                    # Parse timestamp
                    published_at = self._parse_finviz_time(time_str)

                    # Extract tickers from headline or link
                    # Finviz often includes ticker links or symbols in text
                    tickers = []
                    ticker_pattern = r'\b([A-Z]{1,5})\b'  # Simple ticker pattern
                    # Look for ticker mentions in headline
                    ticker_matches = re.findall(ticker_pattern, headline)
                    # Filter out common words
                    common_words = {'CEO', 'CFO', 'IPO', 'ETF', 'USA', 'UK', 'EU', 'FDA', 'SEC', 'AI', 'IT', 'TV'}
                    tickers = [t for t in ticker_matches if t not in common_words and len(t) <= 5]

                    item = FinvizNewsItem(
                        title=headline,
                        url=url,
                        source=source,
                        published_at=published_at,
                        tickers=tickers,
                        raw_html=str(news_cell)
                    )

                    items.append(item)

                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to parse news row: {e}")
                    continue

            self.logger.info(f"✅ Parsed {len(items)} news items")
            return items

        except Exception as e:
            self.logger.error(f"❌ Failed to parse news table: {e}")
            return []

    def _parse_finviz_time(self, time_str: str) -> datetime:
        """
        Parse Finviz timestamp like "Dec-22-24 10:30AM".

        Args:
            time_str: Finviz time string

        Returns:
            datetime object
        """
        try:
            # Format: "Dec-22-24 10:30AM" or "Dec-22 10:30AM"
            # If no year, assume current year

            # Handle "Today" or relative times
            if 'today' in time_str.lower():
                return datetime.now()

            # Try parsing full format first
            for fmt in ["%b-%d-%y %I:%M%p", "%b-%d %I:%M%p"]:
                try:
                    dt = datetime.strptime(time_str, fmt)

                    # If no year in format, use current year
                    if fmt == "%b-%d %I:%M%p":
                        dt = dt.replace(year=datetime.now().year)

                    return dt
                except ValueError:
                    continue

            # Fallback: return now
            self.logger.warning(f"⚠️ Could not parse time: {time_str}, using now")
            return datetime.now()

        except Exception as e:
            self.logger.warning(f"⚠️ Time parse error: {e}")
            return datetime.now()

    def score_headlines(self, items: List[FinvizNewsItem]) -> List[FinvizNewsItem]:
        """
        Score headlines with Gemini Flash for impact (0-100).

        High scores (80+) indicate:
        - Market-moving events (earnings beats/misses, M&A, FDA approvals)
        - Executive changes (CEO resignation, insider trading)
        - Macroeconomic surprises
        - Geopolitical crises

        Args:
            items: List of news items

        Returns:
            List of items with impact_score filled
        """
        try:
            import google.generativeai as genai

            if not self.settings.gemini_api_key:
                self.logger.warning("⚠️ No Gemini API key, skipping scoring")
                return items

            genai.configure(api_key=self.settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Batch score headlines (up to 20 at once)
            batch_size = 20
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]

                # Create prompt
                headlines_text = "\n".join([
                    f"{idx}. {item.title} (Tickers: {', '.join(item.tickers) if item.tickers else 'None'})"
                    for idx, item in enumerate(batch)
                ])

                prompt = f"""Score these news headlines for market impact (0-100):

{headlines_text}

Scoring criteria:
- 90-100: Market-moving events (M&A, earnings surprises, FDA approvals, CEO changes)
- 70-89: Significant news (product launches, analyst upgrades, regulatory news)
- 50-69: Moderate news (earnings reports, partnership announcements)
- 30-49: Minor news (routine updates, analyst comments)
- 0-29: Non-actionable (opinion pieces, general market commentary)

Return ONLY a JSON array with format:
[{{"index": 0, "score": 85, "category": "M&A"}}, ...]

Categories: M&A, Earnings, FDA, Executive, Macro, Product, Regulatory, Analyst, Routine"""

                try:
                    response = model.generate_content(prompt)
                    text = response.text.strip()

                    # Extract JSON
                    import json
                    import re

                    # Remove markdown code blocks if present
                    text = re.sub(r'```json\s*|\s*```', '', text)

                    scores = json.loads(text)

                    # Apply scores
                    for score_data in scores:
                        idx = score_data.get('index')
                        score = score_data.get('score', 0)
                        category = score_data.get('category', 'Unknown')

                        if idx is not None and idx < len(batch):
                            batch[idx].impact_score = float(score)
                            batch[idx].category = category

                    self.logger.info(f"✅ Scored {len(scores)} headlines")

                except Exception as e:
                    self.logger.error(f"❌ Scoring failed: {e}")
                    # Continue without scores

            return items

        except ImportError:
            self.logger.warning("⚠️ google.generativeai not installed, skipping scoring")
            return items
        except Exception as e:
            self.logger.error(f"❌ Scoring error: {e}")
            return items

    def collect(self, score: bool = True, min_score: Optional[float] = None) -> List[FinvizNewsItem]:
        """
        Collect latest news from Finviz.

        Args:
            score: Whether to score headlines with Gemini
            min_score: Minimum impact score to return (overrides self.min_impact_score)

        Returns:
            List of news items (filtered by score if applicable)
        """
        try:
            self.logger.info("🚀 Starting Finviz Scout collection...")

            # 1. Fetch page
            html = self.fetch_news_page()
            if not html:
                self.logger.error("❌ Failed to fetch news page")
                return []

            # 2. Parse
            items = self.parse_news_table(html)
            if not items:
                self.logger.warning("⚠️ No news items parsed")
                return []

            self.logger.info(f"📰 Collected {len(items)} news items")

            # 3. Score (optional)
            if score:
                items = self.score_headlines(items)

                # Filter by score
                threshold = min_score if min_score is not None else self.min_impact_score
                high_impact = [item for item in items if item.impact_score and item.impact_score >= threshold]

                self.logger.info(f"🔥 {len(high_impact)} high-impact items (>= {threshold})")

                return high_impact

            return items

        except Exception as e:
            self.logger.error(f"❌ Collection failed: {e}")
            return []

    def collect_loop(self, interval: int = 30, duration: int = 3600, score: bool = True):
        """
        Run continuous collection loop.

        Args:
            interval: Seconds between collections (default: 30s)
            duration: Total duration in seconds (default: 1 hour)
            score: Whether to score headlines
        """
        start_time = datetime.now()
        iteration = 0

        self.logger.info(f"🔄 Starting collection loop: {interval}s interval, {duration}s duration")

        try:
            while (datetime.now() - start_time).total_seconds() < duration:
                iteration += 1
                self.logger.info(f"\n{'='*60}\n🔄 Iteration {iteration}\n{'='*60}")

                items = self.collect(score=score)

                if items:
                    self.logger.info(f"✅ Collected {len(items)} items:")
                    for item in items[:5]:  # Show first 5
                        score_str = f" [Score: {item.impact_score:.0f}]" if item.impact_score else ""
                        tickers_str = f" ({', '.join(item.tickers)})" if item.tickers else ""
                        self.logger.info(f"  • {item.title[:80]}...{score_str}{tickers_str}")
                else:
                    self.logger.info("⚠️ No new items")

                # Wait for next iteration
                import time
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("\n⏹️ Collection loop stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Loop error: {e}")


# CLI for testing
if __name__ == "__main__":
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scout = FinvizScout(min_impact_score=50.0)

    if len(sys.argv) > 1 and sys.argv[1] == "loop":
        # Continuous mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
        scout.collect_loop(interval=interval, duration=duration)
    else:
        # Single collection
        items = scout.collect(score=True, min_score=70)

        print(f"\n{'='*80}")
        print(f"🔥 HIGH IMPACT NEWS ({len(items)} items)")
        print(f"{'='*80}\n")

        for i, item in enumerate(items, 1):
            print(f"{i}. [{item.impact_score:.0f}] {item.category}")
            print(f"   {item.title}")
            print(f"   Tickers: {', '.join(item.tickers) if item.tickers else 'None'}")
            print(f"   Source: {item.source}")
            print(f"   URL: {item.url}")
            print()
