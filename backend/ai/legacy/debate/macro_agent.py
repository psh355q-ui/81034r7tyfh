"""
Macro Agent for War Room Debate System

Role: Macroeconomic analysis specialist
Focuses on: Interest rates, inflation, GDP, employment, market regime

Author: ai-trading-system
Date: 2025-12-21
Updated: 2025-12-27 - Added Yield Curve analysis
"""

import logging
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)


class MacroAgent:
    """
    Macro Agent - 거시경제 분석 전문가
    
    Core Capabilities:
    - Interest rate analysis (Fed policy)
    - Inflation monitoring (CPI, PPI)
    - GDP growth assessment
    - Employment data analysis
    - Market regime classification
    """
    
    def __init__(self):
        self.agent_name = "macro"
        self.vote_weight = 0.10  # 10% voting weight
    
    async def analyze(self, ticker: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze macro environment impact on ticker.
        
        Args:
            ticker: Stock ticker symbol
            context: Optional context (macro indicators, sector data)
        
        Returns:
            {
                "agent": "macro",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": str,
                "macro_factors": {...}
            }
        """
        try:
            logger.info(f"[Macro Agent] Analyzing {ticker}")
            
            if context and "macro_data" in context:
                return await self._analyze_with_real_data(ticker, context["macro_data"])
            else:
                return await self._analyze_mock(ticker)
        
        except Exception as e:
            logger.error(f"[Macro Agent] Error analyzing {ticker}: {e}")
            return self._fallback_response(ticker)
    
    async def _analyze_with_real_data(self, ticker: str, macro_data: Dict) -> Dict:
        """
        Analyze using real macro indicators.

        Expected macro_data format:
        {
            "fed_rate": 5.25,  # %
            "fed_direction": "HIKING|CUTTING|HOLDING",
            "cpi_yoy": 3.2,  # %
            "gdp_growth": 2.5,  # %
            "unemployment": 3.7,  # %
            "market_regime": "RISK_ON|RISK_OFF|NEUTRAL",
            "yield_curve": {  # Optional: Treasury yields
                "2y": 4.5,  # 2-year yield
                "10y": 4.2  # 10-year yield
            },
            "wti_crude": 78.50,  # Optional: WTI Crude oil price ($/barrel)
            "wti_change_30d": 8.5,  # Optional: 30-day oil price change (%)
            "dxy": 103.2,  # Optional: Dollar Index (DXY)
            "dxy_change_30d": 2.1  # Optional: 30-day DXY change (%)
        }
        """
        fed_rate = macro_data.get("fed_rate", 5.0)
        fed_direction = macro_data.get("fed_direction", "HOLDING")
        cpi_yoy = macro_data.get("cpi_yoy", 3.0)
        gdp_growth = macro_data.get("gdp_growth", 2.0)
        unemployment = macro_data.get("unemployment", 4.0)
        market_regime = macro_data.get("market_regime", "NEUTRAL")
        yield_curve_data = macro_data.get("yield_curve", None)

        # Oil and Dollar data (optional)
        wti_crude = macro_data.get("wti_crude", None)
        wti_change_30d = macro_data.get("wti_change_30d", 0.0)
        dxy = macro_data.get("dxy", None)
        dxy_change_30d = macro_data.get("dxy_change_30d", 0.0)
        
        action = "HOLD"
        confidence = 0.5
        confidence_boost = 0.0

        # Yield Curve Analysis (if available) - CHECKED FIRST
        yc_analysis = None
        yield_curve_inverted = False
        if yield_curve_data and "2y" in yield_curve_data and "10y" in yield_curve_data:
            yc_analysis = self._analyze_yield_curve(
                yield_2y=yield_curve_data["2y"],
                yield_10y=yield_curve_data["10y"]
            )

            # Yield Curve Inversion - Strong recession signal (HIGHEST PRIORITY)
            if yc_analysis["signal"] == "INVERTED":
                # 역전된 수익률 곡선 = 경기 침체 신호
                action = "SELL"
                confidence = 0.85
                reasoning = f"{yc_analysis['reasoning']} - 경기 침체 위험 (수익률 곡선 역전)"
                yield_curve_inverted = True

            # Steep Yield Curve - Economic expansion expected
            elif yc_analysis["signal"] == "STEEP":
                confidence_boost += 0.15

            # Flattening Yield Curve - Warning sign
            elif yc_analysis["signal"] == "FLATTENING":
                confidence_boost -= 0.10

        # Only proceed with other signals if yield curve is NOT inverted
        if not yield_curve_inverted:
            # RISK-ON Environment (favorable for stocks)
            if fed_direction == "CUTTING" and cpi_yoy < 3.0:
                action = "BUY"
                confidence = 0.84
                reasoning = f"금리 인하 사이클 + 인플레 진정 (CPI {cpi_yoy:.1f}%) - Risk ON 국면"

            elif gdp_growth > 2.5 and unemployment < 4.0 and cpi_yoy < 3.5:
                action = "BUY"
                confidence = 0.78
                reasoning = f"골디락스 환경 (GDP +{gdp_growth:.1f}%, 실업률 {unemployment:.1f}%, 인플레 안정)"

            # RISK-OFF Environment (unfavorable)
            elif fed_direction == "HIKING" and cpi_yoy > 4.5:
                action = "SELL"
                confidence = 0.76
                reasoning = f"긴축 사이클 + 고인플레 (CPI {cpi_yoy:.1f}%) - Risk OFF 국면"

            elif gdp_growth < 1.0 or unemployment > 5.0:
                action = "SELL"
                confidence = 0.72
                reasoning = f"경기 둔화 우려 (GDP {gdp_growth:.1f}%, 실업률 {unemployment:.1f}%)"

            # NEUTRAL
            else:
                reasoning = f"혼조 (Fed {fed_direction}, GDP {gdp_growth:.1f}%, CPI {cpi_yoy:.1f}%)"
                confidence = 0.65

            # Apply yield curve confidence boost (if not inverted)
            if yc_analysis and yc_analysis["signal"] in ["STEEP", "FLATTENING"]:
                confidence = min(0.95, confidence + confidence_boost)
                reasoning += f" | 수익률곡선 {yc_analysis['spread_bps']:.0f}bps ({yc_analysis['signal']})"

        # Oil Price Analysis (if available)
        oil_analysis = None
        if wti_crude is not None:
            oil_analysis = self._analyze_oil_price(wti_crude, wti_change_30d)
            ticker_sector = self._get_sector(ticker)

            # Apply sector-specific confidence adjustments
            if oil_analysis["signal"] == "HIGH":
                # High oil price
                if ticker_sector == "Energy":
                    confidence_boost += 0.10
                    reasoning += f" | 고유가 (${wti_crude:.1f}) 에너지 섹터 수혜"
                elif ticker_sector in ["Airlines", "Transportation"]:
                    confidence_boost -= 0.08
                    reasoning += f" | 고유가 (${wti_crude:.1f}) 운송 비용 증가"

            elif oil_analysis["signal"] == "LOW":
                # Low oil price
                if ticker_sector == "Energy":
                    confidence_boost -= 0.08
                    reasoning += f" | 저유가 (${wti_crude:.1f}) 에너지 섹터 타격"
                elif ticker_sector in ["Airlines", "Transportation", "Consumer"]:
                    confidence_boost += 0.08
                    reasoning += f" | 저유가 (${wti_crude:.1f}) 비용 절감 수혜"

            # Extreme oil price movements (±20% in 30 days)
            if wti_change_30d > 20:
                confidence_boost -= 0.05  # 급등 = 불확실성
                reasoning += f" | 유가 급등 (+{wti_change_30d:.1f}%)"
            elif wti_change_30d < -20:
                confidence_boost -= 0.05  # 급락 = 불확실성
                reasoning += f" | 유가 급락 ({wti_change_30d:.1f}%)"

        # Dollar Index Analysis (if available)
        dollar_analysis = None
        if dxy is not None:
            dollar_analysis = self._analyze_dollar_index(dxy, dxy_change_30d)
            is_exporter = self._is_us_exporter(ticker)
            is_multinational = self._is_multinational(ticker)

            # Apply exporter/multinational-specific confidence adjustments
            if dollar_analysis["signal"] == "STRONG":
                # Strong dollar (DXY > 105)
                if is_exporter or is_multinational:
                    confidence_boost -= 0.10
                    reasoning += f" | 강달러 (DXY {dxy:.1f}) 수출 기업 불리"
                elif ticker_sector == "Gold":
                    confidence_boost -= 0.08
                    reasoning += f" | 강달러 (DXY {dxy:.1f}) 금 가격 압박"

            elif dollar_analysis["signal"] == "WEAK":
                # Weak dollar (DXY < 95)
                if is_exporter or is_multinational:
                    confidence_boost += 0.10
                    reasoning += f" | 약달러 (DXY {dxy:.1f}) 수출 기업 수혜"
                elif ticker_sector == "Gold":
                    confidence_boost += 0.08
                    reasoning += f" | 약달러 (DXY {dxy:.1f}) 금 가격 상승"

            # Extreme dollar movements (±5% in 30 days)
            if dxy_change_30d > 5:
                confidence_boost -= 0.05  # 급등 = 불확실성
                reasoning += f" | 달러 급등 (+{dxy_change_30d:.1f}%)"
            elif dxy_change_30d < -5:
                confidence_boost -= 0.05  # 급락 = 불확실성
                reasoning += f" | 달러 급락 ({dxy_change_30d:.1f}%)"

        # Apply all accumulated confidence adjustments
        if confidence_boost != 0.0:
            confidence = min(0.95, max(0.40, confidence + confidence_boost))

        macro_factors = {
            "fed_rate": f"{fed_rate:.2f}%",
            "fed_direction": fed_direction,
            "cpi_yoy": f"{cpi_yoy:.1f}%",
            "gdp_growth": f"{gdp_growth:.1f}%",
            "unemployment": f"{unemployment:.1f}%",
            "market_regime": market_regime
        }

        # Add yield curve data to macro_factors
        if yc_analysis:
            macro_factors["yield_curve"] = {
                "spread_2y_10y": f"{yc_analysis['spread_bps']:.0f}bps",
                "signal": yc_analysis["signal"],
                "status": yc_analysis["status"]
            }

        # Add oil price data to macro_factors
        if oil_analysis:
            macro_factors["oil_price"] = {
                "wti_crude": f"${oil_analysis['oil_price']:.2f}/bbl",
                "change_30d": f"{oil_analysis['oil_change_30d']:+.1f}%",
                "signal": oil_analysis["signal"],
                "inflation_pressure": oil_analysis["inflation_pressure"]
            }

        # Add dollar index data to macro_factors
        if dollar_analysis:
            macro_factors["dollar_index"] = {
                "dxy": f"{dollar_analysis['dxy']:.2f}",
                "change_30d": f"{dollar_analysis['dxy_change_30d']:+.1f}%",
                "signal": dollar_analysis["signal"]
            }
        
        return {
            "agent": "macro",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "macro_factors": macro_factors
        }
    
    async def _analyze_mock(self, ticker: str) -> Dict:
        """Mock macro analysis"""
        scenarios = [
            {
                "action": "BUY",
                "confidence": 0.84,
                "reasoning": "Fed 금리 인하 사이클 시작, CPI 2.8%로 목표치 근접 - Risk ON",
                "macro_factors": {
                    "fed_direction": "CUTTING",
                    "cpi_yoy": "2.8%",
                    "market_regime": "RISK_ON"
                }
            },
            {
                "action": "SELL",
                "confidence": 0.74,
                "reasoning": "Fed 매파적 스탠스 유지, CPI 5.2% 고착화 - Risk OFF",
                "macro_factors": {
                    "fed_direction": "HIKING",
                    "cpi_yoy": "5.2%",
                    "market_regime": "RISK_OFF"
                }
            },
            {
                "action": "HOLD",
                "confidence": 0.68,
                "reasoning": "혼조 (Fed 동결, GDP 성장 완만, 인플레 소폭 하락)",
                "macro_factors": {
                    "fed_direction": "HOLDING",
                    "gdp_growth": "1.8%",
                    "market_regime": "NEUTRAL"
                }
            }
        ]
        
        return {
            "agent": "macro",
            **random.choice(scenarios)
        }
    
    def _fallback_response(self, ticker: str) -> Dict:
        """Fallback on error"""
        return {
            "agent": "macro",
            "action": "HOLD",
            "confidence": 0.60,
            "reasoning": f"거시경제 데이터 부족 - {ticker} 매크로 환경 불확실",
            "macro_factors": {
                "error": True
            }
        }

    def _analyze_oil_price(self, wti_price: float, wti_change_30d: float = 0.0) -> Dict:
        """
        유가 분석 (WTI Crude)

        유가 수준:
        - 고유가 (> $90): 인플레 압력 증가, 에너지 섹터 수혜
        - 저유가 (< $60): 소비 여력 증가, 운송/소비재 섹터 수혜
        - 정상 ($60-90): 안정적 수준

        Args:
            wti_price: 현재 WTI 가격 ($/barrel)
            wti_change_30d: 30일 변화율 (%)

        Returns:
            {
                "oil_price": float,
                "oil_change_30d": float,
                "signal": "HIGH|NORMAL|LOW",
                "inflation_pressure": "INCREASING|STABLE|DECREASING",
                "sector_impact": {...},
                "reasoning": str
            }
        """
        # 유가 수준 판단
        if wti_price > 90:
            signal = "HIGH"
            inflation_pressure = "INCREASING"
            sector_impact = {
                "energy": "POSITIVE",  # XLE (Energy ETF)
                "airlines": "NEGATIVE",  # 항공사 비용 증가
                "transportation": "NEGATIVE",  # 운송 비용 증가
                "consumer": "NEGATIVE"  # 소비재 압박
            }
        elif wti_price < 60:
            signal = "LOW"
            inflation_pressure = "DECREASING"
            sector_impact = {
                "energy": "NEGATIVE",
                "airlines": "POSITIVE",
                "transportation": "POSITIVE",
                "consumer": "POSITIVE"
            }
        else:
            signal = "NORMAL"
            inflation_pressure = "STABLE"
            sector_impact = {}

        # 급등/급락 체크
        if wti_change_30d > 20:
            reasoning = f"유가 급등 (${wti_price:.2f}, +{wti_change_30d:.1f}%) - 인플레 압력 증가"
        elif wti_change_30d < -20:
            reasoning = f"유가 급락 (${wti_price:.2f}, {wti_change_30d:.1f}%) - 소비 여력 증가"
        else:
            reasoning = f"유가 {signal} (${wti_price:.2f}/배럴)"

        return {
            "oil_price": wti_price,
            "oil_change_30d": wti_change_30d,
            "signal": signal,
            "inflation_pressure": inflation_pressure,
            "sector_impact": sector_impact,
            "reasoning": reasoning
        }

    def _analyze_dollar_index(self, dxy: float, dxy_change_30d: float = 0.0) -> Dict:
        """
        달러 인덱스 (DXY) 분석

        달러 강도:
        - 강세 (> 105): 수출 기업 불리, 신흥국 압박, 금/원자재 하락
        - 약세 (< 95): 수출 기업 유리, 신흥국 수혜, 금/원자재 상승
        - 중립 (95-105): 안정적 수준

        Args:
            dxy: 현재 달러 인덱스 (기준: 100)
            dxy_change_30d: 30일 변화율 (%)

        Returns:
            {
                "dxy": float,
                "dxy_change_30d": float,
                "signal": "STRONG|NEUTRAL|WEAK",
                "impact": {...},
                "reasoning": str
            }
        """
        # 달러 강도 판단
        if dxy > 105:
            signal = "STRONG"
            impact = {
                "us_exporters": "NEGATIVE",  # 수출 기업 불리
                "multinationals": "NEGATIVE",  # 다국적 기업 불리
                "emerging_markets": "NEGATIVE",  # 신흥국 압박
                "gold": "NEGATIVE",  # 금 가격 하락
                "commodities": "NEGATIVE"  # 원자재 가격 하락
            }
        elif dxy < 95:
            signal = "WEAK"
            impact = {
                "us_exporters": "POSITIVE",
                "multinationals": "POSITIVE",
                "emerging_markets": "POSITIVE",
                "gold": "POSITIVE",
                "commodities": "POSITIVE"
            }
        else:
            signal = "NEUTRAL"
            impact = {}

        # 급등/급락
        if dxy_change_30d > 5:
            reasoning = f"달러 급강세 (DXY {dxy:.2f}, +{dxy_change_30d:.1f}%) - 수출 기업 부담"
        elif dxy_change_30d < -5:
            reasoning = f"달러 급약세 (DXY {dxy:.2f}, {dxy_change_30d:.1f}%) - 수출 유리"
        else:
            reasoning = f"달러 {signal} (DXY {dxy:.2f})"

        return {
            "dxy": dxy,
            "dxy_change_30d": dxy_change_30d,
            "signal": signal,
            "impact": impact,
            "reasoning": reasoning
        }

    def _get_sector(self, ticker: str) -> str:
        """
        티커의 섹터 확인 (간단한 매핑)

        Args:
            ticker: Stock ticker symbol

        Returns:
            Sector name (Energy, Airlines, Transportation, Technology, etc.)
        """
        # 섹터 매핑 (확장 가능)
        SECTOR_MAP = {
            # Energy
            "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy",
            "XLE": "Energy",  # Energy ETF

            # Airlines
            "AAL": "Airlines", "DAL": "Airlines", "UAL": "Airlines", "LUV": "Airlines",
            "JETS": "Airlines",  # Airlines ETF

            # Transportation
            "UPS": "Transportation", "FDX": "Transportation",

            # Technology (often exporters/multinationals)
            "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
            "META": "Technology", "NVDA": "Technology", "AMD": "Technology",

            # Consumer
            "WMT": "Consumer", "TGT": "Consumer", "COST": "Consumer",

            # Financials
            "JPM": "Financials", "BAC": "Financials", "WFC": "Financials",

            # Gold/Commodities
            "GLD": "Gold", "GDX": "Gold", "GOLD": "Gold",
        }

        return SECTOR_MAP.get(ticker, "Unknown")

    def _is_us_exporter(self, ticker: str) -> bool:
        """
        수출 기업 여부 확인

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if major US exporter
        """
        # 주요 수출 기업 (해외 매출 비중 높음)
        EXPORTERS = [
            "AAPL",  # iPhone 해외 판매
            "MSFT",  # 글로벌 소프트웨어
            "GOOGL", # 글로벌 광고
            "NVDA",  # 반도체 수출
            "AMD",   # 반도체 수출
            "INTC",  # 반도체 수출
            "BA",    # Boeing 항공기
            "CAT",   # Caterpillar 건설장비
            "DE",    # Deere 농기계
        ]
        return ticker in EXPORTERS

    def _is_multinational(self, ticker: str) -> bool:
        """
        다국적 기업 여부 확인 (해외 수익 비중 높음)

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if multinational with significant foreign revenue
        """
        # 다국적 기업 (해외 수익 30% 이상)
        MULTINATIONALS = [
            "AAPL", "MSFT", "GOOGL", "META", "AMZN",
            "NVDA", "AMD", "INTC",
            "KO", "PEP", "MCD", "SBUX",  # Consumer brands
            "JNJ", "PFE", "UNH",  # Healthcare
        ]
        return ticker in MULTINATIONALS

    def _analyze_yield_curve(self, yield_2y: float, yield_10y: float) -> Dict:
        """
        수익률 곡선 (Yield Curve) 분석

        수익률 곡선 스프레드 (10Y - 2Y):
        - 역전 (< 0): 경기 침체 신호 (강한 SELL)
        - 평탄화 (0 ~ 25bps): 경기 둔화 조짐
        - 정상 (25 ~ 150bps): 건강한 경제
        - 가파름 (> 150bps): 경기 확장 기대

        Args:
            yield_2y: 2년물 국채 수익률 (%)
            yield_10y: 10년물 국채 수익률 (%)

        Returns:
            {
                "spread_bps": float,  # 스프레드 (basis points)
                "signal": "INVERTED|FLATTENING|NORMAL|STEEP",
                "status": str,  # 상태 설명
                "reasoning": str  # 분석 근거
            }
        """
        # 스프레드 계산 (10Y - 2Y)
        spread = yield_10y - yield_2y
        spread_bps = spread * 100  # Convert to basis points

        # 신호 분류
        if spread < 0:
            # 역전 (Inverted) - 경기 침체 신호
            signal = "INVERTED"
            status = "경기 침체 신호"
            reasoning = f"수익률 곡선 역전 (10Y-2Y = {spread_bps:.0f}bps)"

        elif spread < 0.25:
            # 평탄화 (Flattening) - 경기 둔화 조짐
            signal = "FLATTENING"
            status = "경기 둔화 조짐"
            reasoning = f"수익률 곡선 평탄화 (10Y-2Y = {spread_bps:.0f}bps)"

        elif spread < 1.50:
            # 정상 (Normal) - 건강한 경제
            signal = "NORMAL"
            status = "건강한 경제"
            reasoning = f"정상 수익률 곡선 (10Y-2Y = {spread_bps:.0f}bps)"

        else:
            # 가파름 (Steep) - 경기 확장 기대
            signal = "STEEP"
            status = "경기 확장 기대"
            reasoning = f"수익률 곡선 가파름 (10Y-2Y = {spread_bps:.0f}bps)"

        return {
            "spread_bps": spread_bps,
            "signal": signal,
            "status": status,
            "reasoning": reasoning
        }
