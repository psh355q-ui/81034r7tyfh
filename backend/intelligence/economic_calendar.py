"""
Economic Calendar Integration for Event Legitimacy Detection.

Integrates with various financial data APIs to fetch scheduled events:
- Earnings reports (company quarterly/annual reports)
- FOMC meetings (Federal Reserve decisions)
- Economic data releases (CPI, NFP, GDP, etc.)
- Central bank announcements

This data is used by the EL (Event Legitimacy) signal in the
4-Signal Consensus Framework.

Author: AI Trading System Team
Date: 2025-12-19
Phase: 18
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of economic events."""
    EARNINGS = "EARNINGS"           # Company earnings reports
    FOMC = "FOMC"                   # Federal Reserve meetings
    CPI = "CPI"                     # Consumer Price Index
    NFP = "NFP"                     # Non-Farm Payrolls
    GDP = "GDP"                     # Gross Domestic Product
    RETAIL_SALES = "RETAIL_SALES"   # Retail sales data
    UNEMPLOYMENT = "UNEMPLOYMENT"   # Unemployment rate
    PPI = "PPI"                     # Producer Price Index
    HOUSING = "HOUSING"             # Housing data
    PMI = "PMI"                     # Purchasing Managers' Index
    CENTRAL_BANK = "CENTRAL_BANK"   # Other central bank events
    FDA = "FDA"                     # FDA approvals (pharma)
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"  # Product announcements
    OTHER = "OTHER"


class EventImportance(str, Enum):
    """Event importance levels."""
    HIGH = "HIGH"       # Market-moving events
    MEDIUM = "MEDIUM"   # Notable but not critical
    LOW = "LOW"         # Minor events


@dataclass
class EconomicEvent:
    """Scheduled economic event."""
    event_type: EventType
    event_name: str
    ticker: Optional[str]  # For company-specific events (earnings)
    scheduled_time: datetime
    importance: EventImportance
    description: str
    country: str = "US"
    source: str = "manual"  # API source


class EconomicCalendar:
    """
    Economic calendar for Event Legitimacy detection.

    Provides scheduled event data for matching against news clusters.
    """

    def __init__(self):
        """Initialize the calendar."""
        self.logger = logging.getLogger(__name__)
        self.events: List[EconomicEvent] = []

        # Load default events (static data)
        self._load_default_events()

        self.logger.info(
            f"EconomicCalendar initialized with {len(self.events)} events"
        )

    def _load_default_events(self):
        """Load default scheduled events (2025-2026)."""
        now = datetime.now()
        current_year = now.year
        next_year = current_year + 1

        # FOMC Meetings (8 scheduled meetings per year)
        fomc_dates = [
            datetime(current_year, 12, 18, 14, 0),  # December (if future)
            datetime(next_year, 1, 29, 14, 0),      # January
            datetime(next_year, 3, 19, 14, 0),      # March
            datetime(next_year, 5, 7, 14, 0),       # May
            datetime(next_year, 6, 18, 14, 0),      # June
            datetime(next_year, 7, 30, 14, 0),      # July
            datetime(next_year, 9, 17, 14, 0),      # September
            datetime(next_year, 11, 5, 14, 0),      # November
            datetime(next_year, 12, 17, 14, 0),     # December
        ]

        for date in fomc_dates:
            if date > now:
                self.events.append(EconomicEvent(
                    event_type=EventType.FOMC,
                    event_name="FOMC Meeting Decision",
                    ticker=None,
                    scheduled_time=date,
                    importance=EventImportance.HIGH,
                    description="Federal Reserve interest rate decision",
                    country="US",
                    source="FED"
                ))

        # Monthly CPI releases (typically 8:30 AM ET, ~13th of each month)
        # Add for next 12 months from now
        for i in range(12):
            target_month = (now.month + i - 1) % 12 + 1
            target_year = now.year + (now.month + i - 1) // 12

            try:
                cpi_date = datetime(target_year, target_month, 13, 8, 30)
                if cpi_date > now:
                    self.events.append(EconomicEvent(
                        event_type=EventType.CPI,
                        event_name=f"CPI {cpi_date.strftime('%B %Y')}",
                        ticker=None,
                        scheduled_time=cpi_date,
                        importance=EventImportance.HIGH,
                        description="Consumer Price Index (inflation data)",
                        country="US",
                        source="BLS"
                    ))
            except ValueError:
                pass

        # Monthly NFP releases (first Friday, 8:30 AM ET)
        # Add for next 12 months from now
        for i in range(12):
            target_month = (now.month + i - 1) % 12 + 1
            target_year = now.year + (now.month + i - 1) // 12

            # Find first Friday of the month
            first_day = datetime(target_year, target_month, 1)
            days_until_friday = (4 - first_day.weekday()) % 7
            nfp_date = first_day + timedelta(days=days_until_friday)
            nfp_date = nfp_date.replace(hour=8, minute=30)

            if nfp_date > now:
                self.events.append(EconomicEvent(
                    event_type=EventType.NFP,
                    event_name=f"Non-Farm Payrolls {nfp_date.strftime('%B %Y')}",
                    ticker=None,
                    scheduled_time=nfp_date,
                    importance=EventImportance.HIGH,
                    description="Monthly jobs report",
                    country="US",
                    source="BLS"
                ))

    def add_event(self, event: EconomicEvent):
        """Add a new event to the calendar."""
        self.events.append(event)
        self.logger.debug(f"Added event: {event.event_name} at {event.scheduled_time}")

    def find_matching_event(
        self,
        timestamp: datetime,
        ticker: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        time_window_minutes: int = 30
    ) -> Optional[EconomicEvent]:
        """
        Find an event matching the given criteria.

        Args:
            timestamp: When the news appeared
            ticker: Stock ticker (for earnings)
            keywords: Keywords from news (for event type matching)
            time_window_minutes: Max time difference (default: 30 min)

        Returns:
            Matching EconomicEvent or None
        """
        time_window = timedelta(minutes=time_window_minutes)

        for event in self.events:
            # Check time window
            time_diff = abs(timestamp - event.scheduled_time)
            if time_diff > time_window:
                continue

            # Check ticker (for company-specific events)
            if ticker and event.ticker:
                if ticker.upper() == event.ticker.upper():
                    self.logger.debug(
                        f"Matched event by ticker: {event.event_name} "
                        f"(time diff: {time_diff.total_seconds():.0f}s)"
                    )
                    return event

            # Check keywords (for macro events)
            if keywords:
                event_keywords = event.event_name.lower() + " " + event.description.lower()
                if any(kw.lower() in event_keywords for kw in keywords):
                    self.logger.debug(
                        f"Matched event by keywords: {event.event_name} "
                        f"(time diff: {time_diff.total_seconds():.0f}s)"
                    )
                    return event

        return None

    def get_upcoming_events(
        self,
        hours: int = 24,
        ticker: Optional[str] = None,
        event_type: Optional[EventType] = None
    ) -> List[EconomicEvent]:
        """
        Get upcoming events within the next N hours.

        Args:
            hours: Look-ahead window (default: 24 hours)
            ticker: Filter by ticker (optional)
            event_type: Filter by event type (optional)

        Returns:
            List of upcoming EconomicEvent
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)

        upcoming = [
            event for event in self.events
            if now <= event.scheduled_time <= cutoff
        ]

        # Apply filters
        if ticker:
            upcoming = [e for e in upcoming if e.ticker == ticker]

        if event_type:
            upcoming = [e for e in upcoming if e.event_type == event_type]

        # Sort by time
        upcoming.sort(key=lambda e: e.scheduled_time)

        return upcoming

    def get_stats(self) -> Dict:
        """Get calendar statistics."""
        now = datetime.now()

        past_events = [e for e in self.events if e.scheduled_time < now]
        future_events = [e for e in self.events if e.scheduled_time >= now]

        event_type_counts = {}
        for event in self.events:
            event_type_counts[event.event_type.value] = \
                event_type_counts.get(event.event_type.value, 0) + 1

        return {
            "total_events": len(self.events),
            "past_events": len(past_events),
            "future_events": len(future_events),
            "event_types": event_type_counts,
        }


# Singleton instance
_calendar_instance: Optional[EconomicCalendar] = None


def get_calendar() -> EconomicCalendar:
    """Get or create the global calendar instance."""
    global _calendar_instance
    if _calendar_instance is None:
        _calendar_instance = EconomicCalendar()
    return _calendar_instance


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Economic Calendar Test")
    print("=" * 80)
    print()

    calendar = EconomicCalendar()

    # Show statistics
    stats = calendar.get_stats()
    print("Calendar Statistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Future events: {stats['future_events']}")
    print(f"  Past events: {stats['past_events']}")
    print()
    print("Event types:")
    for event_type, count in stats['event_types'].items():
        print(f"  {event_type}: {count}")
    print()

    # Show upcoming events
    print("-" * 80)
    print("Upcoming Events (Next 7 Days)")
    print("-" * 80)

    upcoming = calendar.get_upcoming_events(hours=7*24)
    if upcoming:
        for event in upcoming[:10]:  # Show first 10
            print(
                f"{event.scheduled_time.strftime('%Y-%m-%d %H:%M')} | "
                f"{event.importance.value:6} | "
                f"{event.event_name}"
            )
    else:
        print("No upcoming events in the next 7 days")
    print()

    # Test matching
    print("-" * 80)
    print("Event Matching Tests")
    print("-" * 80)

    # Test 1: FOMC meeting (exact time)
    fomc_time = datetime(2025, 3, 19, 14, 0)  # March FOMC
    matched = calendar.find_matching_event(
        timestamp=fomc_time,
        keywords=["fomc", "fed", "interest rate"]
    )
    print(f"Test 1 - FOMC matching: {'✅ MATCHED' if matched else '❌ NOT FOUND'}")
    if matched:
        print(f"  Event: {matched.event_name}")
        print(f"  Type: {matched.event_type.value}")
    print()

    # Test 2: CPI release (with time window)
    cpi_time = datetime(2025, 1, 13, 8, 35)  # 5 min after scheduled
    matched = calendar.find_matching_event(
        timestamp=cpi_time,
        keywords=["cpi", "inflation"],
        time_window_minutes=10
    )
    print(f"Test 2 - CPI matching: {'✅ MATCHED' if matched else '❌ NOT FOUND'}")
    if matched:
        print(f"  Event: {matched.event_name}")
        print(f"  Scheduled: {matched.scheduled_time}")
        print(f"  Time diff: {abs(cpi_time - matched.scheduled_time).total_seconds():.0f}s")
    print()

    # Test 3: No match
    random_time = datetime(2025, 1, 15, 14, 23)  # Random time
    matched = calendar.find_matching_event(
        timestamp=random_time,
        keywords=["random", "test"]
    )
    print(f"Test 3 - Random time: {'✅ MATCHED' if matched else '❌ NOT FOUND (expected)'}")
    print()

    # Add custom earnings event
    print("-" * 80)
    print("Adding Custom Earnings Event")
    print("-" * 80)

    earnings_event = EconomicEvent(
        event_type=EventType.EARNINGS,
        event_name="Apple Q1 2025 Earnings",
        ticker="AAPL",
        scheduled_time=datetime(2025, 1, 30, 16, 0),
        importance=EventImportance.HIGH,
        description="Apple quarterly earnings report",
        country="US",
        source="manual"
    )
    calendar.add_event(earnings_event)

    # Test earnings matching
    earnings_time = datetime(2025, 1, 30, 16, 2)  # 2 min after release
    matched = calendar.find_matching_event(
        timestamp=earnings_time,
        ticker="AAPL",
        time_window_minutes=10
    )
    print(f"Earnings matching: {'✅ MATCHED' if matched else '❌ NOT FOUND'}")
    if matched:
        print(f"  Event: {matched.event_name}")
        print(f"  Ticker: {matched.ticker}")
    print()

    print("=" * 80)
    print("Economic Calendar test completed!")
    print("=" * 80)
