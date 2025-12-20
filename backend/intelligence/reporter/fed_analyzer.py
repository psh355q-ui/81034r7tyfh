"""
Fed Analyzer
Fed 발언 및 정책 분석
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FedEventType(Enum):
    FOMC = "FOMC"
    SPEECH = "SPEECH"
    MINUTES = "MINUTES"
    TESTIMONY = "TESTIMONY"


@dataclass
class FedEvent:
    """Fed 이벤트"""
    date: datetime
    event_type: FedEventType
    speaker: str  # Powell, Waller, etc.
    title: str
    summary: str
    hawkish_score: float  # -1 (dovish) ~ +1 (hawkish)
    key_quotes: List[str] = None
    market_reaction: Optional[str] = None


class FedAnalyzer:
    """
    Fed 발언 분석기
    
    Fed 발언의 hawkish/dovish 정도를 분석
    """
    
    # Hawkish 키워드
    HAWKISH_KEYWORDS = [
        "inflation", "price stability", "rate hike", "tightening",
        "restrictive", "too high", "persistent", "vigilant",
        "further increases", "more work",
    ]
    
    # Dovish 키워드
    DOVISH_KEYWORDS = [
        "accommodation", "support", "rate cut", "easing",
        "slowing", "cooling", "balanced", "patient",
        "data dependent", "pause", "wait and see",
    ]
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    async def analyze_statement(
        self,
        statement: str,
        speaker: str = "Fed",
        context: str = "",
    ) -> Dict:
        """
        Fed 발언 분석
        
        Args:
            statement: 분석할 발언 텍스트
            speaker: 발언자
            context: 추가 컨텍스트
            
        Returns:
            분석 결과
        """
        # 키워드 기반 기본 분석
        hawkish_count = sum(1 for kw in self.HAWKISH_KEYWORDS if kw.lower() in statement.lower())
        dovish_count = sum(1 for kw in self.DOVISH_KEYWORDS if kw.lower() in statement.lower())
        
        total = hawkish_count + dovish_count
        if total > 0:
            hawkish_score = (hawkish_count - dovish_count) / total
        else:
            hawkish_score = 0.0
        
        # 해석
        if hawkish_score > 0.3:
            stance = "HAWKISH"
            interpretation = "금리 인상 또는 긴축 유지 가능성"
        elif hawkish_score < -0.3:
            stance = "DOVISH"
            interpretation = "금리 인하 또는 완화 가능성"
        else:
            stance = "NEUTRAL"
            interpretation = "현 정책 유지 예상"
        
        return {
            "speaker": speaker,
            "hawkish_score": round(hawkish_score, 2),
            "stance": stance,
            "interpretation": interpretation,
            "hawkish_keywords_found": hawkish_count,
            "dovish_keywords_found": dovish_count,
            "market_implication": self._get_market_implication(hawkish_score),
        }
    
    def _get_market_implication(self, hawkish_score: float) -> str:
        """시장 영향 해석"""
        if hawkish_score > 0.5:
            return "국채 금리 상승, 성장주 약세 예상"
        elif hawkish_score > 0.2:
            return "소폭 금리 상승 가능, 경계 필요"
        elif hawkish_score < -0.5:
            return "국채 금리 하락, 위험자산 선호 예상"
        elif hawkish_score < -0.2:
            return "완화적 환경, 성장주 우호적"
        else:
            return "중립적, 방향성 제한적"
