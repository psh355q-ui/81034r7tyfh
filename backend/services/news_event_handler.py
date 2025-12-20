"""
News Event Handler - 뉴스 이벤트 → DCA 자동 평가

Phase E 통합 (옵션 1 - Task 1.2)
뉴스 이벤트 발생 시 포지션 보유 종목에 대해 DCA 평가 자동 실행

작성일: 2025-12-06
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.schemas.base_schema import MarketContext, SignalAction
from backend.ai.strategies.dca_strategy import DCAStrategy, DCADecision
from backend.data.position_tracker import PositionTracker, Position
from backend.ai.consensus.consensus_engine import ConsensusEngine

logger = logging.getLogger(__name__)


class NewsEventHandler:
    """
    뉴스 이벤트 핸들러

    뉴스 발생 시:
    1. 포지션 보유 종목 필터링
    2. DCA 조건 체크
    3. Consensus 투표
    4. 승인 시 Position에 DCA 기록
    """

    def __init__(
        self,
        dca_strategy: DCAStrategy,
        position_tracker: PositionTracker,
        consensus_engine: Optional[ConsensusEngine] = None
    ):
        """
        Initialize News Event Handler

        Args:
            dca_strategy: DCA 전략 인스턴스
            position_tracker: Position 추적기
            consensus_engine: Consensus Engine (옵션)
        """
        self.dca_strategy = dca_strategy
        self.position_tracker = position_tracker
        self.consensus_engine = consensus_engine

        logger.info("NewsEventHandler initialized")

    async def on_news_event(
        self,
        ticker: str,
        news_headline: str,
        news_body: str,
        market_context: MarketContext,
        current_price: float
    ) -> Dict[str, Any]:
        """
        뉴스 이벤트 처리

        Args:
            ticker: 종목 티커
            news_headline: 뉴스 헤드라인
            news_body: 뉴스 본문
            market_context: 시장 컨텍스트
            current_price: 현재 가격

        Returns:
            처리 결과
        """
        logger.info(f"Processing news event for {ticker}: {news_headline[:50]}...")

        result = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "news_headline": news_headline,
            "has_position": False,
            "dca_evaluated": False,
            "dca_recommended": False,
            "consensus_approved": False,
            "action_taken": None
        }

        # 1. 포지션 보유 여부 체크
        position = self.position_tracker.get_position(ticker)

        if position is None:
            logger.info(f"No position for {ticker}, skipping DCA evaluation")
            return result

        result["has_position"] = True
        result["position_summary"] = {
            "avg_entry_price": position.avg_entry_price,
            "total_shares": position.total_shares,
            "dca_count": position.dca_count,
            "total_invested": position.total_invested
        }

        # 2. DCA 조건 체크
        logger.info(f"Position found for {ticker}, evaluating DCA...")
        result["dca_evaluated"] = True

        dca_decision = await self.dca_strategy.should_dca(
            ticker=ticker,
            current_price=current_price,
            avg_entry_price=position.avg_entry_price,
            dca_count=position.dca_count,
            total_invested=position.total_invested,
            context=market_context
        )

        result["dca_decision"] = {
            "should_dca": dca_decision.should_dca,
            "reasoning": dca_decision.reasoning,
            "position_size": dca_decision.position_size,
            "confidence": dca_decision.confidence,
            "risk_factors": dca_decision.risk_factors
        }

        if not dca_decision.should_dca:
            logger.info(f"DCA not recommended for {ticker}: {dca_decision.reasoning}")
            return result

        result["dca_recommended"] = True

        # 3. Consensus 투표 (DCA는 3/3 필요)
        if self.consensus_engine is not None:
            logger.info(f"Running Consensus vote for DCA on {ticker}...")

            try:
                consensus_result = await self.consensus_engine.vote_on_signal(
                    context=market_context,
                    action="DCA",
                    additional_info={
                        "current_price": current_price,
                        "avg_entry_price": position.avg_entry_price,
                        "dca_count": position.dca_count,
                        "total_invested": position.total_invested,
                        "dca_reasoning": dca_decision.reasoning
                    }
                )

                result["consensus_result"] = {
                    "approved": consensus_result.approved,
                    "votes": f"{consensus_result.approve_count}/{consensus_result.total_votes}",
                    "consensus_strength": consensus_result.consensus_strength.value,
                    "individual_votes": [
                        {
                            "ai_name": vote.ai_name,
                            "decision": vote.decision.value,
                            "reasoning": vote.reasoning
                        }
                        for vote in consensus_result.votes
                    ]
                }

                if not consensus_result.approved:
                    logger.info(f"Consensus REJECTED DCA for {ticker}")
                    return result

                result["consensus_approved"] = True
                logger.info(f"✓ Consensus APPROVED DCA for {ticker}")

            except Exception as e:
                logger.error(f"Consensus voting error: {e}")
                result["consensus_error"] = str(e)
                return result

        else:
            # Consensus 엔진 없으면 자동 승인
            logger.warning("No Consensus Engine, auto-approving DCA")
            result["consensus_approved"] = True

        # 4. DCA 실행 (Position에 기록)
        dca_amount = position.total_invested * (dca_decision.position_size or 0.5)

        logger.info(f"Adding DCA entry to {ticker}: ${dca_amount:.2f} @ ${current_price:.2f}")

        self.position_tracker.add_dca_entry(
            ticker=ticker,
            price=current_price,
            amount=dca_amount,
            reasoning=dca_decision.reasoning
        )

        result["action_taken"] = {
            "type": "DCA",
            "amount": dca_amount,
            "price": current_price,
            "shares": dca_amount / current_price if current_price > 0 else 0
        }

        logger.info(f"✓ DCA executed for {ticker}")

        return result

    async def batch_process_news(
        self,
        news_items: List[Dict[str, Any]],
        price_lookup: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        뉴스 배치 처리

        Args:
            news_items: 뉴스 항목 리스트 (ticker, headline, body, context 포함)
            price_lookup: 티커별 현재 가격 딕셔너리

        Returns:
            처리 결과 리스트
        """
        results = []

        for news_item in news_items:
            ticker = news_item.get("ticker")
            headline = news_item.get("headline", "")
            body = news_item.get("body", "")
            context = news_item.get("market_context")

            if ticker is None or context is None:
                logger.warning(f"Skipping news item: missing ticker or context")
                continue

            current_price = price_lookup.get(ticker)
            if current_price is None:
                logger.warning(f"Skipping {ticker}: no price data")
                continue

            result = await self.on_news_event(
                ticker=ticker,
                news_headline=headline,
                news_body=body,
                market_context=context,
                current_price=current_price
            )

            results.append(result)

        logger.info(f"Processed {len(results)} news events")
        return results


# ============================================================================
# 팩토리 함수
# ============================================================================

def create_news_event_handler(
    dca_strategy: Optional[DCAStrategy] = None,
    position_tracker: Optional[PositionTracker] = None,
    consensus_engine: Optional[ConsensusEngine] = None
) -> NewsEventHandler:
    """
    NewsEventHandler 팩토리 함수

    Args:
        dca_strategy: DCA 전략 (없으면 기본값 생성)
        position_tracker: Position Tracker (없으면 기본값 생성)
        consensus_engine: Consensus Engine (옵션)

    Returns:
        NewsEventHandler 인스턴스
    """
    if dca_strategy is None:
        dca_strategy = DCAStrategy()

    if position_tracker is None:
        position_tracker = PositionTracker()

    return NewsEventHandler(
        dca_strategy=dca_strategy,
        position_tracker=position_tracker,
        consensus_engine=consensus_engine
    )


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    import asyncio
    from backend.schemas.base_schema import NewsFeatures, MarketSegment

    async def test():
        print("=" * 70)
        print("NewsEventHandler Test")
        print("=" * 70)

        # 초기화
        handler = create_news_event_handler()

        # 테스트 포지션 생성
        handler.position_tracker.create_position(
            ticker="NVDA",
            company_name="NVIDIA",
            initial_price=150.0,
            initial_amount=10000.0
        )

        # 테스트 뉴스
        market_context = MarketContext(
            ticker="NVDA",
            company_name="NVIDIA",
            chip_info=[],
            supply_chain=[],
            unit_economics=None,
            news=NewsFeatures(
                segment=MarketSegment.TRAINING,
                tickers_mentioned=["NVDA"],
                sentiment=0.3,  # 중립/약간 부정
                urgency="medium",
                tone="neutral"
            ),
            risk_factors={},
            market_regime=None
        )

        # 뉴스 이벤트 처리 (가격 10% 하락)
        result = await handler.on_news_event(
            ticker="NVDA",
            news_headline="NVIDIA faces short-term supply chain challenges",
            news_body="Industry sources report temporary delays in H100 production",
            market_context=market_context,
            current_price=135.0  # 10% 하락
        )

        print(f"\n[Result]")
        print(f"Has Position: {result['has_position']}")
        print(f"DCA Evaluated: {result['dca_evaluated']}")
        print(f"DCA Recommended: {result['dca_recommended']}")

        if result.get("dca_decision"):
            print(f"DCA Reasoning: {result['dca_decision']['reasoning']}")

        if result.get("action_taken"):
            print(f"Action: {result['action_taken']['type']} @ ${result['action_taken']['price']:.2f}")
            print(f"Amount: ${result['action_taken']['amount']:.2f}")

    asyncio.run(test())
