"""
Economic Calendar
경제 지표 발표 일정 및 분석
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """경제 지표 영향도"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class EconomicEvent:
    """경제 지표 이벤트"""
    date: datetime
    indicator: str  # CPI, PCE, NFP, PMI
    country: str = "US"
    actual: Optional[float] = None
    expected: Optional[float] = None
    previous: Optional[float] = None
    impact: ImpactLevel = ImpactLevel.MEDIUM
    surprise: Optional[float] = None  # actual - expected
    market_reaction: Optional[str] = None


# 주요 경제 지표 정보
ECONOMIC_INDICATORS = {
    "CPI": {
        "name": "소비자물가지수 (CPI)",
        "impact": ImpactLevel.HIGH,
        "interpretation": {
            "above": "인플레이션 우려 → 금리 인상 압력 → 주식 약세",
            "below": "인플레이션 둔화 → 금리 인하 기대 → 주식 강세",
            "inline": "예상 부합 → 시장 영향 제한적",
        },
    },
    "PCE": {
        "name": "개인소비지출 (PCE)",
        "impact": ImpactLevel.HIGH,
        "interpretation": {
            "above": "Fed 선호 지표 상승 → 긴축 지속",
            "below": "인플레이션 목표 접근 → 완화 기대",
            "inline": "중립적",
        },
    },
    "NFP": {
        "name": "비농업 고용 (NFP)",
        "impact": ImpactLevel.HIGH,
        "interpretation": {
            "above": "노동시장 과열 → 금리 동결/인상",
            "below": "고용 약화 → 금리 인하 가능성",
            "inline": "골디락스 시나리오",
        },
    },
    "PMI": {
        "name": "구매관리자지수 (PMI)",
        "impact": ImpactLevel.MEDIUM,
        "interpretation": {
            "above": "50 이상시 확장 → 경기 호조",
            "below": "50 미만시 수축 → 경기 둔화",
            "inline": "현상 유지",
        },
    },
    "GDP": {
        "name": "국내총생산 (GDP)",
        "impact": ImpactLevel.HIGH,
        "interpretation": {
            "above": "경제 성장 가속 → 위험자산 선호",
            "below": "성장 둔화 → 안전자산 선호",
            "inline": "예상 부합",
        },
    },
    "RETAIL": {
        "name": "소매판매",
        "impact": ImpactLevel.MEDIUM,
        "interpretation": {
            "above": "소비 견조 → 경기 호조",
            "below": "소비 약화 → 경기 둔화 우려",
            "inline": "안정적 소비",
        },
    },
}


class EconomicCalendar:
    """
    경제 캘린더
    
    주요 경제 지표 발표 일정 추적 및 분석
    """
    
    def __init__(self):
        self.events: List[EconomicEvent] = []
    
    async def get_upcoming_events(
        self,
        days: int = 7,
        impact_filter: ImpactLevel = None,
    ) -> List[EconomicEvent]:
        """
        향후 경제 이벤트 조회
        
        Args:
            days: 조회 기간 (일)
            impact_filter: 영향도 필터
            
        Returns:
            List[EconomicEvent]: 이벤트 목록
        """
        # 실제 구현에서는 경제 캘린더 API 사용
        # 여기서는 예시 데이터 반환
        now = datetime.now()
        
        sample_events = [
            EconomicEvent(
                date=now + timedelta(days=1),
                indicator="CPI",
                expected=3.2,
                previous=3.4,
                impact=ImpactLevel.HIGH,
            ),
            EconomicEvent(
                date=now + timedelta(days=3),
                indicator="NFP",
                expected=180000,
                previous=227000,
                impact=ImpactLevel.HIGH,
            ),
            EconomicEvent(
                date=now + timedelta(days=5),
                indicator="PMI",
                expected=52.5,
                previous=52.1,
                impact=ImpactLevel.MEDIUM,
            ),
        ]
        
        if impact_filter:
            sample_events = [e for e in sample_events if e.impact == impact_filter]
        
        return sample_events
    
    def analyze_surprise(
        self,
        indicator: str,
        actual: float,
        expected: float,
    ) -> Dict:
        """
        서프라이즈 분석
        
        Args:
            indicator: 지표 코드
            actual: 실제 값
            expected: 예상 값
            
        Returns:
            분석 결과
        """
        info = ECONOMIC_INDICATORS.get(indicator, {})
        
        surprise = actual - expected
        surprise_pct = (surprise / expected * 100) if expected != 0 else 0
        
        if surprise_pct > 5:
            direction = "above"
            magnitude = "큰 폭 상회"
        elif surprise_pct > 0:
            direction = "above"
            magnitude = "소폭 상회"
        elif surprise_pct < -5:
            direction = "below"
            magnitude = "큰 폭 하회"
        elif surprise_pct < 0:
            direction = "below"
            magnitude = "소폭 하회"
        else:
            direction = "inline"
            magnitude = "예상 부합"
        
        interpretation = info.get("interpretation", {}).get(direction, "분석 불가")
        
        return {
            "indicator": indicator,
            "name": info.get("name", indicator),
            "actual": actual,
            "expected": expected,
            "surprise": round(surprise, 2),
            "surprise_pct": round(surprise_pct, 2),
            "magnitude": magnitude,
            "interpretation": interpretation,
            "impact": info.get("impact", ImpactLevel.MEDIUM).value,
        }
    
    def format_calendar_korean(
        self,
        events: List[EconomicEvent],
    ) -> str:
        """이벤트 목록을 한국어로 포맷팅"""
        if not events:
            return "향후 주요 경제 이벤트가 없습니다."
        
        lines = ["📅 **주요 경제 일정**\n"]
        
        for event in events:
            info = ECONOMIC_INDICATORS.get(event.indicator, {})
            name = info.get("name", event.indicator)
            impact_emoji = "🔴" if event.impact == ImpactLevel.HIGH else "🟡"
            
            date_str = event.date.strftime("%m/%d (%a)")
            
            line = f"- {date_str} {impact_emoji} **{name}**"
            if event.expected is not None:
                line += f" (예상: {event.expected})"
            
            lines.append(line)
        
        return "\n".join(lines)
