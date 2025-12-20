"""
Query Complexity Analyzer for GraphRAG Dynamic Selection.

This module analyzes query complexity to determine the optimal GraphRAG search mode:
- LOCAL: For simple, specific queries (e.g., "What is AAPL's P/E ratio?")
- GLOBAL: For complex, broad queries (e.g., "Analyze tech sector trends")
- HYBRID: For medium complexity queries

Author: AI Trading System Team
Date: 2025-12-19
Phase: 1.4 - Cost Optimization
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class GraphRAGMode(str, Enum):
    """GraphRAG search modes."""
    LOCAL = "LOCAL"     # Specific entity/document search (cheap, fast)
    GLOBAL = "GLOBAL"   # Community summary search (expensive, comprehensive)
    HYBRID = "HYBRID"   # Combined approach (balanced)


class QueryType(str, Enum):
    """Query type classifications."""
    FACTUAL = "FACTUAL"           # "What is X?"
    COMPARATIVE = "COMPARATIVE"   # "Compare X and Y"
    ANALYTICAL = "ANALYTICAL"     # "Analyze X"
    TREND = "TREND"               # "Trend of X"
    SUMMARIZATION = "SUMMARIZATION"  # "Summarize X"
    EXPLORATORY = "EXPLORATORY"   # "Tell me about X"


@dataclass
class ComplexityScore:
    """Query complexity scoring."""
    scope_score: float        # 0-1: narrow to broad
    depth_score: float        # 0-1: shallow to deep
    entity_count: int         # Number of entities mentioned
    has_comparison: bool      # Contains comparison keywords
    has_aggregation: bool     # Requires aggregation (e.g., "all", "overall")
    overall_score: float      # 0-1: simple to complex
    query_type: QueryType
    recommended_mode: GraphRAGMode
    reasoning: str


class QueryComplexityAnalyzer:
    """
    Analyzes query complexity to recommend optimal GraphRAG mode.

    Scoring criteria:
    1. Scope: narrow (specific ticker) vs broad (sector/market)
    2. Depth: surface (facts) vs deep (analysis/trends)
    3. Entity count: single entity vs multiple entities
    4. Comparison: yes/no
    5. Aggregation: requires summary of multiple sources

    Recommendation logic:
    - Overall score < 0.3 → LOCAL (77% cheaper)
    - Overall score > 0.7 → GLOBAL (most comprehensive)
    - 0.3-0.7 → HYBRID (balanced)
    """

    # Keyword patterns for complexity detection
    NARROW_KEYWORDS = [
        "what is", "show", "get", "find", "display",
        "price", "value", "current", "latest"
    ]

    BROAD_KEYWORDS = [
        "all", "overall", "entire", "whole", "total",
        "market", "sector", "industry", "portfolio"
    ]

    ANALYTICAL_KEYWORDS = [
        "analyze", "assess", "evaluate", "examine",
        "trend", "pattern", "correlation", "impact",
        "forecast", "predict", "estimate"
    ]

    COMPARISON_KEYWORDS = [
        "compare", "versus", "vs", "difference", "between",
        "better", "worse", "higher", "lower"
    ]

    AGGREGATION_KEYWORDS = [
        "summarize", "overview", "summary", "top",
        "best", "worst", "most", "least"
    ]

    def __init__(self):
        """Initialize the analyzer."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("QueryComplexityAnalyzer initialized")

    def analyze(self, query: str) -> ComplexityScore:
        """
        Analyze query complexity and recommend GraphRAG mode.

        Args:
            query: User query string

        Returns:
            ComplexityScore with mode recommendation
        """
        query_lower = query.lower()

        # Detect query type
        query_type = self._detect_query_type(query_lower)

        # Calculate individual scores
        scope_score = self._calculate_scope_score(query_lower)
        depth_score = self._calculate_depth_score(query_lower, query_type)
        entity_count = self._count_entities(query)
        has_comparison = self._has_comparison(query_lower)
        has_aggregation = self._has_aggregation(query_lower)

        # Calculate overall complexity (weighted average)
        overall_score = (
            scope_score * 0.3 +
            depth_score * 0.3 +
            min(entity_count / 5.0, 1.0) * 0.2 +
            (1.0 if has_comparison else 0.0) * 0.1 +
            (1.0 if has_aggregation else 0.0) * 0.1
        )

        # Recommend mode
        recommended_mode, reasoning = self._recommend_mode(
            overall_score, query_type, scope_score, has_comparison
        )

        self.logger.debug(
            f"Query complexity: {overall_score:.2f} → {recommended_mode.value}\n"
            f"  Scope: {scope_score:.2f}, Depth: {depth_score:.2f}, "
            f"Entities: {entity_count}, Type: {query_type.value}"
        )

        return ComplexityScore(
            scope_score=scope_score,
            depth_score=depth_score,
            entity_count=entity_count,
            has_comparison=has_comparison,
            has_aggregation=has_aggregation,
            overall_score=overall_score,
            query_type=query_type,
            recommended_mode=recommended_mode,
            reasoning=reasoning
        )

    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query."""
        if any(kw in query for kw in ["compare", "versus", "vs", "difference"]):
            return QueryType.COMPARATIVE

        if any(kw in query for kw in ["analyze", "assess", "evaluate"]):
            return QueryType.ANALYTICAL

        if any(kw in query for kw in ["trend", "pattern", "over time"]):
            return QueryType.TREND

        if any(kw in query for kw in ["summarize", "overview", "summary"]):
            return QueryType.SUMMARIZATION

        if any(kw in query for kw in ["what is", "show", "get", "find"]):
            return QueryType.FACTUAL

        return QueryType.EXPLORATORY

    def _calculate_scope_score(self, query: str) -> float:
        """
        Calculate scope score (0 = narrow, 1 = broad).

        Narrow: specific ticker, single entity
        Broad: sector, market, portfolio, multiple entities
        """
        # Check for broad keywords
        broad_count = sum(1 for kw in self.BROAD_KEYWORDS if kw in query)
        narrow_count = sum(1 for kw in self.NARROW_KEYWORDS if kw in query)

        # Check for ticker patterns (narrow indicators)
        has_ticker = bool(re.search(r'\b[A-Z]{2,5}\b', query))

        # Calculate score
        if broad_count > 0:
            return min(0.5 + broad_count * 0.2, 1.0)
        elif narrow_count > 0 or has_ticker:
            return max(0.0, 0.3 - narrow_count * 0.1)
        else:
            return 0.5  # Default: medium scope

    def _calculate_depth_score(self, query: str, query_type: QueryType) -> float:
        """
        Calculate depth score (0 = shallow, 1 = deep).

        Shallow: facts, current values
        Deep: analysis, trends, correlations
        """
        # Analytical queries are inherently deep
        if query_type in [QueryType.ANALYTICAL, QueryType.TREND]:
            return 0.8

        # Count analytical keywords
        analytical_count = sum(
            1 for kw in self.ANALYTICAL_KEYWORDS if kw in query
        )

        # Simple factual queries are shallow
        if query_type == QueryType.FACTUAL:
            return 0.2

        # Comparative queries are medium-deep
        if query_type == QueryType.COMPARATIVE:
            return 0.6

        # Default: medium depth
        return min(0.5 + analytical_count * 0.2, 1.0)

    def _count_entities(self, query: str) -> int:
        """
        Count the number of entities (tickers, companies) mentioned.

        Uses simple heuristics:
        - All-caps words (2-5 chars) = tickers
        - Proper nouns = companies
        """
        # Find ticker patterns (all caps, 2-5 chars)
        tickers = re.findall(r'\b[A-Z]{2,5}\b', query)

        # Rough estimate: at least 1 entity if query is not empty
        return max(len(tickers), 1)

    def _has_comparison(self, query: str) -> bool:
        """Check if query involves comparison."""
        return any(kw in query for kw in self.COMPARISON_KEYWORDS)

    def _has_aggregation(self, query: str) -> bool:
        """Check if query requires aggregation."""
        return any(kw in query for kw in self.AGGREGATION_KEYWORDS)

    def _recommend_mode(
        self,
        overall_score: float,
        query_type: QueryType,
        scope_score: float,
        has_comparison: bool
    ) -> Tuple[GraphRAGMode, str]:
        """
        Recommend GraphRAG mode based on complexity scores.

        Logic:
        1. Very simple queries (<0.3) → LOCAL
        2. Very complex queries (>0.7) → GLOBAL
        3. Comparative queries → HYBRID (need both local details and global context)
        4. Broad scope queries (>0.7) → GLOBAL
        5. Medium complexity (0.3-0.7) → HYBRID

        Returns:
            (mode, reasoning)
        """
        # Rule 1: Very simple, specific queries → LOCAL
        if overall_score < 0.3 and scope_score < 0.4:
            return (
                GraphRAGMode.LOCAL,
                "Simple, specific query - local search is sufficient and 77% cheaper"
            )

        # Rule 2: Very complex or broad queries → GLOBAL
        if overall_score > 0.7 or scope_score > 0.7:
            return (
                GraphRAGMode.GLOBAL,
                "Complex or broad query requiring comprehensive community summaries"
            )

        # Rule 3: Comparative queries → HYBRID
        if has_comparison:
            return (
                GraphRAGMode.HYBRID,
                "Comparison requires both specific entity details (local) and contextual understanding (global)"
            )

        # Rule 4: Analytical queries → HYBRID (unless very simple or very complex)
        if query_type in [QueryType.ANALYTICAL, QueryType.TREND]:
            if overall_score < 0.4:
                return (
                    GraphRAGMode.LOCAL,
                    "Simple analytical query - focused local search"
                )
            else:
                return (
                    GraphRAGMode.HYBRID,
                    "Analytical query benefits from both detailed data and broader context"
                )

        # Rule 5: Medium complexity → HYBRID (default)
        return (
            GraphRAGMode.HYBRID,
            "Medium complexity query - hybrid search balances cost and comprehensiveness"
        )

    def get_cost_estimate(
        self,
        mode: GraphRAGMode,
        baseline_tokens: int = 10000
    ) -> Dict[str, float]:
        """
        Estimate token usage and cost for different modes.

        Args:
            mode: GraphRAG mode
            baseline_tokens: Reference token count for GLOBAL mode

        Returns:
            Dict with tokens, cost_usd, and savings_pct
        """
        # Token multipliers (relative to GLOBAL = 1.0)
        multipliers = {
            GraphRAGMode.LOCAL: 0.23,    # 77% reduction
            GraphRAGMode.HYBRID: 0.60,   # 40% reduction
            GraphRAGMode.GLOBAL: 1.0     # Baseline
        }

        multiplier = multipliers[mode]
        tokens = int(baseline_tokens * multiplier)

        # Claude pricing: $3/MTok input, $15/MTok output (assume 80% input, 20% output)
        input_cost = (tokens * 0.8) * 3.0 / 1_000_000
        output_cost = (tokens * 0.2) * 15.0 / 1_000_000
        total_cost = input_cost + output_cost

        # Calculate savings vs GLOBAL
        global_cost = (baseline_tokens * 0.8) * 3.0 / 1_000_000 + \
                      (baseline_tokens * 0.2) * 15.0 / 1_000_000
        savings_pct = ((global_cost - total_cost) / global_cost) * 100 if mode != GraphRAGMode.GLOBAL else 0.0

        return {
            "tokens": tokens,
            "cost_usd": round(total_cost, 4),
            "savings_pct": round(savings_pct, 1),
            "vs_global_tokens": baseline_tokens,
            "vs_global_cost": round(global_cost, 4)
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Query Complexity Analyzer Test")
    print("=" * 80)
    print()

    analyzer = QueryComplexityAnalyzer()

    # Test queries
    test_queries = [
        # Simple queries → LOCAL
        "What is AAPL's current price?",
        "Show me TSLA's P/E ratio",
        "Get the latest earnings for MSFT",

        # Medium queries → HYBRID
        "Compare AAPL and MSFT performance",
        "Analyze TSLA's growth trend",
        "What are the risk factors for NVDA?",

        # Complex queries → GLOBAL
        "Analyze the entire tech sector performance",
        "Summarize all semiconductor companies' outlook",
        "What are the overall market trends in AI stocks?",
        "Evaluate the portfolio's exposure to tech sector risks"
    ]

    print("Testing queries:")
    print("-" * 80)

    for query in test_queries:
        result = analyzer.analyze(query)
        cost_est = analyzer.get_cost_estimate(result.recommended_mode)

        print(f"\nQuery: \"{query}\"")
        print(f"  Type: {result.query_type.value}")
        print(f"  Complexity: {result.overall_score:.2f} "
              f"(scope={result.scope_score:.2f}, depth={result.depth_score:.2f})")
        print(f"  Entities: {result.entity_count}, "
              f"Comparison: {result.has_comparison}, "
              f"Aggregation: {result.has_aggregation}")
        print(f"  → Mode: {result.recommended_mode.value}")
        print(f"  → Cost: ${cost_est['cost_usd']:.4f} "
              f"({cost_est['savings_pct']}% savings vs GLOBAL)")
        print(f"  Reasoning: {result.reasoning}")

    print("\n" + "-" * 80)
    print("Cost Comparison:")
    print("-" * 80)

    for mode in GraphRAGMode:
        cost_est = analyzer.get_cost_estimate(mode, baseline_tokens=10000)
        print(f"{mode.value:8} | "
              f"{cost_est['tokens']:5} tokens | "
              f"${cost_est['cost_usd']:.4f} | "
              f"{cost_est['savings_pct']:5.1f}% savings")

    print("\n" + "=" * 80)
    print("Query Complexity Analyzer test completed!")
    print("=" * 80)
