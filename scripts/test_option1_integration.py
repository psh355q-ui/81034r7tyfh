"""
옵션 1 통합 테스트: Phase A-D-E 전체 파이프라인

테스트 시나리오:
1. 뉴스 분석 → Deep Reasoning → Consensus 투표
2. DCA 평가 → Consensus 투표 → Position 업데이트
3. Broker 주문 체결 → Position 동기화

작성일: 2025-12-06
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_full_integration_pipeline():
    """
    전체 통합 파이프라인 테스트

    Phase A → Phase D → Phase E 연동
    """
    print("=" * 80)
    print("옵션 1 통합 테스트: Phase A-D-E Full Pipeline")
    print("=" * 80)

    # ============================================================================
    # Step 0: 모듈 Import (에러 처리)
    # ============================================================================

    try:
        from backend.ai.strategies.deep_reasoning_strategy import DeepReasoningStrategy
        from backend.ai.consensus.consensus_engine import ConsensusEngine
        from backend.ai.strategies.dca_strategy import DCAStrategy
        from backend.data.position_tracker import PositionTracker
        from backend.services.news_event_handler import NewsEventHandler
        from backend.services.broker_position_sync import BrokerPositionSync
        from backend.schemas.base_schema import (
            MarketContext, NewsFeatures, MarketSegment, ChipInfo
        )

        logger.info("✓ All modules imported successfully")

    except ImportError as e:
        logger.error(f"✗ Module import failed: {e}")
        print(f"\n❌ 모듈 Import 실패: {e}")
        print("필요한 파일들이 모두 있는지 확인하세요.")
        return

    # ============================================================================
    # Step 1: 초기화
    # ============================================================================

    print("\n" + "=" * 80)
    print("Step 1: 시스템 초기화")
    print("=" * 80)

    # Consensus Engine (Mock - AI 클라이언트 없이)
    consensus_engine = ConsensusEngine()
    logger.info("✓ Consensus Engine initialized (mock mode)")

    # Deep Reasoning Strategy (Consensus 연동)
    deep_reasoning = DeepReasoningStrategy(consensus_engine=consensus_engine)
    logger.info("✓ DeepReasoningStrategy initialized with Consensus")

    # DCA Strategy
    dca_strategy = DCAStrategy(
        max_dca_count=3,
        min_price_drop_pct=10.0,
        max_total_loss_pct=30.0
    )
    logger.info("✓ DCA Strategy initialized")

    # Position Tracker
    position_tracker = PositionTracker()
    logger.info("✓ Position Tracker initialized")

    # News Event Handler
    news_handler = NewsEventHandler(
        dca_strategy=dca_strategy,
        position_tracker=position_tracker,
        consensus_engine=consensus_engine
    )
    logger.info("✓ News Event Handler initialized")

    # Broker-Position Sync (Broker 없이)
    broker_sync = BrokerPositionSync(
        position_tracker=position_tracker,
        kis_broker=None  # Mock
    )
    logger.info("✓ Broker-Position Sync initialized (mock mode)")

    print("\n✓ 모든 모듈 초기화 완료")

    # ============================================================================
    # Step 2: 뉴스 분석 → Deep Reasoning → Consensus
    # ============================================================================

    print("\n" + "=" * 80)
    print("Step 2: 뉴스 분석 → Deep Reasoning → Consensus 투표")
    print("=" * 80)

    test_news_headline = "Google announces Gemini 3 trained entirely on TPU v6e with 50% better efficiency"
    test_news_body = "Google's new TPU v6e offers superior cost-per-token compared to NVIDIA H100 for inference workloads"

    print(f"\n뉴스: {test_news_headline}")

    try:
        result = await deep_reasoning.analyze_news(
            news_headline=test_news_headline,
            news_body=test_news_body,
            use_consensus=True
        )

        print(f"\n[분석 결과]")
        print(f"- Consensus Enabled: {result['consensus_enabled']}")
        print(f"- Original Signals: {len(result['original_signals'])}")

        for signal in result['original_signals']:
            print(f"  • {signal['action']} {signal['ticker']}: {signal['reasoning'][:50]}...")

        if result['consensus_results']:
            print(f"\n[Consensus 투표 결과]")
            for cr in result['consensus_results']:
                status = "✓ APPROVED" if cr['approved'] else "✗ REJECTED"
                print(f"  {status} - {cr['action']} {cr['ticker']} ({cr['votes']}, {cr['consensus_strength']})")

        print(f"\n[최종 승인된 시그널]")
        for signal in result['approved_signals']:
            print(f"  • {signal['action']} {signal['ticker']} (confidence: {signal['confidence']:.0%})")

        print(f"\n✓ 뉴스 분석 완료 (처리시간: {result['processing_time_ms']:.1f}ms)")

    except Exception as e:
        logger.error(f"뉴스 분석 실패: {e}")
        print(f"\n❌ 뉴스 분석 실패: {e}")

    # ============================================================================
    # Step 3: 포지션 생성 → DCA 이벤트
    # ============================================================================

    print("\n" + "=" * 80)
    print("Step 3: 포지션 생성 → DCA 이벤트 처리")
    print("=" * 80)

    # 초기 포지션 생성
    print("\n[3-1] 초기 포지션 생성")
    position_tracker.create_position(
        ticker="NVDA",
        company_name="NVIDIA",
        initial_price=150.0,
        initial_amount=10000.0
    )

    position = position_tracker.get_position("NVDA")
    print(f"  ✓ Position created: NVDA @ ${position.avg_entry_price:.2f}")
    print(f"    - Shares: {position.total_shares:.2f}")
    print(f"    - Invested: ${position.total_invested:.2f}")

    # DCA 이벤트 (가격 10% 하락)
    print("\n[3-2] DCA 트리거 이벤트 (가격 10% 하락)")

    test_market_context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA",
        chip_info=[],
        supply_chain=[],
        unit_economics=None,
        news=NewsFeatures(
            segment=MarketSegment.TRAINING,
            tickers_mentioned=["NVDA"],
            sentiment=0.3,  # 중립
            urgency="medium",
            tone="neutral"
        ),
        risk_factors={},
        market_regime=None
    )

    try:
        dca_result = await news_handler.on_news_event(
            ticker="NVDA",
            news_headline="NVIDIA faces short-term supply chain challenges",
            news_body="Industry sources report temporary delays in H100 production",
            market_context=test_market_context,
            current_price=135.0  # 10% 하락
        )

        print(f"\n[DCA 평가 결과]")
        print(f"  - Has Position: {dca_result['has_position']}")
        print(f"  - DCA Evaluated: {dca_result['dca_evaluated']}")
        print(f"  - DCA Recommended: {dca_result['dca_recommended']}")

        if dca_result.get('dca_decision'):
            print(f"  - Reasoning: {dca_result['dca_decision']['reasoning']}")

        if dca_result.get('consensus_result'):
            cr = dca_result['consensus_result']
            status = "✓ APPROVED" if cr['approved'] else "✗ REJECTED"
            print(f"  - Consensus: {status} ({cr['votes']})")

        if dca_result.get('action_taken'):
            action = dca_result['action_taken']
            print(f"\n✓ DCA 실행: ${action['amount']:.2f} @ ${action['price']:.2f}")

        # 업데이트된 포지션 확인
        position = position_tracker.get_position("NVDA")
        pnl = position.get_unrealized_pnl(current_price=135.0)

        print(f"\n[업데이트된 포지션]")
        print(f"  - Avg Entry Price: ${position.avg_entry_price:.2f}")
        print(f"  - Total Shares: {position.total_shares:.2f}")
        print(f"  - DCA Count: {position.dca_count}")
        print(f"  - Unrealized P&L: ${pnl['pnl']:.2f} ({pnl['pnl_pct']:.2%})")

    except Exception as e:
        logger.error(f"DCA 이벤트 처리 실패: {e}")
        print(f"\n❌ DCA 이벤트 처리 실패: {e}")

    # ============================================================================
    # Step 4: Broker 주문 체결 → Position 동기화
    # ============================================================================

    print("\n" + "=" * 80)
    print("Step 4: Broker 주문 체결 → Position 동기화")
    print("=" * 80)

    print("\n[4-1] 새로운 종목 매수 체결")

    try:
        fill_result1 = await broker_sync.on_order_filled(
            ticker="TSLA",
            company_name="Tesla",
            side="BUY",
            quantity=5,
            avg_price=250.0,
            order_id="KIS20241206001",
            filled_at=datetime.now()
        )

        print(f"  - Order ID: {fill_result1['order_id']}")
        print(f"  - Action: {fill_result1['action']}")
        print(f"  - Position Updated: {fill_result1['position_updated']}")

        # TSLA 포지션 확인
        tsla_position = position_tracker.get_position("TSLA")
        if tsla_position:
            print(f"  ✓ TSLA Position created: {tsla_position.total_shares} shares @ ${tsla_position.avg_entry_price:.2f}")

    except Exception as e:
        logger.error(f"Broker 동기화 실패: {e}")
        print(f"\n❌ Broker 동기화 실패: {e}")

    # ============================================================================
    # Step 5: 전체 포트폴리오 요약
    # ============================================================================

    print("\n" + "=" * 80)
    print("Step 5: 전체 포트폴리오 요약")
    print("=" * 80)

    all_positions = position_tracker.get_all_positions()

    print(f"\n총 {len(all_positions)}개 포지션:")

    current_prices = {
        "NVDA": 135.0,
        "TSLA": 250.0
    }

    for pos in all_positions:
        current_price = current_prices.get(pos.ticker, pos.avg_entry_price)
        pnl = pos.get_unrealized_pnl(current_price=current_price)

        print(f"\n  [{pos.ticker}]")
        print(f"    - Shares: {pos.total_shares:.2f}")
        print(f"    - Avg Entry: ${pos.avg_entry_price:.2f}")
        print(f"    - Current: ${current_price:.2f}")
        print(f"    - DCA Count: {pos.dca_count}")
        print(f"    - P&L: ${pnl['pnl']:.2f} ({pnl['pnl_pct']:.2%})")

    # ============================================================================
    # 완료
    # ============================================================================

    print("\n" + "=" * 80)
    print("✓ 옵션 1 통합 테스트 완료")
    print("=" * 80)

    print("\n[통합 완료된 기능]")
    print("  ✓ Deep Reasoning Strategy → Consensus 연동")
    print("  ✓ 뉴스 이벤트 → DCA 자동 평가")
    print("  ✓ Position Tracker ↔ Broker 동기화")

    print("\n[다음 단계]")
    print("  → 옵션 2: 자동 거래 시스템 (Consensus 승인 시 자동 주문)")
    print("  → 옵션 3: 백테스팅 & 성과 분석")
    print("  → 실제 환경 테스트 (실제 AI 클라이언트 연동)")


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    asyncio.run(test_full_integration_pipeline())
