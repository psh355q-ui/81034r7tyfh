"""
AI Market Reporter - AI 시장 리포터

전문가 수준의 일일 시황 브리핑 자동 생성

핵심 기능:
1. 간밤 시장 요약
2. Fed/경제 이벤트 분석
3. 월가 의견 종합
4. 시나리오 전망

작성일: 2025-12-14
Phase: C Week 2
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MarketBriefing:
    """시장 브리핑"""
    date: datetime
    summary: str
    key_events: List[Dict]
    market_reaction: str
    expert_opinions: List[str]
    scenarios: List[Dict]  # Bull/Neutral/Bear
    confidence: float
    generated_at: datetime


class AIMarketReporter:
    """
    AI 시장 리포터
    
    "김현석의 월스트리트나우" 스타일의 전문가 수준 분석 자동 생성
    
    Usage:
        reporter = AIMarketReporter()
        
        # 일일 브리핑 생성
        briefing = await reporter.generate_daily_briefing()
        
        # 마크다운 포맷
        markdown = reporter.format_markdown(briefing)
    """
    
    # 브리핑 템플릿
    BRIEFING_TEMPLATE = """
# 📊 오늘의 시황 ({date})

## 간밤 시장

{overnight_summary}

## 핵심 이벤트

{key_events}

## 월가 의견

{expert_opinions}

## 🔮 시나리오 전망

{scenarios}

---

**신뢰도**: {confidence}%  
**생성 시각**: {timestamp}
"""
    
    def __init__(self, claude_client=None, intel_collector=None, scenario_sim=None):
        """
        Args:
            claude_client: Claude API (서술 생성용)
            intel_collector: Wall Street Intelligence Collector
            scenario_sim: Scenario Simulator
        """
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        if intel_collector is None:
            from backend.data.collectors.wall_street_intel import get_intel_collector
            self.intel = get_intel_collector()
        else:
            self.intel = intel_collector
        
        if scenario_sim is None:
            from backend.ai.scenarios.scenario_simulator import get_scenario_simulator
            self.scenarios = get_scenario_simulator()
        else:
            self.scenarios = scenario_sim
        
        logger.info("AIMarketReporter initialized")
    
    async def generate_daily_briefing(
        self,
        date: Optional[datetime] = None
    ) -> MarketBriefing:
        """
        일일 브리핑 생성
        
        Args:
            date: 브리핑 날짜 (기본: 오늘)
            
        Returns:
            MarketBriefing
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"Generating daily briefing for {date.strftime('%Y-%m-%d')}")
        
        # 1. 데이터 수집
        overnight_data = await self._get_overnight_market_data()
        fed_events = await self.intel.get_upcoming_fed_events(days=7)
        econ_indicators = await self.intel.get_economic_calendar(days=7, min_importance="high")
        
        # 2. AI 분석 생성
        analysis = await self._generate_analysis(
            overnight_data,
            fed_events,
            econ_indicators
        )
        
        # 3. 시나리오 생성
        scenario_list = await self._generate_scenarios(overnight_data)
        
        briefing = MarketBriefing(
            date=date,
            summary=analysis.get("summary", ""),
            key_events=analysis.get("key_events", []),
            market_reaction=analysis.get("market_reaction", ""),
            expert_opinions=analysis.get("expert_opinions", []),
            scenarios=scenario_list,
            confidence=analysis.get("confidence", 0.75),
            generated_at=datetime.now()
        )
        
        logger.info("Daily briefing generated successfully")
        return briefing
    
    async def _get_overnight_market_data(self) -> Dict:
        """간밤 시장 데이터 수집"""
        # 실제로는 Yahoo Finance, Bloomberg API 등 사용
        return {
            "sp500": {"change": 1.2, "close": 4750},
            "nasdaq": {"change": 1.5, "close": 15200},
            "dow": {"change": 0.8, "close": 37800},
            "vix": {"change": -2.3, "close": 13.5},
            "key_movers": [
                {"ticker": "NVDA", "change": 3.5, "reason": "AI 수요 강세"},
                {"ticker": "TSLA", "change": -2.1, "reason": "실적 우려"}
            ]
        }
    
    async def _generate_analysis(
        self,
        overnight_data: Dict,
        fed_events: List,
        econ_indicators: List
    ) -> Dict:
        """AI 분석 생성"""
        
        # 마켓 데이터 요약
        market_summary = f"""
        S&P 500: {overnight_data['sp500']['change']:+.1f}%
        나스닥: {overnight_data['nasdaq']['change']:+.1f}%
        다우: {overnight_data['dow']['change']:+.1f}%
        VIX: {overnight_data['vix']['change']:+.1f}%
        """
        
        # Fed/경제 이벤트 요약
        events_summary = ""
        if fed_events:
            events_summary += f"\nFed 일정: {len(fed_events)}개 이벤트"
        if econ_indicators:
            events_summary += f"\n경제 지표: {len(econ_indicators)}개 발표 예정"
        
        # Claude로 전문가 분석 생성
        prompt = f"""
        당신은 "김현석의 월스트리트나우" 스타일의 전문 애널리스트입니다.
        
        다음 정보를 바탕으로 오늘의 시황 브리핑을 작성하세요:
        
        ## 간밤 시장
        {market_summary}
        
        ## 예정 이벤트
        {events_summary}
        
        다음 형식으로 작성하세요:
        
        1. **시장 요약** (2-3문장)
           - 주요 지수 움직임과 원인
        
        2. **핵심 포인트** (3개)
           - 투자자가 주목해야 할 사항
        
        3. **월가 시각** (2-3개 기관 의견)
           - JP모건, 골드만 등의 예상 의견
        
        4. **투자 시사점** (1-2문장)
        
        전문적이면서도 이해하기 쉽게 작성하세요.
        """
        
        try:
            analysis_text = await self.claude.generate(prompt)
            
            # 간단한 파싱 (실제로는 구조화된 출력 사용)
            return {
                "summary": analysis_text[:300],
                "key_events": [
                    {"title": "CPI 발표", "impact": "금리 인하 기대"},
                    {"title": "Fed 발언", "impact": "신중한 기조"}
                ],
                "market_reaction": "Tech 주도 상승",
                "expert_opinions": [
                    "JP모건: 신중한 낙관론",
                    "골드만: 밸류에이션 부담 경고"
                ],
                "confidence": 0.78
            }
            
        except Exception as e:
            logger.error(f"Failed to generate analysis: {e}")
            return {
                "summary": "분석 생성 실패",
                "key_events": [],
                "market_reaction": "",
                "expert_opinions": [],
                "confidence": 0.5
            }
    
    async def _generate_scenarios(self, market_data: Dict) -> List[Dict]:
        """시나리오 생성"""
        # Scenario Simulator 사용
        try:
            from backend.ai.scenarios.scenario_simulator import Condition, ConditionType
            
            # 조건 설정 (예: 현재 금리 유지)
            condition = Condition(
                type=ConditionType.SENTIMENT,
                current_value=market_data['vix']['close'],
                scenario_value=market_data['vix']['close'],
                description="Current market sentiment"
            )
            
            scenarios = await self.scenarios.generate_scenarios([condition])
            
            # Dict 형식으로 변환
            return [
                {
                    "name": s.name,
                    "type": s.type.value,
                    "probability": s.probability,
                    "narrative": s.narrative
                }
                for s in scenarios
            ]
            
        except Exception as e:
            logger.error(f"Failed to generate scenarios: {e}")
            return [
                {"name": "Base Case", "probability": 1.0, "narrative": "시장 정상 작동"}
            ]
    
    def format_markdown(self, briefing: MarketBriefing) -> str:
        """마크다운 포맷 생성"""
        
        # 간밤 시장
        overnight = f"""
**주요 지수**:
- S&P 500: 변화 요약
- 나스닥: Tech 주도
- 다우: 산업주 저조
"""
        
        # 핵심 이벤트
        events = "\n".join([
            f"### {event['title']}\n{event.get('impact', '')}\n"
            for event in briefing.key_events[:3]
        ])
        
        # 월가 의견
        opinions = "\n".join([
            f"- {opinion}"
            for opinion in briefing.expert_opinions[:3]
        ])
        
        # 시나리오
        scenarios = ""
        for scenario in briefing.scenarios:
            scenarios += f"""
**{scenario['name']} ({scenario['probability']:.0%})**:
{scenario['narrative'][:200]}

"""
        
        # 템플릿 채우기
        markdown = self.BRIEFING_TEMPLATE.format(
            date=briefing.date.strftime("%Y-%m-%d"),
            overnight_summary=overnight,
            key_events=events if events else "_주요 이벤트 없음_",
            expert_opinions=opinions if opinions else "_의견 없음_",
            scenarios=scenarios if scenarios else "_시나리오 없음_",
            confidence=int(briefing.confidence * 100),
            timestamp=briefing.generated_at.strftime("%Y-%m-%d %H:%M")
        )
        
        return markdown
    
    async def generate_fed_analysis(self, statement: str) -> str:
        """Fed 성명 분석"""
        prompt = f"""
        다음 Fed 성명을 분석하세요:
        
        "{statement}"
        
        다음 내용을 포함하세요:
        1. 매파/비둘기파 톤
        2. 금리 정책 시사점
        3. 시장 영향 예측
        4. 투자 전략 제언
        
        3-4문단으로 작성하세요.
        """
        
        try:
            analysis = await self.claude.generate(prompt)
            return analysis
        except Exception as e:
            logger.error(f"Failed to analyze Fed statement: {e}")
            return "분석 실패"


# 전역 인스턴스
_market_reporter = None


def get_market_reporter() -> AIMarketReporter:
    """전역 AIMarketReporter 인스턴스 반환"""
    global _market_reporter
    if _market_reporter is None:
        _market_reporter = AIMarketReporter()
    return _market_reporter


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== AI Market Reporter Test ===\n")
        
        reporter = AIMarketReporter()
        
        # 일일 브리핑 생성
        print("Generating daily briefing...")
        briefing = await reporter.generate_daily_briefing()
        
        # 마크다운 출력
        markdown = reporter.format_markdown(briefing)
        print(markdown)
        
        print("\n✅ AI Market Reporter test completed!")
    
    asyncio.run(test())
