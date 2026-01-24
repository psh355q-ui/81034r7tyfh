"""
Enhanced Daily Reporter - 개선된 일일 브리핑

현재 문제점:
- 다보스 포럼 같은 큰 뉴스 누락
- 주요 뉴스/영향/주가 흐름 표현 부족
- 테마별 시장 평가 없음
- 섹터별 분석 없음

개선 사항:
1. 글로벌 뉴스 수집 (다보스, Fed, 중국 등)
2. 테마별 주가 흐름 분석 (AI, 반도체, 금융 등)
3. 주요 상승/하락 테마 (Gainers/Losers)
4. 섹터별 시장 평가
5. 거시경제 지표 통합
6. 트레이딩 시그널 상세 분석

작성일: 2026-01-21
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from backend.ai.gemini_client import call_gemini_api
from backend.core.database import DatabaseSession
from backend.database.models import (
    NewsInterpretation,
    NewsArticle,
    TradingSignal,
    DeepReasoningAnalysis,
    Order,
    MacroSnapshot
)
from decimal import Decimal

logger = logging.getLogger(__name__)


class EnhancedDailyReporter:
    """
    개선된 일일 브리핑 생성기

    특징:
    - 글로벌 뉴스 우선순위 (다보스, Fed, 지정학적 리스크)
    - 테마별 시장 분석
    - 섹터별 영향도 분석
    - 주가 흐름 시각화
    - 거시경제 컨텍스트
    """

    # 주요 글로벌 이벤트 키워드 (폴백용 - TrendingNewsDetector 실패 시)
    FALLBACK_EVENT_KEYWORDS = [
        'Davos', 'WEF', 'World Economic Forum',
        'Fed', 'Federal Reserve', 'FOMC', 'Powell',
        'Trump', 'Biden', 'White House', 'President',
        'China', 'Taiwan', 'Xi Jinping',
        'Ukraine', 'Russia', 'NATO',
        'OPEC', 'Oil', 'Saudi',
        'inflation', 'CPI', 'GDP', 'jobs report',
        'earnings', 'guidance', 'revenue miss',
    ]

    # 테마 분류 (섹터별)
    THEMES = {
        'AI & Tech': ['NVDA', 'MSFT', 'GOOGL', 'META', 'ORCL', 'CRM', 'ADBE'],
        'Semiconductors': ['NVDA', 'AMD', 'INTC', 'TSM', 'ASML', 'QCOM', 'AVGO'],
        'Cloud & Software': ['MSFT', 'GOOGL', 'AMZN', 'CRM', 'SNOW', 'DDOG'],
        'Financials': ['JPM', 'BAC', 'GS', 'MS', 'C', 'WFC'],
        'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'OXY'],
        'Healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'LLY'],
        'Consumer': ['AMZN', 'TSLA', 'NKE', 'SBUX', 'MCD'],
        'Defense': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
    }

    def __init__(self):
        self.model_name = "gemini-2.0-flash-exp"

        # Trending News Detector 초기화
        try:
            from backend.ai.reporters.trending_news_detector import TrendingNewsDetector
            self.trending_detector = TrendingNewsDetector()
            self.use_trending_detection = True
        except Exception as e:
            logger.warning(f"TrendingNewsDetector not available, using fallback: {e}")
            self.trending_detector = None
            self.use_trending_detection = False

    async def generate_enhanced_briefing(self, date_str: str = None) -> str:
        """
        개선된 일일 브리핑 생성

        Returns:
            Markdown 형식의 브리핑 텍스트
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"📝 Generating Enhanced Daily Briefing for {date_str}...")

        async with DatabaseSession() as session:
            # 1. 최근 트렌딩 토픽 감지 (동적)
            trending_topics = []
            if self.use_trending_detection:
                try:
                    trending_topics = await self.trending_detector.detect_trending_topics(
                        lookback_hours=24,
                        top_n=10
                    )
                    logger.info(f"Detected {len(trending_topics)} trending topics")
                except Exception as e:
                    logger.error(f"Trending detection failed, using fallback: {e}")
                    self.use_trending_detection = False

            # 2. 글로벌 주요 뉴스 (트렌딩 토픽 기반)
            major_news = await self._get_major_global_news(session, trending_topics)

            # 2. 테마별 시장 분석
            theme_analysis = await self._analyze_themes(session)

            # 3. 섹터별 영향도 분석
            sector_impact = await self._analyze_sector_impact(session)

            # 4. 주가 흐름 (상승/하락)
            price_movements = await self._analyze_price_movements(session)

            # 5. 거시경제 컨텍스트
            macro_context = await self._get_macro_context(session)

            # 6. 트레이딩 시그널 상세
            trading_signals = await self._get_detailed_signals(session)

            # 7. 포트폴리오 현황
            portfolio_summary = await self._get_portfolio_summary(session)

            # 8. LLM으로 종합 브리핑 생성
            briefing_content = await self._synthesize_enhanced_report(
                date=date_str,
                major_news=major_news,
                theme_analysis=theme_analysis,
                sector_impact=sector_impact,
                price_movements=price_movements,
                macro_context=macro_context,
                trading_signals=trading_signals,
                portfolio=portfolio_summary,
                trending_topics=trending_topics
            )

            # 9. 면책 조항 래핑
            from backend.utils.disclaimer import wrap_briefing_with_disclaimer
            briefing_with_disclaimer = wrap_briefing_with_disclaimer(
                content=briefing_content,
                briefing_type="premarket",  # 프리마켓/일일 브리핑
                include_header=True,
                include_footer=True
            )

            # 10. 파일 저장
            md_filename = f"docs/Enhanced_Daily_Briefing_{date_str.replace('-', '')}.md"
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(briefing_with_disclaimer)

            logger.info(f"✅ Enhanced Daily Briefing saved: {md_filename}")
            return md_filename

    async def _get_major_global_news(
        self,
        session: AsyncSession,
        trending_topics: List[Dict] = None
    ) -> List[Dict]:
        """
        글로벌 주요 뉴스 수집 (트렌딩 토픽 기반)

        Args:
            session: DB 세션
            trending_topics: 감지된 트렌딩 토픽 (없으면 폴백)

        Returns:
            [{
                'title': str,
                'source': str,
                'sentiment': str,
                'impact': str,
                'reasoning': str,
                'priority': int (1-5),
                'topic': str,  # 관련 토픽
                'topic_score': float  # 토픽 점수
            }]
        """
        try:
            cutoff = datetime.now() - timedelta(hours=24)

            # NewsInterpretation + NewsArticle Join
            stmt = (
                select(NewsInterpretation, NewsArticle)
                .join(NewsArticle, NewsInterpretation.news_article_id == NewsArticle.id)
                .where(NewsInterpretation.interpreted_at >= cutoff)
                .order_by(desc(NewsInterpretation.interpreted_at))
            )
            result = await session.execute(stmt)
            interpretations = result.all()

            major_news = []

            # 트렌딩 토픽이 있으면 사용
            if trending_topics:
                # 토픽별로 뉴스 매칭
                for topic in trending_topics:
                    keywords = topic['keywords']

                    for interp, article in interpretations:
                        text = f"{article.title} {article.summary or ''}".lower()

                        # 키워드 매칭
                        if any(kw.lower() in text for kw in keywords):
                            # 이미 추가된 뉴스는 스킵
                            if any(n['title'] == article.title for n in major_news):
                                continue

                            # 우선순위 = 토픽 점수 / 20 (0-5점)
                            priority = min(int(topic['score'] / 20), 5)

                            major_news.append({
                                'title': article.title,
                                'source': article.source,
                                'sentiment': interp.headline_bias,
                                'impact': interp.expected_impact,
                                'reasoning': interp.reasoning,
                                'priority': priority,
                                'url': article.url,
                                'published': article.published_date,
                                'topic': topic['topic'],
                                'topic_score': topic['score']
                            })

                            # 토픽당 최대 3개 뉴스
                            topic_news_count = sum(1 for n in major_news if n.get('topic') == topic['topic'])
                            if topic_news_count >= 3:
                                break

            # 폴백: 하드코딩된 키워드 사용
            else:
                logger.info("Using fallback keyword-based detection")
                for interp, article in interpretations:
                    priority = self._calculate_news_priority(article.title, article.summary)

                    if priority >= 3:
                        major_news.append({
                            'title': article.title,
                            'source': article.source,
                            'sentiment': interp.headline_bias,
                            'impact': interp.expected_impact,
                            'reasoning': interp.reasoning,
                            'priority': priority,
                            'url': article.url,
                            'published': article.published_date,
                            'topic': 'General',
                            'topic_score': priority * 20
                        })

            # 우선순위 순으로 정렬
            major_news.sort(key=lambda x: (x['priority'], x.get('topic_score', 0)), reverse=True)

            # 상위 10개만
            return major_news[:10]

        except Exception as e:
            logger.error(f"Failed to get major global news: {e}")
            return []

    def _calculate_news_priority(self, title: str, summary: str) -> int:
        """
        뉴스 우선순위 계산 (폴백용, 1-5)

        5: 최우선 이벤트
        4: 중요 이벤트
        3: 보통
        2: 낮음
        1: 매우 낮음
        """
        text = f"{title} {summary}".lower()

        # 5점: 최우선 이벤트 (폴백)
        for keyword in ['davos', 'wef', 'federal reserve', 'fomc', 'powell', 'trump', 'biden', 'white house']:
            if keyword in text:
                return 5

        # 4점: 중요 이벤트
        for keyword in ['china', 'taiwan', 'ukraine', 'russia', 'earnings', 'revenue miss', 'inflation', 'cpi', 'gdp']:
            if keyword in text:
                return 4

        # 3점: 보통
        for keyword in ['market', 'stock', 'trading', 'investor']:
            if keyword in text:
                return 3

        return 2

    async def _analyze_themes(self, session: AsyncSession) -> Dict[str, Any]:
        """
        테마별 시장 분석

        Returns:
            {
                'AI & Tech': {'signal_count': 5, 'sentiment': 'BULLISH', 'tickers': [...]},
                'Semiconductors': {...},
                ...
            }
        """
        try:
            cutoff = datetime.now() - timedelta(hours=24)

            # 최근 트레이딩 시그널 조회
            stmt = (
                select(TradingSignal)
                .where(TradingSignal.created_at >= cutoff)
                .order_by(desc(TradingSignal.created_at))
            )
            result = await session.execute(stmt)
            signals = result.scalars().all()

            # 테마별 분류
            theme_data = {}
            for theme_name, tickers in self.THEMES.items():
                theme_signals = [s for s in signals if s.ticker in tickers]

                if theme_signals:
                    # 감성 집계
                    bullish_count = sum(1 for s in theme_signals if s.action == 'BUY')
                    bearish_count = sum(1 for s in theme_signals if s.action == 'SELL')

                    sentiment = 'NEUTRAL'
                    if bullish_count > bearish_count * 1.5:
                        sentiment = 'BULLISH'
                    elif bearish_count > bullish_count * 1.5:
                        sentiment = 'BEARISH'

                    theme_data[theme_name] = {
                        'signal_count': len(theme_signals),
                        'sentiment': sentiment,
                        'bullish_count': bullish_count,
                        'bearish_count': bearish_count,
                        'tickers': list(set(s.ticker for s in theme_signals))
                    }

            return theme_data

        except Exception as e:
            logger.error(f"Failed to analyze themes: {e}")
            return {}

    async def _analyze_sector_impact(self, session: AsyncSession) -> Dict[str, Any]:
        """
        섹터별 영향도 분석

        Returns:
            {
                'Gainers': [{'theme': 'AI & Tech', 'impact': 'HIGH', 'reason': '...'}],
                'Losers': [...]
            }
        """
        try:
            cutoff = datetime.now() - timedelta(hours=24)

            # Deep Reasoning 분석 조회
            stmt = (
                select(DeepReasoningAnalysis)
                .where(DeepReasoningAnalysis.created_at >= cutoff)
                .order_by(desc(DeepReasoningAnalysis.created_at))
                .limit(10)
            )
            result = await session.execute(stmt)
            analyses = result.scalars().all()

            gainers = []
            losers = []

            for analysis in analyses:
                # 수혜주 (Gainers)
                if analysis.primary_beneficiary_action == 'BUY':
                    # 테마 찾기
                    theme = self._find_theme_by_ticker(analysis.primary_beneficiary_ticker)

                    gainers.append({
                        'theme': theme or analysis.theme,
                        'ticker': analysis.primary_beneficiary_ticker,
                        'impact': 'HIGH',
                        'reason': analysis.bull_case[:150]
                    })

                # 하락주 (Losers)
                elif analysis.primary_beneficiary_action == 'SELL':
                    theme = self._find_theme_by_ticker(analysis.primary_beneficiary_ticker)

                    losers.append({
                        'theme': theme or analysis.theme,
                        'ticker': analysis.primary_beneficiary_ticker,
                        'impact': 'HIGH',
                        'reason': analysis.bear_case[:150]
                    })

            return {
                'gainers': gainers[:5],  # 상위 5개
                'losers': losers[:5]
            }

        except Exception as e:
            logger.error(f"Failed to analyze sector impact: {e}")
            return {'gainers': [], 'losers': []}

    def _find_theme_by_ticker(self, ticker: str) -> Optional[str]:
        """티커로 테마 찾기"""
        for theme_name, tickers in self.THEMES.items():
            if ticker in tickers:
                return theme_name
        return None

    async def _analyze_price_movements(self, session: AsyncSession) -> Dict[str, Any]:
        """
        주가 흐름 분석 (상승/하락)

        Returns:
            {
                'top_gainers': [{'ticker': 'NVDA', 'change': '+5.2%', 'reason': '...'}],
                'top_losers': [...],
                'market_trend': 'BULLISH' | 'BEARISH' | 'MIXED'
            }
        """
        try:
            cutoff = datetime.now() - timedelta(hours=24)

            # 최근 주문 실행 내역 조회
            stmt = (
                select(Order)
                .where(
                    and_(
                        Order.created_at >= cutoff,
                        Order.status == 'FILLED'
                    )
                )
                .order_by(desc(Order.created_at))
            )
            result = await session.execute(stmt)
            orders = result.scalars().all()

            # 티커별 집계
            ticker_data = defaultdict(lambda: {'buy_count': 0, 'sell_count': 0, 'volume': 0})

            for order in orders:
                ticker_data[order.ticker]['volume'] += order.filled_quantity or 0
                if order.action == 'BUY':
                    ticker_data[order.ticker]['buy_count'] += 1
                elif order.action == 'SELL':
                    ticker_data[order.ticker]['sell_count'] += 1

            # 상승주 (매수 많음)
            gainers = []
            for ticker, data in ticker_data.items():
                if data['buy_count'] > data['sell_count']:
                    gainers.append({
                        'ticker': ticker,
                        'buy_count': data['buy_count'],
                        'volume': data['volume']
                    })

            # 하락주 (매도 많음)
            losers = []
            for ticker, data in ticker_data.items():
                if data['sell_count'] > data['buy_count']:
                    losers.append({
                        'ticker': ticker,
                        'sell_count': data['sell_count'],
                        'volume': data['volume']
                    })

            # 정렬
            gainers.sort(key=lambda x: x['buy_count'], reverse=True)
            losers.sort(key=lambda x: x['sell_count'], reverse=True)

            # 시장 전반 트렌드
            total_buy = sum(d['buy_count'] for d in ticker_data.values())
            total_sell = sum(d['sell_count'] for d in ticker_data.values())

            if total_buy > total_sell * 1.5:
                market_trend = 'BULLISH'
            elif total_sell > total_buy * 1.5:
                market_trend = 'BEARISH'
            else:
                market_trend = 'MIXED'

            return {
                'top_gainers': gainers[:5],
                'top_losers': losers[:5],
                'market_trend': market_trend
            }

        except Exception as e:
            logger.error(f"Failed to analyze price movements: {e}")
            return {'top_gainers': [], 'top_losers': [], 'market_trend': 'UNKNOWN'}

    async def _get_macro_context(self, session: AsyncSession) -> Dict[str, Any]:
        """
        거시경제 컨텍스트

        Returns:
            {
                'regime': 'GOLDILOCKS',
                'fed_stance': 'NEUTRAL',
                'vix_level': 15.5,
                'market_sentiment': 'RISK_ON',
                'key_indicators': {...}
            }
        """
        try:
            # 최신 MacroSnapshot 조회
            stmt = (
                select(MacroSnapshot)
                .order_by(desc(MacroSnapshot.snapshot_date))
                .limit(1)
            )
            result = await session.execute(stmt)
            snapshot = result.scalar_one_or_none()

            if snapshot:
                return {
                    'regime': snapshot.regime,
                    'fed_stance': snapshot.fed_stance,
                    'vix_level': float(snapshot.vix_level),
                    'vix_category': snapshot.vix_category,
                    'market_sentiment': snapshot.market_sentiment,
                    'snapshot_date': snapshot.snapshot_date.isoformat()
                }
            else:
                return {
                    'regime': 'UNKNOWN',
                    'fed_stance': 'UNKNOWN',
                    'vix_level': 0.0,
                    'market_sentiment': 'UNKNOWN'
                }

        except Exception as e:
            logger.error(f"Failed to get macro context: {e}")
            return {}

    async def _get_detailed_signals(self, session: AsyncSession) -> List[Dict]:
        """
        트레이딩 시그널 상세 분석

        Returns:
            [{
                'ticker': 'NVDA',
                'action': 'BUY',
                'signal_type': 'PRIMARY',
                'reasoning': '...',
                'confidence': 0.85
            }]
        """
        try:
            cutoff = datetime.now() - timedelta(hours=24)

            stmt = (
                select(TradingSignal)
                .where(TradingSignal.created_at >= cutoff)
                .order_by(desc(TradingSignal.created_at))
                .limit(10)
            )
            result = await session.execute(stmt)
            signals = result.scalars().all()

            signal_list = []
            for s in signals:
                signal_list.append({
                    'ticker': s.ticker,
                    'action': s.action,
                    'signal_type': s.signal_type,
                    'reasoning': s.reasoning,
                    'confidence': float(s.confidence) if s.confidence else 0.0,
                    'created_at': s.created_at.isoformat()
                })

            return signal_list

        except Exception as e:
            logger.error(f"Failed to get detailed signals: {e}")
            return []

    async def _get_portfolio_summary(self, session: AsyncSession) -> Dict[str, Any]:
        """포트폴리오 현황 (기존 로직 재사용)"""
        try:
            from backend.ai.portfolio.account_partitioning import AccountPartitionManager
            partition_manager = AccountPartitionManager()

            summary = await asyncio.to_thread(partition_manager.get_all_summaries)
            return summary
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {}

    async def _synthesize_enhanced_report(
        self,
        date: str,
        major_news: List[Dict],
        theme_analysis: Dict,
        sector_impact: Dict,
        price_movements: Dict,
        macro_context: Dict,
        trading_signals: List[Dict],
        portfolio: Dict,
        trending_topics: List[Dict] = None
    ) -> str:
        """
        LLM으로 종합 브리핑 생성
        """

        # 트렌딩 토픽 요약
        trending_summary = ""
        if trending_topics:
            trending_summary = "**📈 최근 24시간 트렌딩 토픽 (자동 감지):**\n"
            for i, topic in enumerate(trending_topics[:5], 1):
                trending_summary += f"{i}. {topic['topic']} (점수: {topic['score']}/100, 영향력: {topic.get('market_impact', 'N/A')})\n"
            trending_summary += "\n이 토픽들을 중심으로 뉴스를 분석하세요.\n"

        prompt = f"""
당신은 AI 트레이딩 시스템의 최고 투자 책임자(CIO)입니다. {date} 일일 브리핑을 작성하세요.

[데이터 소스]

{trending_summary}

1. 🌍 글로벌 주요 뉴스 (동적 감지):
{json.dumps(major_news, indent=2, ensure_ascii=False)}

2. 📊 테마별 시장 분석:
{json.dumps(theme_analysis, indent=2, ensure_ascii=False)}

3. 📈 섹터별 영향도 (수혜주/피해주):
{json.dumps(sector_impact, indent=2, ensure_ascii=False)}

4. 💹 주가 흐름 (상승/하락):
{json.dumps(price_movements, indent=2, ensure_ascii=False)}

5. 🌐 거시경제 컨텍스트:
{json.dumps(macro_context, indent=2, ensure_ascii=False)}

6. 🎯 트레이딩 시그널 상세:
{json.dumps(trading_signals, indent=2, ensure_ascii=False)}

7. 💼 포트폴리오 현황:
{json.dumps(portfolio, indent=2, ensure_ascii=False)}

[작성 형식]

# 📢 AI 일일 투자 브리핑 ({date})

> "시장은 뉴스를 먹고 자란다" - 월스트리트 격언

---

## 1. 🌍 오늘의 주요 뉴스

### 최근 이슈 (동적 감지)
[위에서 감지된 트렌딩 토픽을 기반으로 주요 이벤트를 구체적으로 설명]

**중요**: 다음 토픽들이 최근 24시간 동안 가장 많이 언급되었습니다:
{[f"- {t['topic']} (점수: {t['score']}/100)" for t in (trending_topics or [])] if trending_topics else "- (트렌딩 토픽 감지 실패, 일반 뉴스 분석)"}

각 토픽에 대해:
- 🔴 **[토픽명]**: [주요 발표 내용 요약]
  - 핵심 내용
  - 시장 영향: [긍정적/부정적/중립]
  - 관련 종목 영향

**예시 형식만 참고** (실제 데이터 기반으로 작성):
- 🔴 **토픽1**: [실제 뉴스 내용]
- 🔵 **토픽2**: [실제 뉴스 내용]

---

## 2. 📊 테마별 시장 분석

### 주요 상승 테마 (Gainers) 🚀
[데이터 기반으로 구체적인 테마와 이유 설명]

**예시**:
1. **AI & Tech** (신호: 5개, 감성: BULLISH)
   - 주요 종목: NVDA, MSFT, GOOGL
   - 이유: [구체적인 뉴스/실적/기술 발전]
   - 시장 예상: [향후 전망]

2. **Semiconductors** (신호: 3개, 감성: BULLISH)
   - 주요 종목: AMD, INTC
   - 이유: [공급망 개선/수요 증가]

### 주요 하락 테마 (Losers) 📉
[마찬가지로 구체적으로]

---

## 3. 💹 주가 흐름 및 시장 분위기

### 오늘의 시장 트렌드: [{price_movements['market_trend']}]

**상승주 Top 5**:
1. [티커] - [+X%] - [상승 이유]
2. ...

**하락주 Top 5**:
1. [티커] - [-X%] - [하락 이유]
2. ...

---

## 4. 🌐 거시경제 컨텍스트

- **시장 레짐**: [{macro_context.get('regime', 'UNKNOWN')}]
- **Fed 스탠스**: [{macro_context.get('fed_stance', 'UNKNOWN')}]
- **VIX 지수**: [{macro_context.get('vix_level', 'N/A')}] ({macro_context.get('vix_category', 'UNKNOWN')})
- **시장 심리**: [{macro_context.get('market_sentiment', 'UNKNOWN')}]

**해석**: [VIX와 시장 심리를 바탕으로 투자자들이 어떻게 행동해야 하는지 제언]

---

## 5. 🎯 AI 트레이딩 시그널

### 생성된 시그널 요약
[각 시그널을 표 형식으로 정리]

| 티커 | 액션 | 타입 | 신뢰도 | 이유 |
|------|------|------|--------|------|
| NVDA | BUY | PRIMARY | 85% | [간략한 이유] |
| ... | ... | ... | ... | ... |

---

## 6. 💼 포트폴리오 현황

- **총 자산**: ${portfolio.get('total_value', 0):,.2f}
- **일일 손익**: ${portfolio.get('daily_pnl', 0):,.2f} ({portfolio.get('daily_pnl_pct', 0):.2f}%)
- **포지션 수**: {portfolio.get('positions_count', 0)}개
- **승률**: {portfolio.get('win_rate', 0):.1f}%

---

## 7. 🚀 투자 전략 제언

[데이터를 종합하여 구체적인 행동 제언]

**예시**:
1. **단기 (1-3일)**:
   - AI/반도체 섹터 강세 지속 예상 → NVDA, AMD 매수 고려
   - VIX 낮음(15 이하) → 리스크 온 모드

2. **중기 (1-2주)**:
   - Fed 금리 동결 예상 → 성장주 우호적
   - 다보스 포럼 후속 반응 주시

3. **리스크 요인**:
   - 중국 경제 둔화
   - 실적 시즌 서프라이즈

---

## 8. 📝 핵심 요약 (TL;DR)

- ✅ **오늘의 핵심**: [3줄 요약]
- ⚠️ **주의사항**: [리스크 요인 1줄]
- 🎯 **추천 행동**: [구체적인 액션 1줄]

---

**작성 톤**: 전문적이고 신뢰감 있으며, 데이터 기반으로 명료하게.
**언어**: 한국어 (Korean)
**이모지**: 각 섹션에 적절한 이모지 사용하여 가독성 향상
**구체성**: 모호한 표현 금지, 구체적인 숫자와 이유 명시

**중요**:
1. 트렌딩 토픽 리스트를 참고하여 **실제로 최근 이슈가 되는 뉴스**를 메인에 표시하세요.
2. "다보스", "Fed" 같은 하드코딩된 키워드에 의존하지 말고, major_news 데이터의 'topic' 필드를 확인하세요.
3. 각 뉴스의 'topic_score'가 높을수록 더 중요한 이슈입니다.
4. major_news가 비어있으면 "최근 24시간 특별한 이슈 없음"이라고 명시하세요.
"""

        response = await call_gemini_api(prompt, self.model_name)
        return response


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        reporter = EnhancedDailyReporter()
        filename = await reporter.generate_enhanced_briefing()
        print(f"✅ Enhanced Daily Briefing generated: {filename}")

    asyncio.run(test())
