"""
Self-Feedback Loop

AI 예측 vs 실제 결과를 비교하여 자동 보정
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class SignalAction(Enum):
    """시그널 액션"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class PredictionRecord:
    """AI 예측 기록"""
    id: Optional[int] = None
    ticker: str = ""
    predicted_at: datetime = field(default_factory=datetime.now)
    
    # 예측 내용
    action: str = "HOLD"  # BUY, SELL, HOLD
    conviction: float = 0.5  # 0-1
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str = ""
    model_used: str = "unknown"
    
    # 컨텍스트
    entry_price: Optional[float] = None
    market_regime: Optional[str] = None
    
    # 결과 (나중에 업데이트)
    actual_return_1d: Optional[float] = None
    actual_return_5d: Optional[float] = None
    actual_return_20d: Optional[float] = None
    prediction_correct: Optional[bool] = None
    evaluated_at: Optional[datetime] = None


@dataclass
class ModelPerformance:
    """모델 성과"""
    model_name: str
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    buy_accuracy: float = 0.0
    sell_accuracy: float = 0.0
    avg_conviction_when_correct: float = 0.0
    avg_conviction_when_wrong: float = 0.0
    confidence_calibration: float = 1.0  # 이상적으로 1.0


@dataclass
class CalibrationAdjustment:
    """신뢰도 보정값"""
    model_name: str
    action: str
    original_confidence: float
    adjusted_confidence: float
    adjustment_ratio: float
    sample_size: int


class FeedbackLoop:
    """
    Self-Feedback Loop
    
    AI 예측과 실제 결과를 비교하여:
    1. 모델별 정확도 추적
    2. Conviction 자동 보정
    3. 주간 성과 리포트 생성
    """
    
    def __init__(
        self,
        database=None,
        redis_client=None,
    ):
        self.database = database
        self.redis_client = redis_client
        
        # 메모리 저장 (DB 없을 때)
        self._predictions: List[PredictionRecord] = []
        self._calibration_cache: Dict[str, Dict] = {}
    
    async def record_prediction(
        self,
        ticker: str,
        action: str,
        conviction: float,
        model_used: str = "unknown",
        target_price: float = None,
        stop_loss: float = None,
        reasoning: str = "",
        entry_price: float = None,
        market_regime: str = None,
    ) -> int:
        """
        예측 기록 저장
        
        Args:
            ticker: 종목 티커
            action: BUY, SELL, HOLD
            conviction: 신뢰도 (0-1)
            model_used: 사용된 AI 모델
            ...
            
        Returns:
            int: 예측 ID
        """
        record = PredictionRecord(
            id=len(self._predictions) + 1,
            ticker=ticker,
            predicted_at=datetime.now(),
            action=action,
            conviction=conviction,
            target_price=target_price,
            stop_loss=stop_loss,
            reasoning=reasoning,
            model_used=model_used,
            entry_price=entry_price,
            market_regime=market_regime,
        )
        
        # DB 저장 또는 메모리 저장
        if self.database:
            await self._save_to_db(record)
        else:
            self._predictions.append(record)
        
        logger.info(f"예측 기록: {ticker} {action} (conviction: {conviction:.0%})")
        
        return record.id
    
    async def evaluate_predictions(self) -> int:
        """
        미평가 예측들을 평가
        
        - 1일, 5일, 20일 후 실제 수익률 계산
        - 방향 예측 정확성 평가
        
        Returns:
            int: 평가된 예측 수
        """
        import yfinance as yf
        
        now = datetime.now()
        evaluated_count = 0
        
        # 평가 대상: 1일 이상 지난 미평가 예측
        for pred in self._predictions:
            if pred.evaluated_at is not None:
                continue
            
            days_passed = (now - pred.predicted_at).days
            
            if days_passed < 1:
                continue
            
            try:
                # 실제 가격 가져오기
                stock = yf.Ticker(pred.ticker)
                hist = stock.history(
                    start=pred.predicted_at.strftime("%Y-%m-%d"),
                    end=now.strftime("%Y-%m-%d")
                )
                
                if hist.empty or pred.entry_price is None:
                    continue
                
                entry = pred.entry_price
                
                # 수익률 계산
                if days_passed >= 1 and len(hist) >= 1:
                    pred.actual_return_1d = (
                        (hist['Close'].iloc[min(1, len(hist)-1)] - entry) / entry * 100
                    )
                
                if days_passed >= 5 and len(hist) >= 5:
                    pred.actual_return_5d = (
                        (hist['Close'].iloc[min(5, len(hist)-1)] - entry) / entry * 100
                    )
                
                if days_passed >= 20 and len(hist) >= 20:
                    pred.actual_return_20d = (
                        (hist['Close'].iloc[min(20, len(hist)-1)] - entry) / entry * 100
                    )
                    pred.evaluated_at = now
                
                # 예측 정확성 평가 (5일 기준)
                if pred.actual_return_5d is not None:
                    if pred.action == "BUY":
                        pred.prediction_correct = pred.actual_return_5d > 0
                    elif pred.action == "SELL":
                        pred.prediction_correct = pred.actual_return_5d < 0
                    else:  # HOLD
                        pred.prediction_correct = abs(pred.actual_return_5d) < 2
                    
                    evaluated_count += 1
                
            except Exception as e:
                logger.error(f"예측 평가 실패 {pred.ticker}: {e}")
        
        logger.info(f"{evaluated_count}개 예측 평가 완료")
        return evaluated_count
    
    async def get_model_performance(
        self,
        model_name: str = None,
    ) -> List[ModelPerformance]:
        """
        모델별 성과 조회
        
        Args:
            model_name: 특정 모델만 조회 (None이면 전체)
            
        Returns:
            List[ModelPerformance]: 모델별 성과
        """
        # 모델별로 그룹화
        model_preds: Dict[str, List[PredictionRecord]] = {}
        
        for pred in self._predictions:
            if pred.prediction_correct is None:
                continue
            
            if model_name and pred.model_used != model_name:
                continue
            
            if pred.model_used not in model_preds:
                model_preds[pred.model_used] = []
            model_preds[pred.model_used].append(pred)
        
        results = []
        for model, preds in model_preds.items():
            correct = [p for p in preds if p.prediction_correct]
            wrong = [p for p in preds if not p.prediction_correct]
            
            buy_preds = [p for p in preds if p.action == "BUY"]
            buy_correct = [p for p in buy_preds if p.prediction_correct]
            
            sell_preds = [p for p in preds if p.action == "SELL"]
            sell_correct = [p for p in sell_preds if p.prediction_correct]
            
            perf = ModelPerformance(
                model_name=model,
                total_predictions=len(preds),
                correct_predictions=len(correct),
                accuracy=len(correct) / len(preds) if preds else 0,
                buy_accuracy=len(buy_correct) / len(buy_preds) if buy_preds else 0,
                sell_accuracy=len(sell_correct) / len(sell_preds) if sell_preds else 0,
                avg_conviction_when_correct=sum(p.conviction for p in correct) / len(correct) if correct else 0,
                avg_conviction_when_wrong=sum(p.conviction for p in wrong) / len(wrong) if wrong else 0,
            )
            
            # Calibration 계산 (신뢰도 vs 실제 정확도)
            if perf.avg_conviction_when_correct > 0:
                perf.confidence_calibration = perf.accuracy / perf.avg_conviction_when_correct
            
            results.append(perf)
        
        return results
    
    async def get_calibration_adjustment(
        self,
        model_name: str,
        action: str = None,
    ) -> Dict[str, CalibrationAdjustment]:
        """
        Conviction 보정값 계산
        
        예: 80% 확신 예측의 실제 정확도가 60%라면
            보정값 = 0.75 (60/80)
            
        Returns:
            Dict: action별 보정값
        """
        adjustments = {}
        
        for act in ["BUY", "SELL", "HOLD"]:
            if action and act != action:
                continue
            
            preds = [
                p for p in self._predictions
                if p.model_used == model_name
                and p.action == act
                and p.prediction_correct is not None
            ]
            
            if len(preds) < 5:  # 최소 5개 샘플 필요
                continue
            
            correct = [p for p in preds if p.prediction_correct]
            actual_accuracy = len(correct) / len(preds)
            avg_conviction = sum(p.conviction for p in preds) / len(preds)
            
            adjustment_ratio = actual_accuracy / avg_conviction if avg_conviction > 0 else 1.0
            
            adjustments[act] = CalibrationAdjustment(
                model_name=model_name,
                action=act,
                original_confidence=avg_conviction,
                adjusted_confidence=avg_conviction * adjustment_ratio,
                adjustment_ratio=adjustment_ratio,
                sample_size=len(preds),
            )
        
        return adjustments
    
    def apply_calibration(
        self,
        model_name: str,
        action: str,
        conviction: float,
    ) -> float:
        """
        보정된 신뢰도 반환
        
        Args:
            model_name: 모델 이름
            action: BUY, SELL, HOLD
            conviction: 원래 신뢰도
            
        Returns:
            float: 보정된 신뢰도
        """
        if model_name not in self._calibration_cache:
            return conviction
        
        cal = self._calibration_cache.get(model_name, {}).get(action)
        if cal is None:
            return conviction
        
        return min(1.0, conviction * cal.adjustment_ratio)
    
    async def generate_weekly_report(self) -> str:
        """
        주간 성과 리포트 생성 (한국어)
        
        Returns:
            str: Markdown 형식 리포트
        """
        performances = await self.get_model_performance()
        
        # 최근 7일 예측만
        week_ago = datetime.now() - timedelta(days=7)
        recent_preds = [
            p for p in self._predictions
            if p.predicted_at >= week_ago
        ]
        evaluated = [p for p in recent_preds if p.prediction_correct is not None]
        
        report = f"""# 📊 AI Trading 주간 성과 리포트

**기간**: {week_ago.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}

## 📈 전체 요약

| 항목 | 수치 |
|------|-----|
| 총 예측 수 | {len(recent_preds)} |
| 평가 완료 | {len(evaluated)} |
| 전체 정확도 | {sum(1 for p in evaluated if p.prediction_correct) / len(evaluated) * 100:.1f}% |

## 🤖 모델별 성과

| 모델 | 예측 수 | 정확도 | BUY 정확도 | SELL 정확도 | 보정 계수 |
|------|--------|--------|-----------|------------|----------|
"""
        for perf in performances:
            report += f"| {perf.model_name} | {perf.total_predictions} | {perf.accuracy*100:.1f}% | {perf.buy_accuracy*100:.1f}% | {perf.sell_accuracy*100:.1f}% | {perf.confidence_calibration:.2f} |\n"
        
        # 최고/최저 성과 종목
        if evaluated:
            best = max(evaluated, key=lambda p: p.actual_return_5d or 0)
            worst = min(evaluated, key=lambda p: p.actual_return_5d or 0)
            
            report += f"""
## 🏆 최고 성과

- **{best.ticker}**: {best.action} → {best.actual_return_5d:+.1f}% (5일)

## 📉 최저 성과

- **{worst.ticker}**: {worst.action} → {worst.actual_return_5d:+.1f}% (5일)
"""
        
        report += f"""
## 💡 권장 사항

"""
        # 보정 필요한 모델
        for perf in performances:
            if perf.confidence_calibration < 0.8:
                report += f"- ⚠️ **{perf.model_name}** 신뢰도 과대평가 (보정 계수: {perf.confidence_calibration:.2f})\n"
            elif perf.confidence_calibration > 1.2:
                report += f"- 📈 **{perf.model_name}** 신뢰도 과소평가 (보정 계수: {perf.confidence_calibration:.2f})\n"
        
        report += f"\n---\n*생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        return report
    
    async def _save_to_db(self, record: PredictionRecord):
        """DB에 예측 저장"""
        # TODO: 실제 DB 저장 구현
        self._predictions.append(record)
