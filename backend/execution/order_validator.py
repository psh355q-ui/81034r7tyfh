"""
Order Validator - Hard Rules Enforcement

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    주문 검증 - Hard Rules 강제 적용
    - AI가 해석할 수 없는 코드 기반 검증
    - 모든 주문은 이 검증을 통과해야 실행 가능
    - 위반 시 즉시 거부 (AI 판단 불가)

Hard Rules (Code-Enforced):
    1. Position Size > 30% portfolio → REJECT
    2. Total Portfolio Risk > 5% → REJECT
    3. No Stop Loss → REJECT
    4. Insufficient Cash → REJECT
    5. Blacklist Symbol → REJECT
    6. Market Closed → REJECT (except emergency)
    7. Duplicate Order (within 5min) → REJECT
    8. Position Count > Max (20) → REJECT

ChatGPT's Key Insight:
    "Hard Rules는 AI가 해석하면 안됨. 코드로 강제해야 함.
     AI는 '리스크가 높지만 기회가 좋다'고 판단할 수 있지만,
     Hard Rule은 예외 없이 거부해야 함."
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum


class ValidationResult(Enum):
    """검증 결과"""
    APPROVED = "approved"      # 승인
    REJECTED = "rejected"      # 거부
    WARNING = "warning"        # 경고 (승인하되 주의)


class OrderValidator:
    """주문 검증기 - Hard Rules 강제 적용"""

    def __init__(self):
        """Initialize Order Validator"""

        # ===================================================================
        # HARD RULES (Code-Enforced - NO AI INTERPRETATION)
        # ===================================================================
        self.HARD_RULES = {
            # Position & Risk Limits
            'max_position_size_pct': 0.30,      # 30% 포지션 상한
            'max_portfolio_risk_pct': 0.05,     # 5% 포트폴리오 리스크 상한
            'max_position_count': 20,           # 최대 포지션 개수
            'min_stop_loss_pct': 0.001,         # 0.1% 최소 Stop Loss (0은 불가)
            'max_stop_loss_pct': 0.10,          # 10% 최대 Stop Loss

            # Cash & Margin
            'min_cash_reserve_pct': 0.05,       # 5% 현금 보유 필수
            'margin_allowed': False,            # 마진 거래 불가

            # Order Controls
            'duplicate_order_window_sec': 300,  # 5분 이내 중복 주문 금지
            'max_order_value_usd': 100000,      # 단일 주문 최대 $100k

            # Market & Symbol Controls
            'allow_market_closed': False,       # 시장 폐장 시 거래 금지
            'blacklist_symbols': [],            # 거래 금지 종목 (관리자 설정)

            # Emergency Controls
            'circuit_breaker_activated': False,  # 서킷브레이커 발동 시 매도만 허용
        }

        # Order history (for duplicate detection)
        self.order_history: List[Dict[str, Any]] = []

    def validate(
        self,
        order: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        market_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        주문 검증 수행

        Args:
            order: 주문 정보
                {
                    'symbol': str,
                    'action': 'buy' | 'sell',
                    'quantity': int,
                    'price': float,
                    'order_value': float,
                    'position_size_pct': float,
                    'stop_loss_pct': float (required for buy),
                    'timestamp': str
                }
            portfolio_state: 포트폴리오 상태
                {
                    'total_value': float,
                    'available_cash': float,
                    'total_risk': float,
                    'positions': List[Dict],
                    'position_count': int
                }
            market_state: 시장 상태 (optional)
                {
                    'is_market_open': bool,
                    'circuit_breaker': bool,
                    'vix': float
                }

        Returns:
            Dict containing:
                - result: APPROVED | REJECTED | WARNING
                - reasoning: 검증 결과 근거
                - violations: Hard Rule 위반 내역
                - warnings: 경고 사항
                - can_execute: bool (실행 가능 여부)
        """
        violations = []
        warnings = []

        # ================================================================
        # RULE 1: Position Size > 30%
        # ================================================================
        position_size_pct = order.get('position_size_pct', 0.0)
        if position_size_pct > self.HARD_RULES['max_position_size_pct']:
            violations.append(
                f"Position size {position_size_pct*100:.1f}% exceeds max {self.HARD_RULES['max_position_size_pct']*100}%"
            )

        # ================================================================
        # RULE 2: Total Portfolio Risk > 5%
        # ================================================================
        total_risk = portfolio_state.get('total_risk', 0.0)
        if total_risk > self.HARD_RULES['max_portfolio_risk_pct']:
            violations.append(
                f"Portfolio risk {total_risk*100:.1f}% exceeds max {self.HARD_RULES['max_portfolio_risk_pct']*100}%"
            )

        # ================================================================
        # RULE 3: Stop Loss Required (for buy orders)
        # ================================================================
        if order['action'] == 'buy':
            stop_loss_pct = order.get('stop_loss_pct', 0.0)
            if stop_loss_pct < self.HARD_RULES['min_stop_loss_pct']:
                violations.append(
                    f"Stop loss required for buy orders (minimum {self.HARD_RULES['min_stop_loss_pct']*100:.1f}%)"
                )
            elif stop_loss_pct > self.HARD_RULES['max_stop_loss_pct']:
                violations.append(
                    f"Stop loss {stop_loss_pct*100:.1f}% exceeds max {self.HARD_RULES['max_stop_loss_pct']*100}%"
                )

        # ================================================================
        # RULE 4: Insufficient Cash
        # ================================================================
        if order['action'] == 'buy':
            order_value = order.get('order_value', 0.0)
            available_cash = portfolio_state.get('available_cash', 0.0)
            total_value = portfolio_state.get('total_value', 1.0)

            # Cash reserve requirement
            min_cash_reserve = total_value * self.HARD_RULES['min_cash_reserve_pct']
            cash_after_order = available_cash - order_value

            if order_value > available_cash:
                violations.append(
                    f"Insufficient cash: ${order_value:,.0f} required, ${available_cash:,.0f} available"
                )
            elif cash_after_order < min_cash_reserve:
                violations.append(
                    f"Cash reserve violation: ${cash_after_order:,.0f} remaining < ${min_cash_reserve:,.0f} required"
                )

        # ================================================================
        # RULE 5: Blacklist Symbol
        # ================================================================
        symbol = order.get('symbol', '')
        if symbol in self.HARD_RULES['blacklist_symbols']:
            violations.append(
                f"Symbol {symbol} is blacklisted"
            )

        # ================================================================
        # RULE 6: Market Closed
        # ================================================================
        if market_state and not self.HARD_RULES['allow_market_closed']:
            is_market_open = market_state.get('is_market_open', True)
            if not is_market_open and order['action'] == 'buy':
                violations.append(
                    "Market is closed - buy orders not allowed"
                )
            elif not is_market_open and order['action'] == 'sell':
                # Sell orders allowed even when market closed (emergency exit)
                warnings.append(
                    "Market is closed - sell order allowed for emergency exit"
                )

        # ================================================================
        # RULE 7: Duplicate Order (within 5 minutes)
        # ================================================================
        duplicate_check = self._check_duplicate_order(order)
        if duplicate_check['is_duplicate']:
            violations.append(
                f"Duplicate order within {self.HARD_RULES['duplicate_order_window_sec']}s: {duplicate_check['previous_order']}"
            )

        # ================================================================
        # RULE 8: Position Count > Max
        # ================================================================
        position_count = portfolio_state.get('position_count', 0)
        if order['action'] == 'buy' and position_count >= self.HARD_RULES['max_position_count']:
            violations.append(
                f"Position count {position_count} exceeds max {self.HARD_RULES['max_position_count']}"
            )

        # ================================================================
        # RULE 9: Max Order Value
        # ================================================================
        order_value = order.get('order_value', 0.0)
        if order_value > self.HARD_RULES['max_order_value_usd']:
            violations.append(
                f"Order value ${order_value:,.0f} exceeds max ${self.HARD_RULES['max_order_value_usd']:,.0f}"
            )

        # ================================================================
        # RULE 10: Circuit Breaker (only sell allowed)
        # ================================================================
        if market_state:
            circuit_breaker = market_state.get('circuit_breaker', False)
            if circuit_breaker and order['action'] == 'buy':
                violations.append(
                    "Circuit breaker activated - only sell orders allowed"
                )

        # ================================================================
        # RULE 11: Margin Trading (not allowed)
        # ================================================================
        if not self.HARD_RULES['margin_allowed']:
            # Check if order would require margin
            if order['action'] == 'buy':
                order_value = order.get('order_value', 0.0)
                available_cash = portfolio_state.get('available_cash', 0.0)
                if order_value > available_cash:
                    violations.append(
                        "Margin trading not allowed"
                    )

        # ================================================================
        # Determine Result
        # ================================================================
        if violations:
            result = ValidationResult.REJECTED.value
            reasoning = f"Order rejected: {', '.join(violations)}"
            can_execute = False
        elif warnings:
            result = ValidationResult.WARNING.value
            reasoning = f"Order approved with warnings: {', '.join(warnings)}"
            can_execute = True
        else:
            result = ValidationResult.APPROVED.value
            reasoning = "Order passed all Hard Rules"
            can_execute = True

        # Record order in history (if approved/warning)
        if can_execute:
            self._record_order(order)

        return {
            'result': result,
            'reasoning': reasoning,
            'violations': violations,
            'warnings': warnings,
            'can_execute': can_execute,
            'timestamp': datetime.utcnow().isoformat(),
            'order_id': order.get('order_id', 'N/A')
        }

    def _check_duplicate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        중복 주문 체크

        Returns:
            {
                'is_duplicate': bool,
                'previous_order': str (if duplicate)
            }
        """
        current_time = datetime.utcnow()
        window_seconds = self.HARD_RULES['duplicate_order_window_sec']

        symbol = order.get('symbol', '')
        action = order.get('action', '')
        quantity = order.get('quantity', 0)

        # Check order history
        for hist_order in self.order_history:
            hist_time = datetime.fromisoformat(hist_order['timestamp'])
            time_diff = (current_time - hist_time).total_seconds()

            # Within time window?
            if time_diff <= window_seconds:
                # Same symbol, action, quantity?
                if (hist_order.get('symbol') == symbol and
                    hist_order.get('action') == action and
                    abs(hist_order.get('quantity', 0) - quantity) / max(quantity, 1) < 0.01):  # 1% tolerance
                    return {
                        'is_duplicate': True,
                        'previous_order': f"{hist_order.get('symbol')} {hist_order.get('action')} x{hist_order.get('quantity')} @ {hist_order['timestamp']}"
                    }

        return {
            'is_duplicate': False,
            'previous_order': None
        }

    def _record_order(self, order: Dict[str, Any]) -> None:
        """주문 기록 (중복 체크용)"""
        order_record = {
            'symbol': order.get('symbol', ''),
            'action': order.get('action', ''),
            'quantity': order.get('quantity', 0),
            'price': order.get('price', 0.0),
            'timestamp': order.get('timestamp', datetime.utcnow().isoformat())
        }
        self.order_history.append(order_record)

        # Keep only recent orders (last 1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.order_history = [
            o for o in self.order_history
            if datetime.fromisoformat(o['timestamp']) > cutoff_time
        ]

    def add_to_blacklist(self, symbol: str) -> None:
        """종목을 블랙리스트에 추가"""
        if symbol not in self.HARD_RULES['blacklist_symbols']:
            self.HARD_RULES['blacklist_symbols'].append(symbol)

    def remove_from_blacklist(self, symbol: str) -> None:
        """종목을 블랙리스트에서 제거"""
        if symbol in self.HARD_RULES['blacklist_symbols']:
            self.HARD_RULES['blacklist_symbols'].remove(symbol)

    def update_hard_rule(self, rule_name: str, value: Any) -> bool:
        """
        Hard Rule 업데이트 (관리자 전용)

        Args:
            rule_name: 룰 이름
            value: 새 값

        Returns:
            bool: 업데이트 성공 여부
        """
        if rule_name in self.HARD_RULES:
            self.HARD_RULES[rule_name] = value
            return True
        return False

    def get_validator_info(self) -> Dict[str, Any]:
        """Get validator information"""
        return {
            'name': 'OrderValidator',
            'purpose': 'Hard Rules enforcement (code-based, NO AI interpretation)',
            'hard_rules': self.HARD_RULES,
            'blacklist_count': len(self.HARD_RULES['blacklist_symbols']),
            'order_history_count': len(self.order_history),
            'chatgpt_insight': 'Hard Rules는 AI가 해석하면 안됨. 코드로 강제해야 함.'
        }


# Example usage
if __name__ == "__main__":
    validator = OrderValidator()

    # Test 1: Valid Buy Order
    print("=== Test 1: Valid Buy Order ===")
    order1 = {
        'symbol': 'AAPL',
        'action': 'buy',
        'quantity': 100,
        'price': 150.0,
        'order_value': 15000.0,
        'position_size_pct': 0.15,  # 15%
        'stop_loss_pct': 0.02,  # 2%
        'timestamp': datetime.utcnow().isoformat()
    }
    portfolio1 = {
        'total_value': 100000,
        'available_cash': 50000,
        'total_risk': 0.02,
        'position_count': 5
    }
    result1 = validator.validate(order1, portfolio1, {'is_market_open': True})
    print(f"Result: {result1['result']}")
    print(f"Reasoning: {result1['reasoning']}")
    print(f"Can Execute: {result1['can_execute']}")
    print()

    # Test 2: Position Size Too Large
    print("=== Test 2: Position Size Too Large ===")
    order2 = {
        'symbol': 'NVDA',
        'action': 'buy',
        'quantity': 200,
        'price': 500.0,
        'order_value': 100000.0,
        'position_size_pct': 0.35,  # 35% - VIOLATION!
        'stop_loss_pct': 0.02,
        'timestamp': datetime.utcnow().isoformat()
    }
    result2 = validator.validate(order2, portfolio1, {'is_market_open': True})
    print(f"Result: {result2['result']}")
    print(f"Violations: {result2['violations']}")
    print(f"Can Execute: {result2['can_execute']}")
    print()

    # Test 3: No Stop Loss
    print("=== Test 3: No Stop Loss ===")
    order3 = {
        'symbol': 'TSLA',
        'action': 'buy',
        'quantity': 50,
        'price': 200.0,
        'order_value': 10000.0,
        'position_size_pct': 0.10,
        'stop_loss_pct': 0.0,  # VIOLATION!
        'timestamp': datetime.utcnow().isoformat()
    }
    result3 = validator.validate(order3, portfolio1, {'is_market_open': True})
    print(f"Result: {result3['result']}")
    print(f"Violations: {result3['violations']}")
    print()

    # Print validator info
    print("=== Validator Info ===")
    info = validator.get_validator_info()
    print(f"Hard Rules: {list(info['hard_rules'].keys())}")
    print(f"Purpose: {info['purpose']}")
