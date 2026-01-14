"""
Economic Calendar Service
- Tracks key macro economic events (CPI, FOMC, Jobs Report)
- Currently uses a manual/simulated schedule for MVP or scrape-ready structure
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EconomicCalendarService:
    def __init__(self):
        # MVP: Pre-defined important events (Mock data or manual maintenance)
        # In production, integrate with Investing.com scraper or AlphaVantage/Fred API
        self.events_db = [
            {"date": "2026-01-15", "event": "CPI Data Release", "impact": "HIGH"},
            {"date": "2026-01-28", "event": "FOMC Meeting", "impact": "CRITICAL"},
            {"date": "2026-02-06", "event": "Non-Farm Payrolls", "impact": "HIGH"},
            {"date": "2026-02-12", "event": "PPI Data Release", "impact": "MEDIUM"},
            {"date": "2026-03-18", "event": "FOMC Meeting", "impact": "CRITICAL"},
            {"date": "2026-04-15", "event": "GDP Growth Rate", "impact": "HIGH"},
        ]

    async def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get economic events for the next N days.
        """
        today = datetime.now()
        end_date = today + timedelta(days=days)
        results = []
        
        for event in self.events_db:
            evt_date = datetime.strptime(event['date'], "%Y-%m-%d")
            
            if today <= evt_date <= end_date:
                days_until = (evt_date - today).days
                results.append({
                    "event": event['event'],
                    "date": event['date'],
                    "impact": event['impact'],
                    "days_until": days_until
                })
                
        return sorted(results, key=lambda x: x['days_until'])

    def check_high_impact_today(self) -> bool:
        """Check if there is a high impact event today"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        for event in self.events_db:
            if event['date'] == today_str and event['impact'] in ["HIGH", "CRITICAL"]:
                return True
        return False
