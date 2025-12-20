"""
ChipEfficiencyComparator - AI 칩 효율 비교 엔진

여러 GPU/TPU/ASIC을 UnitEconomicsEngine을 통해 비교하고
'효율 기반 투자 시그널'을 생성한다.

사용 목적:
- 엔비디아 vs TPU vs AMD 정량 비교
- Training vs Inference 시장별 최적 칩 식별
- 투자 시그널 자동 생성

Output 예시:
{
    "cheapest_token_cost": "NVIDIA Blackwell B200",
    "best_energy_efficiency": "Google TPU v5p",
    "best_for_training": "NVIDIA H200",
    "best_for_inference": "TPU v6e",
    "investment_signal": "Long GOOGL/AVGO, Maintain NVDA Training Exposure"
}

비용: $0/월 (룰 기반 계산)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.schemas.base_schema import (
    ChipInfo,
    UnitEconomics,
    MarketSegment,
    InvestmentSignal,
    SignalAction
)
from backend.ai.economics.unit_economics_engine import UnitEconomicsEngine, DEFAULT_CHIP_SPECS

logger = logging.getLogger(__name__)


class ChipEfficiencyComparator:
    """
    칩 효율 비교 및 투자 시그널 생성 엔진

    주요 기능:
    1. 토큰당 비용 기준 최적 칩 식별
    2. Training vs Inference 시장별 분석
    3. 투자 시그널 자동 생성

    Phase 0 통합:
    - ChipInfo 리스트 입력 → InvestmentSignal 출력
    """

    # 티커 매핑
    VENDOR_TICKERS = {
        "NVIDIA": "NVDA",
        "Google": "GOOGL",
        "AMD": "AMD",
        "Intel": "INTC",
        "Broadcom": "AVGO",  # TPU 설계 파트너
        "TSMC": "TSM",
    }

    # 시장 세그먼트별 키워드
    TRAINING_KEYWORDS = ["H100", "H200", "B200", "Blackwell", "Hopper", "training"]
    INFERENCE_KEYWORDS = ["TPU", "MI300", "MI325", "Gaudi", "inference", "v5p", "v6e"]

    def __init__(self, engine: Optional[UnitEconomicsEngine] = None):
        """
        Args:
            engine: UnitEconomicsEngine 인스턴스 (없으면 기본 생성)
        """
        self.engine = engine or UnitEconomicsEngine()

    def compare_with_schema(
        self,
        chips: List[ChipInfo],
        tokens_per_sec_map: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        ChipInfo 리스트를 받아 효율 분석 및 투자 시그널 생성 (BaseSchema 사용)

        Args:
            chips: ChipInfo 스키마 리스트
            tokens_per_sec_map: 칩별 초당 토큰 생성량 매핑
                {"NVIDIA H100": 18000, "Google TPU v5p": 24000, ...}

        Returns:
            효율 비교 및 투자 시그널
        """
        if not chips:
            return {"error": "No chips provided", "investment_signals": []}

        # 칩별 경제성 평가
        evaluations = []
        for chip in chips:
            tokens_per_sec = tokens_per_sec_map.get(chip.model, 10000)
            economics = self.engine.evaluate_chip(chip, tokens_per_sec)

            evaluations.append({
                "chip": chip,
                "economics": economics,
                "tokens_per_sec": tokens_per_sec,
                "efficiency_score": self._calculate_efficiency_score(chip, economics, tokens_per_sec)
            })

        # 전체 최적 칩
        cheapest = min(evaluations, key=lambda x: x["economics"].token_cost or float('inf'))
        best_energy = min(evaluations, key=lambda x: x["economics"].energy_cost or float('inf'))

        # 세그먼트별 최적 칩
        training_chips = [e for e in evaluations if e["chip"].segment == MarketSegment.TRAINING]
        inference_chips = [e for e in evaluations if e["chip"].segment == MarketSegment.INFERENCE]

        best_training = min(training_chips, key=lambda x: x["economics"].token_cost or float('inf')) if training_chips else None
        best_inference = min(inference_chips, key=lambda x: x["economics"].token_cost or float('inf')) if inference_chips else None

        # 투자 시그널 생성
        signals = self._generate_investment_signals(
            cheapest, best_energy, best_training, best_inference, evaluations
        )

        return {
            "cheapest_token_cost": cheapest["chip"].model,
            "best_energy_efficiency": best_energy["chip"].model,
            "best_for_training": best_training["chip"].model if best_training else None,
            "best_for_inference": best_inference["chip"].model if best_inference else None,
            "investment_signals": signals,
            "details": {
                "all_evaluations": evaluations,
                "training_chips": training_chips,
                "inference_chips": inference_chips
            },
            "analyzed_at": datetime.now().isoformat()
        }

    def _calculate_efficiency_score(
        self,
        chip: ChipInfo,
        economics: UnitEconomics,
        tokens_per_sec: float
    ) -> float:
        """
        종합 효율 점수 계산 (0~1)

        Args:
            chip: ChipInfo
            economics: UnitEconomics
            tokens_per_sec: 초당 토큰 생성량

        Returns:
            효율 점수 (0~1)
        """
        # 비용 점수 (낮을수록 좋음)
        token_cost = economics.token_cost or float('inf')
        cost_score = 1 / (1 + token_cost * 1e9)

        # 에너지 점수 (낮을수록 좋음)
        energy_cost = economics.energy_cost or float('inf')
        energy_score = 1 / (1 + energy_cost * 1e6)

        # 성능 점수
        perf_score = (chip.perf_tflops or 0) / 5000  # 5000 TFLOPS를 최대로

        # 가중 평균
        return cost_score * 0.4 + energy_score * 0.3 + perf_score * 0.3

    def _generate_investment_signals(
        self,
        cheapest: Dict[str, Any],
        best_energy: Dict[str, Any],
        best_training: Optional[Dict[str, Any]],
        best_inference: Optional[Dict[str, Any]],
        all_evaluations: List[Dict[str, Any]]
    ) -> List[InvestmentSignal]:
        """
        비교 결과를 바탕으로 투자 시그널 생성 (InvestmentSignal 스키마 사용)

        Returns:
            InvestmentSignal 리스트
        """
        signals = []

        # 토큰당 비용 최저 칩 벤더 → BUY
        cheapest_vendor = cheapest["chip"].vendor
        if cheapest_vendor in self.VENDOR_TICKERS:
            ticker = self.VENDOR_TICKERS[cheapest_vendor]
            signals.append(InvestmentSignal(
                ticker=ticker,
                action=SignalAction.BUY,
                confidence=0.8,
                reasoning=f"{cheapest_vendor} has lowest cost per token ({cheapest['chip'].model})",
                position_size=0.25,
                risk_factors={"market_segment": "cost_efficiency"}
            ))

        # 에너지 효율 최고 칩 벤더 → BUY
        energy_vendor = best_energy["chip"].vendor
        if energy_vendor in self.VENDOR_TICKERS and energy_vendor != cheapest_vendor:
            ticker = self.VENDOR_TICKERS[energy_vendor]
            signals.append(InvestmentSignal(
                ticker=ticker,
                action=SignalAction.BUY,
                confidence=0.7,
                reasoning=f"{energy_vendor} leads in energy efficiency ({best_energy['chip'].model})",
                position_size=0.2,
                risk_factors={"market_segment": "energy_efficiency"}
            ))

        # TPU 관련 → Broadcom (AVGO) BUY
        if best_inference and "TPU" in best_inference["chip"].model:
            signals.append(InvestmentSignal(
                ticker="AVGO",
                action=SignalAction.BUY,
                confidence=0.65,
                reasoning="TPU dominance benefits Broadcom (TPU design partner)",
                position_size=0.15,
                risk_factors={"market_segment": "inference_asic"}
            ))

        # NVIDIA Training 최적 → HOLD/BUY
        if best_training and best_training["chip"].vendor == "NVIDIA":
            # 이미 BUY 시그널이 있으면 HOLD
            nvda_signals = [s for s in signals if s.ticker == "NVDA"]
            if not nvda_signals:
                signals.append(InvestmentSignal(
                    ticker="NVDA",
                    action=SignalAction.BUY,
                    confidence=0.75,
                    reasoning="NVIDIA maintains training market leadership",
                    position_size=0.3,
                    risk_factors={"market_segment": "training_dominance"}
                ))

        return signals

    def compare(self, specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        레거시 딕셔너리 형식 지원 (하위 호환성)

        Args:
            specs: 칩 스펙 리스트

        Returns:
            효율 비교 및 투자 시그널
        """
        if not specs:
            return {"error": "No specs provided", "investment_signal": None}

        # 모든 칩 평가
        evaluated = [self.engine.evaluate_chip_legacy(s) for s in specs]

        # 전체 최적 칩
        cheapest = min(
            evaluated,
            key=lambda x: x["cost_per_token"] if x["cost_per_token"] != float('inf') else float('inf')
        )
        best_energy = max(evaluated, key=lambda x: x["tokens_per_joule"])
        best_throughput = max(evaluated, key=lambda x: x["throughput_per_dollar"])

        # 세그먼트별 최적 칩
        training_chips = [c for c in evaluated if c.get("segment") == "training"]
        inference_chips = [c for c in evaluated if c.get("segment") == "inference"]

        best_training = None
        best_inference = None

        if training_chips:
            best_training = min(
                training_chips,
                key=lambda x: x["cost_per_token"] if x["cost_per_token"] != float('inf') else float('inf')
            )

        if inference_chips:
            best_inference = min(
                inference_chips,
                key=lambda x: x["cost_per_token"] if x["cost_per_token"] != float('inf') else float('inf')
            )

        # 투자 시그널 생성
        signal = self._generate_investment_signal_legacy(
            cheapest, best_energy, best_training, best_inference, evaluated
        )

        return {
            "cheapest_token_cost": cheapest["name"],
            "best_energy_efficiency": best_energy["name"],
            "best_throughput_per_dollar": best_throughput["name"],
            "best_for_training": best_training["name"] if best_training else None,
            "best_for_inference": best_inference["name"] if best_inference else None,
            "investment_signal": signal,
            "details": {
                "all_chips": evaluated,
                "training_chips": training_chips,
                "inference_chips": inference_chips
            },
            "analyzed_at": datetime.now().isoformat()
        }

    def _generate_investment_signal_legacy(
        self,
        cheapest: Dict[str, Any],
        best_energy: Dict[str, Any],
        best_training: Optional[Dict[str, Any]],
        best_inference: Optional[Dict[str, Any]],
        all_chips: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        레거시 투자 시그널 생성

        Returns:
            {
                "long": ["NVDA", "AVGO"],
                "hold": ["AMD"],
                "avoid": ["INTC"],
                "rationale": "...",
                "confidence": 0.75
            }
        """
        long_tickers = []
        hold_tickers = []
        avoid_tickers = []
        rationales = []

        # 토큰당 비용 최저 칩 벤더 → Long
        cheapest_vendor = cheapest.get("vendor", "Unknown")
        if cheapest_vendor in self.VENDOR_TICKERS:
            ticker = self.VENDOR_TICKERS[cheapest_vendor]
            if ticker not in long_tickers:
                long_tickers.append(ticker)
            rationales.append(f"{cheapest_vendor} has lowest cost per token ({cheapest['name']})")

        # 에너지 효율 최고 칩 벤더 → Long
        energy_vendor = best_energy.get("vendor", "Unknown")
        if energy_vendor in self.VENDOR_TICKERS:
            ticker = self.VENDOR_TICKERS[energy_vendor]
            if ticker not in long_tickers:
                long_tickers.append(ticker)
            rationales.append(f"{energy_vendor} leads in energy efficiency ({best_energy['name']})")

        # TPU 관련 → Broadcom (AVGO) Long
        if best_inference and "TPU" in best_inference.get("name", ""):
            if "AVGO" not in long_tickers:
                long_tickers.append("AVGO")
            rationales.append("TPU dominance benefits Broadcom (TPU design partner)")

        # NVIDIA Training 최적 → 유지
        if best_training and best_training.get("vendor") == "NVIDIA":
            if "NVDA" not in long_tickers:
                long_tickers.append("NVDA")
            rationales.append("NVIDIA maintains training market leadership")

        # 효율 중간 → Hold
        for chip in all_chips:
            vendor = chip.get("vendor", "Unknown")
            ticker = self.VENDOR_TICKERS.get(vendor)
            if ticker and ticker not in long_tickers and ticker not in avoid_tickers:
                if ticker not in hold_tickers:
                    hold_tickers.append(ticker)

        # Intel 특수 케이스 - 소프트웨어 에코시스템 약점
        intel_chips = [c for c in all_chips if c.get("vendor") == "Intel"]
        if intel_chips:
            intel_avg_efficiency = sum(c["tokens_per_joule"] for c in intel_chips) / len(intel_chips)
            overall_avg = sum(c["tokens_per_joule"] for c in all_chips) / len(all_chips)

            if intel_avg_efficiency < overall_avg * 0.7:
                if "INTC" in hold_tickers:
                    hold_tickers.remove("INTC")
                avoid_tickers.append("INTC")
                rationales.append("Intel significantly behind in AI efficiency metrics")

        # 신뢰도 계산 (데이터 품질 기반)
        confidence = self._calculate_confidence(all_chips)

        return {
            "long": long_tickers,
            "hold": hold_tickers,
            "avoid": avoid_tickers,
            "rationale": "; ".join(rationales),
            "confidence": confidence,
            "signal_type": "AI_CHIP_EFFICIENCY"
        }

    def _calculate_confidence(self, chips: List[Dict[str, Any]]) -> float:
        """
        데이터 품질에 기반한 신뢰도 계산

        Returns:
            0.0 ~ 1.0 사이의 신뢰도
        """
        # 기본 신뢰도
        confidence = 0.5

        # 칩 수가 많을수록 신뢰도 증가
        if len(chips) >= 5:
            confidence += 0.15
        elif len(chips) >= 3:
            confidence += 0.1

        # 여러 벤더가 포함되면 신뢰도 증가
        vendors = set(c.get("vendor") for c in chips)
        if len(vendors) >= 4:
            confidence += 0.2
        elif len(vendors) >= 3:
            confidence += 0.15
        elif len(vendors) >= 2:
            confidence += 0.1

        # Training + Inference 둘 다 있으면 신뢰도 증가
        segments = set(c.get("segment") for c in chips)
        if "training" in segments and "inference" in segments:
            confidence += 0.1

        return min(confidence, 1.0)

    def get_market_segment_leaders(self, specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Training과 Inference 시장별 리더 분석

        Returns:
            {
                "training_market": {
                    "leader": "NVIDIA",
                    "leader_chip": "B200",
                    "market_share_estimate": 0.85,
                    "key_strength": "최고 throughput"
                },
                "inference_market": {
                    "leader": "Google",
                    "leader_chip": "TPU v6e",
                    "market_share_estimate": 0.35,
                    "key_strength": "에너지 효율"
                }
            }
        """
        evaluated = [self.engine.evaluate_chip_legacy(s) for s in specs]

        training_chips = [c for c in evaluated if c.get("segment") == "training"]
        inference_chips = [c for c in evaluated if c.get("segment") == "inference"]

        result = {}

        if training_chips:
            best = min(training_chips, key=lambda x: x["cost_per_token"])
            result["training_market"] = {
                "leader": best.get("vendor", "Unknown"),
                "leader_chip": best["name"],
                "cost_per_token": best["cost_per_token"],
                "market_share_estimate": 0.85 if best.get("vendor") == "NVIDIA" else 0.15,
                "key_strength": "최고 throughput 및 CUDA 생태계"
            }

        if inference_chips:
            best = max(inference_chips, key=lambda x: x["tokens_per_joule"])
            result["inference_market"] = {
                "leader": best.get("vendor", "Unknown"),
                "leader_chip": best["name"],
                "tokens_per_joule": best["tokens_per_joule"],
                "market_share_estimate": 0.35 if best.get("vendor") == "Google" else 0.25,
                "key_strength": "에너지 효율 및 TCO 최적화"
            }

        return result


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    comparator = ChipEfficiencyComparator()

    print("=" * 70)
    print("AI Chip Efficiency Comparator & Investment Signal Generator")
    print("=" * 70)

    # 비교 분석 실행
    result = comparator.compare(DEFAULT_CHIP_SPECS)

    print("\n### 효율 비교 결과 ###")
    print(f"  토큰당 비용 최저: {result['cheapest_token_cost']}")
    print(f"  에너지 효율 최고: {result['best_energy_efficiency']}")
    print(f"  성능/가격 최고: {result['best_throughput_per_dollar']}")
    print(f"  Training 최적: {result['best_for_training']}")
    print(f"  Inference 최적: {result['best_for_inference']}")

    print("\n### 투자 시그널 ###")
    signal = result['investment_signal']
    print(f"  📈 Long: {', '.join(signal['long'])}")
    print(f"  📊 Hold: {', '.join(signal['hold'])}")
    print(f"  📉 Avoid: {', '.join(signal['avoid'])}")
    print(f"  💡 Rationale: {signal['rationale']}")
    print(f"  🎯 Confidence: {signal['confidence']:.0%}")

    print("\n### 시장 세그먼트 리더 ###")
    leaders = comparator.get_market_segment_leaders(DEFAULT_CHIP_SPECS)
    for segment, data in leaders.items():
        print(f"\n  [{segment}]")
        print(f"    Leader: {data['leader']} ({data['leader_chip']})")
        print(f"    Market Share (est): {data['market_share_estimate']:.0%}")
        print(f"    Key Strength: {data['key_strength']}")
