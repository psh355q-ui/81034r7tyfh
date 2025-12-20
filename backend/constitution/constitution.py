"""
Constitution - 시스템 헌법

모든 규칙을 통합하고 검증하는 헌법 클래스

작성일: 2025-12-15
"""

from typing import Dict, Any, List, Tuple
from .risk_limits import RiskLimits
from .allocation_rules import AllocationRules
from .trading_constraints import TradingConstraints


class Constitution:
    """
    AI Trading System 헌법
    
    시스템의 모든 규칙을 통합 관리하고
    제안(Proposal)이 헌법을 준수하는지 검증합니다.
    
    Usage:
        const = Constitution()
        is_valid, violations = const.validate_proposal(proposal)
    """
    
    # ========================================
    # 헌법 조항 (Articles)
    # ========================================
    
    ARTICLES = {
        "제1조": {
            "title": "자본 보존 우선",
            "description": "자본 보존이 수익 추구에 우선한다"
        },
        "제2조": {
            "title": "설명 가능성",
            "description": "설명되지 않는 수익은 취하지 않는다"
        },
        "제3조": {
            "title": "인간 최종 결정권",
            "description": "최종 실행권은 인간에게 있다"
        },
        "제4조": {
            "title": "강제 개입",
            "description": "시장이 위험하면 시스템이 강제 개입한다"
        },
        "제5조": {
            "title": "헌법 개정",
            "description": "헌법 개정은 인간 승인이 필요하다"
        }
    }
    
    VERSION = "1.0.0"
    """헌법 버전"""
    
    ENACTED_DATE = "2025-12-15"
    """헌법 제정일"""
    
    def __init__(self):
        """헌법 초기화"""
        self.risk = RiskLimits()
        self.allocation = AllocationRules()
        self.trading = TradingConstraints()
    
    def validate_proposal(
        self,
        proposal: Dict[str, Any],
        context: Dict[str, Any] = None,
        skip_allocation_rules: bool = False  # Bootstrap/Backtest mode
    ) -> Tuple[bool, List[str], List[str]]:
        """
        제안이 헌법을 준수하는지 종합 검증
        
        Args:
            proposal: 매매 제안
            context: 시장/계좌 상황
            skip_allocation_rules: True면 배분 규칙 스킵 (BOOTSTRAP 단계)
        
        Returns:
            (is_valid, violations, violated_articles)
        """
        if context is None:
            context = {}
        
        violations = []
        violated_articles = []
        
        # 1. 리스크 검증 (제1조)
        position_value = proposal.get('position_value', 0)
        total_capital = context.get('total_capital', 1)
        
        risk_valid, risk_violations = self.risk.validate_position_size(
            position_value,
            total_capital
        )
        
        if not risk_valid:
            violations.extend(risk_violations)
            violated_articles.append("제1조: 자본 보존")
        
        # 2. 자산 배분 검증 (제1조)
        # BOOTSTRAP 모드에서는 스킵 (포트폴리오 형성 단계)
        if (not skip_allocation_rules and 
            'current_allocation' in context and 
            'market_regime' in context):
            stock_pct = context['current_allocation'].get('stock', 0)
            cash_pct = context['current_allocation'].get('cash', 0)
            regime = context['market_regime']
            
            alloc_valid, alloc_violations = self.allocation.validate_allocation(
                stock_pct,
                cash_pct,
                regime
            )
            
            if not alloc_valid:
                violations.extend(alloc_violations)
                violated_articles.append("제1조: 자본 보존 (배분 위반)")
        
        # 3. 거래 제약 검증 (제3조)
        if 'daily_trades' in context:
            daily_trades = context.get('daily_trades', 0)
            weekly_trades = context.get('weekly_trades', 0)
            
            freq_valid, freq_violations = self.trading.validate_trade_frequency(
                daily_trades,
                weekly_trades
            )
            
            if not freq_valid:
                violations.extend(freq_violations)
                violated_articles.append("제3조: 인간 결정권 (과도한 매매)")
        
        # 4. 주문 크기 검증
        if 'order_value_usd' in proposal:
            order_value = proposal['order_value_usd']
            daily_volume = context.get('daily_volume_usd', 10000000)
            
            size_valid, size_violations = self.trading.validate_order_size(
                order_value,
                total_capital,
                daily_volume
            )
            
            if not size_valid:
                violations.extend(size_violations)
                violated_articles.append("제1조: 자본 보존 (주문 크기)")
        
        # 5. 인간 승인 필수 (제3조)
        if not proposal.get('is_approved', False):
            if self.trading.REQUIRE_HUMAN_APPROVAL:
                violations.append("제3조 위반: 인간 승인이 필요합니다")
                violated_articles.append("제3조: 인간 최종 결정권")
        
        is_valid = len(violations) == 0
        
        return is_valid, violations, list(set(violated_articles))
    
    def validate_circuit_breaker_trigger(
        self,
        daily_loss: float,
        total_drawdown: float,
        vix: float
    ) -> Tuple[bool, str]:
        """
        Circuit Breaker 발동 여부 판단 (제4조)
        
        Args:
            daily_loss: 당일 손실률 (음수)
            total_drawdown: 총 낙폭 (음수)
            vix: 변동성 지수
            
        Returns:
            (should_trigger, reason)
        """
        # 손실 기준
        if abs(daily_loss) >= self.risk.DAILY_LOSS_CIRCUIT_BREAKER:
            return True, f"일 손실 {abs(daily_loss):.1%} ≥ {self.risk.DAILY_LOSS_CIRCUIT_BREAKER:.1%}"
        
        if abs(total_drawdown) >= self.risk.MAX_DRAWDOWN:
            return True, f"MDD {abs(total_drawdown):.1%} ≥ {self.risk.MAX_DRAWDOWN:.1%}"
        
        # VIX 기준
        if vix >= self.risk.VIX_DANGER_THRESHOLD:
            return True, f"VIX {vix} ≥ {self.risk.VIX_DANGER_THRESHOLD} (위험 모드)"
        
        return False, ""
    
    def get_violated_articles_summary(self, violated_articles: List[str]) -> str:
        """
        위반된 조항 요약 텍스트 생성
        
        Args:
            violated_articles: 위반 조항 리스트
            
        Returns:
            요약 텍스트
        """
        if not violated_articles:
            return "헌법 준수"
        
        summary = "⚠️ 헌법 위반:\n"
        
        for article in violated_articles:
            # "제1조: 자본 보존"에서 번호 추출
            article_num = article.split(':')[0].strip()
            
            if article_num in self.ARTICLES:
                article_info = self.ARTICLES[article_num]
                summary += f"  • {article_num} ({article_info['title']})\n"
        
        return summary
    
    def get_constitution_summary(self) -> str:
        """
        헌법 전체 요약
        
        Returns:
            헌법 요약 텍스트
        """
        summary = f"🏛️ AI Trading System 헌법 v{self.VERSION} ({self.ENACTED_DATE})\n\n"
        
        for article_num, article_info in self.ARTICLES.items():
            summary += f"{article_num} - {article_info['title']}\n"
            summary += f'  "{article_info["description"]}"\n\n'
        
        return summary


if __name__ == "__main__":
    # 테스트
    print("=== Constitution Test ===\n")
    
    const = Constitution()
    
    # 헌법 요약
    print(const.get_constitution_summary())
    
    # 테스트 제안
    proposal = {
        'ticker': 'AAPL',
        'action': 'BUY',
        'position_value': 15000,
        'order_value_usd': 15000,
        'is_approved': False
    }
    
    context = {
        'total_capital': 100000,
        'current_allocation': {'stock': 0.75, 'cash': 0.25},
        'market_regime': 'risk_on',
        'daily_trades': 2,
        'weekly_trades': 5,
        'daily_volume_usd': 5000000
    }
    
    # 검증
    is_valid, violations, violated_articles = const.validate_proposal(proposal, context)
    
    print("제안 검증 결과:")
    print(f"  유효성: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    if violations:
        print("\n위반 사항:")
        for v in violations:
            print(f"  • {v}")
    
    if violated_articles:
        print(f"\n{const.get_violated_articles_summary(violated_articles)}")
    
    # Circuit Breaker 테스트
    print("\nCircuit Breaker 테스트:")
    should_trigger, reason = const.validate_circuit_breaker_trigger(-0.04, -0.08, 22)
    print(f"  발동 여부: {'🚨 Yes' if should_trigger else '✅ No'}")
    if should_trigger:
        print(f"  사유: {reason}")
    
    print("\n✅ Constitution 통합 완료!")
