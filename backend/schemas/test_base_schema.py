"""
BaseSchema 테스트

Phase 0: Foundation
모든 스키마의 유효성 검사 및 예제 테스트

실행: pytest backend/schemas/test_base_schema.py -v
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from .base_schema import (
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


# ═══════════════════════════════════════════════════════════════
# [1] ChipInfo 테스트
# ═══════════════════════════════════════════════════════════════

def test_chip_info_nvidia_h100():
    """NVIDIA H100 칩 정보 생성 테스트"""
    chip = ChipInfo(
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

    assert chip.model == "NVIDIA H100"
    assert chip.vendor == "NVIDIA"
    assert chip.efficiency_score == 0.92
    assert chip.segment == "training"


def test_chip_info_google_tpu():
    """Google TPU v6e 칩 정보 생성 테스트"""
    chip = ChipInfo(
        model="Google TPU v6e",
        vendor="Google",
        process_node="5nm",
        perf_tflops=918.0,
        mem_bw_gbps=4800.0,
        tdp_watts=500.0,
        cost_usd=28000.0,
        efficiency_score=0.88,
        tokens_per_sec=20000.0,
        segment="inference"
    )

    assert chip.segment == "inference"
    assert chip.vendor == "Google"


def test_chip_info_minimal():
    """최소 정보로 ChipInfo 생성 테스트"""
    chip = ChipInfo()
    assert chip.model is None
    assert chip.vendor is None


def test_chip_info_efficiency_validation():
    """효율 점수 범위 검증 테스트"""
    # 정상 범위 (0~1)
    chip = ChipInfo(efficiency_score=0.5)
    assert chip.efficiency_score == 0.5

    # 범위 초과 (예외 발생 예상)
    with pytest.raises(ValidationError):
        ChipInfo(efficiency_score=1.5)


# ═══════════════════════════════════════════════════════════════
# [2] SupplyChainEdge 테스트
# ═══════════════════════════════════════════════════════════════

def test_supply_chain_edge_tsm_to_nvda():
    """TSM → NVDA 공급 관계 테스트"""
    edge = SupplyChainEdge(
        source="TSM",
        target="NVDA",
        relation=RelationType.SUPPLIER,
        confidence=0.98,
        context="TSMC manufactures NVIDIA GPUs using 4nm process"
    )

    assert edge.source == "TSM"
    assert edge.target == "NVDA"
    assert edge.relation == RelationType.SUPPLIER
    assert edge.confidence == 0.98


def test_supply_chain_edge_partner():
    """GOOGL ↔ AVGO 파트너 관계 테스트"""
    edge = SupplyChainEdge(
        source="GOOGL",
        target="AVGO",
        relation=RelationType.PARTNER,
        confidence=0.85,
        context="Broadcom designs custom ASICs for Google TPU"
    )

    assert edge.relation == RelationType.PARTNER


# ═══════════════════════════════════════════════════════════════
# [3] UnitEconomics 테스트
# ═══════════════════════════════════════════════════════════════

def test_unit_economics_full():
    """완전한 UnitEconomics 테스트"""
    economics = UnitEconomics(
        token_cost=1.2e-8,
        energy_cost=0.12,
        capex_cost=30000.0,
        tco_monthly=1250.0,
        lifetime_tokens=2.5e12,
        cost_per_watt=42.86
    )

    assert economics.token_cost == 1.2e-8
    assert economics.tco_monthly == 1250.0


def test_unit_economics_partial():
    """부분 UnitEconomics 테스트"""
    economics = UnitEconomics(
        token_cost=1.5e-8,
        tco_monthly=1100.0
    )

    assert economics.token_cost == 1.5e-8
    assert economics.capex_cost is None


# ═══════════════════════════════════════════════════════════════
# [4] NewsFeatures 테스트
# ═══════════════════════════════════════════════════════════════

def test_news_features_training():
    """Training 뉴스 분류 테스트"""
    news = NewsFeatures(
        headline="NVIDIA Blackwell B200 breaks training records",
        body="NVIDIA announced new Blackwell B200 GPU with unprecedented training performance...",
        segment=MarketSegment.TRAINING,
        sentiment=0.85,
        keywords=["blackwell", "b200", "training"],
        tickers_mentioned=["NVDA", "TSM"],
        confidence=0.92
    )

    assert news.segment == MarketSegment.TRAINING
    assert news.sentiment == 0.85
    assert "NVDA" in news.tickers_mentioned


def test_news_features_inference():
    """Inference 뉴스 분류 테스트"""
    news = NewsFeatures(
        headline="Google TPU v6e optimized for inference",
        segment=MarketSegment.INFERENCE,
        sentiment=0.75,
        keywords=["tpu", "v6e", "inference"],
        tickers_mentioned=["GOOGL", "AVGO"]
    )

    assert news.segment == MarketSegment.INFERENCE


def test_news_features_sentiment_validation():
    """감성 점수 범위 검증 테스트"""
    # 정상 범위 (-1~1)
    news = NewsFeatures(headline="Test", sentiment=0.5)
    assert news.sentiment == 0.5

    # 범위 초과
    with pytest.raises(ValidationError):
        NewsFeatures(headline="Test", sentiment=1.5)


# ═══════════════════════════════════════════════════════════════
# [5] PolicyRisk (PERI) 테스트
# ═══════════════════════════════════════════════════════════════

def test_policy_risk_auto_calculation():
    """PERI 자동 계산 테스트"""
    risk = PolicyRisk(
        fed_conflict_score=0.45,
        successor_signal_score=0.30,
        gov_fed_tension_score=0.60,
        election_risk_score=0.25,
        bond_volatility_score=0.35,
        policy_uncertainty_score=0.40
    )

    # PERI 자동 계산 검증
    expected_peri = (
        0.45 * 0.25 +
        0.30 * 0.20 +
        0.60 * 0.20 +
        0.25 * 0.15 +
        0.35 * 0.10 +
        0.40 * 0.10
    ) * 100

    assert abs(risk.peri - expected_peri) < 0.01


def test_policy_risk_manual_peri():
    """수동 PERI 설정 테스트"""
    risk = PolicyRisk(peri=50.0)
    assert risk.peri == 50.0


def test_policy_risk_range_validation():
    """PERI 범위 검증 테스트"""
    # 정상 범위 (0~100)
    risk = PolicyRisk(peri=75.0)
    assert risk.peri == 75.0

    # 범위 초과
    with pytest.raises(ValidationError):
        PolicyRisk(peri=150.0)


# ═══════════════════════════════════════════════════════════════
# [6] MarketContext 테스트
# ═══════════════════════════════════════════════════════════════

def test_market_context_full():
    """완전한 MarketContext 테스트"""
    context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        chip_info=[
            ChipInfo(
                model="H100",
                vendor="NVIDIA",
                segment="training"
            )
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
    assert context.policy_risk.peri == 35.0


def test_market_context_minimal():
    """최소 MarketContext 테스트"""
    context = MarketContext()
    assert context.ticker is None
    assert len(context.chip_info) == 0
    assert len(context.supply_chain) == 0


# ═══════════════════════════════════════════════════════════════
# [7] MultimodelInput 테스트
# ═══════════════════════════════════════════════════════════════

def test_multimodel_input_ensemble():
    """Multi-AI 앙상블 입력 테스트"""
    base_context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA",
        market_regime=MarketRegime.BULL
    )

    multimodel = MultimodelInput(
        claude_context=base_context,
        chatgpt_context=base_context,
        gemini_context=base_context,
        ensemble_weights={
            "claude": 0.5,
            "chatgpt": 0.3,
            "gemini": 0.2
        },
        debate_mode=False
    )

    assert multimodel.claude_context.ticker == "NVDA"
    assert multimodel.ensemble_weights["claude"] == 0.5
    assert multimodel.debate_mode is False


def test_multimodel_input_different_contexts():
    """다른 컨텍스트로 Multi-AI 입력 테스트"""
    claude_ctx = MarketContext(ticker="NVDA", market_regime=MarketRegime.BULL)
    chatgpt_ctx = MarketContext(ticker="NVDA", market_regime=MarketRegime.SIDEWAYS)
    gemini_ctx = MarketContext(ticker="NVDA", market_regime=MarketRegime.BULL)

    multimodel = MultimodelInput(
        claude_context=claude_ctx,
        chatgpt_context=chatgpt_ctx,
        gemini_context=gemini_ctx
    )

    assert multimodel.claude_context.market_regime == MarketRegime.BULL
    assert multimodel.chatgpt_context.market_regime == MarketRegime.SIDEWAYS


# ═══════════════════════════════════════════════════════════════
# [8] InvestmentSignal 테스트
# ═══════════════════════════════════════════════════════════════

def test_investment_signal_buy():
    """매수 시그널 테스트"""
    signal = InvestmentSignal(
        ticker="NVDA",
        action=SignalAction.BUY,
        confidence=0.85,
        reasoning="Blackwell B200 training efficiency leads market",
        position_size=0.15,
        stop_loss=120.0,
        take_profit=160.0,
        risk_score=0.25,
        metadata={
            "segment": "training",
            "hidden_beneficiaries": ["TSM", "AVGO"]
        }
    )

    assert signal.action == SignalAction.BUY
    assert signal.confidence == 0.85
    assert signal.position_size == 0.15
    assert "TSM" in signal.metadata["hidden_beneficiaries"]


def test_investment_signal_hold():
    """보유 시그널 테스트"""
    signal = InvestmentSignal(
        ticker="AMD",
        action=SignalAction.HOLD,
        confidence=0.60,
        reasoning="Waiting for MI300 launch results"
    )

    assert signal.action == SignalAction.HOLD
    assert signal.confidence == 0.60


def test_investment_signal_validation():
    """시그널 범위 검증 테스트"""
    # 신뢰도 범위 초과
    with pytest.raises(ValidationError):
        InvestmentSignal(
            ticker="NVDA",
            action=SignalAction.BUY,
            confidence=1.5,
            reasoning="Test"
        )

    # 포지션 크기 범위 초과
    with pytest.raises(ValidationError):
        InvestmentSignal(
            ticker="NVDA",
            action=SignalAction.BUY,
            confidence=0.8,
            reasoning="Test",
            position_size=1.5
        )


# ═══════════════════════════════════════════════════════════════
# [9] JSON 직렬화/역직렬화 테스트
# ═══════════════════════════════════════════════════════════════

def test_market_context_json_serialization():
    """MarketContext JSON 직렬화 테스트"""
    context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA",
        market_regime=MarketRegime.BULL
    )

    # JSON 직렬화
    json_str = context.model_dump_json()
    assert "NVDA" in json_str
    assert "bull" in json_str

    # JSON 역직렬화
    context_restored = MarketContext.model_validate_json(json_str)
    assert context_restored.ticker == "NVDA"
    assert context_restored.market_regime == MarketRegime.BULL


def test_multimodel_input_json_roundtrip():
    """MultimodelInput JSON 왕복 테스트"""
    base_context = MarketContext(ticker="NVDA")

    original = MultimodelInput(
        claude_context=base_context,
        chatgpt_context=base_context,
        gemini_context=base_context,
        ensemble_weights={"claude": 0.5, "chatgpt": 0.3, "gemini": 0.2}
    )

    # JSON 왕복
    json_str = original.model_dump_json()
    restored = MultimodelInput.model_validate_json(json_str)

    assert restored.claude_context.ticker == "NVDA"
    assert restored.ensemble_weights["claude"] == 0.5


# ═══════════════════════════════════════════════════════════════
# [10] 통합 테스트
# ═══════════════════════════════════════════════════════════════

def test_full_pipeline_example():
    """전체 파이프라인 통합 테스트"""
    # 1. 뉴스 입력
    news = NewsFeatures(
        headline="NVIDIA Blackwell GPU breaks records",
        segment=MarketSegment.TRAINING,
        sentiment=0.9,
        tickers_mentioned=["NVDA", "TSM"]
    )

    # 2. 칩 정보
    chip = ChipInfo(
        model="B200",
        vendor="NVIDIA",
        segment="training",
        efficiency_score=0.95
    )

    # 3. 공급망
    supply_chain = [
        SupplyChainEdge(
            source="TSM",
            target="NVDA",
            relation=RelationType.SUPPLIER,
            confidence=0.98
        )
    ]

    # 4. MarketContext 생성
    context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA",
        chip_info=[chip],
        supply_chain=supply_chain,
        news=news,
        market_regime=MarketRegime.BULL
    )

    # 5. Multi-AI 입력
    multimodel = MultimodelInput(
        claude_context=context,
        chatgpt_context=context,
        gemini_context=context
    )

    # 6. 최종 시그널
    signal = InvestmentSignal(
        ticker="NVDA",
        action=SignalAction.BUY,
        confidence=0.9,
        reasoning="Training market leader with strong supply chain",
        position_size=0.2
    )

    # 검증
    assert news.segment == MarketSegment.TRAINING
    assert chip.vendor == "NVIDIA"
    assert len(context.supply_chain) == 1
    assert signal.action == SignalAction.BUY
    assert signal.confidence == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
