"""
SEC EDGAR 8-K Monitor - Real-time Corporate Event Tracker

Monitors SEC EDGAR RSS feeds for Form 8-K filings (Current Reports).
Form 8-K discloses material events that shareholders should know about.

Common 8-K Event Types:
- Item 1.01: Entry into Material Agreement (M&A, partnerships)
- Item 1.02: Termination of Material Agreement
- Item 1.03: Bankruptcy or Receivership
- Item 2.01: Completion of Acquisition/Disposition
- Item 5.02: Executive Officer/Director Changes (CEO, CFO departures)
- Item 7.01: Regulation FD Disclosure (earnings guidance changes)
- Item 8.01: Other Events (major announcements)

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
import xml.etree.ElementTree as ET

import aiohttp
import feedparser

try:
    from backend.config import get_settings
except ImportError:
    class MockSettings:
        pass
    def get_settings():
        return MockSettings()


logger = logging.getLogger(__name__)


@dataclass
class SECFiling:
    """SEC 8-K filing data structure."""
    company_name: str
    ticker: Optional[str]
    cik: str  # Central Index Key (unique company identifier)
    form_type: str  # Usually "8-K"
    filing_date: datetime
    items: List[str]  # e.g. ["1.01", "7.01"]
    description: str
    url: str
    accession_number: str  # Unique filing ID
    impact_category: Optional[str] = None  # M&A, Executive, Earnings, etc.
    impact_score: Optional[float] = None  # 0-100

    def to_dict(self) -> Dict:
        """Convert to dict for storage."""
        return {
            'company_name': self.company_name,
            'ticker': self.ticker,
            'cik': self.cik,
            'form_type': self.form_type,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'items': self.items,
            'description': self.description,
            'url': self.url,
            'accession_number': self.accession_number,
            'impact_category': self.impact_category,
            'impact_score': self.impact_score
        }


class SECEdgarMonitor:
    """
    SEC EDGAR 8-K Monitor - Real-time corporate event tracker.

    Strategy:
    1. Poll SEC RSS feed for latest 8-K filings
    2. Parse XML to extract company name, CIK, items, date
    3. Classify impact based on Item codes
    4. Look up ticker symbol (CIK -> ticker mapping)
    5. Return high-impact filings only

    Rate Limits:
    - SEC allows 10 requests/second (very generous)
    - We'll use 2-5 minute polling intervals
    """

    # SEC RSS feeds
    RSS_FEEDS = {
        'recent': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=exclude&start=0&count=100&output=atom',
        'all_filings': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=exclude&start=0&count=100&output=atom'
    }

    BASE_URL = "https://www.sec.gov"

    # Item code to impact mapping
    ITEM_IMPACT = {
        # High impact (80-100)
        '1.01': ('M&A', 95, 'Entry into Material Agreement'),
        '1.03': ('Bankruptcy', 100, 'Bankruptcy or Receivership'),
        '2.01': ('M&A', 90, 'Completion of Acquisition or Disposition'),
        '5.02': ('Executive', 85, 'Departure/Election of Directors or Officers'),

        # Medium-high impact (60-79)
        '1.02': ('Contract', 70, 'Termination of Material Agreement'),
        '2.03': ('Asset Sale', 65, 'Creation of Direct Financial Obligation'),
        '2.04': ('Delisting', 75, 'Triggering Events That Accelerate Obligations'),
        '2.05': ('Accounting', 70, 'Costs Associated with Exit/Disposal'),
        '7.01': ('Earnings', 60, 'Regulation FD Disclosure'),

        # Medium impact (40-59)
        '1.04': ('Bankruptcy', 50, 'Mine Safety Disclosure'),
        '3.01': ('Stock', 55, 'Notice of Delisting'),
        '3.02': ('Stock', 50, 'Unregistered Sales of Equity Securities'),
        '4.01': ('Accounting', 50, 'Changes in Registrant Certifying Accountant'),
        '4.02': ('Accounting', 45, 'Non-Reliance on Previously Issued Financials'),

        # Low impact (20-39)
        '5.01': ('Governance', 30, 'Changes in Control of Registrant'),
        '5.03': ('Governance', 25, 'Amendments to Articles/Bylaws'),
        '5.04': ('Temporary Trading Suspension', 40, 'Temporary Trading Suspension'),
        '5.05': ('Listing', 30, 'Amendment to Code of Ethics'),
        '5.07': ('Shareholder Meeting', 20, 'Submission of Matters to Vote'),

        # Variable impact (catch-all)
        '8.01': ('Other', 50, 'Other Events'),
        '9.01': ('Exhibits', 10, 'Financial Statements and Exhibits')
    }

    def __init__(self, use_cik_mapper: bool = True):
        """Initialize SEC EDGAR monitor.

        Args:
            use_cik_mapper: Enable CIK-to-ticker mapping (default: True)
        """
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        self.seen_filings = set()  # Track accession numbers
        self.last_request_time = None
        self.use_cik_mapper = use_cik_mapper
        self.cik_mapper = None  # Will be initialized in __aenter__

        # User-Agent required by SEC
        self.headers = {
            'User-Agent': 'AI Trading System bot@example.com',  # SEC requires contact info
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)

        # Initialize CIK mapper if enabled
        if self.use_cik_mapper:
            try:
                from backend.data.sec_cik_mapper import SECCIKMapper
                self.cik_mapper = SECCIKMapper(use_redis=False)  # Memory-only for now
                await self.cik_mapper.initialize()
                self.logger.info("✅ CIK mapper initialized")
            except Exception as e:
                self.logger.warning(f"⚠️ CIK mapper unavailable: {e}")
                self.cik_mapper = None

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

        if self.cik_mapper:
            await self.cik_mapper.close()

    async def fetch_rss_feed(self, feed_type: str = 'recent') -> Optional[str]:
        """
        Fetch SEC RSS feed.

        Args:
            feed_type: 'recent' for 8-K only, 'all_filings' for all types

        Returns:
            XML string or None if failed
        """
        try:
            url = self.RSS_FEEDS.get(feed_type, self.RSS_FEEDS['recent'])

            # Rate limiting (be respectful to SEC)
            if self.last_request_time:
                elapsed = (datetime.now() - self.last_request_time).total_seconds()
                if elapsed < 0.2:  # Max 5 req/sec (well below 10 req/sec limit)
                    await asyncio.sleep(0.2 - elapsed)

            self.logger.info(f"🔍 Fetching SEC RSS feed: {feed_type}")

            if not self.session:
                self.session = aiohttp.ClientSession(headers=self.headers)

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                self.last_request_time = datetime.now()

                if response.status == 200:
                    content = await response.text()
                    self.logger.info(f"✅ Successfully fetched SEC feed (status: {response.status})")
                    return content
                else:
                    self.logger.error(f"❌ SEC feed fetch failed (status: {response.status})")
                    return None

        except Exception as e:
            self.logger.error(f"❌ Failed to fetch SEC RSS: {e}")
            return None

    async def parse_rss_feed(self, xml_content: str) -> List[SECFiling]:
        """
        Parse SEC Atom/RSS feed.

        Args:
            xml_content: XML/Atom feed content

        Returns:
            List of SEC filings
        """
        try:
            # Use feedparser for Atom feeds
            feed = feedparser.parse(xml_content)

            if not feed.entries:
                self.logger.warning("⚠️ No entries found in SEC feed")
                return []

            filings = []

            self.logger.info(f"📰 Found {len(feed.entries)} entries in SEC feed")

            for entry in feed.entries:
                try:
                    # Extract basic info
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    link = entry.get('link', '')
                    updated = entry.get('updated', '')

                    # Parse title: "8-K - COMPANY NAME (CIK)"
                    form_type_match = re.search(r'^([^-]+)', title)
                    form_type = form_type_match.group(1).strip() if form_type_match else "Unknown"

                    # Extract company name
                    company_match = re.search(r'-\s*(.+?)\s*\(', title)
                    company_name = company_match.group(1).strip() if company_match else "Unknown"

                    # Extract CIK
                    cik_match = re.search(r'\(([0-9]+)\)', title)
                    cik = cik_match.group(1) if cik_match else "0000000000"

                    # Extract accession number from link
                    # Link format: https://www.sec.gov/cgi-bin/viewer?action=view&cik=...&accession_number=...
                    accession_match = re.search(r'accession_number=([0-9\-]+)', link)
                    if not accession_match:
                        # Try alternative format
                        accession_match = re.search(r'/([0-9]{10}-[0-9]{2}-[0-9]{6})/', link)

                    accession_number = accession_match.group(1) if accession_match else link

                    # Skip if already seen
                    if accession_number in self.seen_filings:
                        continue

                    self.seen_filings.add(accession_number)

                    # Parse filing date
                    filing_date = datetime.now()
                    if updated:
                        try:
                            # feedparser typically parses this already
                            updated_struct = entry.get('updated_parsed')
                            if updated_struct:
                                import time
                                filing_date = datetime.fromtimestamp(time.mktime(updated_struct))
                        except Exception as e:
                            self.logger.warning(f"⚠️ Could not parse date: {updated}")

                    # Extract items from summary
                    items = self._extract_items(summary)

                    # Classify impact
                    impact_category, impact_score = self._classify_impact(items)

                    # Look up ticker from CIK
                    ticker = None
                    if self.cik_mapper:
                        try:
                            ticker = await self.cik_mapper.cik_to_ticker_symbol(cik)
                        except Exception as e:
                            self.logger.debug(f"⚠️ CIK lookup failed for {cik}: {e}")

                    filing = SECFiling(
                        company_name=company_name,
                        ticker=ticker,
                        cik=cik,
                        form_type=form_type,
                        filing_date=filing_date,
                        items=items,
                        description=summary[:200],  # Truncate
                        url=link,
                        accession_number=accession_number,
                        impact_category=impact_category,
                        impact_score=impact_score
                    )

                    filings.append(filing)

                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to parse SEC entry: {e}")
                    continue

            self.logger.info(f"✅ Parsed {len(filings)} SEC filings")
            return filings

        except Exception as e:
            self.logger.error(f"❌ Failed to parse SEC feed: {e}")
            return []

    def _extract_items(self, summary: str) -> List[str]:
        """
        Extract Item codes from filing summary.

        Args:
            summary: Filing description text

        Returns:
            List of item codes (e.g. ["1.01", "9.01"])
        """
        # Look for patterns like "Item 1.01", "Item 5.02"
        item_pattern = r'Item\s+(\d+\.\d+)'
        matches = re.findall(item_pattern, summary, re.IGNORECASE)

        # Deduplicate and sort
        items = sorted(set(matches))

        return items

    def _classify_impact(self, items: List[str]) -> tuple[str, float]:
        """
        Classify filing impact based on Item codes.

        Args:
            items: List of item codes

        Returns:
            (category, impact_score)
        """
        if not items:
            return ('Other', 30)

        # Find highest impact item
        max_score = 0
        max_category = 'Other'

        for item in items:
            if item in self.ITEM_IMPACT:
                category, score, description = self.ITEM_IMPACT[item]
                if score > max_score:
                    max_score = score
                    max_category = category

        return (max_category, max_score if max_score > 0 else 30)

    async def collect(self, min_score: float = 60) -> List[SECFiling]:
        """
        Collect latest 8-K filings.

        Args:
            min_score: Minimum impact score to return

        Returns:
            List of high-impact filings
        """
        try:
            self.logger.info("🚀 Starting SEC EDGAR collection...")

            # Fetch RSS feed
            xml_content = await self.fetch_rss_feed('recent')
            if not xml_content:
                self.logger.error("❌ Failed to fetch SEC feed")
                return []

            # Parse filings
            filings = await self.parse_rss_feed(xml_content)
            if not filings:
                self.logger.warning("⚠️ No filings parsed")
                return []

            # Filter by score
            high_impact = [f for f in filings if f.impact_score and f.impact_score >= min_score]

            self.logger.info(f"🔥 {len(high_impact)} high-impact filings (>= {min_score})")

            return high_impact

        except Exception as e:
            self.logger.error(f"❌ Collection failed: {e}")
            return []

    async def collect_loop(self, interval: int = 120, duration: int = 3600, min_score: float = 60):
        """
        Run continuous collection loop.

        Args:
            interval: Seconds between collections (default: 2 min)
            duration: Total duration in seconds (default: 1 hour)
            min_score: Minimum impact score
        """
        start_time = datetime.now()
        iteration = 0

        self.logger.info(f"🔄 Starting SEC collection loop: {interval}s interval, {duration}s duration")

        try:
            async with self:  # Use context manager
                while (datetime.now() - start_time).total_seconds() < duration:
                    iteration += 1
                    self.logger.info(f"\n{'='*60}\n🔄 Iteration {iteration}\n{'='*60}")

                    filings = await self.collect(min_score=min_score)

                    if filings:
                        self.logger.info(f"✅ Collected {len(filings)} filings:")
                        for filing in filings[:5]:  # Show first 5
                            score_str = f" [Score: {filing.impact_score:.0f}]" if filing.impact_score else ""
                            items_str = f" (Items: {', '.join(filing.items)})" if filing.items else ""
                            self.logger.info(f"  • {filing.company_name} - {filing.impact_category}{score_str}{items_str}")
                    else:
                        self.logger.info("⚠️ No high-impact filings")

                    # Wait for next iteration
                    await asyncio.sleep(interval)

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

    async def main():
        monitor = SECEdgarMonitor()

        if len(sys.argv) > 1 and sys.argv[1] == "loop":
            # Continuous mode
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 120
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
            await monitor.collect_loop(interval=interval, duration=duration, min_score=60)
        else:
            # Single collection
            async with monitor:
                filings = await monitor.collect(min_score=60)

                print(f"\n{'='*80}")
                print(f"🔥 HIGH IMPACT SEC 8-K FILINGS ({len(filings)} items)")
                print(f"{'='*80}\n")

                for i, filing in enumerate(filings, 1):
                    print(f"{i}. [{filing.impact_score:.0f}] {filing.impact_category} - {filing.company_name}")
                    print(f"   Form: {filing.form_type} | CIK: {filing.cik}")
                    print(f"   Items: {', '.join(filing.items)}")
                    print(f"   Date: {filing.filing_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   URL: {filing.url}")
                    print()

    asyncio.run(main())
