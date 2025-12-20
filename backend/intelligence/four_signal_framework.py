"""
4-Signal Consensus Framework for News Manipulation Detection.

This module implements the 4-Signal system to distinguish between:
- MANIPULATION_ATTACK: Coordinated fake news campaigns
- EMBARGO_EVENT: Legitimate news releases (earnings, FOMC, etc.)
- ORGANIC_CONSENSUS: Real market consensus from diverse sources
- VIRAL_TREND: Natural information spread

The Four Signals:
1. DI (Diversity Integrity): Source diversity score (0-1)
2. TN (Temporal Naturalness): Time pattern naturalness (-1 to +1)
3. NI (Narrative Independence): Content uniqueness (0-1)
4. EL (Event Legitimacy): Scheduled event detection (boolean + confidence)

Author: AI Trading System Team
Date: 2025-12-19
Phase: 18
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

try:
    from backend.intelligence.source_classifier import (
        SourceTierClassifier,
        SourceTier,
        get_classifier
    )
except ImportError:
    # Standalone execution
    from source_classifier import (
        SourceTierClassifier,
        SourceTier,
        get_classifier
    )

logger = logging.getLogger(__name__)


class Verdict(str, Enum):
    """News cluster verdict classifications."""
    EMBARGO_EVENT = "EMBARGO_EVENT"           # Scheduled event (high legitimacy)
    ORGANIC_CONSENSUS = "ORGANIC_CONSENSUS"   # Real market consensus
    MANIPULATION_ATTACK = "MANIPULATION_ATTACK"  # Coordinated fake news
    VIRAL_TREND = "VIRAL_TREND"               # Natural viral spread
    SUSPICIOUS_BURST = "SUSPICIOUS_BURST"     # Needs further investigation
    PENDING = "PENDING"                       # Not yet analyzed


@dataclass
class NewsArticle:
    """Individual news article data."""
    id: str
    ticker: str
    title: str
    content: str
    source: str
    source_tier: str  # "MAJOR", "MINOR", "SOCIAL", "UNKNOWN"
    published_at: datetime
    url: Optional[str] = None
    sentiment: Optional[float] = None  # -1 to +1


@dataclass
class NewsCluster:
    """Cluster of similar news articles."""
    fingerprint: str  # Unique identifier (content hash)
    ticker: str
    theme: str  # e.g., "earnings_beat", "FDA_approval", "CEO_scandal"
    articles: List[NewsArticle]
    first_seen: datetime
    last_seen: datetime

    # 4-Signal scores
    di_score: float = 0.5  # Diversity Integrity (0-1)
    tn_score: float = 0.0  # Temporal Naturalness (-1 to +1)
    ni_score: float = 0.5  # Narrative Independence (0-1)
    el_matched: bool = False  # Event Legitimacy
    el_confidence: float = 0.0
    el_event_name: Optional[str] = None

    # Verdict
    verdict: Verdict = Verdict.PENDING
    verdict_reason: str = ""
    confidence_multiplier: float = 1.0  # Applied to trading signals

    # Cooling period (quarantine for suspicious news)
    cooling_intensity: float = 0.0  # 0 = no cooling, 1 = full block
    cooling_until: Optional[datetime] = None


class FourSignalCalculator:
    """
    Calculates the 4 signals for news cluster analysis.

    The signals help distinguish between manipulation and legitimate news.
    """

    # Major media outlets (high credibility)
    MAJOR_SOURCES = {
        "Bloomberg", "Reuters", "Wall Street Journal", "WSJ",
        "CNBC", "Financial Times", "FT", "Associated Press", "AP",
        "MarketWatch", "Barron's", "The Economist",
        "연합뉴스", "조선일보", "중앙일보", "매일경제", "한국경제"
    }

    # News source tier weights
    SOURCE_WEIGHTS = {
        "MAJOR": 2.0,   # Bloomberg, Reuters, WSJ
        "MINOR": 0.5,   # Small news sites
        "SOCIAL": 0.1,  # Reddit, Twitter, blogs
        "UNKNOWN": 0.3  # Unknown sources
    }

    def __init__(self):
        """Initialize the calculator."""
        self.logger = logging.getLogger(__name__)
        self.source_classifier = get_classifier()

    def calculate_all_signals(self, cluster: NewsCluster) -> NewsCluster:
        """
        Calculate all 4 signals for a news cluster.

        Args:
            cluster: NewsCluster with articles

        Returns:
            Updated cluster with signal scores
        """
        cluster.di_score = self._calculate_di(cluster)
        cluster.tn_score = self._calculate_tn(cluster)
        cluster.ni_score = self._calculate_ni(cluster)
        cluster.el_matched, cluster.el_confidence, cluster.el_event_name = self._calculate_el(cluster)

        self.logger.debug(
            f"4-Signal calculated for {cluster.ticker}: "
            f"DI={cluster.di_score:.2f}, TN={cluster.tn_score:.2f}, "
            f"NI={cluster.ni_score:.2f}, EL={cluster.el_matched}"
        )

        return cluster

    def _calculate_di(self, cluster: NewsCluster) -> float:
        """
        Calculate Diversity Integrity (DI) score.

        DI measures source diversity. High DI = news from varied, credible sources.
        Low DI = news from similar/minor sources (manipulation risk).

        Formula:
        - Unique sources count (entropy)
        - Weighted by source tier (MAJOR > MINOR > SOCIAL)
        - Bonus if major media included

        Returns:
            0.0-1.0 (higher = more diverse and credible)
        """
        if not cluster.articles:
            return 0.5  # Neutral

        # Count unique sources with weights
        source_scores = {}
        for article in cluster.articles:
            source = article.source

            # Auto-classify source tier if not provided
            if not article.source_tier or article.source_tier == "UNKNOWN":
                source_info = self.source_classifier.classify(source, article.url)
                tier = source_info.tier.value
            else:
                tier = article.source_tier

            weight = self.SOURCE_WEIGHTS.get(tier, 0.3)

            if source not in source_scores:
                source_scores[source] = weight
            else:
                source_scores[source] += weight * 0.5  # Diminishing returns

        # Calculate diversity score
        total_weighted_sources = sum(source_scores.values())
        unique_sources = len(source_scores)

        # Base score: normalized by article count
        base_score = min(1.0, total_weighted_sources / len(cluster.articles))

        # Bonus if major media included
        has_major = any(
            article.source_tier == "MAJOR" or
            any(maj in article.source for maj in self.MAJOR_SOURCES)
            for article in cluster.articles
        )
        major_bonus = 0.2 if has_major else 0.0

        # Diversity bonus (more unique sources = better)
        diversity_bonus = min(0.2, unique_sources / 10)

        di_score = min(1.0, base_score + major_bonus + diversity_bonus)

        return di_score

    def _calculate_tn(self, cluster: NewsCluster) -> float:
        """
        Calculate Temporal Naturalness (TN) score.

        TN measures whether the timing pattern is natural or suspicious.

        Natural patterns:
        - News spread over minutes/hours (organic)
        - Clean timestamps (00:00, 14:30) for scheduled events

        Suspicious patterns:
        - All articles within 1 second (bot attack)
        - Random mid-second timestamps (14:23:47) for bulk releases

        Returns:
            -1.0 to +1.0 (negative = suspicious, positive = natural)
        """
        if len(cluster.articles) < 2:
            return 0.0  # Neutral

        timestamps = sorted([a.published_at for a in cluster.articles])
        first_ts = timestamps[0]
        last_ts = timestamps[-1]

        # Check if all articles are within 1 minute (burst)
        time_span_seconds = (last_ts - first_ts).total_seconds()

        if time_span_seconds < 60:
            # Burst detected - check if it's clean or suspicious

            # Clean timestamps (scheduled event): 09:00:00, 14:30:00
            is_clean_time = (
                first_ts.second == 0 and
                first_ts.minute % 30 == 0
            )

            if is_clean_time:
                # Scheduled event (embargo lift)
                return +0.8
            else:
                # Suspicious burst (manipulation)
                return -0.8

        elif time_span_seconds < 600:  # 10 minutes
            # Fast spread (could be viral or manipulation)
            # Check timestamp distribution
            time_gaps = [
                (timestamps[i+1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]

            # If gaps are very consistent (e.g., all 30 seconds), suspicious
            avg_gap = sum(time_gaps) / len(time_gaps)
            gap_variance = sum((g - avg_gap) ** 2 for g in time_gaps) / len(time_gaps)

            if gap_variance < 10:  # Very consistent gaps
                return -0.5  # Likely scripted
            else:
                return +0.3  # Natural viral spread

        else:
            # Slow organic spread over hours
            return +0.5

    def _calculate_ni(self, cluster: NewsCluster) -> float:
        """
        Calculate Narrative Independence (NI) score.

        NI measures content diversity. High NI = articles have different takes.
        Low NI = articles are copy-paste (manipulation risk).

        Uses text similarity (Jaccard similarity on title + content).

        Returns:
            0.0-1.0 (higher = more independent/diverse content)
        """
        if len(cluster.articles) < 2:
            return 0.5  # Neutral

        # Calculate pairwise text similarity
        similarities = []

        for i in range(len(cluster.articles)):
            for j in range(i + 1, len(cluster.articles)):
                article_i = cluster.articles[i]
                article_j = cluster.articles[j]

                # Combine title + content for comparison
                text_i = f"{article_i.title} {article_i.content}".lower()
                text_j = f"{article_j.title} {article_j.content}".lower()

                # Jaccard similarity on words
                words_i = set(text_i.split())
                words_j = set(text_j.split())

                intersection = len(words_i & words_j)
                union = len(words_i | words_j)

                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)

        if not similarities:
            return 0.5

        # Average similarity
        avg_similarity = sum(similarities) / len(similarities)

        # Convert to independence score (inverse of similarity)
        ni_score = 1.0 - avg_similarity

        # If similarity > 0.9 (near copy-paste), very low NI
        if avg_similarity > 0.9:
            ni_score *= 0.3  # Severe penalty

        return ni_score

    def _calculate_el(self, cluster: NewsCluster) -> Tuple[bool, float, Optional[str]]:
        """
        Calculate Event Legitimacy (EL) - is this a scheduled event?

        Checks if the news cluster matches a scheduled event like:
        - Earnings reports (quarterly, scheduled)
        - FOMC meetings (8 times/year, scheduled)
        - Economic data releases (CPI, NFP, etc.)
        - Product launches (announced in advance)

        Returns:
            (matched, confidence, event_name)
        """
        # TODO: Integrate with EconomicCalendar database
        # For now, use heuristic detection

        theme = cluster.theme.lower()
        first_ts = cluster.first_seen

        # Check if timestamp is "clean" (scheduled event indicator)
        is_clean_time = (
            first_ts.second == 0 and
            first_ts.minute % 30 == 0
        )

        # Earnings-related keywords
        earnings_keywords = ["earnings", "eps", "revenue", "quarterly", "q1", "q2", "q3", "q4"]
        is_earnings = any(kw in theme for kw in earnings_keywords)

        # FOMC/Fed keywords
        fomc_keywords = ["fomc", "fed", "federal reserve", "interest rate", "powell"]
        is_fomc = any(kw in theme for kw in fomc_keywords)

        # Economic data keywords
        econ_keywords = ["cpi", "inflation", "nfp", "jobs report", "gdp", "unemployment"]
        is_econ_data = any(kw in theme for kw in econ_keywords)

        # Determine legitimacy
        if is_clean_time and (is_earnings or is_fomc or is_econ_data):
            if is_fomc:
                return True, 0.95, "FOMC_MEETING"
            elif is_earnings:
                return True, 0.90, f"{cluster.ticker}_EARNINGS"
            elif is_econ_data:
                return True, 0.85, "ECONOMIC_DATA_RELEASE"

        elif is_earnings and first_ts.hour in [16, 17, 8, 9]:  # Pre/post market hours
            return True, 0.75, f"{cluster.ticker}_EARNINGS"

        return False, 0.0, None


class VerdictClassifier:
    """
    Classifies news clusters into verdict categories based on 4-Signal scores.

    Uses decision tree logic to combine DI, TN, NI, EL into a final verdict.
    """

    def __init__(self):
        """Initialize the classifier."""
        self.logger = logging.getLogger(__name__)

    def classify(self, cluster: NewsCluster) -> NewsCluster:
        """
        Classify a news cluster into a verdict category.

        Decision Logic:
        1. If EL matched (scheduled event) → EMBARGO_EVENT
        2. If DI high + NI high → ORGANIC_CONSENSUS
        3. If DI low + NI low + TN negative → MANIPULATION_ATTACK
        4. If TN negative + burst → SUSPICIOUS_BURST
        5. Otherwise → VIRAL_TREND

        Args:
            cluster: NewsCluster with 4-Signal scores

        Returns:
            Updated cluster with verdict and confidence_multiplier
        """
        di = cluster.di_score
        tn = cluster.tn_score
        ni = cluster.ni_score
        el_matched = cluster.el_matched
        el_conf = cluster.el_confidence

        # Rule 1: Scheduled event (highest priority)
        if el_matched and el_conf > 0.7:
            cluster.verdict = Verdict.EMBARGO_EVENT
            cluster.verdict_reason = (
                f"Scheduled event detected: {cluster.el_event_name} "
                f"(confidence: {el_conf:.2f})"
            )
            cluster.confidence_multiplier = 1.5  # Boost signal
            cluster.cooling_intensity = 0.0  # No cooling needed
            return cluster

        # Rule 2: Manipulation attack (high priority)
        if di < 0.4 and ni < 0.4 and tn < -0.5:
            cluster.verdict = Verdict.MANIPULATION_ATTACK
            cluster.verdict_reason = (
                f"Manipulation detected: Low diversity (DI={di:.2f}), "
                f"copy-paste content (NI={ni:.2f}), suspicious timing (TN={tn:.2f})"
            )
            cluster.confidence_multiplier = 0.0  # Block signal completely
            cluster.cooling_intensity = 1.0  # Full quarantine
            cluster.cooling_until = datetime.now() + timedelta(hours=24)
            return cluster

        # Rule 3: Suspicious burst (quarantine for investigation)
        if tn < -0.6 or (di < 0.5 and ni < 0.5):
            cluster.verdict = Verdict.SUSPICIOUS_BURST
            cluster.verdict_reason = (
                f"Suspicious pattern: DI={di:.2f}, TN={tn:.2f}, NI={ni:.2f}. "
                f"Quarantined for 30 minutes."
            )
            cluster.confidence_multiplier = 0.3  # Reduce signal significantly
            cluster.cooling_intensity = 0.7
            cluster.cooling_until = datetime.now() + timedelta(minutes=30)
            return cluster

        # Rule 4: Organic consensus (good news)
        if di > 0.7 and ni > 0.6:
            cluster.verdict = Verdict.ORGANIC_CONSENSUS
            cluster.verdict_reason = (
                f"Real consensus: High diversity (DI={di:.2f}), "
                f"independent narratives (NI={ni:.2f})"
            )
            cluster.confidence_multiplier = 1.2  # Boost signal moderately
            cluster.cooling_intensity = 0.0
            return cluster

        # Rule 5: Viral trend (default)
        cluster.verdict = Verdict.VIRAL_TREND
        cluster.verdict_reason = (
            f"Natural viral spread: DI={di:.2f}, TN={tn:.2f}, NI={ni:.2f}"
        )
        cluster.confidence_multiplier = 1.0  # Neutral
        cluster.cooling_intensity = 0.0
        return cluster


class NFPICalculator:
    """
    News Fraud Probability Index (NFPI) Calculator.

    Combines 4-Signal scores into a single fraud probability metric (0-100).
    Higher NFPI = higher manipulation risk.
    """

    def calculate_nfpi(self, cluster: NewsCluster) -> float:
        """
        Calculate NFPI (News Fraud Probability Index).

        Formula:
        NFPI = 100 * [
            0.3 * (1 - DI) +        # Low diversity penalty
            0.3 * (1 - NI) +        # Copy-paste penalty
            0.2 * max(0, -TN) +     # Suspicious timing penalty
            0.2 * (1 if not EL else 0)  # Unscheduled penalty
        ]

        Args:
            cluster: NewsCluster with 4-Signal scores

        Returns:
            0-100 (higher = more likely to be fraud/manipulation)
        """
        di = cluster.di_score
        ni = cluster.ni_score
        tn = cluster.tn_score
        el_matched = cluster.el_matched

        # Calculate components
        diversity_penalty = (1 - di) * 0.3
        copyPaste_penalty = (1 - ni) * 0.3
        timing_penalty = max(0, -tn) * 0.2  # Only negative TN contributes
        unscheduled_penalty = 0.2 if not el_matched else 0.0

        nfpi = 100 * (
            diversity_penalty +
            copyPaste_penalty +
            timing_penalty +
            unscheduled_penalty
        )

        return round(nfpi, 2)


# Example usage
if __name__ == "__main__":
    # Test case 1: Manipulation attack
    print("=" * 80)
    print("Test Case 1: Manipulation Attack")
    print("=" * 80)

    articles = [
        NewsArticle(
            id="1", ticker="AAPL", title="AAPL to moon! Buy now!",
            content="AAPL to moon! Buy now! Don't miss out!",
            source="randomsite1.com", source_tier="MINOR",
            published_at=datetime.now()
        ),
        NewsArticle(
            id="2", ticker="AAPL", title="AAPL to moon! Buy now!",
            content="AAPL to moon! Buy now! Don't miss out!",
            source="randomsite2.com", source_tier="MINOR",
            published_at=datetime.now() + timedelta(seconds=1)
        ),
        NewsArticle(
            id="3", ticker="AAPL", title="AAPL to moon! Buy now!",
            content="AAPL to moon! Buy now! Don't miss out!",
            source="randomsite3.com", source_tier="MINOR",
            published_at=datetime.now() + timedelta(seconds=2)
        ),
    ]

    cluster = NewsCluster(
        fingerprint="test1",
        ticker="AAPL",
        theme="moon_hype",
        articles=articles,
        first_seen=articles[0].published_at,
        last_seen=articles[-1].published_at
    )

    calculator = FourSignalCalculator()
    classifier = VerdictClassifier()
    nfpi_calc = NFPICalculator()

    cluster = calculator.calculate_all_signals(cluster)
    cluster = classifier.classify(cluster)
    nfpi = nfpi_calc.calculate_nfpi(cluster)

    print(f"Ticker: {cluster.ticker}")
    print(f"Articles: {len(cluster.articles)}")
    print(f"DI Score: {cluster.di_score:.2f}")
    print(f"TN Score: {cluster.tn_score:.2f}")
    print(f"NI Score: {cluster.ni_score:.2f}")
    print(f"EL Matched: {cluster.el_matched}")
    print(f"Verdict: {cluster.verdict}")
    print(f"Reason: {cluster.verdict_reason}")
    print(f"Confidence Multiplier: {cluster.confidence_multiplier:.2f}")
    print(f"NFPI: {nfpi:.2f}%")
    print()

    # Test case 2: Legitimate earnings
    print("=" * 80)
    print("Test Case 2: Legitimate Earnings Event")
    print("=" * 80)

    earnings_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)

    articles2 = [
        NewsArticle(
            id="4", ticker="AAPL", title="Apple beats Q4 earnings expectations",
            content="Apple reported strong Q4 earnings with EPS of $1.50, beating estimates.",
            source="Bloomberg", source_tier="MAJOR",
            published_at=earnings_time
        ),
        NewsArticle(
            id="5", ticker="AAPL", title="AAPL Q4 results exceed forecasts",
            content="Apple's quarterly results surpassed Wall Street expectations as iPhone sales grew.",
            source="Reuters", source_tier="MAJOR",
            published_at=earnings_time + timedelta(minutes=2)
        ),
        NewsArticle(
            id="6", ticker="AAPL", title="Apple stock rises on earnings beat",
            content="Shares of Apple climbed in after-hours trading following the earnings announcement.",
            source="CNBC", source_tier="MAJOR",
            published_at=earnings_time + timedelta(minutes=5)
        ),
    ]

    cluster2 = NewsCluster(
        fingerprint="test2",
        ticker="AAPL",
        theme="quarterly earnings beat",
        articles=articles2,
        first_seen=articles2[0].published_at,
        last_seen=articles2[-1].published_at
    )

    cluster2 = calculator.calculate_all_signals(cluster2)
    cluster2 = classifier.classify(cluster2)
    nfpi2 = nfpi_calc.calculate_nfpi(cluster2)

    print(f"Ticker: {cluster2.ticker}")
    print(f"Articles: {len(cluster2.articles)}")
    print(f"DI Score: {cluster2.di_score:.2f}")
    print(f"TN Score: {cluster2.tn_score:.2f}")
    print(f"NI Score: {cluster2.ni_score:.2f}")
    print(f"EL Matched: {cluster2.el_matched}")
    print(f"EL Event: {cluster2.el_event_name}")
    print(f"Verdict: {cluster2.verdict}")
    print(f"Reason: {cluster2.verdict_reason}")
    print(f"Confidence Multiplier: {cluster2.confidence_multiplier:.2f}")
    print(f"NFPI: {nfpi2:.2f}%")
    print()

    print("=" * 80)
    print("4-Signal Framework test completed!")
    print("=" * 80)
