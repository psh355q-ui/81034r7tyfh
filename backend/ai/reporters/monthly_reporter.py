
"""
Monthly Report Generator
=======================
Generates a comprehensive monthly readout including:
1. Portfolio Performance (Monthly Return vs Benchmarks)
2. AI Accountability (Monthly NIA Score)
3. Strategic Review (Month-over-Month changes)
4. Forward Outlook (Next Month)

Usage:
    reporter = MonthlyReporter()
    await reporter.generate_monthly_report()
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

class MonthlyReporter:
    def __init__(self):
        self.partition_manager = AccountPartitionManager()
        self.model_name = "gemini-2.0-flash-exp"

    async def generate_monthly_report(self, year: int = None, month: int = None) -> str:
        """
        Generate Monthly Report for the specified year/month.
        Defaults to current month if not specified.
        """
        now = datetime.now()
        if not year: year = now.year
        if not month: month = now.month
        
        # Calculate target period
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
            
        start_date = datetime(year, month, 1)
        end_date = next_month - timedelta(days=1)
        
        date_str = end_date.strftime("%Y-%m-%d") # Report date is end of month
        
        logger.info(f"📅 Generating Monthly Report for {year}-{month}...")

        # 1. Monthly Data Collection
        portfolio_summary = await self._get_portfolio_summary()
        nia_stats = await self._get_monthly_nia_stats(start_date, next_month)
        key_news = await self._get_monthly_key_news(start_date, next_month)
        
        # 2. Synthesis
        report_content = await self._synthesize_report(year, month, portfolio_summary, nia_stats, key_news)
        
        # 3. Save
        filename = f"docs/Monthly_Report_{year}_{month:02d}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info(f"✅ Monthly Report saved to {filename}")
        return filename

    async def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Fetch current portfolio state."""
        # TODO: Implement historical snapshot retrieval to get start-of-month value for accurate Monthly PnL
        try:
            return self.partition_manager.get_all_summaries()
        except Exception as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return {"error": str(e)}

    async def _get_monthly_nia_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate NIA Score for the month."""
        db = get_sync_session()
        try:
            # Count total verified reactions in the month
            total_verified = db.query(NewsMarketReaction).filter(
                and_(
                    NewsMarketReaction.verified_at >= start_date,
                    NewsMarketReaction.verified_at < end_date,
                    NewsMarketReaction.verified_at.isnot(None)
                )
            ).count()
            
            # Count correct
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
                "period": f"{start_date.strftime('%Y-%m')}"
            }
        except Exception as e:
            logger.error(f"Failed to fetch NIA stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def _get_monthly_key_news(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch high-impact news for the month."""
        db = get_sync_session()
        try:
            # Join Interpretation + Article
            results = (
                db.query(NewsInterpretation, NewsArticle)
                .join(NewsArticle, NewsInterpretation.news_article_id == NewsArticle.id)
                .filter(and_(
                    NewsInterpretation.interpreted_at >= start_date,
                    NewsInterpretation.interpreted_at < end_date
                ))
                .filter(NewsInterpretation.expected_impact == 'HIGH')
                .order_by(NewsInterpretation.interpreted_at.desc())
                .limit(15) # Slightly more for monthly
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
            logger.error(f"Failed to fetch monthly news: {e}")
            return []
        finally:
            db.close()

    async def _synthesize_report(self, year: int, month: int, portfolio: Dict, nia: Dict, news: List) -> str:
        """LLM Synthesis for Monthly Report"""
        
        prompt = f"""
        당신은 글로벌 매크로 헤지펀드의 수석 전략가(Chief Strategist)이자 AI 시스템 리더입니다.
        데이터를 바탕으로 깊이 있는 '월간 AI 투자 보고서(Monthly Investment Report)'를 작성하세요.

        [작성 원칙: Head-First & Insight-Driven]
        1. **경영진 브리핑 스타일**: 핵심 결론(Executive Summary)을 최상단에 배치하여, 30초 내에 이 달의 성과와 흐름을 파악할 수 있게 하십시오.
        2. **서사적 분석(Narrative Analysis)**: 단순히 수치를 나열하지 말고, 거시경제-시장심리-AI매매의 인과관계를 스토리텔링하십시오.
        3. **명확한 전망**: 다음 달 시장에 대한 뷰(View)를 모호하지 않게 제시하십시오.

        [DATA SECTION]
        대상 기간: {year}년 {month}월
        
        1. Portfolio Status (End of Month):
        {json.dumps(portfolio, indent=2, ensure_ascii=False)}
        
        2. AI Accountability (NIA Score - News Interpretation Accuracy):
        - Verified Predictions: {nia.get('total_verified', 0)}
        - Correct Predictions: {nia.get('correct', 0)}
        - Accuracy: {nia.get('accuracy_pct', 0)}%
        
        3. Key Market Events (Monthly Highlights):
        {json.dumps(news, indent=2, ensure_ascii=False)}
        
        [OUTPUT FORMAT - MUST FOLLOW]
        # 📅 {year}년 {month}월 월간 투자 운용 보고서
        
        ## 1. Executive Summary (핵심 요약)
        > **"이달의 핵심 내러티브 (Key Narrative)"**
        
        *   **Monthly Performance**: 월간 수익률 [X]% (누적 운용액: {portfolio.get('total_value_usd', 'N/A')})
        *   **Macro Theme**: 이번 달 시장을 지배한 거시경제 테마 (인플레이션, 금리, 전쟁 등)
        *   **AI Reliability (NIA)**: {nia.get('accuracy_pct')}% 적중률 ({nia.get('correct')}/{nia.get('total_verified')})
            *   [AI 성과에 대한 CIO 코멘트]
        *   **Next Month Outlook**: {month+1}월 시장 전망 (Bullish / Bearish / Neutral)

        ---

        ## 2. 📊 Asset Allocation & Review (자산 배분 및 성과 분석)
        ### Strategy Implementation
        *   **Core / Satellite Operation**: 핵심 자산(Core)과 위성 자산(Satellite)의 운용 성과 비교.
        *   **Risk Management**: 현금 비중 조절 및 리스크 대응의 적절성 평가.
        
        ### Deal Review
        *   **Winning Trade**: (데이터 기반) 가장 성공적이었던 판단.
        *   **Missed Opportunity**: (데이터 기반) 놓친 기회나 아쉬운 판단 복기.

        ## 3. 🧠 Deep Reasoning & Market Insight (시장 심층 분석)
        [제공된 뉴스 데이터를 종합하여 AI가 분석한 시장의 이면. 단순 사실 나열 금지.]
        *   **Market Driver**: 무엇이 가격을 움직였는가?
        *   **Sentiment Shift**: 투자자 심리는 어떻게 변했는가?

        ## 4. 🔭 Strategic Outlook for Next Month ({month+1}월 전략)
        ### Macro Scenarios
        *   **Scenario A (Base Case)**: 가장 유력한 시장 시나리오.
        *   **Scenario B (Risk Case)**: 대비해야 할 리스크 시나리오.

        ### Investment Guide
        *   **Actionable Advice**: 비중을 늘려야 할 섹터 vs 줄여야 할 섹터.
        *   **Closing Remark**: 투자자들에게 전하는 이번 달의 마지막 조언.

        작성 톤: 전문적이고 통찰력 있는 기관 투자자 보고서 스타일.
        언어: 한국어 (Korean Business Style).
        """
        
        return await call_gemini_api(prompt, self.model_name)

if __name__ == "__main__":
    import asyncio
    reporter = MonthlyReporter()
    asyncio.run(reporter.generate_monthly_report())
