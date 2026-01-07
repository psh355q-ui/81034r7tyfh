
"""
Quarterly Report Generator
=========================
Generates a comprehensive quarterly readout including:
1. Portfolio Performance (Quarterly Return)
2. AI Accountability (Quarterly NIA Score)
3. Macro-Economic Review (Quarterly Highlights)
4. Strategic Outlook (Next Quarter)

Usage:
    reporter = QuarterlyReporter()
    await reporter.generate_quarterly_report()
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

class QuarterlyReporter:
    def __init__(self):
        self.partition_manager = AccountPartitionManager()
        self.model_name = "gemini-2.0-flash-exp"

    async def generate_quarterly_report(self, year: int = None, quarter: int = None) -> str:
        """
        Generate Quarterly Report for the specified year/quarter.
        Defaults to current quarter-end if not specified.
        """
        now = datetime.now()
        if not year: year = now.year
        if not quarter:
            # Determine current/last quarter based on current month
            # If jan, last quarter is prev year Q4
            if now.month <= 3: 
                quarter = 1 
            elif now.month <= 6:
                quarter = 2
            elif now.month <= 9:
                quarter = 3
            else:
                quarter = 4
        
        # Calculate dates
        if quarter == 1:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 3, 31)
        elif quarter == 2:
            start_date = datetime(year, 4, 1)
            end_date = datetime(year, 6, 30)
        elif quarter == 3:
            start_date = datetime(year, 7, 1)
            end_date = datetime(year, 9, 30)
        else: # Q4
            start_date = datetime(year, 10, 1)
            end_date = datetime(year, 12, 31)
            
        date_str = end_date.strftime("%Y-%m-%d") # Report date is end of quarter
        
        logger.info(f"📅 Generating Quarterly Report for {year}-Q{quarter}...")

        # 1. Quarterly Data Collection
        portfolio_summary = await self._get_portfolio_summary()
        nia_stats = await self._get_period_nia_stats(start_date, end_date + timedelta(days=1))
        key_news = await self._get_period_key_news(start_date, end_date + timedelta(days=1))
        
        # 2. Synthesis
        report_content = await self._synthesize_report(year, quarter, portfolio_summary, nia_stats, key_news)
        
        # 3. Save
        filename = f"docs/Quarterly_Report_{year}_Q{quarter}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info(f"✅ Quarterly Report saved to {filename}")
        return filename

    async def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Fetch current portfolio state."""
        try:
            return self.partition_manager.get_all_summaries()
        except Exception as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return {"error": str(e)}

    async def _get_period_nia_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate NIA Score for the period."""
        db = get_sync_session()
        try:
            total_verified = db.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.verified_at >= start_date,
                    NewsMarketReaction.verified_at < end_date,
                    NewsMarketReaction.verified_at.isnot(None)
                )
            ).count()
            
            correct_count = db.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.verified_at >= start_date,
                    NewsMarketReaction.verified_at < end_date,
                    NewsMarketReaction.verified_at.isnot(None),
                    NewsMarketReaction.interpretation_correct == True
                )
            ).count()
            
            accuracy = (correct_count / total_verified * 100) if total_verified > 0 else 0.0
            
            return {
                "total_verified": total_verified,
                "correct": correct_count,
                "accuracy_pct": round(accuracy, 1),
                "period": f"{start_date.strftime('%Y-%m')} ~ {end_date.strftime('%Y-%m')}"
            }
        except Exception as e:
            logger.error(f"Failed to fetch NIA stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_period_key_news(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch high-impact news for the period."""
        db = get_sync_session()
        try:
            results = (
                db.query(NewsInterpretation, NewsArticle)
                .join(NewsArticle, NewsInterpretation.news_article_id == NewsArticle.id)
                .filter(and_(
                    NewsInterpretation.interpreted_at >= start_date,
                    NewsInterpretation.interpreted_at < end_date
                ))
                .filter(NewsInterpretation.expected_impact == 'HIGH')
                .order_by(NewsInterpretation.interpreted_at.desc())
                .limit(20) # Top 20 for quarter
                .all()
            )
            
            news_list = []
            for interp, article in results:
                news_list.append({
                    "date": article.published_date.strftime("%Y-%m-%d"),
                    "title": article.title,
                    "sentiment": interp.headline_bias,
                    "reasoning": interp.reasoning[:200] + "..."
                })
                
            return news_list
        except Exception as e:
            logger.error(f"Failed to fetch period news: {e}")
            return []
        finally:
            db.close()

    async def _synthesize_report(self, year: int, quarter: int, portfolio: Dict, nia: Dict, news: List) -> str:
        """LLM Synthesis for Quarterly Report"""
        
        prompt = f"""
        당신은 AI 트레이딩 시스템의 최고 투자 책임자(CIO)입니다.
        데이터를 바탕으로 통찰력 있는 '분기 투자 운용 보고서(Quarterly Investment Report)'를 작성하세요.

        [작성 원칙: 3.0 Pro Insights]
        1. **Executive Impact**: 핵심 결론을 최상단에 배치하여 경영진이 1분 내에 분기 성과와 향후 방향성을 파악하게 하십시오.
        2. **Deep Reasoning Integration**: AI가 뉴스를 어떻게 해석하고 투자에 반영했는지 구체적인 사례(성공/실패)와 함께 기술하십시오.
        3. **Forward Looking**: 과거 회고는 30%, 미래 전망과 대응 전략에 70%의 비중을 두십시오.

        [DATA SECTION]
        대상 기간: {year}년 {quarter}분기 (Q{quarter})
        
        1. Portfolio Status (End of Quarter):
        {json.dumps(portfolio, indent=2, ensure_ascii=False)}
        
        2. AI Accountability (NIA Score - Quarterly Prediction Accuracy):
        - Verified Predictions: {nia.get('total_verified', 0)}
        - Correct Predictions: {nia.get('correct', 0)}
        - Accuracy: {nia.get('accuracy_pct', 0)}%
        
        3. Key Market Events (Quarterly Highlights):
        {json.dumps(news, indent=2, ensure_ascii=False)}
        
        [OUTPUT FORMAT - MUST FOLLOW]
        # 📊 {year}년 {quarter}분기(Q{quarter}) AI 투자 운용 보고서
        
        ## 1. Executive Summary (핵심 요약)
        > **"분기를 관통하는 핵심 전략 테마 (Strategic Theme)"**

        *   **Quarterly Performance**: 분기 수익률 및 운용 성과 (Total AUM: {portfolio.get('total_value_usd', 'N/A')})
        *   **Macro Environment**: 이번 분기 시장을 규정한 핵심 변수 (금리, 성장, 물가 등)
        *   **AI Reliability (NIA)**: {nia.get('accuracy_pct')}% 적중률 - [AI 모델의 성과 총평]
        *   **Next Quarter Strategy**: 다음 분기 핵심 운용 기조 (Aggressive / Defensive)

        ---

        ## 2. 🏛️ Portfolio & Performance Review (포트폴리오 성과 분석)
        ### Structure & Allocation
        *   **Portfolio Balance**: Core / Income / Satellite 비중의 적절성 평가.
        *   **Pivot Points**: 분기 중 있었던 주요 리밸런싱 혹은 포지션 변경의 근거와 결과.

        ### Winners & Losers
        *   **Top Contributors**: 수익 기여도가 높았던 종목/섹터.
        *   **Lessons Learned**: 손실이 발생했거나 미진했던 부분에 대한 회고.

        ## 3. 🧠 Deep Reasoning AI Review
        *   **Best Prediction**: AI가 정확히 예측한 지정학적/거시경제 이벤트.
        *   **Missed Signal**: 시장의 노이즈로 분류했으나 실제로는 중요했던 이벤트 혹은 그 반대.
        
        ## 4. 🔭 Strategic Outlook for Q{quarter+1 if quarter < 4 else 1} (향후 전망)
        ### Scenario Planning
        *   **Bull Case (긍정 시나리오)**: 시장 상승을 견인할 요소.
        *   **Bear Case (부정 시나리오)**: 주의해야 할 하방 리스크.
        
        ### Investment Roadmap
        *   **Sector Pick**: 다음 분기 매력적인 섹터.
        *   **CIO's Directive**: 구체적인 비중 조절 및 매매 지침.

        작성 톤: 글로벌 탑티어 헤지펀드 CIO의 깊이 있는 분석 보고서 스타일.
        언어: 한국어 (Korean Business Style).
        """
        
        return await call_gemini_api(prompt, self.model_name)

if __name__ == "__main__":
    import asyncio
    reporter = QuarterlyReporter()
    asyncio.run(reporter.generate_quarterly_report())
