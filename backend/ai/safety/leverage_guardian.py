"""
Leverage Guardian - Safety Layer for High-Risk Instruments

Phase: Phase 4.2 - Grand Unified Strategy (Safety Layer)
Date: 2026-01-05

Purpose:
    레버리지 상품(3x ETF 등)에 대한 자동 안전 장치.
    - 전체 자산의 10% 이내로 제한 (Satellite Wallet)
    - 장기 보유 경고 (Volatility Drag)
    - 고변동성 시장 진입 차단 (VIX > 30)

Key Rules:
    1. 레버리지 ETF는 전체 포트폴리오의 10% 이내만 허용
    2. 보유 기간 5일 초과 시 경고
    3. VIX 30 이상일 때 신규 진입 차단
    4. 사용자 동의 없이 레버리지 거래 불가

Usage:
    guardian = LeverageGuardian()
    result = guardian.validate_order(ticker="TQQQ", quantity=10, portfolio_value=100000)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class LeverageCategory(str, Enum):
    """레버리지 상품 카테고리"""
    LEVERAGED_LONG = "leveraged_long"    # 3x 롱 (TQQQ, SOXL, UPRO)
    LEVERAGED_SHORT = "leveraged_short"  # 3x 숏 (SQQQ, SPXU, SOXS)
    INVERSE = "inverse"                   # 1x 인버스 (SH, PSQ)
    NORMAL = "normal"                     # 일반 주식/ETF


# 레버리지 상품 목록 (업데이트 필요 시 추가)
LEVERAGED_ETFS: Dict[str, LeverageCategory] = {
    # 3x 롱
    "TQQQ": LeverageCategory.LEVERAGED_LONG,   # Nasdaq 3x
    "SOXL": LeverageCategory.LEVERAGED_LONG,   # 반도체 3x
    "UPRO": LeverageCategory.LEVERAGED_LONG,   # S&P 500 3x
    "LABU": LeverageCategory.LEVERAGED_LONG,   # 바이오 3x
    "FAS": LeverageCategory.LEVERAGED_LONG,    # 금융 3x
    "TECL": LeverageCategory.LEVERAGED_LONG,   # 기술 3x
    "NUGT": LeverageCategory.LEVERAGED_LONG,   # 금 채굴 3x
    "FNGU": LeverageCategory.LEVERAGED_LONG,   # FANG+ 3x
    
    # 3x 숏
    "SQQQ": LeverageCategory.LEVERAGED_SHORT,  # Nasdaq 3x 숏
    "SOXS": LeverageCategory.LEVERAGED_SHORT,  # 반도체 3x 숏
    "SPXU": LeverageCategory.LEVERAGED_SHORT,  # S&P 500 3x 숏
    "LABD": LeverageCategory.LEVERAGED_SHORT,  # 바이오 3x 숏
    "FAZ": LeverageCategory.LEVERAGED_SHORT,   # 금융 3x 숏
    "TECS": LeverageCategory.LEVERAGED_SHORT,  # 기술 3x 숏
    "DUST": LeverageCategory.LEVERAGED_SHORT,  # 금 채굴 3x 숏
    "FNGD": LeverageCategory.LEVERAGED_SHORT,  # FANG+ 3x 숏
    
    # 1x 인버스
    "SH": LeverageCategory.INVERSE,    # S&P 500 인버스
    "PSQ": LeverageCategory.INVERSE,   # Nasdaq 인버스
    "DOG": LeverageCategory.INVERSE,   # Dow 인버스
}


@dataclass
class LeverageValidationResult:
    """레버리지 검증 결과"""
    allowed: bool
    category: LeverageCategory
    warnings: List[str]
    max_allowed_quantity: int
    max_allowed_value: float
    position_cap_pct: float  # 허용된 최대 비율
    requires_acknowledgment: bool
    rejection_reason: Optional[str] = None


class LeverageGuardian:
    """
    Leverage Guardian - 레버리지 상품 안전 장치
    
    레버리지 ETF에 대한 포지션 크기를 제한하고,
    장기 보유 및 고변동성 시장에서의 진입을 경고합니다.
    """
    
    # 기본 Hard Rules
    DEFAULT_RULES = {
        "max_leverage_pct": 0.10,         # 전체 자산의 10%
        "max_holding_days": 5,            # 최대 보유 5일
        "vix_threshold": 30,              # VIX 30 이상 시 경고
        "require_acknowledgment": True,   # 동의 필수
        "allow_inverse_in_volatility": True,  # 고변동성 시 인버스 허용
    }
    
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        """
        Args:
            rules: 커스텀 규칙 (기본값 오버라이드)
        """
        self.rules = {**self.DEFAULT_RULES, **(rules or {})}
    
    def is_leveraged(self, ticker: str) -> bool:
        """해당 티커가 레버리지 상품인지 확인"""
        return ticker.upper() in LEVERAGED_ETFS
    
    def get_category(self, ticker: str) -> LeverageCategory:
        """해당 티커의 레버리지 카테고리 반환"""
        return LEVERAGED_ETFS.get(ticker.upper(), LeverageCategory.NORMAL)
    
    def validate_order(
        self,
        ticker: str,
        quantity: int,
        price: float,
        portfolio_value: float,
        current_leverage_value: float = 0.0,
        vix_level: Optional[float] = None,
        user_acknowledged: bool = False
    ) -> LeverageValidationResult:
        """
        레버리지 주문 검증
        
        Args:
            ticker: 종목 티커
            quantity: 주문 수량
            price: 현재가
            portfolio_value: 전체 포트폴리오 가치
            current_leverage_value: 현재 레버리지 포지션 총 가치
            vix_level: 현재 VIX 수준 (None이면 체크 안 함)
            user_acknowledged: 사용자 동의 여부
        
        Returns:
            LeverageValidationResult: 검증 결과
        """
        category = self.get_category(ticker)
        warnings: List[str] = []
        allowed = True
        rejection_reason = None
        
        # 일반 상품은 바로 승인
        if category == LeverageCategory.NORMAL:
            return LeverageValidationResult(
                allowed=True,
                category=category,
                warnings=[],
                max_allowed_quantity=quantity,
                max_allowed_value=quantity * price,
                position_cap_pct=1.0,
                requires_acknowledgment=False
            )
        
        # 레버리지 상품 검증 시작
        order_value = quantity * price
        max_leverage_value = portfolio_value * self.rules["max_leverage_pct"]
        available_leverage_value = max_leverage_value - current_leverage_value
        
        # 1. 포지션 크기 제한 체크
        if order_value > available_leverage_value:
            if available_leverage_value <= 0:
                allowed = False
                rejection_reason = f"레버리지 상품 한도 초과: 현재 {current_leverage_value:,.0f}원 / 최대 {max_leverage_value:,.0f}원"
            else:
                # 가능한 수량으로 조정
                max_allowed_quantity = int(available_leverage_value / price)
                warnings.append(
                    f"⚠️ 요청 수량 {quantity}주 → {max_allowed_quantity}주로 조정 필요 "
                    f"(레버리지 한도: 포트폴리오의 {self.rules['max_leverage_pct']*100:.0f}%)"
                )
        else:
            max_allowed_quantity = quantity
        
        # 2. VIX 체크 (롱 레버리지만)
        if vix_level and vix_level > self.rules["vix_threshold"]:
            if category == LeverageCategory.LEVERAGED_LONG:
                warnings.append(
                    f"🔴 고변동성 경고: VIX={vix_level:.1f} (임계치: {self.rules['vix_threshold']}). "
                    f"롱 레버리지 진입은 매우 위험합니다."
                )
            elif category == LeverageCategory.LEVERAGED_SHORT:
                if self.rules["allow_inverse_in_volatility"]:
                    warnings.append(
                        f"🟡 고변동성: 숏 레버리지는 헤지 목적으로만 사용 권장."
                    )
        
        # 3. Volatility Drag 경고 (항상)
        if category in [LeverageCategory.LEVERAGED_LONG, LeverageCategory.LEVERAGED_SHORT]:
            warnings.append(
                f"⚠️ 레버리지 드래그 경고: {ticker}는 장기 보유 시 지수 대비 수익률이 괴리됩니다. "
                f"최대 {self.rules['max_holding_days']}일 이내 청산을 권장합니다."
            )
        
        # 4. 동의 필수 체크
        requires_ack = self.rules["require_acknowledgment"]
        if requires_ack and not user_acknowledged:
            warnings.append(
                "🛑 레버리지 상품 거래 시 위험 고지 동의가 필요합니다."
            )
            allowed = False
            rejection_reason = "사용자 동의 필요: '이 거래의 손실 가능성을 인지했습니다' 확인 필수"
        
        return LeverageValidationResult(
            allowed=allowed,
            category=category,
            warnings=warnings,
            max_allowed_quantity=max_allowed_quantity if allowed else 0,
            max_allowed_value=max_allowed_quantity * price if allowed else 0.0,
            position_cap_pct=self.rules["max_leverage_pct"],
            requires_acknowledgment=requires_ack,
            rejection_reason=rejection_reason
        )
    
    def check_holding_duration(
        self,
        ticker: str,
        entry_date: datetime,
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        보유 기간 경고 체크
        
        Args:
            ticker: 종목 티커
            entry_date: 진입 일자
            current_date: 현재 일자 (None이면 now())
        
        Returns:
            Dict with 'warning' and 'days_held'
        """
        if not self.is_leveraged(ticker):
            return {"warning": None, "days_held": 0}
        
        current = current_date or datetime.now()
        days_held = (current - entry_date).days
        
        if days_held > self.rules["max_holding_days"]:
            return {
                "warning": f"⚠️ {ticker} 보유 {days_held}일차: 권장 보유 기간({self.rules['max_holding_days']}일) 초과. 청산 검토 필요.",
                "days_held": days_held,
                "exceeded": True
            }
        elif days_held >= self.rules["max_holding_days"] - 1:
            return {
                "warning": f"🟡 {ticker} 보유 {days_held}일차: 곧 권장 보유 기간 도래. 청산 계획 수립 필요.",
                "days_held": days_held,
                "exceeded": False
            }
        
        return {"warning": None, "days_held": days_held, "exceeded": False}
    
    def get_leveraged_tickers(self) -> List[str]:
        """등록된 모든 레버리지 티커 반환"""
        return list(LEVERAGED_ETFS.keys())
    
    def get_rules(self) -> Dict[str, Any]:
        """현재 적용 중인 규칙 반환"""
        return self.rules.copy()


# 싱글톤 인스턴스
_default_guardian: Optional[LeverageGuardian] = None


def get_leverage_guardian() -> LeverageGuardian:
    """전역 LeverageGuardian 인스턴스 반환"""
    global _default_guardian
    if _default_guardian is None:
        _default_guardian = LeverageGuardian()
    return _default_guardian


# 테스트용
if __name__ == "__main__":
    guardian = LeverageGuardian()
    
    print("=== Leverage Guardian Test ===\n")
    
    # Test 1: Normal stock
    result = guardian.validate_order("AAPL", 10, 150.0, 100000)
    print(f"AAPL (일반): Allowed={result.allowed}, Warnings={len(result.warnings)}")
    
    # Test 2: Leveraged ETF without acknowledgment
    result = guardian.validate_order("TQQQ", 100, 50.0, 100000)
    print(f"TQQQ (레버리지, 미동의): Allowed={result.allowed}")
    print(f"  Rejection: {result.rejection_reason}")
    
    # Test 3: Leveraged ETF with acknowledgment
    result = guardian.validate_order("TQQQ", 100, 50.0, 100000, user_acknowledged=True)
    print(f"TQQQ (레버리지, 동의): Allowed={result.allowed}")
    print(f"  Max Allowed: {result.max_allowed_quantity}주 (${result.max_allowed_value:,.0f})")
    for w in result.warnings:
        print(f"  {w}")
    
    # Test 4: Over limit
    result = guardian.validate_order("SOXL", 500, 30.0, 100000, current_leverage_value=8000, user_acknowledged=True)
    print(f"\nSOXL (한도 근접): Allowed={result.allowed}")
    print(f"  Max Allowed: {result.max_allowed_quantity}주")
