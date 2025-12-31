"""
Price Tracking Verifier

1h/1d/3d 후 실제 가격을 측정하여 AI 해석의 정확도를 검증하는 자동화 스크립트

실행:
- 1시간마다 스케줄러가 호출 (scheduler.py)
- news_market_reactions 테이블의 pending 검증 조회
- 실제 가격 조회 (KIS API)
- interpretation_correct 판정
- DB 업데이트

Integration:
- scheduler.py: schedule.every().hour.do(self.run_price_tracking_verification)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

from backend.database.repository import (
    NewsInterpretationRepository,
    NewsMarketReactionRepository,
    get_sync_session
)
from backend.database.models import NewsMarketReaction

# KIS API integration
from backend.brokers.kis_broker import KISBroker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceTrackingVerifier:
    """
    가격 추적 검증자

    역할:
    1. 1h/1d/3d 전에 생성된 해석 중 아직 검증 안된 것 조회
    2. 현재 가격 조회 (KIS API)
    3. 가격 변화율 계산
    4. AI 해석 정확도 판정
    5. DB 업데이트
    """

    def __init__(self):
        # KIS API client initialization (Paper Trading)
        self.kis_broker = KISBroker(
            account_no=os.getenv("KIS_PAPER_ACCOUNT", "50096724"),
            product_code='01',
            is_virtual=True
        )
        logger.info("✅ PriceTrackingVerifier initialized with KIS Broker")

    async def verify_interpretations(self, time_horizon: str = "1h") -> Dict:
        """
        특정 time horizon의 해석 검증

        Args:
            time_horizon: "1h" | "1d" | "3d"

        Returns:
            {
                "verified_count": 5,
                "correct_count": 4,
                "accuracy": 0.8
            }
        """
        logger.info(f"🔍 Starting {time_horizon} verification")

        with get_sync_session() as session:
            reaction_repo = NewsMarketReactionRepository(session)

            # 1. Get pending verifications
            pending = reaction_repo.get_pending_verifications(time_horizon)

            if not pending:
                logger.info(f"✅ No pending {time_horizon} verifications")
                return {
                    "verified_count": 0,
                    "correct_count": 0,
                    "accuracy": 0.0
                }

            logger.info(f"📊 Found {len(pending)} pending {time_horizon} verifications")

            verified_count = 0
            correct_count = 0

            # 2. Verify each reaction
            for reaction in pending:
                try:
                    # Get current price
                    current_price = await self._get_current_price(reaction.ticker)

                    if current_price is None:
                        logger.warning(f"⚠️ Failed to get price for {reaction.ticker}")
                        continue

                    # Calculate price change (convert Decimal to float)
                    price_at_news_float = float(reaction.price_at_news) if reaction.price_at_news else 0.0

                    if price_at_news_float == 0.0:
                        logger.warning(f"⚠️ price_at_news is zero for {reaction.ticker}, skipping")
                        continue

                    price_change = ((current_price - price_at_news_float) / price_at_news_float) * 100

                    # Check correctness
                    interpretation = reaction.interpretation
                    correct = self._check_correctness(
                        interpretation.headline_bias,
                        price_change
                    )

                    # Calculate confidence justification
                    confidence_justified = self._check_confidence_justified(
                        interpretation.confidence,
                        interpretation.expected_impact,
                        abs(price_change)
                    )

                    # Calculate magnitude accuracy
                    magnitude_accuracy = self._calculate_magnitude_accuracy(
                        interpretation.expected_impact,
                        abs(price_change)
                    )

                    # Update DB
                    update_data = {
                        "verified_at": datetime.now()
                    }

                    if time_horizon == "1h":
                        update_data["price_1h_after"] = current_price
                        update_data["actual_price_change_1h"] = price_change
                    elif time_horizon == "1d":
                        update_data["price_1d_after"] = current_price
                        update_data["actual_price_change_1d"] = price_change
                    elif time_horizon == "3d":
                        update_data["price_3d_after"] = current_price
                        update_data["actual_price_change_3d"] = price_change

                    # Only update correctness on 1d verification (main metric)
                    if time_horizon == "1d":
                        update_data["interpretation_correct"] = correct
                        update_data["confidence_justified"] = confidence_justified
                        update_data["magnitude_accuracy"] = magnitude_accuracy

                    reaction_repo.update(reaction, update_data)

                    verified_count += 1
                    if correct:
                        correct_count += 1

                    logger.info(
                        f"✅ Verified {reaction.ticker}: "
                        f"{interpretation.headline_bias} → {price_change:+.2f}% "
                        f"({'✓' if correct else '✗'})"
                    )

                except Exception as e:
                    logger.error(f"❌ Error verifying {reaction.ticker}: {e}", exc_info=True)

            accuracy = correct_count / verified_count if verified_count > 0 else 0.0

            logger.info(
                f"📈 {time_horizon} Verification Complete: "
                f"{correct_count}/{verified_count} correct ({accuracy*100:.1f}%)"
            )

            return {
                "verified_count": verified_count,
                "correct_count": correct_count,
                "accuracy": round(accuracy, 2)
            }

    async def verify_all_horizons(self) -> Dict:
        """
        모든 time horizon 검증 (1h, 1d, 3d)

        Returns:
            {
                "1h": {...},
                "1d": {...},
                "3d": {...}
            }
        """
        logger.info("🚀 Starting all horizon verification")

        results = {}

        for horizon in ["1h", "1d", "3d"]:
            results[horizon] = await self.verify_interpretations(horizon)

        logger.info("✅ All horizon verification complete")
        return results

    # ========== Private Helper Methods ==========

    async def _get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price from KIS API

        Args:
            ticker: 종목 코드

        Returns:
            float: 현재 가격 (실패 시 None)
        """
        try:
            # KIS Broker (sync) call wrapped in async
            price_data = await asyncio.to_thread(
                self.kis_broker.get_price,
                ticker,
                'NASDAQ'
            )

            if price_data and 'current_price' in price_data:
                return price_data['current_price']
            else:
                logger.warning(f"⚠️ No price data for {ticker}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get price for {ticker}: {e}")
            return None

    def _check_correctness(self, headline_bias: str, actual_price_change: float) -> bool:
        """
        Check if interpretation was correct

        Args:
            headline_bias: "BULLISH" | "BEARISH" | "NEUTRAL"
            actual_price_change: 실제 가격 변화율 (%)

        Returns:
            bool: 정확 여부
        """
        if headline_bias == "BULLISH":
            return actual_price_change > 1.0  # 1% 이상 상승
        elif headline_bias == "BEARISH":
            return actual_price_change < -1.0  # 1% 이상 하락
        else:  # NEUTRAL
            return -1.0 <= actual_price_change <= 1.0  # ±1% 이내

    def _check_confidence_justified(
        self, confidence: int, expected_impact: str, actual_magnitude: float
    ) -> bool:
        """
        Check if high confidence was justified

        Args:
            confidence: 0-100
            expected_impact: "HIGH" | "MEDIUM" | "LOW"
            actual_magnitude: 실제 가격 변화 크기 (%)

        Returns:
            bool: confidence가 justified 되었는지
        """
        # High confidence (80+) should match high impact
        if confidence >= 80:
            if expected_impact == "HIGH":
                return actual_magnitude >= 5.0
            else:
                return actual_magnitude >= 2.0

        # Medium confidence (50-79) should match medium+ impact
        elif confidence >= 50:
            return actual_magnitude >= 2.0

        # Low confidence (<50) - always justified
        else:
            return True

    def _calculate_magnitude_accuracy(
        self, expected_impact: str, actual_magnitude: float
    ) -> float:
        """
        Calculate magnitude accuracy score

        Args:
            expected_impact: "HIGH" (5%+) | "MEDIUM" (2-5%) | "LOW" (<2%)
            actual_magnitude: 실제 가격 변화 크기 (%)

        Returns:
            float: 0.0 ~ 1.0 (정확도)
        """
        if expected_impact == "HIGH":
            if actual_magnitude >= 5.0:
                return 1.0  # Perfect
            elif actual_magnitude >= 2.0:
                return 0.5  # Partial
            else:
                return 0.0  # Wrong

        elif expected_impact == "MEDIUM":
            if 2.0 <= actual_magnitude < 5.0:
                return 1.0  # Perfect
            elif actual_magnitude >= 1.0:
                return 0.7  # Close
            else:
                return 0.3  # Partial

        else:  # LOW
            if actual_magnitude < 2.0:
                return 1.0  # Perfect
            elif actual_magnitude < 5.0:
                return 0.5  # Partial
            else:
                return 0.0  # Wrong


# ========== Standalone Execution ==========

async def main():
    """
    Manual execution for testing
    """
    verifier = PriceTrackingVerifier()

    # Verify all horizons
    results = await verifier.verify_all_horizons()

    print("="*60)
    print("📊 Price Tracking Verification Results")
    print("="*60)

    for horizon, result in results.items():
        print(f"\n{horizon} Verification:")
        print(f"  Verified: {result['verified_count']}")
        print(f"  Correct: {result['correct_count']}")
        print(f"  Accuracy: {result['accuracy']*100:.1f}%")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
