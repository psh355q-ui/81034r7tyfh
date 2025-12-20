"""
UnitEconomicsEngine - AI GPU/TPU/ASIC 단위 경제학 계산기

토큰당 비용(Cost per Token), 에너지 효율(Tokens per Joule),
성능 대비 가격(Throughput per Dollar)을 계산한다.

사용 목적:
- 엔비디아가 비싸 보이지만 실제로 싼지 검증
- TPU / AMD / ASIC과 정량적 비교
- DeepReasoningStrategy에 정량 팩터 제공

핵심 인사이트:
"엔비디아 칩은 비싸 보이지만, 토큰당 비용은 가장 싸다. 그래서 여전히 시장을 지배한다."

비용: $0/월 (룰 기반 계산)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import BaseSchema for integration
from backend.schemas.base_schema import ChipInfo, UnitEconomics, MarketSegment

logger = logging.getLogger(__name__)


class UnitEconomicsEngine:
    """
    AI 칩의 단위 경제학(Unit Economics) 계산 엔진

    주요 메트릭:
    1. Cost per Token: 토큰당 비용 (하드웨어 + 전력)
    2. Tokens per Joule: 에너지 효율
    3. Throughput per Dollar: 성능 대비 가격
    4. Cost per Watt: 전력비 효율

    Phase 0 통합:
    - ChipInfo 입력 → UnitEconomics 출력
    """

    # 기본 설정값
    DEFAULT_ELECTRICITY_COST = 0.12  # $/kWh (미국 평균)
    DEFAULT_LIFESPAN_YEARS = 3  # 하드웨어 수명 (년)
    DEFAULT_UPTIME_RATIO = 0.95  # 가동률 (95%)

    def __init__(
        self,
        electricity_cost: float = DEFAULT_ELECTRICITY_COST,
        lifespan_years: int = DEFAULT_LIFESPAN_YEARS,
        uptime_ratio: float = DEFAULT_UPTIME_RATIO
    ):
        """
        Args:
            electricity_cost: 전기요금 ($/kWh)
            lifespan_years: 하드웨어 수명 (년)
            uptime_ratio: 가동률 (0.0 ~ 1.0)
        """
        self.electricity_cost = electricity_cost
        self.lifespan_hours = lifespan_years * 365 * 24
        self.uptime_ratio = uptime_ratio

    def tokens_per_lifetime(
        self,
        tokens_per_sec: float,
        lifespan_hours: Optional[int] = None
    ) -> float:
        """
        칩의 생애 전체 생성 토큰 수 계산

        Args:
            tokens_per_sec: 초당 토큰 생성량
            lifespan_hours: 수명 시간 (기본값: 3년 * 365일 * 24시간)

        Returns:
            생애 전체 토큰 수
        """
        if lifespan_hours is None:
            lifespan_hours = self.lifespan_hours

        effective_hours = lifespan_hours * self.uptime_ratio
        return tokens_per_sec * effective_hours * 3600

    def compute_cost_per_token(
        self,
        hw_price: float,
        power_watts: float,
        tokens_per_sec: float,
        electricity_cost: Optional[float] = None,
        lifespan_hours: Optional[int] = None
    ) -> float:
        """
        토큰당 비용 계산

        공식: (하드웨어 가격 + 생애 전력 비용) / 생애 전체 토큰 수

        Args:
            hw_price: 하드웨어 가격 ($)
            power_watts: 소비 전력 (W)
            tokens_per_sec: 초당 토큰 생성량
            electricity_cost: 전기요금 ($/kWh)
            lifespan_hours: 수명 시간

        Returns:
            토큰당 비용 ($)
        """
        if electricity_cost is None:
            electricity_cost = self.electricity_cost
        if lifespan_hours is None:
            lifespan_hours = self.lifespan_hours

        # 생애 전체 토큰 수
        effective_hours = lifespan_hours * self.uptime_ratio
        lifetime_tokens = self.tokens_per_lifetime(tokens_per_sec, lifespan_hours)

        if lifetime_tokens == 0:
            return float('inf')

        # 생애 전력 비용 계산
        # 전력(kW) * 시간 * 전기요금
        lifetime_power_cost = (power_watts / 1000) * effective_hours * electricity_cost

        # 총 비용
        total_cost = hw_price + lifetime_power_cost

        return total_cost / lifetime_tokens

    def energy_efficiency(self, tokens_per_sec: float, watts: float) -> float:
        """
        에너지 효율 계산 (Tokens per Joule)

        Args:
            tokens_per_sec: 초당 토큰 생성량
            watts: 소비 전력 (W)

        Returns:
            Joule당 토큰 수
        """
        if watts == 0:
            return 0
        return tokens_per_sec / watts

    def throughput_per_dollar(self, tokens_per_sec: float, hw_price: float) -> float:
        """
        성능 대비 가격 계산 (Throughput per Dollar)

        Args:
            tokens_per_sec: 초당 토큰 생성량
            hw_price: 하드웨어 가격 ($)

        Returns:
            달러당 처리량
        """
        if hw_price == 0:
            return 0
        return tokens_per_sec / hw_price

    def cost_per_watt(self, hw_price: float, watts: float) -> float:
        """
        전력비 효율 계산 (Cost per Watt)

        Args:
            hw_price: 하드웨어 가격 ($)
            watts: 소비 전력 (W)

        Returns:
            Watt당 비용
        """
        if watts == 0:
            return 0
        return hw_price / watts

    def evaluate_chip(self, chip: ChipInfo, tokens_per_sec: float) -> UnitEconomics:
        """
        칩 스펙을 받아 단위 경제학 지표 계산 (BaseSchema 사용)

        Args:
            chip: ChipInfo 스키마
            tokens_per_sec: 초당 토큰 생성량 (추론 성능)

        Returns:
            UnitEconomics 스키마
        """
        # 기본값 설정
        price = chip.cost_usd or 0
        power = chip.tdp_watts or 0

        # 계산
        cost_per_token = self.compute_cost_per_token(price, power, tokens_per_sec)
        energy_per_token = power / tokens_per_sec if tokens_per_sec > 0 else float('inf')
        lifetime_tokens = self.tokens_per_lifetime(tokens_per_sec)

        # 월간 TCO 계산
        effective_hours = self.lifespan_hours * self.uptime_ratio
        monthly_power_cost = (power / 1000) * (effective_hours / 36) * self.electricity_cost  # 36개월
        monthly_depreciation = price / 36  # 3년 분할
        tco_monthly = monthly_depreciation + monthly_power_cost

        return UnitEconomics(
            token_cost=cost_per_token,
            energy_cost=energy_per_token * self.electricity_cost / 1000,  # Wh → kWh
            capex_cost=price,
            tco_monthly=tco_monthly,
            lifetime_tokens=lifetime_tokens
        )

    def evaluate_chip_legacy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        레거시 딕셔너리 형식 지원 (하위 호환성)

        Args:
            spec: 칩 스펙 딕셔너리
                {
                    "name": "NVIDIA H200",
                    "price": 40000,  # USD
                    "power": 700,    # Watts
                    "tokens_per_sec": 18000,
                    "segment": "training"  # training or inference
                }

        Returns:
            계산된 경제성 지표
        """
        name = spec.get("name", "Unknown")
        price = spec.get("price", 0)
        power = spec.get("power", 0)
        tokens_per_sec = spec.get("tokens_per_sec", 0)
        segment = spec.get("segment", "unknown")
        vendor = spec.get("vendor", "Unknown")

        cost_per_token = self.compute_cost_per_token(price, power, tokens_per_sec)
        tokens_per_joule = self.energy_efficiency(tokens_per_sec, power)
        throughput_dollar = self.throughput_per_dollar(tokens_per_sec, price)
        cost_watt = self.cost_per_watt(price, power)

        return {
            "name": name,
            "vendor": vendor,
            "segment": segment,
            "price": price,
            "power": power,
            "tokens_per_sec": tokens_per_sec,
            "cost_per_token": cost_per_token,
            "tokens_per_joule": tokens_per_joule,
            "throughput_per_dollar": throughput_dollar,
            "cost_per_watt": cost_watt,
            "lifetime_tokens": self.tokens_per_lifetime(tokens_per_sec),
            "evaluated_at": datetime.now().isoformat()
        }

    def compare_chips(self, specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        여러 칩의 경제성 비교 (레거시 지원)

        Args:
            specs: 칩 스펙 리스트

        Returns:
            비교 결과
        """
        if not specs:
            return {"error": "No specs provided"}

        evaluated = [self.evaluate_chip_legacy(s) for s in specs]

        # 메트릭별 최고 칩 찾기
        cheapest = min(
            evaluated,
            key=lambda x: x["cost_per_token"] if x["cost_per_token"] != float('inf') else float('inf')
        )
        best_energy = max(evaluated, key=lambda x: x["tokens_per_joule"])
        best_throughput = max(evaluated, key=lambda x: x["throughput_per_dollar"])

        return {
            "chips_evaluated": len(evaluated),
            "best_by_metric": {
                "lowest_cost_per_token": cheapest["name"],
                "best_energy_efficiency": best_energy["name"],
                "best_throughput_per_dollar": best_throughput["name"]
            },
            "rankings": {
                "by_cost_per_token": sorted(evaluated, key=lambda x: x["cost_per_token"]),
                "by_energy_efficiency": sorted(evaluated, key=lambda x: -x["tokens_per_joule"]),
                "by_throughput_per_dollar": sorted(evaluated, key=lambda x: -x["throughput_per_dollar"])
            },
            "all_chips": evaluated
        }


# ============================================================================
# 기본 칩 스펙 데이터
# ============================================================================

DEFAULT_CHIP_SPECS = [
    {
        "name": "NVIDIA H100",
        "vendor": "NVIDIA",
        "price": 35000,
        "power": 700,
        "tokens_per_sec": 18000,
        "segment": "training",
        "notes": "데이터센터 표준, Hopper 아키텍처"
    },
    {
        "name": "NVIDIA H200",
        "vendor": "NVIDIA",
        "price": 40000,
        "power": 700,
        "tokens_per_sec": 22000,
        "segment": "training",
        "notes": "H100 대비 메모리 증가, HBM3e"
    },
    {
        "name": "NVIDIA Blackwell B200",
        "vendor": "NVIDIA",
        "price": 45000,
        "power": 700,
        "tokens_per_sec": 26000,
        "segment": "training",
        "notes": "차세대 Blackwell 아키텍처"
    },
    {
        "name": "Google TPU v5p",
        "vendor": "Google",
        "price": 30000,
        "power": 550,
        "tokens_per_sec": 24000,
        "segment": "inference",
        "notes": "Google Cloud 전용, Gemini 학습용"
    },
    {
        "name": "Google TPU v6e",
        "vendor": "Google",
        "price": 35000,
        "power": 500,
        "tokens_per_sec": 28000,
        "segment": "inference",
        "notes": "에너지 효율 최적화"
    },
    {
        "name": "AMD MI300X",
        "vendor": "AMD",
        "price": 25000,
        "power": 650,
        "tokens_per_sec": 16000,
        "segment": "inference",
        "notes": "CDNA3 아키텍처, ROCm 생태계"
    },
    {
        "name": "AMD MI325X",
        "vendor": "AMD",
        "price": 28000,
        "power": 700,
        "tokens_per_sec": 20000,
        "segment": "inference",
        "notes": "MI300X 후속, 메모리 증가"
    },
    {
        "name": "Intel Gaudi 3",
        "vendor": "Intel",
        "price": 15000,
        "power": 500,
        "tokens_per_sec": 12000,
        "segment": "inference",
        "notes": "가격 경쟁력, 소프트웨어 에코시스템 약점"
    }
]


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    engine = UnitEconomicsEngine()

    print("=" * 60)
    print("AI Chip Unit Economics Analysis")
    print("=" * 60)

    # 비교 분석
    result = engine.compare_chips(DEFAULT_CHIP_SPECS)

    print(f"\n총 {result['chips_evaluated']}개 칩 분석 완료")
    print("\n### 메트릭별 최고 칩 ###")
    for metric, chip in result["best_by_metric"].items():
        print(f"  {metric}: {chip}")

    print("\n### 토큰당 비용 랭킹 (낮을수록 좋음) ###")
    for i, chip in enumerate(result["rankings"]["by_cost_per_token"][:5], 1):
        cost = chip["cost_per_token"]
        if cost == float('inf'):
            cost_str = "N/A"
        else:
            cost_str = f"${cost:.10f}"
        print(f"  {i}. {chip['name']}: {cost_str}")

    print("\n### 에너지 효율 랭킹 (높을수록 좋음) ###")
    for i, chip in enumerate(result["rankings"]["by_energy_efficiency"][:5], 1):
        print(f"  {i}. {chip['name']}: {chip['tokens_per_joule']:.2f} tokens/joule")

    print("\n### 성능 대비 가격 랭킹 (높을수록 좋음) ###")
    for i, chip in enumerate(result["rankings"]["by_throughput_per_dollar"][:5], 1):
        print(f"  {i}. {chip['name']}: {chip['throughput_per_dollar']:.4f} tokens/sec/$")

    # BaseSchema 테스트
    print("\n" + "=" * 60)
    print("BaseSchema Integration Test")
    print("=" * 60)

    # ChipInfo 생성
    h100 = ChipInfo(
        model="NVIDIA H100",
        vendor="NVIDIA",
        process_node="4nm",
        perf_tflops=1979.0,
        mem_bw_gbps=3350.0,
        tdp_watts=700.0,
        cost_usd=35000.0,
        segment=MarketSegment.TRAINING
    )

    # UnitEconomics 계산
    economics = engine.evaluate_chip(h100, tokens_per_sec=18000)

    print(f"\nChip: {h100.model}")
    print(f"  Token Cost: ${economics.token_cost:.10f}")
    print(f"  Energy Cost: ${economics.energy_cost:.10f}")
    print(f"  TCO Monthly: ${economics.tco_monthly:.2f}")
    print(f"  Lifetime Tokens: {economics.lifetime_tokens:.2e}")
