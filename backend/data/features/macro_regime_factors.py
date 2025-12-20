"""
Macro Regime Factors for Feature Store Integration

Credit/FX/Debt 팩터를 Feature Store에 통합하기 위한 모듈

Features:
1. credit_stress_factor - 신용 스프레드 기반 스트레스 지표
2. dollar_strength_factor - 달러 강세 지표
3. debt_pressure_factor - 국가 부채 압박 지표
4. macro_risk_score - 종합 매크로 리스크 점수
5. yield_curve_inversion - 수익률 곡선 역전 여부

비용: $0/월 (무료 FRED API)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .enhanced_fred_collector import EnhancedFREDCollector, LiquidityCrunchDetector

logger = logging.getLogger(__name__)


# =============================================================================
# Feature Store용 팩터 정의
# =============================================================================

MACRO_FACTOR_DEFINITIONS = {
    "credit_stress_factor": {
        "name": "Credit Stress Factor",
        "description": "HY 스프레드 기반 신용 시장 스트레스 지표 (1년 평균 대비)",
        "category": "macro_regime",
        "data_source": "FRED",
        "calculation": "(HY_SPREAD / AVG_1Y_HY_SPREAD) - 1",
        "unit": "ratio",
        "range": (-0.5, 2.0),
        "ttl_days": 1,
        "cost_usd": 0.0,
        "priority": 1,  # ChatGPT 제안: 가장 중요한 선행 지표
    },
    "dollar_strength_factor": {
        "name": "Dollar Strength Factor",
        "description": "달러 인덱스(DXY) 기반 강세 지표 (1년 평균 대비)",
        "category": "macro_regime",
        "data_source": "FRED",
        "calculation": "(DXY / AVG_1Y_DXY) - 1",
        "unit": "ratio",
        "range": (-0.2, 0.3),
        "ttl_days": 1,
        "cost_usd": 0.0,
        "priority": 2,
    },
    "debt_pressure_factor": {
        "name": "Debt Pressure Factor",
        "description": "미국 국가 부채 YoY 증가율",
        "category": "macro_regime",
        "data_source": "FRED",
        "calculation": "(US_DEBT / US_DEBT_1Y_AGO) - 1",
        "unit": "ratio",
        "range": (0.0, 0.3),
        "ttl_days": 7,  # 분기별 데이터이므로 긴 TTL
        "cost_usd": 0.0,
        "priority": 3,
    },
    "yield_curve_inversion": {
        "name": "Yield Curve Inversion",
        "description": "10Y-2Y 국채 수익률 스프레드 역전 여부",
        "category": "macro_regime",
        "data_source": "FRED",
        "calculation": "10Y_TREASURY - 2Y_TREASURY",
        "unit": "boolean",
        "range": (0, 1),
        "ttl_days": 1,
        "cost_usd": 0.0,
        "priority": 4,
    },
    "macro_risk_score": {
        "name": "Composite Macro Risk Score",
        "description": "신용/환율/부채/수익률 곡선을 종합한 리스크 점수",
        "category": "macro_regime",
        "data_source": "FRED",
        "calculation": "weighted_sum(credit:40%, fx:30%, debt:20%, yield:10%)",
        "unit": "score",
        "range": (0.0, 1.0),
        "ttl_days": 1,
        "cost_usd": 0.0,
        "priority": 0,  # 최상위
    },
    "liquidity_crunch_warning": {
        "name": "M7 Liquidity Crunch Warning",
        "description": "M7 기업의 대규모 채권 발행으로 인한 유동성 고갈 경고",
        "category": "event_driven",
        "data_source": "NEWS",
        "calculation": "keyword_detection(bond_issuance + ai_capex)",
        "unit": "boolean",
        "range": (0, 1),
        "ttl_days": 1,
        "cost_usd": 0.0,
        "priority": 0,  # Gemini 제안: 최상위 이벤트
    },
}


class MacroRegimeFeature:
    """
    매크로 국면 팩터를 Feature Store에 통합하기 위한 래퍼 클래스
    
    Usage:
        feature = MacroRegimeFeature()
        result = await feature.calculate("credit_stress_factor")
        # result["value"] = 0.15  (15% above average)
    """
    
    def __init__(self):
        self.fred_collector = EnhancedFREDCollector(cache_days=1)
        self.liquidity_detector = LiquidityCrunchDetector()
        self._cached_factors: Optional[Dict[str, float]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def calculate(
        self,
        factor_name: str,
        as_of_date: Optional[datetime] = None,
        news_headlines: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        특정 매크로 팩터를 계산합니다.
        
        Args:
            factor_name: 팩터 이름 (credit_stress_factor, dollar_strength_factor 등)
            as_of_date: 기준 날짜 (현재는 무시, 항상 최신 데이터 사용)
            news_headlines: 뉴스 헤드라인 (liquidity_crunch_warning용)
            
        Returns:
            {
                "value": float | bool,
                "factor_name": str,
                "category": str,
                "metadata": {
                    "calculated_at": datetime,
                    "ttl_days": int,
                    "cost_usd": float,
                    "data_source": str,
                }
            }
        """
        if factor_name not in MACRO_FACTOR_DEFINITIONS:
            raise ValueError(f"Unknown factor: {factor_name}")
        
        definition = MACRO_FACTOR_DEFINITIONS[factor_name]
        
        # 특별 케이스: 유동성 고갈 경고
        if factor_name == "liquidity_crunch_warning":
            return await self._calculate_liquidity_warning(
                news_headlines or [],
                definition
            )
        
        # 일반 매크로 팩터
        factors = await self._get_or_fetch_factors()
        
        value = factors.get(factor_name, 0.0)
        
        # 부울 타입 변환
        if definition["unit"] == "boolean":
            value = bool(value)
        
        return {
            "value": value,
            "factor_name": factor_name,
            "category": definition["category"],
            "metadata": {
                "calculated_at": datetime.now().isoformat(),
                "ttl_days": definition["ttl_days"],
                "cost_usd": definition["cost_usd"],
                "data_source": definition["data_source"],
                "description": definition["description"],
            }
        }
    
    async def calculate_all(self) -> Dict[str, Any]:
        """
        모든 매크로 팩터를 한 번에 계산합니다.
        
        Returns:
            {
                "credit_stress_factor": {...},
                "dollar_strength_factor": {...},
                ...
                "metadata": {
                    "total_cost_usd": 0.0,
                    "calculated_at": datetime,
                }
            }
        """
        results = {}
        
        for factor_name in MACRO_FACTOR_DEFINITIONS.keys():
            if factor_name != "liquidity_crunch_warning":
                results[factor_name] = await self.calculate(factor_name)
        
        results["metadata"] = {
            "total_cost_usd": 0.0,
            "calculated_at": datetime.now().isoformat(),
            "factors_count": len(results) - 1,  # metadata 제외
        }
        
        return results
    
    async def _get_or_fetch_factors(self) -> Dict[str, float]:
        """캐시된 팩터를 반환하거나 새로 계산"""
        # 캐시가 1시간 이내면 재사용
        if self._cached_factors and self._cache_timestamp:
            age = datetime.now() - self._cache_timestamp
            if age.total_seconds() < 3600:  # 1시간
                return self._cached_factors
        
        # 새로 계산
        self._cached_factors = await self.fred_collector.calculate_macro_factors()
        self._cache_timestamp = datetime.now()
        
        return self._cached_factors
    
    async def _calculate_liquidity_warning(
        self,
        news_headlines: list,
        definition: Dict
    ) -> Dict[str, Any]:
        """유동성 고갈 경고 계산"""
        result = await self.liquidity_detector.check_liquidity_warning(news_headlines)
        
        return {
            "value": result["LIQUIDITY_CRUNCH_WARNING"],
            "factor_name": "liquidity_crunch_warning",
            "category": definition["category"],
            "confidence": result["confidence"],
            "triggered_by": result["triggered_by"],
            "metadata": {
                "calculated_at": datetime.now().isoformat(),
                "ttl_days": definition["ttl_days"],
                "cost_usd": definition["cost_usd"],
                "data_source": definition["data_source"],
                "description": definition["description"],
                "details": result["details"],
            }
        }
    
    def get_feature_definitions(self) -> Dict:
        """Feature Store 등록용 정의 반환"""
        return MACRO_FACTOR_DEFINITIONS
    
    async def get_regime_recommendation(self) -> Dict[str, str]:
        """
        현재 매크로 상황에 기반한 투자 전략 권고
        
        Returns:
            {
                "regime": "BULL" | "SIDEWAYS" | "RISK_OFF" | "CRASH",
                "stock_allocation": float (0.0 ~ 1.0),
                "cash_allocation": float,
                "sector_bias": "defensive" | "neutral" | "aggressive",
                "reasoning": str,
            }
        """
        signals = await self.fred_collector.get_regime_signals()
        
        regime = signals.get("overall_signal", "BULL")
        risk_score = signals.get("macro_risk_score", 0.0)
        
        # 전략 권고
        if regime == "CRASH":
            return {
                "regime": regime,
                "stock_allocation": 0.1,  # 10%만 주식
                "cash_allocation": 0.9,   # 90% 현금
                "sector_bias": "defensive",
                "reasoning": f"매크로 리스크 점수 {risk_score:.2f}. "
                           f"신용 스프레드 위기 또는 강달러로 인한 위험 회피 국면. "
                           f"현금 비중을 최대화하고 방어주만 보유."
            }
        elif regime == "RISK_OFF":
            return {
                "regime": regime,
                "stock_allocation": 0.3,  # 30% 주식
                "cash_allocation": 0.7,   # 70% 현금
                "sector_bias": "defensive",
                "reasoning": f"매크로 리스크 점수 {risk_score:.2f}. "
                           f"유동성 고갈 또는 부채 압박 시나리오. "
                           f"방어주 위주로 포트폴리오 구성."
            }
        elif regime == "SIDEWAYS":
            return {
                "regime": regime,
                "stock_allocation": 0.5,  # 50% 주식
                "cash_allocation": 0.5,   # 50% 현금
                "sector_bias": "neutral",
                "reasoning": f"매크로 리스크 점수 {risk_score:.2f}. "
                           f"불확실성 높음. 밸런스 포트폴리오 유지."
            }
        else:  # BULL
            return {
                "regime": regime,
                "stock_allocation": 0.8,  # 80% 주식
                "cash_allocation": 0.2,   # 20% 현금
                "sector_bias": "aggressive",
                "reasoning": f"매크로 리스크 점수 {risk_score:.2f}. "
                           f"신용 시장 안정, 달러 약세. "
                           f"성장주 위주로 공격적 포지션 가능."
            }


# =============================================================================
# Feature Store 통합 헬퍼 함수
# =============================================================================

# 싱글톤 인스턴스
_macro_feature_instance: Optional[MacroRegimeFeature] = None


def get_macro_feature() -> MacroRegimeFeature:
    """싱글톤 인스턴스 반환"""
    global _macro_feature_instance
    if _macro_feature_instance is None:
        _macro_feature_instance = MacroRegimeFeature()
    return _macro_feature_instance


async def calculate_credit_stress_factor(
    ticker: str = "MARKET",
    as_of_date: Optional[datetime] = None
) -> float:
    """
    Feature Store 호환 인터페이스
    
    Note: ticker는 무시됨 (시장 전체 지표)
    """
    feature = get_macro_feature()
    result = await feature.calculate("credit_stress_factor", as_of_date)
    return result["value"]


async def calculate_dollar_strength_factor(
    ticker: str = "MARKET",
    as_of_date: Optional[datetime] = None
) -> float:
    """Feature Store 호환 인터페이스"""
    feature = get_macro_feature()
    result = await feature.calculate("dollar_strength_factor", as_of_date)
    return result["value"]


async def calculate_debt_pressure_factor(
    ticker: str = "MARKET",
    as_of_date: Optional[datetime] = None
) -> float:
    """Feature Store 호환 인터페이스"""
    feature = get_macro_feature()
    result = await feature.calculate("debt_pressure_factor", as_of_date)
    return result["value"]


async def calculate_macro_risk_score(
    ticker: str = "MARKET",
    as_of_date: Optional[datetime] = None
) -> float:
    """Feature Store 호환 인터페이스"""
    feature = get_macro_feature()
    result = await feature.calculate("macro_risk_score", as_of_date)
    return result["value"]


# =============================================================================
# Demo
# =============================================================================

async def demo_macro_factors():
    """매크로 팩터 데모"""
    print("=" * 80)
    print("Macro Regime Factors Demo")
    print("=" * 80)
    
    feature = MacroRegimeFeature()
    
    # 1. 개별 팩터 계산
    print("\n[1] Individual Factor Calculation")
    print("-" * 40)
    
    credit_result = await feature.calculate("credit_stress_factor")
    print(f"Credit Stress Factor: {credit_result['value']:+.2%}")
    print(f"  Cost: ${credit_result['metadata']['cost_usd']}")
    
    dollar_result = await feature.calculate("dollar_strength_factor")
    print(f"Dollar Strength Factor: {dollar_result['value']:+.2%}")
    
    debt_result = await feature.calculate("debt_pressure_factor")
    print(f"Debt Pressure Factor: {debt_result['value']:+.2%}")
    
    # 2. 모든 팩터 한번에
    print("\n[2] All Factors at Once")
    print("-" * 40)
    
    all_factors = await feature.calculate_all()
    print(f"Total factors calculated: {all_factors['metadata']['factors_count']}")
    print(f"Total cost: ${all_factors['metadata']['total_cost_usd']}")
    
    # 3. 투자 전략 권고
    print("\n[3] Investment Strategy Recommendation")
    print("-" * 40)
    
    recommendation = await feature.get_regime_recommendation()
    print(f"Market Regime: {recommendation['regime']}")
    print(f"Stock Allocation: {recommendation['stock_allocation']:.0%}")
    print(f"Cash Allocation: {recommendation['cash_allocation']:.0%}")
    print(f"Sector Bias: {recommendation['sector_bias']}")
    print(f"\nReasoning: {recommendation['reasoning']}")
    
    # 4. Feature Store 통합 테스트
    print("\n[4] Feature Store Integration Test")
    print("-" * 40)
    
    credit = await calculate_credit_stress_factor()
    dollar = await calculate_dollar_strength_factor()
    debt = await calculate_debt_pressure_factor()
    risk = await calculate_macro_risk_score()
    
    print(f"Credit Stress: {credit:+.2%}")
    print(f"Dollar Strength: {dollar:+.2%}")
    print(f"Debt Pressure: {debt:+.2%}")
    print(f"Macro Risk Score: {risk:.2f}")
    
    print("\n" + "=" * 80)
    print("Demo complete! All factors calculated at $0 cost.")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_macro_factors())