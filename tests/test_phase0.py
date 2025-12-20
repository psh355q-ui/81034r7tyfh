"""
Phase 0 BaseSchema 검증 스크립트

실행: python test_phase0.py
"""

import sys
import traceback
from datetime import datetime


def test_imports():
    """Import 테스트"""
    print("[1/5] Testing imports...")
    try:
        from backend.schemas.base_schema import (
            ChipInfo,
            SupplyChainEdge,
            RelationType,
            UnitEconomics,
            NewsFeatures,
            MarketSegment,
            PolicyRisk,
            MarketContext,
            MarketRegime,
            MultimodelInput,
            InvestmentSignal,
            SignalAction,
        )
        print("      SUCCESS: All schemas imported successfully")
        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def test_chip_info():
    """ChipInfo 생성 테스트"""
    print("\n[2/5] Testing ChipInfo...")
    try:
        from backend.schemas.base_schema import ChipInfo

        # NVIDIA H100
        h100 = ChipInfo(
            model="NVIDIA H100",
            vendor="NVIDIA",
            process_node="4nm",
            perf_tflops=1979.0,
            mem_bw_gbps=3350.0,
            tdp_watts=700.0,
            cost_usd=30000.0,
            efficiency_score=0.92,
            tokens_per_sec=15000.0,
            segment="training"
        )

        assert h100.model == "NVIDIA H100"
        assert h100.efficiency_score == 0.92
        print(f"      SUCCESS: Created {h100.model} (efficiency: {h100.efficiency_score})")

        # Google TPU
        tpu = ChipInfo(
            model="Google TPU v6e",
            vendor="Google",
            segment="inference"
        )
        assert tpu.vendor == "Google"
        print(f"      SUCCESS: Created {tpu.model}")

        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def test_policy_risk():
    """PolicyRisk PERI 자동 계산 테스트"""
    print("\n[3/5] Testing PolicyRisk (PERI auto-calculation)...")
    try:
        from backend.schemas.base_schema import PolicyRisk

        risk = PolicyRisk(
            fed_conflict_score=0.45,
            successor_signal_score=0.30,
            gov_fed_tension_score=0.60,
            election_risk_score=0.25,
            bond_volatility_score=0.35,
            policy_uncertainty_score=0.40
        )

        expected_peri = (
            0.45 * 0.25 +
            0.30 * 0.20 +
            0.60 * 0.20 +
            0.25 * 0.15 +
            0.35 * 0.10 +
            0.40 * 0.10
        ) * 100

        assert abs(risk.peri - expected_peri) < 0.01
        print(f"      SUCCESS: PERI auto-calculated = {risk.peri:.2f} (expected: {expected_peri:.2f})")

        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def test_market_context():
    """MarketContext 통합 테스트"""
    print("\n[4/5] Testing MarketContext...")
    try:
        from backend.schemas.base_schema import (
            MarketContext,
            ChipInfo,
            SupplyChainEdge,
            RelationType,
            UnitEconomics,
            NewsFeatures,
            MarketSegment,
            PolicyRisk,
            MarketRegime,
        )

        context = MarketContext(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            chip_info=[
                ChipInfo(model="H100", vendor="NVIDIA", segment="training")
            ],
            supply_chain=[
                SupplyChainEdge(
                    source="TSM",
                    target="NVDA",
                    relation=RelationType.SUPPLIER,
                    confidence=0.98
                )
            ],
            unit_economics=UnitEconomics(
                token_cost=1.2e-8,
                tco_monthly=1250.0
            ),
            news=NewsFeatures(
                headline="NVIDIA announces new GPU",
                segment=MarketSegment.TRAINING,
                sentiment=0.85
            ),
            risk_factors={
                "geopolitical": 0.3,
                "supply_chain": 0.2
            },
            policy_risk=PolicyRisk(peri=35.0),
            market_regime=MarketRegime.BULL
        )

        assert context.ticker == "NVDA"
        assert len(context.chip_info) == 1
        assert len(context.supply_chain) == 1
        assert context.market_regime == MarketRegime.BULL

        print(f"      SUCCESS: MarketContext for {context.ticker}")
        print(f"               - Chip count: {len(context.chip_info)}")
        print(f"               - Supply chain edges: {len(context.supply_chain)}")
        print(f"               - Market regime: {context.market_regime.value}")
        print(f"               - PERI: {context.policy_risk.peri}")

        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def test_full_pipeline():
    """전체 파이프라인 통합 테스트"""
    print("\n[5/5] Testing Full Pipeline (News -> Context -> Signal)...")
    try:
        from backend.schemas.base_schema import (
            NewsFeatures,
            MarketSegment,
            ChipInfo,
            SupplyChainEdge,
            RelationType,
            MarketContext,
            MarketRegime,
            MultimodelInput,
            InvestmentSignal,
            SignalAction,
        )

        # 1. 뉴스 입력
        news = NewsFeatures(
            headline="NVIDIA Blackwell GPU breaks training records",
            segment=MarketSegment.TRAINING,
            sentiment=0.9,
            tickers_mentioned=["NVDA", "TSM"]
        )

        # 2. MarketContext 생성
        context = MarketContext(
            ticker="NVDA",
            company_name="NVIDIA",
            chip_info=[
                ChipInfo(model="B200", vendor="NVIDIA", segment="training", efficiency_score=0.95)
            ],
            supply_chain=[
                SupplyChainEdge(source="TSM", target="NVDA", relation=RelationType.SUPPLIER, confidence=0.98)
            ],
            news=news,
            market_regime=MarketRegime.BULL
        )

        # 3. Multi-AI 입력
        multimodel = MultimodelInput(
            claude_context=context,
            chatgpt_context=context,
            gemini_context=context,
            ensemble_weights={
                "claude": 0.5,
                "chatgpt": 0.3,
                "gemini": 0.2
            }
        )

        # 4. 투자 시그널
        signal = InvestmentSignal(
            ticker="NVDA",
            action=SignalAction.BUY,
            confidence=0.9,
            reasoning="Training market leader with strong supply chain",
            position_size=0.2,
            metadata={
                "segment": "training",
                "hidden_beneficiaries": ["TSM", "AVGO"]
            }
        )

        # 검증
        assert news.segment == MarketSegment.TRAINING
        assert context.ticker == "NVDA"
        assert multimodel.ensemble_weights["claude"] == 0.5
        assert signal.action == SignalAction.BUY

        print(f"      SUCCESS: Full pipeline test passed")
        print(f"               News: {news.headline}")
        print(f"               Context: {context.ticker} ({context.market_regime.value})")
        print(f"               Signal: {signal.action.value} @ {signal.confidence}")
        print(f"               Ensemble weights: Claude={multimodel.ensemble_weights['claude']}")

        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def test_json_serialization():
    """JSON 직렬화/역직렬화 테스트"""
    print("\n[BONUS] Testing JSON serialization...")
    try:
        from backend.schemas.base_schema import MarketContext, MarketRegime

        # 원본 생성
        original = MarketContext(
            ticker="NVDA",
            company_name="NVIDIA",
            market_regime=MarketRegime.BULL
        )

        # JSON 직렬화
        json_str = original.model_dump_json()
        assert "NVDA" in json_str
        assert "bull" in json_str

        # JSON 역직렬화
        restored = MarketContext.model_validate_json(json_str)
        assert restored.ticker == "NVDA"
        assert restored.market_regime == MarketRegime.BULL

        print(f"      SUCCESS: JSON roundtrip test passed")
        print(f"               Original: {original.ticker}")
        print(f"               Restored: {restored.ticker}")

        return True
    except Exception as e:
        print(f"      FAILED: {e}")
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("=" * 70)
    print("Phase 0: BaseSchema Validation Test")
    print("=" * 70)

    results = []

    # 테스트 실행
    results.append(("Imports", test_imports()))
    results.append(("ChipInfo", test_chip_info()))
    results.append(("PolicyRisk", test_policy_risk()))
    results.append(("MarketContext", test_market_context()))
    results.append(("Full Pipeline", test_full_pipeline()))
    results.append(("JSON Serialization", test_json_serialization()))

    # 결과 출력
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    passed = 0
    failed = 0

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name:<25} [{status}]")

        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n✓ Phase 0 BaseSchema validation SUCCESSFUL!")
        print("  Ready to proceed to Phase A (AI Chip Analysis)")
        return 0
    else:
        print(f"\n✗ Phase 0 validation FAILED ({failed} test(s) failed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
