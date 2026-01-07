
"""
Annual Report Generator
=======================
Generates a comprehensive annual review (Year-in-Review) including:
1. Investment Journey (Timeline of Major Decisions)
2. System Evolution (Upgrades & Milestones)
3. Performance Analysis (Annual Return) - Simulated for MVP
4. Next Year Outlook

Usage:
    reporter = AnnualReporter()
    await reporter.generate_annual_report(year=2026)
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import extract

from backend.ai.gemini_client import call_gemini_api
from backend.ai.portfolio.account_partitioning import AccountPartitionManager
from backend.database.repository import get_sync_session
from backend.database.models import TradingSignal, AnalysisResult

logger = logging.getLogger(__name__)

class AnnualReporter:
    def __init__(self):
        self.partition_manager = AccountPartitionManager()
        self.model_name = "gemini-2.0-flash-exp"

    async def generate_annual_report(self, year: int = None) -> str:
        """
        Generate Annual Report for the specified year.
        """
        if not year:
            year = datetime.now().year
        
        logger.info(f"📅 Generating Annual Report for {year}...")

        # 1. Collect Data
        portfolio_summary = await self._get_annual_performance()
        journey_timeline = await self._get_investment_journey(year)
        milestones = self._get_system_milestones(year)
        
        # 2. Synthesis
        report_content = await self._synthesize_report(year, portfolio_summary, journey_timeline, milestones)
        
        # 3. Save
        filename = f"docs/Annual_Report_{year}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info(f"✅ Annual Report saved to {filename}")
        return filename

    async def _get_annual_performance(self) -> Dict[str, Any]:
        """Fetch portfolio performance (Current snapshot as proxy for YTD)."""
        try:
            return self.partition_manager.get_all_summaries()
        except Exception as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return {"error": str(e)}

    async def _get_investment_journey(self, year: int) -> List[Dict]:
        """Reconstruct the investment journey from TradingSignals."""
        db = get_sync_session()
        try:
            # Query major signals (High Confidence)
            signals = (
                db.query(TradingSignal)
                .filter(extract('year', TradingSignal.created_at) == year)
                .filter(TradingSignal.confidence >= 80) # Only high conviction
                .order_by(TradingSignal.created_at.asc())
                .limit(20) # Top 20 moments
                .all()
            )
            
            timeline = []
            for s in signals:
                timeline.append({
                    "date": s.created_at.strftime("%Y-%m-%d"),
                    "ticker": s.ticker,
                    "action": s.action,
                    "type": s.signal_type,
                    "reasoning": s.reasoning[:100] + "..."
                })
                
            return timeline
        except Exception as e:
            logger.error(f"Failed to fetch journey: {e}")
            return []
        finally:
            db.close()

    def _get_system_milestones(self, year: int) -> List[str]:
        """Return hardcoded system milestones for the year."""
        # In a real system, this could come from a Changelog DB or Release Tags
        # For 2026 (Projected/Current), we list what we have achieved.
        if year == 2026:
            return [
                "1월: AI Trading System MVP Launch",
                "1월: Shadow Trading 시작 (보수적 운용)",
                "1월: Deep Reasoning & War Room 통합",
                "1월: AI Accountability System 도입 (NIA Score)",
                # Future projected
                "2월: 배당 투자 알고리즘 도입 (예정)",
                "3월: 데이터 시각화 대시보드 오픈 (예정)"
            ]
        return []

    async def _synthesize_report(self, year: int, portfolio: Dict, journey: List, milestones: List) -> str:
        """LLM Synthesis for Annual Report"""
        
        prompt = f"""
        당신은 AI 트레이딩 시스템을 총괄하는 최고 경영자(CEO)이자 CIO입니다.
        한 해를 결산하는 '연간 AI 투자 운영 보고서(Annual Investment Report)'를 작성하세요.

        [작성 원칙: Visionary & Head-First]
        1. **Executive Highlight**: 경영진이 한 해의 성패를 즉시 파악할 수 있도록, 핵심 성과와 교훈을 최상단에 요약하십시오.
        2. **Story of Evolution**: 단순한 수익률 보고를 넘어, 시스템이 어떻게 진화했고 위기를 어떻게 극복했는지 '여정(Journey)'을 서술하십시오.
        3. **Future Roadmap**: 내년도 비전과 목표를 명확하고 웅장하게 제시하십시오.

        [DATA SECTION]
        대상 연도: {year}년
        
        1. Portfolio Performance (Year-End):
        {json.dumps(portfolio, indent=2, ensure_ascii=False)}
        
        2. Investment Journey (Major Decisions Timeline):
        {json.dumps(journey, indent=2, ensure_ascii=False)}
        
        3. System Evolution (Key Milestones):
        {json.dumps(milestones, indent=2, ensure_ascii=False)}
        
        [OUTPUT FORMAT - MUST FOLLOW]
        # 🏆 {year} 연간 AI 투자 운용 보고서 (Annual Report)
        
        ## 1. Executive Summary (경영 요약)
        > **"올해를 정의하는 핵심 문장 (The Defining Sentence of the Year)"**
        
        *   **Total Return**: 연간 수익률 [X]% (최종 운용액: {portfolio.get('total_value_usd', 'N/A')})
        *   **Key Achievement**: [올해 가장 자랑할 만한 성과나 시스템 도입]
        *   **Critical Lesson**: [올해 겪은 가장 큰 시행착오와 배움]
        *   **Next Year Vision**: {year+1}년의 핵심 키워드

        ---

        ## 2. 🛣️ The Investment Journey (투자의 여정)
        ### Timeline Review
        *   **Q1~Q2 (상반기)**: [초기 셋업과 시장 적응기]
        *   **Q3~Q4 (하반기)**: [시스템 고도화와 성과 실현기]
        
        ### Decisive Moments
        *   **Best Decision**: [데이터 기반 최고의 판단]
        *   **Crisis Management**: [위기 상황에서의 대응과 결과]

        ## 3. ⚙️ System Evolution (AI 시스템 진화)
        *   **Technological Breakthrough**: 올 한 해 이룩한 기술적 성과 (Deep Reasoning, NIA 등)
        *   **Infrastructure**: 안정성 및 확장성 확보 내역

        ## 4. 🔭 {year + 1} Strategic Outlook (내년 전망 및 전략)
        ### Market View
        *   **Macro Shift**: 내년 시장을 주도할 거시경제 변화 예상.
        
        ### System Roadmap
        *   **New Features**: 내년 도입 예정인 핵심 기능 (e.g., 배당 알고리즘, 고도화된 헷징).
        
        ### Closing Message
        [투자자들에게 전하는 신뢰와 비전의 메시지. 웅장하고 신뢰감 있게 마무리.]

        작성 톤: 웅장하고 비전 제시적인 CEO/CIO 톤.
        언어: 한국어 (Korean Business Style).
        """
        
        return await call_gemini_api(prompt, self.model_name)

if __name__ == "__main__":
    import asyncio
    reporter = AnnualReporter()
    asyncio.run(reporter.generate_annual_report())
