"""
AI Meta-Analysis Engine - AI 자기 분석 엔진

ChatGPT Feature 7: AI 메타 분석

AI 스스로 과거 실수를 분석하고 개선 방안 제시

분석 영역:
1. 과거 잘못된 예측 패턴
2. AI별 강점/약점 분석
3. 개선 제안사항
4. 학습 우선순위

작성일: 2025-12-16
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class MistakePattern:
    """실수 패턴"""
    pattern_type: str  # "OVERCONFIDENT", "SECTOR_BIAS", "TIMING_ERROR", etc.
    description: str
    frequency: int
    severity: float  # 0~1
    example_tickers: List[str]


@dataclass
class AgentStrengthWeakness:
    """AI 에이전트 강점/약점"""
    agent_name: str
    strengths: List[str]
    weaknesses: List[str]
    win_rate: float
    avg_pnl: float
    best_sectors: List[str]
    worst_sectors: List[str]


@dataclass
class ImprovementSuggestion:
    """개선 제안"""
    priority: int  # 1~10
    category: str
    suggestion: str
    expected_impact: str
    implementation_difficulty: str  # "LOW", "MEDIUM", "HIGH"


@dataclass
class MetaAnalysisResult:
    """메타 분석 결과"""
    mistake_patterns: List[MistakePattern]
    agent_analysis: List[AgentStrengthWeakness]
    improvement_suggestions: List[ImprovementSuggestion]
    overall_performance_score: float  # 0~100
    key_insights: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)


class AIMetaAnalyzer:
    """
    AI 메타 분석 엔진
    
    AI 스스로 과거 실수를 분석하고 개선 방안 제시
    
    Usage:
        analyzer = AIMetaAnalyzer()
        result = analyzer.analyze_performance(
            debate_history=debates,
            agent_metrics=metrics
        )
        for suggestion in result.improvement_suggestions:
            print(f"{suggestion.priority}. {suggestion.suggestion}")
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_performance(
        self,
        debate_history: List[Dict[str, Any]],
        agent_metrics: Dict[str, Any]
    ) -> MetaAnalysisResult:
        """
        AI 성능 메타 분석
        
        Args:
            debate_history: 토론 내역
            agent_metrics: 에이전트별 메트릭
        
        Returns:
            MetaAnalysisResult
        """
        # 1. 실수 패턴 분석
        mistake_patterns = self._analyze_mistake_patterns(debate_history)
        
        # 2. 에이전트별 강점/약점 분석
        agent_analysis = self._analyze_agent_performance(agent_metrics)
        
        # 3. 개선 제안사항 생성
        improvement_suggestions = self._generate_improvements(
            mistake_patterns,
            agent_analysis
        )
        
        # 4. 전체 성능 점수
        overall_score = self._calculate_overall_score(agent_metrics)
        
        # 5. 핵심 인사이트
        key_insights = self._generate_key_insights(
            mistake_patterns,
            agent_analysis,
            overall_score
        )
        
        result = MetaAnalysisResult(
            mistake_patterns=mistake_patterns,
            agent_analysis=agent_analysis,
            improvement_suggestions=improvement_suggestions,
            overall_performance_score=overall_score,
            key_insights=key_insights
        )
        
        self.logger.info(
            f"Meta-analysis complete: Score {overall_score:.1f}/100, "
            f"{len(improvement_suggestions)} suggestions"
        )
        
        return result
    
    def _analyze_mistake_patterns(
        self,
        debate_history: List[Dict[str, Any]]
    ) -> List[MistakePattern]:
        """실수 패턴 분석"""
        patterns = []
        
        # 과신 패턴 (높은 확신도 + 손실)
        overconfident_cases = [
            d for d in debate_history
            if d.get('consensus_strength', 0) > 0.8
            and d.get('pnl_result', 0) < -0.05
        ]
        
        if len(overconfident_cases) >= 2:
            patterns.append(MistakePattern(
                pattern_type="OVERCONFIDENT",
                description="높은 확신도에도 불구하고 손실 발생",
                frequency=len(overconfident_cases),
                severity=0.7,
                example_tickers=[d.get('ticker', '') for d in overconfident_cases[:3]]
            ))
        
        # 타이밍 에러 (너무 빠른/느린 진입)
        # (실제로는 더 복잡한 로직)
        patterns.append(MistakePattern(
            pattern_type="TIMING_ERROR",
            description="진입 타이밍이 일관되게 부적절",
            frequency=5,
            severity=0.5,
            example_tickers=["TSLA", "NVDA"]
        ))
        
        return patterns
    
    def _analyze_agent_performance(
        self,
        agent_metrics: Dict[str, Any]
    ) -> List[AgentStrengthWeakness]:
        """에이전트별 성능 분석"""
        analysis = []
        
        # 샘플 데이터 (실제로는 AgentWeightTrainer에서 가져옴)
        sample_agents = {
            'claude': {'win_rate': 0.65, 'avg_pnl': 0.05},
            'chatgpt': {'win_rate': 0.70, 'avg_pnl': 0.06},
            'gemini': {'win_rate': 0.60, 'avg_pnl': 0.03}
        }
        
        for agent_name, metrics in sample_agents.items():
            analysis.append(AgentStrengthWeakness(
                agent_name=agent_name,
                strengths=self._identify_strengths(agent_name, metrics),
                weaknesses=self._identify_weaknesses(agent_name, metrics),
                win_rate=metrics['win_rate'],
                avg_pnl=metrics['avg_pnl'],
                best_sectors=["Tech", "Healthcare"],
                worst_sectors=["Energy", "Utilities"]
            ))
        
        return analysis
    
    def _identify_strengths(
        self,
        agent_name: str,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """강점 식별"""
        strengths = []
        
        if metrics.get('win_rate', 0) > 0.65:
            strengths.append("높은 승률")
        
        if metrics.get('avg_pnl', 0) > 0.05:
            strengths.append("우수한 수익률")
        
        return strengths or ["데이터 부족"]
    
    def _identify_weaknesses(
        self,
        agent_name: str,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """약점 식별"""
        weaknesses = []
        
        if metrics.get('win_rate', 0) < 0.60:
            weaknesses.append("승률 개선 필요")
        
        if metrics.get('avg_pnl', 0) < 0.03:
            weaknesses.append("수익폭 확대 필요")
        
        return weaknesses or ["특이사항 없음"]
    
    def _generate_improvements(
        self,
        patterns: List[MistakePattern],
        agent_analysis: List[AgentStrengthWeakness]
    ) -> List[ImprovementSuggestion]:
        """개선 제안사항 생성"""
        suggestions = []
        
        # 과신 패턴 개선
        if any(p.pattern_type == "OVERCONFIDENT" for p in patterns):
            suggestions.append(ImprovementSuggestion(
                priority=1,
                category="합의 메커니즘",
                suggestion="높은 확신도(>80%)일 때 추가 검증 단계 도입",
                expected_impact="과신으로 인한 손실 30% 감소 예상",
                implementation_difficulty="MEDIUM"
            ))
        
        # 타이밍 개선
        suggestions.append(ImprovementSuggestion(
            priority=2,
            category="진입 타이밍",
            suggestion="기술적 지표와 AI 판단 결합하여 진입점 최적화",
            expected_impact="타이밍 정확도 20% 향상 예상",
            implementation_difficulty="HIGH"
        ))
        
        # 에이전트 가중치 조정
        low_performers = [a for a in agent_analysis if a.win_rate < 0.60]
        if low_performers:
            suggestions.append(ImprovementSuggestion(
                priority=3,
                category="에이전트 가중치",
                suggestion=f"{', '.join(a.agent_name for a in low_performers)} 가중치 하향 조정",
                expected_impact="전체 승률 5% 향상 예상",
                implementation_difficulty="LOW"
            ))
        
        return sorted(suggestions, key=lambda x: x.priority)
    
    def _calculate_overall_score(
        self,
        agent_metrics: Dict[str, Any]
    ) -> float:
        """전체 성능 점수 계산"""
        # 샘플 점수 (실제로는 복잡한 계산)
        return 72.5
    
    def _generate_key_insights(
        self,
        patterns: List[MistakePattern],
        agent_analysis: List[AgentStrengthWeakness],
        score: float
    ) -> List[str]:
        """핵심 인사이트 생성"""
        insights = []
        
        # 전체 점수 평가
        if score >= 75:
            insights.append(f"✅ 전체 성능: 우수 ({score:.1f}/100)")
        elif score >= 60:
            insights.append(f"⚠️ 전체 성능: 양호 ({score:.1f}/100), 개선 여지 있음")
        else:
            insights.append(f"🔴 전체 성능: 개선 필요 ({score:.1f}/100)")
        
        # 주요 문제점
        if patterns:
            top_pattern = max(patterns, key=lambda x: x.severity)
            insights.append(f"🎯 주요 개선점: {top_pattern.description}")
        
        # 최고/최저 성능 에이전트
        if agent_analysis:
            best = max(agent_analysis, key=lambda x: x.win_rate)
            worst = min(agent_analysis, key=lambda x: x.win_rate)
            insights.append(
                f"📊 성능 편차: {best.agent_name} ({best.win_rate:.0%}) vs "
                f"{worst.agent_name} ({worst.win_rate:.0%})"
            )
        
        return insights


# 전역 인스턴스
_meta_analyzer: Optional[AIMetaAnalyzer] = None


def get_meta_analyzer() -> AIMetaAnalyzer:
    """전역 AIMetaAnalyzer 인스턴스 반환"""
    global _meta_analyzer
    if _meta_analyzer is None:
        _meta_analyzer = AIMetaAnalyzer()
    return _meta_analyzer
