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
Updated: 2025-12-27 - Added regulatory and litigation news detection
"""

from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
import logging
import json
import anthropic
import os

from backend.database.models import NewsArticle, GroundingSearchLog
from backend.database.repository import (
    get_sync_session,
    MacroContextRepository,
    NewsInterpretationRepository
)
from backend.ai.gemini_client import call_gemini_api

# Use GLM instead of Claude for cost efficiency
try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False
    logger.warning("GLM client not available, will use fallback")

logger = logging.getLogger(__name__)


class NewsAgent:
    """뉴스 기반 투표 Agent (War Room 7th member)"""

    def __init__(self):
        self.agent_name = "news"
        self.vote_weight = 0.10  # 10% 투표권
        self.model_name = "gemini-2.0-flash-exp"
        # Use GLM client instead of Claude for cost efficiency
        if GLM_AVAILABLE and os.getenv("GLM_API_KEY"):
            try:
                self.glm_client = GLMClient()
                self.use_glm = True
                logger.info("✅ NewsAgent using GLM-4.7 for news interpretation")
            except Exception as e:
                logger.warning(f"GLM client init failed: {e}, falling back to Claude")
                self.use_glm = False
        else:
            self.use_glm = False
        self.enable_interpretation = os.getenv("ENABLE_NEWS_INTERPRETATION", "true").lower() == "true"
    
    async def interpret_articles(self, ticker: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        제공된 기사 리스트 해석 (War Room 연동용)
        
        Args:
            ticker: 종목 코드
            articles: 기사 리스트 (dict)
            
        Returns:
            List[Dict]: 해석 결과 리스트
        """
        if not self.enable_interpretation or not articles:
            return []

        interpretations = []
        try:
            # Sync session for reading macro context
            db = get_sync_session()
            macro_context = self._get_macro_context(db)
            db.close()
            
            for article in articles:
                # Use summary if available, else content
                content = article.get('summary') or article.get('content') or ''
                
                # Call internal interpretation logic
                result = await self._interpret_news(
                    ticker=ticker,
                    headline=article['title'],
                    content=content,
                    macro_context=macro_context
                )
                
                if result:
                    interpretations.append(result)
                    
        except Exception as e:
            logger.error(f"❌ NewsAgent.interpret_articles failed: {e}")
            
        return interpretations

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
            
            # 4. [NEW] 뉴스 해석 (Phase 2)
            if self.enable_interpretation and (emergency_news or recent_news):
                logger.info(f"🔍 News Agent: Interpreting important news for {ticker}")
                await self._interpret_and_save_news(ticker, emergency_news, recent_news, db)

            # 5. 규제/소송 뉴스 감지
            regulatory_analysis = self._detect_regulatory_litigation(news_summaries)
            
            # 6. [NEW] 지정학/칩워 위기 감지
            critical_event = self._detect_critical_events(news_summaries)

            # 7. 시계열 트렌드 분석
            trend_analysis = self._analyze_temporal_trend(news_summaries)

            # 8. Gemini로 감성 분석
            logger.info(f"📰 News Agent: Analyzing {len(news_summaries)} news for {ticker}")
            sentiment_result = await self._analyze_sentiment(
                ticker, 
                news_summaries, 
                trend_analysis, 
                regulatory_analysis
            )

            # 9. 투표 결정
            action, confidence = self._decide_action(
                sentiment_result,
                len(emergency_news),
                len(recent_news),
                trend_analysis,
                regulatory_analysis,
                critical_event  # [NEW] Pass critical event
            )
            
            # 트렌드 정보 추가
            trend_info = ""
            if trend_analysis:
                trend_emoji = "📈" if trend_analysis['trend'] == 'IMPROVING' else "📉" if trend_analysis['trend'] == 'DETERIORATING' else "➡️"
                risk_emoji = "✅" if trend_analysis['risk_trajectory'] == 'DECREASING' else "⚠️" if trend_analysis['risk_trajectory'] == 'INCREASING' else "➖"
                trend_info = f"""
- 뉴스 트렌드: {trend_emoji} {trend_analysis['trend']} (최근 {trend_analysis['sentiment_change']:+.2f})
- 위험도 방향: {risk_emoji} {trend_analysis['risk_trajectory']}"""

            # 규제/소송 정보 추가
            regulatory_info = ""
            if regulatory_analysis['has_risk']:
                reg_emoji = "⚖️" if regulatory_analysis['litigation_count'] > 0 else "📜"
                regulatory_info = f"""
- {reg_emoji} 규제/소송: {regulatory_analysis['severity']} ({regulatory_analysis['litigation_count']}건 소송, {regulatory_analysis['regulatory_count']}건 규제)"""

            reasoning = f"""
뉴스 분석 결과 ({len(emergency_news)}개 긴급 + {len(recent_news)}개 일반):
- 감성 점수: {sentiment_result['score']:.2f}
- 긍정 뉴스: {sentiment_result['positive_count']}개
- 부정 뉴스: {sentiment_result['negative_count']}개{trend_info}{regulatory_info}
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

    def _detect_regulatory_litigation(self, news_summaries: List[Dict]) -> Dict[str, Any]:
        """
        규제/소송 뉴스 감지
        
        키워드 기반 감지:
        - 소송: lawsuit, litigation, sued, settlement, class action
        - 규제: regulation, SEC, FTC, antitrust, investigation, probe
        
        Returns:
            {
                "has_risk": bool,
                "litigation_count": int,  # 소송 관련 뉴스 수
                "regulatory_count": int,  # 규제 관련 뉴스 수
                "severity": "CRITICAL|HIGH|MODERATE|LOW",
                "keywords_found": List[str]
            }
        """
        # 소송 관련 키워드
        litigation_keywords = [
            'lawsuit', 'litigation', 'sued', 'settlement', 'class action',
            '소송', '집단소송', '합의금', '법적 분쟁', '소송 패소'
        ]
        
        # 규제 관련 키워드
        regulatory_keywords = [
            'sec', 'ftc', 'doj', 'antitrust', 'investigation', 'probe',
            'fine', 'penalty', 'violation', 'compliance',
            '규제', '조사', '제재', '위반', '벌금', '당국', '감사'
        ]
        
        litigation_count = 0
        regulatory_count = 0
        keywords_found = []
        
        for news in news_summaries:
            content = ""
            if news['type'] == 'EMERGENCY':
                content = news.get('content', '').lower()
            else:
                content = news.get('title', '').lower()
                
            # 소송 키워드 검사
            for keyword in litigation_keywords:
                if keyword.lower() in content:
                    litigation_count += 1
                    if keyword not in keywords_found:
                        keywords_found.append(keyword)
                    break  # 한 뉴스당 한 번만 카운트
            
            # 규제 키워드 검사
            for keyword in regulatory_keywords:
                if keyword.lower() in content:
                    regulatory_count += 1
                    if keyword not in keywords_found:
                        keywords_found.append(keyword)
                    break
                    
        # 심각도 판정
        total_issues = litigation_count + regulatory_count
        
        if total_issues == 0:
            severity = "NONE"
            has_risk = False
        elif total_issues >= 5 or litigation_count >= 3:
            severity = "CRITICAL"
            has_risk = True
        elif total_issues >= 3 or litigation_count >= 2:
            severity = "HIGH"
            has_risk = True
        elif total_issues >= 2:
            severity = "MODERATE"
            has_risk = True
        else:
            severity = "LOW"
            has_risk = True
            
        return {
            "has_risk": has_risk,
            "litigation_count": litigation_count,
            "regulatory_count": regulatory_count,
            "severity": severity,
            "keywords_found": keywords_found[:5]  # 최대 5개만
        }

    def detect_critical_events(self, news_items: List[Dict]) -> Dict[str, Any]:
        """
        [New] 지정학적 위기 / 칩 워 / 매크로 충격 감지 (The Watchtower Trigger)
        Public method for external agents (e.g. AnalystAgentMVP)
        
        Uses centralized keywords from `watchtower_triggers.py` to optimize AI costs.
        Only triggers Deep Reasoning for truly critical events.
        
        Args:
            news_items: List of dicts. Keys can be 'title', 'content', 'summary'.
        
        Returns:
            {
                "event_type": "GEOPOLITICS|CHIP_WAR|MACRO|REGULATORY|NONE",
                "detected": bool,
                "urgency": "CRITICAL|HIGH|MEDIUM|NONE",
                "keywords": List[str]
            }
        """
        try:
            from backend.ai.monitoring.watchtower_triggers import (
                GEOPOLITICAL_TRIGGERS,
                CHIP_WAR_TRIGGERS,
                MACRO_SHOCK_TRIGGERS,
                REGULATORY_TRIGGERS
            )
        except ImportError:
            logger.error("❌ Failed to import Watchtower triggers, using fallback")
            return {"event_type": "NONE", "detected": False, "urgency": "NONE", "keywords": []}

        detected_events = []
        
        for news in news_items:
            # Construct consolidated text for searching
            text_monitor = []
            if 'title' in news: text_monitor.append(news['title'])
            if 'headline' in news: text_monitor.append(news['headline'])
            if 'content' in news: text_monitor.append(str(news['content']))
            if 'summary' in news: text_monitor.append(str(news['summary']))
            if 'query' in news: text_monitor.append(str(news['query'])) # For GroundingSearchLog
            
            full_text = " ".join(text_monitor).lower()
                
            # 1. Geopolitics (Highest Priority)
            geo_matches = [kw for kw in GEOPOLITICAL_TRIGGERS if kw in full_text]
            if geo_matches:
                detected_events.append({
                    "type": "GEOPOLITICS",
                    "urgency": "CRITICAL",
                    "keywords": geo_matches
                })
            
            # 2. Chip War
            chip_matches = [kw for kw in CHIP_WAR_TRIGGERS if kw in full_text]
            if chip_matches:
                detected_events.append({
                    "type": "CHIP_WAR",
                    "urgency": "HIGH",
                    "keywords": chip_matches
                })

            # 3. Macro Shock
            macro_matches = [kw for kw in MACRO_SHOCK_TRIGGERS if kw in full_text]
            if macro_matches:
                detected_events.append({
                    "type": "MACRO_SHOCK",
                    "urgency": "HIGH", 
                    "keywords": macro_matches
                })
                
        # Sort by urgency (CRITICAL > HIGH > MEDIUM)
        urgency_map = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "NONE": 0}
        
        if detected_events:
            # Select the most urgent event
            top_event = max(detected_events, key=lambda x: urgency_map.get(x['urgency'], 0))
            
            return {
                "event_type": top_event['type'],
                "detected": True,
                "urgency": top_event['urgency'],
                "keywords": list(set(top_event['keywords']))[:5]
            }
            
        return {
            "event_type": "NONE",
            "detected": False,
            "urgency": "NONE",
            "keywords": []
        }

    async def _analyze_sentiment(self, ticker: str, news_summaries: List[Dict], trend_analysis: Dict = None, regulatory_analysis: Dict = None) -> Dict[str, Any]:
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

        regulatory_context = ""
        if regulatory_analysis and regulatory_analysis['has_risk']:
            regulatory_context = f"""

규제/소송 이슈:
- 심각도: {regulatory_analysis['severity']}
- 소송 건수: {regulatory_analysis['litigation_count']}
- 규제 건수: {regulatory_analysis['regulatory_count']}
- 발견 키워드: {', '.join(regulatory_analysis['keywords_found'])}

**경고**: 규제/소송 이슈는 주가에 부정적 영향을 줄 가능성이 높습니다. 감성 점수에 반영하세요.
"""

        prompt = f"""
당신은 {ticker} 주식에 대한 뉴스 감성 분석가입니다.

다음 뉴스들을 분석하여 종합 점수를 산출하세요:

{self._format_news_for_prompt(news_summaries)}
{trend_context}{regulatory_context}

**중요**:
1. 시계열 트렌드를 고려하여, 최근 뉴스가 과거 대비 개선되는지 악화되는지 반영하세요.
2. 규제/소송 이슈는 심각도에 따라 감성 점수를 -0.2 ~ -0.5 하향 조정하세요.

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
        trend_analysis: Dict = None,
        regulatory_analysis: Dict = None,
        critical_event: Dict = None
    ) -> tuple[str, float]:
        """감성 점수 → 매매 결정 (시계열 트렌드, 규제, 지정학 위기 반영)"""

        score = sentiment_result['score']

        # 긴급 뉴스가 있으면 confidence 높임
        urgency_boost = 0.2 if emergency_count > 0 else 0

        # 시계열 트렌드 반영
        trend_boost = 0
        if trend_analysis:
            if trend_analysis['trend'] == 'IMPROVING':
                trend_boost = 0.1
            elif trend_analysis['trend'] == 'DETERIORATING':
                trend_boost = -0.1

        # 규제/소송 리스크 반영
        regulatory_penalty = 0
        force_sell = False
        if regulatory_analysis and regulatory_analysis['has_risk']:
            if regulatory_analysis['severity'] == 'CRITICAL':
                regulatory_penalty = -0.5
                force_sell = True
            elif regulatory_analysis['severity'] == 'HIGH':
                regulatory_penalty = -0.3
            elif regulatory_analysis['severity'] == 'MODERATE':
                regulatory_penalty = -0.2
            else:
                regulatory_penalty = -0.1
                
        # [NEW] 지정학/칩워 위기 반영 (SUPER PRIORITY)
        geo_penalty = 0
        if critical_event and critical_event['detected']:
            if critical_event['urgency'] == 'CRITICAL':
                # 전쟁/침공 등은 무조건 매도 및 최대 신뢰도
                force_sell = True
                geo_penalty = -1.0 # 강력한 하방 압력
                logger.warning(f"🚨 CRITICAL GEOPOLITICAL EVENT: {critical_event['keywords']}")
            elif critical_event['urgency'] == 'HIGH':
                geo_penalty = -0.5
                
        adjusted_score = score + trend_boost + regulatory_penalty + geo_penalty

        # 강제 매도 조건 (규제 Critical or 지정학 Critical)
        if force_sell:
            action = "SELL"
            confidence = 0.95  # 매우 높은 확신
        elif adjusted_score > 0.6:
            action = "BUY"
            confidence = min(0.95, abs(adjusted_score) + urgency_boost)
        elif adjusted_score < -0.6:
            action = "SELL"
            confidence = min(0.95, abs(adjusted_score) + urgency_boost)
        else:
            action = "HOLD"
            confidence = 0.5 + abs(adjusted_score) * 0.3

        return action, confidence

    # ====================================
    # Phase 2: News Interpretation Methods
    # ====================================

    async def _interpret_and_save_news(
        self,
        ticker: str,
        emergency_news: List,
        recent_news: List[NewsArticle],
        db_session
    ):
        """
        중요 뉴스를 선택하여 Claude API로 해석하고 DB에 저장

        Args:
            ticker: 종목 코드
            emergency_news: 긴급 뉴스 목록
            recent_news: 일반 뉴스 목록
            db_session: DB 세션
        """
        # 1. Macro context 조회
        macro_context = self._get_macro_context(db_session)

        # 2. 중요 뉴스 선택 (최대 5개)
        important_news = self._select_important_news(emergency_news, recent_news, limit=5)

        if not important_news:
            logger.info(f"🔍 News Agent: No important news to interpret for {ticker}")
            return

        # 3. 각 뉴스 해석 + DB 저장
        interpretation_repo = NewsInterpretationRepository(db_session)

        for news_item in important_news:
            try:
                # NewsArticle인 경우
                if isinstance(news_item, NewsArticle):
                    news_id = news_item.id
                    headline = news_item.title
                    content = news_item.content or ""
                else:
                    # GroundingSearchLog인 경우 (긴급 뉴스)
                    news_id = None  # GroundingSearchLog는 news_articles 테이블에 없음
                    headline = news_item.query
                    content = ""

                # 이미 해석된 뉴스는 skip
                if news_id:
                    existing = interpretation_repo.get_by_news_article(news_id)
                    if existing:
                        logger.info(f"🔍 News Agent: Already interpreted news_id={news_id}, skipping")
                        continue

                # Claude API로 해석
                interpretation = await self._interpret_news(
                    ticker=ticker,
                    headline=headline,
                    content=content,
                    macro_context=macro_context
                )

                # DB 저장 (news_id가 있는 경우만)
                if news_id and interpretation:
                    interpretation_data = {
                        "news_article_id": news_id,
                        "ticker": ticker,
                        "headline_bias": interpretation["headline_bias"],
                        "expected_impact": interpretation["expected_impact"],
                        "time_horizon": interpretation["time_horizon"],
                        "confidence": interpretation["confidence"],
                        "reasoning": interpretation["reasoning"],
                        "macro_context_id": macro_context["id"] if macro_context else None,
                        "interpreted_at": datetime.now()
                    }

                    saved = interpretation_repo.create(interpretation_data)
                    logger.info(f"✅ News Agent: Saved interpretation id={saved.id} for news_id={news_id}")

            except Exception as e:
                logger.error(f"❌ News Agent: Failed to interpret news: {e}", exc_info=True)
                continue

    def _get_macro_context(self, db_session) -> Optional[Dict]:
        """
        오늘의 macro context 조회

        Returns:
            Dict: macro context 또는 None
        """
        try:
            macro_repo = MacroContextRepository(db_session)
            snapshot = macro_repo.get_by_date(date.today())

            if snapshot:
                return {
                    "id": snapshot.id,
                    "regime": snapshot.regime,
                    "fed_stance": snapshot.fed_stance,
                    "vix_category": snapshot.vix_category,
                    "market_sentiment": snapshot.market_sentiment,
                    "sp500_trend": snapshot.sp500_trend,
                    "dominant_narrative": snapshot.dominant_narrative
                }
            else:
                logger.warning(f"⚠️ No macro context for {date.today()}, using fallback")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get macro context: {e}")
            return None

    def _select_important_news(
        self,
        emergency_news: List,
        recent_news: List[NewsArticle],
        limit: int = 5
    ) -> List:
        """
        중요 뉴스 선택

        우선순위:
        1. 긴급 뉴스 (모두)
        2. sentiment_score가 높거나 낮은 뉴스
        3. 최신 뉴스

        Args:
            emergency_news: 긴급 뉴스 목록
            recent_news: 일반 뉴스 목록
            limit: 최대 개수

        Returns:
            List: 선택된 뉴스 목록
        """
        selected = []

        # 1. 긴급 뉴스 우선
        for news in emergency_news:
            if len(selected) >= limit:
                break
            selected.append(news)

        # 2. 일반 뉴스 중 sentiment 극단값 우선
        if len(selected) < limit:
            # sentiment_score 기준 정렬
            sorted_news = sorted(
                recent_news,
                key=lambda x: abs(x.sentiment_score) if hasattr(x, 'sentiment_score') and x.sentiment_score else 0,
                reverse=True
            )

            for news in sorted_news:
                if len(selected) >= limit:
                    break
                selected.append(news)

        return selected[:limit]

    async def _interpret_news(
        self,
        ticker: str,
        headline: str,
        content: str,
        macro_context: Optional[Dict]
    ) -> Optional[Dict]:
        """
        Claude API로 뉴스 해석

        Args:
            ticker: 종목 코드
            headline: 뉴스 헤드라인
            content: 뉴스 본문
            macro_context: 거시 경제 컨텍스트

        Returns:
            Dict: {
                "headline_bias": "BULLISH|BEARISH|NEUTRAL",
                "expected_impact": "HIGH|MEDIUM|LOW",
                "time_horizon": "IMMEDIATE|INTRADAY|MULTI_DAY",
                "confidence": 0.0-1.0,
                "reasoning": "해석 근거"
            }
        """
        macro_info = ""
        if macro_context:
            macro_info = f"""
현재 거시 경제 상황:
- 시장 체제: {macro_context['regime']}
- Fed 스탠스: {macro_context['fed_stance']}
- VIX: {macro_context['vix_category']}
- 시장 센티먼트: {macro_context['market_sentiment']}
- S&P 500 트렌드: {macro_context['sp500_trend']}
- 지배적 서사: {macro_context['dominant_narrative']}
"""

        prompt = f"""
당신은 {ticker} 주식에 대한 뉴스 해석 전문가입니다.

다음 뉴스를 분석하여 투자 관점에서 해석하세요:

**뉴스 헤드라인**: {headline}

**뉴스 내용**: {content[:500] if content else "내용 없음"}
{macro_info}

다음 JSON 형식으로만 응답하세요 (추가 설명 없이):
{{
  "headline_bias": "BULLISH|BEARISH|NEUTRAL",
  "expected_impact": "HIGH|MEDIUM|LOW",
  "time_horizon": "IMMEDIATE|INTRADAY|MULTI_DAY",
  "confidence": 0.0-1.0,
  "reasoning": "이 뉴스가 {ticker} 주가에 미칠 영향에 대한 간결한 해석 (100자 이내)"
}}

**주의사항**:
- headline_bias: 뉴스가 주가에 긍정적(BULLISH), 부정적(BEARISH), 중립적(NEUTRAL)인지
- expected_impact: 주가 변동 예상 크기 (HIGH: 5%+, MEDIUM: 2-5%, LOW: <2%)
- time_horizon: 영향 시점 (IMMEDIATE: 10분내, INTRADAY: 당일, MULTI_DAY: 며칠)
- confidence: 이 해석에 대한 확신도 (0.0-1.0)
- 거시 경제 상황을 고려하여 해석하세요
"""

        try:
            # Use GLM for cost efficiency
            response = await self.glm_client.chat(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            response_text = response["choices"][0]["message"]["content"].strip()

            # JSON 파싱
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            interpretation = json.loads(response_text)

            # 검증
            required_fields = ["headline_bias", "expected_impact", "time_horizon", "confidence", "reasoning"]
            for field in required_fields:
                if field not in interpretation:
                    raise ValueError(f"Missing field: {field}")

            logger.info(f"✅ News Agent: Interpreted news - {interpretation['headline_bias']} / {interpretation['expected_impact']}")
            return interpretation

        except Exception as e:
            logger.error(f"❌ News Agent: Claude interpretation failed: {e}", exc_info=True)
            return None
