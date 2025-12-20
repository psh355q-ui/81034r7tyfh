"""
Trading Constraints - 거래 제약

매매 실행 시 준수해야 할 불변 규칙

작성일: 2025-12-15
헌법: 제3조 (최종 실행권은 인간)
"""


class TradingConstraints:
    """
    거래 제약 상수
    
    거래 시간, 빈도, 크기 등의 운영 제약
    """
    
    # ========================================
    # 거래 시간 (Trading Hours)
    # ========================================
    
    MARKET_OPEN_BUFFER_MINUTES = 5
    """시장 개장 후 5분 대기 (변동성 회피)"""
    
    MARKET_CLOSE_BUFFER_MINUTES = 10
    """시장 마감 10분 전 거래 중단"""
    
    ALLOW_PREMARKET_TRADING = False
    """프리마켓 거래 금지"""
    
    ALLOW_AFTERHOURS_TRADING = False
    """시간외 거래 금지"""
    
    # ========================================
    # 거래 빈도 (Trading Frequency)
    # ========================================
    
    MAX_DAILY_TRADES = 5
    """일 최대 거래 5회 (과도한 매매 방지)"""
    
    MAX_WEEKLY_TRADES = 15
    """주 최대 거래 15회"""
    
    MIN_HOLD_PERIOD_HOURS = 24
    """최소 보유 기간 24시간 (단타 방지)"""
    
    COOLDOWN_PERIOD_HOURS = 4
    """동일 종목 재매매 대기 4시간"""
    
    # ========================================
    # 주문 크기 (Order Size)
    # ========================================
    
    MAX_ORDER_SIZE_USD = 50000
    """단일 주문 최대 $50,000"""
    
    MIN_ORDER_SIZE_USD = 1000
    """단일 주문 최소 $1,000"""
    
    MAX_ORDER_PERCENTAGE = 0.10
    """총 자본 대비 단일 주문 10% 이하"""
    
    # ========================================
    # 주문 유형 (Order Types)
    # ========================================
    
    ALLOW_MARKET_ORDERS = True
    """시장가 주문 허용"""
    
    ALLOW_LIMIT_ORDERS = True
    """지정가 주문 허용"""
    
    ALLOW_STOP_ORDERS = True
    """손절 주문 허용"""
    
    ALLOW_CONDITIONAL_ORDERS = False
    """조건부 주문 금지"""
    
    # ========================================
    # 레버리지 및 파생 (Leverage & Derivatives)
    # ========================================
    
    ALLOW_SHORT_SELLING = False
    """공매도 금지"""
    
    ALLOW_LEVERAGE = False
    """레버리지 금지"""
    
    ALLOW_OPTIONS = False
    """옵션 거래 금지"""
    
    ALLOW_FUTURES = False
    """선물 거래 금지"""
    
    # ========================================
    # 안전 장치 (Safety Mechanisms)
    # ========================================
    
    REQUIRE_HUMAN_APPROVAL = True
    """모든 거래는 인간 승인 필요 (헌법 제3조)"""
    
    MAX_ORDERS_WITHOUT_REVIEW = 3
    """검토 없이 연속 3회까지만 가능"""
    
    CIRCUIT_BREAKER_COOLDOWN_HOURS = 24
    """Circuit Breaker 발동 후 24시간 대기"""
    
    # ========================================
    # 유동성 (Liquidity)
    # ========================================
    
    MIN_DAILY_VOLUME_USD = 1000000
    """거래 대상 종목 일 거래량 $1M 이상"""
    
    MAX_VOLUME_PARTICIPATION = 0.05
    """일 거래량의 5% 이하만 매매 (시장 충격 최소화)"""
    
    @classmethod
    def validate_order_timing(cls, market_open: bool, minutes_from_open: int, minutes_to_close: int) -> tuple[bool, list[str]]:
        """
        주문 시간이 적절한지 검증
        
        Args:
            market_open: 시장 개장 여부
            minutes_from_open: 개장 후 경과 분
            minutes_to_close: 마감까지 남은 분
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        if not market_open:
            violations.append("시장이 개장하지 않았습니다")
        
        if minutes_from_open < cls.MARKET_OPEN_BUFFER_MINUTES:
            violations.append(
                f"개장 대기 시간 부족: {minutes_from_open}분 < {cls.MARKET_OPEN_BUFFER_MINUTES}분"
            )
        
        if minutes_to_close < cls.MARKET_CLOSE_BUFFER_MINUTES:
            violations.append(
                f"마감 임박: {minutes_to_close}분 < {cls.MARKET_CLOSE_BUFFER_MINUTES}분"
            )
        
        return len(violations) == 0, violations
    
    @classmethod
    def validate_order_size(
        cls,
        order_value_usd: float,
        total_capital_usd: float,
        daily_volume_usd: float
    ) -> tuple[bool, list[str]]:
        """
        주문 크기가 적절한지 검증
        
        Args:
            order_value_usd: 주문 금액 ($)
            total_capital_usd: 총 자본 ($)
            daily_volume_usd: 종목 일 거래량 ($)
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        # 절대 크기 제약
        # 대형 자본($100K+)은 비율 제한만 적용, 소형 자본은 절대 금액도 체크
        if total_capital_usd < 100_000:  # $100K 미만
            if order_value_usd > cls.MAX_ORDER_SIZE_USD:
                violations.append(
                    f"주문 크기 초과: ${order_value_usd:,.0f} > ${cls.MAX_ORDER_SIZE_USD:,.0f}"
                )
        
        if order_value_usd < cls.MIN_ORDER_SIZE_USD:
            violations.append(
                f"주문 크기 미달: ${order_value_usd:,.0f} < ${cls.MIN_ORDER_SIZE_USD:,.0f}"
            )
        
        # 자본 대비 비율 (모든 규모에 적용)
        if total_capital_usd > 0:
            order_pct = order_value_usd / total_capital_usd
            if order_pct > cls.MAX_ORDER_PERCENTAGE:
                violations.append(
                    f"자본 대비 주문 과다: {order_pct:.1%} > {cls.MAX_ORDER_PERCENTAGE:.1%}"
                )
        
        # 유동성 검증
        if daily_volume_usd < cls.MIN_DAILY_VOLUME_USD:
            violations.append(
                f"거래량 부족: ${daily_volume_usd:,.0f} < ${cls.MIN_DAILY_VOLUME_USD:,.0f}"
            )
        
        if daily_volume_usd > 0:
            participation = order_value_usd / daily_volume_usd
            if participation > cls.MAX_VOLUME_PARTICIPATION:
                violations.append(
                    f"일 거래량 대비 주문 과다: {participation:.2%} > {cls.MAX_VOLUME_PARTICIPATION:.2%}"
                )
        
        return len(violations) == 0, violations
    
    @classmethod
    def validate_trade_frequency(
        cls,
        daily_trades: int,
        weekly_trades: int
    ) -> tuple[bool, list[str]]:
        """
        거래 빈도가 제한 내인지 검증
        
        Args:
            daily_trades: 오늘 거래 횟수
            weekly_trades: 이번주 거래 횟수
            
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        if daily_trades >= cls.MAX_DAILY_TRADES:
            violations.append(
                f"일 거래 한도 도달: {daily_trades}회 >= {cls.MAX_DAILY_TRADES}회"
            )
        
        if weekly_trades >= cls.MAX_WEEKLY_TRADES:
            violations.append(
                f"주 거래 한도 도달: {weekly_trades}회 >= {cls.MAX_WEEKLY_TRADES}회"
            )
        
        return len(violations) == 0, violations


if __name__ == "__main__":
    # 테스트
    print("=== Trading Constraints Test ===\n")
    
    print("거래 시간 제약:")
    print(f"  개장 대기: {TradingConstraints.MARKET_OPEN_BUFFER_MINUTES}분")
    print(f"  마감 대기: {TradingConstraints.MARKET_CLOSE_BUFFER_MINUTES}분")
    
    print("\n거래 빈도 제약:")
    print(f"  일 최대: {TradingConstraints.MAX_DAILY_TRADES}회")
    print(f"  주 최대: {TradingConstraints.MAX_WEEKLY_TRADES}회")
    
    print("\n주문 크기:")
    print(f"  최소: ${TradingConstraints.MIN_ORDER_SIZE_USD:,}")
    print(f"  최대: ${TradingConstraints.MAX_ORDER_SIZE_USD:,}")
    
    print("\n안전 장치:")
    print(f"  인간 승인 필요: {TradingConstraints.REQUIRE_HUMAN_APPROVAL}")
    print(f"  공매도 금지: {not TradingConstraints.ALLOW_SHORT_SELLING}")
    
    # 검증 테스트
    print("\n검증 테스트:")
    is_valid, _ = TradingConstraints.validate_order_timing(True, 10, 20)
    print(f"  시간 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    is_valid, _ = TradingConstraints.validate_order_size(10000, 100000, 5000000)
    print(f"  크기 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    print("\n✅ Trading Constraints 정의 완료!")
