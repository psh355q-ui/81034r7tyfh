"""
News Agent for War Room Debate

7번째 War Room 멤버로 긴급 뉴스(Grounding API)와 일반 뉴스를 분석하여
매매 의견을 제시합니다.

Vote Weight: 10%
Data Sources:
- GroundingSearchLog (긴급 뉴스)
- NewsArticle (일반 뉴스)
- Gemini 2.0 Flash (감성 분석)

Author: AI Trading System
Date: 2025-12-21
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json

from backend.database.models import NewsArticle, GroundingSearchLog
from backend.database.repository import get_sync_session
from backend.ai.gemini_client import call_gemini_api

logger = logging.getLogger(__name__)


class NewsAgent:
    """뉴스 기반 투표 Agent (War Room 7th member)"""
    
    def __init__(self):
        self.agent_name = "news"
        self.vote_weight = 0.10  # 10% 투표권
        self.model_name = "gemini-2.0-flash-exp"
    
    async def analyze(self, ticker: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        뉴스 분석 후 투표 결정
        
        Args:
            ticker: 분석할 티커 (예: AAPL)
            context: 추가 컨텍스트 (선택)
        
        Returns:
            {
                "agent": "news",
                "action": "BUY/SELL/HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "...",
                "news_count": int,
                "emergency_count": int,
                "sentiment_score": float
            }
        """
        db = get_sync_session()
        
        try:
            # 1. Emergency News 조회 (최근 15일)
            cutoff = datetime.now() - timedelta(days=15)
            
            # GroundingSearchLog fields: query (not search_query), no ticker column, search_date (not created_at)
            emergency_news = db.query(GroundingSearchLog)\
                .filter(
                    GroundingSearchLog.query.ilike(f"%{ticker}%"),  # Search in query text
                    GroundingSearchLog.search_date >= cutoff         # Use search_date
                )\
                .order_by(GroundingSearchLog.search_date.desc())\
                .limit(5)\
                .all()
            
            # 2. 일반 뉴스 조회 (최근 15일) - Phase 20 real-time news
            # Priority: tickers field > title/content search
            recent_news = db.query(NewsArticle)\
                .filter(
                    NewsArticle.published_date >= cutoff
                )\
                .order_by(NewsArticle.published_date.desc())\
                .limit(200)\
                .all()

            # 티커 필터링 (우선순위: tickers 배열 > 제목/내용)
            ticker_news = []
            for n in recent_news:
                # Check tickers array first (from Phase 20)
                if n.tickers and ticker.upper() in [t.upper() for t in n.tickers]:
                    ticker_news.append(n)
                # Fallback: title/content search
                elif ticker.upper() in n.title.upper() or ticker.upper() in (n.content or '').upper():
                    ticker_news.append(n)

                if len(ticker_news) >= 30:
                    break

            recent_news = ticker_news
            
            # 3. 뉴스 요약 생성
            news_summaries = []
            
            for news in emergency_news:
                # GroundingSearchLog has: query, result_count, estimated_cost
                # No 'urgency' field by default
                news_summaries.append({
                    "type": "EMERGENCY",
                    "urgency": "HIGH",  # Default urgency
                    "content": news.query[:200] if news.query else f"Emergency search for {ticker}"
                })
            
            for article in recent_news:
                # Use Phase 20 sentiment_score if available
                sentiment = article.sentiment_score if hasattr(article, 'sentiment_score') and article.sentiment_score else 0.0

                # Add tags for context (from Phase 20 auto-tagging)
                tags_str = ', '.join(article.tags[:3]) if hasattr(article, 'tags') and article.tags else ''

                news_summaries.append({
                    "type": "REGULAR",
                    "title": article.title,
                    "sentiment": sentiment,  # Phase 20 sentiment
                    "tags": tags_str,        # Phase 20 tags
                    "source": article.source if hasattr(article, 'source') else 'Unknown'
                })
            
            # 뉴스가 없으면 중립 투표
            if not news_summaries:
                logger.info(f"📰 News Agent: No news found for {ticker}")
                return {
                    "agent": "news",
                    "action": "HOLD",
                    "confidence": 0.5,
                    "reasoning": f"{ticker}에 대한 최근 15일 뉴스 없음 (중립 유지)",
                    "news_count": 0,
                    "emergency_count": 0,
                    "sentiment_score": 0.0
                }
            
            # 4. 시계열 트렌드 분석
            trend_analysis = self._analyze_temporal_trend(news_summaries)

            # 5. Gemini로 감성 분석
            logger.info(f"📰 News Agent: Analyzing {len(news_summaries)} news for {ticker}")
            sentiment_result = await self._analyze_sentiment(ticker, news_summaries, trend_analysis)

            # 6. 투표 결정
            action, confidence = self._decide_action(
                sentiment_result,
                len(emergency_news),
                len(recent_news),
                trend_analysis
            )
            
            # 트렌드 정보 추가
            trend_info = ""
            if trend_analysis:
                trend_emoji = "📈" if trend_analysis['trend'] == 'IMPROVING' else "📉" if trend_analysis['trend'] == 'DETERIORATING' else "➡️"
                risk_emoji = "✅" if trend_analysis['risk_trajectory'] == 'DECREASING' else "⚠️" if trend_analysis['risk_trajectory'] == 'INCREASING' else "➖"
                trend_info = f"""
- 뉴스 트렌드: {trend_emoji} {trend_analysis['trend']} (최근 {trend_analysis['sentiment_change']:+.2f})
- 위험도 방향: {risk_emoji} {trend_analysis['risk_trajectory']}"""

            reasoning = f"""
뉴스 분석 결과 ({len(emergency_news)}개 긴급 + {len(recent_news)}개 일반):
- 감성 점수: {sentiment_result['score']:.2f}
- 긍정 뉴스: {sentiment_result['positive_count']}개
- 부정 뉴스: {sentiment_result['negative_count']}개{trend_info}
- 주요 키워드: {', '.join(sentiment_result['keywords'][:5])}
"""
            
            logger.info(f"📰 News Agent: {action} (confidence: {confidence:.2f})")
            
            return {
                "agent": "news",
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning.strip(),
                "news_count": len(recent_news),
                "emergency_count": len(emergency_news),
                "sentiment_score": sentiment_result['score']
            }
        
        except Exception as e:
            logger.error(f"❌ News Agent error: {e}", exc_info=True)
            # 에러 발생 시 중립 투표
            return {
                "agent": "news",
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": f"뉴스 분석 실패: {str(e)}",
                "news_count": 0,
                "emergency_count": 0,
                "sentiment_score": 0.0
            }
        
        finally:
            db.close()
    
    def _analyze_temporal_trend(self, news_summaries: List[Dict]) -> Dict[str, Any]:
        """
        시계열 트렌드 분석: 뉴스 감성이 시간에 따라 어떻게 변화하는지 분석

        Returns:
            {
                "trend": "IMPROVING|DETERIORATING|STABLE",
                "recent_sentiment": float,  # 최근 3일 평균
                "older_sentiment": float,   # 4-15일 평균
                "sentiment_change": float,  # 변화량
                "risk_trajectory": "INCREASING|DECREASING|NEUTRAL"
            }
        """
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_cutoff = now - timedelta(days=3)

        recent_news = []
        older_news = []

        for news in news_summaries:
            if news['type'] == 'EMERGENCY':
                # 긴급 뉴스는 최근으로 간주
                recent_news.append(news)
                continue

            # 일반 뉴스는 발행일 확인 필요 (news_summaries에 published_at 추가 필요)
            # 현재는 순서 기반으로 절반 나눔
            if len(recent_news) < len(news_summaries) / 2:
                recent_news.append(news)
            else:
                older_news.append(news)

        # 각 기간별 평균 감성 계산
        recent_sentiment = sum(n.get('sentiment', 0) for n in recent_news) / len(recent_news) if recent_news else 0
        older_sentiment = sum(n.get('sentiment', 0) for n in older_news) / len(older_news) if older_news else 0

        sentiment_change = recent_sentiment - older_sentiment

        # 트렌드 판정
        if sentiment_change > 0.2:
            trend = "IMPROVING"
            risk_trajectory = "DECREASING"
        elif sentiment_change < -0.2:
            trend = "DETERIORATING"
            risk_trajectory = "INCREASING"
        else:
            trend = "STABLE"
            risk_trajectory = "NEUTRAL"

        return {
            "trend": trend,
            "recent_sentiment": recent_sentiment,
            "older_sentiment": older_sentiment,
            "sentiment_change": sentiment_change,
            "risk_trajectory": risk_trajectory,
            "recent_count": len(recent_news),
            "older_count": len(older_news)
        }

    async def _analyze_sentiment(self, ticker: str, news_summaries: List[Dict], trend_analysis: Dict = None) -> Dict[str, Any]:
        """Gemini로 뉴스 감성 분석 (시계열 트렌드 포함)"""

        if not news_summaries:
            return {
                'score': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'keywords': [],
                'trend': None
            }

        trend_context = ""
        if trend_analysis:
            trend_context = f"""

시계열 트렌드:
- 최근 3일 감성: {trend_analysis['recent_sentiment']:.2f}
- 4-15일 감성: {trend_analysis['older_sentiment']:.2f}
- 변화 추세: {trend_analysis['trend']} ({trend_analysis['sentiment_change']:+.2f})
- 위험도 방향: {trend_analysis['risk_trajectory']}
"""

        prompt = f"""
당신은 {ticker} 주식에 대한 뉴스 감성 분석가입니다.

다음 뉴스들을 분석하여 종합 점수를 산출하세요:

{self._format_news_for_prompt(news_summaries)}
{trend_context}

**중요**: 시계열 트렌드를 고려하여, 최근 뉴스가 과거 대비 개선되는지 악화되는지 반영하세요.

다음 JSON 형식으로만 응답하세요 (추가 설명 없이):
{{
  "score": -1.0 ~ 1.0 (부정 ~ 긍정),
  "positive_count": 긍정 뉴스 개수,
  "negative_count": 부정 뉴스 개수,
  "keywords": ["키워드1", "키워드2", "키워드3"]
}}
"""
        
        try:
            # Gemini API 호출
            response_text = await call_gemini_api(
                prompt=prompt,
                model_name=self.model_name,
                temperature=0.3
            )
            
            # JSON 파싱
            # response_text가 "```json\n...\n```" 형식일 수 있으므로 정리
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            return {
                'score': float(result.get('score', 0.0)),
                'positive_count': int(result.get('positive_count', 0)),
                'negative_count': int(result.get('negative_count', 0)),
                'keywords': result.get('keywords', [])
            }
        
        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            # 파싱 실패 시 중립 반환
            return {
                'score': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'keywords': []
            }
    
    def _format_news_for_prompt(self, news_summaries: List[Dict]) -> str:
        """뉴스를 프롬프트 형식으로 변환 (Phase 20 enhanced)"""
        lines = []
        for i, news in enumerate(news_summaries, 1):
            if news['type'] == 'EMERGENCY':
                lines.append(f"{i}. [긴급 {news['urgency']}] {news['content']}")
            else:
                # Include sentiment and tags from Phase 20
                sentiment_emoji = "📈" if news.get('sentiment', 0) > 0.3 else "📉" if news.get('sentiment', 0) < -0.3 else "➖"
                tags_info = f" [{news.get('tags', '')}]" if news.get('tags') else ""
                source_info = f" ({news.get('source', 'Unknown')})"

                lines.append(f"{i}. {sentiment_emoji} {news['title']}{tags_info}{source_info}")

        return "\n".join(lines)
    
    def _decide_action(
        self,
        sentiment_result: Dict[str, Any],
        emergency_count: int,
        news_count: int,
        trend_analysis: Dict = None
    ) -> tuple[str, float]:
        """감성 점수 → 매매 결정 (시계열 트렌드 반영)"""

        score = sentiment_result['score']

        # 긴급 뉴스가 있으면 confidence 높임
        urgency_boost = 0.2 if emergency_count > 0 else 0

        # 시계열 트렌드 반영
        trend_boost = 0
        if trend_analysis:
            # IMPROVING: 긍정 뉴스 증가 → BUY 신호 강화
            # DETERIORATING: 부정 뉴스 증가 → SELL 신호 강화
            if trend_analysis['trend'] == 'IMPROVING':
                trend_boost = 0.1
            elif trend_analysis['trend'] == 'DETERIORATING':
                trend_boost = -0.1

        adjusted_score = score + trend_boost

        if adjusted_score > 0.6:
            action = "BUY"
            confidence = min(0.95, abs(adjusted_score) + urgency_boost)
        elif adjusted_score < -0.6:
            action = "SELL"
            confidence = min(0.95, abs(adjusted_score) + urgency_boost)
        else:
            action = "HOLD"
            confidence = 0.5 + abs(adjusted_score) * 0.3

        return action, confidence
