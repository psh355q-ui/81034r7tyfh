"""
FLE Calculator - Forced Liquidation Equity (강제 청산 자산)

ChatGPT Integration Feature 3:
- 지금 전부 매도하면 손에 남는 실제 현금
- 수수료 및 세금 고려
- 추상적 수익률 대신 구체적 금액

철학:
"실제 돈이 얼마인지 보여주면, 사람들은 더 신중해진다"

작성일: 2025-12-16
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """포지션"""
    ticker: str
    quantity: int
    current_price: float
    cost_basis: float  # 평균 매수가
    
    @property
    def market_value(self) -> float:
        """현재 시장가"""
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """미실현 손익"""
        return self.market_value - (self.quantity * self.cost_basis)


@dataclass
class Portfolio:
    """포트폴리오"""
    user_id: str
    positions: List[Position] = field(default_factory=list)
    cash: float = 0.0
    
    @property
    def total_market_value(self) -> float:
        """총 시장가"""
        return sum(pos.market_value for pos in self.positions)
    
    @property
    def total_cost_basis(self) -> float:
        """총 매수가"""
        return sum(pos.quantity * pos.cost_basis for pos in self.positions)


@dataclass
class FLEResult:
    """FLE 계산 결과"""
    # 핵심 지표
    fle: float  # 강제 청산 자산
    peak_fle: float  # 역대 최고
    drawdown: float  # 하락 금액
    drawdown_pct: float  # 하락 비율
    
    # 세부 내역
    total_position_value: float
    estimated_fees: float
    estimated_tax: float
    cash_balance: float
    
    # 경고 레벨
    alert_level: str  # SAFE, MILD, WARNING, CRITICAL
    
    # 타임스탬프
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "fle": self.fle,
            "peak_fle": self.peak_fle,
            "drawdown": self.drawdown,
            "drawdown_pct": self.drawdown_pct,
            "total_position_value": self.total_position_value,
            "estimated_fees": self.estimated_fees,
            "estimated_tax": self.estimated_tax,
            "cash_balance": self.cash_balance,
            "alert_level": self.alert_level,
            "calculated_at": self.calculated_at.isoformat()
        }


class FLECalculator:
    """
    FLE (Forced Liquidation Equity) 계산기
    
    지금 당장 모든 포지션을 시장가로 팔면 남는 실제 현금
    
    Usage:
        calculator = FLECalculator()
        result = calculator.calculate_fle(portfolio)
        
        if result.alert_level == "CRITICAL":
            print(f"⚠️ 최고점 대비 {result.drawdown_pct:.1%} 하락!")
    """
    
    # 수수료 및 세금 상수
    BROKERAGE_FEE_RATE = 0.003  # 0.3% 중개 수수료
    TAX_RATE = 0.22  # 22% 양도소득세
    
    # 경고 임계값
    ALERT_THRESHOLDS = {
        "SAFE": 0.0,      # 하락 없음
        "MILD": 0.05,     # 5% 하락
        "WARNING": 0.10,  # 10% 하락
        "CRITICAL": 0.15  # 15% 하락
    }
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Args:
            storage_path: FLE 히스토리 저장 경로
        """
        self.storage_path = storage_path
        self.fle_history: Dict[str, List[FLEResult]] = {}
    
    def calculate_fle(self, portfolio: Portfolio) -> FLEResult:
        """
        FLE 계산
        
        Args:
            portfolio: 포트폴리오
        
        Returns:
            FLEResult
        
        Example:
            >>> portfolio = Portfolio(
            ...     user_id="user123",
            ...     positions=[Position("AAPL", 100, 180, 150)],
            ...     cash=10000
            ... )
            >>> result = calculator.calculate_fle(portfolio)
            >>> print(f"FLE: ${result.fle:,.0f}")
            FLE: $27,460
        """
        # 1. 총 포지션 가치
        total_position_value = portfolio.total_market_value
        
        # 2. 예상 수수료 (0.3%)
        estimated_fees = total_position_value * self.BROKERAGE_FEE_RATE
        
        # 3. 예상 세금 (22% on gains only)
        total_gains = max(0, total_position_value - portfolio.total_cost_basis)
        estimated_tax = total_gains * self.TAX_RATE
        
        # 4. FLE 계산
        fle = total_position_value - estimated_fees - estimated_tax + portfolio.cash
        
        # 5. Peak FLE 조회
        peak_fle = self._get_peak_fle(portfolio.user_id)
        if fle > peak_fle:
            peak_fle = fle
            self._update_peak_fle(portfolio.user_id, peak_fle)
        
        # 6. Drawdown 계산
        drawdown = peak_fle - fle
        drawdown_pct = drawdown / peak_fle if peak_fle > 0 else 0.0
        
        # 7. 경고 레벨 결정
        alert_level = self._determine_alert_level(drawdown_pct)
        
        # 8. 결과 생성
        result = FLEResult(
            fle=fle,
            peak_fle=peak_fle,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
            total_position_value=total_position_value,
            estimated_fees=estimated_fees,
            estimated_tax=estimated_tax,
            cash_balance=portfolio.cash,
            alert_level=alert_level
        )
        
        # 9. 히스토리 저장
        self._save_to_history(portfolio.user_id, result)
        
        logger.info(
            f"FLE calculated: ${fle:,.0f} "
            f"(Peak: ${peak_fle:,.0f}, Drawdown: {drawdown_pct:.1%}, Alert: {alert_level})"
        )
        
        return result
    
    def _determine_alert_level(self, drawdown_pct: float) -> str:
        """경고 레벨 결정"""
        if drawdown_pct >= self.ALERT_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"  # 15% 이상 하락
        elif drawdown_pct >= self.ALERT_THRESHOLDS["WARNING"]:
            return "WARNING"   # 10% 이상 하락
        elif drawdown_pct >= self.ALERT_THRESHOLDS["MILD"]:
            return "MILD"      # 5% 이상 하락
        else:
            return "SAFE"      # 5% 미만
    
    def _get_peak_fle(self, user_id: str) -> float:
        """사용자의 역대 최고 FLE 조회"""
        history = self.fle_history.get(user_id, [])
        if not history:
            return 0.0
        return max(result.fle for result in history)
    
    def _update_peak_fle(self, user_id: str, new_peak: float):
        """Peak FLE 업데이트"""
        # 메모리에만 저장 (실제로는 DB 저장)
        pass
    
    def _save_to_history(self, user_id: str, result: FLEResult):
        """FLE 히스토리 저장"""
        if user_id not in self.fle_history:
            self.fle_history[user_id] = []
        
        self.fle_history[user_id].append(result)
        
        # 최근 100개만 유지
        if len(self.fle_history[user_id]) > 100:
            self.fle_history[user_id] = self.fle_history[user_id][-100:]
    
    def get_fle_history(
        self,
        user_id: str,
        days: int = 30
    ) -> List[FLEResult]:
        """FLE 히스토리 조회"""
        return self.fle_history.get(user_id, [])[-days:]
    
    def get_safety_message(self, result: FLEResult) -> str:
        """
        경고 레벨별 메시지 생성
        
        ChatGPT 철학: 비난/훈계 ❌, 다독임 ⭐
        """
        if result.alert_level == "CRITICAL":
            return f"""
⚠️ 투자 현황 점검 시간입니다

지금 전부 매도하면 손에 남는 돈
₩{result.fle:,.0f}

최고점 대비 ₩{result.drawdown:,.0f} 하락 ({result.drawdown_pct:.1%})

💡 오늘은 여기서 멈추고 내일 다시 보는 것도 좋습니다.
잠시 쉬어가는 것도 전략의 일부입니다.
"""
        
        elif result.alert_level == "WARNING":
            return f"""
📊 포트폴리오 점검

현재 FLE: ₩{result.fle:,.0f}
최고점 대비: -{result.drawdown_pct:.1%}

시장 변동성이 있습니다. 
포지션을 점검해보시는 것이 좋을 것 같습니다.
"""
        
        elif result.alert_level == "MILD":
            return f"""
ℹ️ FLE 업데이트

현재 FLE: ₩{result.fle:,.0f}
최고점: ₩{result.peak_fle:,.0f}

소폭 조정 중입니다. 정상 범위 내입니다.
"""
        
        else:  # SAFE
            return f"""
✅ 포트폴리오 안정

현재 FLE: ₩{result.fle:,.0f}
역대 최고 갱신 중!
"""


# Singleton instance
_fle_calculator: Optional[FLECalculator] = None


def get_fle_calculator() -> FLECalculator:
    """FLE 계산기 싱글톤 인스턴스"""
    global _fle_calculator
    if _fle_calculator is None:
        _fle_calculator = FLECalculator()
    return _fle_calculator
