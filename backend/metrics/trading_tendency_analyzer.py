"""
Trading Tendency Analyzer - 거래 성향 분석기

ChatGPT Feature 6: 거래 성향 지표

사용자의 거래 패턴을 분석하여 보수적 ↔ 공격적 성향을 점수화

분석 요소:
1. Position Size (포지션 크기)
2. Holding Period (보유 기간)
3. Risk Level (위험 수준)
4. Diversification (분산 정도)
5. Reaction Speed (반응 속도)

작성일: 2025-12-16
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TendencyLevel(Enum):
    """거래 성향 레벨"""
    VERY_CONSERVATIVE = "매우 보수적"
    CONSERVATIVE = "보수적"
    MODERATE = "중립적"
    AGGRESSIVE = "공격적"
    VERY_AGGRESSIVE = "매우 공격적"


@dataclass
class TradeAction:
    """거래 액션"""
    ticker: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    price: float
    timestamp: datetime
    portfolio_percentage: float  # 포트폴리오 대비 비중


@dataclass
class TendencyMetrics:
    """성향 메트릭"""
    position_size_score: float  # 0~100 (포지션 크기)
    holding_period_score: float  # 0~100 (보유 기간)
    risk_level_score: float  # 0~100 (위험 수준)
    diversification_score: float  # 0~100 (분산 정도)
    reaction_speed_score: float  # 0~100 (반응 속도)
    
    def overall_score(self) -> float:
        """전체 성향 점수 (0: 보수적, 100: 공격적)"""
        return (
            self.position_size_score * 0.3 +
            self.holding_period_score * 0.2 +
            self.risk_level_score * 0.25 +
            self.diversification_score * 0.15 +
            self.reaction_speed_score * 0.1
        )


@dataclass
class TendencyResult:
    """성향 분석 결과"""
    tendency_score: float  # 0~100
    tendency_level: TendencyLevel
    metrics: TendencyMetrics
    insights: List[str]
    recommendations: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)


class TradingTendencyAnalyzer:
    """
    거래 성향 분석기
    
    사용자의 거래 패턴을 분석하여 보수적 ↔ 공격적 성향 점수 제공
    
    Usage:
        analyzer = TradingTendencyAnalyzer()
        result = analyzer.analyze_tendency(
            trade_history=trades,
            current_portfolio=portfolio
        )
        print(f"성향: {result.tendency_level.value}")
        print(f"점수: {result.tendency_score:.1f}/100")
    """
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_tendency(
        self,
        trade_history: List[TradeAction],
        current_portfolio: Dict[str, Any]
    ) -> TendencyResult:
        """
        거래 성향 분석
        
        Args:
            trade_history: 거래 내역 리스트
            current_portfolio: 현재 포트폴리오
        
        Returns:
            TendencyResult
        """
        # 1. Position Size 분석
        position_size_score = self._analyze_position_size(trade_history)
        
        # 2. Holding Period 분석
        holding_period_score = self._analyze_holding_period(trade_history)
        
        # 3. Risk Level 분석
        risk_level_score = self._analyze_risk_level(current_portfolio)
        
        # 4. Diversification 분석
        diversification_score = self._analyze_diversification(current_portfolio)
        
        # 5. Reaction Speed 분석
        reaction_speed_score = self._analyze_reaction_speed(trade_history)
        
        # Metrics 생성
        metrics = TendencyMetrics(
            position_size_score=position_size_score,
            holding_period_score=holding_period_score,
            risk_level_score=risk_level_score,
            diversification_score=diversification_score,
            reaction_speed_score=reaction_speed_score
        )
        
        # 전체 점수
        tendency_score = metrics.overall_score()
        
        # 레벨 결정
        tendency_level = self._determine_level(tendency_score)
        
        # 인사이트 생성
        insights = self._generate_insights(metrics, tendency_score)
        
        # 추천사항 생성
        recommendations = self._generate_recommendations(tendency_score, metrics)
        
        result = TendencyResult(
            tendency_score=tendency_score,
            tendency_level=tendency_level,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations
        )
        
        self.logger.info(
            f"Tendency Analysis: {tendency_level.value} "
            f"(Score: {tendency_score:.1f}/100)"
        )
        
        return result
    
    def _analyze_position_size(self, trade_history: List[TradeAction]) -> float:
        """포지션 크기 분석 (작을수록 보수적)"""
        if not trade_history:
            return 50.0
        
        avg_position_pct = sum(t.portfolio_percentage for t in trade_history) / len(trade_history)
        
        # 5% 이하: 보수적 (0~30)
        # 10% : 중립 (50)
        # 20% 이상: 공격적 (70~100)
        if avg_position_pct <= 5:
            return min(avg_position_pct * 6, 30)  # 0~30
        elif avg_position_pct <= 10:
            return 30 + (avg_position_pct - 5) * 4  # 30~50
        elif avg_position_pct <= 20:
            return 50 + (avg_position_pct - 10) * 2  # 50~70
        else:
            return min(70 + (avg_position_pct - 20) * 1.5, 100)
    
    def _analyze_holding_period(self, trade_history: List[TradeAction]) -> float:
        """보유 기간 분석 (길수록 보수적)"""
        if len(trade_history) < 2:
            return 50.0
        
        # 매수 후 매도까지 평균 기간 계산 (샘플)
        # 실제로는 실제 보유 기간 계산 필요
        
        # 1일 이하: 공격적 (80~100)
        # 1주일: 중립 (50)
        # 1개월 이상: 보수적 (0~30)
        
        avg_days = 7  # 샘플: 평균 7일 보유
        
        if avg_days <= 1:
            return 90
        elif avg_days <= 7:
            return 80 - (avg_days - 1) * 5  # 80~50
        elif avg_days <= 30:
            return 50 - (avg_days - 7) * 1.5  # 50~15
        else:
            return max(15 - (avg_days - 30) * 0.5, 0)
    
    def _analyze_risk_level(self, portfolio: Dict[str, Any]) -> float:
        """위험 수준 분석 (변동성 높을수록 공격적)"""
        # 포트폴리오 Beta, 변동성 등 분석
        # 샘플: 중립
        return 50.0
    
    def _analyze_diversification(self, portfolio: Dict[str, Any]) -> float:
        """분산 정도 분석 (집중될수록 공격적)"""
        positions = portfolio.get('positions', [])
        
        if not positions:
            return 50.0
        
        num_positions = len(positions)
        
        # 1~3 종목: 공격적 (70~100)
        # 5~10 종목: 중립 (50)
        # 20+ 종목: 보수적 (0~30)
        
        if num_positions <= 3:
            return 100 - num_positions * 10
        elif num_positions <= 10:
            return 70 - (num_positions - 3) * 3
        elif num_positions <= 20:
            return 50 - (num_positions - 10) * 2
        else:
            return max(30 - (num_positions - 20) * 1, 0)
    
    def _analyze_reaction_speed(self, trade_history: List[TradeAction]) -> float:
        """반응 속도 분석 (빠를수록 공격적)"""
        # 뉴스/신호 후 거래까지 시간 분석
        # 샘플: 중립
        return 50.0
    
    def _determine_level(self, score: float) -> TendencyLevel:
        """점수에 따른 레벨 결정"""
        if score < 20:
            return TendencyLevel.VERY_CONSERVATIVE
        elif score < 40:
            return TendencyLevel.CONSERVATIVE
        elif score < 60:
            return TendencyLevel.MODERATE
        elif score < 80:
            return TendencyLevel.AGGRESSIVE
        else:
            return TendencyLevel.VERY_AGGRESSIVE
    
    def _generate_insights(self, metrics: TendencyMetrics, score: float) -> List[str]:
        """인사이트 생성"""
        insights = []
        
        # Position Size
        if metrics.position_size_score < 30:
            insights.append("포지션 크기가 매우 작습니다 (보수적)")
        elif metrics.position_size_score > 70:
            insights.append("포지션 크기가 큽니다 (공격적)")
        
        # Diversification
        if metrics.diversification_score < 30:
            insights.append("종목이 많이 분산되어 있습니다")
        elif metrics.diversification_score > 70:
            insights.append("소수 종목에 집중되어 있습니다")
        
        # Overall
        if score < 40:
            insights.append("전반적으로 신중하고 안정적인 투자 스타일입니다")
        elif score > 60:
            insights.append("전반적으로 적극적이고 기회 포착형 스타일입니다")
        
        return insights
    
    def _generate_recommendations(
        self,
        score: float,
        metrics: TendencyMetrics
    ) -> List[str]:
        """추천사항 생성"""
        recommendations = []
        
        if score < 30:
            recommendations.append("💡 너무 보수적일 수 있습니다. 검증된 기회에는 조금 더 과감하게 접근해보세요.")
        elif score > 70:
            recommendations.append("⚠️ 공격적인 스타일입니다. 포지션 크기와 분산을 점검해보세요.")
        
        if metrics.diversification_score > 80:
            recommendations.append("💡 집중도가 높습니다. 분산 투자로 리스크를 낮출 수 있습니다.")
        
        if metrics.position_size_score > 80:
            recommendations.append("⚠️ 개별 포지션이 큽니다. 1종목 비중 10% 이하를 권장합니다.")
        
        return recommendations


# 전역 인스턴스
_tendency_analyzer: Optional[TradingTendencyAnalyzer] = None


def get_tendency_analyzer() -> TradingTendencyAnalyzer:
    """전역 TradingTendencyAnalyzer 인스턴스 반환"""
    global _tendency_analyzer
    if _tendency_analyzer is None:
        _tendency_analyzer = TradingTendencyAnalyzer()
    return _tendency_analyzer
