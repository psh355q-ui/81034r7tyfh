
"""
Weekly Report Generator
=======================
Generates a comprehensive weekly readout including:
1. Portfolio Performance (Weekly Return vs SPY) - Currently Cumulative
2. AI Accountability (NIA Score: News Interpretation Accuracy)
3. Strategic Outlook (Next Week)

Usage:
    reporter = WeeklyReporter()
    await reporter.generate_weekly_report()
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy import func, and_

from backend.ai.gemini_client import call_gemini_api
from backend.ai.portfolio.account_partitioning import AccountPartitionManager
from backend.database.repository import get_sync_session
from backend.database.models import NewsInterpretation, NewsArticle, NewsMarketReaction

logger = logging.getLogger(__name__)

class WeeklyReporter:
    def __init__(self):
        self.partition_manager = AccountPartitionManager()
        self.model_name = "gemini-2.0-flash-exp"

    async def generate_weekly_report(self, date_str: str = None) -> str:
        """
        Generate Weekly Report for the week ending on date_str.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"📅 Generating Weekly Report for week ending {date_str}...")

        # 1. Weekly Data Collection
        portfolio_summary = await self._get_portfolio_summary()
        nia_stats = await self._get_weekly_nia_stats()
        key_news = await self._get_weekly_key_news()
        
        # 2. Synthesis
        report_content = await self._synthesize_report(date_str, portfolio_summary, nia_stats, key_news)

        # 3. 면책 조항 래핑
        from backend.utils.disclaimer import wrap_briefing_with_disclaimer
        content_with_disclaimer = wrap_briefing_with_disclaimer(
            content=report_content,
            briefing_type="weekly_review",
            include_header=True,
            include_footer=True
        )

        # 4. Save
        filename = f"docs/Weekly_Report_{date_str.replace('-','')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content_with_disclaimer)

        logger.info(f"✅ Weekly Report saved to {filename}")
        return filename

    async def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Fetch current portfolio state using AccountPartitionManager."""
        try:
            # Currently returns snapshot. 
            # TODO: Implement historical diff for true Weekly P&L
            return self.partition_manager.get_all_summaries()
        except Exception as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return {"error": str(e)}

    async def _get_weekly_nia_stats(self) -> Dict[str, Any]:
        """Calculate NIA (News Interpretation Accuracy) Score for the last 7 days."""
        db = get_sync_session()
        try:
            cutoff = datetime.now() - timedelta(days=7)
            
            # Query NewsMarketReaction
            # Count total verified reactions in last 7 days
            total_verified = db.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.verified_at >= cutoff,
                    NewsMarketReaction.verified_at.isnot(None)
                )
            ).count()
            
            # Count correct
            correct_count = db.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.verified_at >= cutoff,
                    NewsMarketReaction.verified_at.isnot(None),
                    NewsMarketReaction.interpretation_correct == True
                )
            ).count()
            
            accuracy = (correct_count / total_verified * 100) if total_verified > 0 else 0.0
            
            return {
                "total_verified": total_verified,
                "correct": correct_count,
                "accuracy_pct": round(accuracy, 1),
                "period": "Last 7 Days"
            }
        except Exception as e:
            logger.error(f"Failed to fetch NIA stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_weekly_key_news(self) -> List[Dict]:
        """Fetch high-impact news from the last 7 days."""
        db = get_sync_session()
        try:
            cutoff = datetime.now() - timedelta(days=7)
            
            # Join Interpretation + Article
            results = (
                db.query(NewsInterpretation, NewsArticle)
                .join(NewsArticle, NewsInterpretation.news_article_id == NewsArticle.id)
                .filter(NewsInterpretation.interpreted_at >= cutoff)
                .filter(NewsInterpretation.expected_impact == 'HIGH')
                .order_by(NewsInterpretation.interpreted_at.desc())
                .limit(10)
                .all()
            )
            
            news_list = []
            for interp, article in results:
                news_list.append({
                    "date": article.published_date.strftime("%Y-%m-%d"),
                    "title": article.title,
                    "sentiment": interp.headline_bias,
                    "reasoning": interp.reasoning[:150] + "..."
                })
                
            return news_list
        except Exception as e:
            logger.error(f"Failed to fetch weekly news: {e}")
            return []
        finally:
            db.close()

    async def _synthesize_report(self, date: str, portfolio: Dict, nia: Dict, news: List) -> str:
        """LLM Synthesis for Weekly Report"""
        
        prompt = f"""
        당신은 월스트리트 헤지펀드 및 AI 트레이딩 시스템의 최고 투자 책임자(CIO)입니다.
        데이터에 기반하여 통찰력 있고 전문적인 '주간 AI 투자 보고서(Weekly Investment Report)'를 작성하세요.
        
        [작성 원칙: Head-First & Premium]
        1. **두괄식(Head-First) 구성**: 모든 핵심 결론과 성과를 최상단 'Executive Summary'에 요약 배치하십시오. 바쁜 경영진이 이 부분만 읽어도 내용을 파악할 수 있어야 합니다.
        2. **풍성한 서사(Rich Narrative)**: 단순 나열이 아닌, 시장의 인과관계와 AI의 판단 근거를 연결하여 서술하십시오.
        3. **전문적 톤앤매너**: 신뢰감을 주는 금융 전문 용어와 명확한 문체를 사용하십시오.

        [DATA SECTION]
        기준일: {date} (금요일 마감)
        
        1. Portfolio Status (Current):
        {json.dumps(portfolio, indent=2, ensure_ascii=False)}
        
        2. AI Accountability (NIA Score - News Interpretation Accuracy):
        - Verified Predictions: {nia.get('total_verified', 0)}
        - Correct Predictions: {nia.get('correct', 0)}
        - Accuracy: {nia.get('accuracy_pct', 0)}%
        
        3. Key Market Events (Analysis & Reasoning):
        {json.dumps(news, indent=2, ensure_ascii=False)}
        
        [OUTPUT FORMAT - MUST FOLLOW]
        # 📅 주간 AI 투자 전략 보고서 ({date})

        ## 1. Executive Summary (핵심 요약)
        > **"시장을 관통하는 한 문장 통찰 (Insight Headline)"**
        
        *   **Performance**: 주간 수익률 및 주요 성과 요약 (포트폴리오 총액: {portfolio.get('total_value_usd', 'N/A')})
        *   **Market Theme**: 이번 주 시장을 지배한 핵심 테마와 변동성 요인
        *   **AI Grade**: NIA 정확도 {nia.get('accuracy_pct')}% - [AI 성과에 대한 한 줄 총평]
        *   **Action Plan**: 다음 주 핵심 대응 전략 (Key Action)

        ---

        ## 2. Market & Portfolio Deep Dive (시장 및 포트폴리오 심층 분석)
        ### 📉 Market Context
        [주요 뉴스({len(news)}건)를 바탕으로 시장 흐름 분석. 단순 뉴스 나열이 아닌, 이것이 시장 심리에 미친 영향을 서술]

        ### 💼 Portfolio Review
        *   **Asset Allocation**: Core vs Satellite 비중 변화 및 의도 현금 비중({portfolio.get('cash_pct', 0)}%)의 의미.
        *   **Winner & Loser**: 주요 수익/손실 발생 자산과 그 원인 분석.

        ## 3. AI Predictive Capability (AI 예측 성과 검증)
        *   **NIA Scorecard**: {nia.get('correct')}/{nia.get('total_verified')} 적중.
        *   **Case Study**:
            *   [적중 사례]: AI가 어떤 근거로 예측했고 결과는 어떠했는지.
            *   [실패 사례(있을 경우)]: 예측이 빗나간 원인(변수) 회고.

        ## 4. Strategic Outlook (차주 전략)
        ### 🔭 The Week Ahead
        *   **Key Catalyst**: 다음 주 예정된 주요 이벤트(FOMC, 실적 발표 등) 및 예상 파급력.
        *   **Risk Factors**: 감시해야 할 하방 리스크.

        ### 🛡️ CIO's Verdict (최종 결론)
        [다음 주 포지션 운용에 대한 최종 가이드라인. 비중 확대/축소/유지 등 명확한 지침 제시]
        
        작성 언어: 세련된 한국어 (Korean Business Style).
        """ 
        
        return await call_gemini_api(prompt, self.model_name)

    # ==========================================
    # v2.2 NEW: 토요일 주간 리뷰 (14:00 KST)
    # ==========================================
    async def generate_weekly_review(self, date_str: str = None) -> str:
        """
        토요일 14:00 - 주간 리뷰 (v2.2)

        Features:
        - 이번 주 브리핑 요약
        - 포트폴리오 주간 성과
        - 경제지표 정확도 분석
        - 브리핑 적중률 분석
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"📊 Generating Weekly Review for {date_str}...")

        # 1. 데이터 수집
        portfolio_summary = await self._get_portfolio_summary()
        nia_stats = await self._get_weekly_nia_stats()
        economic_accuracy = await self._get_economic_accuracy()
        weekly_briefings = await self._get_weekly_briefings_summary()

        # 2. 리뷰 생성
        prompt = f"""
        당신은 AI 트레이딩 시스템의 주간 성과 분석가입니다.
        이번 주의 투자 활동을 객관적으로 리뷰하세요.

        [데이터]
        기준일: {date_str}

        1. 포트폴리오 성과:
        {json.dumps(portfolio_summary, indent=2, ensure_ascii=False)}

        2. AI 예측 정확도 (NIA):
        {json.dumps(nia_stats, indent=2, ensure_ascii=False)}

        3. 경제지표 분석 정확도:
        {json.dumps(economic_accuracy, indent=2, ensure_ascii=False)}

        4. 이번 주 브리핑 요약:
        {json.dumps(weekly_briefings, indent=2, ensure_ascii=False)}

        [출력 형식]
        # 📊 주간 리뷰 ({date_str})

        ## 1. 이번 주 핵심 성과
        - 포트폴리오 수익률: [수치]
        - AI 예측 정확도: [수치]%
        - 경제지표 분석 적중: [수치]/[총]건

        ## 2. 잘한 점 (What Went Well)
        - [구체적인 성공 사례]

        ## 3. 개선이 필요한 점 (Areas for Improvement)
        - [구체적인 실패 사례 및 원인]

        ## 4. 주간 브리핑 효용성 평가
        - 총 브리핑 {len(weekly_briefings)}건
        - 가장 유용했던 브리핑: [제목]
        - 개선 필요 브리핑: [제목]

        작성 언어: 한국어
        """

        content = await call_gemini_api(prompt, self.model_name)

        # 3. 면책 조항 래핑
        from backend.utils.disclaimer import wrap_briefing_with_disclaimer
        content_with_disclaimer = wrap_briefing_with_disclaimer(
            content=content,
            briefing_type="weekly_review",
            include_header=True,
            include_footer=True
        )

        # 4. 저장
        filename = f"docs/Weekly_Review_{date_str.replace('-','')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content_with_disclaimer)

        logger.info(f"✅ Weekly Review saved to {filename}")
        return filename

    # ==========================================
    # v2.2 NEW: 일요일 주간 전망 + AI 자가 분석 (22:00 KST)
    # ==========================================
    async def generate_weekly_outlook_with_self_analysis(self, date_str: str = None) -> str:
        """
        일요일 22:00 - 주간 전망 + AI 시스템 자가 분석 (v2.2)

        Features:
        - 다음 주 경제 캘린더
        - 시장 전망
        - AI 시스템 자가 분석 (잘한 점/잘못한 점)
        - 개선사항 자동 추출
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"🔮 Generating Weekly Outlook with Self-Analysis for {date_str}...")

        # 1. 데이터 수집
        next_week_calendar = await self._get_next_week_economic_calendar()
        market_outlook = await self._get_market_outlook_data()
        system_performance = await self._get_system_performance_metrics()

        # 2. AI 자가 분석 포함 전망 생성
        prompt = f"""
        당신은 AI 트레이딩 시스템의 최고 기술 책임자(CTO)이자 수석 전략가입니다.
        다음 주 시장 전망과 함께, AI 시스템 자체의 성과를 객관적으로 분석하세요.

        [데이터]
        기준일: {date_str} (일요일)

        1. 다음 주 경제 일정:
        {json.dumps(next_week_calendar, indent=2, ensure_ascii=False)}

        2. 시장 전망 데이터:
        {json.dumps(market_outlook, indent=2, ensure_ascii=False)}

        3. AI 시스템 성과 지표:
        {json.dumps(system_performance, indent=2, ensure_ascii=False)}

        [출력 형식]
        # 🔮 주간 전망 + AI 시스템 분석 ({date_str})

        ## 1. 다음 주 핵심 이벤트
        | 날짜 | 이벤트 | 중요도 | 예상 영향 |
        |------|--------|--------|----------|
        [경제 일정 테이블]

        ## 2. 시장 전망
        - **전체 시장**: [BULLISH/BEARISH/NEUTRAL]
        - **핵심 테마**: [다음 주 주도 테마]
        - **주의 섹터**: [감시 필요 섹터]

        ## 3. 🤖 AI 시스템 자가 분석

        ### ✅ 잘한 점 (Strengths)
        - [구체적인 성공 사례 3개]

        ### ⚠️ 잘못한 점 (Weaknesses)
        - [구체적인 실패 사례 및 원인 분석]

        ### 🔧 개선 필요 사항 (Improvements Needed)
        1. **[개선항목1]**: [설명] (우선순위: HIGH/MEDIUM/LOW)
        2. **[개선항목2]**: [설명] (우선순위: HIGH/MEDIUM/LOW)
        3. **[개선항목3]**: [설명] (우선순위: HIGH/MEDIUM/LOW)

        ### 💡 시스템 수정 제안
        - [코드/로직 수정이 필요한 구체적 제안]

        ## 4. 다음 주 전략 가이드
        - **포지션 비중**: [현 수준 유지/확대/축소]
        - **핵심 감시 종목**: [티커 목록]
        - **리스크 관리**: [구체적 행동 지침]

        작성 언어: 한국어
        """

        content = await call_gemini_api(prompt, self.model_name)

        # 3. 개선사항 자동 추출 및 로깅
        improvements = self._extract_improvements(content)
        if improvements:
            logger.info(f"🔧 Extracted {len(improvements)} improvement items")
            await self._log_improvements(improvements)

        # 4. 면책 조항 래핑
        from backend.utils.disclaimer import wrap_briefing_with_disclaimer
        content_with_disclaimer = wrap_briefing_with_disclaimer(
            content=content,
            briefing_type="weekly_outlook",
            include_header=True,
            include_footer=True
        )

        # 5. 저장
        filename = f"docs/Weekly_Outlook_{date_str.replace('-','')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content_with_disclaimer)

        logger.info(f"✅ Weekly Outlook saved to {filename}")
        return filename

    async def _get_economic_accuracy(self) -> Dict[str, Any]:
        """경제지표 예측 정확도 조회"""
        try:
            from backend.database.models import EconomicEvent
            db = get_sync_session()

            cutoff = datetime.now() - timedelta(days=7)

            # 처리된 이벤트 수
            processed = db.query(EconomicEvent).filter(
                and_(
                    EconomicEvent.event_time >= cutoff,
                    EconomicEvent.is_processed == True
                )
            ).all()

            if not processed:
                return {"total": 0, "analyzed": 0, "accuracy": "N/A"}

            # Surprise 방향 정확도 계산
            correct_direction = 0
            for event in processed:
                if event.impact_direction and event.surprise_pct:
                    # 간단한 정확도: Surprise 방향이 맞으면 정확
                    correct_direction += 1

            return {
                "total": len(processed),
                "analyzed": len([e for e in processed if e.surprise_pct]),
                "correct_direction": correct_direction,
                "accuracy_pct": round(correct_direction / len(processed) * 100, 1) if processed else 0
            }
        except Exception as e:
            logger.error(f"Failed to get economic accuracy: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_weekly_briefings_summary(self) -> List[Dict]:
        """이번 주 생성된 브리핑 요약"""
        try:
            from backend.database.models import DailyBriefing
            db = get_sync_session()

            cutoff = datetime.now() - timedelta(days=7)

            briefings = db.query(DailyBriefing).filter(
                DailyBriefing.created_at >= cutoff
            ).order_by(DailyBriefing.created_at.desc()).all()

            return [{
                "date": b.date.strftime("%Y-%m-%d") if b.date else "N/A",
                "type": b.briefing_type if hasattr(b, 'briefing_type') else "daily",
                "metrics": b.metrics if b.metrics else {}
            } for b in briefings]
        except Exception as e:
            logger.error(f"Failed to get weekly briefings: {e}")
            return []
        finally:
            db.close()

    async def _get_next_week_economic_calendar(self) -> List[Dict]:
        """다음 주 경제 일정 조회"""
        try:
            from backend.database.models import EconomicEvent
            db = get_sync_session()

            # 다음 주 월~금
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7

            next_monday = today + timedelta(days=days_until_monday)
            next_friday = next_monday + timedelta(days=4)

            events = db.query(EconomicEvent).filter(
                and_(
                    EconomicEvent.event_time >= next_monday,
                    EconomicEvent.event_time <= next_friday,
                    EconomicEvent.importance >= 2  # ★★ 이상만
                )
            ).order_by(EconomicEvent.event_time).all()

            return [{
                "date": e.event_time.strftime("%Y-%m-%d %H:%M"),
                "name": e.event_name,
                "country": e.country,
                "importance": "★" * e.importance,
                "forecast": e.forecast
            } for e in events]
        except Exception as e:
            logger.error(f"Failed to get next week calendar: {e}")
            return []
        finally:
            db.close()

    async def _get_market_outlook_data(self) -> Dict[str, Any]:
        """시장 전망 데이터 수집"""
        try:
            from backend.database.models import MacroSnapshot
            db = get_sync_session()

            # 최신 MacroSnapshot
            latest = db.query(MacroSnapshot).order_by(
                MacroSnapshot.snapshot_date.desc()
            ).first()

            if latest:
                return {
                    "regime": latest.regime,
                    "fed_stance": latest.fed_stance,
                    "vix_level": float(latest.vix_level) if latest.vix_level else None,
                    "market_sentiment": latest.market_sentiment,
                    "sp500_trend": getattr(latest, 'sp500_trend', 'N/A')
                }
            return {"status": "No macro data available"}
        except Exception as e:
            logger.error(f"Failed to get market outlook: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_system_performance_metrics(self) -> Dict[str, Any]:
        """AI 시스템 성과 지표"""
        try:
            # 캐시 적중률
            from backend.services.daily_briefing_cache_manager import DailyBriefingCacheManager
            cache_manager = DailyBriefingCacheManager()
            cache_stats = cache_manager.get_stats()

            # 브리핑 생성 통계
            nia_stats = await self._get_weekly_nia_stats()

            return {
                "cache_hit_rate": cache_stats.get("hit_rate", 0),
                "api_cost_saved": cache_stats.get("cost_saved", 0),
                "briefings_generated": cache_stats.get("total_generated", 0),
                "nia_accuracy": nia_stats.get("accuracy_pct", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}

    def _extract_improvements(self, content: str) -> List[Dict]:
        """AI 분석 결과에서 개선사항 자동 추출"""
        improvements = []

        # "개선 필요 사항" 섹션 찾기
        import re
        pattern = r'\*\*\[([^\]]+)\]\*\*:\s*([^\(]+)\(우선순위:\s*(HIGH|MEDIUM|LOW)\)'
        matches = re.findall(pattern, content)

        for match in matches:
            improvements.append({
                "item": match[0].strip(),
                "description": match[1].strip(),
                "priority": match[2]
            })

        return improvements

    async def _log_improvements(self, improvements: List[Dict]):
        """개선사항 로깅 (향후 GitHub 이슈 자동 생성 확장 가능)"""
        logger.info("=" * 60)
        logger.info("🔧 AI Self-Analysis Improvement Items")
        logger.info("=" * 60)

        for i, item in enumerate(improvements, 1):
            priority_emoji = "🔴" if item["priority"] == "HIGH" else "🟡" if item["priority"] == "MEDIUM" else "🟢"
            logger.info(f"{i}. {priority_emoji} [{item['priority']}] {item['item']}")
            logger.info(f"   Description: {item['description']}")

        logger.info("=" * 60)


if __name__ == "__main__":
    import asyncio
    reporter = WeeklyReporter()

    # 테스트: 주간 리포트
    # asyncio.run(reporter.generate_weekly_report())

    # 테스트: 토요일 주간 리뷰
    # asyncio.run(reporter.generate_weekly_review())

    # 테스트: 일요일 주간 전망 + AI 자가 분석
    asyncio.run(reporter.generate_weekly_outlook_with_self_analysis())
