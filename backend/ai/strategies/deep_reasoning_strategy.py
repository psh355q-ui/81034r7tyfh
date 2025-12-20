"""
DeepReasoningStrategy - 3단 구조 심층 추론 전략

GPT 권장 구조: Ingestion → Reasoning → Signal

Phase A 통합:
1. Ingestion Layer: 원시 데이터 → MarketContext
2. Reasoning Layer: MarketContext 기반 AI 분석
3. Signal Layer: MarketContext → InvestmentSignal

작성일: 2025-12-03 (Phase A 통합)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import BaseSchema
from backend.schemas.base_schema import (
    MarketContext,
    ChipInfo,
    UnitEconomics,
    NewsFeatures,
    InvestmentSignal,
    SignalAction,
    MarketSegment
)

# Import Phase A modules
from backend.ai.economics.unit_economics_engine import UnitEconomicsEngine
from backend.ai.economics.chip_efficiency_comparator import ChipEfficiencyComparator
from backend.data.knowledge.ai_value_chain import AIValueChainGraph
from backend.ai.news.news_segment_classifier import NewsSegmentClassifier

logger = logging.getLogger(__name__)


class DeepReasoningStrategy:
    """
    3단 구조 심층 추론 전략

    GPT 권장 인터페이스:
    - Ingestion Layer: 원시 데이터를 BaseSchema로 변환
    - Reasoning Layer: 3개 AI가 동일 MarketContext를 분석
    - Signal Layer: 추론 결과를 매매 신호로 변환

    Phase A 모듈 통합:
    - UnitEconomicsEngine: 칩 경제성 분석
    - ChipEfficiencyComparator: 효율 비교 및 시그널
    - AIValueChainGraph: 밸류체인 분석
    - NewsSegmentClassifier: 뉴스 세그먼트 분류
    """

    def __init__(self):
        """DeepReasoningStrategy 초기화"""
        # Phase A 모듈 초기화
        self.economics_engine = UnitEconomicsEngine()
        self.chip_comparator = ChipEfficiencyComparator(self.economics_engine)
        self.value_chain = AIValueChainGraph()
        self.news_classifier = NewsSegmentClassifier(self.value_chain)

        logger.info("DeepReasoningStrategy initialized with Phase A modules")

    # ═══════════════════════════════════════════════════════════════
    # [1] Ingestion Layer - 원시 데이터를 BaseSchema로 변환
    # ═══════════════════════════════════════════════════════════════

    def ingest(
        self,
        news_headline: str,
        news_body: str = "",
        chip_data: Optional[List[Dict[str, Any]]] = None
    ) -> MarketContext:
        """
        원시 데이터를 MarketContext로 변환하는 '어댑터 역할'

        Args:
            news_headline: 뉴스 헤드라인
            news_body: 뉴스 본문
            chip_data: 칩 데이터 (선택)

        Returns:
            MarketContext 스키마
        """
        logger.info(f"Ingesting news: {news_headline[:50]}...")

        # 1. 뉴스 분류
        news_features = self.news_classifier.classify(news_headline, news_body)

        # 2. 언급된 티커 추출
        ticker = news_features.tickers_mentioned[0] if news_features.tickers_mentioned else "UNKNOWN"
        company_name = ticker  # 간단히 티커를 이름으로 사용

        # 3. 칩 정보 (데이터가 제공되지 않으면 빈 리스트)
        chip_info_list = []
        if chip_data:
            for chip_dict in chip_data:
                chip_info = ChipInfo(
                    model=chip_dict.get("name", "Unknown"),
                    vendor=chip_dict.get("vendor", "Unknown"),
                    process_node=chip_dict.get("process_node"),
                    perf_tflops=chip_dict.get("perf_tflops"),
                    mem_bw_gbps=chip_dict.get("mem_bw_gbps"),
                    tdp_watts=chip_dict.get("power"),
                    cost_usd=chip_dict.get("price"),
                    segment=MarketSegment.TRAINING if chip_dict.get("segment") == "training" else MarketSegment.INFERENCE
                )
                chip_info_list.append(chip_info)

        # 4. 공급망 엣지
        supply_chain_edges = self.value_chain.get_supply_chain_edges(ticker)

        # 5. MarketContext 구성
        context = MarketContext(
            ticker=ticker,
            company_name=company_name,
            chip_info=chip_info_list,
            supply_chain=supply_chain_edges,
            unit_economics=None,  # Reasoning에서 계산
            news=news_features,
            risk_factors={},
            market_regime=None
        )

        return context

    # ═══════════════════════════════════════════════════════════════
    # [2] Reasoning Layer - 3개 AI가 동일 MarketContext를 분석
    # ═══════════════════════════════════════════════════════════════

    async def reason(self, context: MarketContext) -> Dict[str, Any]:
        """
        MarketContext를 기반으로 심층 추론

        현재는 Phase A 모듈만 사용 (Claude/ChatGPT/Gemini는 Phase B 이후)

        Args:
            context: MarketContext 스키마

        Returns:
            추론 결과 딕셔너리
        """
        logger.info(f"Reasoning for {context.ticker}...")

        reasoning = {
            "timestamp": datetime.now().isoformat(),
            "ticker": context.ticker,
            "news_segment": context.news.segment if context.news else None,
            "phase_a_analysis": {},
            "confidence": 0.0
        }

        # Phase A 분석

        # 1. 밸류체인 분석 (수혜 기업 파악)
        if context.news and context.news.tickers_mentioned:
            primary_ticker = context.news.tickers_mentioned[0]
            beneficiaries = self.value_chain.find_beneficiaries(primary_ticker, "positive")
            reasoning["phase_a_analysis"]["value_chain"] = beneficiaries
        else:
            reasoning["phase_a_analysis"]["value_chain"] = {"error": "No ticker mentioned"}

        # 2. 칩 효율성 분석
        if context.chip_info:
            # ChipInfo를 딕셔너리로 변환 (레거시 메서드 호출용)
            chip_specs = []
            for chip in context.chip_info:
                chip_specs.append({
                    "name": chip.model,
                    "vendor": chip.vendor,
                    "price": chip.cost_usd or 0,
                    "power": chip.tdp_watts or 0,
                    "tokens_per_sec": 10000,  # 기본값 (실제로는 외부 데이터 필요)
                    "segment": chip.segment.value if chip.segment else "training"
                })

            chip_comparison = self.chip_comparator.compare(chip_specs)
            reasoning["phase_a_analysis"]["chip_efficiency"] = {
                "cheapest": chip_comparison["cheapest_token_cost"],
                "best_energy": chip_comparison["best_energy_efficiency"],
                "signal": chip_comparison["investment_signal"]
            }

        # 3. 뉴스 세그먼트 기반 분석
        if context.news:
            segment = context.news.segment
            if segment == MarketSegment.TRAINING:
                reasoning["phase_a_analysis"]["segment_leaders"] = ["NVDA", "TSM"]
                reasoning["confidence"] = context.news.sentiment or 0.7
            elif segment == MarketSegment.INFERENCE:
                reasoning["phase_a_analysis"]["segment_leaders"] = ["GOOGL", "AVGO"]
                reasoning["confidence"] = context.news.sentiment or 0.7
            else:
                reasoning["phase_a_analysis"]["segment_leaders"] = ["NVDA", "GOOGL", "TSM"]
                reasoning["confidence"] = 0.5

        return reasoning

    # ═══════════════════════════════════════════════════════════════
    # [3] Signal Layer - 추론 결과를 매매 신호로 변환
    # ═══════════════════════════════════════════════════════════════

    def generate_signal(self, reasoning_bundle: Dict[str, Any]) -> List[InvestmentSignal]:
        """
        Reasoning Layer의 결과를 '매매 신호'로 변환

        Args:
            reasoning_bundle: reason() 메서드의 반환값

        Returns:
            InvestmentSignal 리스트
        """
        logger.info("Generating investment signals...")

        signals = []

        # Phase A 분석 결과 추출
        phase_a = reasoning_bundle.get("phase_a_analysis", {})
        confidence = reasoning_bundle.get("confidence", 0.5)

        # 1. 밸류체인 수혜자 → BUY 시그널
        value_chain = phase_a.get("value_chain", {})
        direct_beneficiaries = value_chain.get("direct_beneficiaries", [])
        indirect_beneficiaries = value_chain.get("indirect_beneficiaries", [])

        for ticker in direct_beneficiaries:
            signals.append(InvestmentSignal(
                ticker=ticker,
                action=SignalAction.BUY,
                confidence=min(confidence, 0.9),
                reasoning=f"Direct beneficiary from {value_chain.get('news_ticker', 'news')}",
                position_size=0.2
            ))

        for ticker in indirect_beneficiaries:
            signals.append(InvestmentSignal(
                ticker=ticker,
                action=SignalAction.BUY,
                confidence=min(confidence * 0.8, 0.8),
                reasoning=f"Indirect beneficiary via supply chain",
                position_size=0.1
            ))

        # 2. 칩 효율성 시그널
        chip_signal = phase_a.get("chip_efficiency", {}).get("signal", {})
        long_tickers = chip_signal.get("long", [])

        for ticker in long_tickers:
            # 중복 방지
            if not any(s.ticker == ticker for s in signals):
                signals.append(InvestmentSignal(
                    ticker=ticker,
                    action=SignalAction.BUY,
                    confidence=chip_signal.get("confidence", 0.7),
                    reasoning="Chip efficiency leader",
                    position_size=0.15
                ))

        # 3. 시그널이 없으면 기본 HOLD
        if not signals:
            signals.append(InvestmentSignal(
                ticker="SPY",
                action=SignalAction.HOLD,
                confidence=0.5,
                reasoning="Insufficient data for actionable signals",
                position_size=0.0
            ))

        return signals

    # ═══════════════════════════════════════════════════════════════
    # [통합] Full Pipeline: Ingest → Reason → Signal
    # ═══════════════════════════════════════════════════════════════

    async def analyze_news(
        self,
        news_headline: str,
        news_body: str = "",
        chip_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        전체 파이프라인 실행: Ingestion → Reasoning → Signal

        Args:
            news_headline: 뉴스 헤드라인
            news_body: 뉴스 본문
            chip_data: 칩 데이터 (선택)

        Returns:
            분석 결과 및 투자 시그널
        """
        start_time = datetime.now()

        # 1. Ingestion
        context = self.ingest(news_headline, news_body, chip_data)

        # 2. Reasoning
        reasoning = await self.reason(context)

        # 3. Signal Generation
        signals = self.generate_signal(reasoning)

        # 4. 결과 통합
        result = {
            "timestamp": datetime.now().isoformat(),
            "input_news": news_headline,
            "market_context": {
                "ticker": context.ticker,
                "segment": context.news.segment.value if context.news else None,
                "tickers_mentioned": context.news.tickers_mentioned if context.news else []
            },
            "reasoning": reasoning,
            "investment_signals": [
                {
                    "ticker": s.ticker,
                    "action": s.action.value,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning,
                    "position_size": s.position_size
                }
                for s in signals
            ],
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }

        return result


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test():
        strategy = DeepReasoningStrategy()

        print("=" * 70)
        print("DeepReasoningStrategy 3-Tier Pipeline Test")
        print("=" * 70)

        # 테스트 뉴스
        headline = "Google announces TPU v6e for inference workloads with 50% better efficiency"
        body = "The new TPU v6e offers superior cost per token compared to NVIDIA H100"

        # 분석 실행
        result = await strategy.analyze_news(headline, body)

        print(f"\nNews: {result['input_news']}")
        print(f"\nMarket Context:")
        print(f"  Ticker: {result['market_context']['ticker']}")
        print(f"  Segment: {result['market_context']['segment']}")
        print(f"\nInvestment Signals:")
        for signal in result['investment_signals']:
            print(f"  {signal['action']} {signal['ticker']}: {signal['reasoning']} (confidence: {signal['confidence']:.0%})")
        print(f"\nProcessing Time: {result['processing_time_ms']:.1f}ms")

    asyncio.run(test())
