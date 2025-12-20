"""
AI Review Data Models and Repository

로컬 JSON 저장으로 AI 분석 히스토리 관리
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import hashlib


# ============================================================================
# Data Directory
# ============================================================================

# Docker 컨테이너 호환 경로
DATA_DIR = Path("/app/data/ai_reviews")
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    DATA_DIR = Path("/tmp/ai_reviews")
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AIAnalysisResult:
    """AI 분석 결과"""
    action: str  # BUY, SELL, HOLD
    conviction: float  # 0.0 ~ 1.0
    reasoning: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: float = 0.0
    risk_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []


@dataclass
class DetailedReasoning:
    """상세 분석 근거"""
    technical_analysis: str = ""
    fundamental_analysis: str = ""
    sentiment_analysis: str = ""
    risk_assessment: str = ""


@dataclass
class ModelInfo:
    """AI 모델 정보"""
    model_name: str
    tokens_used: int
    response_time_ms: int
    cost_usd: float = 0.0


@dataclass
class DiffFromPrevious:
    """이전 분석 대비 변경사항"""
    has_changes: bool
    conviction_change: float = 0.0
    action_changed: bool = False
    reasoning_diff: str = ""


@dataclass
class AIReviewRecord:
    """AI 분석 기록"""
    analysis_id: str
    ticker: str
    timestamp: str
    analysis: AIAnalysisResult
    detailed_reasoning: DetailedReasoning
    model_info: ModelInfo
    diff_from_previous: Optional[DiffFromPrevious] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AIReviewRecord':
        """Create from dictionary"""
        return cls(
            analysis_id=data['analysis_id'],
            ticker=data['ticker'],
            timestamp=data['timestamp'],
            analysis=AIAnalysisResult(**data['analysis']),
            detailed_reasoning=DetailedReasoning(**data['detailed_reasoning']),
            model_info=ModelInfo(**data['model_info']),
            diff_from_previous=DiffFromPrevious(**data['diff_from_previous']) 
                if data.get('diff_from_previous') else None
        )


# ============================================================================
# Repository
# ============================================================================

class AIReviewRepository:
    """
    AI 분석 결과 저장소
    
    Features:
    - 로컬 JSON 파일 저장
    - 티커별 히스토리 관리
    - 자동 diff 계산
    - 검색 및 필터링
    """
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file for quick lookups
        self.index_file = self.data_dir / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """인덱스 파일이 없으면 생성"""
        if not self.index_file.exists():
            self._save_index({
                "total_count": 0,
                "reviews": [],
                "by_ticker": {},
                "last_updated": datetime.utcnow().isoformat()
            })
    
    def _load_index(self) -> dict:
        """인덱스 파일 로드"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "total_count": 0,
                "reviews": [],
                "by_ticker": {},
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def _save_index(self, index: dict):
        """인덱스 파일 저장"""
        index["last_updated"] = datetime.utcnow().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self, ticker: str, timestamp: str) -> str:
        """고유 ID 생성"""
        content = f"{ticker}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_file_path(self, analysis_id: str) -> Path:
        """분석 ID로 파일 경로 반환"""
        return self.data_dir / f"{analysis_id}.json"
    
    def _calculate_diff(self, ticker: str, new_analysis: AIAnalysisResult) -> Optional[DiffFromPrevious]:
        """이전 분석과 비교"""
        previous = self.get_latest_by_ticker(ticker)
        
        if not previous:
            return None
        
        prev_analysis = previous.analysis
        
        # 변경 사항 계산
        action_changed = prev_analysis.action != new_analysis.action
        conviction_change = new_analysis.conviction - prev_analysis.conviction
        
        # 주요 차이점 설명
        diff_parts = []
        
        if action_changed:
            diff_parts.append(f"투자 의견 변경: {prev_analysis.action} → {new_analysis.action}")
        
        if abs(conviction_change) > 0.1:
            direction = "상승" if conviction_change > 0 else "하락"
            diff_parts.append(f"확신도 {direction}: {conviction_change * 100:.1f}%p")
        
        # 가격 목표 변경
        if prev_analysis.target_price and new_analysis.target_price:
            price_change = (new_analysis.target_price - prev_analysis.target_price) / prev_analysis.target_price * 100
            if abs(price_change) > 5:
                diff_parts.append(f"목표가 변경: ${prev_analysis.target_price:.2f} → ${new_analysis.target_price:.2f} ({price_change:+.1f}%)")
        
        # 새로운 리스크 요인
        new_risks = set(new_analysis.risk_factors) - set(prev_analysis.risk_factors)
        if new_risks:
            diff_parts.append(f"새로운 리스크: {', '.join(new_risks)}")
        
        has_changes = action_changed or abs(conviction_change) > 0.05 or len(diff_parts) > 0
        
        return DiffFromPrevious(
            has_changes=has_changes,
            conviction_change=conviction_change,
            action_changed=action_changed,
            reasoning_diff="\n".join(diff_parts) if diff_parts else "주요 변경사항 없음"
        )
    
    def save(self, record: AIReviewRecord) -> str:
        """
        AI 분석 결과 저장
        
        Returns:
            analysis_id
        """
        # 자동 diff 계산
        if record.diff_from_previous is None:
            record.diff_from_previous = self._calculate_diff(record.ticker, record.analysis)
        
        # 파일 저장
        file_path = self._get_file_path(record.analysis_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 인덱스 업데이트
        index = self._load_index()
        
        # 새 레코드 정보 추가
        review_summary = {
            "analysis_id": record.analysis_id,
            "ticker": record.ticker,
            "timestamp": record.timestamp,
            "action": record.analysis.action,
            "conviction": record.analysis.conviction,
            "reasoning_preview": record.analysis.reasoning[:200] + "..." if len(record.analysis.reasoning) > 200 else record.analysis.reasoning,
            "has_changes": record.diff_from_previous.has_changes if record.diff_from_previous else False,
            "model_name": record.model_info.model_name
        }
        
        # 중복 체크 (같은 ID가 있으면 업데이트)
        existing_idx = next(
            (i for i, r in enumerate(index["reviews"]) if r["analysis_id"] == record.analysis_id),
            None
        )
        
        if existing_idx is not None:
            index["reviews"][existing_idx] = review_summary
        else:
            index["reviews"].insert(0, review_summary)  # 최신 순
            index["total_count"] += 1
        
        # 티커별 인덱스
        if record.ticker not in index["by_ticker"]:
            index["by_ticker"][record.ticker] = []
        
        if record.analysis_id not in index["by_ticker"][record.ticker]:
            index["by_ticker"][record.ticker].insert(0, record.analysis_id)
        
        self._save_index(index)
        
        return record.analysis_id
    
    def get(self, analysis_id: str) -> Optional[AIReviewRecord]:
        """ID로 분석 결과 조회"""
        file_path = self._get_file_path(analysis_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AIReviewRecord.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading {analysis_id}: {e}")
            return None
    
    def get_latest_by_ticker(self, ticker: str) -> Optional[AIReviewRecord]:
        """티커의 최신 분석 결과 조회"""
        index = self._load_index()
        
        ticker_ids = index.get("by_ticker", {}).get(ticker, [])
        
        if not ticker_ids:
            return None
        
        return self.get(ticker_ids[0])
    
    def get_history_by_ticker(self, ticker: str, limit: int = 10) -> List[AIReviewRecord]:
        """티커별 분석 히스토리"""
        index = self._load_index()
        
        ticker_ids = index.get("by_ticker", {}).get(ticker, [])[:limit]
        
        records = []
        for analysis_id in ticker_ids:
            record = self.get(analysis_id)
            if record:
                records.append(record)
        
        return records
    
    def list_all(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        모든 분석 목록 조회
        
        Returns:
            {
                "total_count": int,
                "today_count": int,
                "avg_conviction": float,
                "changed_count": int,
                "reviews": List[dict]
            }
        """
        index = self._load_index()
        
        reviews = index.get("reviews", [])[offset:offset + limit]
        
        # 통계 계산
        today = datetime.utcnow().date()
        today_count = sum(
            1 for r in reviews
            if datetime.fromisoformat(r["timestamp"]).date() == today
        )
        
        avg_conviction = (
            sum(r["conviction"] for r in reviews) / len(reviews)
            if reviews else 0
        )
        
        changed_count = sum(1 for r in reviews if r.get("has_changes", False))
        
        return {
            "total_count": index.get("total_count", 0),
            "today_count": today_count,
            "avg_conviction": avg_conviction,
            "changed_count": changed_count,
            "reviews": reviews
        }
    
    def search(self, 
               ticker: Optional[str] = None,
               action: Optional[str] = None,
               min_conviction: Optional[float] = None,
               has_changes_only: bool = False,
               days_back: int = 30,
               limit: int = 50) -> List[dict]:
        """
        분석 결과 검색
        
        Args:
            ticker: 특정 티커
            action: BUY/SELL/HOLD
            min_conviction: 최소 확신도
            has_changes_only: 변경사항 있는 것만
            days_back: 최근 N일
            limit: 최대 결과 수
        """
        index = self._load_index()
        reviews = index.get("reviews", [])
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        filtered = []
        for review in reviews:
            if len(filtered) >= limit:
                break
            
            # 날짜 필터
            review_date = datetime.fromisoformat(review["timestamp"])
            if review_date < cutoff_date:
                continue
            
            # 티커 필터
            if ticker and review["ticker"] != ticker:
                continue
            
            # 액션 필터
            if action and review["action"] != action:
                continue
            
            # 확신도 필터
            if min_conviction and review["conviction"] < min_conviction:
                continue
            
            # 변경사항 필터
            if has_changes_only and not review.get("has_changes", False):
                continue
            
            filtered.append(review)
        
        return filtered
    
    def delete(self, analysis_id: str) -> bool:
        """분석 결과 삭제"""
        file_path = self._get_file_path(analysis_id)
        
        if not file_path.exists():
            return False
        
        # 파일 삭제
        file_path.unlink()
        
        # 인덱스 업데이트
        index = self._load_index()
        
        index["reviews"] = [
            r for r in index["reviews"] 
            if r["analysis_id"] != analysis_id
        ]
        
        for ticker in index.get("by_ticker", {}):
            index["by_ticker"][ticker] = [
                aid for aid in index["by_ticker"][ticker]
                if aid != analysis_id
            ]
        
        index["total_count"] = len(index["reviews"])
        self._save_index(index)
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        index = self._load_index()
        reviews = index.get("reviews", [])
        
        if not reviews:
            return {
                "total": 0,
                "by_action": {},
                "by_ticker": {},
                "avg_conviction": 0,
                "changed_rate": 0
            }
        
        # 액션별 통계
        by_action = {}
        for review in reviews:
            action = review["action"]
            by_action[action] = by_action.get(action, 0) + 1
        
        # 티커별 통계
        by_ticker = {}
        for ticker, ids in index.get("by_ticker", {}).items():
            by_ticker[ticker] = len(ids)
        
        # 확신도 평균
        avg_conviction = sum(r["conviction"] for r in reviews) / len(reviews)
        
        # 변경률
        changed_count = sum(1 for r in reviews if r.get("has_changes", False))
        changed_rate = changed_count / len(reviews) if reviews else 0
        
        return {
            "total": index.get("total_count", 0),
            "by_action": by_action,
            "by_ticker": dict(sorted(by_ticker.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_conviction": avg_conviction,
            "changed_rate": changed_rate
        }


# ============================================================================
# Factory Function for Creating Records
# ============================================================================

def create_ai_review_record(
    ticker: str,
    analysis_result: dict,
    detailed_reasoning: dict,
    model_name: str,
    tokens_used: int,
    response_time_ms: int,
    cost_usd: float = 0.0
) -> AIReviewRecord:
    """
    AI 분석 결과로부터 레코드 생성
    
    Args:
        ticker: 종목 코드
        analysis_result: {action, conviction, reasoning, target_price, stop_loss, position_size, risk_factors}
        detailed_reasoning: {technical_analysis, fundamental_analysis, sentiment_analysis, risk_assessment}
        model_name: 사용된 모델명
        tokens_used: 사용된 토큰 수
        response_time_ms: 응답 시간 (ms)
        cost_usd: 비용 (USD)
    """
    timestamp = datetime.utcnow().isoformat()
    analysis_id = AIReviewRepository()._generate_id(ticker, timestamp)
    
    return AIReviewRecord(
        analysis_id=analysis_id,
        ticker=ticker,
        timestamp=timestamp,
        analysis=AIAnalysisResult(
            action=analysis_result.get("action", "HOLD"),
            conviction=analysis_result.get("conviction", 0.5),
            reasoning=analysis_result.get("reasoning", ""),
            target_price=analysis_result.get("target_price"),
            stop_loss=analysis_result.get("stop_loss"),
            position_size=analysis_result.get("position_size", 0.0),
            risk_factors=analysis_result.get("risk_factors", [])
        ),
        detailed_reasoning=DetailedReasoning(
            technical_analysis=detailed_reasoning.get("technical_analysis", ""),
            fundamental_analysis=detailed_reasoning.get("fundamental_analysis", ""),
            sentiment_analysis=detailed_reasoning.get("sentiment_analysis", ""),
            risk_assessment=detailed_reasoning.get("risk_assessment", "")
        ),
        model_info=ModelInfo(
            model_name=model_name,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            cost_usd=cost_usd
        )
    )


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # 저장소 초기화
    repo = AIReviewRepository()
    
    # 샘플 레코드 생성
    sample_record = create_ai_review_record(
        ticker="AAPL",
        analysis_result={
            "action": "BUY",
            "conviction": 0.85,
            "reasoning": "Apple의 강력한 실적과 AI 통합 전략이 주가 상승을 이끌 것으로 예상됩니다. iPhone 16 사이클이 예상보다 강하고, 서비스 부문 성장이 지속되고 있습니다.",
            "target_price": 235.0,
            "stop_loss": 195.0,
            "position_size": 0.08,
            "risk_factors": ["중국 시장 불확실성", "AI 경쟁 심화", "규제 리스크"]
        },
        detailed_reasoning={
            "technical_analysis": "RSI 65로 과매수 직전, 20일 이평선 위에서 강세 유지. 볼린저 밴드 상단 근처로 단기 조정 가능성 있으나 중기 상승 추세 유효.",
            "fundamental_analysis": "P/E 32.5배로 역사적 평균보다 높지만, EPS 성장률 15%를 고려하면 합리적. 순현금 보유고 $60B, 자사주 매입 지속.",
            "sentiment_analysis": "기관 투자자들의 매수세 지속. 애널리스트 목표가 평균 $240. SNS 감성 긍정적 75%.",
            "risk_assessment": "중국 매출 의존도 20%가 지정학적 리스크. AI PC 전환 지연 시 성장 둔화 가능. 반독점 규제 강화 주시 필요."
        },
        model_name="claude-3-5-haiku-latest",
        tokens_used=2500,
        response_time_ms=1234,
        cost_usd=0.0025
    )
    
    # 저장
    analysis_id = repo.save(sample_record)
    print(f"✅ Saved: {analysis_id}")
    
    # 조회
    loaded = repo.get(analysis_id)
    print(f"📄 Loaded: {loaded.ticker} - {loaded.analysis.action}")
    
    # 목록 조회
    all_reviews = repo.list_all(limit=10)
    print(f"📊 Total reviews: {all_reviews['total_count']}")
    print(f"📈 Today: {all_reviews['today_count']}")
    print(f"🎯 Avg Conviction: {all_reviews['avg_conviction']:.1%}")
    
    # 통계
    stats = repo.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  By Action: {stats['by_action']}")
    print(f"  Changed Rate: {stats['changed_rate']:.1%}")
