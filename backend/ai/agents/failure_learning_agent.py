"""
Failure Learning Agent

Phase 29 확장: AI 예측 실패 분석 및 학습 시스템
Date: 2025-12-30

AI가 틀린 예측을 분석하여:
1. 실패 패턴 식별
2. 근본 원인 분석 (Gemini Flash 사용)
3. 개선 제안 생성
4. War Room 가중치 조정 제안

주요 기능:
- 실패 예측 수집 (accuracy < 0.5)
- 자동 근본 원인 분석 (RCA)
- 에이전트별 실패율 추적
- 가중치 조정 제안
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, func, desc
import google.generativeai as genai

from backend.database.repository import get_sync_session
from backend.database.models import (
    NewsInterpretation,
    NewsMarketReaction,
    FailureAnalysis
)

logger = logging.getLogger(__name__)


class FailureLearningAgent:
    """
    실패 학습 에이전트

    AI 예측 실패를 분석하고 시스템을 개선하는 피드백 루프
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize Failure Learning Agent

        Args:
            gemini_api_key: Gemini API key (optional, uses env var if not provided)
        """
        self.agent_name = "FailureLearningAgent"

        # Gemini API for root cause analysis
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
            self.use_gemini = True
            logger.info("✅ Gemini API initialized for root cause analysis")
        else:
            self.gemini_model = None
            self.use_gemini = False
            logger.warning("⚠️ GEMINI_API_KEY not found - using rule-based analysis")

    def collect_failed_predictions(
        self,
        lookback_days: int = 7,
        accuracy_threshold: float = 0.5
    ) -> List[Dict]:
        """
        실패한 예측 수집 (accuracy < threshold)

        Args:
            lookback_days: 조회 기간 (기본 7일)
            accuracy_threshold: 실패 기준 (기본 0.5)

        Returns:
            List of failed predictions with details
        """
        logger.info(f"🔍 Collecting failed predictions (last {lookback_days} days, accuracy < {accuracy_threshold})")

        with get_sync_session() as session:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Query failed predictions (1d accuracy < threshold)
            failed = session.query(
                NewsInterpretation,
                NewsMarketReaction
            ).join(
                NewsMarketReaction,
                NewsInterpretation.id == NewsMarketReaction.interpretation_id
            ).filter(
                and_(
                    NewsMarketReaction.accuracy_1d.isnot(None),
                    NewsMarketReaction.accuracy_1d < accuracy_threshold,
                    NewsMarketReaction.verified_at_1d >= cutoff_date
                )
            ).order_by(
                desc(NewsMarketReaction.verified_at_1d)
            ).all()

            results = []
            for interp, reaction in failed:
                results.append({
                    "interpretation_id": interp.id,
                    "ticker": interp.ticker,
                    "headline_bias": interp.headline_bias,
                    "expected_impact": interp.expected_impact,
                    "confidence": interp.confidence,
                    "reasoning": interp.reasoning,
                    "interpreted_at": interp.interpreted_at,
                    "price_change_1d": float(reaction.price_change_1d) if reaction.price_change_1d else None,
                    "accuracy_1d": float(reaction.accuracy_1d) if reaction.accuracy_1d else None,
                    "verified_at": reaction.verified_at_1d
                })

            logger.info(f"📊 Found {len(results)} failed predictions")
            return results

    def classify_failure_type(self, prediction: Dict) -> str:
        """
        실패 유형 분류

        Types:
        - WRONG_DIRECTION: 방향 예측 실패 (BULLISH인데 하락, BEARISH인데 상승)
        - WRONG_MAGNITUDE: 방향은 맞지만 영향도 과대/과소평가
        - WRONG_TIMING: 시간대 예측 실패 (INTRADAY인데 며칠 걸림)
        - WRONG_CONFIDENCE: 신뢰도 과대평가 (confidence 높은데 틀림)
        - MISSED_SIGNAL: 중요한 신호 놓침
        - FALSE_POSITIVE: 중요하지 않은 뉴스를 중요하게 판단

        Args:
            prediction: Failed prediction dict

        Returns:
            Failure type string
        """
        bias = prediction["headline_bias"]
        price_change = prediction["price_change_1d"]
        confidence = prediction["confidence"]
        accuracy = prediction["accuracy_1d"]

        # WRONG_DIRECTION: Opposite direction
        if bias == "BULLISH" and price_change < -1.0:
            return "WRONG_DIRECTION"
        elif bias == "BEARISH" and price_change > 1.0:
            return "WRONG_DIRECTION"

        # WRONG_CONFIDENCE: High confidence but very wrong
        if confidence >= 80 and accuracy < 0.3:
            return "WRONG_CONFIDENCE"

        # WRONG_MAGNITUDE: Right direction but wrong impact
        if prediction["expected_impact"] == "HIGH" and abs(price_change) < 1.0:
            return "WRONG_MAGNITUDE"

        # Default: MISSED_SIGNAL
        return "MISSED_SIGNAL"

    def calculate_severity(self, prediction: Dict, failure_type: str) -> str:
        """
        실패 심각도 계산

        Severity Levels:
        - CRITICAL: 큰 금액 손실 가능성 (HIGH impact + 완전 반대 방향)
        - HIGH: 중요한 오판 (높은 신뢰도인데 틀림)
        - MEDIUM: 일반적인 오류
        - LOW: 사소한 오차

        Args:
            prediction: Failed prediction dict
            failure_type: Failure type

        Returns:
            Severity string (CRITICAL/HIGH/MEDIUM/LOW)
        """
        impact = prediction["expected_impact"]
        confidence = prediction["confidence"]
        price_change = abs(prediction["price_change_1d"] or 0)

        # CRITICAL: HIGH impact + WRONG_DIRECTION + big price move
        if impact == "HIGH" and failure_type == "WRONG_DIRECTION" and price_change > 5.0:
            return "CRITICAL"

        # HIGH: High confidence but very wrong
        if confidence >= 80 and failure_type == "WRONG_CONFIDENCE":
            return "HIGH"

        # MEDIUM: Significant mistakes
        if failure_type in ["WRONG_DIRECTION", "WRONG_MAGNITUDE"]:
            return "MEDIUM"

        # LOW: Minor errors
        return "LOW"

    def analyze_root_cause_with_gemini(self, prediction: Dict, failure_type: str) -> Tuple[str, str, str]:
        """
        Gemini를 사용한 근본 원인 분석

        Args:
            prediction: Failed prediction dict
            failure_type: Failure type

        Returns:
            (root_cause, lesson_learned, recommended_fix)
        """
        if not self.use_gemini:
            return self._rule_based_analysis(prediction, failure_type)

        try:
            prompt = f"""
You are a financial AI failure analyst. Analyze why this prediction failed.

**Failed Prediction:**
- Ticker: {prediction['ticker']}
- Predicted Bias: {prediction['headline_bias']}
- Expected Impact: {prediction['expected_impact']}
- Confidence: {prediction['confidence']}%
- Reasoning: {prediction['reasoning']}

**Actual Outcome:**
- Price Change (1d): {prediction['price_change_1d']:.2f}%
- Accuracy Score: {prediction['accuracy_1d']:.2f}

**Failure Type:** {failure_type}

Provide a concise analysis in this format:

ROOT CAUSE:
[1-2 sentences explaining why the AI was wrong]

LESSON LEARNED:
[Key takeaway for future predictions]

RECOMMENDED FIX:
[Specific actionable improvement]
"""

            response = self.gemini_model.generate_content(prompt)
            analysis = response.text

            # Parse response
            root_cause = self._extract_section(analysis, "ROOT CAUSE:")
            lesson = self._extract_section(analysis, "LESSON LEARNED:")
            fix = self._extract_section(analysis, "RECOMMENDED FIX:")

            return (root_cause, lesson, fix)

        except Exception as e:
            logger.warning(f"⚠️ Gemini analysis failed: {e}, using rule-based fallback")
            return self._rule_based_analysis(prediction, failure_type)

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from Gemini response"""
        try:
            start = text.index(section_name) + len(section_name)
            end = text.index("\n\n", start) if "\n\n" in text[start:] else len(text)
            return text[start:end].strip()
        except ValueError:
            return "Analysis section not found"

    def _rule_based_analysis(self, prediction: Dict, failure_type: str) -> Tuple[str, str, str]:
        """
        규칙 기반 분석 (Gemini 없을 때 fallback)

        Returns:
            (root_cause, lesson_learned, recommended_fix)
        """
        bias = prediction["headline_bias"]
        confidence = prediction["confidence"]

        if failure_type == "WRONG_DIRECTION":
            return (
                f"AI predicted {bias} but market moved opposite direction. "
                f"Likely missed important context or misinterpreted sentiment.",
                "Headlines can be misleading. Always cross-check with actual fundamentals.",
                "Add sentiment cross-validation with multiple sources. Lower weight for headline-only analysis."
            )

        elif failure_type == "WRONG_CONFIDENCE":
            return (
                f"AI was {confidence}% confident but accuracy was only {prediction['accuracy_1d']:.1%}. "
                f"Overconfidence in news impact assessment.",
                "High confidence doesn't guarantee accuracy. Be more conservative.",
                "Reduce confidence scores by 20% for news-based predictions. Add uncertainty margin."
            )

        elif failure_type == "WRONG_MAGNITUDE":
            return (
                f"Predicted {prediction['expected_impact']} impact but actual price change was {prediction['price_change_1d']:.2f}%. "
                f"Overestimated market reaction.",
                "News impact varies by market conditions. Don't assume linear response.",
                "Factor in VIX and sector momentum before estimating impact magnitude."
            )

        else:  # MISSED_SIGNAL, FALSE_POSITIVE, WRONG_TIMING
            return (
                f"Failure to accurately assess news significance for {prediction['ticker']}.",
                "Context matters more than headlines. Consider broader market regime.",
                "Improve macro context integration. Add sector-specific filters."
            )

    def save_failure_analysis(
        self,
        prediction: Dict,
        failure_type: str,
        severity: str,
        root_cause: str,
        lesson: str,
        fix: str
    ) -> int:
        """
        실패 분석을 DB에 저장

        Args:
            prediction: Failed prediction
            failure_type: Failure type
            severity: Severity level
            root_cause: Root cause description
            lesson: Lesson learned
            fix: Recommended fix

        Returns:
            Saved FailureAnalysis ID
        """
        with get_sync_session() as session:
            analysis = FailureAnalysis(
                interpretation_id=prediction["interpretation_id"],
                ticker=prediction["ticker"],
                failure_type=failure_type,
                severity=severity,
                expected_outcome=f"{prediction['headline_bias']} with {prediction['expected_impact']} impact",
                actual_outcome=f"Price changed {prediction['price_change_1d']:.2f}% (accuracy: {prediction['accuracy_1d']:.2%})",
                root_cause=root_cause,
                lesson_learned=lesson,
                recommended_fix=fix,
                fix_applied=False,
                analyzed_by=self.agent_name,
                analyzed_at=datetime.now()
            )

            session.add(analysis)
            session.commit()
            session.refresh(analysis)

            logger.info(f"💾 Saved failure analysis #{analysis.id} ({failure_type} - {severity})")
            return analysis.id

    def analyze_all_failures(self, lookback_days: int = 7) -> Dict:
        """
        모든 실패 예측 분석 및 저장

        Args:
            lookback_days: 조회 기간

        Returns:
            Summary statistics
        """
        logger.info(f"🚀 Starting failure analysis (last {lookback_days} days)")

        # Collect failed predictions
        failed_predictions = self.collect_failed_predictions(lookback_days)

        if not failed_predictions:
            logger.info("✅ No failures found - system is performing well!")
            return {
                "total_failures": 0,
                "analyzed": 0,
                "by_type": {},
                "by_severity": {}
            }

        # Analyze each failure
        analyzed_count = 0
        by_type = {}
        by_severity = {}

        for prediction in failed_predictions:
            try:
                # Classify failure
                failure_type = self.classify_failure_type(prediction)
                severity = self.calculate_severity(prediction, failure_type)

                # Root cause analysis
                root_cause, lesson, fix = self.analyze_root_cause_with_gemini(prediction, failure_type)

                # Save to DB
                self.save_failure_analysis(
                    prediction, failure_type, severity,
                    root_cause, lesson, fix
                )

                analyzed_count += 1
                by_type[failure_type] = by_type.get(failure_type, 0) + 1
                by_severity[severity] = by_severity.get(severity, 0) + 1

            except Exception as e:
                logger.error(f"❌ Failed to analyze prediction #{prediction['interpretation_id']}: {e}")

        logger.info(f"✅ Analyzed {analyzed_count}/{len(failed_predictions)} failures")

        return {
            "total_failures": len(failed_predictions),
            "analyzed": analyzed_count,
            "by_type": by_type,
            "by_severity": by_severity
        }

    def get_agent_failure_stats(self, lookback_days: int = 30) -> Dict[str, Dict]:
        """
        에이전트별 실패 통계

        Args:
            lookback_days: 조회 기간

        Returns:
            Dict mapping agent name to failure stats
        """
        logger.info(f"📊 Calculating agent failure stats (last {lookback_days} days)")

        with get_sync_session() as session:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Get all interpretations with reactions
            results = session.query(
                NewsInterpretation,
                NewsMarketReaction
            ).join(
                NewsMarketReaction,
                NewsInterpretation.id == NewsMarketReaction.interpretation_id
            ).filter(
                and_(
                    NewsMarketReaction.accuracy_1d.isnot(None),
                    NewsMarketReaction.verified_at_1d >= cutoff_date
                )
            ).all()

            # TODO: Link interpretations to specific agents
            # For now, return placeholder stats
            # Real implementation would need news_decision_links table

            return {
                "news_agent": {
                    "total_predictions": len(results),
                    "failures": len([r for r in results if r[1].accuracy_1d < 0.5]),
                    "failure_rate": len([r for r in results if r[1].accuracy_1d < 0.5]) / len(results) if results else 0.0
                }
            }

    def generate_weight_adjustment_recommendation(self) -> Dict:
        """
        War Room 가중치 조정 제안 생성

        Returns:
            Weight adjustment recommendations
        """
        logger.info("💡 Generating weight adjustment recommendations")

        # Get agent stats
        stats = self.get_agent_failure_stats(lookback_days=30)

        recommendations = {}

        for agent_name, agent_stats in stats.items():
            failure_rate = agent_stats["failure_rate"]

            if failure_rate > 0.6:  # 60% 이상 실패
                recommendations[agent_name] = {
                    "current_failure_rate": failure_rate,
                    "action": "DECREASE",
                    "suggested_change": -0.05,  # -5%
                    "reason": f"High failure rate ({failure_rate:.1%})"
                }
            elif failure_rate < 0.3:  # 30% 미만 실패 (70% 성공)
                recommendations[agent_name] = {
                    "current_failure_rate": failure_rate,
                    "action": "INCREASE",
                    "suggested_change": +0.03,  # +3%
                    "reason": f"Low failure rate ({failure_rate:.1%}) - performing well"
                }
            else:
                recommendations[agent_name] = {
                    "current_failure_rate": failure_rate,
                    "action": "MAINTAIN",
                    "suggested_change": 0.0,
                    "reason": "Performance within acceptable range"
                }

        logger.info(f"✅ Generated {len(recommendations)} recommendations")
        return recommendations


def main():
    """CLI entry point for testing"""
    logging.basicConfig(level=logging.INFO)

    agent = FailureLearningAgent()

    # Analyze recent failures
    print("\n" + "="*80)
    print("Failure Learning Agent - Test Run")
    print("="*80 + "\n")

    results = agent.analyze_all_failures(lookback_days=7)

    print("\n" + "="*80)
    print("Analysis Results")
    print("="*80)
    print(f"Total Failures: {results['total_failures']}")
    print(f"Analyzed: {results['analyzed']}")
    print(f"\nBy Type:")
    for ftype, count in results['by_type'].items():
        print(f"  {ftype}: {count}")
    print(f"\nBy Severity:")
    for severity, count in results['by_severity'].items():
        print(f"  {severity}: {count}")
    print("="*80 + "\n")

    # Weight adjustment recommendations
    recommendations = agent.generate_weight_adjustment_recommendation()
    print("Weight Adjustment Recommendations:")
    for agent_name, rec in recommendations.items():
        print(f"  {agent_name}: {rec['action']} ({rec['suggested_change']:+.2%}) - {rec['reason']}")
    print()


if __name__ == "__main__":
    main()
