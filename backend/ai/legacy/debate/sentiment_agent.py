"""
Sentiment Agent for War Room Debate System

Role: Social media sentiment analysis specialist
Focuses on: Twitter/Reddit sentiment, investor psychology (Fear & Greed), social trends

Author: ai-trading-system
Date: 2025-12-27
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    Sentiment Agent - 소셜 미디어 감성 분석 전문가

    Core Capabilities:
    - Twitter/Reddit sentiment extraction
    - Fear & Greed Index calculation
    - Social trend detection
    - Retail investor psychology analysis
    """

    def __init__(self):
        self.agent_name = "sentiment"
        self.vote_weight = 0.08  # 8% voting weight (소셜은 참고용)

    async def analyze(self, ticker: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze social media sentiment for ticker.

        Args:
            ticker: Stock ticker symbol
            context: Optional context (social_data, fear_greed_index)

        Returns:
            {
                "agent": "sentiment",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": str,
                "sentiment_factors": {...}
            }
        """
        try:
            logger.info(f"[Sentiment Agent] Analyzing {ticker}")

            if context and "social_data" in context:
                return await self._analyze_with_real_data(ticker, context["social_data"])
            else:
                return await self._analyze_mock(ticker)

        except Exception as e:
            logger.error(f"[Sentiment Agent] Error analyzing {ticker}: {e}")
            return self._fallback_response(ticker)

    async def _analyze_with_real_data(self, ticker: str, social_data: Dict) -> Dict:
        """
        Analyze using real social media data.

        Expected social_data format:
        {
            "twitter_sentiment": 0.65,  # -1.0 ~ 1.0
            "twitter_volume": 15000,    # Tweet count (24h)
            "reddit_sentiment": 0.45,
            "reddit_mentions": 850,     # Mention count (24h)
            "fear_greed_index": 72,     # 0-100 (CNN Fear & Greed Index)
            "trending_rank": 5,         # 1-100 (1 = most trending)
            "sentiment_change_24h": 0.15,  # Sentiment 24h change
            "bullish_ratio": 0.68       # % of bullish posts
        }
        """
        twitter_sentiment = social_data.get("twitter_sentiment", 0)
        twitter_volume = social_data.get("twitter_volume", 0)
        reddit_sentiment = social_data.get("reddit_sentiment", 0)
        reddit_mentions = social_data.get("reddit_mentions", 0)
        fear_greed_index = social_data.get("fear_greed_index", 50)
        trending_rank = social_data.get("trending_rank", 100)
        sentiment_change_24h = social_data.get("sentiment_change_24h", 0)
        bullish_ratio = social_data.get("bullish_ratio", 0.5)

        action = "HOLD"
        confidence = 0.5
        confidence_boost = 0.0
        sentiment_factors = {}

        # 1. 종합 소셜 감성 점수 계산 (가중 평균)
        # Twitter 60% + Reddit 40%
        overall_sentiment = (twitter_sentiment * 0.6) + (reddit_sentiment * 0.4)

        # 2. Fear & Greed Index 분석
        fear_greed_analysis = self._analyze_fear_greed(fear_greed_index)
        sentiment_factors["fear_greed"] = {
            "index": fear_greed_index,
            "level": fear_greed_analysis["level"],
            "signal": fear_greed_analysis["signal"]
        }

        # 3. 소셜 트렌딩 분석
        is_trending = trending_rank <= 20  # Top 20 = trending
        high_volume = (twitter_volume > 10000) or (reddit_mentions > 500)

        sentiment_factors["trending"] = {
            "rank": trending_rank,
            "is_trending": is_trending,
            "twitter_volume": twitter_volume,
            "reddit_mentions": reddit_mentions
        }

        # 4. 매매 신호 결정

        # === BUY 신호 ===
        # Case 1: 강한 긍정 감성 + 높은 거래량
        if overall_sentiment > 0.6 and high_volume:
            action = "BUY"
            confidence = min(0.85, 0.70 + (overall_sentiment - 0.6) * 0.5)
            reasoning = f"강한 긍정 소셜 감성 ({overall_sentiment:.2f}) + 높은 언급량 (Twitter {twitter_volume}, Reddit {reddit_mentions})"

        # Case 2: Extreme Fear (역투자 기회)
        elif fear_greed_index < 25 and overall_sentiment > 0:
            action = "BUY"
            confidence = 0.78
            reasoning = f"Extreme Fear ({fear_greed_index}) + 긍정 감성 ({overall_sentiment:.2f}) - 역투자 기회"

        # Case 3: Trending + 상승 모멘텀
        elif is_trending and sentiment_change_24h > 0.3:
            action = "BUY"
            confidence = 0.75
            reasoning = f"급상승 트렌드 (순위 {trending_rank}, 24h 감성 변화 +{sentiment_change_24h:.2f})"

        # === SELL 신호 ===
        # Case 1: 강한 부정 감성
        elif overall_sentiment < -0.5:
            action = "SELL"
            confidence = 0.80
            reasoning = f"강한 부정 소셜 감성 ({overall_sentiment:.2f}) - 투자 심리 악화"

        # Case 2: Extreme Greed (과열 경고)
        elif fear_greed_index > 85 and bullish_ratio > 0.90:
            action = "SELL"
            confidence = 0.82
            reasoning = f"Extreme Greed ({fear_greed_index}) + 과도한 낙관 (강세 {bullish_ratio:.1%}) - 과열 조정 위험"

        # Case 3: 급락 트렌드
        elif sentiment_change_24h < -0.4:
            action = "SELL"
            confidence = 0.75
            reasoning = f"급락 트렌드 (24h 감성 변화 {sentiment_change_24h:.2f}) - 투자 심리 급락"

        # === HOLD (중립) ===
        else:
            sentiment_level = "긍정" if overall_sentiment > 0.3 else "부정" if overall_sentiment < -0.3 else "중립"
            reasoning = f"소셜 감성 {sentiment_level} ({overall_sentiment:.2f}), Fear & Greed {fear_greed_index} - 관망 추천"
            confidence = 0.60

        # 5. Fear & Greed 신호 통합
        if fear_greed_analysis["signal"] == "CONTRARIAN_BUY":
            # Extreme Fear → 역투자 매수
            if action == "HOLD":
                action = "BUY"
                confidence = 0.72
                reasoning = f"Extreme Fear ({fear_greed_index}) - 역투자 매수 기회"
            elif action == "BUY":
                confidence_boost += 0.1
                reasoning += f" | Fear & Greed 역투자 ({fear_greed_index})"

        elif fear_greed_analysis["signal"] == "CONTRARIAN_SELL":
            # Extreme Greed → 과열 매도
            if action == "HOLD":
                action = "SELL"
                confidence = 0.70
                reasoning = f"Extreme Greed ({fear_greed_index}) - 과열 조정 경고"
            elif action == "SELL":
                confidence_boost += 0.1
                reasoning += f" | Fear & Greed 과열 ({fear_greed_index})"

        # 6. Trending Boost
        if is_trending and action == "BUY":
            confidence_boost += 0.05
            reasoning += f" | Trending #{trending_rank}"

        # 7. 거래량 확인 (Low Volume = 신뢰도 감소)
        if not high_volume and action in ["BUY", "SELL"]:
            confidence_boost -= 0.1
            reasoning += f" | 낮은 소셜 언급량 (주의)"

        # Final confidence adjustment
        confidence = min(0.90, max(0.40, confidence + confidence_boost))

        sentiment_factors.update({
            "overall_sentiment": f"{overall_sentiment:.2f}",
            "twitter_sentiment": f"{twitter_sentiment:.2f}",
            "reddit_sentiment": f"{reddit_sentiment:.2f}",
            "sentiment_change_24h": f"{sentiment_change_24h:+.2f}",
            "bullish_ratio": f"{bullish_ratio:.1%}"
        })

        return {
            "agent": "sentiment",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "sentiment_factors": sentiment_factors
        }

    async def _analyze_mock(self, ticker: str) -> Dict:
        """Mock sentiment analysis when real data unavailable"""
        scenarios = [
            {
                "action": "BUY",
                "confidence": 0.75,
                "reasoning": "긍정 소셜 감성 (0.68) + Extreme Fear (22) - 역투자 기회",
                "sentiment_factors": {
                    "overall_sentiment": "0.68",
                    "fear_greed": {"index": 22, "level": "EXTREME_FEAR", "signal": "CONTRARIAN_BUY"},
                    "trending": {"rank": 12, "is_trending": True}
                }
            },
            {
                "action": "SELL",
                "confidence": 0.80,
                "reasoning": "부정 소셜 감성 (-0.52) + Extreme Greed (88) - 과열 조정 위험",
                "sentiment_factors": {
                    "overall_sentiment": "-0.52",
                    "fear_greed": {"index": 88, "level": "EXTREME_GREED", "signal": "CONTRARIAN_SELL"},
                    "trending": {"rank": 5, "is_trending": True}
                }
            },
            {
                "action": "HOLD",
                "confidence": 0.60,
                "reasoning": "중립 소셜 감성 (0.12), Fear & Greed 중립 (52) - 관망",
                "sentiment_factors": {
                    "overall_sentiment": "0.12",
                    "fear_greed": {"index": 52, "level": "NEUTRAL", "signal": "NEUTRAL"},
                    "trending": {"rank": 45, "is_trending": False}
                }
            }
        ]

        return {
            "agent": "sentiment",
            **random.choice(scenarios)
        }

    def _fallback_response(self, ticker: str) -> Dict:
        """Fallback response on error"""
        return {
            "agent": "sentiment",
            "action": "HOLD",
            "confidence": 0.50,
            "reasoning": f"소셜 감성 데이터 수신 실패 - {ticker} 관망 추천",
            "sentiment_factors": {
                "error": True
            }
        }

    def _analyze_fear_greed(self, index: int) -> Dict[str, Any]:
        """
        CNN Fear & Greed Index 분석

        Index 범위:
        - 0-24: Extreme Fear (극도의 공포)
        - 25-44: Fear (공포)
        - 45-55: Neutral (중립)
        - 56-75: Greed (탐욕)
        - 76-100: Extreme Greed (극도의 탐욕)

        역투자 전략:
        - Extreme Fear → BUY (공포 매수 기회)
        - Extreme Greed → SELL (탐욕 과열 경고)

        Args:
            index: Fear & Greed Index (0-100)

        Returns:
            {
                "level": str,
                "signal": str,  # CONTRARIAN_BUY/CONTRARIAN_SELL/NEUTRAL
                "reasoning": str
            }
        """
        if index < 25:
            level = "EXTREME_FEAR"
            signal = "CONTRARIAN_BUY"
            reasoning = f"극도의 공포 ({index}) - 역투자 매수 기회"
        elif index < 45:
            level = "FEAR"
            signal = "NEUTRAL"
            reasoning = f"공포 ({index}) - 주의 필요"
        elif index < 56:
            level = "NEUTRAL"
            signal = "NEUTRAL"
            reasoning = f"중립 ({index}) - 정상 범위"
        elif index < 76:
            level = "GREED"
            signal = "NEUTRAL"
            reasoning = f"탐욕 ({index}) - 과열 주의"
        else:  # >= 76
            level = "EXTREME_GREED"
            signal = "CONTRARIAN_SELL"
            reasoning = f"극도의 탐욕 ({index}) - 과열 조정 경고"

        return {
            "level": level,
            "signal": signal,
            "reasoning": reasoning
        }

    def _detect_social_trends(self, social_data: Dict) -> Dict[str, Any]:
        """
        소셜 트렌드 감지

        감지 항목:
        - WallStreetBets (WSB) mentions
        - Meme stock surge (급격한 언급 증가)
        - Coordinated buying (집단 매수)
        - Retail frenzy (개인 투자자 열풍)

        Args:
            social_data: 소셜 데이터

        Returns:
            {
                "is_meme_stock": bool,
                "wsb_mentions": int,
                "retail_interest": str,  # LOW/MODERATE/HIGH/EXTREME
                "coordination_detected": bool
            }
        """
        twitter_volume = social_data.get("twitter_volume", 0)
        reddit_mentions = social_data.get("reddit_mentions", 0)
        sentiment_change_24h = social_data.get("sentiment_change_24h", 0)
        bullish_ratio = social_data.get("bullish_ratio", 0.5)

        # WallStreetBets mentions (Reddit 기준)
        wsb_mentions = reddit_mentions  # 실제로는 특정 서브레딧 필터링 필요

        # Meme Stock 판정 (급격한 증가 + 높은 강세 비율)
        is_meme_stock = (
            (twitter_volume > 50000 or reddit_mentions > 2000) and
            sentiment_change_24h > 0.5 and
            bullish_ratio > 0.85
        )

        # 개인 투자자 관심도
        total_volume = twitter_volume + reddit_mentions
        if total_volume > 100000:
            retail_interest = "EXTREME"
        elif total_volume > 50000:
            retail_interest = "HIGH"
        elif total_volume > 10000:
            retail_interest = "MODERATE"
        else:
            retail_interest = "LOW"

        # 집단 매수 감지 (짧은 시간에 높은 강세 비율)
        coordination_detected = (
            sentiment_change_24h > 0.6 and
            bullish_ratio > 0.90
        )

        return {
            "is_meme_stock": is_meme_stock,
            "wsb_mentions": wsb_mentions,
            "retail_interest": retail_interest,
            "coordination_detected": coordination_detected
        }
