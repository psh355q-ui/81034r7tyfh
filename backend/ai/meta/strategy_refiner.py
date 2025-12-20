"""
Strategy Refiner - 전략 자기 개선 시스템

Phase F4: 자율 진화 시스템

AI가 스스로 성과를 분석하고 전략 개선안을 생성

핵심 기능:
- 일일/주간 성과 분석
- "반성문 및 개선안" 생성
- Config/Prompt 수정 제안
- 자동 학습 및 최적화

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 스키마 정의
# ═══════════════════════════════════════════════════════════════

class ReviewPeriod(str, Enum):
    """리뷰 기간"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ImprovementType(str, Enum):
    """개선 유형"""
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    PARAMETER_TUNING = "parameter_tuning"
    PROMPT_MODIFICATION = "prompt_modification"
    STRATEGY_CHANGE = "strategy_change"
    RISK_RULE = "risk_rule"


class Priority(str, Enum):
    """우선순위"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TradeRecord:
    """거래 기록"""
    trade_id: str
    ticker: str
    action: str  # BUY, SELL, HOLD
    entry_price: float
    exit_price: Optional[float]
    pnl: float  # 손익 (%)
    ai_votes: Dict[str, str]  # {"claude": "BUY", "chatgpt": "HOLD", "gemini": "BUY"}
    ai_confidences: Dict[str, float]
    timestamp: datetime
    holding_period_days: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "ticker": self.ticker,
            "action": self.action,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "ai_votes": self.ai_votes,
            "ai_confidences": self.ai_confidences,
            "timestamp": self.timestamp.isoformat(),
            "holding_period_days": self.holding_period_days
        }


@dataclass
class PerformanceSnapshot:
    """성과 스냅샷"""
    period: ReviewPeriod
    start_date: date
    end_date: date
    
    # 전체 성과
    total_trades: int
    win_count: int
    loss_count: int
    win_rate: float
    total_return: float  # %
    avg_return: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    
    # AI별 성과
    agent_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # 패턴 분석
    best_performing_tickers: List[str] = field(default_factory=list)
    worst_performing_tickers: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period.value,
            "date_range": f"{self.start_date} ~ {self.end_date}",
            "overall": {
                "total_trades": self.total_trades,
                "win_rate": self.win_rate,
                "total_return": self.total_return,
                "avg_return": self.avg_return,
                "max_drawdown": self.max_drawdown,
                "sharpe_ratio": self.sharpe_ratio
            },
            "agents": self.agent_performance,
            "analysis": {
                "best_tickers": self.best_performing_tickers,
                "worst_tickers": self.worst_performing_tickers,
                "mistakes": self.common_mistakes
            }
        }


@dataclass
class ImprovementSuggestion:
    """개선 제안"""
    id: str
    improvement_type: ImprovementType
    priority: Priority
    title: str
    description: str
    rationale: str
    expected_impact: str
    implementation: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.improvement_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "expected_impact": self.expected_impact,
            "implementation": self.implementation,
            "applied": self.applied
        }


@dataclass
class ReflectionReport:
    """반성문 및 개선안 보고서"""
    period: ReviewPeriod
    generated_at: datetime
    performance: PerformanceSnapshot
    
    # 분석
    key_findings: List[str]
    lessons_learned: List[str]
    
    # 개선안
    suggestions: List[ImprovementSuggestion]
    
    # 요약
    summary: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period.value,
            "generated_at": self.generated_at.isoformat(),
            "performance": self.performance.to_dict(),
            "findings": self.key_findings,
            "lessons": self.lessons_learned,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "summary": self.summary,
            "confidence": self.confidence
        }


# ═══════════════════════════════════════════════════════════════
# Strategy Refiner 클래스
# ═══════════════════════════════════════════════════════════════

class StrategyRefiner:
    """
    전략 자기 개선 시스템
    
    Usage:
        refiner = StrategyRefiner()
        
        # 거래 기록 추가
        refiner.add_trade(trade_record)
        
        # 일일 리뷰
        daily_report = refiner.generate_daily_review()
        
        # 주간 리뷰
        weekly_report = refiner.generate_weekly_review()
        
        # 개선안 적용
        for suggestion in weekly_report.suggestions:
            if suggestion.priority == Priority.CRITICAL:
                refiner.apply_suggestion(suggestion)
    """
    
    # 성과 기준값
    TARGET_WIN_RATE = 0.55
    TARGET_AVG_RETURN = 0.02  # 2%
    MAX_ACCEPTABLE_DD = 0.15  # 15%
    
    def __init__(self, data_dir: Optional[Path] = None):
        """초기화"""
        self.data_dir = data_dir or Path("data/evolution")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._trades: List[TradeRecord] = []
        self._reports: List[ReflectionReport] = []
        self._applied_suggestions: List[ImprovementSuggestion] = []
        
        logger.info("StrategyRefiner initialized")
    
    def add_trade(self, trade: TradeRecord):
        """거래 기록 추가"""
        self._trades.append(trade)
        logger.debug(f"Added trade: {trade.ticker} {trade.action} PnL: {trade.pnl:.2%}")
    
    def add_trades(self, trades: List[TradeRecord]):
        """여러 거래 기록 추가"""
        self._trades.extend(trades)
    
    def get_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TradeRecord]:
        """기간별 거래 조회"""
        trades = self._trades
        
        if start_date:
            trades = [t for t in trades if t.timestamp.date() >= start_date]
        if end_date:
            trades = [t for t in trades if t.timestamp.date() <= end_date]
        
        return trades
    
    def calculate_performance(
        self,
        trades: List[TradeRecord],
        period: ReviewPeriod
    ) -> PerformanceSnapshot:
        """성과 계산"""
        if not trades:
            return PerformanceSnapshot(
                period=period,
                start_date=date.today(),
                end_date=date.today(),
                total_trades=0,
                win_count=0,
                loss_count=0,
                win_rate=0.0,
                total_return=0.0,
                avg_return=0.0,
                max_drawdown=0.0
            )
        
        # 기본 통계
        win_trades = [t for t in trades if t.pnl > 0]
        loss_trades = [t for t in trades if t.pnl <= 0]
        
        total_trades = len(trades)
        win_count = len(win_trades)
        loss_count = len(loss_trades)
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        returns = [t.pnl for t in trades]
        total_return = sum(returns)
        avg_return = total_return / total_trades if total_trades > 0 else 0
        
        # Max Drawdown 계산 (간소화)
        cumulative = 0
        peak = 0
        max_dd = 0
        for r in returns:
            cumulative += r
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # AI별 성과
        agent_perf = self._calculate_agent_performance(trades)
        
        # 티커별 분석
        ticker_returns = {}
        for t in trades:
            if t.ticker not in ticker_returns:
                ticker_returns[t.ticker] = []
            ticker_returns[t.ticker].append(t.pnl)
        
        ticker_avg = {
            ticker: sum(rets) / len(rets)
            for ticker, rets in ticker_returns.items()
        }
        sorted_tickers = sorted(ticker_avg.items(), key=lambda x: x[1], reverse=True)
        
        # 공통 실수 분석
        mistakes = self._analyze_common_mistakes(trades)
        
        return PerformanceSnapshot(
            period=period,
            start_date=min(t.timestamp.date() for t in trades),
            end_date=max(t.timestamp.date() for t in trades),
            total_trades=total_trades,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_rate,
            total_return=total_return,
            avg_return=avg_return,
            max_drawdown=max_dd,
            agent_performance=agent_perf,
            best_performing_tickers=[t[0] for t in sorted_tickers[:3]],
            worst_performing_tickers=[t[0] for t in sorted_tickers[-3:]],
            common_mistakes=mistakes
        )
    
    def _calculate_agent_performance(
        self,
        trades: List[TradeRecord]
    ) -> Dict[str, Dict[str, float]]:
        """AI 에이전트별 성과 계산"""
        agents = ["claude", "chatgpt", "gemini"]
        result = {}
        
        for agent in agents:
            correct_calls = 0
            total_calls = 0
            confidence_sum = 0
            
            for trade in trades:
                if agent not in trade.ai_votes:
                    continue
                
                total_calls += 1
                vote = trade.ai_votes[agent]
                confidence = trade.ai_confidences.get(agent, 0.5)
                confidence_sum += confidence
                
                # 올바른 콜인지 확인
                if trade.pnl > 0:
                    if vote in ["BUY", "INCREASE"] and trade.action == "BUY":
                        correct_calls += 1
                    elif vote in ["SELL", "REDUCE"] and trade.action == "SELL":
                        correct_calls += 1
                elif trade.pnl < 0:
                    if vote in ["SELL", "REDUCE", "HOLD"] and trade.action == "BUY":
                        correct_calls += 1  # 매수 반대가 맞았음
            
            accuracy = correct_calls / total_calls if total_calls > 0 else 0
            avg_confidence = confidence_sum / total_calls if total_calls > 0 else 0
            
            result[agent] = {
                "accuracy": accuracy,
                "total_calls": total_calls,
                "avg_confidence": avg_confidence
            }
        
        return result
    
    def _analyze_common_mistakes(self, trades: List[TradeRecord]) -> List[str]:
        """공통 실수 분석"""
        mistakes = []
        
        loss_trades = [t for t in trades if t.pnl < 0]
        if not loss_trades:
            return ["손실 거래 없음"]
        
        # 높은 신뢰도 손실
        high_conf_losses = [
            t for t in loss_trades
            if max(t.ai_confidences.values(), default=0) > 0.8
        ]
        if len(high_conf_losses) >= 3:
            mistakes.append(f"높은 신뢰도 손실 {len(high_conf_losses)}건: 과신 경향")
        
        # 짧은 보유기간 손실
        short_hold_losses = [
            t for t in loss_trades
            if t.holding_period_days < 3
        ]
        if len(short_hold_losses) >= 3:
            mistakes.append(f"단기 손절 {len(short_hold_losses)}건: 조급한 청산")
        
        # 만장일치 손실
        unanimous_losses = [
            t for t in loss_trades
            if len(set(t.ai_votes.values())) == 1
        ]
        if len(unanimous_losses) >= 2:
            mistakes.append(f"만장일치 손실 {len(unanimous_losses)}건: 그룹씽크 위험")
        
        return mistakes if mistakes else ["특별한 패턴 없음"]
    
    def generate_review(
        self,
        period: ReviewPeriod = ReviewPeriod.DAILY
    ) -> ReflectionReport:
        """리뷰 보고서 생성"""
        # 기간 설정
        end_date = date.today()
        if period == ReviewPeriod.DAILY:
            start_date = end_date - timedelta(days=1)
        elif period == ReviewPeriod.WEEKLY:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 거래 조회
        trades = self.get_trades(start_date, end_date)
        
        # 성과 계산
        performance = self.calculate_performance(trades, period)
        
        # 핵심 발견사항
        findings = self._generate_findings(performance)
        
        # 교훈
        lessons = self._generate_lessons(performance)
        
        # 개선 제안
        suggestions = self._generate_suggestions(performance)
        
        # 요약
        summary = self._generate_summary(performance, suggestions)
        
        report = ReflectionReport(
            period=period,
            generated_at=datetime.now(),
            performance=performance,
            key_findings=findings,
            lessons_learned=lessons,
            suggestions=suggestions,
            summary=summary,
            confidence=0.8
        )
        
        self._reports.append(report)
        
        # 저장
        self._save_report(report)
        
        return report
    
    def generate_daily_review(self) -> ReflectionReport:
        """일일 리뷰"""
        return self.generate_review(ReviewPeriod.DAILY)
    
    def generate_weekly_review(self) -> ReflectionReport:
        """주간 리뷰"""
        return self.generate_review(ReviewPeriod.WEEKLY)
    
    def _generate_findings(self, perf: PerformanceSnapshot) -> List[str]:
        """핵심 발견사항 생성"""
        findings = []
        
        if perf.total_trades == 0:
            return ["거래 없음"]
        
        # 승률 분석
        if perf.win_rate >= 0.6:
            findings.append(f"높은 승률 {perf.win_rate:.1%}: 전략 효과적")
        elif perf.win_rate < 0.4:
            findings.append(f"낮은 승률 {perf.win_rate:.1%}: 전략 재검토 필요")
        
        # 수익률 분석
        if perf.avg_return > 0.03:
            findings.append(f"우수한 평균 수익률 {perf.avg_return:.2%}")
        elif perf.avg_return < -0.02:
            findings.append(f"손실 {perf.avg_return:.2%}: 리스크 관리 강화 필요")
        
        # Drawdown 분석
        if perf.max_drawdown > self.MAX_ACCEPTABLE_DD:
            findings.append(f"과도한 드로다운 {perf.max_drawdown:.2%}")
        
        # AI 성과 분석
        for agent, data in perf.agent_performance.items():
            if data.get("accuracy", 0) < 0.4:
                findings.append(f"{agent} 정확도 낮음: {data['accuracy']:.1%}")
        
        return findings if findings else ["특별 사항 없음"]
    
    def _generate_lessons(self, perf: PerformanceSnapshot) -> List[str]:
        """교훈 생성"""
        lessons = []
        
        if perf.common_mistakes:
            for mistake in perf.common_mistakes[:3]:
                lessons.append(f"교훈: {mistake} → 주의 필요")
        
        if perf.worst_performing_tickers:
            lessons.append(f"피해야 할 종목 패턴: {', '.join(perf.worst_performing_tickers[:2])}")
        
        if perf.best_performing_tickers:
            lessons.append(f"강점: {', '.join(perf.best_performing_tickers[:2])} 분석 우수")
        
        return lessons if lessons else ["특별한 교훈 없음"]
    
    def _generate_suggestions(
        self,
        perf: PerformanceSnapshot
    ) -> List[ImprovementSuggestion]:
        """개선 제안 생성"""
        suggestions = []
        suggestion_id = 0
        
        # 1. 가중치 조정 제안
        for agent, data in perf.agent_performance.items():
            accuracy = data.get("accuracy", 0.5)
            
            if accuracy < 0.4:
                suggestion_id += 1
                suggestions.append(ImprovementSuggestion(
                    id=f"sug_{suggestion_id}",
                    improvement_type=ImprovementType.WEIGHT_ADJUSTMENT,
                    priority=Priority.HIGH,
                    title=f"{agent} 가중치 하향",
                    description=f"{agent}의 정확도가 {accuracy:.1%}로 낮음. 가중치 감소 권장.",
                    rationale=f"지난 기간 {agent}가 여러 손실 거래에서 잘못된 판단",
                    expected_impact="전체 승률 2-5% 개선 예상",
                    implementation={
                        "agent": agent,
                        "current_weight": 1.0,
                        "suggested_weight": 0.7,
                        "method": "agent_weight_trainer.adjust_weight()"
                    }
                ))
            elif accuracy > 0.7:
                suggestion_id += 1
                suggestions.append(ImprovementSuggestion(
                    id=f"sug_{suggestion_id}",
                    improvement_type=ImprovementType.WEIGHT_ADJUSTMENT,
                    priority=Priority.MEDIUM,
                    title=f"{agent} 가중치 상향",
                    description=f"{agent}의 정확도가 {accuracy:.1%}로 우수. 가중치 증가 권장.",
                    rationale=f"지난 기간 {agent}가 일관된 정확한 판단",
                    expected_impact="전체 수익률 1-3% 개선 예상",
                    implementation={
                        "agent": agent,
                        "current_weight": 1.0,
                        "suggested_weight": 1.3,
                        "method": "agent_weight_trainer.adjust_weight()"
                    }
                ))
        
        # 2. 드로다운 높을 때 리스크 규칙
        if perf.max_drawdown > self.MAX_ACCEPTABLE_DD:
            suggestion_id += 1
            suggestions.append(ImprovementSuggestion(
                id=f"sug_{suggestion_id}",
                improvement_type=ImprovementType.RISK_RULE,
                priority=Priority.CRITICAL,
                title="손절매 기준 강화",
                description=f"드로다운 {perf.max_drawdown:.1%}가 기준 {self.MAX_ACCEPTABLE_DD:.0%} 초과",
                rationale="큰 손실 방지를 위해 조기 손절 필요",
                expected_impact="최대 손실 30-50% 감소 예상",
                implementation={
                    "config_key": "STOP_LOSS_THRESHOLD",
                    "current_value": 0.1,
                    "suggested_value": 0.07,
                    "method": "config.update()"
                }
            ))
        
        # 3. 승률 낮을 때 전략 변경
        if perf.win_rate < 0.4:
            suggestion_id += 1
            suggestions.append(ImprovementSuggestion(
                id=f"sug_{suggestion_id}",
                improvement_type=ImprovementType.STRATEGY_CHANGE,
                priority=Priority.HIGH,
                title="진입 조건 강화",
                description=f"승률 {perf.win_rate:.1%}가 목표 {self.TARGET_WIN_RATE:.0%} 미달",
                rationale="낮은 승률은 진입 신호가 부정확함을 의미",
                expected_impact="거래 수 -20%, 승률 +15% 예상",
                implementation={
                    "config_key": "MIN_CONSENSUS_STRENGTH",
                    "current_value": 0.6,
                    "suggested_value": 0.75,
                    "method": "consensus_engine.set_threshold()"
                }
            ))
        
        # 우선순위 정렬
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        suggestions.sort(key=lambda x: priority_order[x.priority])
        
        return suggestions
    
    def _generate_summary(
        self,
        perf: PerformanceSnapshot,
        suggestions: List[ImprovementSuggestion]
    ) -> str:
        """요약 생성"""
        parts = []
        
        # 성과 요약
        if perf.total_trades == 0:
            return "거래 없음. 분석 불가."
        
        status = "양호" if perf.win_rate >= 0.5 and perf.total_return >= 0 else "개선 필요"
        parts.append(f"전체 상태: {status}")
        parts.append(f"거래 {perf.total_trades}건, 승률 {perf.win_rate:.1%}, 수익률 {perf.total_return:.2%}")
        
        # 핵심 제안
        critical = [s for s in suggestions if s.priority == Priority.CRITICAL]
        if critical:
            parts.append(f"긴급 조치 필요: {critical[0].title}")
        
        return " | ".join(parts)
    
    def apply_suggestion(self, suggestion: ImprovementSuggestion) -> bool:
        """개선안 적용 (시뮬레이션)"""
        logger.info(f"Applying suggestion: {suggestion.title}")
        
        suggestion.applied = True
        self._applied_suggestions.append(suggestion)
        
        # 실제 적용은 각 모듈의 메서드 호출 필요
        # 여기서는 로깅만
        logger.info(f"Suggestion applied: {suggestion.implementation}")
        
        return True
    
    def _save_report(self, report: ReflectionReport):
        """보고서 저장"""
        filename = f"report_{report.period.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Report saved: {filepath}")
    
    def get_latest_report(
        self,
        period: Optional[ReviewPeriod] = None
    ) -> Optional[ReflectionReport]:
        """최근 보고서 조회"""
        reports = self._reports
        if period:
            reports = [r for r in reports if r.period == period]
        return reports[-1] if reports else None


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_strategy_refiner: Optional[StrategyRefiner] = None


def get_strategy_refiner() -> StrategyRefiner:
    """StrategyRefiner 싱글톤 인스턴스"""
    global _strategy_refiner
    if _strategy_refiner is None:
        _strategy_refiner = StrategyRefiner()
    return _strategy_refiner


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random
    
    refiner = StrategyRefiner()
    
    print("=== Strategy Refiner Test ===\n")
    
    # 테스트 거래 생성
    tickers = ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT"]
    for i in range(20):
        pnl = random.uniform(-0.15, 0.2)
        trade = TradeRecord(
            trade_id=f"trade_{i}",
            ticker=random.choice(tickers),
            action="BUY" if pnl > 0 else "SELL",
            entry_price=100,
            exit_price=100 * (1 + pnl),
            pnl=pnl,
            ai_votes={
                "claude": random.choice(["BUY", "SELL", "HOLD"]),
                "chatgpt": random.choice(["BUY", "SELL", "HOLD"]),
                "gemini": random.choice(["BUY", "SELL", "HOLD"])
            },
            ai_confidences={
                "claude": random.uniform(0.5, 0.95),
                "chatgpt": random.uniform(0.5, 0.95),
                "gemini": random.uniform(0.5, 0.95)
            },
            timestamp=datetime.now() - timedelta(days=random.randint(0, 7)),
            holding_period_days=random.randint(1, 10)
        )
        refiner.add_trade(trade)
    
    # 주간 리뷰 생성
    report = refiner.generate_weekly_review()
    
    print(f"Period: {report.period.value}")
    print(f"Summary: {report.summary}")
    print(f"\nFindings:")
    for f in report.key_findings:
        print(f"  - {f}")
    
    print(f"\nLessons:")
    for l in report.lessons_learned:
        print(f"  - {l}")
    
    print(f"\nSuggestions ({len(report.suggestions)}):")
    for s in report.suggestions[:5]:
        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        print(f"  {priority_emoji[s.priority.value]} [{s.priority.value}] {s.title}")
        print(f"     {s.description}")
