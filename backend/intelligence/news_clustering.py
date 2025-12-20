"""
News Clustering System for 4-Signal Framework.

This module groups similar news articles into clusters and assigns fingerprints
for deduplication and manipulation detection.

Features:
- Content-based fingerprinting (title + keywords)
- Time-window clustering (group articles within N minutes)
- Automatic cluster updates as new articles arrive
- Integration with 4-Signal Calculator

Author: AI Trading System Team
Date: 2025-12-19
Phase: 18
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict

try:
    from backend.intelligence.four_signal_framework import (
        NewsArticle,
        NewsCluster,
        FourSignalCalculator,
        VerdictClassifier,
        NFPICalculator,
        Verdict
    )
except ImportError:
    # Standalone execution
    from four_signal_framework import (
        NewsArticle,
        NewsCluster,
        FourSignalCalculator,
        VerdictClassifier,
        NFPICalculator,
        Verdict
    )

logger = logging.getLogger(__name__)


class NewsClusteringEngine:
    """
    Groups similar news articles into clusters for manipulation detection.

    Clustering Strategy:
    1. Extract content fingerprint (normalized keywords)
    2. Group articles with same fingerprint within time window
    3. Calculate 4-Signal scores for each cluster
    4. Classify verdict and apply confidence adjustments
    """

    def __init__(
        self,
        time_window_minutes: int = 60,
        min_cluster_size: int = 2
    ):
        """
        Initialize clustering engine.

        Args:
            time_window_minutes: Max time gap for grouping (default: 60 min)
            min_cluster_size: Min articles to form cluster (default: 2)
        """
        self.time_window = timedelta(minutes=time_window_minutes)
        self.min_cluster_size = min_cluster_size

        # Active clusters (fingerprint -> NewsCluster)
        self.clusters: Dict[str, NewsCluster] = {}

        # 4-Signal components
        self.signal_calculator = FourSignalCalculator()
        self.verdict_classifier = VerdictClassifier()
        self.nfpi_calculator = NFPICalculator()

        logger.info(
            f"NewsClusteringEngine initialized: "
            f"time_window={time_window_minutes}min, "
            f"min_size={min_cluster_size}"
        )

    def add_article(self, article: NewsArticle) -> Optional[NewsCluster]:
        """
        Add a new article and update/create clusters.

        Args:
            article: NewsArticle to process

        Returns:
            Updated or newly created NewsCluster (if cluster size >= min)
        """
        # Generate fingerprint
        fingerprint = self._generate_fingerprint(article)

        # Check if cluster exists
        if fingerprint in self.clusters:
            cluster = self.clusters[fingerprint]

            # Check if article is within time window
            time_diff = abs((article.published_at - cluster.last_seen).total_seconds())

            if time_diff <= self.time_window.total_seconds():
                # Add to existing cluster
                cluster.articles.append(article)
                cluster.last_seen = max(cluster.last_seen, article.published_at)

                logger.debug(
                    f"Article added to existing cluster: {fingerprint} "
                    f"(now {len(cluster.articles)} articles)"
                )

                # Recalculate signals
                self._update_cluster_signals(cluster)

                return cluster if len(cluster.articles) >= self.min_cluster_size else None
            else:
                # Time window expired, create new cluster
                logger.debug(
                    f"Time window expired for {fingerprint}, creating new cluster"
                )
                return self._create_new_cluster(article, fingerprint)
        else:
            # Create new cluster
            return self._create_new_cluster(article, fingerprint)

    def _create_new_cluster(self, article: NewsArticle, fingerprint: str) -> Optional[NewsCluster]:
        """Create a new news cluster."""
        theme = self._extract_theme(article)

        cluster = NewsCluster(
            fingerprint=fingerprint,
            ticker=article.ticker,
            theme=theme,
            articles=[article],
            first_seen=article.published_at,
            last_seen=article.published_at
        )

        self.clusters[fingerprint] = cluster

        logger.debug(
            f"New cluster created: {fingerprint} "
            f"(ticker={article.ticker}, theme={theme})"
        )

        # Don't calculate signals yet (need min_cluster_size articles)
        return None

    def _update_cluster_signals(self, cluster: NewsCluster):
        """Recalculate 4-Signal scores and verdict for a cluster."""
        if len(cluster.articles) < self.min_cluster_size:
            return

        # Calculate 4 signals
        cluster = self.signal_calculator.calculate_all_signals(cluster)

        # Classify verdict
        cluster = self.verdict_classifier.classify(cluster)

        # Calculate NFPI
        nfpi = self.nfpi_calculator.calculate_nfpi(cluster)

        logger.info(
            f"Cluster updated: {cluster.fingerprint[:8]}... | "
            f"{cluster.ticker} | Articles: {len(cluster.articles)} | "
            f"Verdict: {cluster.verdict.value} | NFPI: {nfpi:.1f}% | "
            f"Confidence: {cluster.confidence_multiplier:.2f}x"
        )

    def _generate_fingerprint(self, article: NewsArticle) -> str:
        """
        Generate content-based fingerprint for article.

        Uses normalized keywords from title and content to group similar articles.

        Args:
            article: NewsArticle

        Returns:
            32-character hex fingerprint
        """
        # Extract keywords (normalize)
        text = f"{article.title} {article.content}".lower()

        # Remove common words (stopwords)
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "be", "been", "have", "has",
            "said", "says", "will", "can", "could", "would", "should"
        }

        words = [w for w in text.split() if w not in stopwords and len(w) > 2]

        # Extract key terms (nouns, entities)
        # For simplicity, use top frequent words
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1

        # Top 10 keywords
        top_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [kw for kw, _ in top_keywords]

        # Add ticker for grouping
        keywords.insert(0, article.ticker.lower())

        # Generate hash
        fingerprint_text = "_".join(sorted(keywords))
        fingerprint = hashlib.md5(fingerprint_text.encode()).hexdigest()

        return fingerprint

    def _extract_theme(self, article: NewsArticle) -> str:
        """
        Extract theme/topic from article.

        Uses keyword matching to identify common themes:
        - earnings, revenue, profit → "earnings_report"
        - FDA, approval, drug → "fda_approval"
        - CEO, resign, fired → "executive_change"
        - etc.

        Args:
            article: NewsArticle

        Returns:
            Theme string
        """
        text = f"{article.title} {article.content}".lower()

        # Theme patterns
        themes = {
            "earnings_report": ["earnings", "revenue", "profit", "eps", "quarterly", "q1", "q2", "q3", "q4"],
            "fda_approval": ["fda", "approval", "drug", "clinical", "trial"],
            "executive_change": ["ceo", "cfo", "executive", "resign", "fired", "appointed"],
            "merger_acquisition": ["merger", "acquisition", "buyout", "takeover", "deal"],
            "product_launch": ["launch", "release", "unveil", "announce", "new product"],
            "legal_issue": ["lawsuit", "sue", "court", "settlement", "fine", "penalty"],
            "partnership": ["partnership", "collaboration", "agreement", "deal", "contract"],
            "guidance": ["guidance", "forecast", "outlook", "expect", "project"],
            "analyst_rating": ["upgrade", "downgrade", "rating", "target price", "analyst"],
            "insider_trading": ["insider", "buy", "sell", "stock purchase", "filing"],
        }

        for theme, keywords in themes.items():
            if any(kw in text for kw in keywords):
                return theme

        return "general_news"

    def get_cluster(self, fingerprint: str) -> Optional[NewsCluster]:
        """Get cluster by fingerprint."""
        return self.clusters.get(fingerprint)

    def get_ticker_clusters(self, ticker: str) -> List[NewsCluster]:
        """Get all active clusters for a ticker."""
        return [
            cluster for cluster in self.clusters.values()
            if cluster.ticker == ticker and len(cluster.articles) >= self.min_cluster_size
        ]

    def get_active_clusters(self, max_age_hours: int = 24) -> List[NewsCluster]:
        """
        Get all active clusters (recent and significant).

        Args:
            max_age_hours: Maximum age in hours (default: 24)

        Returns:
            List of NewsCluster
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        active_clusters = [
            cluster for cluster in self.clusters.values()
            if cluster.last_seen >= cutoff_time and
            len(cluster.articles) >= self.min_cluster_size
        ]

        # Sort by last_seen (most recent first)
        active_clusters.sort(key=lambda c: c.last_seen, reverse=True)

        return active_clusters

    def cleanup_old_clusters(self, max_age_hours: int = 48):
        """
        Remove old clusters to free memory.

        Args:
            max_age_hours: Maximum age before cleanup (default: 48)
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        old_fingerprints = [
            fp for fp, cluster in self.clusters.items()
            if cluster.last_seen < cutoff_time
        ]

        for fp in old_fingerprints:
            del self.clusters[fp]

        if old_fingerprints:
            logger.info(f"Cleaned up {len(old_fingerprints)} old clusters")

    def get_cluster_stats(self) -> Dict:
        """Get statistics about current clusters."""
        total_clusters = len(self.clusters)
        active_clusters = len(self.get_active_clusters())

        verdict_counts = defaultdict(int)
        for cluster in self.clusters.values():
            verdict_counts[cluster.verdict.value] += 1

        return {
            "total_clusters": total_clusters,
            "active_clusters_24h": active_clusters,
            "verdict_distribution": dict(verdict_counts),
            "avg_articles_per_cluster": (
                sum(len(c.articles) for c in self.clusters.values()) / total_clusters
                if total_clusters > 0 else 0
            )
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("News Clustering Engine Test")
    print("=" * 80)
    print()

    # Initialize engine
    engine = NewsClusteringEngine(time_window_minutes=60, min_cluster_size=2)

    # Simulate manipulation attack (3 copy-paste articles)
    print("Simulating manipulation attack (3 copy-paste articles)...")
    print()

    base_time = datetime.now()

    for i in range(3):
        article = NewsArticle(
            id=f"attack_{i}",
            ticker="TSLA",
            title="TSLA to $5000! Buy now!",
            content="TSLA to $5000! Buy now! Don't miss this opportunity!",
            source=f"sketchy-site-{i}.com",
            source_tier="MINOR",
            published_at=base_time + timedelta(seconds=i)
        )

        cluster = engine.add_article(article)

        if cluster:
            print(f"✅ Cluster formed after article {i+1}")
            print(f"   Verdict: {cluster.verdict.value}")
            print(f"   NFPI: {engine.nfpi_calculator.calculate_nfpi(cluster):.1f}%")
            print(f"   Confidence Multiplier: {cluster.confidence_multiplier:.2f}x")
            print(f"   Reason: {cluster.verdict_reason}")
            print()

    # Simulate legitimate earnings (3 diverse sources)
    print("-" * 80)
    print("Simulating legitimate earnings event (3 major sources)...")
    print()

    earnings_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)

    sources = [
        ("Bloomberg", "MAJOR", 0),
        ("Reuters", "MAJOR", 120),
        ("WSJ", "MAJOR", 300),
    ]

    for i, (source, tier, delay) in enumerate(sources):
        article = NewsArticle(
            id=f"earnings_{i}",
            ticker="AAPL",
            title=f"Apple beats Q4 earnings expectations - {source}",
            content=f"Apple reported strong Q4 results. {source} analysis shows EPS of $1.50 beat estimates.",
            source=source,
            source_tier=tier,
            published_at=earnings_time + timedelta(seconds=delay)
        )

        cluster = engine.add_article(article)

        if cluster:
            print(f"✅ Cluster formed after article {i+1}")
            print(f"   Verdict: {cluster.verdict.value}")
            print(f"   NFPI: {engine.nfpi_calculator.calculate_nfpi(cluster):.1f}%")
            print(f"   Confidence Multiplier: {cluster.confidence_multiplier:.2f}x")
            print(f"   Event: {cluster.el_event_name}")
            print(f"   Reason: {cluster.verdict_reason}")
            print()

    # Show statistics
    print("-" * 80)
    print("Engine Statistics:")
    print("-" * 80)

    stats = engine.get_cluster_stats()
    print(f"Total clusters: {stats['total_clusters']}")
    print(f"Active clusters (24h): {stats['active_clusters_24h']}")
    print(f"Avg articles per cluster: {stats['avg_articles_per_cluster']:.1f}")
    print()
    print("Verdict distribution:")
    for verdict, count in stats['verdict_distribution'].items():
        print(f"  {verdict}: {count}")

    print()
    print("=" * 80)
    print("News Clustering Engine test completed!")
    print("=" * 80)
