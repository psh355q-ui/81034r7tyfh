"""
Failure Learning Scheduler

Phase 29 확장: 자동 학습 스케줄러
Date: 2025-12-30

매일 자정에 실행되어:
1. NIA 점수 계산
2. 실패 예측 분석
3. War Room 가중치 자동 조정
4. 학습 결과 저장

Schedule: 매일 00:00 (KST)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import and_, func

from backend.database.repository import get_sync_session
from backend.database.models import (
    NewsInterpretation,
    NewsMarketReaction,
    AgentWeightsHistory
)
from backend.ai.agents.failure_learning_agent import FailureLearningAgent

logger = logging.getLogger(__name__)


class FailureLearningScheduler:
    """
    자동 학습 스케줄러

    매일 실행되어 NIA 점수 기반으로 War Room 가중치를 자동 조정
    """

    def __init__(self):
        """Initialize scheduler"""
        self.agent = FailureLearningAgent()
        self.scheduler_name = "FailureLearningScheduler"

    def calculate_nia_score(self, lookback_days: int = 30) -> Optional[float]:
        """
        NIA (News Interpretation Accuracy) 점수 계산

        Args:
            lookback_days: 조회 기간 (기본 30일)

        Returns:
            NIA score (0.0 ~ 1.0) or None if no data
        """
        logger.info(f"📊 Calculating NIA score (last {lookback_days} days)")

        with get_sync_session() as session:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # Get all verified predictions
            results = session.query(
                NewsMarketReaction.accuracy_1d
            ).join(
                NewsInterpretation,
                NewsMarketReaction.interpretation_id == NewsInterpretation.id
            ).filter(
                and_(
                    NewsMarketReaction.accuracy_1d.isnot(None),
                    NewsMarketReaction.verified_at_1d >= cutoff_date
                )
            ).all()

            if not results:
                logger.warning("⚠️ No verified predictions found")
                return None

            # Calculate average accuracy
            accuracies = [r[0] for r in results]
            nia_score = sum(accuracies) / len(accuracies)

            logger.info(f"✅ NIA Score: {nia_score:.2%} (based on {len(accuracies)} predictions)")
            return nia_score

    def get_current_weights(self) -> Dict[str, float]:
        """
        현재 War Room 가중치 조회

        Returns:
            Dict mapping agent name to weight
        """
        with get_sync_session() as session:
            # Get latest weights
            latest = session.query(AgentWeightsHistory).order_by(
                AgentWeightsHistory.changed_at.desc()
            ).first()

            if latest:
                return {
                    "trader_agent": float(latest.trader_agent or 0.15),
                    "risk_agent": float(latest.risk_agent or 0.15),
                    "analyst_agent": float(latest.analyst_agent or 0.12),
                    "macro_agent": float(latest.macro_agent or 0.14),
                    "institutional_agent": float(latest.institutional_agent or 0.14),
                    "news_agent": float(latest.news_agent or 0.14),
                    "chip_war_agent": float(latest.chip_war_agent or 0.14),
                    "dividend_risk_agent": float(latest.dividend_risk_agent or 0.02)
                }
            else:
                # Default weights
                return {
                    "trader_agent": 0.15,
                    "risk_agent": 0.15,
                    "analyst_agent": 0.12,
                    "macro_agent": 0.14,
                    "institutional_agent": 0.14,
                    "news_agent": 0.14,
                    "chip_war_agent": 0.14,
                    "dividend_risk_agent": 0.02
                }

    def adjust_weights_based_on_nia(
        self,
        nia_score: float,
        current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        NIA 점수 기반 가중치 자동 조정

        규칙:
        - NIA < 60%: News Agent -2%, 다른 에이전트로 재배분
        - 60% <= NIA < 80%: 변화 없음
        - NIA >= 80%: News Agent +2%, 다른 에이전트에서 가져오기

        Args:
            nia_score: NIA 점수 (0.0 ~ 1.0)
            current_weights: 현재 가중치

        Returns:
            Adjusted weights
        """
        logger.info(f"⚙️ Adjusting weights based on NIA: {nia_score:.2%}")

        new_weights = current_weights.copy()

        # News Agent weight adjustment
        news_weight = new_weights["news_agent"]
        adjustment = 0.0

        if nia_score < 0.60:
            # Poor performance - decrease News Agent weight
            adjustment = -0.02
            reason = f"NIA below 60% ({nia_score:.1%}) - decreasing News Agent weight"
        elif nia_score >= 0.80:
            # Excellent performance - increase News Agent weight
            adjustment = 0.02
            reason = f"NIA above 80% ({nia_score:.1%}) - increasing News Agent weight"
        else:
            # Acceptable performance - no change
            reason = f"NIA in acceptable range ({nia_score:.1%}) - maintaining weights"
            logger.info(f"✅ {reason}")
            return new_weights

        # Apply adjustment to News Agent
        new_news_weight = max(0.05, min(0.25, news_weight + adjustment))
        actual_adjustment = new_news_weight - news_weight

        if actual_adjustment == 0.0:
            logger.info("⚠️ News Agent weight at boundary - no adjustment")
            return new_weights

        new_weights["news_agent"] = new_news_weight

        # Redistribute to/from other agents (excluding PM and News)
        other_agents = [
            "trader_agent",
            "risk_agent",
            "analyst_agent",
            "macro_agent",
            "institutional_agent",
            "chip_war_agent",
            "dividend_risk_agent"
        ]

        # Calculate redistribution per agent
        redistribution_per_agent = -actual_adjustment / len(other_agents)

        for agent in other_agents:
            new_weights[agent] = max(0.01, new_weights[agent] + redistribution_per_agent)

        # Normalize to ensure sum = 1.0 (excluding PM which is 0)
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.001:
            scale = 1.0 / total
            for agent in new_weights:
                new_weights[agent] *= scale

        logger.info(f"✅ {reason}")
        logger.info(f"   News Agent: {news_weight:.2%} → {new_weights['news_agent']:.2%} ({actual_adjustment:+.2%})")

        return new_weights

    def save_weight_adjustment(
        self,
        old_weights: Dict[str, float],
        new_weights: Dict[str, float],
        reason: str
    ) -> bool:
        """
        가중치 조정 히스토리 저장

        Args:
            old_weights: 이전 가중치
            new_weights: 새 가중치
            reason: 조정 이유

        Returns:
            True if saved successfully
        """
        logger.info("💾 Saving weight adjustment to history")

        try:
            with get_sync_session() as session:
                history = AgentWeightsHistory(
                    changed_at=datetime.now(),
                    changed_by=self.scheduler_name,
                    reason=reason,
                    trader_agent=new_weights["trader_agent"],
                    risk_agent=new_weights["risk_agent"],
                    analyst_agent=new_weights["analyst_agent"],
                    macro_agent=new_weights["macro_agent"],
                    institutional_agent=new_weights["institutional_agent"],
                    news_agent=new_weights["news_agent"],
                    chip_war_agent=new_weights["chip_war_agent"],
                    dividend_risk_agent=new_weights["dividend_risk_agent"],
                    pm_agent=0.0  # PM has no weight (final decision maker)
                )

                session.add(history)
                session.commit()

                logger.info("✅ Weight adjustment saved")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to save weight adjustment: {e}")
            return False

    def run_daily_learning_cycle(self) -> Dict:
        """
        일일 학습 사이클 실행

        1. NIA 점수 계산
        2. 실패 분석
        3. 가중치 조정
        4. 히스토리 저장

        Returns:
            Learning cycle results
        """
        logger.info("🚀 Starting daily learning cycle")
        start_time = datetime.now()

        results = {
            "timestamp": start_time.isoformat(),
            "success": False,
            "nia_score": None,
            "weight_adjusted": False,
            "failure_analysis": None
        }

        try:
            # Step 1: Calculate NIA score
            nia_score = self.calculate_nia_score(lookback_days=30)
            results["nia_score"] = nia_score

            if nia_score is None:
                logger.warning("⚠️ No NIA score - skipping learning cycle")
                return results

            # Step 2: Analyze failures
            logger.info("🔍 Analyzing failed predictions")
            failed_predictions = self.agent.collect_failed_predictions(
                lookback_days=7,
                accuracy_threshold=0.5
            )

            if failed_predictions:
                analysis_result = self.agent.analyze_failures_batch(failed_predictions)
                results["failure_analysis"] = analysis_result
                logger.info(f"📊 Analyzed {analysis_result['analyzed']} failures")
            else:
                logger.info("✅ No failed predictions to analyze")

            # Step 3: Adjust weights based on NIA
            current_weights = self.get_current_weights()
            new_weights = self.adjust_weights_based_on_nia(nia_score, current_weights)

            # Check if weights changed
            weights_changed = any(
                abs(new_weights[agent] - current_weights[agent]) > 0.001
                for agent in current_weights.keys()
            )

            if weights_changed:
                reason = f"Auto-adjusted based on NIA score {nia_score:.2%} (Daily Learning Cycle)"
                saved = self.save_weight_adjustment(current_weights, new_weights, reason)
                results["weight_adjusted"] = saved

                if saved:
                    logger.info("✅ Weights adjusted and saved")
                else:
                    logger.error("❌ Failed to save weight adjustment")
            else:
                logger.info("ℹ️ No weight adjustment needed")

            # Success
            results["success"] = True
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Daily learning cycle completed in {duration:.1f}s")

        except Exception as e:
            logger.error(f"❌ Daily learning cycle failed: {e}", exc_info=True)
            results["error"] = str(e)

        return results


def run_scheduler():
    """Entry point for running the scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scheduler = FailureLearningScheduler()
    results = scheduler.run_daily_learning_cycle()

    print("\n" + "="*80)
    print("📊 DAILY LEARNING CYCLE RESULTS")
    print("="*80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Success: {results['success']}")
    print(f"NIA Score: {results['nia_score']:.2%}" if results['nia_score'] else "NIA Score: N/A")
    print(f"Weight Adjusted: {results['weight_adjusted']}")

    if results.get('failure_analysis'):
        fa = results['failure_analysis']
        print(f"Failures Analyzed: {fa['analyzed']}/{fa['total_failures']}")

    print("="*80)

    return results


if __name__ == "__main__":
    run_scheduler()
