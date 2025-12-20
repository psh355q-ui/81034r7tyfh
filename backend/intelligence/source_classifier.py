"""
Source Tier Classifier for News Credibility Assessment.

Automatically classifies news sources into tiers:
- MAJOR: Established, credible news organizations (Bloomberg, Reuters, WSJ)
- MINOR: Smaller, regional, or specialized news sites
- SOCIAL: Social media, blogs, forums (Reddit, Twitter, personal blogs)
- UNKNOWN: Unrecognized sources

This classification is critical for the DI (Diversity Integrity) signal
in the 4-Signal Consensus Framework.

Author: AI Trading System Team
Date: 2025-12-19
Phase: 18
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SourceTier(str, Enum):
    """News source tier classifications."""
    MAJOR = "MAJOR"      # High credibility, established organizations
    MINOR = "MINOR"      # Smaller or regional news sites
    SOCIAL = "SOCIAL"    # Social media, blogs, forums
    UNKNOWN = "UNKNOWN"  # Unrecognized or new sources


@dataclass
class SourceInfo:
    """Information about a news source."""
    name: str
    tier: SourceTier
    credibility_score: float  # 0.0-1.0
    country: Optional[str] = None
    category: Optional[str] = None  # "financial", "general", "tech", etc.


class SourceTierClassifier:
    """
    Classifies news sources into credibility tiers.

    Uses a combination of:
    1. Known source database (curated list)
    2. Domain patterns (e.g., .gov, .edu)
    3. Name patterns (e.g., "Times", "Post", "News")
    """

    # Major news organizations (Tier 1)
    MAJOR_SOURCES = {
        # US Financial
        "Bloomberg": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Bloomberg News": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Bloomberg.com": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Reuters": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Reuters.com": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Wall Street Journal": {"credibility": 0.95, "country": "US", "category": "financial"},
        "WSJ": {"credibility": 0.95, "country": "US", "category": "financial"},
        "WSJ.com": {"credibility": 0.95, "country": "US", "category": "financial"},
        "Financial Times": {"credibility": 0.95, "country": "UK", "category": "financial"},
        "FT": {"credibility": 0.95, "country": "UK", "category": "financial"},
        "FT.com": {"credibility": 0.95, "country": "UK", "category": "financial"},
        "CNBC": {"credibility": 0.90, "country": "US", "category": "financial"},
        "MarketWatch": {"credibility": 0.85, "country": "US", "category": "financial"},
        "Barron's": {"credibility": 0.90, "country": "US", "category": "financial"},
        "Investor's Business Daily": {"credibility": 0.85, "country": "US", "category": "financial"},
        "The Economist": {"credibility": 0.90, "country": "UK", "category": "financial"},

        # US General News
        "Associated Press": {"credibility": 0.95, "country": "US", "category": "general"},
        "AP": {"credibility": 0.95, "country": "US", "category": "general"},
        "AP News": {"credibility": 0.95, "country": "US", "category": "general"},
        "New York Times": {"credibility": 0.90, "country": "US", "category": "general"},
        "NYTimes": {"credibility": 0.90, "country": "US", "category": "general"},
        "Washington Post": {"credibility": 0.90, "country": "US", "category": "general"},
        "USA Today": {"credibility": 0.80, "country": "US", "category": "general"},
        "CNN": {"credibility": 0.75, "country": "US", "category": "general"},
        "Fox Business": {"credibility": 0.75, "country": "US", "category": "financial"},

        # Korean Major News
        "연합뉴스": {"credibility": 0.90, "country": "KR", "category": "general"},
        "Yonhap": {"credibility": 0.90, "country": "KR", "category": "general"},
        "조선일보": {"credibility": 0.85, "country": "KR", "category": "general"},
        "Chosun Ilbo": {"credibility": 0.85, "country": "KR", "category": "general"},
        "중앙일보": {"credibility": 0.85, "country": "KR", "category": "general"},
        "JoongAng Ilbo": {"credibility": 0.85, "country": "KR", "category": "general"},
        "동아일보": {"credibility": 0.85, "country": "KR", "category": "general"},
        "Donga Ilbo": {"credibility": 0.85, "country": "KR", "category": "general"},
        "한국경제": {"credibility": 0.90, "country": "KR", "category": "financial"},
        "Hankyung": {"credibility": 0.90, "country": "KR", "category": "financial"},
        "매일경제": {"credibility": 0.90, "country": "KR", "category": "financial"},
        "Maeil Business": {"credibility": 0.90, "country": "KR", "category": "financial"},
        "서울경제": {"credibility": 0.85, "country": "KR", "category": "financial"},

        # Tech News
        "TechCrunch": {"credibility": 0.80, "country": "US", "category": "tech"},
        "The Verge": {"credibility": 0.80, "country": "US", "category": "tech"},
        "Ars Technica": {"credibility": 0.85, "country": "US", "category": "tech"},
        "CNET": {"credibility": 0.75, "country": "US", "category": "tech"},

        # International
        "BBC": {"credibility": 0.90, "country": "UK", "category": "general"},
        "BBC News": {"credibility": 0.90, "country": "UK", "category": "general"},
        "Guardian": {"credibility": 0.85, "country": "UK", "category": "general"},
        "The Guardian": {"credibility": 0.85, "country": "UK", "category": "general"},
    }

    # Social media and user-generated content platforms
    SOCIAL_PLATFORMS = {
        "Reddit", "Twitter", "X.com", "Facebook", "LinkedIn",
        "Medium", "Substack", "YouTube", "TikTok", "Instagram",
        "Discord", "Telegram", "WeChat", "KakaoTalk",
        "네이버 블로그", "다음 블로그", "티스토리"
    }

    # Domain patterns for classification
    TRUSTED_DOMAINS = {
        ".gov",   # Government sites
        ".edu",   # Educational institutions
        ".mil",   # Military
        ".go.kr", # Korean government
        ".ac.kr", # Korean academic
    }

    def __init__(self):
        """Initialize the classifier."""
        self.logger = logging.getLogger(__name__)

        # Build normalized lookup (lowercase keys)
        self.major_lookup = {
            k.lower(): v for k, v in self.MAJOR_SOURCES.items()
        }

        self.social_lookup = {
            s.lower() for s in self.SOCIAL_PLATFORMS
        }

        self.logger.info(
            f"SourceTierClassifier initialized: "
            f"{len(self.major_lookup)} major sources, "
            f"{len(self.social_lookup)} social platforms"
        )

    def classify(self, source: str, url: Optional[str] = None) -> SourceInfo:
        """
        Classify a news source into a tier.

        Args:
            source: Source name (e.g., "Bloomberg", "reddit.com")
            url: Optional full URL for domain analysis

        Returns:
            SourceInfo with tier and credibility score
        """
        source_lower = source.lower()

        # Step 1: Check major sources (exact match)
        if source_lower in self.major_lookup:
            info = self.major_lookup[source_lower]
            return SourceInfo(
                name=source,
                tier=SourceTier.MAJOR,
                credibility_score=info["credibility"],
                country=info.get("country"),
                category=info.get("category")
            )

        # Step 2: Check major sources (partial match)
        for major_name, info in self.major_lookup.items():
            if major_name in source_lower or source_lower in major_name:
                return SourceInfo(
                    name=source,
                    tier=SourceTier.MAJOR,
                    credibility_score=info["credibility"],
                    country=info.get("country"),
                    category=info.get("category")
                )

        # Step 3: Check social media platforms
        for social_name in self.social_lookup:
            if social_name in source_lower:
                return SourceInfo(
                    name=source,
                    tier=SourceTier.SOCIAL,
                    credibility_score=0.2,
                    category="social"
                )

        # Step 4: Check URL domain patterns (if available)
        if url:
            url_lower = url.lower()

            # Trusted domains
            for domain in self.TRUSTED_DOMAINS:
                if domain in url_lower:
                    return SourceInfo(
                        name=source,
                        tier=SourceTier.MAJOR,
                        credibility_score=0.90,
                        category="official"
                    )

            # Social domains
            if any(s in url_lower for s in ["reddit.com", "twitter.com", "x.com", "facebook.com"]):
                return SourceInfo(
                    name=source,
                    tier=SourceTier.SOCIAL,
                    credibility_score=0.2,
                    category="social"
                )

        # Step 5: Heuristic patterns
        credibility, tier = self._apply_heuristics(source)

        return SourceInfo(
            name=source,
            tier=tier,
            credibility_score=credibility,
            category="unknown"
        )

    def _apply_heuristics(self, source: str) -> tuple[float, SourceTier]:
        """
        Apply heuristic rules to estimate credibility.

        Heuristics:
        - Contains "Times", "Post", "Herald" → likely MINOR (0.5)
        - Contains "News", "Today", "Daily" → likely MINOR (0.5)
        - Contains numbers or random chars → likely MINOR/UNKNOWN (0.3)
        - Very short name (< 5 chars) → likely UNKNOWN (0.3)
        - Contains "blog", "opinion", "analyst" → SOCIAL (0.3)
        """
        source_lower = source.lower()

        # Blog/opinion indicators
        if any(kw in source_lower for kw in ["blog", "blogger", "opinion", "analyst", "substack"]):
            return 0.3, SourceTier.SOCIAL

        # Established news patterns
        if any(kw in source_lower for kw in ["times", "post", "herald", "tribune", "journal"]):
            return 0.5, SourceTier.MINOR

        if any(kw in source_lower for kw in ["news", "today", "daily", "press", "gazette"]):
            return 0.5, SourceTier.MINOR

        # Financial keywords
        if any(kw in source_lower for kw in ["finance", "economic", "market", "invest", "trade"]):
            return 0.5, SourceTier.MINOR

        # Suspicious patterns
        if any(char.isdigit() for char in source):
            return 0.3, SourceTier.UNKNOWN

        if len(source) < 5:
            return 0.3, SourceTier.UNKNOWN

        # Default: UNKNOWN with low credibility
        return 0.4, SourceTier.UNKNOWN

    def classify_batch(self, sources: list[str]) -> Dict[str, SourceInfo]:
        """
        Classify multiple sources at once.

        Args:
            sources: List of source names

        Returns:
            Dict mapping source name to SourceInfo
        """
        results = {}
        for source in sources:
            results[source] = self.classify(source)
        return results

    def get_tier_weight(self, tier: SourceTier) -> float:
        """
        Get the weight for a source tier (for DI calculation).

        Returns:
            Weight multiplier (0.1-2.0)
        """
        weights = {
            SourceTier.MAJOR: 2.0,
            SourceTier.MINOR: 0.5,
            SourceTier.SOCIAL: 0.1,
            SourceTier.UNKNOWN: 0.3,
        }
        return weights.get(tier, 0.3)

    def is_major_source(self, source: str) -> bool:
        """Quick check if source is a major news organization."""
        info = self.classify(source)
        return info.tier == SourceTier.MAJOR

    def get_stats(self) -> Dict:
        """Get classifier statistics."""
        return {
            "major_sources_count": len(self.major_lookup),
            "social_platforms_count": len(self.social_lookup),
            "supported_tiers": [tier.value for tier in SourceTier],
        }


# Singleton instance
_classifier_instance: Optional[SourceTierClassifier] = None


def get_classifier() -> SourceTierClassifier:
    """Get or create the global classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SourceTierClassifier()
    return _classifier_instance


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Source Tier Classifier Test")
    print("=" * 80)
    print()

    classifier = SourceTierClassifier()

    # Test cases
    test_sources = [
        ("Bloomberg", None),
        ("Reuters", None),
        ("Wall Street Journal", None),
        ("CNBC", None),
        ("연합뉴스", None),
        ("한국경제", None),
        ("Reddit", None),
        ("Twitter", None),
        ("TechCrunch", None),
        ("Some Random News Site", None),
        ("randomsite123.com", "http://randomsite123.com/article"),
        ("Financial Times", None),
        ("매일경제", None),
        ("네이버 블로그", None),
        ("The Verge", None),
    ]

    print("Classifying sources:")
    print("-" * 80)
    print(f"{'Source':<30} {'Tier':<12} {'Credibility':<12} {'Weight':<8}")
    print("-" * 80)

    for source, url in test_sources:
        info = classifier.classify(source, url)
        weight = classifier.get_tier_weight(info.tier)

        print(
            f"{source:<30} "
            f"{info.tier.value:<12} "
            f"{info.credibility_score:<12.2f} "
            f"{weight:<8.1f}x"
        )

    print()
    print("-" * 80)

    # Statistics
    stats = classifier.get_stats()
    print("\nClassifier Statistics:")
    print(f"  Major sources: {stats['major_sources_count']}")
    print(f"  Social platforms: {stats['social_platforms_count']}")
    print(f"  Supported tiers: {', '.join(stats['supported_tiers'])}")

    # Batch classification
    print("\n" + "=" * 80)
    print("Batch Classification Test")
    print("=" * 80)

    batch_sources = ["Bloomberg", "Reddit", "Unknown Site", "WSJ"]
    results = classifier.classify_batch(batch_sources)

    for source, info in results.items():
        print(f"{source}: {info.tier.value} (credibility: {info.credibility_score:.2f})")

    print()
    print("=" * 80)
    print("Source Tier Classifier test completed!")
    print("=" * 80)
