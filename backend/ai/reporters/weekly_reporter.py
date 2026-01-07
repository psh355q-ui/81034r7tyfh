
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
        
        # 3. Save
        filename = f"docs/Weekly_Report_{date_str.replace('-','')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
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

if __name__ == "__main__":
    import asyncio
    reporter = WeeklyReporter()
    asyncio.run(reporter.generate_weekly_report())
