"""
Investment Journey Memory - User Decision Tracking & Coaching

Phase: Phase 4.2 - Grand Unified Strategy (Core Features)
Date: 2026-01-05

Purpose:
    사용자의 투자 결정 히스토리를 기억하고, 과거 패턴을 기반으로 코칭.
    "3개월 전 비슷한 장세에서 패닉 셀링으로 -15% 손실 → 이번엔 홀딩 추천"

Key Features:
    1. 결정 패턴 분석: 공포 구간 대응, 탐욕 구간 대응
    2. 과거 결과 추적: 각 결정의 30일/90일 후 결과
    3. 회고적 코칭: 유사 상황 발생 시 과거 교훈 상기
    4. 의사결정 품질 점수: 수익률이 아닌 '프로세스' 점수

Usage:
    memory = InvestmentJourneyMemory(user_id="user123")
    memory.record_decision(decision_data)
    coaching = memory.get_coaching(current_situation)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """투자 결정 유형"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ADD_POSITION = "add_position"       # 추가 매수
    REDUCE_POSITION = "reduce_position" # 부분 매도
    PANIC_SELL = "panic_sell"           # 공포 매도
    FOMO_BUY = "fomo_buy"               # 공포 탐욕 매수
    STOP_LOSS = "stop_loss"             # 손절
    TAKE_PROFIT = "take_profit"         # 익절


class MarketCondition(str, Enum):
    """시장 상황"""
    FEAR = "fear"                 # 공포 (VIX > 30 또는 급락)
    GREED = "greed"               # 탐욕 (VIX < 15, 급등)
    NEUTRAL = "neutral"           # 중립
    HIGH_VOLATILITY = "high_vol"  # 고변동성
    TRENDING_UP = "trending_up"   # 상승 추세
    TRENDING_DOWN = "trending_down"  # 하락 추세


@dataclass
class InvestmentDecision:
    """투자 결정 기록"""
    decision_id: str
    user_id: str
    ticker: str
    decision_type: DecisionType
    market_condition: MarketCondition
    
    # 결정 시점 데이터
    entry_price: float
    quantity: int
    decision_date: datetime
    reasoning: str  # 사용자 또는 AI의 결정 근거
    
    # 결과 추적 (나중에 업데이트)
    price_30d: Optional[float] = None
    price_90d: Optional[float] = None
    outcome_30d: Optional[float] = None  # % 변화
    outcome_90d: Optional[float] = None  # % 변화
    
    # 메타데이터
    ai_recommendation: Optional[str] = None  # AI가 추천한 행동
    followed_ai: bool = False  # AI 추천을 따랐는지
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "decision_type": self.decision_type.value,
            "market_condition": self.market_condition.value,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "decision_date": self.decision_date.isoformat(),
            "reasoning": self.reasoning,
            "price_30d": self.price_30d,
            "price_90d": self.price_90d,
            "outcome_30d": self.outcome_30d,
            "outcome_90d": self.outcome_90d,
            "ai_recommendation": self.ai_recommendation,
            "followed_ai": self.followed_ai,
        }


@dataclass
class CoachingAdvice:
    """코칭 조언"""
    message: str
    based_on_decisions: List[str]  # 참조된 과거 결정 ID
    confidence: float
    historical_success_rate: Optional[float] = None


@dataclass
class DecisionQualityScore:
    """의사결정 품질 점수"""
    fear_response_score: float      # 공포 구간 대응 점수 (0-100)
    greed_response_score: float     # 탐욕 구간 대응 점수 (0-100)
    consistency_score: float        # 전략 일관성 점수 (0-100)
    discipline_score: float         # 규율 준수 점수 (0-100)
    overall_score: float            # 전체 품질 점수 (0-100)
    
    insights: List[str] = field(default_factory=list)


class InvestmentJourneyMemory:
    """
    Investment Journey Memory - 투자 여정 기억 시스템
    
    사용자의 투자 결정 패턴을 분석하고, 과거 경험을 기반으로 코칭합니다.
    """
    
    def __init__(self, user_id: str, decisions: Optional[List[InvestmentDecision]] = None):
        """
        Args:
            user_id: 사용자 ID
            decisions: 기존 결정 이력 (Optional)
        """
        self.user_id = user_id
        self.decisions: List[InvestmentDecision] = decisions or []
    
    def record_decision(
        self,
        ticker: str,
        decision_type: str,
        market_condition: str,
        entry_price: float,
        quantity: int,
        reasoning: str,
        ai_recommendation: Optional[str] = None,
        followed_ai: bool = False
    ) -> InvestmentDecision:
        """
        투자 결정 기록
        
        Args:
            ticker: 종목 티커
            decision_type: 결정 유형 (buy, sell, hold, panic_sell, etc.)
            market_condition: 시장 상황 (fear, greed, neutral, etc.)
            entry_price: 진입/청산 가격
            quantity: 수량
            reasoning: 결정 근거
            ai_recommendation: AI 추천 (있다면)
            followed_ai: AI 추천 따랐는지
        
        Returns:
            InvestmentDecision: 생성된 결정 기록
        """
        decision = InvestmentDecision(
            decision_id=f"{self.user_id}_{ticker}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=self.user_id,
            ticker=ticker,
            decision_type=DecisionType(decision_type.lower()),
            market_condition=MarketCondition(market_condition.lower()),
            entry_price=entry_price,
            quantity=quantity,
            decision_date=datetime.now(),
            reasoning=reasoning,
            ai_recommendation=ai_recommendation,
            followed_ai=followed_ai
        )
        
        self.decisions.append(decision)
        logger.info(f"📝 Decision recorded: {decision.decision_id} - {decision.decision_type.value} {ticker}")
        
        return decision
    
    def update_outcome(
        self,
        decision_id: str,
        current_price: float,
        days_since: int
    ) -> Optional[InvestmentDecision]:
        """
        결정의 결과 업데이트 (30일/90일 후)
        
        Args:
            decision_id: 결정 ID
            current_price: 현재 가격
            days_since: 경과 일수
        
        Returns:
            업데이트된 결정 객체
        """
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                change_pct = ((current_price - decision.entry_price) / decision.entry_price) * 100
                
                if days_since >= 30 and decision.price_30d is None:
                    decision.price_30d = current_price
                    decision.outcome_30d = change_pct
                    logger.info(f"📊 30-day outcome updated: {decision_id} = {change_pct:.1f}%")
                
                if days_since >= 90 and decision.price_90d is None:
                    decision.price_90d = current_price
                    decision.outcome_90d = change_pct
                    logger.info(f"📊 90-day outcome updated: {decision_id} = {change_pct:.1f}%")
                
                return decision
        
        return None
    
    def get_coaching(
        self,
        ticker: str,
        current_market_condition: str,
        current_action: Optional[str] = None
    ) -> CoachingAdvice:
        """
        현재 상황에 대한 코칭 조언 제공
        
        Args:
            ticker: 현재 고려 중인 티커
            current_market_condition: 현재 시장 상황
            current_action: 사용자가 고려 중인 행동
        
        Returns:
            CoachingAdvice: 코칭 조언
        """
        condition = MarketCondition(current_market_condition.lower())
        
        # 유사 상황 검색
        similar_decisions = self._find_similar_situations(condition, ticker)
        
        if not similar_decisions:
            return CoachingAdvice(
                message="아직 유사한 과거 경험이 없습니다. 신중하게 결정해주세요.",
                based_on_decisions=[],
                confidence=0.3
            )
        
        # 과거 결과 분석
        outcomes = [d.outcome_30d for d in similar_decisions if d.outcome_30d is not None]
        
        if not outcomes:
            messages = self._generate_pattern_message(similar_decisions, current_action)
            return CoachingAdvice(
                message=messages,
                based_on_decisions=[d.decision_id for d in similar_decisions],
                confidence=0.5
            )
        
        avg_outcome = sum(outcomes) / len(outcomes)
        positive_count = sum(1 for o in outcomes if o > 0)
        success_rate = positive_count / len(outcomes)
        
        # 코칭 메시지 생성
        message = self._generate_coaching_message(
            similar_decisions, 
            avg_outcome, 
            success_rate, 
            current_action
        )
        
        return CoachingAdvice(
            message=message,
            based_on_decisions=[d.decision_id for d in similar_decisions],
            confidence=min(0.9, 0.5 + (len(similar_decisions) * 0.1)),
            historical_success_rate=success_rate
        )
    
    def get_quality_score(self) -> DecisionQualityScore:
        """
        의사결정 품질 점수 계산
        
        Returns:
            DecisionQualityScore: 품질 점수 및 인사이트
        """
        if not self.decisions:
            return DecisionQualityScore(
                fear_response_score=50.0,
                greed_response_score=50.0,
                consistency_score=50.0,
                discipline_score=50.0,
                overall_score=50.0,
                insights=["충분한 데이터가 없습니다."]
            )
        
        insights = []
        
        # 1. 공포 구간 대응 점수
        fear_decisions = [d for d in self.decisions if d.market_condition == MarketCondition.FEAR]
        fear_score = self._calculate_condition_score(fear_decisions, "fear")
        
        # 2. 탐욕 구간 대응 점수
        greed_decisions = [d for d in self.decisions if d.market_condition == MarketCondition.GREED]
        greed_score = self._calculate_condition_score(greed_decisions, "greed")
        
        # 3. 전략 일관성 점수
        consistency_score = self._calculate_consistency_score()
        
        # 4. 규율 준수 점수 (AI 추천 따르기)
        followed_ai = [d for d in self.decisions if d.followed_ai]
        discipline_score = (len(followed_ai) / len(self.decisions)) * 100 if self.decisions else 50
        
        # 인사이트 생성
        if fear_score < 50:
            insights.append("공포 구간에서 패닉 셀링 비율이 높습니다. 장기 관점을 유지해보세요.")
        if greed_score < 50:
            insights.append("탐욕 구간에서 FOMO 매수 비율이 높습니다. 신중한 진입이 필요합니다.")
        if consistency_score > 70:
            insights.append("일관된 전략을 유지하고 계십니다. 잘 하고 계세요!")
        if discipline_score < 40:
            insights.append("AI 추천을 더 자주 따르는 것을 고려해보세요.")
        
        overall = (fear_score + greed_score + consistency_score + discipline_score) / 4
        
        return DecisionQualityScore(
            fear_response_score=fear_score,
            greed_response_score=greed_score,
            consistency_score=consistency_score,
            discipline_score=discipline_score,
            overall_score=overall,
            insights=insights
        )
    
    def _find_similar_situations(
        self, 
        condition: MarketCondition, 
        ticker: Optional[str] = None
    ) -> List[InvestmentDecision]:
        """유사 상황 검색"""
        similar = []
        for d in self.decisions:
            if d.market_condition == condition:
                if ticker is None or d.ticker == ticker:
                    similar.append(d)
        return similar[-10:]  # 최근 10개만
    
    def _generate_pattern_message(
        self, 
        decisions: List[InvestmentDecision],
        current_action: Optional[str]
    ) -> str:
        """패턴 기반 메시지 생성"""
        if not decisions:
            return "데이터 부족"
        
        panic_count = sum(1 for d in decisions if d.decision_type == DecisionType.PANIC_SELL)
        hold_count = sum(1 for d in decisions if d.decision_type == DecisionType.HOLD)
        
        if panic_count > hold_count:
            return f"📊 과거 유사 상황에서 {panic_count}회 패닉 셀링을 하셨습니다. 이번엔 차분히 판단해보세요."
        elif hold_count > panic_count:
            return f"📊 과거 유사 상황에서 {hold_count}회 홀딩을 선택하셨습니다. 일관성을 유지하세요."
        else:
            return "📊 과거 유사 상황이 발견되었습니다. 신중하게 결정하세요."
    
    def _generate_coaching_message(
        self,
        decisions: List[InvestmentDecision],
        avg_outcome: float,
        success_rate: float,
        current_action: Optional[str]
    ) -> str:
        """코칭 메시지 생성"""
        if avg_outcome > 0:
            msg = f"📈 과거 유사 상황에서 평균 {avg_outcome:.1f}% 수익 (성공률: {success_rate:.0%}). "
            msg += "비슷한 접근을 고려해보세요."
        else:
            msg = f"📉 과거 유사 상황에서 평균 {avg_outcome:.1f}% 손실 (성공률: {success_rate:.0%}). "
            msg += "이번엔 다른 접근을 고려해보세요."
        
        # 가장 최근 유사 결정
        recent = decisions[-1]
        days_ago = (datetime.now() - recent.decision_date).days
        msg += f"\n\n🕐 가장 최근: {days_ago}일 전 {recent.ticker}에서 '{recent.decision_type.value}' 결정"
        
        return msg
    
    def _calculate_condition_score(self, decisions: List[InvestmentDecision], condition_type: str) -> float:
        """특정 조건에서의 점수 계산"""
        if not decisions:
            return 50.0  # 기본값
        
        good_decisions = 0
        for d in decisions:
            if condition_type == "fear":
                # 공포 구간에서 홀딩/매수 = 좋은 결정 (보통)
                if d.decision_type in [DecisionType.HOLD, DecisionType.BUY, DecisionType.ADD_POSITION]:
                    good_decisions += 1
            elif condition_type == "greed":
                # 탐욕 구간에서 홀딩/매도 = 좋은 결정 (보통)
                if d.decision_type in [DecisionType.HOLD, DecisionType.SELL, DecisionType.TAKE_PROFIT]:
                    good_decisions += 1
        
        return (good_decisions / len(decisions)) * 100
    
    def _calculate_consistency_score(self) -> float:
        """전략 일관성 점수 계산"""
        if len(self.decisions) < 2:
            return 50.0
        
        # 같은 티커에서 같은 조건에 같은 결정을 했는지
        consistent_count = 0
        compared = 0
        
        ticker_conditions = {}
        for d in self.decisions:
            key = (d.ticker, d.market_condition)
            if key in ticker_conditions:
                if ticker_conditions[key] == d.decision_type:
                    consistent_count += 1
                compared += 1
            ticker_conditions[key] = d.decision_type
        
        if compared == 0:
            return 50.0
        
        return (consistent_count / compared) * 100
    
    def get_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """결정 이력 조회"""
        return [d.to_dict() for d in self.decisions[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 요약"""
        if not self.decisions:
            return {"total_decisions": 0}
        
        return {
            "total_decisions": len(self.decisions),
            "by_type": {
                t.value: sum(1 for d in self.decisions if d.decision_type == t)
                for t in DecisionType
            },
            "by_condition": {
                c.value: sum(1 for d in self.decisions if d.market_condition == c)
                for c in MarketCondition
            },
            "ai_followed_rate": sum(1 for d in self.decisions if d.followed_ai) / len(self.decisions)
        }


# 사용자별 메모리 캐시 (간단한 in-memory)
_user_memories: Dict[str, InvestmentJourneyMemory] = {}


def get_journey_memory(user_id: str) -> InvestmentJourneyMemory:
    """사용자별 Journey Memory 인스턴스 반환"""
    if user_id not in _user_memories:
        _user_memories[user_id] = InvestmentJourneyMemory(user_id=user_id)
    return _user_memories[user_id]


# 테스트용
if __name__ == "__main__":
    memory = InvestmentJourneyMemory(user_id="test_user")
    
    print("=== Investment Journey Memory Test ===\n")
    
    # 과거 결정 기록
    memory.record_decision(
        ticker="AAPL",
        decision_type="panic_sell",
        market_condition="fear",
        entry_price=150.0,
        quantity=10,
        reasoning="시장 폭락 무서워서 매도"
    )
    
    memory.record_decision(
        ticker="NVDA",
        decision_type="hold",
        market_condition="fear",
        entry_price=400.0,
        quantity=5,
        reasoning="장기 투자 관점 유지",
        ai_recommendation="hold",
        followed_ai=True
    )
    
    memory.record_decision(
        ticker="TSLA",
        decision_type="fomo_buy",
        market_condition="greed",
        entry_price=300.0,
        quantity=3,
        reasoning="다들 사니까 나도"
    )
    
    # 결과 업데이트 시뮬레이션
    memory.update_outcome("test_user_AAPL_20260105120000", 180.0, 30)
    
    # 코칭 받기
    coaching = memory.get_coaching("AAPL", "fear")
    print(f"Coaching: {coaching.message}")
    print(f"Confidence: {coaching.confidence:.0%}")
    
    # 품질 점수
    score = memory.get_quality_score()
    print(f"\nQuality Scores:")
    print(f"  Fear Response: {score.fear_response_score:.0f}")
    print(f"  Greed Response: {score.greed_response_score:.0f}")
    print(f"  Consistency: {score.consistency_score:.0f}")
    print(f"  Discipline: {score.discipline_score:.0f}")
    print(f"  Overall: {score.overall_score:.0f}")
    for insight in score.insights:
        print(f"  💡 {insight}")
