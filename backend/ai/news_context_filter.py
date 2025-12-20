"""
News Context Filtering Engine - Phase 14.5

Advanced news filtering using 4-way ensemble approach.
Eliminates noise and identifies true risk signals.

Based on ChatGPT/Gemini recommendations:
1. Risk Cluster Learning - Pattern from crash days
2. Sector Risk Vectors - Sector-specific profiles
3. Crash Pattern Matching - Company-specific risk patterns
4. Sentiment Trend Analysis - 30-day moving average

Usage:
    filter = NewsContextFilter(db_session)

    # Analyze single news
    risk_score = await filter.analyze_news(
        ticker="AAPL",
        news_content="Apple supplier faces production delays...",
        publish_date=datetime.now()
    )

    # Filter news batch
    filtered = await filter.filter_news_batch(news_list)
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class NewsRiskScore:
    """News risk assessment result."""

    news_id: Optional[int]
    ticker: str
    title: str
    publish_date: datetime

    # Individual scores (0-1)
    cluster_risk: float
    sector_risk: float
    crash_pattern_risk: float
    sentiment_trend_risk: float

    # Ensemble score
    final_risk_score: float
    risk_level: str  # "CRITICAL", "HIGH", "NORMAL", "LOW"

    # Metadata
    cluster_id: Optional[int] = None
    sector: Optional[str] = None
    similar_crashes: Optional[List[str]] = None
    sentiment_change: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["publish_date"] = self.publish_date.isoformat()
        return data


@dataclass
class RiskCluster:
    """Risk cluster from historical crashes."""

    cluster_id: int
    cluster_name: str
    centroid_embedding: np.ndarray
    crash_count: int
    avg_price_drop: float
    keywords: List[str]
    example_news: List[str]


# ============================================================================
# News Context Filter
# ============================================================================


class NewsContextFilter:
    """
    Advanced news filtering with 4-way ensemble.

    Filters out noise and identifies true risk signals
    using multiple validation methods.

    Ensemble weights (tunable):
    - cluster_risk: 30%
    - sector_risk: 20%
    - crash_pattern_risk: 30%
    - sentiment_trend_risk: 20%
    """

    # Ensemble weights (sum to 1.0)
    WEIGHTS = {
        "cluster_risk": 0.30,
        "sector_risk": 0.20,
        "crash_pattern_risk": 0.30,
        "sentiment_trend_risk": 0.20,
    }

    # Risk level thresholds
    RISK_THRESHOLDS = {
        "CRITICAL": 0.70,
        "HIGH": 0.50,
        "NORMAL": 0.30,
        "LOW": 0.0,
    }

    # Sector ETF mapping
    SECTOR_ETFS = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLV": "Healthcare",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLI": "Industrials",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLC": "Communications",
    }

    def __init__(self, db_session: AsyncSession):
        """
        Initialize news context filter.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.risk_clusters: Optional[List[RiskCluster]] = None
        self.sector_vectors: Dict[str, np.ndarray] = {}
        self.crash_patterns: Dict[str, List[Dict]] = defaultdict(list)

        logger.info("NewsContextFilter initialized")

    # ========================================================================
    # Method 1: Risk Cluster Learning
    # ========================================================================

    async def learn_risk_clusters(
        self,
        min_price_drop: float = -0.05,
        lookback_days: int = 365,
        n_clusters: int = 5
    ) -> List[RiskCluster]:
        """
        Learn risk clusters from historical crash days.

        Process:
        1. Find days with >5% price drops
        2. Collect news from those days
        3. K-means clustering on embeddings
        4. Create risk clusters

        Args:
            min_price_drop: Minimum price drop (e.g., -0.05 = -5%)
            lookback_days: Days to look back
            n_clusters: Number of clusters

        Returns:
            List of risk clusters
        """
        logger.info(
            f"Learning risk clusters: drop<{min_price_drop}, "
            f"lookback={lookback_days}d, clusters={n_clusters}"
        )

        from backend.core.models.embedding_models import DocumentEmbedding

        # Find crash days
        # TODO: Query actual price data when available
        # For now, use a heuristic based on news sentiment

        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Get all news embeddings from crash period
        result = await self.db.execute(
            select(
                DocumentEmbedding.id,
                DocumentEmbedding.ticker,
                DocumentEmbedding.title,
                DocumentEmbedding.embedding,
                DocumentEmbedding.source_date,
            ).where(
                and_(
                    DocumentEmbedding.document_type == "news_article",
                    DocumentEmbedding.source_date >= cutoff_date,
                )
            ).limit(1000)  # Limit for performance
        )

        embeddings_data = result.fetchall()

        if len(embeddings_data) < n_clusters:
            logger.warning(
                f"Not enough data for clustering: {len(embeddings_data)} < {n_clusters}"
            )
            return []

        # Extract embeddings
        embeddings = np.array([row.embedding for row in embeddings_data])

        # K-means clustering
        from sklearn.cluster import KMeans

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Build clusters
        clusters = []
        for cluster_id in range(n_clusters):
            mask = cluster_labels == cluster_id
            cluster_embeddings = embeddings[mask]
            cluster_data = [embeddings_data[i] for i, m in enumerate(mask) if m]

            if len(cluster_data) == 0:
                continue

            # Calculate centroid
            centroid = kmeans.cluster_centers_[cluster_id]

            # Extract keywords (simple heuristic from titles)
            titles = [row.title for row in cluster_data]
            keywords = self._extract_common_keywords(titles)

            cluster = RiskCluster(
                cluster_id=cluster_id,
                cluster_name=f"Risk_Cluster_{cluster_id}",
                centroid_embedding=centroid,
                crash_count=len(cluster_data),
                avg_price_drop=-0.05,  # Placeholder
                keywords=keywords,
                example_news=titles[:3],
            )

            clusters.append(cluster)

        self.risk_clusters = clusters

        logger.info(f"Learned {len(clusters)} risk clusters")

        return clusters

    def _extract_common_keywords(self, titles: List[str], top_k: int = 5) -> List[str]:
        """Extract common keywords from titles."""
        from collections import Counter
        import re

        # Simple keyword extraction
        all_words = []
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}

        for title in titles:
            words = re.findall(r'\b[a-z]{4,}\b', title.lower())
            all_words.extend([w for w in words if w not in stopwords])

        counter = Counter(all_words)
        return [word for word, count in counter.most_common(top_k)]

    async def calculate_cluster_risk(
        self,
        news_embedding: np.ndarray
    ) -> Tuple[float, Optional[int]]:
        """
        Calculate risk based on cluster proximity.

        Args:
            news_embedding: News embedding vector

        Returns:
            (risk_score, cluster_id)
        """
        if not self.risk_clusters:
            await self.learn_risk_clusters()

        if not self.risk_clusters:
            return 0.0, None

        # Find nearest cluster
        min_distance = float('inf')
        nearest_cluster_id = None

        for cluster in self.risk_clusters:
            # Cosine similarity (convert to distance)
            similarity = np.dot(news_embedding, cluster.centroid_embedding) / (
                np.linalg.norm(news_embedding) * np.linalg.norm(cluster.centroid_embedding)
            )
            distance = 1 - similarity

            if distance < min_distance:
                min_distance = distance
                nearest_cluster_id = cluster.cluster_id

        # Convert distance to risk score (closer = higher risk)
        risk_score = max(0, 1 - min_distance)

        return risk_score, nearest_cluster_id

    # ========================================================================
    # Method 2: Sector Risk Vectors
    # ========================================================================

    async def build_sector_vectors(self) -> Dict[str, np.ndarray]:
        """
        Build sector-specific risk vectors.

        Process:
        1. Get news for each sector ETF
        2. Average embeddings to create sector profile
        3. Use for sector-specific risk assessment

        Returns:
            Dictionary of sector vectors
        """
        logger.info("Building sector risk vectors...")

        from backend.core.models.embedding_models import DocumentEmbedding

        sector_vectors = {}

        for etf, sector_name in self.SECTOR_ETFS.items():
            # Get news for this ETF/sector
            result = await self.db.execute(
                select(
                    DocumentEmbedding.embedding
                ).where(
                    and_(
                        DocumentEmbedding.ticker == etf,
                        DocumentEmbedding.document_type == "news_article",
                    )
                ).limit(100)
            )

            embeddings = [row.embedding for row in result.fetchall()]

            if embeddings:
                # Average to create sector vector
                sector_vector = np.mean(embeddings, axis=0)
                sector_vectors[sector_name] = sector_vector
                logger.info(f"Built vector for {sector_name} ({len(embeddings)} news)")

        self.sector_vectors = sector_vectors

        return sector_vectors

    async def calculate_sector_risk(
        self,
        ticker: str,
        news_embedding: np.ndarray
    ) -> float:
        """
        Calculate sector-specific risk.

        Args:
            ticker: Stock ticker
            news_embedding: News embedding

        Returns:
            Sector risk score
        """
        if not self.sector_vectors:
            await self.build_sector_vectors()

        if not self.sector_vectors:
            return 0.0

        # TODO: Map ticker to sector (hardcoded for now)
        sector_map = {
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology",
            "NVDA": "Technology",
            "JPM": "Financials",
            "BAC": "Financials",
            "XOM": "Energy",
        }

        sector = sector_map.get(ticker, "Technology")  # Default to tech

        if sector not in self.sector_vectors:
            return 0.0

        sector_vector = self.sector_vectors[sector]

        # Calculate similarity
        similarity = np.dot(news_embedding, sector_vector) / (
            np.linalg.norm(news_embedding) * np.linalg.norm(sector_vector)
        )

        # Higher similarity = higher sector-specific risk
        risk_score = max(0, similarity)

        return risk_score

    # ========================================================================
    # Method 3: Crash Pattern Matching
    # ========================================================================

    async def learn_crash_patterns(
        self,
        ticker: str,
        min_price_drop: float = -0.05,
        lookback_days: int = 730  # 2 years
    ) -> List[Dict]:
        """
        Learn company-specific crash patterns.

        Args:
            ticker: Stock ticker
            min_price_drop: Minimum price drop
            lookback_days: Days to look back

        Returns:
            List of crash patterns
        """
        logger.info(f"Learning crash patterns for {ticker}")

        # TODO: Query actual price data + news
        # For now, return empty (will be populated with real data)

        patterns = []

        # Placeholder: In production, this would:
        # 1. Find days when ticker dropped >5%
        # 2. Get news from those days
        # 3. Create pattern signatures

        self.crash_patterns[ticker] = patterns

        return patterns

    async def calculate_crash_pattern_risk(
        self,
        ticker: str,
        news_embedding: np.ndarray
    ) -> float:
        """
        Calculate risk based on historical crash patterns.

        Args:
            ticker: Stock ticker
            news_embedding: News embedding

        Returns:
            Crash pattern risk score
        """
        if ticker not in self.crash_patterns:
            await self.learn_crash_patterns(ticker)

        patterns = self.crash_patterns.get(ticker, [])

        if not patterns:
            return 0.0

        # Find most similar crash pattern
        max_similarity = 0.0

        for pattern in patterns:
            pattern_embedding = pattern["embedding"]

            similarity = np.dot(news_embedding, pattern_embedding) / (
                np.linalg.norm(news_embedding) * np.linalg.norm(pattern_embedding)
            )

            max_similarity = max(max_similarity, similarity)

        return max(0, max_similarity)

    # ========================================================================
    # Method 4: Sentiment Trend Analysis
    # ========================================================================

    async def calculate_sentiment_trend_risk(
        self,
        ticker: str,
        news_embedding: np.ndarray,
        publish_date: datetime,
        window_days: int = 30
    ) -> Tuple[float, float]:
        """
        Calculate risk based on sentiment trend changes.

        Process:
        1. Get recent news embeddings (30 days)
        2. Calculate moving average sentiment
        3. Detect structural breaks (golden cross, etc.)

        Args:
            ticker: Stock ticker
            news_embedding: Current news embedding
            publish_date: Publish date
            window_days: MA window

        Returns:
            (risk_score, sentiment_change)
        """
        from backend.core.models.embedding_models import DocumentEmbedding

        # Get recent news
        cutoff_date = publish_date - timedelta(days=window_days)

        result = await self.db.execute(
            select(
                DocumentEmbedding.embedding,
                DocumentEmbedding.source_date,
            ).where(
                and_(
                    DocumentEmbedding.ticker == ticker,
                    DocumentEmbedding.document_type == "news_article",
                    DocumentEmbedding.source_date >= cutoff_date,
                    DocumentEmbedding.source_date < publish_date,
                )
            ).order_by(DocumentEmbedding.source_date)
        )

        historical_embeddings = result.fetchall()

        if len(historical_embeddings) < 3:
            return 0.0, 0.0

        # Calculate average historical sentiment
        avg_embedding = np.mean(
            [row.embedding for row in historical_embeddings],
            axis=0
        )

        # Calculate similarity with current news
        similarity = np.dot(news_embedding, avg_embedding) / (
            np.linalg.norm(news_embedding) * np.linalg.norm(avg_embedding)
        )

        # Large deviation = risk
        sentiment_change = 1 - similarity
        risk_score = max(0, sentiment_change)

        return risk_score, sentiment_change

    # ========================================================================
    # Ensemble Analysis
    # ========================================================================

    async def analyze_news(
        self,
        ticker: str,
        news_content: str,
        title: str,
        publish_date: datetime,
        news_id: Optional[int] = None,
        embedding: Optional[np.ndarray] = None
    ) -> NewsRiskScore:
        """
        Comprehensive news risk analysis using 4-way ensemble.

        Args:
            ticker: Stock ticker
            news_content: News content
            title: News title
            publish_date: Publish date
            news_id: News ID (optional)
            embedding: Pre-computed embedding (optional)

        Returns:
            NewsRiskScore with ensemble analysis
        """
        # Get/create embedding
        if embedding is None:
            from backend.ai.embedding_engine import EmbeddingEngine

            engine = EmbeddingEngine(self.db)

            # Generate embedding for news
            embeddings = await engine.generate_embedding(news_content)
            embedding = np.array(embeddings[0])

        # Calculate 4 risk scores
        cluster_risk, cluster_id = await self.calculate_cluster_risk(embedding)
        sector_risk = await self.calculate_sector_risk(ticker, embedding)
        crash_pattern_risk = await self.calculate_crash_pattern_risk(ticker, embedding)
        sentiment_trend_risk, sentiment_change = await self.calculate_sentiment_trend_risk(
            ticker, embedding, publish_date
        )

        # Ensemble
        final_risk_score = (
            self.WEIGHTS["cluster_risk"] * cluster_risk +
            self.WEIGHTS["sector_risk"] * sector_risk +
            self.WEIGHTS["crash_pattern_risk"] * crash_pattern_risk +
            self.WEIGHTS["sentiment_trend_risk"] * sentiment_trend_risk
        )

        # Determine risk level
        if final_risk_score >= self.RISK_THRESHOLDS["CRITICAL"]:
            risk_level = "CRITICAL"
        elif final_risk_score >= self.RISK_THRESHOLDS["HIGH"]:
            risk_level = "HIGH"
        elif final_risk_score >= self.RISK_THRESHOLDS["NORMAL"]:
            risk_level = "NORMAL"
        else:
            risk_level = "LOW"

        result = NewsRiskScore(
            news_id=news_id,
            ticker=ticker,
            title=title,
            publish_date=publish_date,
            cluster_risk=cluster_risk,
            sector_risk=sector_risk,
            crash_pattern_risk=crash_pattern_risk,
            sentiment_trend_risk=sentiment_trend_risk,
            final_risk_score=final_risk_score,
            risk_level=risk_level,
            cluster_id=cluster_id,
            sentiment_change=sentiment_change,
        )

        logger.info(
            f"News risk: {ticker} | {risk_level} ({final_risk_score:.2f}) | "
            f"Cluster={cluster_risk:.2f}, Sector={sector_risk:.2f}, "
            f"Crash={crash_pattern_risk:.2f}, Sentiment={sentiment_trend_risk:.2f}"
        )

        return result

    async def filter_news_batch(
        self,
        news_list: List[Dict[str, Any]],
        min_risk_score: float = 0.5
    ) -> List[NewsRiskScore]:
        """
        Filter batch of news, keeping only high-risk items.

        Args:
            news_list: List of news dicts with ticker, title, content, publish_date
            min_risk_score: Minimum risk score to keep

        Returns:
            Filtered list of high-risk news
        """
        logger.info(f"Filtering {len(news_list)} news items (threshold={min_risk_score})")

        results = []

        for news in news_list:
            result = await self.analyze_news(
                ticker=news["ticker"],
                news_content=news.get("content", ""),
                title=news["title"],
                publish_date=news["publish_date"],
                news_id=news.get("id"),
            )

            if result.final_risk_score >= min_risk_score:
                results.append(result)

        logger.info(
            f"Filtered to {len(results)} high-risk news "
            f"({len(results)/len(news_list)*100:.1f}% pass rate)"
        )

        return results


# Example usage
if __name__ == "__main__":
    import asyncio
    from backend.core.database import get_db

    async def demo():
        async with get_db() as db:
            filter_engine = NewsContextFilter(db)

            # Learn clusters
            clusters = await filter_engine.learn_risk_clusters()
            print(f"\nLearned {len(clusters)} risk clusters")

            # Build sector vectors
            sectors = await filter_engine.build_sector_vectors()
            print(f"\nBuilt {len(sectors)} sector vectors")

            # Analyze sample news
            result = await filter_engine.analyze_news(
                ticker="AAPL",
                news_content="Apple supplier faces production delays due to supply chain issues",
                title="Apple Supplier Production Delays",
                publish_date=datetime.now()
            )

            print(f"\nNews Risk Analysis:")
            print(f"  Ticker: {result.ticker}")
            print(f"  Risk Level: {result.risk_level}")
            print(f"  Final Score: {result.final_risk_score:.2f}")
            print(f"  Cluster Risk: {result.cluster_risk:.2f}")
            print(f"  Sector Risk: {result.sector_risk:.2f}")
            print(f"  Crash Pattern: {result.crash_pattern_risk:.2f}")
            print(f"  Sentiment Trend: {result.sentiment_trend_risk:.2f}")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
