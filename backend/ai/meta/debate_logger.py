"""
Debate Logger - AI 토론 기록 시스템

Phase F1: AI 집단지성 고도화

AI들의 토론 과정과 결과를 구조화하여 저장하고, 
미래 학습과 분석을 위한 데이터 축적

저장 정보:
- 타임스탬프
- 티커/종목
- AI별 투표 및 논거
- 최종 결정
- PnL 결과 (사후 기록)
- 시장 변동성 컨텍스트

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 토론 로그 구조
# ═══════════════════════════════════════════════════════════════

class VoteType(str, Enum):
    """투표 유형"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    DCA = "DCA"
    STOP_LOSS = "STOP_LOSS"
    ABSTAIN = "ABSTAIN"


@dataclass
class AgentVote:
    """개별 AI 에이전트 투표"""
    agent_name: str
    vote: VoteType
    confidence: float
    reasoning: str
    role: Optional[str] = None  # AI 역할
    processing_time_ms: float = 0.0
    voted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "vote": self.vote.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "role": self.role,
            "processing_time_ms": self.processing_time_ms,
            "voted_at": self.voted_at.isoformat()
        }


@dataclass
class MarketContextSnapshot:
    """토론 시점 시장 컨텍스트 스냅샷"""
    price: float
    price_change_1d: Optional[float] = None
    price_change_5d: Optional[float] = None
    volume_ratio: Optional[float] = None  # 평균 대비 거래량
    volatility: Optional[float] = None
    vix: Optional[float] = None
    market_sentiment: Optional[str] = None  # bullish, bearish, neutral
    sector_trend: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass  
class DebateOutcome:
    """토론 결과 및 사후 검증"""
    final_decision: VoteType
    consensus_strength: float  # 0.0 ~ 1.0
    dissenting_agents: List[str] = field(default_factory=list)
    executed: bool = False
    execution_price: Optional[float] = None
    pnl_result: Optional[float] = None  # 사후 기록
    pnl_percentage: Optional[float] = None
    outcome_recorded_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_decision": self.final_decision.value,
            "consensus_strength": self.consensus_strength,
            "dissenting_agents": self.dissenting_agents,
            "executed": self.executed,
            "execution_price": self.execution_price,
            "pnl_result": self.pnl_result,
            "pnl_percentage": self.pnl_percentage,
            "outcome_recorded_at": (
                self.outcome_recorded_at.isoformat() 
                if self.outcome_recorded_at else None
            )
        }


@dataclass
class DebateRecord:
    """토론 전체 기록"""
    id: str
    timestamp: datetime
    ticker: str
    topic: str  # 토론 주제 (예: "BUY 결정", "실적 발표 대응")
    votes: List[AgentVote]
    context: MarketContextSnapshot
    outcome: DebateOutcome
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "ticker": self.ticker,
            "topic": self.topic,
            "votes": [v.to_dict() for v in self.votes],
            "context": self.context.to_dict(),
            "outcome": self.outcome.to_dict(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebateRecord":
        """딕셔너리에서 DebateRecord 생성"""
        votes = [
            AgentVote(
                agent_name=v["agent_name"],
                vote=VoteType(v["vote"]),
                confidence=v["confidence"],
                reasoning=v["reasoning"],
                role=v.get("role"),
                processing_time_ms=v.get("processing_time_ms", 0),
                voted_at=datetime.fromisoformat(v["voted_at"])
            )
            for v in data["votes"]
        ]
        
        context = MarketContextSnapshot(**data["context"])
        
        outcome_data = data["outcome"]
        outcome = DebateOutcome(
            final_decision=VoteType(outcome_data["final_decision"]),
            consensus_strength=outcome_data["consensus_strength"],
            dissenting_agents=outcome_data.get("dissenting_agents", []),
            executed=outcome_data.get("executed", False),
            execution_price=outcome_data.get("execution_price"),
            pnl_result=outcome_data.get("pnl_result"),
            pnl_percentage=outcome_data.get("pnl_percentage"),
            outcome_recorded_at=(
                datetime.fromisoformat(outcome_data["outcome_recorded_at"])
                if outcome_data.get("outcome_recorded_at") else None
            )
        )
        
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ticker=data["ticker"],
            topic=data["topic"],
            votes=votes,
            context=context,
            outcome=outcome,
            metadata=data.get("metadata", {})
        )


# ═══════════════════════════════════════════════════════════════
# Debate Logger 클래스
# ═══════════════════════════════════════════════════════════════

class DebateLogger:
    """
    AI 토론 기록 및 관리 시스템
    
    Usage:
        logger = DebateLogger()
        
        # 토론 기록
        record = logger.log_debate(
            ticker="NVDA",
            topic="BUY 결정",
            votes=[vote1, vote2, vote3],
            context=market_context,
            final_decision=VoteType.BUY,
            consensus_strength=0.85
        )
        
        # PnL 결과 업데이트
        logger.update_outcome(record.id, pnl_result=500.0, pnl_percentage=5.0)
        
        # 조회
        recent = logger.get_recent_debates(ticker="NVDA", limit=10)
        
        # 분석
        stats = logger.get_agent_performance("claude")
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        max_memory_records: int = 1000
    ):
        """
        Args:
            storage_path: 로그 파일 저장 경로 (None이면 메모리만)
            max_memory_records: 메모리에 유지할 최대 레코드 수
        """
        self.storage_path = storage_path
        self.max_memory_records = max_memory_records
        
        # 메모리 저장소
        self._records: Dict[str, DebateRecord] = {}
        self._records_by_ticker: Dict[str, List[str]] = {}
        
        # 통계
        self._stats = {
            "total_debates": 0,
            "by_decision": {},
            "by_ticker": {},
            "by_agent": {}
        }
        
        # 저장 경로 초기화
        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)
            self._load_existing_records()
        
        logger.info(f"DebateLogger initialized: storage={storage_path}")
    
    def _generate_id(self) -> str:
        """고유 ID 생성"""
        import uuid
        return f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def log_debate(
        self,
        ticker: str,
        topic: str,
        votes: List[AgentVote],
        context: MarketContextSnapshot,
        final_decision: VoteType,
        consensus_strength: float,
        dissenting_agents: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DebateRecord:
        """
        토론 기록
        
        Args:
            ticker: 종목 티커
            topic: 토론 주제
            votes: AI별 투표 목록
            context: 시장 컨텍스트
            final_decision: 최종 결정
            consensus_strength: 합의 강도
            dissenting_agents: 반대 의견 에이전트
            metadata: 추가 메타데이터
            
        Returns:
            DebateRecord: 기록된 토론
        """
        record_id = self._generate_id()
        
        record = DebateRecord(
            id=record_id,
            timestamp=datetime.now(),
            ticker=ticker,
            topic=topic,
            votes=votes,
            context=context,
            outcome=DebateOutcome(
                final_decision=final_decision,
                consensus_strength=consensus_strength,
                dissenting_agents=dissenting_agents or []
            ),
            metadata=metadata or {}
        )
        
        # 메모리에 저장
        self._records[record_id] = record
        
        # 티커별 인덱스
        if ticker not in self._records_by_ticker:
            self._records_by_ticker[ticker] = []
        self._records_by_ticker[ticker].append(record_id)
        
        # 통계 업데이트
        self._update_stats(record)
        
        # 파일로 저장
        if self.storage_path:
            self._save_record(record)
        
        # 메모리 정리
        self._cleanup_memory()
        
        logger.info(
            f"Debate logged: {record_id} | {ticker} | {final_decision.value} | "
            f"consensus={consensus_strength:.2f}"
        )
        
        return record
    
    def update_outcome(
        self,
        record_id: str,
        executed: Optional[bool] = None,
        execution_price: Optional[float] = None,
        pnl_result: Optional[float] = None,
        pnl_percentage: Optional[float] = None
    ) -> bool:
        """
        토론 결과 업데이트 (사후 PnL 기록)
        
        Args:
            record_id: 토론 ID
            executed: 실행 여부
            execution_price: 체결 가격
            pnl_result: 실현 손익
            pnl_percentage: 손익률
            
        Returns:
            bool: 업데이트 성공 여부
        """
        record = self._records.get(record_id)
        if not record:
            logger.warning(f"Record not found: {record_id}")
            return False
        
        if executed is not None:
            record.outcome.executed = executed
        if execution_price is not None:
            record.outcome.execution_price = execution_price
        if pnl_result is not None:
            record.outcome.pnl_result = pnl_result
        if pnl_percentage is not None:
            record.outcome.pnl_percentage = pnl_percentage
        
        record.outcome.outcome_recorded_at = datetime.now()
        
        # 파일 업데이트
        if self.storage_path:
            self._save_record(record)
        
        logger.info(f"Outcome updated: {record_id} | PnL={pnl_result}")
        
        return True
    
    def get_debate(self, record_id: str) -> Optional[DebateRecord]:
        """ID로 토론 조회"""
        return self._records.get(record_id)
    
    def get_recent_debates(
        self,
        ticker: Optional[str] = None,
        limit: int = 10,
        decision_filter: Optional[VoteType] = None
    ) -> List[DebateRecord]:
        """
        최근 토론 조회
        
        Args:
            ticker: 티커 필터 (선택)
            limit: 최대 개수
            decision_filter: 결정 유형 필터 (선택)
        """
        if ticker:
            record_ids = self._records_by_ticker.get(ticker, [])
            records = [self._records[rid] for rid in record_ids if rid in self._records]
        else:
            records = list(self._records.values())
        
        # 필터링
        if decision_filter:
            records = [r for r in records if r.outcome.final_decision == decision_filter]
        
        # 정렬 및 제한
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records[:limit]
    
    def get_debates_with_outcomes(
        self,
        min_pnl: Optional[float] = None,
        max_pnl: Optional[float] = None,
        limit: int = 100
    ) -> List[DebateRecord]:
        """PnL 결과가 있는 토론 조회"""
        records = [
            r for r in self._records.values() 
            if r.outcome.pnl_result is not None
        ]
        
        if min_pnl is not None:
            records = [r for r in records if r.outcome.pnl_result >= min_pnl]
        if max_pnl is not None:
            records = [r for r in records if r.outcome.pnl_result <= max_pnl]
        
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records[:limit]
    
    def get_agent_performance(
        self,
        agent_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        에이전트별 성과 분석
        
        Args:
            agent_name: 에이전트 이름
            days: 분석 기간 (일)
            
        Returns:
            성과 통계
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        records = [
            r for r in self._records.values()
            if r.timestamp >= cutoff and r.outcome.pnl_result is not None
        ]
        
        agent_stats = {
            "total_votes": 0,
            "correct_predictions": 0,
            "total_pnl": 0.0,
            "wins": 0,
            "losses": 0,
            "abstains": 0
        }
        
        for record in records:
            for vote in record.votes:
                if vote.agent_name == agent_name:
                    agent_stats["total_votes"] += 1
                    
                    if vote.vote == VoteType.ABSTAIN:
                        agent_stats["abstains"] += 1
                        continue
                    
                    # 예측 정확성 판정
                    pnl = record.outcome.pnl_result
                    if pnl > 0:
                        agent_stats["wins"] += 1
                        if vote.vote in [VoteType.BUY, VoteType.DCA]:
                            agent_stats["correct_predictions"] += 1
                    elif pnl < 0:
                        agent_stats["losses"] += 1
                        if vote.vote in [VoteType.SELL, VoteType.STOP_LOSS]:
                            agent_stats["correct_predictions"] += 1
                    
                    agent_stats["total_pnl"] += pnl
        
        # 비율 계산
        total = agent_stats["total_votes"] - agent_stats["abstains"]
        if total > 0:
            agent_stats["win_rate"] = agent_stats["wins"] / total
            agent_stats["accuracy"] = agent_stats["correct_predictions"] / total
            agent_stats["avg_pnl"] = agent_stats["total_pnl"] / total
        else:
            agent_stats["win_rate"] = 0.0
            agent_stats["accuracy"] = 0.0
            agent_stats["avg_pnl"] = 0.0
        
        return agent_stats
    
    def get_consensus_analysis(self, days: int = 30) -> Dict[str, Any]:
        """합의 강도와 성과 간의 관계 분석"""
        cutoff = datetime.now() - timedelta(days=days)
        
        records = [
            r for r in self._records.values()
            if r.timestamp >= cutoff and r.outcome.pnl_result is not None
        ]
        
        # 합의 강도별 성과
        strength_buckets = {
            "low (0.0-0.5)": {"count": 0, "total_pnl": 0, "wins": 0},
            "medium (0.5-0.8)": {"count": 0, "total_pnl": 0, "wins": 0},
            "high (0.8-1.0)": {"count": 0, "total_pnl": 0, "wins": 0}
        }
        
        for record in records:
            strength = record.outcome.consensus_strength
            pnl = record.outcome.pnl_result
            
            if strength < 0.5:
                bucket = "low (0.0-0.5)"
            elif strength < 0.8:
                bucket = "medium (0.5-0.8)"
            else:
                bucket = "high (0.8-1.0)"
            
            strength_buckets[bucket]["count"] += 1
            strength_buckets[bucket]["total_pnl"] += pnl
            if pnl > 0:
                strength_buckets[bucket]["wins"] += 1
        
        # 비율 계산
        for bucket, stats in strength_buckets.items():
            if stats["count"] > 0:
                stats["avg_pnl"] = stats["total_pnl"] / stats["count"]
                stats["win_rate"] = stats["wins"] / stats["count"]
            else:
                stats["avg_pnl"] = 0.0
                stats["win_rate"] = 0.0
        
        return strength_buckets
    
    def export_for_training(
        self,
        output_path: Path,
        format: str = "jsonl"
    ) -> int:
        """
        학습용 데이터 내보내기
        
        Args:
            output_path: 출력 파일 경로
            format: 형식 (jsonl, json)
            
        Returns:
            내보낸 레코드 수
        """
        records = [r for r in self._records.values() if r.outcome.pnl_result is not None]
        
        if format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    [r.to_dict() for r in records],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        
        logger.info(f"Exported {len(records)} records to {output_path}")
        return len(records)
    
    def _update_stats(self, record: DebateRecord):
        """통계 업데이트"""
        self._stats["total_debates"] += 1
        
        # 결정별
        decision = record.outcome.final_decision.value
        if decision not in self._stats["by_decision"]:
            self._stats["by_decision"][decision] = 0
        self._stats["by_decision"][decision] += 1
        
        # 티커별
        ticker = record.ticker
        if ticker not in self._stats["by_ticker"]:
            self._stats["by_ticker"][ticker] = 0
        self._stats["by_ticker"][ticker] += 1
        
        # 에이전트별
        for vote in record.votes:
            agent = vote.agent_name
            if agent not in self._stats["by_agent"]:
                self._stats["by_agent"][agent] = {"total": 0, "votes": {}}
            self._stats["by_agent"][agent]["total"] += 1
            
            vote_type = vote.vote.value
            if vote_type not in self._stats["by_agent"][agent]["votes"]:
                self._stats["by_agent"][agent]["votes"][vote_type] = 0
            self._stats["by_agent"][agent]["votes"][vote_type] += 1
    
    def _save_record(self, record: DebateRecord):
        """파일로 저장"""
        if not self.storage_path:
            return
        
        # 날짜별 디렉토리
        date_dir = self.storage_path / record.timestamp.strftime("%Y-%m")
        date_dir.mkdir(exist_ok=True)
        
        # 파일 저장
        file_path = date_dir / f"{record.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_existing_records(self):
        """기존 레코드 로드"""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        count = 0
        for json_file in self.storage_path.rglob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                record = DebateRecord.from_dict(data)
                self._records[record.id] = record
                
                if record.ticker not in self._records_by_ticker:
                    self._records_by_ticker[record.ticker] = []
                self._records_by_ticker[record.ticker].append(record.id)
                
                count += 1
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
        
        logger.info(f"Loaded {count} existing debate records")
    
    def _cleanup_memory(self):
        """메모리 정리"""
        if len(self._records) <= self.max_memory_records:
            return
        
        # 오래된 레코드 제거
        sorted_records = sorted(
            self._records.items(),
            key=lambda x: x[1].timestamp
        )
        
        to_remove = len(self._records) - self.max_memory_records
        for record_id, _ in sorted_records[:to_remove]:
            del self._records[record_id]
        
        logger.debug(f"Removed {to_remove} old records from memory")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return self._stats.copy()


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_debate_logger: Optional[DebateLogger] = None


def get_debate_logger(storage_path: Optional[Path] = None) -> DebateLogger:
    """DebateLogger 싱글톤 인스턴스"""
    global _debate_logger
    if _debate_logger is None:
        _debate_logger = DebateLogger(storage_path=storage_path)
    return _debate_logger


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger = DebateLogger()
    
    print("=== Debate Logger Test ===\n")
    
    # 테스트 데이터 생성
    votes = [
        AgentVote(
            agent_name="claude",
            vote=VoteType.BUY,
            confidence=0.75,
            reasoning="Strong fundamentals and AI demand growth",
            role="risk_controller"
        ),
        AgentVote(
            agent_name="chatgpt",
            vote=VoteType.BUY,
            confidence=0.80,
            reasoning="Sector rotation favors tech",
            role="sector_specialist"
        ),
        AgentVote(
            agent_name="gemini",
            vote=VoteType.HOLD,
            confidence=0.60,
            reasoning="Valuation concerns at current levels",
            role="macro_strategist"
        )
    ]
    
    context = MarketContextSnapshot(
        price=560.0,
        price_change_1d=2.5,
        price_change_5d=8.0,
        volume_ratio=1.5,
        volatility=0.25,
        vix=18.5,
        market_sentiment="bullish"
    )
    
    # 토론 기록
    record = logger.log_debate(
        ticker="NVDA",
        topic="BUY 결정",
        votes=votes,
        context=context,
        final_decision=VoteType.BUY,
        consensus_strength=0.72,
        dissenting_agents=["gemini"]
    )
    
    print(f"Recorded debate: {record.id}")
    print(f"  Ticker: {record.ticker}")
    print(f"  Decision: {record.outcome.final_decision.value}")
    print(f"  Consensus: {record.outcome.consensus_strength:.2f}")
    print(f"  Votes: {len(record.votes)}")
    
    # 결과 업데이트
    print("\nUpdating outcome...")
    logger.update_outcome(
        record.id,
        executed=True,
        execution_price=558.0,
        pnl_result=500.0,
        pnl_percentage=5.0
    )
    
    # 조회
    updated_record = logger.get_debate(record.id)
    print(f"  PnL: ${updated_record.outcome.pnl_result}")
    print(f"  PnL%: {updated_record.outcome.pnl_percentage}%")
    
    # 통계
    print("\n" + "="*50)
    print("Stats:")
    stats = logger.get_stats()
    print(f"  Total debates: {stats['total_debates']}")
    print(f"  By decision: {stats['by_decision']}")
