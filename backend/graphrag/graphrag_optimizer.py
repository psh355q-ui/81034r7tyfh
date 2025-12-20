"""
GraphRAG Optimizer with Dynamic Mode Selection.

This module optimizes GraphRAG queries by automatically selecting the best search mode
(LOCAL/GLOBAL/HYBRID) based on query complexity, achieving up to 77% token reduction.

Integration:
- Uses QueryComplexityAnalyzer for mode recommendation
- Wraps existing GraphRAG search engines
- Tracks cost savings metrics

Author: AI Trading System Team
Date: 2025-12-19
Phase: 1.4 - Cost Optimization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from backend.graphrag.query_complexity_analyzer import (
        QueryComplexityAnalyzer,
        GraphRAGMode,
        ComplexityScore
    )
except ImportError:
    from query_complexity_analyzer import (
        QueryComplexityAnalyzer,
        GraphRAGMode,
        ComplexityScore
    )


logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    query: str
    timestamp: datetime
    recommended_mode: str
    actual_mode: str
    complexity_score: float
    estimated_tokens: int
    estimated_cost_usd: float
    estimated_savings_pct: float
    response_time_ms: float
    success: bool


class GraphRAGOptimizer:
    """
    Optimizes GraphRAG queries with dynamic mode selection.

    Features:
    - Automatic mode selection based on query complexity
    - Cost tracking and savings metrics
    - Fallback handling (GLOBAL → HYBRID → LOCAL)
    - Query history logging
    - Performance monitoring

    Usage:
        optimizer = GraphRAGOptimizer(
            local_search_engine=local_engine,
            global_search_engine=global_engine
        )

        result = await optimizer.search(
            query="What is AAPL's P/E ratio?",
            force_mode=None  # Auto-detect
        )

        # Check savings
        print(optimizer.get_cost_summary())
    """

    def __init__(
        self,
        local_search_engine: Optional[Any] = None,
        global_search_engine: Optional[Any] = None,
        enable_auto_mode: bool = True
    ):
        """
        Initialize GraphRAG optimizer.

        Args:
            local_search_engine: GraphRAG local search instance
            global_search_engine: GraphRAG global search instance
            enable_auto_mode: Enable automatic mode selection (default: True)
        """
        self.local_search_engine = local_search_engine
        self.global_search_engine = global_search_engine
        self.enable_auto_mode = enable_auto_mode

        # Initialize complexity analyzer
        self.complexity_analyzer = QueryComplexityAnalyzer()

        # Metrics tracking
        self.query_history: List[QueryMetrics] = []
        self.total_queries = 0
        self.total_tokens_saved = 0
        self.total_cost_saved = 0.0

        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"GraphRAGOptimizer initialized (auto_mode={enable_auto_mode})"
        )

    async def search(
        self,
        query: str,
        force_mode: Optional[GraphRAGMode] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute optimized GraphRAG search.

        Args:
            query: Search query
            force_mode: Force specific mode (None = auto-detect)
            **kwargs: Additional arguments for search engines

        Returns:
            Dict with:
                - result: Search result
                - mode_used: Mode that was used
                - complexity: ComplexityScore
                - metrics: QueryMetrics
        """
        start_time = datetime.now()

        # Analyze query complexity
        complexity = self.complexity_analyzer.analyze(query)

        # Determine mode
        if force_mode:
            mode = force_mode
            self.logger.info(f"Using forced mode: {mode.value}")
        elif self.enable_auto_mode:
            mode = complexity.recommended_mode
            self.logger.info(
                f"Auto-selected mode: {mode.value} "
                f"(complexity={complexity.overall_score:.2f})"
            )
        else:
            # Default to GLOBAL if auto mode is disabled
            mode = GraphRAGMode.GLOBAL
            self.logger.info("Auto-mode disabled, using GLOBAL")

        # Execute search
        try:
            result = await self._execute_search(query, mode, **kwargs)
            success = True
        except Exception as e:
            self.logger.error(f"Search failed with {mode.value}: {e}")

            # Fallback strategy: GLOBAL → HYBRID → LOCAL
            result, mode = await self._fallback_search(query, mode, **kwargs)
            success = result is not None

        # Calculate metrics
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        cost_estimate = self.complexity_analyzer.get_cost_estimate(mode)

        # Record metrics
        metrics = QueryMetrics(
            query=query,
            timestamp=start_time,
            recommended_mode=complexity.recommended_mode.value,
            actual_mode=mode.value,
            complexity_score=complexity.overall_score,
            estimated_tokens=cost_estimate["tokens"],
            estimated_cost_usd=cost_estimate["cost_usd"],
            estimated_savings_pct=cost_estimate["savings_pct"],
            response_time_ms=response_time_ms,
            success=success
        )

        self._record_metrics(metrics)

        return {
            "result": result,
            "mode_used": mode.value,
            "complexity": asdict(complexity),
            "metrics": asdict(metrics)
        }

    async def _execute_search(
        self,
        query: str,
        mode: GraphRAGMode,
        **kwargs
    ) -> Any:
        """Execute search with specified mode."""
        if mode == GraphRAGMode.LOCAL:
            if not self.local_search_engine:
                raise RuntimeError("Local search engine not configured")
            return await self._local_search(query, **kwargs)

        elif mode == GraphRAGMode.GLOBAL:
            if not self.global_search_engine:
                raise RuntimeError("Global search engine not configured")
            return await self._global_search(query, **kwargs)

        elif mode == GraphRAGMode.HYBRID:
            # Hybrid: Run both and combine results
            return await self._hybrid_search(query, **kwargs)

        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def _local_search(self, query: str, **kwargs) -> Any:
        """Execute local search (entity-specific)."""
        self.logger.debug(f"Executing LOCAL search: {query}")

        # Call actual local search engine
        if hasattr(self.local_search_engine, 'search'):
            return await self.local_search_engine.search(query, **kwargs)
        elif hasattr(self.local_search_engine, 'query'):
            return await self.local_search_engine.query(query, **kwargs)
        else:
            # Mock implementation for testing
            return {
                "mode": "LOCAL",
                "query": query,
                "result": f"Local search result for: {query}",
                "entities": ["entity1", "entity2"]
            }

    async def _global_search(self, query: str, **kwargs) -> Any:
        """Execute global search (community summaries)."""
        self.logger.debug(f"Executing GLOBAL search: {query}")

        # Call actual global search engine
        if hasattr(self.global_search_engine, 'search'):
            return await self.global_search_engine.search(query, **kwargs)
        elif hasattr(self.global_search_engine, 'query'):
            return await self.global_search_engine.query(query, **kwargs)
        else:
            # Mock implementation for testing
            return {
                "mode": "GLOBAL",
                "query": query,
                "result": f"Global search result for: {query}",
                "communities": ["community1", "community2"]
            }

    async def _hybrid_search(self, query: str, **kwargs) -> Any:
        """Execute hybrid search (local + global)."""
        self.logger.debug(f"Executing HYBRID search: {query}")

        try:
            # Run both searches
            local_result = await self._local_search(query, **kwargs)
            global_result = await self._global_search(query, **kwargs)

            # Combine results
            return {
                "mode": "HYBRID",
                "query": query,
                "local": local_result,
                "global": global_result,
                "combined": self._combine_results(local_result, global_result)
            }
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {e}")
            # Fallback to global only
            return await self._global_search(query, **kwargs)

    def _combine_results(self, local: Any, global_: Any) -> str:
        """Combine local and global search results."""
        # Simple combination logic (can be customized)
        local_text = str(local.get("result", "")) if isinstance(local, dict) else str(local)
        global_text = str(global_.get("result", "")) if isinstance(global_, dict) else str(global_)

        return f"{local_text}\n\nContext: {global_text}"

    async def _fallback_search(
        self,
        query: str,
        failed_mode: GraphRAGMode,
        **kwargs
    ) -> tuple[Any, GraphRAGMode]:
        """
        Fallback strategy when primary mode fails.

        Fallback order: GLOBAL → HYBRID → LOCAL → None
        """
        self.logger.warning(f"Attempting fallback from {failed_mode.value}")

        fallback_order = {
            GraphRAGMode.GLOBAL: [GraphRAGMode.HYBRID, GraphRAGMode.LOCAL],
            GraphRAGMode.HYBRID: [GraphRAGMode.LOCAL, GraphRAGMode.GLOBAL],
            GraphRAGMode.LOCAL: [GraphRAGMode.HYBRID, GraphRAGMode.GLOBAL]
        }

        for fallback_mode in fallback_order.get(failed_mode, []):
            try:
                self.logger.info(f"Trying fallback mode: {fallback_mode.value}")
                result = await self._execute_search(query, fallback_mode, **kwargs)
                return result, fallback_mode
            except Exception as e:
                self.logger.error(f"Fallback {fallback_mode.value} failed: {e}")

        # All modes failed
        self.logger.error("All search modes failed")
        return None, failed_mode

    def _record_metrics(self, metrics: QueryMetrics):
        """Record query metrics for cost tracking."""
        self.query_history.append(metrics)
        self.total_queries += 1

        if metrics.success:
            # Calculate savings vs GLOBAL mode
            baseline_cost = self.complexity_analyzer.get_cost_estimate(
                GraphRAGMode.GLOBAL
            )
            cost_saved = baseline_cost["cost_usd"] - metrics.estimated_cost_usd
            tokens_saved = baseline_cost["tokens"] - metrics.estimated_tokens

            if cost_saved > 0:
                self.total_cost_saved += cost_saved
                self.total_tokens_saved += tokens_saved

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost optimization summary.

        Returns:
            Dict with cost metrics and savings statistics
        """
        if self.total_queries == 0:
            return {
                "total_queries": 0,
                "message": "No queries executed yet"
            }

        # Mode distribution
        mode_counts = {}
        for metrics in self.query_history:
            mode = metrics.actual_mode
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        # Success rate
        successful_queries = sum(1 for m in self.query_history if m.success)
        success_rate = (successful_queries / self.total_queries) * 100

        # Average metrics
        avg_complexity = sum(m.complexity_score for m in self.query_history) / self.total_queries
        avg_response_time = sum(m.response_time_ms for m in self.query_history) / self.total_queries

        # Cost breakdown
        total_estimated_cost = sum(m.estimated_cost_usd for m in self.query_history)
        baseline_cost_if_all_global = self.total_queries * 0.054  # $0.054 per GLOBAL query

        return {
            "total_queries": self.total_queries,
            "successful_queries": successful_queries,
            "success_rate_pct": round(success_rate, 1),
            "mode_distribution": mode_counts,
            "avg_complexity_score": round(avg_complexity, 2),
            "avg_response_time_ms": round(avg_response_time, 1),
            "cost_metrics": {
                "total_estimated_cost_usd": round(total_estimated_cost, 4),
                "baseline_cost_if_all_global_usd": round(baseline_cost_if_all_global, 4),
                "total_cost_saved_usd": round(self.total_cost_saved, 4),
                "total_tokens_saved": self.total_tokens_saved,
                "savings_percentage": round(
                    (self.total_cost_saved / baseline_cost_if_all_global * 100)
                    if baseline_cost_if_all_global > 0 else 0,
                    1
                )
            }
        }

    def get_query_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent query history.

        Args:
            limit: Max number of queries to return

        Returns:
            List of query metrics (most recent first)
        """
        return [
            asdict(m) for m in reversed(self.query_history[-limit:])
        ]

    def reset_metrics(self):
        """Reset all metrics."""
        self.query_history.clear()
        self.total_queries = 0
        self.total_tokens_saved = 0
        self.total_cost_saved = 0
        self.logger.info("Metrics reset")


# Example usage
if __name__ == "__main__":
    import asyncio

    print("=" * 80)
    print("GraphRAG Optimizer Test")
    print("=" * 80)
    print()

    async def test_optimizer():
        """Test the optimizer with mock queries."""
        # Initialize optimizer (no real engines for testing)
        optimizer = GraphRAGOptimizer(enable_auto_mode=True)

        # Test queries
        test_queries = [
            "What is AAPL's current price?",
            "Compare AAPL and MSFT",
            "Analyze the entire tech sector",
            "Show TSLA's P/E ratio",
            "What are overall market trends?",
            "Get NVDA risk factors",
            "Summarize all AI stocks",
            "Find AMZN's latest earnings"
        ]

        print("Executing test queries...")
        print("-" * 80)

        for query in test_queries:
            result = await optimizer.search(query)

            print(f"\nQuery: \"{query}\"")
            print(f"  Mode: {result['mode_used']}")
            print(f"  Complexity: {result['complexity']['overall_score']:.2f}")
            print(f"  Est. Cost: ${result['metrics']['estimated_cost_usd']:.4f}")
            print(f"  Savings: {result['metrics']['estimated_savings_pct']:.1f}%")
            print(f"  Response: {result['metrics']['response_time_ms']:.1f}ms")

        # Get summary
        print("\n" + "=" * 80)
        print("Cost Summary")
        print("=" * 80)

        summary = optimizer.get_cost_summary()
        print(f"\nTotal Queries: {summary['total_queries']}")
        print(f"Success Rate: {summary['success_rate_pct']}%")
        print(f"\nMode Distribution:")
        for mode, count in summary['mode_distribution'].items():
            pct = (count / summary['total_queries']) * 100
            print(f"  {mode}: {count} ({pct:.1f}%)")

        print(f"\nAvg Complexity: {summary['avg_complexity_score']:.2f}")
        print(f"Avg Response Time: {summary['avg_response_time_ms']:.1f}ms")

        cost = summary['cost_metrics']
        print(f"\nCost Analysis:")
        print(f"  Actual Cost: ${cost['total_estimated_cost_usd']:.4f}")
        print(f"  Baseline (all GLOBAL): ${cost['baseline_cost_if_all_global_usd']:.4f}")
        print(f"  Total Saved: ${cost['total_cost_saved_usd']:.4f}")
        print(f"  Tokens Saved: {cost['total_tokens_saved']:,}")
        print(f"  Savings: {cost['savings_percentage']:.1f}%")

        print("\n" + "=" * 80)
        print("GraphRAG Optimizer test completed!")
        print("=" * 80)

    # Run test
    asyncio.run(test_optimizer())
