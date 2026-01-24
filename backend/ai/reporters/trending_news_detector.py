"""
Trending News Detector - 최근 이슈 자동 감지

하드코딩된 키워드 대신 동적으로 최근 트렌드를 감지:
1. 뉴스 빈도 분석 (24시간 내 등장 횟수)
2. 시장 영향력 분석 (트레이딩 시그널 생성 여부)
3. LLM을 통한 중요도 평가
4. 시간 경과에 따른 자연스러운 우선순위 조정

작성일: 2026-01-21
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from collections import Counter
import re

from backend.ai.gemini_client import call_gemini_api
from backend.core.database import DatabaseSession
from backend.database.models import (
    NewsInterpretation,
    NewsArticle,
    TradingSignal,
    DeepReasoningAnalysis
)

logger = logging.getLogger(__name__)


class TrendingNewsDetector:
    """
    최근 이슈를 동적으로 감지하는 시스템

    특징:
    - 뉴스 빈도 분석 (자주 등장하는 키워드/이벤트)
    - 시장 영향력 분석 (트레이딩 시그널 생성 여부)
    - LLM을 통한 중요도 평가
    - 시간 경과에 따른 자연스러운 감쇠 (decay)
    """

    def __init__(self):
        self.model_name = "gemini-2.0-flash-exp"

    async def detect_trending_topics(
        self,
        lookback_hours: int = 24,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        최근 트렌딩 토픽 감지

        Args:
            lookback_hours: 분석 기간 (시간)
            top_n: 상위 N개 토픽

        Returns:
            [{
                'topic': str,  # 토픽명 (예: "Davos Forum", "Fed Rate Cut")
                'score': float,  # 중요도 점수 (0-100)
                'frequency': int,  # 등장 횟수
                'market_impact': str,  # HIGH/MEDIUM/LOW
                'sentiment': str,  # BULLISH/BEARISH/NEUTRAL
                'key_news': [...]  # 관련 주요 뉴스
            }]
        """
        async with DatabaseSession() as session:
            cutoff = datetime.now() - timedelta(hours=lookback_hours)

            # 1. 뉴스 수집
            news_articles = await self._fetch_recent_news(session, cutoff)

            if not news_articles:
                logger.warning("No recent news found")
                return []

            # 2. 키워드 추출 및 빈도 분석
            keyword_freq = await self._analyze_keyword_frequency(news_articles)

            # 3. 토픽 클러스터링 (유사 키워드 그룹화)
            topics = await self._cluster_keywords_to_topics(keyword_freq, news_articles)

            # 4. 시장 영향력 분석
            topics_with_impact = await self._analyze_market_impact(session, topics, cutoff)

            # 5. LLM으로 중요도 평가
            scored_topics = await self._score_topics_with_llm(topics_with_impact, news_articles)

            # 6. 정렬 및 상위 N개 반환
            scored_topics.sort(key=lambda x: x['score'], reverse=True)

            return scored_topics[:top_n]

    async def _fetch_recent_news(
        self,
        session: AsyncSession,
        cutoff: datetime
    ) -> List[Tuple[NewsArticle, Optional[NewsInterpretation]]]:
        """최근 뉴스 가져오기"""
        try:
            stmt = (
                select(NewsArticle, NewsInterpretation)
                .outerjoin(NewsInterpretation, NewsArticle.id == NewsInterpretation.news_article_id)
                .where(NewsArticle.published_date >= cutoff)
                .order_by(desc(NewsArticle.published_date))
                .limit(100)  # 최근 100개
            )
            result = await session.execute(stmt)
            return result.all()

        except Exception as e:
            logger.error(f"Failed to fetch recent news: {e}")
            return []

    async def _analyze_keyword_frequency(
        self,
        news_articles: List[Tuple[NewsArticle, Optional[NewsInterpretation]]]
    ) -> Counter:
        """
        키워드 빈도 분석

        Returns:
            Counter({'Trump': 15, 'Fed': 12, 'China': 10, ...})
        """
        keywords = []

        for article, interp in news_articles:
            # 제목에서 키워드 추출
            title_words = self._extract_keywords_from_text(article.title)
            keywords.extend(title_words)

            # 요약에서도 추출
            if article.summary:
                summary_words = self._extract_keywords_from_text(article.summary)
                keywords.extend(summary_words)

        # 빈도 계산
        freq = Counter(keywords)

        # 불용어 제거 (a, the, is 등)
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but'}
        freq = Counter({k: v for k, v in freq.items() if k.lower() not in stopwords})

        return freq

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출

        - 대문자로 시작하는 단어 (고유명사)
        - 2글자 이상
        - 숫자 제외
        """
        if not text:
            return []

        # 단어 분리
        words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)

        # 필터링
        keywords = [w for w in words if len(w) >= 2 and not w.isdigit()]

        return keywords

    async def _cluster_keywords_to_topics(
        self,
        keyword_freq: Counter,
        news_articles: List[Tuple[NewsArticle, Optional[NewsInterpretation]]]
    ) -> List[Dict[str, Any]]:
        """
        키워드를 토픽으로 클러스터링

        예:
        - 'Trump', 'Trump administration', 'President Trump' → 'Trump Administration'
        - 'Fed', 'Federal Reserve', 'Powell' → 'Federal Reserve'
        - 'Davos', 'WEF', 'World Economic Forum' → 'Davos Forum'
        """
        # LLM으로 클러스터링
        top_keywords = [k for k, v in keyword_freq.most_common(30)]

        prompt = f"""
다음은 최근 24시간 뉴스에서 자주 등장한 키워드 목록입니다:

{', '.join(top_keywords)}

이 키워드들을 의미가 유사한 것끼리 그룹화하여 "토픽"으로 만들어주세요.

출력 형식 (JSON):
[
    {{
        "topic": "토픽명 (예: Trump Administration, Federal Reserve, China-Taiwan Tensions)",
        "keywords": ["관련 키워드1", "관련 키워드2", ...],
        "description": "토픽 설명 (1줄)"
    }},
    ...
]

규칙:
- 최대 10개 토픽
- 각 토픽은 명확하고 구체적으로 (예: "Trump" → "Trump Administration Policies")
- 시장에 영향을 줄 수 있는 토픽 우선
- JSON 형식으로만 출력, 추가 설명 불필요
"""

        try:
            response = await call_gemini_api(prompt, self.model_name)

            # JSON 파싱
            import json
            # Gemini가 ```json ... ``` 로 감쌀 수 있으므로 제거
            response_clean = response.strip()
            if response_clean.startswith('```'):
                response_clean = response_clean.split('```')[1]
                if response_clean.startswith('json'):
                    response_clean = response_clean[4:]
            response_clean = response_clean.strip()

            topics = json.loads(response_clean)

            # 빈도 추가
            for topic in topics:
                topic['frequency'] = sum(keyword_freq.get(kw, 0) for kw in topic['keywords'])

            return topics

        except Exception as e:
            logger.error(f"Failed to cluster keywords: {e}")
            # 폴백: 상위 키워드를 토픽으로 사용
            return [
                {
                    'topic': keyword,
                    'keywords': [keyword],
                    'description': f'News about {keyword}',
                    'frequency': count
                }
                for keyword, count in keyword_freq.most_common(10)
            ]

    async def _analyze_market_impact(
        self,
        session: AsyncSession,
        topics: List[Dict[str, Any]],
        cutoff: datetime
    ) -> List[Dict[str, Any]]:
        """
        토픽별 시장 영향력 분석

        - 트레이딩 시그널 생성 여부
        - Deep Reasoning 분석 여부
        """
        try:
            # 최근 트레이딩 시그널 조회
            stmt_signals = (
                select(TradingSignal)
                .where(TradingSignal.created_at >= cutoff)
            )
            result_signals = await session.execute(stmt_signals)
            signals = result_signals.scalars().all()

            # Deep Reasoning 조회
            stmt_dr = (
                select(DeepReasoningAnalysis)
                .where(DeepReasoningAnalysis.created_at >= cutoff)
            )
            result_dr = await session.execute(stmt_dr)
            analyses = result_dr.scalars().all()

            # 토픽별 영향력 계산
            for topic in topics:
                keywords = topic['keywords']

                # 시그널 매칭
                related_signals = [
                    s for s in signals
                    if any(kw.lower() in s.reasoning.lower() for kw in keywords)
                ]

                # Deep Reasoning 매칭
                related_analyses = [
                    a for a in analyses
                    if any(kw.lower() in a.theme.lower() for kw in keywords)
                ]

                # 영향력 계산
                signal_count = len(related_signals)
                analysis_count = len(related_analyses)

                if signal_count >= 3 or analysis_count >= 2:
                    topic['market_impact'] = 'HIGH'
                elif signal_count >= 1 or analysis_count >= 1:
                    topic['market_impact'] = 'MEDIUM'
                else:
                    topic['market_impact'] = 'LOW'

                # 감성 계산 (시그널 기준)
                if related_signals:
                    buy_count = sum(1 for s in related_signals if s.action == 'BUY')
                    sell_count = sum(1 for s in related_signals if s.action == 'SELL')

                    if buy_count > sell_count * 1.5:
                        topic['sentiment'] = 'BULLISH'
                    elif sell_count > buy_count * 1.5:
                        topic['sentiment'] = 'BEARISH'
                    else:
                        topic['sentiment'] = 'NEUTRAL'
                else:
                    topic['sentiment'] = 'NEUTRAL'

            return topics

        except Exception as e:
            logger.error(f"Failed to analyze market impact: {e}")
            # 폴백: 모든 토픽 LOW로 설정
            for topic in topics:
                topic['market_impact'] = 'LOW'
                topic['sentiment'] = 'NEUTRAL'
            return topics

    async def _score_topics_with_llm(
        self,
        topics: List[Dict[str, Any]],
        news_articles: List[Tuple[NewsArticle, Optional[NewsInterpretation]]]
    ) -> List[Dict[str, Any]]:
        """
        LLM으로 토픽 중요도 평가 (0-100점)

        고려 사항:
        - 빈도 (자주 등장할수록 높음)
        - 시장 영향력 (HIGH > MEDIUM > LOW)
        - 시의성 (최근 뉴스일수록 높음)
        - 글로벌 영향력 (글로벌 이벤트 > 지역 이벤트)
        """
        try:
            # 토픽 요약
            topics_summary = []
            for topic in topics:
                topics_summary.append({
                    'topic': topic['topic'],
                    'frequency': topic['frequency'],
                    'market_impact': topic['market_impact'],
                    'sentiment': topic['sentiment']
                })

            prompt = f"""
다음은 최근 24시간 뉴스에서 감지된 토픽들입니다:

{topics_summary}

각 토픽의 중요도를 0-100점으로 평가해주세요.

평가 기준:
1. 시장 영향력 (40점): 주식/채권/외환 시장에 미치는 영향
2. 글로벌 영향력 (30점): 전 세계적 관심도
3. 시의성 (20점): 현재 진행 중이거나 곧 발생할 이벤트
4. 빈도 (10점): 뉴스 등장 횟수

출력 형식 (JSON):
[
    {{
        "topic": "토픽명",
        "score": 85,
        "reasoning": "평가 이유 (1줄)"
    }},
    ...
]

규칙:
- 객관적으로 평가 (감정 배제)
- 실제 시장에 영향을 줄 토픽 우선 (예: Fed 금리 > 연예인 스캔들)
- JSON 형식으로만 출력
"""

            response = await call_gemini_api(prompt, self.model_name)

            # JSON 파싱
            import json
            response_clean = response.strip()
            if response_clean.startswith('```'):
                response_clean = response_clean.split('```')[1]
                if response_clean.startswith('json'):
                    response_clean = response_clean[4:]
            response_clean = response_clean.strip()

            scores = json.loads(response_clean)

            # 토픽에 점수 추가
            score_dict = {s['topic']: s for s in scores}

            for topic in topics:
                if topic['topic'] in score_dict:
                    topic['score'] = score_dict[topic['topic']]['score']
                    topic['reasoning'] = score_dict[topic['topic']]['reasoning']
                else:
                    # 폴백: 빈도와 영향력 기준 점수
                    freq_score = min(topic['frequency'] * 2, 30)
                    impact_score = {'HIGH': 40, 'MEDIUM': 20, 'LOW': 10}.get(topic['market_impact'], 10)
                    topic['score'] = freq_score + impact_score
                    topic['reasoning'] = 'Automatic scoring based on frequency and impact'

            return topics

        except Exception as e:
            logger.error(f"Failed to score topics with LLM: {e}")
            # 폴백: 빈도와 영향력 기준 점수
            for topic in topics:
                freq_score = min(topic['frequency'] * 2, 30)
                impact_score = {'HIGH': 40, 'MEDIUM': 20, 'LOW': 10}.get(topic.get('market_impact', 'LOW'), 10)
                topic['score'] = freq_score + impact_score
                topic['reasoning'] = 'Automatic scoring based on frequency and impact'

            return topics

    async def get_key_news_for_topic(
        self,
        topic: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        특정 토픽의 주요 뉴스 가져오기

        Returns:
            [{
                'title': str,
                'source': str,
                'url': str,
                'published': datetime,
                'sentiment': str
            }]
        """
        async with DatabaseSession() as session:
            keywords = topic['keywords']
            cutoff = datetime.now() - timedelta(hours=24)

            try:
                # 키워드 포함 뉴스 조회
                stmt = (
                    select(NewsArticle, NewsInterpretation)
                    .outerjoin(NewsInterpretation, NewsArticle.id == NewsInterpretation.news_article_id)
                    .where(NewsArticle.published_date >= cutoff)
                    .order_by(desc(NewsArticle.published_date))
                )
                result = await session.execute(stmt)
                all_news = result.all()

                # 키워드 매칭
                related_news = []
                for article, interp in all_news:
                    text = f"{article.title} {article.summary or ''}".lower()
                    if any(kw.lower() in text for kw in keywords):
                        related_news.append({
                            'title': article.title,
                            'source': article.source,
                            'url': article.url,
                            'published': article.published_date,
                            'sentiment': interp.headline_bias if interp else 'NEUTRAL'
                        })

                        if len(related_news) >= limit:
                            break

                return related_news

            except Exception as e:
                logger.error(f"Failed to get key news: {e}")
                return []


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        detector = TrendingNewsDetector()

        print("=" * 70)
        print("Trending News Detector Test")
        print("=" * 70)

        # 트렌딩 토픽 감지
        topics = await detector.detect_trending_topics(lookback_hours=24, top_n=10)

        print(f"\n📊 Detected {len(topics)} trending topics:\n")

        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic['topic']} (Score: {topic['score']}/100)")
            print(f"   Frequency: {topic['frequency']} mentions")
            print(f"   Market Impact: {topic['market_impact']}")
            print(f"   Sentiment: {topic['sentiment']}")
            print(f"   Reasoning: {topic['reasoning']}")
            print()

        # 상위 토픽의 주요 뉴스
        if topics:
            print("=" * 70)
            print(f"Key News for Top Topic: {topics[0]['topic']}")
            print("=" * 70)

            key_news = await detector.get_key_news_for_topic(topics[0], limit=5)

            for i, news in enumerate(key_news, 1):
                print(f"{i}. {news['title']}")
                print(f"   Source: {news['source']}")
                print(f"   Sentiment: {news['sentiment']}")
                print()

    asyncio.run(test())
