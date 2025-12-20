"""
Portfolio Phase - 포트폴리오 단계 관리

BOOTSTRAP vs ACTIVE 단계 구분 및 전환 조건

작성일: 2025-12-15
"""

from enum import Enum


class PortfolioPhase(Enum):
    """포트폴리오 단계"""
    
    BOOTSTRAP = "bootstrap"
    """초기 형성 단계 (배분 규칙 완화)"""
    
    ACTIVE = "active"
    """정상 운용 단계 (전체 규칙 적용)"""


class BootstrapExitConditions:
    """
    BOOTSTRAP 단계 종료 조건
    
    백테스트 재현성과 명확한 단계 전환을 위한 조건 정의
    """
    
    MIN_TRADES = 3
    """최소 거래 3건 실행"""
    
    MIN_STOCK_EXPOSURE = 0.30
    """주식 비중 30% 이상 달성"""
    
    MAX_DAYS = 5
    """최대 5일 경과 (강제 종료)"""
    
    @classmethod
    def should_exit_bootstrap(
        cls,
        trades_count: int,
        stock_exposure: float,
        days_in_bootstrap: int
    ) -> tuple[bool, str]:
        """
        BOOTSTRAP 단계 종료 여부 판단
        
        Args:
            trades_count: 실행된 거래 횟수
            stock_exposure: 현재 주식 비중 (0.0-1.0)
            days_in_bootstrap: BOOTSTRAP 단계 경과 일수
            
        Returns:
            (should_exit, reason)
            
        Example:
            >>> should_exit, reason = BootstrapExitConditions.should_exit_bootstrap(
            ...     trades_count=4,
            ...     stock_exposure=0.25,
            ...     days_in_bootstrap=2
            ... )
            >>> print(should_exit, reason)
            True "거래 4건 달성"
        """
        # 조건 1: 충분한 거래 실행
        if trades_count >= cls.MIN_TRADES:
            return True, f"거래 {trades_count}건 달성"
        
        # 조건 2: 충분한 주식 비중
        if stock_exposure >= cls.MIN_STOCK_EXPOSURE:
            return True, f"주식 비중 {stock_exposure:.1%} 달성"
        
        # 조건 3: 최대 기간 초과 (강제 종료)
        if days_in_bootstrap >= cls.MAX_DAYS:
            return True, f"최대 기간 {days_in_bootstrap}일 도달 (강제 종료)"
        
        # BOOTSTRAP 계속
        return False, f"BOOTSTRAP 진행 중 (거래 {trades_count}건, 주식 {stock_exposure:.1%}, {days_in_bootstrap}일차)"


if __name__ == "__main__":
    # 테스트
    print("=== Portfolio Phase Test ===\n")
    
    print("Enum 값:")
    print(f"  BOOTSTRAP: {PortfolioPhase.BOOTSTRAP.value}")
    print(f"  ACTIVE: {PortfolioPhase.ACTIVE.value}")
    
    print("\nBOOTSTRAP 종료 조건:")
    print(f"  최소 거래: {BootstrapExitConditions.MIN_TRADES}건")
    print(f"  최소 주식 비중: {BootstrapExitConditions.MIN_STOCK_EXPOSURE:.1%}")
    print(f"  최대 기간: {BootstrapExitConditions.MAX_DAYS}일")
    
    # 시나리오 테스트
    print("\n테스트 시나리오:")
    
    scenarios = [
        (1, 0.10, 1, "거래 부족, 주식 부족, 기간 OK"),
        (3, 0.15, 2, "거래 OK → 종료"),
        (2, 0.35, 3, "주식 OK → 종료"),
        (0, 0.00, 5, "강제 종료 → 종료"),
    ]
    
    for trades, exposure, days, desc in scenarios:
        should_exit, reason = BootstrapExitConditions.should_exit_bootstrap(
            trades, exposure, days
        )
        status = "✅ 종료" if should_exit else "⏳ 계속"
        print(f"  {desc}")
        print(f"    → {status}: {reason}")
    
    print("\n✅ Portfolio Phase 정의 완료!")
