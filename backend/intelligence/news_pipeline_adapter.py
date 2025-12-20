"""
News Pipeline Adapter for 4-Signal Framework Integration.

This adapter bridges the existing news pipeline with the 4-Signal Consensus Framework,
enabling automatic manipulation detection and credibility assessment for all incoming news.

Integration Points:
- NewsDeepAnalyzer (backend/data/news_analyzer.py)
- NewsArticle models (backend/data/news_models.py)
- Trading signal generation (backend/signals/news_signal_generator.py)

Author: AI Trading System Team
Date: 2025-12-19
Phase: 18
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

try:
    from backend.intelligence.news_clustering import NewsClusteringEngine
    from backend.intelligence.four_signal_framework import (
        NewsArticle as FourSignalArticle,
        NewsCluster,
        Verdict
    )
    from backend.intelligence.source_classifier import get_classifier
    from backend.intelligence.economic_calendar import get_calendar
    from backend.data.news_models import NewsArticle, NewsAnalysis
except ImportError:
    # Standalone mode
    from news_clustering import NewsClusteringEngine
    from four_signal_framework import (
        NewsArticle as FourSignalArticle,
        NewsCluster,
        Verdict
    )
    from source_classifier import get_classifier
    from economic_calendar import get_calendar

logger = logging.getLogger(__name__)


class NewsPipelineAdapter:
    """
    Adapter for integrating 4-Signal Framework with existing news pipeline.

    Usage:
        adapter = NewsPipelineAdapter(db_session)

        # Process incoming news
        result = adapter.process_news_article(
            article_id=123,
            ticker="AAPL",
            title="Apple beats Q4 earnings",
            content="Apple reported...",
            source="Bloomberg",
            published_at=datetime.now()
        )

        # Check if trading signal should be blocked
        if result['verdict'] == 'MANIPULATION_ATTACK':
            # Block signal
            pass
        elif result['verdict'] == 'EMBARGO_EVENT':
            # Boost signal
            confidence *= result['confidence_multiplier']
    """

    def __init__(self, db: Session):
        """
        Initialize the adapter.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.clustering_engine = NewsClusteringEngine(
            time_window_minutes=60,
            min_cluster_size=2
        )
        self.source_classifier = get_classifier()
        self.calendar = get_calendar()

        logger.info("NewsPipelineAdapter initialized")

    def process_news_article(
        self,
        article_id: int,
        ticker: str,
        title: str,
        content: str,
        source: str,
        published_at: datetime,
        url: Optional[str] = None,
        sentiment: Optional[float] = None
    ) -> Dict:
        """
        Process a news article through the 4-Signal Framework.

        Args:
            article_id: Database article ID
            ticker: Stock ticker
            title: Article title
            content: Article content
            source: News source name
            published_at: Publication timestamp
            url: Article URL (optional)
            sentiment: Sentiment score -1 to +1 (optional)

        Returns:
            Dict with:
                - verdict: Verdict classification
                - confidence_multiplier: Trading signal adjustment (0.0-1.5)
                - nfpi: News Fraud Probability Index (0-100)
                - cluster_id: Cluster fingerprint
                - should_trade: Boolean recommendation
                - cooling_until: Cooling period end time (if applicable)
                - reason: Verdict explanation
        """
        # Convert to 4-Signal article format
        four_signal_article = self._convert_to_four_signal_article(
            article_id=str(article_id),
            ticker=ticker,
            title=title,
            content=content,
            source=source,
            published_at=published_at,
            url=url,
            sentiment=sentiment
        )

        # Add to clustering engine
        cluster = self.clustering_engine.add_article(four_signal_article)

        if cluster is None:
            # Cluster not yet formed (need more articles)
            logger.debug(
                f"Article {article_id} added to clustering engine, "
                f"waiting for more articles"
            )
            return {
                "verdict": "PENDING",
                "confidence_multiplier": 1.0,
                "nfpi": 50.0,  # Neutral
                "cluster_id": None,
                "should_trade": True,  # Allow trading for now
                "cooling_until": None,
                "reason": "Cluster not yet formed, need more similar articles"
            }

        # Cluster formed, calculate NFPI
        nfpi = self.clustering_engine.nfpi_calculator.calculate_nfpi(cluster)

        # Determine if trading should proceed
        should_trade = self._should_allow_trading(cluster)

        # Store cluster info in database (optional)
        self._save_cluster_to_db(cluster, nfpi)

        logger.info(
            f"Article {article_id} processed: {cluster.verdict.value}, "
            f"NFPI={nfpi:.1f}%, confidence=×{cluster.confidence_multiplier:.2f}"
        )

        return {
            "verdict": cluster.verdict.value,
            "confidence_multiplier": cluster.confidence_multiplier,
            "nfpi": nfpi,
            "cluster_id": cluster.fingerprint,
            "should_trade": should_trade,
            "cooling_until": cluster.cooling_until,
            "reason": cluster.verdict_reason,
            "di_score": cluster.di_score,
            "tn_score": cluster.tn_score,
            "ni_score": cluster.ni_score,
            "el_matched": cluster.el_matched,
        }

    def _convert_to_four_signal_article(
        self,
        article_id: str,
        ticker: str,
        title: str,
        content: str,
        source: str,
        published_at: datetime,
        url: Optional[str] = None,
        sentiment: Optional[float] = None
    ) -> FourSignalArticle:
        """Convert database article to 4-Signal format."""
        # Classify source tier
        source_info = self.source_classifier.classify(source, url)

        return FourSignalArticle(
            id=article_id,
            ticker=ticker,
            title=title,
            content=content or title,  # Fallback to title if no content
            source=source,
            source_tier=source_info.tier.value,
            published_at=published_at,
            url=url,
            sentiment=sentiment
        )

    def _should_allow_trading(self, cluster: NewsCluster) -> bool:
        """
        Determine if trading signal should be allowed based on verdict.

        Returns:
            True if trading should proceed, False if blocked
        """
        # Block manipulation attacks completely
        if cluster.verdict == Verdict.MANIPULATION_ATTACK:
            logger.warning(
                f"⚠️  Trading BLOCKED for {cluster.ticker}: "
                f"Manipulation attack detected"
            )
            return False

        # Check cooling period
        if cluster.cooling_until and datetime.now() < cluster.cooling_until:
            logger.warning(
                f"⚠️  Trading BLOCKED for {cluster.ticker}: "
                f"In cooling period until {cluster.cooling_until}"
            )
            return False

        # Allow trading for other verdicts
        return True

    def _save_cluster_to_db(self, cluster: NewsCluster, nfpi: float):
        """
        Save cluster information to database.

        Note: This requires the database migration 006_create_news_clusters.sql
        to be run first.
        """
        try:
            from backend.data.news_models import NewsClusterDB

            # Check if cluster already exists
            existing = self.db.query(NewsClusterDB).filter_by(
                fingerprint=cluster.fingerprint
            ).first()

            if existing:
                # Update existing cluster
                existing.last_seen = cluster.last_seen
                existing.article_count = len(cluster.articles)
                existing.di_score = cluster.di_score
                existing.tn_score = cluster.tn_score
                existing.ni_score = cluster.ni_score
                existing.el_matched = cluster.el_matched
                existing.el_confidence = cluster.el_confidence
                existing.el_event_name = cluster.el_event_name
                existing.verdict = cluster.verdict.value
                existing.verdict_reason = cluster.verdict_reason
                existing.confidence_multiplier = cluster.confidence_multiplier
                existing.cooling_intensity = cluster.cooling_intensity
                existing.cooling_until = cluster.cooling_until
                existing.nfpi_score = nfpi
                existing.updated_at = datetime.now()
            else:
                # Create new cluster
                new_cluster = NewsClusterDB(
                    fingerprint=cluster.fingerprint,
                    ticker=cluster.ticker,
                    theme=cluster.theme,
                    first_seen=cluster.first_seen,
                    last_seen=cluster.last_seen,
                    article_count=len(cluster.articles),
                    di_score=cluster.di_score,
                    tn_score=cluster.tn_score,
                    ni_score=cluster.ni_score,
                    el_matched=cluster.el_matched,
                    el_confidence=cluster.el_confidence,
                    el_event_name=cluster.el_event_name,
                    verdict=cluster.verdict.value,
                    verdict_reason=cluster.verdict_reason,
                    confidence_multiplier=cluster.confidence_multiplier,
                    cooling_intensity=cluster.cooling_intensity,
                    cooling_until=cluster.cooling_until,
                    nfpi_score=nfpi
                )
                self.db.add(new_cluster)

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to save cluster to database: {e}")
            self.db.rollback()
            # Non-critical error, continue processing

    def get_ticker_credibility_summary(self, ticker: str) -> Dict:
        """
        Get credibility summary for a ticker based on recent clusters.

        Args:
            ticker: Stock ticker

        Returns:
            Dict with credibility metrics
        """
        clusters = self.clustering_engine.get_ticker_clusters(ticker)

        if not clusters:
            return {
                "ticker": ticker,
                "cluster_count": 0,
                "avg_nfpi": None,
                "manipulation_risk": "UNKNOWN",
                "recommended_action": "NEUTRAL"
            }

        # Calculate metrics
        nfpi_scores = [
            self.clustering_engine.nfpi_calculator.calculate_nfpi(c)
            for c in clusters
        ]
        avg_nfpi = sum(nfpi_scores) / len(nfpi_scores)

        manipulation_count = sum(
            1 for c in clusters
            if c.verdict == Verdict.MANIPULATION_ATTACK
        )
        embargo_count = sum(
            1 for c in clusters
            if c.verdict == Verdict.EMBARGO_EVENT
        )

        # Determine risk level
        if manipulation_count > 0:
            risk = "HIGH"
        elif avg_nfpi > 60:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        # Recommended action
        if manipulation_count > 0:
            action = "AVOID"
        elif embargo_count > 0:
            action = "BUY"
        else:
            action = "NEUTRAL"

        return {
            "ticker": ticker,
            "cluster_count": len(clusters),
            "avg_nfpi": round(avg_nfpi, 2),
            "manipulation_risk": risk,
            "manipulation_clusters": manipulation_count,
            "legitimate_events": embargo_count,
            "recommended_action": action,
            "recent_verdicts": [c.verdict.value for c in clusters]
        }

    def get_suspicious_activity_report(self) -> List[Dict]:
        """
        Get report of all suspicious news activity.

        Returns:
            List of suspicious clusters with details
        """
        all_clusters = self.clustering_engine.get_active_clusters(max_age_hours=24)

        suspicious = [
            c for c in all_clusters
            if c.verdict in [Verdict.MANIPULATION_ATTACK, Verdict.SUSPICIOUS_BURST]
        ]

        report = []
        for cluster in suspicious:
            nfpi = self.clustering_engine.nfpi_calculator.calculate_nfpi(cluster)

            report.append({
                "ticker": cluster.ticker,
                "theme": cluster.theme,
                "verdict": cluster.verdict.value,
                "nfpi": round(nfpi, 2),
                "article_count": len(cluster.articles),
                "first_seen": cluster.first_seen.isoformat(),
                "sources": [a.source for a in cluster.articles],
                "reason": cluster.verdict_reason,
                "cooling_until": cluster.cooling_until.isoformat() if cluster.cooling_until else None
            })

        return report


# Global adapter instance (singleton)
_adapter_instance: Optional[NewsPipelineAdapter] = None


def get_adapter(db: Session) -> NewsPipelineAdapter:
    """Get or create the global adapter instance."""
    global _adapter_instance
    if _adapter_instance is None or _adapter_instance.db != db:
        _adapter_instance = NewsPipelineAdapter(db)
    return _adapter_instance


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("News Pipeline Adapter Test")
    print("=" * 80)
    print()

    # Mock database session (for testing)
    class MockDB:
        def query(self, *args, **kwargs):
            return self
        def filter_by(self, *args, **kwargs):
            return self
        def first(self):
            return None
        def add(self, obj):
            pass
        def commit(self):
            pass
        def rollback(self):
            pass

    db = MockDB()

    # Initialize adapter
    adapter = NewsPipelineAdapter(db)

    print("Testing manipulation detection...")
    print("-" * 80)

    # Test 1: Manipulation attack
    for i in range(3):
        result = adapter.process_news_article(
            article_id=1000 + i,
            ticker="TSLA",
            title="TSLA to $5000! Buy now!",
            content="TSLA to $5000! Buy now! Don't miss out!",
            source=f"sketchy-site-{i}.com",
            published_at=datetime.now(),
            url=f"http://sketchy-site-{i}.com/article"
        )

        if result['cluster_id']:
            print(f"Article {i+1} result:")
            print(f"  Verdict: {result['verdict']}")
            print(f"  NFPI: {result['nfpi']:.1f}%")
            print(f"  Should trade: {'✅ YES' if result['should_trade'] else '❌ NO'}")
            print(f"  Confidence: ×{result['confidence_multiplier']:.2f}")
            print()

    print("-" * 80)
    print("Testing legitimate earnings...")
    print("-" * 80)

    # Test 2: Legitimate earnings
    sources = ["Bloomberg", "Reuters", "WSJ"]
    for i, source in enumerate(sources):
        result = adapter.process_news_article(
            article_id=2000 + i,
            ticker="AAPL",
            title=f"Apple beats Q4 earnings - {source}",
            content=f"Apple reported strong results. {source} analysis shows...",
            source=source,
            published_at=datetime.now().replace(hour=16, minute=0, second=0),
            url=f"http://{source.lower()}.com/article"
        )

        if result['cluster_id']:
            print(f"Article {i+1} result:")
            print(f"  Verdict: {result['verdict']}")
            print(f"  NFPI: {result['nfpi']:.1f}%")
            print(f"  Should trade: {'✅ YES' if result['should_trade'] else '❌ NO'}")
            print(f"  Confidence: ×{result['confidence_multiplier']:.2f}")
            print()

    # Get credibility summary
    print("-" * 80)
    print("Credibility Summaries:")
    print("-" * 80)

    for ticker in ["TSLA", "AAPL"]:
        summary = adapter.get_ticker_credibility_summary(ticker)
        print(f"\n{ticker}:")
        print(f"  Clusters: {summary['cluster_count']}")
        if summary['avg_nfpi'] is not None:
            print(f"  Avg NFPI: {summary['avg_nfpi']:.1f}%")
            print(f"  Risk: {summary['manipulation_risk']}")
            print(f"  Recommendation: {summary['recommended_action']}")

    # Suspicious activity report
    print("\n" + "-" * 80)
    print("Suspicious Activity Report:")
    print("-" * 80)

    report = adapter.get_suspicious_activity_report()
    if report:
        for item in report:
            print(f"\n⚠️  {item['ticker']} - {item['verdict']}")
            print(f"   NFPI: {item['nfpi']:.1f}%")
            print(f"   Articles: {item['article_count']}")
            print(f"   Sources: {', '.join(item['sources'][:3])}")
    else:
        print("No suspicious activity detected")

    print("\n" + "=" * 80)
    print("News Pipeline Adapter test completed!")
    print("=" * 80)
