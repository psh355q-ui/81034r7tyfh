"""
Allocation Rules - 자산 배분 규칙

포트폴리오 자산 배분의 불변 원칙

작성일: 2025-12-15
헌법: 제1조 (자본 보존 우선)
"""


class AllocationRules:
    """
    자산 배분 규칙 상수
    
    시장 체제별, 리스크 프로필별 자산 배분 원칙
    """
    
    # ========================================
    # 기본 배분 (Base Allocation)
    # ========================================
    
    MIN_CASH_RESERVE = 0.10
    """최소 현금 보유 10% (비상 자금)"""
    
    MAX_STOCK_ALLOCATION = 0.90
    """주식 최대 배분 90%"""
    
    TARGET_CASH_RESERVE = 0.15
    """목표 현금 비율 15%"""
    
    # ========================================
    # 시장 체제별 배분 (Regime-Based Allocation)
    # ========================================
    
    # Risk On (위험 선호) - 상승장
    RISK_ON_STOCK_MIN = 0.70
    RISK_ON_STOCK_MAX = 0.90
    RISK_ON_CASH_MIN = 0.10
    
    # Neutral (중립) - 혼조장
    NEUTRAL_STOCK_MIN = 0.40
    NEUTRAL_STOCK_MAX = 0.60
    NEUTRAL_CASH_MIN = 0.40
    
    # Risk Off (위험 회피) - 하락장
    RISK_OFF_STOCK_MIN = 0.10
    RISK_OFF_STOCK_MAX = 0.30
    RISK_OFF_CASH_MIN = 0.70
    
    # ========================================
    # 리밸런싱 (Rebalancing)
    # ========================================
    
    REBALANCE_THRESHOLD = 0.05
    """목표 비중 대비 5% 이상 편차 시 리밸런싱"""
    
    REBALANCE_FREQUENCY_DAYS = 7
    """최소 리밸런싱 주기 7일 (주 1회)"""
    
    MAX_REBALANCE_TRADE_SIZE = 0.10
    """단일 리밸런싱 거래 크기 10% 이하"""
    
    # ========================================
    # 섹터 배분 (Sector Allocation)
    # ========================================
    
    MAX_SECTOR_WEIGHT = 0.40
    """단일 섹터 최대 40%"""
    
    MIN_SECTOR_DIVERSIFICATION = 3
    """최소 섹터 분산 3개"""
    
    SECTOR_REBALANCE_THRESHOLD = 0.10
    """섹터 비중 10% 편차 시 조정"""
    
    # ========================================
    # 유동성 관리 (Liquidity Management)
    # ========================================
    
    EMERGENCY_CASH_THRESHOLD = 0.05
    """긴급 현금 5% 이하 시 경고"""
    
    LIQUIDITY_BUFFER_FOR_MARGIN_CALL = 0.20
    """마진콜 대비 유동성 버퍼 20%"""
    
    @classmethod
    def get_regime_allocation(cls, regime: str) -> dict:
        """
        시장 체제에 따른 권장 배분 반환
        
        Args:
            regime: 'risk_on', 'neutral', 'risk_off'
            
        Returns:
            {stock_min, stock_max, cash_min}
        """
        regime = regime.lower()
        
        if regime == 'risk_on':
            return {
                'stock_min': cls.RISK_ON_STOCK_MIN,
                'stock_max': cls.RISK_ON_STOCK_MAX,
                'cash_min': cls.RISK_ON_CASH_MIN
            }
        elif regime == 'risk_off':
            return {
                'stock_min': cls.RISK_OFF_STOCK_MIN,
                'stock_max': cls.RISK_OFF_STOCK_MAX,
                'cash_min': cls.RISK_OFF_CASH_MIN
            }
        else:  # neutral
            return {
                'stock_min': cls.NEUTRAL_STOCK_MIN,
                'stock_max': cls.NEUTRAL_STOCK_MAX,
                'cash_min': cls.NEUTRAL_CASH_MIN
            }
    
    @classmethod
    def validate_allocation(
        cls,
        stock_pct: float,
        cash_pct: float,
        regime: str = 'neutral'
    ) -> tuple[bool, list[str]]:
        """
        자산 배분이 규칙을 준수하는지 검증
        
        Args:
            stock_pct: 주식 비율
            cash_pct: 현금 비율
            regime: 시장 체제
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        # 기본 제약
        if cash_pct < cls.MIN_CASH_RESERVE:
            violations.append(
                f"현금 보유 부족: {cash_pct:.1%} < {cls.MIN_CASH_RESERVE:.1%}"
            )
        
        if stock_pct > cls.MAX_STOCK_ALLOCATION:
            violations.append(
                f"주식 비중 과다: {stock_pct:.1%} > {cls.MAX_STOCK_ALLOCATION:.1%}"
            )
        
        # 체제별 제약
        regime_rules = cls.get_regime_allocation(regime)
        
        if stock_pct < regime_rules['stock_min']:
            violations.append(
                f"{regime} 체제: 주식 비중 미달 "
                f"({stock_pct:.1%} < {regime_rules['stock_min']:.1%})"
            )
        
        if stock_pct > regime_rules['stock_max']:
            violations.append(
                f"{regime} 체제: 주식 비중 초과 "
                f"({stock_pct:.1%} > {regime_rules['stock_max']:.1%})"
            )
        
        return len(violations) == 0, violations
    
    @classmethod
    def needs_rebalancing(
        cls,
        current_allocation: dict,
        target_allocation: dict
    ) -> tuple[bool, list[str]]:
        """
        리밸런싱 필요 여부 판단
        
        Args:
            current_allocation: {stock: 0.65, cash: 0.35}
            target_allocation: {stock: 0.70, cash: 0.30}
            
        Returns:
            (needs_rebalance, reasons)
        """
        reasons = []
        needs_rebalance = False
        
        for asset in ['stock', 'cash']:
            current = current_allocation.get(asset, 0)
            target = target_allocation.get(asset, 0)
            diff = abs(current - target)
            
            if diff > cls.REBALANCE_THRESHOLD:
                needs_rebalance = True
                reasons.append(
                    f"{asset}: {current:.1%} → {target:.1%} "
                    f"(편차 {diff:.1%})"
                )
        
        return needs_rebalance, reasons


if __name__ == "__main__":
    # 테스트
    print("=== Allocation Rules Test ===\n")
    
    print("기본 배분:")
    print(f"  최소 현금: {AllocationRules.MIN_CASH_RESERVE:.1%}")
    print(f"  최대 주식: {AllocationRules.MAX_STOCK_ALLOCATION:.1%}")
    
    print("\n체제별 배분:")
    for regime in ['risk_on', 'neutral', 'risk_off']:
        rules = AllocationRules.get_regime_allocation(regime)
        print(f"  {regime}: 주식 {rules['stock_min']:.1%}-{rules['stock_max']:.1%}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, violations = AllocationRules.validate_allocation(0.75, 0.25, 'risk_on')
    print(f"  Risk On 배분: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    # 리밸런싱 테스트
    current = {'stock': 0.65, 'cash': 0.35}
    target = {'stock': 0.75, 'cash': 0.25}
    needs, reasons = AllocationRules.needs_rebalancing(current, target)
    print(f"  리밸런싱 필요: {'✅ Yes' if needs else '❌ No'}")
    
    print("\n✅ Allocation Rules 정의 완료!")
