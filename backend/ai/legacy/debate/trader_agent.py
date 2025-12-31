"""
Trader Agent for War Room Debate System

Role: Short-term technical analysis specialist
Focuses on: Price action, chart patterns, momentum indicators, volume analysis

Author: ai-trading-system
Date: 2025-12-21
Updated: 2025-12-27 - Added Support/Resistance detection, Multi-Timeframe analysis
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random  # Temporary for mock implementation

logger = logging.getLogger(__name__)


class TraderAgent:
    """
    Trader Agent - 단기 기술적 분석 전문가
    
    Core Capabilities:
    - Technical Analysis (RSI, MACD, Moving Averages)
    - Entry/Exit Signals
    - Risk/Reward Calculation
    """
    
    def __init__(self):
        self.agent_name = "trader"
        self.vote_weight = 0.15  # 15% voting weight
    
    async def analyze(self, ticker: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze ticker using technical indicators.
        
        Args:
            ticker: Stock ticker symbol
            context: Optional market context (price data, indicators)
        
        Returns:
            {
                "agent": "trader",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": str,
                "technical_factors": {...}
            }
        """
        try:
            logger.info(f"[Trader Agent] Analyzing {ticker}")
            
            # TODO: Replace with real technical analysis
            # For now, use simplified logic based on context or randomization
            
            if context and "technical_data" in context:
                return await self._analyze_with_real_data(ticker, context["technical_data"])
            else:
                return await self._analyze_mock(ticker)
        
        except Exception as e:
            logger.error(f"[Trader Agent] Error analyzing {ticker}: {e}")
            return self._fallback_response(ticker)
    
    async def _analyze_with_real_data(self, ticker: str, technical_data: Dict) -> Dict:
        """
        Analyze using real technical indicators.

        Expected technical_data format:
        {
            "rsi": 45.0,
            "macd": "BULLISH_CROSS",
            "ma20": 195.0,
            "ma50": 190.0,
            "volume_change": 1.5,  # 150% increase
            "price": 197.50,
            "ohlcv_data": [...]  # Optional: For support/resistance analysis
            "ohlcv_weekly": [...]  # Optional: Weekly data for multi-timeframe
            "ohlcv_monthly": [...]  # Optional: Monthly data for multi-timeframe
            "bollinger_bands": {  # Optional: Pre-calculated Bollinger Bands
                "upper": 205.0,
                "middle": 195.0,
                "lower": 185.0
            }
        }
        """
        rsi = technical_data.get("rsi", 50)
        macd_signal = technical_data.get("macd", "NEUTRAL")
        ma20 = technical_data.get("ma20", 0)
        ma50 = technical_data.get("ma50", 0)
        volume_change = technical_data.get("volume_change", 1.0)
        price = technical_data.get("price", 0)
        ohlcv_data = technical_data.get("ohlcv_data", [])
        bollinger_bands = technical_data.get("bollinger_bands", None)

        # Decision logic based on SKILL.md
        action = "HOLD"
        confidence = 0.5
        confidence_boost = 0.0
        technical_factors = {}

        # Multi-Timeframe Analysis (if weekly/monthly data available)
        mtf_analysis = None
        ohlcv_weekly = technical_data.get("ohlcv_weekly", [])
        ohlcv_monthly = technical_data.get("ohlcv_monthly", [])

        if ohlcv_data and ohlcv_weekly and ohlcv_monthly:
            mtf_analysis = self._analyze_multi_timeframe(
                daily_data=ohlcv_data,
                weekly_data=ohlcv_weekly,
                monthly_data=ohlcv_monthly
            )
            technical_factors["multi_timeframe"] = {
                "daily_trend": mtf_analysis["daily_trend"],
                "weekly_trend": mtf_analysis["weekly_trend"],
                "monthly_trend": mtf_analysis["monthly_trend"],
                "alignment_score": f"{mtf_analysis['alignment_score']:.2f}",
                "alignment_status": mtf_analysis["alignment_status"]
            }

        # Support/Resistance Analysis (if OHLCV data available)
        sr_analysis = None
        if ohlcv_data and len(ohlcv_data) >= 11:
            sr_analysis = self._find_support_resistance(ohlcv_data)
            technical_factors["support_resistance"] = {
                "nearest_support": sr_analysis["nearest_support"],
                "nearest_resistance": sr_analysis["nearest_resistance"],
                "support_distance": f"{sr_analysis['support_distance_pct']:.2f}%" if sr_analysis['support_distance_pct'] else "N/A",
                "resistance_distance": f"{sr_analysis['resistance_distance_pct']:.2f}%" if sr_analysis['resistance_distance_pct'] else "N/A"
            }

        # Bollinger Bands Analysis (if available or can be calculated)
        bb_analysis = None
        if bollinger_bands:
            # Use pre-calculated Bollinger Bands
            bb_analysis = self._analyze_bollinger_bands(price, bollinger_bands)
        elif ohlcv_data and len(ohlcv_data) >= 20:
            # Calculate Bollinger Bands from OHLCV data
            bb = self._calculate_bollinger_bands(ohlcv_data)
            bb_analysis = self._analyze_bollinger_bands(price, bb)

        if bb_analysis:
            technical_factors["bollinger_bands"] = {
                "position": bb_analysis["position"],
                "band_width_pct": f"{bb_analysis['band_width_pct']:.2f}%",
                "price_position": bb_analysis["price_position"],
                "signal": bb_analysis["signal"]
            }

        # BUY Signals
        if ma20 > ma50 and rsi < 50 and volume_change > 1.3:
            # Golden cross + RSI not overbought + volume increase
            action = "BUY"
            confidence = min(0.90, 0.7 + (volume_change - 1.0) * 0.2)
            reasoning = f"골든크로스 발생 (MA20 > MA50), 거래량 증가 (+{(volume_change-1)*100:.0f}%), RSI {rsi:.0f} (중립)"

        elif rsi < 30 and volume_change > 1.2:
            # Oversold + volume confirmation
            action = "BUY"
            confidence = 0.85
            reasoning = f"과매도 구간 진입 (RSI {rsi:.0f}), 거래량 증가로 반등 가능성"

        # SELL Signals
        elif ma20 < ma50 and rsi > 70:
            # Death cross + overbought
            action = "SELL"
            confidence = 0.80
            reasoning = f"데드크로스 발생 (MA20 < MA50), 과매수 구간 (RSI {rsi:.0f})"

        elif rsi > 75 and volume_change < 0.8:
            # Overbought + declining volume
            action = "SELL"
            confidence = 0.75
            reasoning = f"과매수 + 거래량 감소 (RSI {rsi:.0f}, 거래량 {(volume_change-1)*100:+.0f}%)"

        # HOLD (neutral signals)
        else:
            trend = "상승" if ma20 > ma50 else "하락" if ma20 < ma50 else "횡보"
            reasoning = f"관망 추천 (추세: {trend}, RSI {rsi:.0f}, 거래량 변화 {(volume_change-1)*100:+.0f}%)"
            confidence = 0.6

        # Multi-Timeframe Alignment Boost/Penalty
        if mtf_analysis:
            alignment_score = mtf_analysis["alignment_score"]
            alignment_status = mtf_analysis["alignment_status"]

            if alignment_score >= 0.8:
                # Strong alignment across all timeframes
                confidence_boost += 0.2
                reasoning += f" | 타임프레임 정렬 ({alignment_status}, {alignment_score:.2f})"
            elif alignment_score >= 0.6:
                # Moderate alignment
                confidence_boost += 0.1
                reasoning += f" | 타임프레임 정렬 ({alignment_status}, {alignment_score:.2f})"
            elif alignment_score <= 0.3:
                # Conflicting timeframes - reduce confidence significantly
                confidence_boost -= 0.3
                reasoning += f" | 타임프레임 충돌 경고 ({alignment_status}, {alignment_score:.2f})"

            # Cross-timeframe trend confirmation
            daily_trend = mtf_analysis["daily_trend"]
            weekly_trend = mtf_analysis["weekly_trend"]
            monthly_trend = mtf_analysis["monthly_trend"]

            # Override HOLD to BUY if all timeframes bullish
            if action == "HOLD" and daily_trend == "UPTREND" and weekly_trend == "UPTREND" and monthly_trend == "UPTREND":
                action = "BUY"
                confidence = 0.75
                reasoning = f"모든 타임프레임 상승세 (월봉/주봉/일봉 정렬) - 매수 기회"

            # Override HOLD to SELL if all timeframes bearish
            elif action == "HOLD" and daily_trend == "DOWNTREND" and weekly_trend == "DOWNTREND" and monthly_trend == "DOWNTREND":
                action = "SELL"
                confidence = 0.75
                reasoning = f"모든 타임프레임 하락세 (월봉/주봉/일봉 정렬) - 매도 신호"

        # Support/Resistance Boost
        if sr_analysis:
            support_dist = sr_analysis['support_distance_pct']
            resistance_dist = sr_analysis['resistance_distance_pct']
            nearest_support = sr_analysis['nearest_support']
            nearest_resistance = sr_analysis['nearest_resistance']

            # 지지선 근처 (2% 이내) = 매수 기회
            if action in ["BUY", "HOLD"] and support_dist and support_dist < 2.0:
                confidence_boost += 0.15
                reasoning += f" | 지지선 근처 매수 기회 (${nearest_support:.2f}, -{support_dist:.1f}%)"

            # 저항선 돌파 = 강한 매수
            if action == "BUY" and nearest_resistance and price > nearest_resistance:
                confidence_boost += 0.2
                reasoning += f" | 저항선 돌파 (${nearest_resistance:.2f})"

            # 저항선 근처 (2% 이내) = 매도 압력
            if action in ["SELL", "HOLD"] and resistance_dist and resistance_dist < 2.0:
                if action == "HOLD":
                    action = "SELL"
                    confidence = 0.65
                else:
                    confidence_boost += 0.1
                reasoning += f" | 저항선 근처 매도 압력 (${nearest_resistance:.2f}, +{resistance_dist:.1f}%)"

        # Bollinger Bands Signal Integration
        if bb_analysis:
            bb_signal = bb_analysis["signal"]
            bb_position = bb_analysis["position"]
            band_width_pct = bb_analysis["band_width_pct"]

            # 과매도 구간 (하단 밴드 돌파)
            if bb_signal == "OVERSOLD" and action in ["BUY", "HOLD"]:
                if action == "HOLD":
                    action = "BUY"
                    confidence = 0.75
                    reasoning = f"볼린저밴드 하단 돌파 (과매도) - 반등 매수 기회"
                else:
                    confidence_boost += 0.15
                    reasoning += f" | 볼린저밴드 하단 ({bb_position})"

            # 과매수 구간 (상단 밴드 돌파)
            elif bb_signal == "OVERBOUGHT" and action in ["SELL", "HOLD"]:
                if action == "HOLD":
                    action = "SELL"
                    confidence = 0.70
                    reasoning = f"볼린저밴드 상단 돌파 (과매수) - 조정 매도 신호"
                else:
                    confidence_boost += 0.1
                    reasoning += f" | 볼린저밴드 상단 ({bb_position})"

            # 밴드폭 축소 (Squeeze) - 변동성 축소 후 돌파 대기
            elif bb_signal == "SQUEEZE":
                if band_width_pct < 5.0:  # 밴드폭 5% 미만
                    # 변동성 축소 구간 - 관망
                    if action == "BUY" or action == "SELL":
                        confidence_boost -= 0.1  # 신뢰도 감소
                    reasoning += f" | 볼린저밴드 축소 (변동성 감소, 돌파 대기)"

            # 밴드폭 확장 (Expansion) - 강한 추세
            elif bb_signal == "EXPANSION":
                if band_width_pct > 15.0:  # 밴드폭 15% 이상
                    # 강한 추세 진행 중
                    if action == "BUY" or action == "SELL":
                        confidence_boost += 0.1
                        reasoning += f" | 볼린저밴드 확장 (강한 추세)"

        # Final confidence adjustment
        confidence = min(0.95, confidence + confidence_boost)

        technical_factors.update({
            "trend": "UPTREND" if ma20 > ma50 else "DOWNTREND" if ma20 < ma50 else "SIDEWAYS",
            "rsi": rsi,
            "macd": macd_signal,
            "volume_change": f"{(volume_change-1)*100:+.0f}%",
            "ma20": ma20,
            "ma50": ma50
        })

        return {
            "agent": "trader",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "technical_factors": technical_factors
        }
    
    async def _analyze_mock(self, ticker: str) -> Dict:
        """
        Mock analysis when real data is unavailable.
        Uses randomized but realistic patterns.
        """
        # Simulate technical analysis with randomized but logical combinations
        scenarios = [
            {
                "action": "BUY",
                "confidence": 0.85,
                "reasoning": "골든크로스 발생, 거래량 급증 (전일 대비 +150%), RSI 45 (중립 구간)",
                "technical_factors": {
                    "trend": "UPTREND",
                    "rsi": 45,
                    "macd": "BULLISH_CROSS",
                    "volume_change": "+150%"
                }
            },
            {
                "action": "SELL",
                "confidence": 0.75,
                "reasoning": "과매수 구간 진입 (RSI 78), 데드크로스 발생, 거래량 감소 -20%",
                "technical_factors": {
                    "trend": "DOWNTREND",
                    "rsi": 78,
                    "macd": "BEARISH_CROSS",
                    "volume_change": "-20%"
                }
            },
            {
                "action": "HOLD",
                "confidence": 0.60,
                "reasoning": "횡보 추세, RSI 중립 (52), 거래량 평균 수준, 방향성 불명확",
                "technical_factors": {
                    "trend": "SIDEWAYS",
                    "rsi": 52,
                    "macd": "NEUTRAL",
                    "volume_change": "+5%"
                }
            },
            {
                "action": "BUY",
                "confidence": 0.90,
                "reasoning": "강한 지지선 반등, 돌파성 거래량 (+200%), MACD 골든크로스",
                "technical_factors": {
                    "trend": "STRONG_UPTREND",
                    "rsi": 48,
                    "macd": "BULLISH_CROSS",
                    "volume_change": "+200%"
                }
            }
        ]
        
        scenario = random.choice(scenarios)
        
        return {
            "agent": "trader",
            **scenario
        }
    
    def _fallback_response(self, ticker: str) -> Dict:
        """Fallback conservative response on error"""
        return {
            "agent": "trader",
            "action": "HOLD",
            "confidence": 0.50,
            "reasoning": f"기술적 분석 실패 - {ticker} 데이터 수신 오류로 관망 추천",
            "technical_factors": {
                "error": True
            }
        }

    def _find_support_resistance(self, ohlcv_data: List[Dict]) -> Dict:
        """
        최근 고점/저점 기반 지지선/저항선 탐지 (Pivot Point 방식)

        Args:
            ohlcv_data: List of OHLCV bars with keys: 'high', 'low', 'close'

        Returns:
            {
                "support_levels": [float],  # 지지선 목록 (최대 3개)
                "resistance_levels": [float],  # 저항선 목록 (최대 3개)
                "nearest_support": float,  # 현재가 아래 가장 가까운 지지선
                "nearest_resistance": float,  # 현재가 위 가장 가까운 저항선
                "support_distance_pct": float,  # 지지선까지 거리 (%)
                "resistance_distance_pct": float  # 저항선까지 거리 (%)
            }

        방법:
        - Pivot High: 좌우 5개 봉보다 높은 고점 → 저항선
        - Pivot Low: 좌우 5개 봉보다 낮은 저점 → 지지선
        """
        if len(ohlcv_data) < 11:  # 최소 11개 봉 필요 (좌5 + 중1 + 우5)
            return {
                "support_levels": [],
                "resistance_levels": [],
                "nearest_support": None,
                "nearest_resistance": None,
                "support_distance_pct": None,
                "resistance_distance_pct": None
            }

        highs = [bar['high'] for bar in ohlcv_data]
        lows = [bar['low'] for bar in ohlcv_data]

        resistance_levels = []
        support_levels = []

        # Pivot Point 탐지 (좌우 5개 봉 확인)
        for i in range(5, len(ohlcv_data) - 5):
            # Pivot High (저항선)
            left_highs = highs[i-5:i]
            right_highs = highs[i+1:i+6]
            if all(highs[i] > h for h in left_highs) and all(highs[i] > h for h in right_highs):
                resistance_levels.append(highs[i])

            # Pivot Low (지지선)
            left_lows = lows[i-5:i]
            right_lows = lows[i+1:i+6]
            if all(lows[i] < l for l in left_lows) and all(lows[i] < l for l in right_lows):
                support_levels.append(lows[i])

        # 최근 3개 저항선/지지선만 사용 (내림차순 정렬)
        resistance_levels = sorted(set(resistance_levels), reverse=True)[:3]
        support_levels = sorted(set(support_levels), reverse=True)[:3]

        current_price = ohlcv_data[-1]['close']

        # 현재가와 지지/저항 거리 계산
        support_below = [s for s in support_levels if s < current_price]
        resistance_above = [r for r in resistance_levels if r > current_price]

        nearest_support = max(support_below) if support_below else None
        nearest_resistance = min(resistance_above) if resistance_above else None

        support_distance_pct = ((current_price - nearest_support) / current_price * 100) if nearest_support else None
        resistance_distance_pct = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None

        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "support_distance_pct": support_distance_pct,
            "resistance_distance_pct": resistance_distance_pct
        }

    def _analyze_multi_timeframe(self, daily_data: List[Dict], weekly_data: List[Dict], monthly_data: List[Dict]) -> Dict:
        """
        멀티 타임프레임 분석 (일봉, 주봉, 월봉)

        전략:
        - 월봉 추세 확인 → 주봉 추세 확인 → 일봉 진입 타이밍
        - 상위 타임프레임 추세와 일치할 때만 강한 신호

        Args:
            daily_data: 최근 100일 OHLCV 데이터
            weekly_data: 최근 52주 OHLCV 데이터
            monthly_data: 최근 20개월 OHLCV 데이터

        Returns:
            {
                "daily_trend": "UPTREND|DOWNTREND|SIDEWAYS",
                "weekly_trend": "UPTREND|DOWNTREND|SIDEWAYS",
                "monthly_trend": "UPTREND|DOWNTREND|SIDEWAYS",
                "alignment_score": 0.0-1.0,  # 타임프레임 정렬 점수
                "alignment_status": "STRONG|MODERATE|WEAK|CONFLICTING"
            }
        """
        # 1. 각 타임프레임별 추세 분석
        daily_trend = self._calculate_trend(daily_data, timeframe="daily")
        weekly_trend = self._calculate_trend(weekly_data, timeframe="weekly")
        monthly_trend = self._calculate_trend(monthly_data, timeframe="monthly")

        # 2. 타임프레임 정렬 점수 계산
        alignment_score = self._calculate_alignment_score(daily_trend, weekly_trend, monthly_trend)

        # 3. 정렬 상태 분류
        if alignment_score >= 0.8:
            alignment_status = "STRONG"  # 강한 정렬
        elif alignment_score >= 0.6:
            alignment_status = "MODERATE"  # 보통 정렬
        elif alignment_score >= 0.4:
            alignment_status = "WEAK"  # 약한 정렬
        else:
            alignment_status = "CONFLICTING"  # 충돌 (타임프레임 간 불일치)

        return {
            "daily_trend": daily_trend,
            "weekly_trend": weekly_trend,
            "monthly_trend": monthly_trend,
            "alignment_score": alignment_score,
            "alignment_status": alignment_status
        }

    def _calculate_trend(self, ohlcv_data: List[Dict], timeframe: str = "daily") -> str:
        """
        OHLCV 데이터로부터 추세 계산

        방법:
        - MA20 > MA50: 상승 추세
        - MA20 < MA50: 하락 추세
        - 그 외: 횡보

        Args:
            ohlcv_data: OHLCV 봉 데이터
            timeframe: "daily"|"weekly"|"monthly"

        Returns:
            "UPTREND"|"DOWNTREND"|"SIDEWAYS"
        """
        if len(ohlcv_data) < 50:
            return "SIDEWAYS"  # 데이터 부족

        closes = [bar['close'] for bar in ohlcv_data]

        # 이동평균 계산
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50

        # 추세 판단
        if ma20 > ma50 * 1.02:  # 2% 이상 차이
            return "UPTREND"
        elif ma20 < ma50 * 0.98:  # 2% 이상 차이
            return "DOWNTREND"
        else:
            return "SIDEWAYS"

    def _calculate_alignment_score(self, daily_trend: str, weekly_trend: str, monthly_trend: str) -> float:
        """
        타임프레임 정렬 점수 계산

        점수 기준:
        - 모두 같은 방향 (UPTREND/DOWNTREND): 1.0
        - 2개 같은 방향: 0.66
        - 1개만 같은 방향: 0.33
        - 모두 다른 방향: 0.0

        특수 케이스:
        - SIDEWAYS는 중립으로 간주 (점수 0.5 기여)

        Args:
            daily_trend: 일봉 추세
            weekly_trend: 주봉 추세
            monthly_trend: 월봉 추세

        Returns:
            0.0-1.0 점수
        """
        trends = [daily_trend, weekly_trend, monthly_trend]

        # SIDEWAYS 제거 후 실제 추세만 확인
        non_sideways_trends = [t for t in trends if t != "SIDEWAYS"]

        # 모두 SIDEWAYS인 경우
        if len(non_sideways_trends) == 0:
            return 0.5  # 중립

        # 실제 추세 일치도 확인
        uptrend_count = trends.count("UPTREND")
        downtrend_count = trends.count("DOWNTREND")
        sideways_count = trends.count("SIDEWAYS")

        # 모두 같은 방향
        if uptrend_count == 3:
            return 1.0  # 완벽한 상승 정렬
        elif downtrend_count == 3:
            return 1.0  # 완벽한 하락 정렬

        # 2개 같은 방향
        elif uptrend_count == 2:
            return 0.75 if sideways_count == 1 else 0.66
        elif downtrend_count == 2:
            return 0.75 if sideways_count == 1 else 0.66

        # 1개만 같은 방향 (충돌)
        elif uptrend_count == 1 and downtrend_count == 1:
            return 0.33  # 타임프레임 충돌

        # SIDEWAYS 2개 + 추세 1개
        elif sideways_count == 2:
            return 0.5

        # 모두 다른 방향 (최악)
        else:
            return 0.0

    def _calculate_bollinger_bands(self, ohlcv_data: List[Dict], period: int = 20, std_dev: float = 2.0) -> Dict:
        """
        볼린저밴드 계산

        공식:
        - Middle Band (SMA): 20일 이동평균
        - Upper Band: Middle + (2 × 표준편차)
        - Lower Band: Middle - (2 × 표준편차)

        Args:
            ohlcv_data: OHLCV 데이터
            period: 이동평균 기간 (기본 20)
            std_dev: 표준편차 배수 (기본 2.0)

        Returns:
            {
                "upper": float,  # 상단 밴드
                "middle": float,  # 중간선 (SMA)
                "lower": float  # 하단 밴드
            }
        """
        if len(ohlcv_data) < period:
            # 데이터 부족 - 현재가 기준 임시값
            current_price = ohlcv_data[-1]['close'] if ohlcv_data else 0
            return {
                "upper": current_price * 1.1,
                "middle": current_price,
                "lower": current_price * 0.9
            }

        closes = [bar['close'] for bar in ohlcv_data[-period:]]

        # Middle Band (SMA)
        middle = sum(closes) / period

        # 표준편차 계산
        variance = sum((c - middle) ** 2 for c in closes) / period
        std = variance ** 0.5

        # Upper/Lower Bands
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }

    def _analyze_bollinger_bands(self, current_price: float, bands: Dict) -> Dict:
        """
        볼린저밴드 분석

        신호:
        - 하단 밴드 돌파 (가격 < Lower): OVERSOLD (과매도, 매수 기회)
        - 상단 밴드 돌파 (가격 > Upper): OVERBOUGHT (과매수, 매도 기회)
        - 밴드폭 축소: SQUEEZE (변동성 감소, 돌파 대기)
        - 밴드폭 확장: EXPANSION (강한 추세)

        Args:
            current_price: 현재 가격
            bands: 볼린저밴드 값 {"upper", "middle", "lower"}

        Returns:
            {
                "position": "BELOW_LOWER|LOWER_THIRD|MIDDLE|UPPER_THIRD|ABOVE_UPPER",
                "signal": "OVERSOLD|OVERBOUGHT|NEUTRAL|SQUEEZE|EXPANSION",
                "band_width_pct": float,  # 밴드폭 (%)
                "price_position": str  # 현재가 위치 설명
            }
        """
        upper = bands["upper"]
        middle = bands["middle"]
        lower = bands["lower"]

        # 밴드폭 계산 (%)
        band_width_pct = ((upper - lower) / middle) * 100 if middle > 0 else 0

        # 가격 위치 판단
        if current_price < lower:
            position = "BELOW_LOWER"
            signal = "OVERSOLD"
            price_position = f"하단 밴드 하회 (${lower:.2f})"
        elif current_price < lower + (middle - lower) * 0.33:
            position = "LOWER_THIRD"
            signal = "NEUTRAL"
            price_position = "하단 1/3 구간"
        elif current_price < middle + (upper - middle) * 0.33:
            position = "MIDDLE"
            signal = "NEUTRAL"
            price_position = "중간 구간"
        elif current_price < upper:
            position = "UPPER_THIRD"
            signal = "NEUTRAL"
            price_position = "상단 1/3 구간"
        else:  # current_price >= upper
            position = "ABOVE_UPPER"
            signal = "OVERBOUGHT"
            price_position = f"상단 밴드 상회 (${upper:.2f})"

        # 밴드폭 기반 추가 신호
        if signal == "NEUTRAL":
            if band_width_pct < 5.0:
                signal = "SQUEEZE"  # 변동성 축소
            elif band_width_pct > 15.0:
                signal = "EXPANSION"  # 변동성 확대

        return {
            "position": position,
            "signal": signal,
            "band_width_pct": band_width_pct,
            "price_position": price_position
        }
