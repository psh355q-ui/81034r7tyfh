"""
Non-Standard Risk Factor Calculation.

Analyzes news/social media for negative keywords to detect risks that
traditional fundamental/technical analysis might miss.

Keywords tracked:
- 횡령 (embezzlement)
- 압수수색 (raid)
- 제품결함 (product defect)
- 소송 (lawsuit)
- 파업 (strike)
- 회계부정 (accounting fraud)
- 배임 (breach of trust)
- 내부고발 (whistleblowing)
- 리콜 (recall)

No AI used - pure rule-based analysis.
Cost: $0
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from .news_collector import NewsCollector, NewsArticle

logger = logging.getLogger(__name__)


# Risk keyword categories
RISK_KEYWORDS = {
    "legal": [
        "lawsuit", "sued", "litigation", "court", "settlement",
        "소송", "고소", "법정", "합의",
    ],
    "regulatory": [
        "investigation", "raid", "sec", "fda", "ftc",
        "압수수색", "조사", "검찰", "감사원",
    ],
    "operational": [
        "recall", "defect", "malfunction", "failure", "outage",
        "리콜", "결함", "고장", "장애", "중단",
    ],
    "labor": [
        "strike", "walkout", "union", "layoff", "protest",
        "파업", "노조", "해고", "시위", "쟁의",
    ],
    "governance": [
        "fraud", "embezzlement", "bribery", "corruption", "whistleblower",
        "횡령", "배임", "뇌물", "부정", "내부고발",
    ],
    "reputation": [
        "scandal", "controversy", "boycott", "backlash",
        "스캔들", "논란", "불매", "반발",
    ],
}


class NonStandardRiskCalculator:
    """
    Calculate non-standard risk score based on news keyword analysis.

    Risk Score Range: 0.0 (no risk) to 1.0 (extreme risk)
    """

    def __init__(self, news_collector: Optional[NewsCollector] = None):
        """
        Initialize risk calculator.

        Args:
            news_collector: NewsCollector instance (creates new if None)
        """
        self.news_collector = news_collector or NewsCollector()

        # Risk scoring weights by category
        self.category_weights = {
            "legal": 0.15,
            "regulatory": 0.25,  # Highest weight
            "operational": 0.20,
            "labor": 0.10,
            "governance": 0.25,  # Highest weight
            "reputation": 0.05,
        }

    async def calculate_risk(
        self,
        ticker: str,
        days: int = 30,
        use_cache: bool = True,
    ) -> Dict:
        """
        Calculate non-standard risk score for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze (default 30)
            use_cache: Whether to use cached news (default True)

        Returns:
            Dict with:
                - risk_score: 0.0-1.0 (overall risk)
                - category_scores: dict of category-specific scores
                - risk_articles: list of articles triggering risk
                - total_articles: total articles analyzed
                - keywords_found: dict of keyword counts
        """
        logger.info(f"Calculating non-standard risk for {ticker} (last {days} days)")

        # Fetch news
        news_articles = await self.news_collector.fetch_news(
            ticker=ticker,
            days=days,
        )

        if not news_articles:
            logger.warning(f"No news found for {ticker}")
            return self._empty_risk_result()

        # Analyze each article for risk keywords
        category_mentions = {cat: 0 for cat in RISK_KEYWORDS.keys()}
        risk_articles = []
        all_keywords_found = {}

        for article in news_articles:
            text = article.get_full_text().lower()

            article_risk = False
            article_keywords = []

            # Check each category
            for category, keywords in RISK_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        category_mentions[category] += 1
                        article_risk = True
                        article_keywords.append(keyword)

                        # Track keyword frequency
                        all_keywords_found[keyword] = (
                            all_keywords_found.get(keyword, 0) + 1
                        )

            # If article mentions risk keywords, add to risk_articles
            if article_risk:
                risk_articles.append({
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at,
                    "keywords": article_keywords,
                })

        # Calculate category-specific scores
        total_articles = len(news_articles)
        category_scores = {}

        for category, mentions in category_mentions.items():
            # Score = (mentions / total_articles) normalized to 0-1
            # Cap at 1.0 if mentions > articles (multiple mentions per article)
            raw_score = mentions / total_articles if total_articles > 0 else 0
            normalized_score = min(raw_score / 0.3, 1.0)  # 30% mention rate = max risk
            category_scores[category] = normalized_score

        # Calculate weighted overall risk score
        risk_score = sum(
            category_scores[cat] * self.category_weights[cat]
            for cat in RISK_KEYWORDS.keys()
        )

        logger.info(
            f"Risk score for {ticker}: {risk_score:.2f} "
            f"({len(risk_articles)}/{total_articles} articles)"
        )

        return {
            "risk_score": risk_score,
            "category_scores": category_scores,
            "risk_articles": risk_articles,
            "total_articles": total_articles,
            "keywords_found": all_keywords_found,
            "analyzed_at": datetime.now(),
        }

    def _empty_risk_result(self) -> Dict:
        """Return empty risk result when no news available."""
        return {
            "risk_score": 0.0,
            "category_scores": {cat: 0.0 for cat in RISK_KEYWORDS.keys()},
            "risk_articles": [],
            "total_articles": 0,
            "keywords_found": {},
            "analyzed_at": datetime.now(),
        }

    def interpret_risk_score(self, risk_score: float) -> Dict:
        """
        Interpret risk score into actionable recommendation.

        Args:
            risk_score: Risk score (0.0-1.0)

        Returns:
            Dict with interpretation and recommended action
        """
        if risk_score < 0.1:
            return {
                "level": "LOW",
                "interpretation": "Minimal non-standard risk detected",
                "action": "No special action required",
                "max_position_size": 5.0,  # Full position allowed
            }
        elif risk_score < 0.3:
            return {
                "level": "MODERATE",
                "interpretation": "Some concerning news detected",
                "action": "Monitor closely, reduce position size",
                "max_position_size": 3.0,  # Reduce to 3%
            }
        elif risk_score < 0.6:
            return {
                "level": "HIGH",
                "interpretation": "Significant risk factors present",
                "action": "Avoid new positions, consider reducing existing",
                "max_position_size": 1.0,  # Minimal position only
            }
        else:
            return {
                "level": "CRITICAL",
                "interpretation": "Severe risk detected - major negative news",
                "action": "Do not trade - await clarification",
                "max_position_size": 0.0,  # No position allowed
            }


# =============================================================================
# Feature Store Integration
# =============================================================================

async def calculate_non_standard_risk_feature(
    ticker: str,
    as_of_date: datetime,
    days: int = 30,
) -> float:
    """
    Calculate non-standard risk feature for Feature Store.

    This function is designed to be called by Feature Store.

    Args:
        ticker: Stock ticker symbol
        as_of_date: Date to calculate feature for
        days: Number of days to look back (default 30)

    Returns:
        Risk score (0.0-1.0)
    """
    calculator = NonStandardRiskCalculator()
    result = await calculator.calculate_risk(ticker, days)
    return result["risk_score"]