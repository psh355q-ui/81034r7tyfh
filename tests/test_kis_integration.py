"""
KIS Integration Test - Phase A/B/C/D + 한국투자증권 통합 테스트

전체 파이프라인 테스트:
Security → Phase A → Phase C → Phase B → KIS Order (DRY RUN)

작성일: 2025-12-03
"""

import sys
sys.path.insert(0, '.')

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from backend.api.kis_integration_router import (
    KISAutoTradeRequest,
    kis_auto_trade,
    get_kis_balance,
    kis_health_check,
    KIS_BROKER_AVAILABLE
)


async def test_kis_health():
    """Test 1: KIS 연동 상태 확인"""
    print("\n" + "=" * 70)
    print("TEST 1: KIS 연동 상태 확인")
    print("=" * 70)

    try:
        result = await kis_health_check()

        print(f"KIS Available: {result['kis_available']}")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")

        if result['kis_available']:
            print("✅ KIS API 연동 정상")
        else:
            print("❌ KIS API 사용 불가 - KIS_API_PATH 확인 필요")
            print("   (테스트는 계속 진행됩니다 - Dry Run 모드)")

        return result['kis_available']

    except Exception as e:
        logger.error(f"Health check 오류: {e}")
        return False


async def test_phase_pipeline_dry_run():
    """Test 2: Phase 파이프라인 테스트 (Dry Run)"""
    print("\n" + "=" * 70)
    print("TEST 2: Phase 파이프라인 테스트 (Dry Run)")
    print("=" * 70)

    # Test news: NVIDIA Blackwell B200 발표
    request = KISAutoTradeRequest(
        headline="NVIDIA announces Blackwell B200 GPU with breakthrough training performance",
        body="NVIDIA revealed its next-generation Blackwell B200 GPU, setting new records for AI training workloads.",
        url="https://investing.com/news/nvidia-blackwell",
        is_virtual=True,  # 모의투자
        dry_run=True  # 실제 주문 안 함 (분석만)
    )

    print(f"\n입력 뉴스:")
    print(f"  Headline: {request.headline}")
    print(f"  URL: {request.url}")
    print(f"  Dry Run: {request.dry_run}")

    try:
        result = await kis_auto_trade(request)

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🔒 SECURITY VALIDATION")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Original: {result.analysis.original_headline}")
        print(f"  Sanitized: {result.analysis.sanitized_headline}")
        print(f"  Threats Detected: {result.analysis.threats_detected}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📊 PHASE A: 뉴스 분석")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Segment: {result.analysis.segment}")
        print(f"  Sentiment: {result.analysis.sentiment:.2f}")
        print(f"  Tickers: {', '.join(result.analysis.tickers_mentioned)}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🤖 PHASE C: AI 3-Way 토론")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Final Ticker: {result.analysis.final_ticker}")
        print(f"  Final Action: {result.analysis.final_action}")
        print(f"  Confidence: {result.analysis.final_confidence:.2%}")
        print(f"  Consensus: {result.analysis.consensus_level:.2%}")
        print(f"  Model Votes: {result.analysis.model_votes}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 PHASE C: 편향 탐지")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Bias Score: {result.analysis.bias_score:.2%}")
        print(f"  Is Biased: {result.analysis.is_biased}")
        if result.analysis.corrected_confidence:
            print(f"  Original Confidence: {result.analysis.final_confidence:.2%}")
            print(f"  Corrected Confidence: {result.analysis.corrected_confidence:.2%}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"⚠️  PHASE B: 매크로 리스크")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  PERI Score: {result.analysis.peri_score:.1f}")
        print(f"  PERI Level: {result.analysis.peri_level}")
        print(f"  Buffett Index: {result.analysis.buffett_index:.1f}%")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📝 PHASE B: Signal → Order")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Order Created: {result.analysis.order_created}")
        if result.analysis.order_created:
            print(f"  Order Side: {result.analysis.order_side.upper()}")
            print(f"  Quantity: {result.analysis.order_quantity}")

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"💼 KIS BROKER STATUS")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  KIS Enabled: {result.kis_enabled}")
        print(f"  Order Executed: {result.kis_order_executed}")
        print(f"  Mode: {result.mode}")
        print(f"  Timestamp: {result.timestamp}")

        if result.analysis.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.analysis.warnings:
                print(f"  - {warning}")

        print(f"\n✅ Phase 파이프라인 테스트 성공!")
        return True

    except Exception as e:
        logger.error(f"Pipeline test 오류: {e}", exc_info=True)
        print(f"\n❌ Phase 파이프라인 테스트 실패: {e}")
        return False


async def test_kis_balance(kis_available: bool):
    """Test 3: KIS 계좌 잔고 조회"""
    if not kis_available:
        print("\n" + "=" * 70)
        print("TEST 3: KIS 계좌 잔고 조회 (SKIPPED - KIS API 없음)")
        print("=" * 70)
        return

    print("\n" + "=" * 70)
    print("TEST 3: KIS 계좌 잔고 조회")
    print("=" * 70)

    try:
        result = await get_kis_balance(is_virtual=True)

        print(f"\n계좌 정보:")
        print(f"  Broker: {result.broker}")
        print(f"  Account: {result.account}")
        print(f"  Mode: {result.mode}")
        print(f"  Total Value: ${result.total_value:,.2f}")
        print(f"  Cash: ${result.cash:,.2f}")
        print(f"  Positions: {len(result.positions)}")

        if result.positions:
            print(f"\n보유 종목:")
            for pos in result.positions[:5]:
                print(f"  - {pos['symbol']}: {pos['quantity']}주")

        print(f"\n✅ 잔고 조회 성공!")

    except Exception as e:
        logger.error(f"Balance check 오류: {e}")
        print(f"\n⚠️  잔고 조회 실패: {e}")
        print("  (계좌번호 또는 KIS API 설정 확인 필요)")


async def main():
    """메인 테스트 실행"""
    print("=" * 70)
    print("🚀 KIS Integration Test")
    print("=" * 70)
    print(f"시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test 1: Health Check
    kis_available = await test_kis_health()

    # Test 2: Phase Pipeline (Dry Run)
    pipeline_ok = await test_phase_pipeline_dry_run()

    # Test 3: KIS Balance (KIS가 사용 가능할 때만)
    await test_kis_balance(kis_available)

    # Summary
    print("\n" + "=" * 70)
    print("📊 테스트 요약")
    print("=" * 70)
    print(f"  KIS API Available: {'✅' if kis_available else '❌'}")
    print(f"  Phase Pipeline: {'✅' if pipeline_ok else '❌'}")
    print(f"  전체 통합: {'✅' if pipeline_ok else '❌'}")

    print("\n" + "=" * 70)
    print("✅ 테스트 완료!")
    print("=" * 70)

    if not kis_available:
        print("\n⚠️  KIS API가 설정되지 않았습니다.")
        print("   하지만 Phase 파이프라인은 정상 작동합니다.")
        print("   실제 주문을 원하시면 KIS API를 설정하세요.")
        print()
        print("   참고: docs/KIS_Integration.md")


if __name__ == "__main__":
    asyncio.run(main())
