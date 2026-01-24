"""
US Market Close Reporter - 미국장 마감 브리핑 v2.3
==================================================

v2.3 업데이트 (2026-01-24):
- ChatGPT/Gemini 피드백 기반 전면 개편
- 시점 분리 시스템 (CLOSING/MORNING 모드)
- 교과서적 정의 삭제, 결과 중심 분석
- JSON 프로토콜 출력 준비

기존 기능:
1. S&P500 대형주 중심 분석
2. 거시지표 분석 (금, 은, BTC, DXY, USD/KRW, 10Y Treasury)
3. 경제캘린더 연동
4. 데이터 부족 시 Gemini 웹검색 폴백
5. Risk Agent + Trader Agent 분석 패턴

작성일: 2026-01-24
업데이트: 2026-01-24 (v2.3 시점 분리 시스템)
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.ai.gemini_client import call_gemini_api
from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, EconomicEvent
from backend.utils.disclaimer import wrap_briefing_with_disclaimer

# v2.3: 시점 분리 시스템
from backend.ai.reporters.briefing_mode import (
    BriefingMode,
    get_current_briefing_mode,
    get_mode_constraints,
    validate_output_for_mode,
)
from backend.ai.reporters.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class USMarketCloseReporter:
    """
    미국장 마감 브리핑 생성기 (개선 버전)

    Features:
    - S&P500 대형주 중심 분석
    - 거시지표 (금, 은, BTC, DXY, USD/KRW, 10Y Treasury)
    - 경제캘린더 연동
    - 데이터 부족 시 Gemini 웹검색 폴백
    - Risk Agent 스타일 리스크 분석 (Sharpe Ratio, VaR, Kelly Criterion)
    - Trader Agent 스타일 기술적 분석 (S/R, MTF, Bollinger Bands)
    - 매수/매도세 및 기관 현금흐름 분석
    """

    # S&P500 대형주 (시가총액 상위)
    MEGA_CAPS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'BRK.B', 'LLY']
    LARGE_CAPS = ['UNH', 'JPM', 'V', 'XOM', 'MA', 'JNJ', 'PG', 'HD', 'COST', 'ABBV',
                  'MRK', 'CVX', 'AVGO', 'KO', 'PEP', 'WMT', 'BAC', 'CRM', 'ORCL', 'AMD']

    # 거시지표 키워드
    MACRO_KEYWORDS = {
        'gold': ['gold', 'xau', '금', '금값'],
        'silver': ['silver', 'xag', '은', '은값'],
        'bitcoin': ['bitcoin', 'btc', '비트코인'],
        'dollar_index': ['dxy', 'dollar index', '달러인덱스'],
        'usdkrw': ['usd/krw', 'usdkrw', '원달러', '환율', 'won'],
        'treasury_10y': ['10-year', '10y treasury', '국채', 'yield', '금리'],
        'oil': ['wti', 'crude oil', '유가', 'oil'],
        'vix': ['vix', '변동성', 'volatility']
    }

    def __init__(self):
        self.model_name = "gemini-2.0-flash-exp"

    async def generate_us_close_briefing(
        self,
        date_str: str = None,
        mode: BriefingMode = None
    ) -> str:
        """
        미국장 마감 브리핑 생성 (v2.3 - 모드 기반)

        Args:
            date_str: 날짜 문자열 (YYYY-MM-DD)
            mode: 브리핑 모드 (None이면 자동 감지)

        Returns:
            저장된 파일 경로
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # v2.3: 모드 자동 감지
        if mode is None:
            mode = get_current_briefing_mode()

        logger.info(f"🇺🇸 Generating Briefing for {date_str} (Mode: {mode.value})...")

        db = get_sync_session()

        try:
            # 1. 최근 뉴스 수집 (6시간)
            cutoff = datetime.now() - timedelta(hours=6)
            recent_news = db.query(NewsArticle).filter(
                NewsArticle.published_date >= cutoff
            ).order_by(NewsArticle.published_date.desc()).limit(50).all()

            logger.info(f"[1/6] 최근 6시간 뉴스: {len(recent_news)}개")

            # 2. 대형주 관련 뉴스 분류
            mega_cap_news = self._filter_news_by_tickers(recent_news, self.MEGA_CAPS)
            large_cap_news = self._filter_news_by_tickers(recent_news, self.LARGE_CAPS)
            other_news = [n for n in recent_news if n not in mega_cap_news and n not in large_cap_news]

            logger.info(f"[2/6] 메가캡 뉴스: {len(mega_cap_news)}개, 대형주: {len(large_cap_news)}개, 기타: {len(other_news)}개")

            # 3. 거시지표 관련 뉴스
            macro_news = self._filter_macro_news(recent_news)
            logger.info(f"[3/6] 거시지표 뉴스: {len(macro_news)}개")

            # 4. 경제캘린더 조회
            economic_events = self._get_economic_events(db, date_str)
            logger.info(f"[4/6] 오늘/내일 경제지표: {len(economic_events)}개")

            # 5. Gemini로 브리핑 생성 (데이터 부족 시 웹검색 요청)
            logger.info("[5/6] Gemini API로 브리핑 생성 중...")

            briefing_content = await self._generate_briefing_with_gemini(
                date_str=date_str,
                mega_cap_news=mega_cap_news,
                large_cap_news=large_cap_news,
                other_news=other_news[:10],  # 중소형주는 10개만
                macro_news=macro_news,
                economic_events=economic_events,
                has_sufficient_data=len(recent_news) > 10,
                mode=mode  # v2.3: 모드 전달
            )

            # 6. 면책 조항 추가 및 저장
            logger.info("[6/6] 면책 조항 추가 및 저장...")

            # v2.3: 모드에 따른 브리핑 타입 설정
            briefing_type_map = {
                BriefingMode.CLOSING: "closing",
                BriefingMode.MORNING: "premarket",
                BriefingMode.INTRADAY: "intraday",
                BriefingMode.KOREAN: "korean",
            }

            final_content = wrap_briefing_with_disclaimer(
                content=briefing_content,
                briefing_type=briefing_type_map.get(mode, "closing"),
                include_header=True,
                include_footer=True
            )

            # v2.3: 모드별 파일명
            filename = f"docs/Briefing_{mode.value}_{date_str.replace('-', '')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(final_content)

            logger.info(f"✅ US Close Briefing saved: {filename}")
            return filename

        finally:
            db.close()

    def _filter_news_by_tickers(self, news_list: List, tickers: List[str]) -> List:
        """티커 기반 뉴스 필터링"""
        filtered = []
        for article in news_list:
            text = f"{article.title} {article.summary or ''}".upper()
            for ticker in tickers:
                if ticker in text or f"${ticker}" in text:
                    filtered.append(article)
                    break
        return filtered

    def _filter_macro_news(self, news_list: List) -> Dict[str, List]:
        """거시지표 관련 뉴스 분류"""
        macro_news = {key: [] for key in self.MACRO_KEYWORDS.keys()}

        for article in news_list:
            text = f"{article.title} {article.summary or ''}".lower()
            for key, keywords in self.MACRO_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    macro_news[key].append({
                        'title': article.title,
                        'summary': (article.summary or '')[:150]
                    })

        # 빈 카테고리 제거
        return {k: v for k, v in macro_news.items() if v}

    def _get_economic_events(self, db, date_str: str) -> List[Dict]:
        """오늘/내일 경제지표 조회"""
        try:
            today = datetime.strptime(date_str, "%Y-%m-%d")
            tomorrow = today + timedelta(days=1)
            day_after = today + timedelta(days=2)

            events = db.query(EconomicEvent).filter(
                EconomicEvent.event_time >= today,
                EconomicEvent.event_time < day_after,
                EconomicEvent.importance >= 2
            ).order_by(EconomicEvent.event_time).all()

            return [{
                'time': e.event_time.strftime("%m/%d %H:%M"),
                'name': e.event_name,
                'importance': "★" * e.importance,
                'forecast': e.forecast,
                'previous': e.previous,
                'actual': e.actual
            } for e in events]
        except Exception as e:
            logger.error(f"Error fetching economic events: {e}")
            return []

    async def _generate_briefing_with_gemini(
        self,
        date_str: str,
        mega_cap_news: List,
        large_cap_news: List,
        other_news: List,
        macro_news: Dict,
        economic_events: List,
        has_sufficient_data: bool,
        mode: BriefingMode = None
    ) -> str:
        """
        Gemini로 브리핑 생성 (v2.3 - 모드 기반)

        Args:
            mode: 브리핑 모드 (None이면 자동 감지)
        """
        # v2.3: 모드 자동 감지
        if mode is None:
            mode = get_current_briefing_mode()

        logger.info(f"📝 Briefing Mode: {mode.value}")
        mode_constraints = get_mode_constraints(mode)

        # 뉴스 데이터 포맷팅
        mega_cap_data = [{'title': n.title, 'summary': (n.summary or '')[:150]} for n in mega_cap_news[:10]]
        large_cap_data = [{'title': n.title, 'summary': (n.summary or '')[:150]} for n in large_cap_news[:10]]
        other_data = [{'title': n.title, 'summary': (n.summary or '')[:150]} for n in other_news]

        # 웹검색 지시 (데이터 부족 시)
        web_search_instruction = ""
        if not has_sufficient_data or not macro_news:
            web_search_instruction = """
            ⚠️ **중요**: 뉴스 데이터가 부족합니다. 다음 항목에 대해 최신 정보를 기반으로 분석해주세요:
            - S&P500 지수 및 나스닥 종가/등락률
            - 금(XAU), 은(XAG) 가격
            - 비트코인(BTC) 가격
            - 달러인덱스(DXY)
            - 원달러 환율(USD/KRW)
            - 미국 10년물 국채 금리
            - WTI 유가
            - VIX 지수

            최신 시장 데이터를 기반으로 정확한 수치와 함께 분석해주세요.
            """

        # v2.3: PromptBuilder를 사용하여 모드별 프롬프트 생성
        briefing_data = {
            "mega_cap_news": mega_cap_data if mega_cap_data else "데이터 없음 - 웹검색 필요",
            "large_cap_news": large_cap_data if large_cap_data else "데이터 없음",
            "macro_news": macro_news if macro_news else "데이터 없음 - 웹검색 필요",
            "economic_events": economic_events if economic_events else "오늘 주요 지표 없음",
            "other_news": other_data if other_data else "데이터 없음",
            "web_search_required": not has_sufficient_data or not macro_news,
            "formatted_events_table": self._format_economic_events_for_prompt(economic_events),
        }

        # 웹검색 지시 추가 (데이터 부족 시)
        if not has_sufficient_data or not macro_news:
            briefing_data["web_search_instruction"] = """
⚠️ **중요**: 뉴스 데이터가 부족합니다. 다음 항목에 대해 최신 정보를 기반으로 분석해주세요:
- S&P500 지수 및 나스닥 종가/등락률
- 금(XAU), 은(XAG) 가격
- 비트코인(BTC) 가격
- 달러인덱스(DXY)
- 원달러 환율(USD/KRW)
- 미국 10년물 국채 금리
- WTI 유가
- VIX 지수
"""

        # PromptBuilder로 모드별 프롬프트 생성
        prompt = PromptBuilder.build(mode, briefing_data, date_str)

        # v2.3: Gemini API 호출 및 출력 검증
        logger.info(f"📤 Sending prompt to Gemini ({self.model_name})...")
        raw_output = await call_gemini_api(prompt, self.model_name)

        # v2.3: 출력 검증 (모드 제약 조건 준수 여부)
        validation = validate_output_for_mode(raw_output, mode)
        if not validation["valid"]:
            logger.warning(f"⚠️ Output validation issues:")
            if validation["violations"]:
                logger.warning(f"  - Banned phrases used: {validation['violations']}")
            if validation["missing"]:
                logger.warning(f"  - Missing required phrases: {validation['missing']}")
            logger.warning(f"  - Compliance score: {validation['score']}/100")
        else:
            logger.info(f"✅ Output validation passed (score: {validation['score']}/100)")

        return raw_output

    def _format_economic_events_for_prompt(self, events: List[Dict]) -> str:
        """경제지표 이벤트 포맷팅"""
        if not events:
            return "| - | 오늘 주요 발표 예정 지표 없음 | - | - | - |"

        lines = []
        for e in events:
            lines.append(f"| {e['time']} | {e['name']} | {e['importance']} | {e.get('forecast', '-')} | {e.get('previous', '-')} |")
        return "\n".join(lines)


async def main():
    """테스트 - v2.3 모드 시스템"""
    import sys

    # 명령줄 인자로 모드 지정 가능
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else None
    mode = None

    if mode_arg:
        mode_map = {
            "closing": BriefingMode.CLOSING,
            "morning": BriefingMode.MORNING,
            "intraday": BriefingMode.INTRADAY,
            "korean": BriefingMode.KOREAN,
        }
        mode = mode_map.get(mode_arg.lower())
        if not mode:
            print(f"❌ Invalid mode: {mode_arg}")
            print(f"   Available modes: {', '.join(mode_map.keys())}")
            return

    reporter = USMarketCloseReporter()

    # 현재 모드 표시
    current_mode = mode or get_current_briefing_mode()
    print(f"\n📝 Briefing Mode: {current_mode.value}")
    print(f"   Mode constraints: {get_mode_constraints(current_mode)['name']}")

    filename = await reporter.generate_us_close_briefing(mode=mode)

    print(f"\n✅ 브리핑 생성 완료: {filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"브리핑 길이: {len(content)}자")
    print("\n" + "=" * 70)
    print("미리보기 (처음 2000자):")
    print("=" * 70)
    print(content[:2000])


if __name__ == "__main__":
    asyncio.run(main())
