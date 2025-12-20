"""
Enhanced ChatGPT Strategy with Macro Regime Detection

Gemini + ChatGPT 제안을 통합한 시장 국면 판단 전략

Features:
1. 신용 스프레드 기반 위기 감지 (ChatGPT 제안)
2. 환율 기반 Risk-Off 신호 (사용자 제안)
3. 국가 부채 압박 모니터링 (YouTube 시나리오)
4. M7 유동성 고갈 이벤트 감지 (Gemini 제안)
5. 동적 포트폴리오 비중 조절

비용: $0.03/일 = $0.90/월
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..features.macro_regime_factors import MacroRegimeFeature

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """시장 국면 정의"""
    BULL = "Bull"           # 강세장 - 공격적 투자
    SIDEWAYS = "Sideways"   # 횡보장 - 중립적 투자
    RISK_OFF = "Risk-Off"   # 위험회피 - 방어적 투자
    CRASH = "Crash"         # 위기 - 현금 확보


class EnhancedChatGPTStrategy:
    """
    강화된 ChatGPT 전략
    
    ChatGPT-4o mini를 사용하여 시장 국면을 판단하고,
    매크로 팩터를 통합하여 투자 전략을 수립합니다.
    
    Cost: $0.03/day = $0.90/month
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        use_macro_factors: bool = True,
    ):
        """
        Args:
            openai_api_key: OpenAI API 키 (없으면 룰 기반만 사용)
            use_macro_factors: 매크로 팩터 사용 여부
        """
        self.api_key = openai_api_key
        self.use_macro_factors = use_macro_factors
        self.macro_feature = MacroRegimeFeature() if use_macro_factors else None
        
        # 섹터별 기본 가중치
        self.default_sector_weights = {
            "Information Technology": 0.25,
            "Health Care": 0.15,
            "Financials": 0.12,
            "Consumer Discretionary": 0.12,
            "Communication Services": 0.10,
            "Industrials": 0.08,
            "Consumer Staples": 0.06,
            "Energy": 0.05,
            "Utilities": 0.03,
            "Real Estate": 0.02,
            "Materials": 0.02,
        }
        
        # 국면별 섹터 조정
        self.regime_sector_adjustments = {
            MarketRegime.BULL: {
                "Information Technology": 1.3,
                "Consumer Discretionary": 1.2,
                "Communication Services": 1.2,
                "Consumer Staples": 0.6,
                "Utilities": 0.5,
            },
            MarketRegime.SIDEWAYS: {
                "Information Technology": 1.0,
                "Health Care": 1.1,
                "Consumer Staples": 1.2,
                "Utilities": 1.1,
            },
            MarketRegime.RISK_OFF: {
                "Consumer Staples": 1.5,
                "Utilities": 1.5,
                "Health Care": 1.3,
                "Information Technology": 0.7,
                "Consumer Discretionary": 0.6,
            },
            MarketRegime.CRASH: {
                "Consumer Staples": 2.0,
                "Utilities": 1.8,
                "Health Care": 1.5,
                "Information Technology": 0.3,
                "Consumer Discretionary": 0.2,
                "Communication Services": 0.4,
            },
        }
    
    async def detect_market_regime(
        self,
        market_context: Dict[str, Any],
        news_headlines: Optional[List[str]] = None,
    ) -> MarketRegime:
        """
        통합된 시장 국면 판단
        
        우선순위 (ChatGPT 제안):
        1. 신용 스트레스 + 강달러 = CRASH (선행 지표)
        2. 부채 압박 + M7 유동성 경고 = RISK_OFF (중기 지표)
        3. VIX/모멘텀 = 후행 지표
        
        Args:
            market_context: 시장 데이터 (VIX, S&P 500 모멘텀 등)
            news_headlines: 최근 뉴스 헤드라인
            
        Returns:
            MarketRegime
        """
        logger.info("Detecting market regime...")
        
        # === 1순위: 매크로 팩터 기반 판단 (선행 지표) ===
        if self.use_macro_factors and self.macro_feature:
            macro_regime = await self._detect_macro_regime(
                market_context,
                news_headlines or []
            )
            
            # 매크로가 CRASH 또는 RISK_OFF를 감지하면 최우선 적용
            if macro_regime in [MarketRegime.CRASH, MarketRegime.RISK_OFF]:
                logger.warning(f"[MACRO] Critical signal detected: {macro_regime}")
                return macro_regime
        
        # === 2순위: 기존 시장 지표 (후행 지표) ===
        stock_regime = self._detect_stock_market_regime(market_context)
        
        logger.info(f"Final regime: {stock_regime}")
        return stock_regime
    
    async def _detect_macro_regime(
        self,
        market_context: Dict[str, Any],
        news_headlines: List[str],
    ) -> MarketRegime:
        """
        매크로 팩터 기반 국면 판단
        
        ChatGPT 제안 로직:
        - 신용 스트레스 > 0.3 AND 달러 강세 > 0.05 = CRASH
        - 부채 압박 > 0.10 AND M7 유동성 경고 = RISK_OFF
        """
        # 매크로 팩터 가져오기
        if "credit_stress_factor" in market_context:
            # 이미 context에 있으면 사용
            credit_stress = market_context.get("credit_stress_factor", 0.0)
            dollar_strength = market_context.get("dollar_strength_factor", 0.0)
            debt_pressure = market_context.get("debt_pressure_factor", 0.0)
        else:
            # Feature Store에서 계산
            factors = await self.macro_feature.calculate_all()
            credit_stress = factors.get("credit_stress_factor", {}).get("value", 0.0)
            dollar_strength = factors.get("dollar_strength_factor", {}).get("value", 0.0)
            debt_pressure = factors.get("debt_pressure_factor", {}).get("value", 0.0)
        
        # === 조건 1: 신용 경색 + 강달러 = CRASH ===
        if credit_stress > 0.3 and dollar_strength > 0.05:
            logger.critical(
                f"[REGIME] CRASH detected! "
                f"Credit stress={credit_stress:+.2%}, "
                f"Dollar strength={dollar_strength:+.2%}"
            )
            return MarketRegime.CRASH
        
        # === 조건 2: 2-Sigma 돌파 = CRASH ===
        # ChatGPT 제안: HY 스프레드가 1년 평균 + 2σ 초과
        is_2sigma = market_context.get("is_2sigma_breach", False)
        if is_2sigma:
            logger.critical("[REGIME] CRASH detected! HY Spread > 2-Sigma threshold")
            return MarketRegime.CRASH
        
        # === 조건 3: 유동성 고갈 시나리오 = RISK_OFF ===
        # Gemini 제안: M7 채권 발행 감지
        liquidity_result = await self.macro_feature._calculate_liquidity_warning(
            news_headlines,
            {"ttl_days": 1, "cost_usd": 0.0, "data_source": "NEWS", "description": ""}
        )
        m7_liquidity_warning = liquidity_result.get("value", False)
        
        if debt_pressure > 0.10 and m7_liquidity_warning:
            logger.warning(
                f"[REGIME] RISK_OFF detected! "
                f"Debt pressure={debt_pressure:+.2%}, "
                f"M7 liquidity warning={m7_liquidity_warning}"
            )
            return MarketRegime.RISK_OFF
        
        # === 조건 4: 달러만 강세 (중간 수준) ===
        if dollar_strength > 0.08:
            logger.info(f"[REGIME] Strong dollar ({dollar_strength:+.2%}), leaning RISK_OFF")
            return MarketRegime.RISK_OFF
        
        # === 조건 5: 신용만 스트레스 (중간 수준) ===
        if credit_stress > 0.4:
            logger.info(f"[REGIME] High credit stress ({credit_stress:+.2%}), RISK_OFF")
            return MarketRegime.RISK_OFF
        
        # 매크로는 정상
        return MarketRegime.BULL
    
    def _detect_stock_market_regime(
        self,
        market_context: Dict[str, Any]
    ) -> MarketRegime:
        """
        주식 시장 지표 기반 국면 판단 (기존 로직)
        
        후행 지표:
        - VIX
        - S&P 500 모멘텀
        """
        vix = market_context.get("vix", 20.0)
        sp500_mom_20d = market_context.get("sp500_mom_20d", 0.0)
        
        # CRASH: VIX > 35 AND 모멘텀 < -10%
        if vix > 35.0 and sp500_mom_20d < -0.10:
            logger.warning(f"[STOCK] CRASH: VIX={vix}, Mom={sp500_mom_20d:+.2%}")
            return MarketRegime.CRASH
        
        # RISK_OFF: VIX > 28 AND 모멘텀 < -5%
        if vix > 28.0 and sp500_mom_20d < -0.05:
            logger.info(f"[STOCK] RISK_OFF: VIX={vix}, Mom={sp500_mom_20d:+.2%}")
            return MarketRegime.RISK_OFF
        
        # SIDEWAYS: VIX > 22 OR |모멘텀| < 2%
        if vix > 22.0 or abs(sp500_mom_20d) < 0.02:
            logger.info(f"[STOCK] SIDEWAYS: VIX={vix}, Mom={sp500_mom_20d:+.2%}")
            return MarketRegime.SIDEWAYS
        
        # BULL: 기본
        logger.info(f"[STOCK] BULL: VIX={vix}, Mom={sp500_mom_20d:+.2%}")
        return MarketRegime.BULL
    
    def adjust_sector_weights(
        self,
        regime: MarketRegime,
    ) -> Dict[str, float]:
        """
        시장 국면에 따른 섹터 가중치 조정
        
        Args:
            regime: 현재 시장 국면
            
        Returns:
            조정된 섹터 가중치 (합 = 1.0)
        """
        adjustments = self.regime_sector_adjustments.get(regime, {})
        
        adjusted_weights = {}
        for sector, base_weight in self.default_sector_weights.items():
            multiplier = adjustments.get(sector, 1.0)
            adjusted_weights[sector] = base_weight * multiplier
        
        # 정규화 (합 = 1.0)
        total = sum(adjusted_weights.values())
        normalized = {k: v / total for k, v in adjusted_weights.items()}
        
        return normalized
    
    def get_position_sizing(
        self,
        regime: MarketRegime,
    ) -> Dict[str, float]:
        """
        시장 국면에 따른 포지션 크기 결정
        
        ChatGPT 제안 기반:
        - CRASH: 주식 10%, 현금 90%
        - RISK_OFF: 주식 30%, 현금 70%
        - SIDEWAYS: 주식 50%, 현금 50%
        - BULL: 주식 80%, 현금 20%
        
        Returns:
            {
                "stock_allocation": float,
                "cash_allocation": float,
                "max_position_size": float,
            }
        """
        if regime == MarketRegime.CRASH:
            return {
                "stock_allocation": 0.10,
                "cash_allocation": 0.90,
                "max_position_size": 0.02,  # 개별 종목 최대 2%
            }
        elif regime == MarketRegime.RISK_OFF:
            return {
                "stock_allocation": 0.30,
                "cash_allocation": 0.70,
                "max_position_size": 0.03,  # 개별 종목 최대 3%
            }
        elif regime == MarketRegime.SIDEWAYS:
            return {
                "stock_allocation": 0.50,
                "cash_allocation": 0.50,
                "max_position_size": 0.04,  # 개별 종목 최대 4%
            }
        else:  # BULL
            return {
                "stock_allocation": 0.80,
                "cash_allocation": 0.20,
                "max_position_size": 0.05,  # 개별 종목 최대 5%
            }
    
    async def get_trading_signals(
        self,
        market_context: Dict[str, Any],
        news_headlines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        완전한 트레이딩 시그널 생성
        
        Returns:
            {
                "regime": MarketRegime,
                "sector_weights": Dict[str, float],
                "position_sizing": Dict[str, float],
                "risk_level": str,
                "action_summary": str,
            }
        """
        # 1. 국면 판단
        regime = await self.detect_market_regime(market_context, news_headlines)
        
        # 2. 섹터 가중치
        sector_weights = self.adjust_sector_weights(regime)
        
        # 3. 포지션 크기
        position_sizing = self.get_position_sizing(regime)
        
        # 4. 리스크 레벨
        risk_level = self._calculate_risk_level(regime)
        
        # 5. 액션 요약
        action_summary = self._generate_action_summary(regime, position_sizing)
        
        return {
            "regime": regime.value,
            "sector_weights": sector_weights,
            "position_sizing": position_sizing,
            "risk_level": risk_level,
            "action_summary": action_summary,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _calculate_risk_level(self, regime: MarketRegime) -> str:
        """리스크 레벨 계산"""
        mapping = {
            MarketRegime.BULL: "LOW",
            MarketRegime.SIDEWAYS: "MODERATE",
            MarketRegime.RISK_OFF: "HIGH",
            MarketRegime.CRASH: "CRITICAL",
        }
        return mapping.get(regime, "UNKNOWN")
    
    def _generate_action_summary(
        self,
        regime: MarketRegime,
        position_sizing: Dict[str, float]
    ) -> str:
        """액션 요약 생성"""
        stock_pct = position_sizing["stock_allocation"] * 100
        cash_pct = position_sizing["cash_allocation"] * 100
        
        if regime == MarketRegime.CRASH:
            return (
                f"🚨 CRASH REGIME: 즉시 현금 비중을 {cash_pct:.0f}%로 확대. "
                f"신용 경색 또는 유동성 고갈 위험. 방어주만 {stock_pct:.0f}% 유지."
            )
        elif regime == MarketRegime.RISK_OFF:
            return (
                f"⚠️ RISK-OFF REGIME: 현금 비중 {cash_pct:.0f}% 권장. "
                f"방어 섹터(Consumer Staples, Utilities, Health Care) 위주로 "
                f"{stock_pct:.0f}% 투자."
            )
        elif regime == MarketRegime.SIDEWAYS:
            return (
                f"📊 SIDEWAYS REGIME: 밸런스 포트폴리오 유지. "
                f"주식 {stock_pct:.0f}%, 현금 {cash_pct:.0f}%. "
                f"중립적 섹터 배분."
            )
        else:  # BULL
            return (
                f"🚀 BULL REGIME: 공격적 투자 가능. "
                f"주식 {stock_pct:.0f}%, 현금 {cash_pct:.0f}%. "
                f"성장 섹터(Tech, Consumer Disc.) 오버웨이트."
            )
    
    def get_metrics(self) -> Dict:
        """전략 메트릭"""
        return {
            "strategy_name": "EnhancedChatGPTStrategy",
            "use_macro_factors": self.use_macro_factors,
            "cost_per_day": 0.03,  # ChatGPT-4o mini
            "cost_per_month": 0.90,
            "features": [
                "credit_stress_detection",
                "dollar_strength_monitoring",
                "debt_pressure_tracking",
                "m7_liquidity_warning",
                "dynamic_sector_weighting",
            ]
        }


# =============================================================================
# Demo
# =============================================================================

async def demo_enhanced_strategy():
    """강화된 전략 데모"""
    print("=" * 80)
    print("Enhanced ChatGPT Strategy Demo")
    print("=" * 80)
    
    strategy = EnhancedChatGPTStrategy(use_macro_factors=True)
    
    # 테스트 시나리오들
    scenarios = [
        {
            "name": "Normal Bull Market",
            "context": {
                "vix": 15.0,
                "sp500_mom_20d": 0.05,
                "credit_stress_factor": 0.05,
                "dollar_strength_factor": -0.02,
                "debt_pressure_factor": 0.03,
            },
            "news": [],
        },
        {
            "name": "Credit Crisis (ChatGPT Scenario)",
            "context": {
                "vix": 25.0,
                "sp500_mom_20d": -0.03,
                "credit_stress_factor": 0.35,  # > 0.3
                "dollar_strength_factor": 0.08,  # > 0.05
                "debt_pressure_factor": 0.08,
            },
            "news": [],
        },
        {
            "name": "M7 Liquidity Crunch (YouTube Scenario)",
            "context": {
                "vix": 20.0,
                "sp500_mom_20d": 0.01,
                "credit_stress_factor": 0.15,
                "dollar_strength_factor": 0.03,
                "debt_pressure_factor": 0.12,  # > 0.10
            },
            "news": [
                "Meta announces $30 billion bond offering to fund AI infrastructure",
                "Google plans massive data center expansion with $25B investment",
            ],
        },
        {
            "name": "Stock Market Crash (Traditional)",
            "context": {
                "vix": 40.0,
                "sp500_mom_20d": -0.15,
                "credit_stress_factor": 0.20,
                "dollar_strength_factor": 0.04,
                "debt_pressure_factor": 0.06,
            },
            "news": [],
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Scenario {i}] {scenario['name']}")
        print("-" * 60)
        
        # 국면 판단 (매크로 팩터 사용하지 않고 context에서 직접)
        strategy.use_macro_factors = False  # context에 이미 팩터가 있음
        
        signals = await strategy.get_trading_signals(
            scenario["context"],
            scenario["news"]
        )
        
        print(f"Regime: {signals['regime']}")
        print(f"Risk Level: {signals['risk_level']}")
        print(f"\nPosition Sizing:")
        print(f"  Stock: {signals['position_sizing']['stock_allocation']:.0%}")
        print(f"  Cash: {signals['position_sizing']['cash_allocation']:.0%}")
        print(f"  Max Position: {signals['position_sizing']['max_position_size']:.0%}")
        
        print(f"\nTop 3 Sector Weights:")
        sorted_sectors = sorted(
            signals['sector_weights'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for sector, weight in sorted_sectors[:3]:
            print(f"  {sector}: {weight:.1%}")
        
        print(f"\n{signals['action_summary']}")
    
    # 메트릭
    print("\n" + "=" * 80)
    print("Strategy Metrics:")
    metrics = strategy.get_metrics()
    print(f"  Cost: ${metrics['cost_per_month']}/month")
    print(f"  Features: {len(metrics['features'])}")
    for feature in metrics['features']:
        print(f"    - {feature}")
    
    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_enhanced_strategy())