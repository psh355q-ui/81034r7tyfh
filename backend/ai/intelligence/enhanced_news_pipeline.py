"""
Enhanced News Processing Pipeline Component

Market Intelligence v2.0 - Phase 4, T4.3

This component integrates all intelligence components into a unified workflow
that processes news articles through multiple analysis stages and generates
comprehensive insights with forced contrarian view analysis.

Key Features:
1. Full pipeline integration (Filter → Intelligence → Narrative → FactCheck → MarketConfirm → Horizon → Policy → Insight)
2. Each stage mockable for independent testing
3. Contrarian view forced display (contrarian_view, invalidation_conditions, failure_triggers)
4. End-to-end integration with error handling

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class PipelineStage(Enum):
    """Pipeline processing stages"""
    FILTER = "filter"                      # Stage 1: News filtering
    NARRATIVE = "narrative"                # Stage 2: Narrative analysis
    FACT_CHECK = "fact_check"              # Stage 3: Fact verification
    MARKET_CONFIRM = "market_confirm"      # Stage 4: Market confirmation
    HORIZON = "horizon"                    # Stage 5: Horizon tagging
    POLICY = "policy"                      # Stage 6: Policy analysis
    FINAL_INSIGHT = "final_insight"        # Final: Comprehensive insight


@dataclass
class ContrarianView:
    """
    Contrarian view analysis

    Attributes:
        bull_case: Bullish scenario and contrarian position
        bear_case: Bearish scenario and contrarian position
        key_risks: Key risks to watch
        confidence: Confidence in contrarian view (0-1)
    """
    bull_case: Optional[str]
    bear_case: Optional[str]
    key_risks: List[str] = field(default_factory=list)
    confidence: float = 0.75

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_risks": self.key_risks,
            "confidence": self.confidence,
        }


@dataclass
class PipelineResult:
    """
    Result of pipeline processing

    Attributes:
        success: Whether pipeline completed successfully
        stages: Results from each stage
        final_insight: Final generated insight
        contrarian_view: Forced contrarian analysis
        invalidation_conditions: Conditions that could invalidate the thesis
        failure_triggers: Events that would signal failure
        processing_time_ms: Total processing time
    """
    success: bool
    stages: Dict[str, IntelligenceResult]
    final_insight: Optional[str]
    contrarian_view: Optional[ContrarianView]
    invalidation_conditions: List[str] = field(default_factory=list)
    failure_triggers: List[str] = field(default_factory=list)
    processing_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "stages": {k: v.to_dict() if hasattr(v, "to_dict") else v.data for k, v in self.stages.items()},
            "final_insight": self.final_insight,
            "contrarian_view": self.contrarian_view.to_dict() if self.contrarian_view else None,
            "invalidation_conditions": self.invalidation_conditions,
            "failure_triggers": self.failure_triggers,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================================
# Main Component
# ============================================================================

class EnhancedNewsProcessingPipeline(BaseIntelligence):
    """
    Enhanced News Processing Pipeline

    Integrates all intelligence components into a unified workflow that processes
    news articles through multiple analysis stages, generating comprehensive insights
    with forced contrarian view analysis.

    Key Features:
    1. Stage-by-stage processing with error handling
    2. Each stage independently mockable
    3. Forced contrarian view display
    4. Invalidation condition identification
    5. Failure trigger detection

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsProcessingPipeline

        llm = get_llm_provider()
        pipeline = EnhancedNewsProcessingPipeline(
            llm_provider=llm,
            intelligence_components={...},
        )

        # Process a news article
        result = await pipeline.process_article(article)

        if result.data["contrarian_view"]["bear_case"]:
            print("Contrarian view suggests caution")
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        intelligence_components: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Enhanced News Processing Pipeline

        Args:
            llm_provider: LLM Provider instance
            intelligence_components: Dictionary of intelligence components
        """
        super().__init__(
            name="EnhancedNewsProcessingPipeline",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self._components = intelligence_components or {}

        # Statistics
        self._processed_count = 0
        self._early_termination_count = 0
        self._component_failures = {}

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Process article through pipeline (main entry point)

        Args:
            data: Article data with title, content, etc.

        Returns:
            IntelligenceResult: Pipeline processing result
        """
        article = data.get("article", {})
        return await self.process_article(article)

    async def process_article(
        self,
        article: Dict[str, Any],
    ) -> PipelineResult:
        """
        Process a news article through the complete pipeline

        Args:
            article: Article data with title, content, source, published_at

        Returns:
            PipelineResult: Complete pipeline result with all stages
        """
        start_time = datetime.now()

        # Validate article
        if not article or not article.get("title"):
            return self._create_error_result("Article title is required", article)

        stages = {}
        invalidation_conditions = []
        failure_triggers = []

        try:
            # Stage 1: Filter (early exit if not relevant)
            filter_result = await self._stage1_filter(article)
            stages["filter"] = filter_result

            if not filter_result.success or not filter_result.data.get("is_relevant", True):
                self._early_termination_count += 1
                return self._create_result(
                    stages=stages,
                    final_insight="Article filtered out as irrelevant",
                    processing_time_ms=self._calculate_time(start_time),
                )

            # Stage 2: Narrative Analysis
            narrative_result = await self._stage2_narrative(article)
            stages["narrative"] = narrative_result

            # Stage 3: Fact Check
            fact_check_result = await self._stage3_fact_check(article)
            stages["fact_check"] = fact_check_result

            # Check for fact check failures
            if not fact_check_result.success or fact_check_result.data.get("verification_status") == "HALLUCINATION":
                failure_triggers.append("Fact verification failed - potential hallucination")

            # Stage 4: Market Confirmation
            narrative_data = narrative_result.data.copy()
            market_confirm_result = await self._stage4_market_confirm(narrative_data)
            stages["market_confirm"] = market_confirm_result

            # Check for market invalidation
            if market_confirm_result.data.get("confirmation_status") == "CONTRADICTED":
                invalidation_conditions.append("Price action contradicts narrative")

            # Stage 5: Horizon Tagging
            insight_data = {**narrative_data, **market_confirm_result.data}
            horizon_result = await self._stage5_horizon_tagging(insight_data)
            stages["horizon"] = horizon_result

            # Stage 6: Policy Analysis
            policy_result = await self._stage6_policy_analysis(insight_data)
            stages["policy"] = policy_result

            # Generate final insight
            final_insight = await self._generate_final_insight(stages)

            # Generate contrarian view
            contrarian_view = await self._generate_contrarian_view(stages)

            # Identify invalidation conditions
            conditions = self._identify_invalidation_conditions(stages)
            invalidation_conditions.extend(conditions)

            # Identify failure triggers
            triggers = self._identify_failure_triggers(stages)
            failure_triggers.extend(triggers)

            self._processed_count += 1

            return self._create_result(
                success=True,
                stages=stages,
                final_insight=final_insight,
                contrarian_view=contrarian_view,
                invalidation_conditions=invalidation_conditions,
                failure_triggers=failure_triggers,
                processing_time_ms=self._calculate_time(start_time),
            )

        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            return self._create_error_result(
                f"Pipeline error: {str(e)}",
                stages=stages,
                processing_time_ms=self._calculate_time(start_time),
            )

    async def _stage1_filter(self, article: Dict[str, Any]) -> IntelligenceResult:
        """Stage 1: News filtering"""
        component = self._components.get("news_filter")
        if component and hasattr(component, "filter_news"):
            return await component.filter_news(article)

        # Default: accept all articles
        return self.create_result(
            success=True,
            data={"is_relevant": True, "stage": "filter"},
            reasoning="No filter component, article accepted by default",
        )

    async def _stage2_narrative(self, article: Dict[str, Any]) -> IntelligenceResult:
        """Stage 2: Narrative analysis"""
        component = self._components.get("narrative_engine")
        if component and hasattr(component, "analyze_news"):
            return await component.analyze_news(article)

        # Default: extract theme from title
        title = article.get("title", "")
        theme = title[:50] if title else "Unknown"
        return self.create_result(
            success=True,
            data={"narrative_phase": "UNKNOWN", "theme": theme, "stage": "narrative"},
            reasoning=f"Extracted theme: {theme}",
        )

    async def _stage3_fact_check(self, article: Dict[str, Any]) -> IntelligenceResult:
        """Stage 3: Fact verification"""
        component = self._components.get("fact_checker")
        if component and hasattr(component, "verify_data"):
            return await component.verify_data(article)

        # Default: pass without verification
        return self.create_result(
            success=True,
            data={"verification_status": "NOT_VERIFIED", "stage": "fact_check"},
            reasoning="No fact checker component, verification skipped",
        )

    async def _stage4_market_confirm(self, narrative: Dict[str, Any]) -> IntelligenceResult:
        """Stage 4: Market confirmation"""
        component = self._components.get("market_confirmation")
        if component and hasattr(component, "confirm_narrative"):
            return await component.confirm_narrative(narrative)

        # Default: neutral confirmation
        return self.create_result(
            success=True,
            data={"confirmation_status": "NEUTRAL", "stage": "market_confirm"},
            reasoning="No market confirmation component, neutral status",
        )

    async def _stage5_horizon_tagging(self, insight: Dict[str, Any]) -> IntelligenceResult:
        """Stage 5: Horizon tagging"""
        component = self._components.get("horizon_tagger")
        if component and hasattr(component, "tag_horizons"):
            return await component.tag_horizons(insight)

        # Default: medium-term horizon
        return self.create_result(
            success=True,
            data={"horizons": ["mid_term"], "stage": "horizon"},
            reasoning="No horizon tagger component, default to medium-term",
        )

    async def _stage6_policy_analysis(self, insight: Dict[str, Any]) -> IntelligenceResult:
        """Stage 6: Policy feasibility"""
        component = self._components.get("policy_feasibility")
        if component and hasattr(component, "analyze_feasibility"):
            return await component.analyze_feasibility(insight)

        # Default: no policy impact
        return self.create_result(
            success=True,
            data={"feasibility": 0.5, "stage": "policy"},
            reasoning="No policy component, neutral feasibility",
        )

    async def _generate_final_insight(self, stages: Dict[str, IntelligenceResult]) -> str:
        """Generate final comprehensive insight"""
        try:
            # Build insight from all stages
            insight_parts = []

            # Narrative phase
            if "narrative" in stages:
                narrative_data = stages["narrative"].data
                phase = narrative_data.get("narrative_phase", "UNKNOWN")
                insight_parts.append(f"Narrative: {phase}")

            # Market confirmation
            if "market_confirm" in stages:
                confirm_data = stages["market_confirm"].data
                status = confirm_data.get("confirmation_status", "NEUTRAL")
                insight_parts.append(f"Market: {status}")

            # Horizon
            if "horizon" in stages:
                horizon_data = stages["horizon"].data
                horizons = horizon_data.get("horizons", [])
                insight_parts.append(f"Horizon: {', '.join(horizons)}")

            # Use LLM to generate final insight if available
            if self.llm:
                prompt = self._build_insight_prompt(stages)
                llm_result = await self.llm.complete_with_system(
                    system_prompt="You are a market analyst. Generate a concise trading insight (2-3 sentences).",
                    user_prompt=prompt,
                )
                return llm_result.content

            return " | ".join(insight_parts)

        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            return "Generated insight unavailable"

    def _build_insight_prompt(self, stages: Dict[str, IntelligenceResult]) -> str:
        """Build prompt for LLM insight generation"""
        sections = []

        for stage_name, result in stages.items():
            if result.reasoning:
                sections.append(f"{stage_name.upper()}: {result.reasoning}")

        return "\n\n".join(sections)

    async def _generate_contrarian_view(self, stages: Dict[str, IntelligenceResult]) -> ContrarianView:
        """
        Generate forced contrarian view analysis

        Args:
            stages: Results from all pipeline stages

        Returns:
            ContrarianView: Contrarian perspective
        """
        try:
            # Analyze for contrarian signals
            bull_case = None
            bear_case = None
            key_risks = []
            confidence = 0.7

            # Check narrative phase
            if "narrative" in stages:
                narrative_data = stages["narrative"].data
                phase = narrative_data.get("narrative_phase", "")

                if phase == "FATIGUED":
                    bull_case = "Narrative fatigue suggests taking profits on recent winners"
                    key_risks.append("Late-stage narrative with low new information")
                elif phase == "CONSENSUS":
                    bull_case = "Consensus indicates potential reversal opportunity"
                    key_risks.append("Crowded trade with universal agreement")
                elif phase == "EMERGING":
                    bear_case = "Emerging narrative - wait for confirmation before entering"
                    key_risks.append("Early-stage narrative with high uncertainty")

            # Check market confirmation
            if "market_confirm" in stages:
                confirm_data = stages["market_confirm"].data
                status = confirm_data.get("confirmation_status", "")

                if status == "CONTRADICTED":
                    bull_case = "Price contradicts narrative - high conviction short opportunity"
                    key_risks.append("Divergence between story and price")
                elif status == "CONFIRMED":
                    bear_case = "Price confirms narrative - trend may be overextended"
                    key_risks.append("Confirmation often precedes reversal")

            # Determine confidence based on stage agreement
            agreement_score = 0
            for result in stages.values():
                if result.success:
                    agreement_score += 1

            confidence = min(0.95, 0.5 + (agreement_score / len(stages)) * 0.1)

            return ContrarianView(
                bull_case=bull_case,
                bear_case=bear_case,
                key_risks=key_risks,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Contrarian view generation error: {e}")
            return ContrarianView(
                bull_case="Unable to determine bull case",
                bear_case="Unable to determine bear case",
                key_risks=["Analysis error"],
                confidence=0.5,
            )

    def _identify_invalidation_conditions(self, stages: Dict[str, IntelligenceResult]) -> List[str]:
        """Identify conditions that could invalidate the thesis"""
        conditions = []

        # Fact check issues
        if "fact_check" in stages:
            fact_data = stages["fact_check"].data
            if fact_data.get("verification_status") == "HALLUCINATION":
                conditions.append("Fact verification failed - potential hallucination")

        # Market contradictions
        if "market_confirm" in stages:
            confirm_data = stages["market_confirm"].data
            if confirm_data.get("confirmation_status") == "CONTRADICTED":
                conditions.append("Price action contradicts narrative")

        # Narrative fatigue
        if "narrative" in stages:
            narrative_data = stages["narrative"].data
            if narrative_data.get("narrative_phase") == "FATIGUED":
                conditions.append("Narrative showing fatigue signs")

        # High crowding
        if stages.get("contrary_signal"):
            contrary_data = stages["contrary_signal"].data
            if contrary_data.get("crowding_level") in ["HIGH", "EXTREME"]:
                conditions.append("Extreme market crowding detected")

        return conditions

    def _identify_failure_triggers(self, stages: Dict[str, IntelligenceResult]) -> List[str]:
        """Identify events that would signal failure"""
        triggers = []

        # Component failures
        for stage_name, result in stages.items():
            if not result.success:
                triggers.append(f"{stage_name} component failed")

        # Data quality issues
        if "fact_check" in stages:
            fact_data = stages["fact_check"].data
            if fact_data.get("verification_status") == "HALLUCINATION":
                triggers.append("LLM hallucination detected")

        # Market regime changes
        if stages.get("regime_guard"):
            regime_data = stages["regime_guard"].data
            if regime_data.get("regime_changed") is True:
                triggers.append("Market regime change detected")

        # Extreme crowding
        if stages.get("contrary_signal"):
            contrary_data = stages["contrary_signal"].data
            if contrary_data.get("crowding_level") == "EXTREME":
                triggers.append("Extreme crowding - high reversal risk")

        return triggers

    def _create_result(
        self,
        success: bool = True,
        stages: Optional[Dict[str, IntelligenceResult]] = None,
        final_insight: Optional[str] = None,
        contrarian_view: Optional[ContrarianView] = None,
        invalidation_conditions: List[str] = None,
        failure_triggers: List[str] = None,
        processing_time_ms: int = 0,
    ) -> PipelineResult:
        """Create PipelineResult"""
        return PipelineResult(
            success=success,
            stages=stages or {},
            final_insight=final_insight,
            contrarian_view=contrarian_view,
            invalidation_conditions=invalidation_conditions or [],
            failure_triggers=failure_triggers or [],
            processing_time_ms=processing_time_ms,
        )

    def _create_error_result(
        self,
        message: str,
        stages: Optional[Dict[str, IntelligenceResult]] = None,
        processing_time_ms: int = 0,
    ) -> PipelineResult:
        """Create error PipelineResult"""
        return PipelineResult(
            success=False,
            stages=stages or {},
            final_insight=f"Error: {message}",
            contrarian_view=ContrarianView(
                bull_case=None,
                bear_case="Analysis failed",
                key_risks=["Pipeline error"],
                confidence=0.0,
            ),
            invalidation_conditions=["Pipeline error occurred"],
            failure_triggers=[message],
            processing_time_ms=processing_time_ms,
        )

    def _calculate_time(self, start_time: datetime) -> int:
        """Calculate elapsed time in milliseconds"""
        return int((datetime.now() - start_time).total_seconds() * 1000)

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        return {
            "total_processed": self._processed_count,
            "early_terminations": self._early_termination_count,
            "component_failures": self._component_failures,
        }


# ============================================================================
# Factory function
# ============================================================================

def create_enhanced_pipeline(
    llm_provider: Optional[LLMProvider] = None,
    intelligence_components: Optional[Dict[str, Any]] = None,
) -> EnhancedNewsProcessingPipeline:
    """
    Create Enhanced News Processing Pipeline instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        intelligence_components: Dictionary of intelligence components

    Returns:
        EnhancedNewsProcessingPipeline: Configured pipeline instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return EnhancedNewsProcessingPipeline(
        llm_provider=llm_provider,
        intelligence_components=intelligence_components,
    )
