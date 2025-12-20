"""
Supply Chain Risk Calculator for AI Trading System.

This module analyzes supply chain risk using recursive graph traversal:
- Direct operational risk
- Supplier concentration risk
- Customer concentration risk
- Geographic exposure risk

Cost: $0/month (no AI, rule-based analysis)
Update frequency: Monthly (30 days)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class SupplyChainRiskCalculator:
    """
    Calculate supply chain risk score (0.0-1.0) using recursive analysis.

    Scoring factors:
    - Direct Operational Risk (40%): Company's own operational risk
    - Supplier Risk (35%): Weighted risk from key suppliers
    - Customer Concentration (15%): Revenue concentration risk
    - Geographic Risk (10%): Geographic diversification

    Max recursion depth: 3 levels
    Update frequency: Monthly (30 days)
    """

    def __init__(self):
        """Initialize calculator with cache."""
        # In-memory cache for risk scores (30-day TTL)
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(days=30)

        # Metrics tracking
        self.total_calculations = 0
        self.cache_hits = 0
        self.max_depth_reached = 0

        # Supply chain data (mock data - in production, fetch from Bloomberg/FactSet)
        self._supply_chain_data = self._load_supply_chain_data()

    def calculate_risk(
        self,
        ticker: str,
        depth: int = 0,
        max_depth: int = 3,
        visited: Optional[Set[str]] = None,
    ) -> Dict:
        """
        Calculate supply chain risk with recursive analysis.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            visited: Set of already visited tickers (prevents cycles)

        Returns:
            {
                "score": 0.0-1.0 (overall risk, higher = more risk),
                "confidence": "high" | "medium" | "low",
                "components": {
                    "direct_risk": 0.0-1.0,
                    "supplier_risk": 0.0-1.0,
                    "customer_risk": 0.0-1.0,
                    "geographic_risk": 0.0-1.0
                },
                "details": {
                    "suppliers": list,
                    "customers": list,
                    "geographic_exposure": dict,
                    "max_depth_reached": int
                },
                "last_updated": str (ISO format),
                "ttl_days": 30
            }
        """
        # Initialize visited set
        if visited is None:
            visited = set()

        # Prevent circular dependencies
        if ticker in visited:
            logger.debug(f"Circular dependency detected: {ticker}")
            return self._default_risk_score(ticker)

        visited.add(ticker)

        # Check cache first
        cached = self._get_from_cache(ticker)
        if cached and depth == 0:  # Only use cache at top level
            self.cache_hits += 1
            logger.info(f"Cache hit for {ticker}")
            return cached

        # Track metrics
        self.total_calculations += 1
        self.max_depth_reached = max(self.max_depth_reached, depth)

        logger.info(f"Calculating supply chain risk for {ticker} (depth={depth})")

        try:
            # Get supply chain data
            chain_data = self._supply_chain_data.get(ticker, {})

            # 1. Direct operational risk
            direct_risk = self._calculate_direct_risk(ticker, chain_data)

            # 2. Supplier risk (recursive)
            supplier_risk = 0.0
            if depth < max_depth:
                supplier_risk = self._calculate_supplier_risk(
                    ticker, chain_data, depth, max_depth, visited.copy()
                )
            else:
                # At max depth, use simple average
                suppliers = chain_data.get("suppliers", [])
                if suppliers:
                    supplier_risk = sum(s.get("risk", 0.5) for s in suppliers) / len(suppliers)

            # 3. Customer concentration risk
            customer_risk = self._calculate_customer_risk(ticker, chain_data)

            # 4. Geographic risk
            geographic_risk = self._calculate_geographic_risk(ticker, chain_data)

            # Weighted total score
            total_score = (
                direct_risk * 0.40 +
                supplier_risk * 0.35 +
                customer_risk * 0.15 +
                geographic_risk * 0.10
            )

            # Confidence assessment
            confidence = self._assess_confidence(chain_data)

            result = {
                "score": round(total_score, 4),
                "confidence": confidence,
                "components": {
                    "direct_risk": round(direct_risk, 4),
                    "supplier_risk": round(supplier_risk, 4),
                    "customer_risk": round(customer_risk, 4),
                    "geographic_risk": round(geographic_risk, 4),
                },
                "details": {
                    "suppliers": chain_data.get("suppliers", []),
                    "customers": chain_data.get("customers", []),
                    "geographic_exposure": chain_data.get("geographic_exposure", {}),
                    "max_depth_reached": depth,
                },
                "last_updated": datetime.now().isoformat(),
                "ttl_days": 30,
            }

            # Cache result (only at top level)
            if depth == 0:
                self._add_to_cache(ticker, result)

            logger.info(
                f"Supply chain risk for {ticker}: {result['score']:.4f} "
                f"(confidence: {result['confidence']}, depth: {depth})"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating supply chain risk for {ticker}: {e}")
            return self._default_risk_score(ticker)

    def _calculate_direct_risk(self, ticker: str, chain_data: dict) -> float:
        """
        Calculate direct operational risk (0.0-1.0).

        Based on:
        - Industry sector risk
        - Company size (market cap)
        - Operational complexity
        """
        # Use mock data or default
        return chain_data.get("direct_risk", 0.5)

    def _calculate_supplier_risk(
        self,
        ticker: str,
        chain_data: dict,
        depth: int,
        max_depth: int,
        visited: Set[str],
    ) -> float:
        """
        Calculate supplier risk recursively (0.0-1.0).

        Risk = weighted average of supplier risks * dependency factors
        """
        suppliers = chain_data.get("suppliers", [])

        if not suppliers:
            return 0.3  # Low risk if no supplier concentration

        total_risk = 0.0
        total_weight = 0.0

        for supplier in suppliers:
            supplier_ticker = supplier.get("ticker")
            dependency = supplier.get("dependency", 0.0)  # 0.0-1.0

            if not supplier_ticker:
                continue

            # Recursive call to get supplier's risk
            if depth + 1 < max_depth and supplier_ticker not in visited:
                supplier_result = self.calculate_risk(
                    supplier_ticker,
                    depth=depth + 1,
                    max_depth=max_depth,
                    visited=visited.copy()
                )
                supplier_risk = supplier_result["score"]
            else:
                # At max depth or already visited, use stored risk
                supplier_risk = supplier.get("risk", 0.5)

            # Weight by dependency
            total_risk += supplier_risk * dependency
            total_weight += dependency

        # Normalize by total weight
        if total_weight > 0:
            return total_risk / total_weight
        else:
            return 0.3  # Default low risk

    def _calculate_customer_risk(self, ticker: str, chain_data: dict) -> float:
        """
        Calculate customer concentration risk (0.0-1.0).

        High concentration = high risk (if key customer leaves)
        """
        customers = chain_data.get("customers", [])

        if not customers:
            return 0.3  # Low risk if diversified

        # Calculate Herfindahl index for concentration
        total_share = sum(c.get("revenue_share", 0.0) for c in customers)

        if total_share > 0:
            herfindahl = sum(
                (c.get("revenue_share", 0.0) / total_share) ** 2
                for c in customers
            )

            # Normalize: HHI of 1.0 = max risk, HHI of 0.1 = low risk
            return min(herfindahl, 1.0)
        else:
            return 0.3

    def _calculate_geographic_risk(self, ticker: str, chain_data: dict) -> float:
        """
        Calculate geographic diversification risk (0.0-1.0).

        High exposure to risky regions = high risk
        """
        geo_exposure = chain_data.get("geographic_exposure", {})

        if not geo_exposure:
            return 0.5  # Medium risk if no data

        # Risk weights for regions
        region_risk = {
            "North America": 0.2,
            "Europe": 0.3,
            "China": 0.7,
            "Asia (ex-China)": 0.5,
            "Rest of World": 0.6,
        }

        # Weighted average risk
        total_risk = 0.0
        total_exposure = 0.0

        for region, exposure in geo_exposure.items():
            risk = region_risk.get(region, 0.5)
            total_risk += risk * exposure
            total_exposure += exposure

        if total_exposure > 0:
            return total_risk / total_exposure
        else:
            return 0.5

    def _assess_confidence(self, chain_data: dict) -> str:
        """Assess confidence level based on data availability."""
        has_suppliers = bool(chain_data.get("suppliers"))
        has_customers = bool(chain_data.get("customers"))
        has_geo = bool(chain_data.get("geographic_exposure"))

        data_points = sum([has_suppliers, has_customers, has_geo])

        if data_points >= 3:
            return "high"
        elif data_points >= 2:
            return "medium"
        else:
            return "low"

    def _default_risk_score(self, ticker: str) -> Dict:
        """Return default neutral risk score."""
        return {
            "score": 0.5,
            "confidence": "low",
            "components": {
                "direct_risk": 0.5,
                "supplier_risk": 0.5,
                "customer_risk": 0.5,
                "geographic_risk": 0.5,
            },
            "details": {},
            "last_updated": datetime.now().isoformat(),
            "ttl_days": 30,
        }

    def _get_from_cache(self, ticker: str) -> Optional[Dict]:
        """Get cached risk score if not expired."""
        if ticker not in self._cache:
            return None

        cached = self._cache[ticker]
        last_updated = datetime.fromisoformat(cached["last_updated"])

        if datetime.now() - last_updated < self._cache_ttl:
            return cached
        else:
            # Expired, remove from cache
            del self._cache[ticker]
            return None

    def _add_to_cache(self, ticker: str, result: Dict) -> None:
        """Add result to cache."""
        self._cache[ticker] = result

    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_metrics(self) -> Dict:
        """Get calculation metrics."""
        return {
            "total_calculations": self.total_calculations,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": (
                self.cache_hits / self.total_calculations
                if self.total_calculations > 0
                else 0.0
            ),
            "max_depth_reached": self.max_depth_reached,
            "cache_size": len(self._cache),
        }

    def _load_supply_chain_data(self) -> Dict:
        """
        Load supply chain data (mock data for now).

        In production, this would fetch from:
        - Bloomberg supply chain database
        - FactSet SupplyChain Relationships
        - SEC 10-K filings (customer/supplier disclosures)
        """
        return {
            "AAPL": {
                "direct_risk": 0.3,
                "suppliers": [
                    {"ticker": "TSMC", "dependency": 0.7, "risk": 0.4},
                    {"ticker": "FOXCONN", "dependency": 0.5, "risk": 0.5},
                    {"ticker": "QCOM", "dependency": 0.3, "risk": 0.35},
                ],
                "customers": [
                    {"name": "Direct Sales", "revenue_share": 0.7},
                    {"name": "Carriers", "revenue_share": 0.2},
                    {"name": "Retail Partners", "revenue_share": 0.1},
                ],
                "geographic_exposure": {
                    "North America": 0.4,
                    "Europe": 0.25,
                    "China": 0.2,
                    "Asia (ex-China)": 0.15,
                },
            },
            "TSLA": {
                "direct_risk": 0.6,
                "suppliers": [
                    {"ticker": "PANA", "dependency": 0.8, "risk": 0.5},
                    {"ticker": "LG", "dependency": 0.6, "risk": 0.45},
                    {"ticker": "CATL", "dependency": 0.7, "risk": 0.55},
                ],
                "customers": [
                    {"name": "Direct Sales", "revenue_share": 1.0},
                ],
                "geographic_exposure": {
                    "North America": 0.5,
                    "Europe": 0.2,
                    "China": 0.3,
                },
            },
            "NVDA": {
                "direct_risk": 0.35,
                "suppliers": [
                    {"ticker": "TSMC", "dependency": 0.9, "risk": 0.4},
                ],
                "customers": [
                    {"name": "Cloud Providers", "revenue_share": 0.6},
                    {"name": "Enterprises", "revenue_share": 0.25},
                    {"name": "Gaming", "revenue_share": 0.15},
                ],
                "geographic_exposure": {
                    "North America": 0.5,
                    "Europe": 0.2,
                    "China": 0.15,
                    "Asia (ex-China)": 0.15,
                },
            },
            "TSMC": {
                "direct_risk": 0.4,
                "suppliers": [
                    {"ticker": "ASML", "dependency": 0.8, "risk": 0.35},
                ],
                "customers": [
                    {"name": "Apple", "revenue_share": 0.25},
                    {"name": "NVIDIA", "revenue_share": 0.15},
                    {"name": "AMD", "revenue_share": 0.1},
                    {"name": "Other", "revenue_share": 0.5},
                ],
                "geographic_exposure": {
                    "Asia (ex-China)": 0.9,
                    "North America": 0.05,
                    "Europe": 0.05,
                },
            },
            "ASML": {
                "direct_risk": 0.35,
                "suppliers": [],
                "customers": [
                    {"name": "TSMC", "revenue_share": 0.3},
                    {"name": "Samsung", "revenue_share": 0.2},
                    {"name": "Intel", "revenue_share": 0.15},
                    {"name": "Other", "revenue_share": 0.35},
                ],
                "geographic_exposure": {
                    "Europe": 0.3,
                    "Asia (ex-China)": 0.5,
                    "North America": 0.1,
                    "China": 0.1,
                },
            },
        }
