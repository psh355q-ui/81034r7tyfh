"""
Risk Limits - 리스크 한도

시스템의 불변 리스크 제한 규칙

작성일: 2025-12-15
헌법: 제1조 (자본 보존 우선)
"""


class RiskLimits:
    """
    리스크 한도 상수
    
    이 값들은 시스템의 헌법이며 런타임에 수정 불가능합니다.
    수정하려면 check_integrity.py의 해시를 업데이트해야 합니다.
    """
    
    # ========================================
    # 손실 제한 (Loss Limits)
    # ========================================
    
    MAX_DAILY_LOSS = 0.05
    """일 최대 손실 5%"""
    
    MAX_DRAWDOWN = 0.10
    """최대 낙폭 (MDD) 10%"""
    
    MAX_CONSECUTIVE_LOSSES = 3
    """연속 손실 거래 3회까지 허용"""
    
    DAILY_LOSS_CIRCUIT_BREAKER = 0.03
    """일 손실 3% 도달 시 Circuit Breaker 발동"""
    
    # ========================================
    # 포지션 제한 (Position Limits)
    # ========================================
    
    MAX_POSITION_SIZE = 0.20
    """단일 종목 최대 비중 20%"""
    
    MAX_SECTOR_EXPOSURE = 0.40
    """단일 섹터 최대 노출 40%"""
    
    MAX_TOTAL_POSITIONS = 10
    """동시 보유 최대 종목 수 10개"""
    
    MIN_POSITION_SIZE_USD = 1000
    """최소 포지션 크기 $1,000"""
    
    # ========================================
    # 변동성 제한 (Volatility Limits)
    # ========================================
    
    VIX_CAUTION_THRESHOLD = 20
    """VIX 20 초과 시 주의 모드"""
    
    VIX_DANGER_THRESHOLD = 25
    """VIX 25 초과 시 방어 모드 (신규 진입 금지)"""
    
    MAX_PORTFOLIO_VOLATILITY = 0.30
    """포트폴리오 연 변동성 30% 이하"""
    
    # ========================================
    # 레버리지 및 파생상품 (Leverage & Derivatives)
    # ========================================
    
    MAX_LEVERAGE = 1.0
    """레버리지 금지 (1.0 = 현금 범위 내)"""
    
    ALLOW_OPTIONS = False
    """옵션 거래 금지"""
    
    ALLOW_SHORT_SELLING = False
    """공매도 금지"""
    
    ALLOW_MARGIN_TRADING = False
    """마진 거래 금지"""
    
    # ========================================
    # 집중도 제한 (Concentration Limits)
    # ========================================
    
    MAX_CORRELATION_THRESHOLD = 0.70
    """보유 종목 간 최대 상관계수 0.70"""
    
    DIVERSIFICATION_MIN_STOCKS = 3
    """최소 분산 종목 수 3개"""
    
    @classmethod
    def get_all_limits(cls) -> dict:
        """모든 제한 사항을 딕셔너리로 반환"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def validate_loss(cls, daily_loss: float, total_drawdown: float) -> tuple[bool, list[str]]:
        """
        손실이 한도 내에 있는지 검증
        
        Args:
            daily_loss: 당일 손실률 (음수)
            total_drawdown: 총 낙폭 (음수)
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        if abs(daily_loss) > cls.MAX_DAILY_LOSS:
            violations.append(
                f"일 손실 한도 초과: {daily_loss:.2%} > {cls.MAX_DAILY_LOSS:.2%}"
            )
        
        if abs(total_drawdown) > cls.MAX_DRAWDOWN:
            violations.append(
                f"최대 낙폭 초과: {total_drawdown:.2%} > {cls.MAX_DRAWDOWN:.2%}"
            )
        
        return len(violations) == 0, violations
    
    @classmethod
    def validate_position_size(cls, position_value: float, total_capital: float) -> tuple[bool, list[str]]:
        """
        포지션 크기가 한도 내에 있는지 검증
        
        Args:
            position_value: 포지션 가치
            total_capital: 총 자본
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        position_pct = position_value / total_capital if total_capital > 0 else 0
        
        if position_pct > cls.MAX_POSITION_SIZE:
            violations.append(
                f"포지션 크기 초과: {position_pct:.2%} > {cls.MAX_POSITION_SIZE:.2%}"
            )
        
        if position_value < cls.MIN_POSITION_SIZE_USD:
            violations.append(
                f"포지션 크기 미달: ${position_value:,.0f} < ${cls.MIN_POSITION_SIZE_USD:,.0f}"
            )
        
        return len(violations) == 0, violations


if __name__ == "__main__":
    # 테스트
    print("=== Risk Limits Test ===\n")
    
    print("손실 제한:")
    print(f"  일 최대 손실: {RiskLimits.MAX_DAILY_LOSS:.1%}")
    print(f"  최대 낙폭: {RiskLimits.MAX_DRAWDOWN:.1%}")
    
    print("\n포지션 제한:")
    print(f"  단일 종목: {RiskLimits.MAX_POSITION_SIZE:.1%}")
    print(f"  섹터 노출: {RiskLimits.MAX_SECTOR_EXPOSURE:.1%}")
    
    print("\n변동성 제한:")
    print(f"  VIX 주의: {RiskLimits.VIX_CAUTION_THRESHOLD}")
    print(f"  VIX 위험: {RiskLimits.VIX_DANGER_THRESHOLD}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, violations = RiskLimits.validate_loss(-0.03, -0.08)
    print(f"  손실 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    is_valid, violations = RiskLimits.validate_position_size(15000, 100000)
    print(f"  포지션 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    print("\n✅ Risk Limits 정의 완료!")
