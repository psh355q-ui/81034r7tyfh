"""
FactChecker Component - LLM Hallucination Prevention

Market Intelligence v2.0 - Phase 1, T1.3

This component validates LLM-extracted data against external sources (YFinance, SEC, FRED)
to prevent hallucinations and ensure data accuracy.

Key Features:
1. Earnings data verification against YFinance
2. Economic indicator verification against FRED
3. Policy number verification against SEC Edgar
4. Confidence adjustment based on verification results

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class FactVerificationStatus(Enum):
    """Fact verification status"""
    VERIFIED = "VERIFIED"           # Data matches external source
    DISCREPANCY = "DISCREPANCY"     # Data differs but within tolerance
    HALLUCINATION = "HALLUCINATION" # Data completely wrong or not found
    PENDING = "PENDING"             # Verification in progress
    ERROR = "ERROR"                 # Verification error


@dataclass
class FactCheckResult:
    """
    Result of fact verification

    Attributes:
        verified: Whether the fact was verified
        data_type: Type of data verified (earnings, economic_indicator, policy)
        extracted_value: Value extracted by LLM
        actual_value: Actual value from external source
        diff_percentage: Percentage difference
        reasoning: Explanation of verification result
        confidence_adjustment: Recommended confidence adjustment
    """
    verified: bool
    data_type: str
    extracted_value: float
    actual_value: Optional[float]
    diff_percentage: Optional[float]
    reasoning: str = ""
    confidence_adjustment: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "verified": self.verified,
            "data_type": self.data_type,
            "extracted_value": self.extracted_value,
            "actual_value": self.actual_value,
            "diff_percentage": self.diff_percentage,
            "reasoning": self.reasoning,
            "confidence_adjustment": self.confidence_adjustment,
        }


# ============================================================================
# Main Component
# ============================================================================

class FactChecker(BaseIntelligence):
    """
    Fact Checker

    Validates LLM-extracted data against external sources to prevent hallucinations.

    Supported Data Types:
    1. Earnings data (revenue, EPS) - verified against YFinance
    2. Economic indicators (Fed funds rate, unemployment, CPI) - verified against FRED
    3. Policy numbers (allocated amounts) - verified against SEC Edgar

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.fact_checker import FactChecker

        llm = get_llm_provider()
        checker = FactChecker(
            llm_provider=llm,
            yfinance_client=yfinance_client,
            sec_client=sec_client,
            fred_client=fred_client,
        )

        # Verify earnings data
        result = await checker.verify_earnings({
            "ticker": "NVDA",
            "revenue": 61.0,
            "eps": 3.25,
        })

        if result.verified:
            print("Earnings data verified!")
        else:
            print(f"Discrepancy: {result.diff_percentage:.1%}")
    """

    # Default tolerances
    DEFAULT_EARNINGS_TOLERANCE = 0.05  # 5%
    DEFAULT_ECONOMIC_TOLERANCE = 0.02  # 2%
    DEFAULT_POLICY_TOLERANCE = 0.05    # 5%

    def __init__(
        self,
        llm_provider: LLMProvider,
        yfinance_client: Optional[Any] = None,
        sec_client: Optional[Any] = None,
        fred_client: Optional[Any] = None,
    ):
        """
        Initialize FactChecker

        Args:
            llm_provider: LLM Provider instance
            yfinance_client: YFinance API client (optional)
            sec_client: SEC Edgar API client (optional)
            fred_client: FRED API client (optional)
        """
        super().__init__(
            name="FactChecker",
            phase=IntelligencePhase.P0,
        )

        self.llm = llm_provider
        self.yfinance_client = yfinance_client
        self.sec_client = sec_client
        self.fred_client = fred_client

        # Verification statistics
        self._verification_count = 0
        self._hallucination_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze and verify data (main entry point)

        Args:
            data: Data to verify with extracted facts

        Returns:
            IntelligenceResult: Verification result
        """
        return await self.verify_intelligence_result(data)

    async def verify_intelligence_result(
        self,
        intelligence_result: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Verify data from intelligence components

        Args:
            intelligence_result: Result from intelligence component with extracted facts

        Returns:
            IntelligenceResult: Verification result with adjusted confidence
        """
        try:
            # Extract facts from intelligence result
            extracted_data = intelligence_result.get("extracted_data", {})
            original_confidence = intelligence_result.get("confidence", 0.7)

            if not extracted_data:
                return self.create_result(
                    success=True,
                    data={
                        "stage": "fact_check",
                        "verification_status": "SKIPPED",
                        "reason": "No data to verify",
                        "adjusted_confidence": original_confidence,
                    },
                    confidence=original_confidence,
                    reasoning="No data to verify",
                )

            # Detect data type and verify
            data_type = self._detect_data_type(extracted_data)
            verify_result = await self._verify_by_type(extracted_data, data_type)

            # Adjust confidence based on verification
            adjusted_confidence = self._adjust_confidence(
                original_confidence,
                verify_result,
            )

            # Update statistics
            self._verification_count += 1
            if not verify_result.verified:
                self._hallucination_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "fact_check",
                    "verification_status": "VERIFIED" if verify_result.verified else "HALLUCINATION",
                    "data_type": data_type,
                    "verified": verify_result.verified,
                    "adjusted_confidence": adjusted_confidence,
                    "confidence_adjustment": adjusted_confidence - original_confidence,
                    "fact_check": verify_result.to_dict(),
                },
                confidence=adjusted_confidence,
                reasoning=verify_result.reasoning,
            )

        except Exception as e:
            logger.error(f"Fact check error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "fact_check"},
            )
            result.add_error(f"Verification error: {str(e)}")
            return result

    async def verify_earnings(
        self,
        extracted_data: Dict[str, Any],
        tolerance: Optional[float] = None,
    ) -> FactCheckResult:
        """
        Verify earnings data against YFinance

        Args:
            extracted_data: Extracted earnings data with 'ticker' and 'revenue'/'eps'
            tolerance: Allowed tolerance (default: DEFAULT_EARNINGS_TOLERANCE)

        Returns:
            FactCheckResult: Verification result
        """
        tolerance = tolerance or self.DEFAULT_EARNINGS_TOLERANCE

        try:
            ticker = extracted_data.get("ticker")
            if not ticker:
                return FactCheckResult(
                    verified=False,
                    data_type="earnings",
                    extracted_value=0.0,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="Missing ticker symbol",
                )

            # Get actual data from YFinance
            if self.yfinance_client is None:
                return FactCheckResult(
                    verified=False,
                    data_type="earnings",
                    extracted_value=extracted_data.get("revenue", 0.0),
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="YFinance client not configured",
                )

            actual_data = await self.yfinance_client.get_latest_earnings(ticker)
            if actual_data is None:
                return FactCheckResult(
                    verified=False,
                    data_type="earnings",
                    extracted_value=extracted_data.get("revenue", 0.0),
                    actual_value=None,
                    diff_percentage=None,
                    reasoning=f"No earnings data found for {ticker}",
                )

            # Compare revenue
            extracted_revenue = extracted_data.get("revenue", 0.0)
            actual_revenue = actual_data.get("revenue")

            if actual_revenue is None or actual_revenue == 0:
                return FactCheckResult(
                    verified=False,
                    data_type="earnings",
                    extracted_value=extracted_revenue,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="No revenue data available",
                )

            diff_pct = abs(extracted_revenue - actual_revenue) / actual_revenue
            verified = diff_pct <= tolerance

            return FactCheckResult(
                verified=verified,
                data_type="earnings",
                extracted_value=extracted_revenue,
                actual_value=actual_revenue,
                diff_percentage=diff_pct,
                reasoning=f"Revenue {extracted_revenue} vs actual {actual_revenue} ({diff_pct:.1%} diff)",
                confidence_adjustment=self._calculate_confidence_adjustment(verified, diff_pct),
            )

        except Exception as e:
            logger.error(f"Earnings verification error: {e}")
            return FactCheckResult(
                verified=False,
                data_type="earnings",
                extracted_value=extracted_data.get("revenue", 0.0),
                actual_value=None,
                diff_percentage=None,
                reasoning=f"Verification error: {str(e)}",
            )

    async def verify_economic_indicator(
        self,
        extracted_data: Dict[str, Any],
        tolerance: Optional[float] = None,
    ) -> FactCheckResult:
        """
        Verify economic indicator against FRED

        Args:
            extracted_data: Extracted indicator data with 'indicator_name' and 'value'
            tolerance: Allowed tolerance (default: DEFAULT_ECONOMIC_TOLERANCE)

        Returns:
            FactCheckResult: Verification result
        """
        tolerance = tolerance or self.DEFAULT_ECONOMIC_TOLERANCE

        try:
            indicator_name = extracted_data.get("indicator_name")
            extracted_value = extracted_data.get("value")

            if not indicator_name or extracted_value is None:
                return FactCheckResult(
                    verified=False,
                    data_type="economic_indicator",
                    extracted_value=extracted_value or 0.0,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="Missing indicator name or value",
                )

            # Get actual data from FRED
            if self.fred_client is None:
                return FactCheckResult(
                    verified=False,
                    data_type="economic_indicator",
                    extracted_value=extracted_value,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="FRED client not configured",
                )

            actual_value = await self.fred_client.get_latest_value(indicator_name)
            if actual_value is None:
                # Try verification method
                verify_result = await self.fred_client.verify_economic_indicator(
                    indicator_name,
                    extracted_value,
                    tolerance,
                )
                if verify_result:
                    return FactCheckResult(
                        verified=verify_result.get("verified", False),
                        data_type="economic_indicator",
                        extracted_value=extracted_value,
                        actual_value=verify_result.get("actual"),
                        diff_percentage=verify_result.get("diff_pct"),
                        reasoning=verify_result.get("reason", ""),
                    )

                return FactCheckResult(
                    verified=False,
                    data_type="economic_indicator",
                    extracted_value=extracted_value,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning=f"No data found for {indicator_name}",
                )

            # Compare values
            diff_pct = abs(extracted_value - actual_value) / actual_value if actual_value != 0 else 0
            verified = diff_pct <= tolerance

            return FactCheckResult(
                verified=verified,
                data_type="economic_indicator",
                extracted_value=extracted_value,
                actual_value=actual_value,
                diff_percentage=diff_pct,
                reasoning=f"{indicator_name}: {extracted_value} vs actual {actual_value} ({diff_pct:.1%} diff)",
                confidence_adjustment=self._calculate_confidence_adjustment(verified, diff_pct),
            )

        except Exception as e:
            logger.error(f"Economic indicator verification error: {e}")
            return FactCheckResult(
                verified=False,
                data_type="economic_indicator",
                extracted_value=extracted_data.get("value", 0.0),
                actual_value=None,
                diff_percentage=None,
                reasoning=f"Verification error: {str(e)}",
            )

    async def verify_policy(
        self,
        extracted_data: Dict[str, Any],
        tolerance: Optional[float] = None,
    ) -> FactCheckResult:
        """
        Verify policy number against SEC Edgar

        Args:
            extracted_data: Extracted policy data with 'policy_name' and 'allocated_amount'
            tolerance: Allowed tolerance (default: DEFAULT_POLICY_TOLERANCE)

        Returns:
            FactCheckResult: Verification result
        """
        tolerance = tolerance or self.DEFAULT_POLICY_TOLERANCE

        try:
            policy_name = extracted_data.get("policy_name")
            extracted_amount = extracted_data.get("allocated_amount")

            if not policy_name or extracted_amount is None:
                return FactCheckResult(
                    verified=False,
                    data_type="policy",
                    extracted_value=extracted_amount or 0.0,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="Missing policy name or amount",
                )

            # Get actual data from SEC
            if self.sec_client is None:
                return FactCheckResult(
                    verified=False,
                    data_type="policy",
                    extracted_value=extracted_amount,
                    actual_value=None,
                    diff_percentage=None,
                    reasoning="SEC client not configured",
                )

            # Try verification method
            verify_result = await self.sec_client.verify_policy_number(
                policy_name,
                extracted_amount,
                tolerance,
            )

            if verify_result:
                return FactCheckResult(
                    verified=verify_result.get("verified", False),
                    data_type="policy",
                    extracted_value=extracted_amount,
                    actual_value=verify_result.get("actual"),
                    diff_percentage=verify_result.get("diff_pct"),
                    reasoning=verify_result.get("reason", ""),
                    confidence_adjustment=self._calculate_confidence_adjustment(
                        verify_result.get("verified", False),
                        verify_result.get("diff_pct", 0),
                    ),
                )

            return FactCheckResult(
                verified=False,
                data_type="policy",
                extracted_value=extracted_amount,
                actual_value=None,
                diff_percentage=None,
                reasoning=f"No data found for {policy_name}",
            )

        except Exception as e:
            logger.error(f"Policy verification error: {e}")
            return FactCheckResult(
                verified=False,
                data_type="policy",
                extracted_value=extracted_data.get("allocated_amount", 0.0),
                actual_value=None,
                diff_percentage=None,
                reasoning=f"Verification error: {str(e)}",
            )

    async def batch_verify(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[FactCheckResult]:
        """
        Verify multiple facts in batch

        Args:
            facts: List of facts to verify

        Returns:
            List[FactCheckResult]: Verification results
        """
        results = []
        for fact in facts:
            data_type = self._detect_data_type(fact)
            result = await self._verify_by_type(fact, data_type)
            results.append(result)
        return results

    def _detect_data_type(self, data: Dict[str, Any]) -> str:
        """Detect the type of data to verify"""
        if "ticker" in data and ("revenue" in data or "eps" in data):
            return "earnings"
        elif "indicator_name" in data and "value" in data:
            return "economic_indicator"
        elif "policy_name" in data and "allocated_amount" in data:
            return "policy"
        else:
            return "unknown"

    async def _verify_by_type(
        self,
        data: Dict[str, Any],
        data_type: str,
    ) -> FactCheckResult:
        """Route verification to appropriate method"""
        if data_type == "earnings":
            return await self.verify_earnings(data)
        elif data_type == "economic_indicator":
            return await self.verify_economic_indicator(data)
        elif data_type == "policy":
            return await self.verify_policy(data)
        else:
            return FactCheckResult(
                verified=False,
                data_type="unknown",
                extracted_value=0.0,
                actual_value=None,
                diff_percentage=None,
                reasoning="Unknown data type",
            )

    def _calculate_confidence_adjustment(
        self,
        verified: bool,
        diff_percentage: float,
    ) -> float:
        """Calculate confidence adjustment based on verification result"""
        if verified:
            # Boost confidence for verified facts
            # Smaller discrepancy = larger boost
            boost = 0.1 * (1.0 - min(diff_percentage, 0.1) / 0.1)
            return boost
        else:
            # Penalize confidence for failed verification
            # Larger discrepancy = larger penalty
            penalty = -0.2 * min(diff_percentage, 0.5) / 0.5
            return penalty

    def _adjust_confidence(
        self,
        original_confidence: float,
        verify_result: FactCheckResult,
    ) -> float:
        """Adjust confidence based on verification result"""
        adjustment = verify_result.confidence_adjustment
        adjusted = original_confidence + adjustment

        # Clamp to [0, 1]
        return max(0.0, min(1.0, adjusted))

    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics"""
        hallucination_rate = (
            self._hallucination_count / self._verification_count
            if self._verification_count > 0
            else 0
        )

        return {
            "total_verifications": self._verification_count,
            "hallucinations_detected": self._hallucination_count,
            "hallucination_rate": round(hallucination_rate, 3),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_fact_checker(
    llm_provider: Optional[LLMProvider] = None,
    yfinance_client: Optional[Any] = None,
    sec_client: Optional[Any] = None,
    fred_client: Optional[Any] = None,
) -> FactChecker:
    """
    Create FactChecker instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        yfinance_client: YFinance API client (optional)
        sec_client: SEC Edgar API client (optional)
        fred_client: FRED API client (optional)

    Returns:
        FactChecker: Configured checker instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return FactChecker(
        llm_provider=llm_provider,
        yfinance_client=yfinance_client,
        sec_client=sec_client,
        fred_client=fred_client,
    )
