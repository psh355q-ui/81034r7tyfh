"""
Point-in-Time Data Access for Backtesting

Prevents Lookahead Bias by ensuring:
- Only data available at simulation time is accessed
- News crawled_at (not published_at) is used for availability
- AI analyses completed before simulation time only

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class PointInTimeDataAccess:
    """
    Point-in-Time data access layer for backtesting.
    
    CRITICAL: This class ensures NO FUTURE DATA is leaked into backtest.
    All queries are filtered by the simulation timestamp.
    """
    
    def __init__(self, db: Session):
        """
        Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._current_simulation_time: Optional[datetime] = None
        self._lookahead_violations: List[Dict[str, Any]] = []
    
    def set_simulation_time(self, timestamp: datetime):
        """
        Set the current simulation time.
        
        All subsequent queries will only return data
        that was available at this exact moment.
        
        Args:
            timestamp: The simulation timestamp
        """
        self._current_simulation_time = timestamp
        logger.debug(f"Simulation time set to: {timestamp.isoformat()}")
    
    def get_simulation_time(self) -> datetime:
        """Get current simulation time"""
        if self._current_simulation_time is None:
            raise ValueError("Simulation time not set. Call set_simulation_time() first.")
        return self._current_simulation_time
    
    def get_available_news(
        self,
        NewsArticle,  # SQLAlchemy model
        max_age_hours: int = 24,
        min_impact: Optional[float] = None,
        ticker: Optional[str] = None,
    ) -> List:
        """
        Get news articles that were AVAILABLE at simulation time.
        
        CRITICAL: Uses crawled_at, NOT published_at!
        
        A news article is considered "available" when:
        1. It was crawled (crawled_at) BEFORE or AT simulation time
        2. Optionally filtered by age from simulation time
        
        Args:
            NewsArticle: SQLAlchemy model for news articles
            max_age_hours: Only news within this age (from sim time)
            min_impact: Minimum impact magnitude filter
            ticker: Filter by specific ticker relevance
        
        Returns:
            List of news articles available at simulation time
        """
        sim_time = self.get_simulation_time()
        
        # Base query: crawled BEFORE simulation time
        query = self.db.query(NewsArticle).filter(
            NewsArticle.crawled_at <= sim_time
        )
        
        # Age filter (from simulation time, not current time)
        if max_age_hours > 0:
            cutoff = sim_time - timedelta(hours=max_age_hours)
            query = query.filter(NewsArticle.crawled_at >= cutoff)
        
        # Impact filter (if news has analysis)
        if min_impact is not None:
            # Join with analysis table
            from data.news_models import NewsAnalysis
            query = query.join(NewsAnalysis).filter(
                and_(
                    NewsAnalysis.impact_magnitude >= min_impact,
                    NewsAnalysis.analyzed_at <= sim_time  # Analysis must be done before sim time!
                )
            )
        
        # Ticker filter
        if ticker:
            from data.news_models import NewsTickerRelevance
            query = query.join(NewsTickerRelevance).filter(
                NewsTickerRelevance.ticker_symbol == ticker.upper()
            )
        
        articles = query.order_by(NewsArticle.crawled_at.desc()).all()
        
        logger.debug(
            f"PiT Query: {len(articles)} articles available at {sim_time.isoformat()} "
            f"(max_age={max_age_hours}h, min_impact={min_impact}, ticker={ticker})"
        )
        
        return articles
    
    def get_available_analyses(
        self,
        NewsAnalysis,  # SQLAlchemy model
        actionable_only: bool = False,
        min_confidence: float = 0.0,
    ) -> List:
        """
        Get AI analyses that were COMPLETED at simulation time.
        
        CRITICAL: Uses analyzed_at timestamp!
        
        Args:
            NewsAnalysis: SQLAlchemy model
            actionable_only: Filter for trading_actionable=True
            min_confidence: Minimum sentiment confidence
        
        Returns:
            List of analyses available at simulation time
        """
        sim_time = self.get_simulation_time()
        
        # Base query: analysis completed BEFORE simulation time
        query = self.db.query(NewsAnalysis).filter(
            NewsAnalysis.analyzed_at <= sim_time
        )
        
        if actionable_only:
            query = query.filter(NewsAnalysis.trading_actionable == True)
        
        if min_confidence > 0:
            query = query.filter(NewsAnalysis.sentiment_confidence >= min_confidence)
        
        analyses = query.order_by(NewsAnalysis.analyzed_at.desc()).all()
        
        logger.debug(f"PiT Query: {len(analyses)} analyses available at {sim_time.isoformat()}")
        
        return analyses
    
    def get_market_data(
        self,
        ticker: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get market data available at simulation time.
        
        For backtesting, this would query your price database
        or cached historical data up to simulation time.
        
        Args:
            ticker: Stock symbol
            lookback_days: Days of history to retrieve
        
        Returns:
            Dictionary with price data, volume, etc.
        """
        sim_time = self.get_simulation_time()
        
        # TODO: Implement based on your price data storage
        # Example structure:
        # query = self.db.query(PriceData).filter(
        #     and_(
        #         PriceData.ticker == ticker,
        #         PriceData.timestamp <= sim_time,
        #         PriceData.timestamp >= sim_time - timedelta(days=lookback_days)
        #     )
        # ).order_by(PriceData.timestamp.desc()).all()
        
        logger.debug(f"PiT Query: Market data for {ticker} at {sim_time.isoformat()}")
        
        return {
            "ticker": ticker,
            "as_of": sim_time.isoformat(),
            "lookback_days": lookback_days,
            "data": []  # Placeholder
        }
    
    def validate_no_lookahead(
        self,
        data_timestamp: datetime,
        data_source: str = "unknown",
    ) -> bool:
        """
        Validate that data timestamp is NOT in the future relative to simulation.
        
        Call this when using any external data to ensure no lookahead bias.
        
        Args:
            data_timestamp: Timestamp of the data being used
            data_source: Description of data source (for logging)
        
        Returns:
            True if valid (no lookahead), False if violation
        """
        sim_time = self.get_simulation_time()
        
        if data_timestamp > sim_time:
            violation = {
                "simulation_time": sim_time.isoformat(),
                "data_timestamp": data_timestamp.isoformat(),
                "data_source": data_source,
                "lookahead_seconds": (data_timestamp - sim_time).total_seconds(),
            }
            self._lookahead_violations.append(violation)
            
            logger.error(
                f"🚨 LOOKAHEAD BIAS DETECTED!\n"
                f"  Simulation Time: {sim_time.isoformat()}\n"
                f"  Data Timestamp: {data_timestamp.isoformat()}\n"
                f"  Source: {data_source}\n"
                f"  Lookahead: {violation['lookahead_seconds']:.1f} seconds"
            )
            
            return False
        
        return True
    
    def get_lookahead_violations(self) -> List[Dict[str, Any]]:
        """Get all detected lookahead bias violations"""
        return self._lookahead_violations.copy()
    
    def clear_violations(self):
        """Clear violation log"""
        self._lookahead_violations = []
    
    def check_integrity(self) -> Dict[str, Any]:
        """
        Check data integrity for backtesting.
        
        Returns:
            Dictionary with integrity check results
        """
        return {
            "simulation_time": self._current_simulation_time.isoformat() if self._current_simulation_time else None,
            "lookahead_violations": len(self._lookahead_violations),
            "violations": self._lookahead_violations[-10:],  # Last 10
            "status": "OK" if len(self._lookahead_violations) == 0 else "VIOLATIONS_DETECTED",
        }


class BacktestNewsSignalValidator:
    """
    Validates that news-based signals don't use future information.
    
    Integrates with NewsSignalGenerator to ensure Point-in-Time compliance.
    """
    
    def __init__(self, pit_access: PointInTimeDataAccess):
        """
        Args:
            pit_access: Point-in-Time data access layer
        """
        self.pit = pit_access
        self._signal_timestamps: List[Dict[str, Any]] = []
    
    def validate_signal_generation(
        self,
        signal_timestamp: datetime,
        news_used: List,  # List of NewsArticle objects
        analysis_used: Optional[Any] = None,
    ) -> bool:
        """
        Validate that signal generation only used available data.
        
        Args:
            signal_timestamp: When the signal was "generated" in simulation
            news_used: News articles used for signal
            analysis_used: AI analysis used for signal
        
        Returns:
            True if valid, False if lookahead detected
        """
        valid = True
        
        # Check each news article
        for article in news_used:
            if hasattr(article, 'crawled_at'):
                if not self.pit.validate_no_lookahead(
                    article.crawled_at,
                    f"NewsArticle:{article.id}"
                ):
                    valid = False
        
        # Check analysis timestamp
        if analysis_used and hasattr(analysis_used, 'analyzed_at'):
            if not self.pit.validate_no_lookahead(
                analysis_used.analyzed_at,
                f"NewsAnalysis:{analysis_used.id}"
            ):
                valid = False
        
        # Log signal
        self._signal_timestamps.append({
            "signal_time": signal_timestamp,
            "news_count": len(news_used),
            "valid": valid,
        })
        
        return valid
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report"""
        total = len(self._signal_timestamps)
        valid = sum(1 for s in self._signal_timestamps if s["valid"])
        
        return {
            "total_signals": total,
            "valid_signals": valid,
            "invalid_signals": total - valid,
            "validity_rate": valid / total if total > 0 else 1.0,
            "pit_violations": len(self.pit.get_lookahead_violations()),
        }


# ============================================================================
# Example Integration with BacktestEngine
# ============================================================================

"""
Example: How to use in your backtest engine

class EventDrivenBacktestEngine:
    def __init__(self, db):
        self.db = db
        self.pit_access = PointInTimeDataAccess(db)
        self.signal_validator = BacktestNewsSignalValidator(self.pit_access)
    
    async def run_backtest(self, start_date, end_date, strategy):
        results = []
        
        # Simulate each trading day
        current_time = start_date
        while current_time <= end_date:
            # Set simulation time
            self.pit_access.set_simulation_time(current_time)
            
            # Get ONLY news available at this time
            available_news = self.pit_access.get_available_news(
                NewsArticle,
                max_age_hours=24,
                min_impact=0.5
            )
            
            # Generate signals from available news
            for news in available_news:
                if news.analysis:
                    # Validate we're not using future analysis
                    is_valid = self.signal_validator.validate_signal_generation(
                        current_time,
                        [news],
                        news.analysis
                    )
                    
                    if not is_valid:
                        logger.error(f"Signal rejected: lookahead bias detected")
                        continue
                    
                    signal = strategy.generate_signal(news.analysis)
                    results.append(signal)
            
            # Move to next time step
            current_time += timedelta(hours=1)
        
        # Final integrity check
        integrity = self.pit_access.check_integrity()
        if integrity["status"] != "OK":
            logger.error(f"Backtest has lookahead bias! {integrity}")
        
        return {
            "signals": results,
            "integrity": integrity,
            "validation": self.signal_validator.get_validation_report()
        }
"""


if __name__ == "__main__":
    # Test Point-in-Time access
    print("Point-in-Time Data Access Module")
    print("================================")
    print("")
    print("This module ensures backtest integrity by:")
    print("1. Using crawled_at (not published_at) for news availability")
    print("2. Using analyzed_at for AI analysis availability")
    print("3. Detecting and logging lookahead bias violations")
    print("4. Providing validation reports")
    print("")
    print("Integration:")
    print("  pit = PointInTimeDataAccess(db)")
    print("  pit.set_simulation_time(datetime(2025, 1, 1, 9, 30))")
    print("  news = pit.get_available_news(NewsArticle, max_age_hours=24)")
    print("  # Returns only news crawled before 2025-01-01 09:30")
