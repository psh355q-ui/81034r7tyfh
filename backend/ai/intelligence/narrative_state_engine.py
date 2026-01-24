"""
NarrativeStateEngine Component - Fact/Narrative Separation & Phase Tracking

Market Intelligence v2.0 - Phase 1, T1.2

This component implements ChatGPT's core insight: separating Fact layer from Narrative layer
to track market narratives through their lifecycle:
- EMERGING: New narrative appears
- ACCELERATING: Gaining momentum
- CONSENSUS: Widely accepted
- FATIGUED: Overplayed/losing impact
- REVERSING: Breaking down

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider, ModelConfig, ModelProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class NarrativePhase(Enum):
    """Narrative lifecycle phases"""
    EMERGING = "EMERGING"       # New narrative appears
    ACCELERATING = "ACCELERATING"  # Gaining momentum
    CONSENSUS = "CONSENSUS"     # Widely accepted
    FATIGUED = "FATIGUED"       # Overplayed/losing impact
    REVERSING = "REVERSING"     # Breaking down


@dataclass
class NarrativeState:
    """
    Narrative state tracking

    Attributes:
        topic: Narrative topic (e.g., "AI Semiconductor Boom")
        fact_layer: Concrete facts (earnings, data, events)
        narrative_layer: Market interpretation/thesis
        phase: Current lifecycle phase
        confidence: Confidence in phase assessment (0.0 to 1.0)
        evidence_count: Number of data points supporting this narrative
        first_seen: When narrative first emerged
        last_updated: Last time this narrative was updated
        related_symbols: Related stock symbols
    """
    topic: str
    fact_layer: str
    narrative_layer: str
    phase: NarrativePhase
    confidence: float = 0.7
    evidence_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    related_symbols: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "topic": self.topic,
            "fact_layer": self.fact_layer,
            "narrative_layer": self.narrative_layer,
            "phase": self.phase.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "related_symbols": self.related_symbols,
        }


# ============================================================================
# Main Component
# ============================================================================

class NarrativeStateEngine(BaseIntelligence):
    """
    Narrative State Engine

    Implements Fact/Narrative separation and tracks narrative lifecycle phases.

    Key Features:
    1. Separates Fact layer (concrete data) from Narrative layer (interpretation)
    2. Tracks narrative phase: EMERGING → ACCELERATING → CONSENSUS → FATIGUED → REVERSING
    3. Detects narrative shifts when new evidence suggests phase change
    4. Maintains narrative state in database via Repository Pattern

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.narrative_state_engine import NarrativeStateEngine

        llm = get_llm_provider()
        engine = NarrativeStateEngine(llm_provider=llm)

        # Analyze news article
        result = await engine.analyze_news(article)
        fact_layer = result.data["fact_layer"]
        narrative_layer = result.data["narrative_layer"]
        phase = result.data["phase"]

        # Detect narrative shift
        shift = await engine.detect_narrative_shift(previous_state, new_article)
        if shift:
            print(f"Narrative shifted from {shift['from_phase']} to {shift['to_phase']}")
    """

    # System prompts
    ANALYZE_SYSTEM_PROMPT = """You are an expert market narrative analyst specializing in separating FACT from NARRATIVE.

Your task is to analyze news articles and extract:
1. **fact_layer**: Concrete, verifiable facts (numbers, events, data)
2. **narrative_layer**: Market interpretation, thesis, or story
3. **phase**: Current lifecycle phase of this narrative
4. **confidence**: Your confidence in the phase assessment (0.0 to 1.0)
5. **evidence**: Key evidence points supporting your assessment

**Narrative Phases**:
- EMERGING: New narrative, limited coverage, early stage
- ACCELERATING: Gaining momentum, increasing coverage
- CONSENSUS: Widely accepted, mainstream view
- FATIGUED: Overplayed, losing impact, saturation
- REVERSING: Breaking down, contradictory evidence

**Format**: Respond in JSON format ONLY. No additional text:
{
    "fact_layer": "Concrete facts...",
    "narrative_layer": "Market interpretation...",
    "phase": "ACCELERATING",
    "confidence": 0.85,
    "evidence": ["evidence1", "evidence2", "evidence3"]
}

IMPORTANT: The phase field must be one of: EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING

**Examples**:

Fact: "Samsung reported Q4 revenue of KRW 77.2 trillion, up 12% YoY. Operating profit: KRW 6.5 trillion."
Narrative: "AI chip boom powers Samsung's earnings recovery as memory prices rise."

Fact: "Fed Chair Powell confirmed rate cuts likely in 2025 if inflation cools."
Narrative: "Fed pivot is confirmed - market expectations validated."""

    DETECT_SHIFT_SYSTEM_PROMPT = """You are a narrative shift detection specialist.

Given a previous narrative state and a new news article, determine if the narrative has shifted to a different phase.

**Narrative Flow**: EMERGING → ACCELERATING → CONSENSUS → FATIGUED → REVERSING

**Output Format**: JSON
{
    "shift_detected": true/false,
    "from_phase": "PREVIOUS_PHASE",
    "to_phase": "NEW_PHASE",
    "reasoning": "Brief explanation...",
    "confidence": 0.8
}

**Consider**:
- Volume/intensity of coverage
- New evidence strength
- Market reaction
- Consensus level
- Contradictory signals"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        analysis_config: Optional[ModelConfig] = None,
    ):
        """
        Initialize NarrativeStateEngine

        Args:
            llm_provider: LLM Provider instance
            analysis_config: Custom analysis config (optional)
        """
        super().__init__(
            name="NarrativeStateEngine",
            phase=IntelligencePhase.P0,
        )

        self.llm = llm_provider
        self.analysis_config = analysis_config or llm_provider.create_stage2_config()

        # In-memory state tracking (in production, use database)
        self._narrative_states: Dict[str, NarrativeState] = {}

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze news article (main entry point)

        Args:
            data: Article data with 'title' and 'content'

        Returns:
            IntelligenceResult: Analysis result
        """
        return await self.analyze_news(data)

    async def analyze_news(self, article: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze news article and extract Fact/Narrative layers

        Args:
            article: Article data with 'title', 'content', and optional 'symbols'

        Returns:
            IntelligenceResult: Analysis result with:
                - fact_layer: Concrete facts
                - narrative_layer: Market interpretation
                - phase: Current narrative phase
                - confidence: Confidence score
                - evidence: Supporting evidence list
                - topic: Extracted narrative topic
                - saved: True if saved to database
        """
        # Validate input
        try:
            self.validate_input(article, ["title", "content"])
        except ValueError as e:
            result = self.create_result(
                success=False,
                data={"stage": "narrative_analysis"},
            )
            result.add_error(f"Input validation failed: {str(e)}")
            return result

        start_time = datetime.now()

        try:
            # Build prompt
            prompt = self._build_analysis_prompt(article)

            # Call LLM
            response = await self.llm.complete_with_system(
                system_prompt=self.ANALYZE_SYSTEM_PROMPT,
                user_prompt=prompt,
                config=self.analysis_config,
            )

            # Parse response
            parsed = self._parse_analysis_response(response.content)

            # Extract topic
            topic = self._extract_topic(article, parsed)

            # Create narrative state
            narrative_state = NarrativeState(
                topic=topic,
                fact_layer=parsed["fact_layer"],
                narrative_layer=parsed["narrative_layer"],
                phase=NarrativePhase(parsed["phase"]),
                confidence=parsed["confidence"],
                evidence_count=len(parsed.get("evidence", [])),
                related_symbols=article.get("symbols", []),
            )

            # Save state (in-memory for now, should use DB in production)
            self._narrative_states[topic] = narrative_state

            latency = (datetime.now() - start_time).total_seconds() * 1000

            return self.create_result(
                success=True,
                data={
                    "stage": "narrative_analysis",
                    "topic": topic,
                    "fact_layer": parsed["fact_layer"],
                    "narrative_layer": parsed["narrative_layer"],
                    "phase": parsed["phase"],
                    "confidence": parsed["confidence"],
                    "evidence": parsed.get("evidence", []),
                    "saved": True,
                },
                confidence=parsed["confidence"],
                reasoning=f"Narrative: {topic} in {parsed['phase']} phase",
                metadata={
                    "latency_ms": int(latency),
                    "tokens_used": response.tokens_used,
                    "narrative_state": narrative_state.to_dict(),
                },
            )

        except Exception as e:
            logger.error(f"Narrative analysis error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "narrative_analysis"},
            )
            result.add_error(f"Analysis error: {str(e)}")
            return result

    async def detect_narrative_shift(
        self,
        previous_state: NarrativeState,
        new_article: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if narrative has shifted to a different phase

        Args:
            previous_state: Previous narrative state
            new_article: New news article to analyze

        Returns:
            Dict with shift details if shift detected, None/FALSE otherwise
                - from_phase: Previous phase
                - to_phase: New phase
                - reasoning: Explanation
                - confidence: Confidence in shift detection
        """
        try:
            # Build shift detection prompt
            prompt = self._build_shift_detection_prompt(previous_state, new_article)

            # Call LLM
            response = await self.llm.complete_with_system(
                system_prompt=self.DETECT_SHIFT_SYSTEM_PROMPT,
                user_prompt=prompt,
                config=self.analysis_config,
            )

            # Parse response
            parsed = self._parse_shift_response(response.content)

            if not parsed.get("shift_detected", False):
                return False  # No shift

            return {
                "from_phase": parsed["from_phase"],
                "to_phase": parsed["to_phase"],
                "reasoning": parsed.get("reasoning", ""),
                "confidence": parsed.get("confidence", 0.7),
            }

        except Exception as e:
            logger.error(f"Shift detection error: {e}")
            return None

    def _build_analysis_prompt(self, article: Dict[str, Any]) -> str:
        """Build analysis prompt from article"""
        return f"""Title: {article['title']}
Content: {article['content']}

Extract the Fact layer and Narrative layer from this news article."""

    def _build_shift_detection_prompt(
        self,
        previous_state: NarrativeState,
        new_article: Dict[str, Any]
    ) -> str:
        """Build shift detection prompt"""
        return f"""Previous Narrative State:
- Topic: {previous_state.topic}
- Phase: {previous_state.phase.value}
- Fact Layer: {previous_state.fact_layer[:200]}...
- Narrative Layer: {previous_state.narrative_layer[:200]}...
- Evidence Count: {previous_state.evidence_count}
- Last Updated: {previous_state.last_updated.strftime('%Y-%m-%d')}

New Article:
- Title: {new_article['title']}
- Content: {new_article['content']}

Has this narrative shifted to a different phase?"""

    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            parsed = json.loads(content)
            return {
                "fact_layer": parsed.get("fact_layer", ""),
                "narrative_layer": parsed.get("narrative_layer", ""),
                "phase": parsed.get("phase", "EMERGING"),
                "confidence": parsed.get("confidence", 0.7),
                "evidence": parsed.get("evidence", []),
            }
        except json.JSONDecodeError:
            return self._parse_analysis_fallback(content)

    def _parse_shift_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM shift detection response"""
        try:
            parsed = json.loads(content)
            return {
                "shift_detected": parsed.get("shift_detected", False),
                "from_phase": parsed.get("from_phase", ""),
                "to_phase": parsed.get("to_phase", ""),
                "reasoning": parsed.get("reasoning", ""),
                "confidence": parsed.get("confidence", 0.7),
            }
        except json.JSONDecodeError:
            return {"shift_detected": False}

    def _parse_analysis_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback parser when JSON parsing fails"""
        # Simple rule-based extraction
        lines = text.split('\n')

        fact_layer = ""
        narrative_layer = ""
        phase = "EMERGING"

        for line in lines:
            line_lower = line.lower()
            if "fact" in line_lower or "earnings" in line_lower or "revenue" in line_lower:
                fact_layer += line + " "
            elif "narrative" in line_lower or "story" in line_lower or "thesis" in line_lower:
                narrative_layer += line + " "

        # Phase detection from keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ["accelerating", "gaining", "building"]):
            phase = "ACCELERATING"
        elif any(word in text_lower for word in ["consensus", "widely", "mainstream"]):
            phase = "CONSENSUS"
        elif any(word in text_lower for word in ["fatigue", "overplayed", "saturation"]):
            phase = "FATIGUED"
        elif any(word in text_lower for word in ["reversing", "breakdown", "contradictory"]):
            phase = "REVERSING"

        return {
            "fact_layer": fact_layer.strip() or text[:300],
            "narrative_layer": narrative_layer.strip() or text[300:600],
            "phase": phase,
            "confidence": 0.6,
            "evidence": ["Derived from text analysis"],
        }

    def _extract_topic(self, article: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Extract narrative topic from article and analysis"""
        # Simple topic extraction from title
        title = article.get("title", "")

        # Keywords for common topics
        topic_keywords = {
            "AI Semiconductor Boom": ["ai", "chip", "semiconductor", "nvidia", "samsung"],
            "Fed Rate Cuts": ["fed", "rate cut", "interest rate", "powell"],
            "EV Trade": ["ev", "electric vehicle", "tesla", "byd"],
            "China Reopening": ["china", "reopening", "chinese economy"],
        }

        title_lower = title.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return topic

        # Fallback: use first few words of title
        return " ".join(title.split()[:5])


# ============================================================================
# Factory function
# ============================================================================

def create_narrative_state_engine(
    llm_provider: Optional[LLMProvider] = None,
) -> NarrativeStateEngine:
    """
    Create NarrativeStateEngine instance

    Args:
        llm_provider: LLM Provider (uses default if None)

    Returns:
        NarrativeStateEngine: Configured engine instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return NarrativeStateEngine(llm_provider=llm_provider)
