
"""
Report Orchestrator Agent
=========================
Aggregates data from various system components (Shadow Trading, News, Macro) 
and synthesizes a comprehensive Daily Briefing using LLM.

Role:
- Collector: Fetches latest stats from DB/Agents.
- Editor: Synthesizes disparate data into a coherent narrative.
- Publisher: Saves report to docs/ or database.
"""


import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession


from backend.ai.debate.news_agent import NewsAgent
from backend.ai.market_regime import MarketRegimeEnsemble # Placeholder if needed
from backend.ai.gemini_client import call_gemini_api
from backend.ai.portfolio.account_partitioning import AccountPartitionManager
from backend.core.database import DatabaseSession
from backend.notifications.telegram_notifier import create_telegram_notifier
from backend.database.models import (
    NewsInterpretation, 
    NewsArticle, 
    AnalysisResult, 
    TradingSignal, 
    DeepReasoningAnalysis,
    Order
)
from backend.reporting.report_templates import (
    DailyReport, 
    ExecutiveSummary, 
    TradingActivity, 
    PortfolioOverview,
    AIPerformance,
    RiskMetrics
)
from backend.reporting.pdf_renderer import render_daily_report_pdf
from decimal import Decimal

logger = logging.getLogger(__name__)

class ReportOrchestrator:
    def __init__(self):
        self.news_agent = NewsAgent()
        # partition_manager usually has async methods or sync methods. 
        # AccountPartitionManager seems to use Sync Repository generally, 
        # but check if we need to make it async compatible or wraps calls.
        # AccountPartitionManager in this codebase seems to handle its own DB sessions? 
        # Actually in phase 6 it was implemented. Assuming get_all_summaries is sync or async?
        # Checked earlier logs: AccountPartitionManager might trigger DB.
        self.partition_manager = AccountPartitionManager()
        self.model_name = "gemini-2.0-flash-exp"
        self.notifier = create_telegram_notifier()
        
    async def generate_daily_briefing(self, date_str: str = None, use_enhanced: bool = True) -> str:
        """
        Generates the Daily Briefing markdown report.

        Args:
            date_str: 날짜 (YYYY-MM-DD)
            use_enhanced: True면 개선된 버전 사용 (기본값)
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"📝 Generating Daily Briefing for {date_str}... (Enhanced={use_enhanced})")

        # 개선된 버전 사용
        if use_enhanced:
            try:
                from backend.ai.reporters.enhanced_daily_reporter import EnhancedDailyReporter
                enhanced_reporter = EnhancedDailyReporter()
                return await enhanced_reporter.generate_enhanced_briefing(date_str)
            except Exception as e:
                logger.error(f"Enhanced reporter failed, falling back to basic: {e}")
                # 실패 시 기본 버전으로 폴백
                use_enhanced = False

        # 기본 버전
        if not use_enhanced:
            async with DatabaseSession() as session:
                # 1. Collect Data
                # A. Shadow Trading Stats
                portfolio_summary = await self._get_portfolio_summary(session)

                # B. Critical News (The Watchtower)
                news_summary = await self._get_news_summary(session)

                # C. Deep Reasoning / Macro Insights
                deep_insights = await self._get_deep_insights(session)

                # 2. Synthesize via LLM
                report_content = await self._synthesize_report(date_str, portfolio_summary, news_summary, deep_insights)

                # 3. Save Markdown
                md_filename = f"docs/Daily_Briefing_{date_str.replace('-','')}.md"
                with open(md_filename, "w", encoding="utf-8") as f:
                    f.write(report_content)

                # 4. Generate PDF
                try:
                    pdf_bytes = self._create_pdf_report(date_str, portfolio_summary, report_content)
                    pdf_filename = f"docs/Daily_Briefing_{date_str.replace('-','')}.pdf"
                    with open(pdf_filename, "wb") as f:
                        f.write(pdf_bytes)
                    logger.info(f"✅ PDF Generated: {pdf_filename}")

                    # 5. Notify via Telegram (PDF)
                    if self.notifier:
                        await self.notifier.send_file(
                            pdf_filename,
                            caption=f"📢 **Daily Briefing** ({date_str})\n\nAttached is the daily AI trading report."
                        )

                    return pdf_filename
                except Exception as e:
                    logger.error(f"Failed to generate PDF: {e}")
                    # Fallback to sending MD if PDF fails
                    if self.notifier:
                        await self.notifier.send_file(
                            md_filename,
                            caption=f"📢 **Daily Briefing** ({date_str})\n\n(PDF Generation Failed, sending Markdown)"
                        )
                    return md_filename

    def _create_pdf_report(self, date_str: str, portfolio: Dict, narrative: str) -> bytes:
        """Create DailyReport object and render to PDF."""
        
        # Helper to safely get Decimal
        def d(val):
            return Decimal(str(val)) if val is not None else Decimal(0)
            
        exec_summary = ExecutiveSummary(
            portfolio_value=d(portfolio.get('total_value', 0)),
            daily_pnl=d(portfolio.get('daily_pnl', 0)),
            daily_return_pct=d(portfolio.get('daily_pnl_pct', 0)),
            total_return_pct=d(portfolio.get('total_return_pct', 0)),
            win_rate=d(portfolio.get('win_rate', 0)),
            sharpe_ratio=d(portfolio.get('sharpe_ratio', 0)),
            positions_count=portfolio.get('positions_count', 0),
            trades_count=portfolio.get('trades_today', 0),
            ai_cost_usd=Decimal("0.50"), # Mock
            highlights=["AI Market Analysis Completed", "Portfolio Rebalanced"], # Mock
        )
        
        port_overview = PortfolioOverview(
            total_value=d(portfolio.get('total_value', 0)),
            cash=d(portfolio.get('cash', 0)),
            invested_value=d(portfolio.get('total_value', 0) - portfolio.get('cash', 0)),
            positions_count=portfolio.get('positions_count', 0),
            sector_allocation={"Tech": 50.0, "Cash": 30.0, "Other": 20.0}, # Mock if not present
            strategy_allocation={"Core": 60.0, "Satellite": 40.0}
        )
        
        report = DailyReport(
            report_id=f"daily_{date_str}",
            report_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
            generated_at=datetime.now(),
            executive_summary=exec_summary,
            portfolio_overview=port_overview,
            narrative_analysis=narrative
        )
         
        return render_daily_report_pdf(report)


    async def _get_portfolio_summary(self, session: AsyncSession) -> Dict[str, Any]:
        """Fetch consolidated portfolio stats."""
        # AccountPartitionManager usually uses its own session management or needs one passing.
        # If AccountPartitionManager methods are sync, run them in executor to avoid blocking.
        # For now, assuming it's fast enough or safe.
        # Ideally: await asyncio.to_thread(self.partition_manager.get_all_summaries)
        try:
            # Running sync method in thread pool to prevent blocking
            summary = await asyncio.to_thread(self.partition_manager.get_all_summaries)
            return summary
        except Exception as e:
            logger.error(f"Failed to fetch portfolio summary: {e}")
            return {"error": str(e)}

    async def _get_news_summary(self, session: AsyncSession) -> List[Dict]:
        """Fetch top news from NewsInterpretation (War Room) or recent articles."""
        try:
            # 1. Fetch recent interpretations (War Room analysis)
            cutoff = datetime.now() - timedelta(hours=24)
            
            # Async Query
            stmt = (
                select(NewsInterpretation, NewsArticle)
                .join(NewsArticle, NewsInterpretation.news_article_id == NewsArticle.id)
                .where(NewsInterpretation.interpreted_at >= cutoff)
                .order_by(desc(NewsInterpretation.interpreted_at))
                .limit(10)
            )
            result = await session.execute(stmt)
            interpretations = result.all() # list of (NewsInterpretation, NewsArticle)
            
            summary_list = []
            for interp, article in interpretations:
                summary_list.append({
                    "title": article.title,
                    "sentiment": interp.headline_bias, # BULLISH/BEARISH
                    "impact": interp.expected_impact, # HIGH/MEDIUM
                    "reasoning": interp.reasoning[:200]
                })
                
            # If empty, fallback to raw news
            if not summary_list:
                stmt_news = (
                    select(NewsArticle)
                    .where(NewsArticle.published_date >= cutoff)
                    .order_by(desc(NewsArticle.published_date))
                    .limit(5)
                )
                result_news = await session.execute(stmt_news)
                recent_news = result_news.scalars().all()
                
                for article in recent_news:
                     summary_list.append({
                        "title": article.title,
                        "sentiment": getattr(article, 'sentiment_label', 'NEUTRAL'),
                        "summary": article.summary[:200] if article.summary else ""
                    })

            return summary_list
            
        except Exception as e:
            logger.error(f"Failed to fetch news summary: {e}")
            return []

    async def _get_deep_insights(self, session: AsyncSession) -> str:
        """Fetch Deep Reasoning analysis and Signals."""
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            
            # 1. Deep Reasoning Analysis (New Table)
            stmt = (
                select(DeepReasoningAnalysis)
                .where(DeepReasoningAnalysis.created_at >= cutoff)
                .order_by(desc(DeepReasoningAnalysis.created_at))
                .limit(5)
            )
            result_dr = await session.execute(stmt)
            analyses = result_dr.scalars().all()
            
            insights = []
            for a in analyses:
                beneficiary = f"Primary: {a.primary_beneficiary_ticker} ({a.primary_beneficiary_action})"
                if a.hidden_beneficiary_ticker:
                    beneficiary += f", Hidden: {a.hidden_beneficiary_ticker}"
                
                insights.append(
                    f"- [Theme: {a.theme}]\n"
                    f"  {beneficiary}\n"
                    f"  Bull Case: {a.bull_case[:150]}...\n"
                    f"  Bear Case: {a.bear_case[:150]}..."
                )
                
            # 2. Signals
            stmt_sig = (
                select(TradingSignal)
                .where(TradingSignal.created_at >= cutoff)
                .order_by(desc(TradingSignal.created_at))
                .limit(5)
            )
            result_sig = await session.execute(stmt_sig)
            signals = result_sig.scalars().all()
            
            signal_texts = []
            for s in signals:
                signal_texts.append(f"- {s.action} {s.ticker} ({s.signal_type}): {s.reasoning[:100]}...")
            
            if not insights and not signal_texts:
                return "No deep reasoning logic active in the last 24h."
                
            return "## Deep Reasoning Analysis:\n" + "\n".join(insights) + "\n\n## Generated Signals:\n" + "\n".join(signal_texts)
            
        except Exception as e:
            logger.error(f"Failed to fetch deep insights: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Error retrieving insights."

    async def _synthesize_report(self, date: str, portfolio: Dict, news: List, deep: str) -> str:
        """Use LLM to write the report."""
        
        prompt = f"""
        당신은 AI 트레이딩 시스템의 최고 투자 책임자(CIO)입니다. {date} 일일 브리핑을 작성하세요.
        
        [데이터 소스]
        1. 포트폴리오 현황:
           {json.dumps(portfolio, indent=2, ensure_ascii=False)}
           
        2. 주요 뉴스 및 AI 해석 (War Room):
           {json.dumps(news, indent=2, ensure_ascii=False)}
           
        3. 심층 분석 (Deep Reasoning):
           {deep}
        
        [작성 형식]
        # 📢 일일 AI 투자 브리핑 ({date})
        
        ## 1. 📊 시장 및 포트폴리오 요약
        - **총 자산**: $[금액] (변동폭)
        - **포트폴리오 상태**: [Core/Income/Satellite 비중 및 건전성 요약]
        - **시장 분위기**: [뉴스 기반 시장 전반적 분위기 요약]
        
        ## 2. 🌍 주요 이슈 및 분석 (War Room)
        - [뉴스 제목]
          - AI 해석: [감성/영향 요약]
          - [추가 뉴스...]
        
        ## 3. 🧠 심층 분석 인사이트 (Deep Reasoning)
        - [분석 내용 또는 "특이사항 없음"]
        - [생성된 시그널 요약]
        
        ## 4. 🚀 투자 전략 제언
        - [데이터 기반 향후 대응 전략 2-3줄, 한국어로 전문적이고 통찰력 있게 작성]
        
        작성 톤: 전문적이며 신뢰감 있는 어조. 핵심 위주로 명료하게.
        언어: 한국어 (Korean).
        """
        
        response = await call_gemini_api(prompt, self.model_name)
        return response

if __name__ == "__main__":
    # Test run
    orchestrator = ReportOrchestrator()
    asyncio.run(orchestrator.generate_daily_briefing())
