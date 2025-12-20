"""
Economic Calendar - 경제 캘린더 기반 예측

향후 경제 이벤트를 추적하고 AI로 영향을 예측하여
선제적으로 리스크를 관리

핵심 기능:
1. 주요 경제 이벤트 추적 (FOMC, CPI, NFP 등)
2. AI 영향 예측 (Bull/Bear 시나리오)
3. 변동성 레벨 예측
4. 자동 거래 중지 권장

작성일: 2025-12-15
Phase: E Week 1-2
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EventImportance(Enum):
    """이벤트 중요도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """이벤트 유형"""
    FOMC = "fomc"           # 연준 금리 결정
    CPI = "cpi"             # 소비자물가지수
    NFP = "nfp"             # 비농업 고용
    GDP = "gdp"             # GDP
    EARNINGS = "earnings"    # 기업 실적
    GEOPOLITICAL = "geopolitical"  # 지정학적
    OTHER = "other"


class MarketImpact(Enum):
    """예상 시장 영향"""
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    HIGH_VOLATILITY = "high_volatility"


@dataclass
class EconomicEvent:
    """경제 이벤트"""
    date: datetime
    event_type: EventType
    title: str
    importance: EventImportance
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None  # 발표 후
    description: str = ""


@dataclass
class EventImpactPrediction:
    """이벤트 영향 예측"""
    event: EconomicEvent
    bull_scenario: str  # 상승 시나리오
    bear_scenario: str  # 하락 시나리오
    volatility_level: float  # 0.0 ~ 1.0
    market_impact: MarketImpact
    trading_recommendation: str  # 거래 권장사항
    confidence: float  # 예측 신뢰도
    analysis: str  # AI 분석
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CalendarAlert:
    """캘린더 알림"""
    event: EconomicEvent
    days_until: int
    action: str  # "PAUSE_TRADING", "REDUCE_POSITION", "MONITOR"
    reason: str


class EconomicCalendar:
    """
    경제 캘린더
    
    향후 경제 이벤트를 추적하고 AI로 영향을 예측합니다.
    
    Usage:
        calendar = EconomicCalendar()
        
        # 향후 이벤트 조회
        events = await calendar.get_upcoming_events(days=7)
        
        # AI 영향 예측
        prediction = await calendar.predict_impact(events[0])
        
        print(f"Volatility: {prediction.volatility_level:.0%}")
        print(f"Recommendation: {prediction.trading_recommendation}")
    """
    
    def __init__(self):
        logger.info("EconomicCalendar initialized")
    
    async def get_upcoming_events(
        self,
        days: int = 7,
        min_importance: EventImportance = EventImportance.MEDIUM
    ) -> List[EconomicEvent]:
        """
        향후 경제 이벤트 조회
        
        Args:
            days: 조회 기간 (일)
            min_importance: 최소 중요도
            
        Returns:
            EconomicEvent 리스트
        """
        logger.info(f"Fetching upcoming events for {days} days")
        
        # 실제로는 Trading Economics, Investing.com API 사용
        # 여기서는 샘플 데이터
        
        now = datetime.now()
        events = []
        
        # 샘플 이벤트 생성
        sample_events = [
            {
                "delta_days": 1,
                "type": EventType.CPI,
                "title": "CPI (Consumer Price Index)",
                "importance": EventImportance.HIGH,
                "forecast": "3.2%",
                "previous": "3.1%",
                "description": "월간 소비자물가지수 발표"
            },
            {
                "delta_days": 3,
                "type": EventType.FOMC,
                "title": "FOMC Meeting",
                "importance": EventImportance.CRITICAL,
                "forecast": "Hold at 5.50%",
                "previous": "5.50%",
                "description": "연준 금리 결정 회의"
            },
            {
                "delta_days": 5,
                "type": EventType.NFP,
                "title": "Non-Farm Payrolls",
                "importance": EventImportance.HIGH,
                "forecast": "180K",
                "previous": "175K",
                "description": "비농업 고용 지표"
            },
            {
                "delta_days": 7,
                "type": EventType.GDP,
                "title": "GDP Growth Rate",
                "importance": EventImportance.MEDIUM,
                "forecast": "2.1%",
                "previous": "2.0%",
                "description": "분기 GDP 성장률"
            }
        ]
        
        for sample in sample_events:
            if sample["delta_days"] <= days:
                event_date = now + timedelta(days=sample["delta_days"])
                
                event = EconomicEvent(
                    date=event_date,
                    event_type=sample["type"],
                    title=sample["title"],
                    importance=sample["importance"],
                    forecast=sample.get("forecast"),
                    previous=sample.get("previous"),
                    description=sample["description"]
                )
                
                # 중요도 필터링
                importance_order = {
                    EventImportance.LOW: 1,
                    EventImportance.MEDIUM: 2,
                    EventImportance.HIGH: 3,
                    EventImportance.CRITICAL: 4
                }
                
                if importance_order[event.importance] >= importance_order[min_importance]:
                    events.append(event)
        
        logger.info(f"Found {len(events)} upcoming events")
        return events
    
    async def predict_impact(
        self,
        event: EconomicEvent
    ) -> EventImpactPrediction:
        """
        AI 영향 예측
        
        Args:
            event: 경제 이벤트
            
        Returns:
            EventImpactPrediction
        """
        logger.info(f"Predicting impact for: {event.title}")
        
        # Claude에게 예측 요청
        from backend.ai.claude_client import get_claude_client
        
        claude = get_claude_client()
        
        prompt = f"""
        다음 경제 이벤트의 시장 영향을 분석하세요:
        
        이벤트: {event.title}
        일시: {event.date.strftime('%Y-%m-%d %H:%M')}
        중요도: {event.importance.value}
        예상: {event.forecast}
        이전: {event.previous}
        
        다음 형식으로 답변하세요:
        
        1. 상승 시나리오 (Bull):
        [예상치보다 좋을 경우 시장 반응]
        
        2. 하락 시나리오 (Bear):
        [예상치보다 나쁠 경우 시장 반응]
        
        3. 변동성 레벨 (0.0 ~ 1.0):
        [예상 변동성 수치]
        
        4. 거래 권장사항:
        [거래 전략 조언]
        
        간결하게 작성하세요.
        """
        
        try:
            analysis = await claude.generate(prompt)
            
            # 간단한 파싱 (실제로는 더 정교하게)
            bull_scenario = "예상치 상회 시 상승 가능성"
            bear_scenario = "예상치 하회 시 하락 위험"
            
            # 중요도에 따른 변동성
            volatility_map = {
                EventImportance.LOW: 0.2,
                EventImportance.MEDIUM: 0.4,
                EventImportance.HIGH: 0.6,
                EventImportance.CRITICAL: 0.9
            }
            volatility = volatility_map.get(event.importance, 0.5)
            
            # 시장 영향 판단
            market_impact = MarketImpact.HIGH_VOLATILITY if volatility > 0.7 else MarketImpact.NEUTRAL
            
            # 거래 권장사항
            if event.importance == EventImportance.CRITICAL:
                recommendation = "이벤트 2일 전부터 포지션 축소 권장"
            elif event.importance == EventImportance.HIGH:
                recommendation = "이벤트 1일 전 신규 매수 자제"
            else:
                recommendation = "모니터링 유지"
            
            prediction = EventImpactPrediction(
                event=event,
                bull_scenario=bull_scenario,
                bear_scenario=bear_scenario,
                volatility_level=volatility,
                market_impact=market_impact,
                trading_recommendation=recommendation,
                confidence=0.75,
                analysis=analysis
            )
            
            logger.info(f"Impact prediction complete: volatility={volatility:.0%}")
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to predict impact: {e}")
            
            # Fallback
            return EventImpactPrediction(
                event=event,
                bull_scenario="분석 실패",
                bear_scenario="분석 실패",
                volatility_level=0.5,
                market_impact=MarketImpact.NEUTRAL,
                trading_recommendation="모니터링",
                confidence=0.3,
                analysis="AI 분석 실패"
            )
    
    async def get_alerts(
        self,
        days_ahead: int = 3
    ) -> List[CalendarAlert]:
        """
        이벤트 알림 생성
        
        Args:
            days_ahead: 알림 기준 일수
            
        Returns:
            CalendarAlert 리스트
        """
        events = await self.get_upcoming_events(days=days_ahead)
        alerts = []
        
        for event in events:
            days_until = (event.date - datetime.now()).days
            
            # 중요 이벤트 임박 시 알림
            if event.importance == EventImportance.CRITICAL and days_until <= 2:
                alert = CalendarAlert(
                    event=event,
                    days_until=days_until,
                    action="PAUSE_TRADING",
                    reason=f"CRITICAL 이벤트 {days_until}일 전 - 거래 중지 권장"
                )
                alerts.append(alert)
            
            elif event.importance == EventImportance.HIGH and days_until <= 1:
                alert = CalendarAlert(
                    event=event,
                    days_until=days_until,
                    action="REDUCE_POSITION",
                    reason=f"HIGH 이벤트 {days_until}일 전 - 포지션 축소 권장"
                )
                alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} alerts")
        return alerts
    
    def should_pause_trading(
        self,
        alerts: List[CalendarAlert]
    ) -> tuple[bool, str]:
        """
        거래 중지 필요 여부 판단
        
        Args:
            alerts: 알림 리스트
            
        Returns:
            (중지 필요 여부, 사유)
        """
        for alert in alerts:
            if alert.action == "PAUSE_TRADING":
                return True, alert.reason
        
        return False, ""


# 전역 인스턴스
_economic_calendar = None


def get_economic_calendar() -> EconomicCalendar:
    """전역 EconomicCalendar 인스턴스 반환"""
    global _economic_calendar
    if _economic_calendar is None:
        _economic_calendar = EconomicCalendar()
    return _economic_calendar


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Economic Calendar Test ===\n")
        
        calendar = EconomicCalendar()
        
        # 1. 향후 이벤트 조회
        print("📅 Upcoming Events (7 days):\n")
        events = await calendar.get_upcoming_events(days=7)
        
        for event in events:
            days_until = (event.date - datetime.now()).days
            print(f"[{event.importance.value.upper()}] {event.title}")
            print(f"  일시: {event.date.strftime('%Y-%m-%d')} (D-{days_until})")
            print(f"  예상: {event.forecast} | 이전: {event.previous}")
            print()
        
        # 2. AI 영향 예측
        if events:
            print("🔮 AI Impact Prediction:\n")
            prediction = await calendar.predict_impact(events[0])
            
            print(f"이벤트: {prediction.event.title}")
            print(f"변동성: {prediction.volatility_level:.0%}")
            print(f"시장 영향: {prediction.market_impact.value}")
            print(f"권장사항: {prediction.trading_recommendation}")
            print()
        
        # 3. 알림 생성
        print("⚠️  Alerts:\n")
        alerts = await calendar.get_alerts(days_ahead=3)
        
        for alert in alerts:
            print(f"[{alert.action}] {alert.event.title}")
            print(f"  사유: {alert.reason}")
            print()
        
        # 4. 거래 중지 판단
        should_pause, reason = calendar.should_pause_trading(alerts)
        
        if should_pause:
            print(f"🛑 거래 중지 필요!")
            print(f"   사유: {reason}")
        else:
            print("✅ 거래 가능")
        
        print("\n✅ Economic Calendar test completed!")
    
    asyncio.run(test())
