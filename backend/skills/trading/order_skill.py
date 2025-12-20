"""
Order Skill

고급 주문 관리 및 실행 Skill

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class OrderSkill(BaseSkill):
    """
    고급 주문 관리 Skill

    기능:
    - 분할 매수/매도 (TWAP, VWAP)
    - 조건부 주문 (가격 도달 시)
    - 트레일링 스톱
    - 브래킷 주문 (진입 + 익절 + 손절)

    Usage:
        skill = OrderSkill()
        tools = skill.get_tools()
        result = await skill.execute(
            "create_split_order",
            ticker="AAPL",
            action="BUY",
            total_quantity=100,
            num_splits=5
        )
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Trading.Order",
            category=SkillCategory.TRADING,
            description="고급 주문 관리 - 분할 매수, 조건부 주문, 트레일링 스톱",
            keywords=[
                "주문", "order", "매수", "buy", "매도", "sell",
                "분할", "split", "조건부", "conditional", "트레일링", "trailing",
                "브래킷", "bracket", "TWAP", "VWAP"
            ],
            cost_tier=CostTier.FREE,
            requires_api_key=False,
            rate_limit_per_min=None,
        )

        # 주문 큐 (메모리 기반, 실제로는 DB 사용)
        self._pending_orders = []
        self._active_trailing_stops = []

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Order Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_split_order",
                    "description": "분할 매수/매도 주문 생성 (TWAP 방식). 큰 주문을 여러 번에 나누어 실행.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커 (예: 'AAPL', '005930')"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "매수/매도"
                            },
                            "total_quantity": {
                                "type": "integer",
                                "description": "총 수량"
                            },
                            "num_splits": {
                                "type": "integer",
                                "description": "분할 횟수 (2-10)",
                                "default": 5
                            },
                            "interval_minutes": {
                                "type": "integer",
                                "description": "분할 간격 (분 단위)",
                                "default": 5
                            },
                            "order_type": {
                                "type": "string",
                                "enum": ["market", "limit"],
                                "description": "주문 유형",
                                "default": "market"
                            }
                        },
                        "required": ["ticker", "action", "total_quantity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_conditional_order",
                    "description": "조건부 주문 생성. 특정 가격 도달 시 자동 실행.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "매수/매도"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "수량"
                            },
                            "condition_type": {
                                "type": "string",
                                "enum": ["price_above", "price_below"],
                                "description": "조건 유형"
                            },
                            "trigger_price": {
                                "type": "number",
                                "description": "트리거 가격"
                            },
                            "execution_price": {
                                "type": "number",
                                "description": "실행 가격 (optional, 지정가 주문)",
                                "default": None
                            },
                            "expire_minutes": {
                                "type": "integer",
                                "description": "만료 시간 (분 단위, 0이면 무제한)",
                                "default": 0
                            }
                        },
                        "required": ["ticker", "action", "quantity", "condition_type", "trigger_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_trailing_stop",
                    "description": "트레일링 스톱 설정. 가격이 유리하게 움직이면 손절가도 함께 이동.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "수량"
                            },
                            "trail_type": {
                                "type": "string",
                                "enum": ["percent", "amount"],
                                "description": "트레일링 유형 (비율/금액)",
                                "default": "percent"
                            },
                            "trail_value": {
                                "type": "number",
                                "description": "트레일링 값 (percent: 5 = 5%, amount: 1000 = $1000)"
                            },
                            "initial_stop_price": {
                                "type": "number",
                                "description": "초기 손절가 (optional)",
                                "default": None
                            }
                        },
                        "required": ["ticker", "quantity", "trail_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_bracket_order",
                    "description": "브래킷 주문 생성. 진입 + 익절 + 손절을 동시에 설정.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "진입 방향"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "수량"
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "진입 가격 (None이면 시장가)",
                                "default": None
                            },
                            "take_profit_price": {
                                "type": "number",
                                "description": "익절 가격"
                            },
                            "stop_loss_price": {
                                "type": "number",
                                "description": "손절 가격"
                            }
                        },
                        "required": ["ticker", "action", "quantity", "take_profit_price", "stop_loss_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pending_orders",
                    "description": "대기 중인 조건부 주문 목록 조회",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커 (optional, 전체 조회 시 생략)",
                                "default": None
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_pending_order",
                    "description": "대기 중인 주문 취소",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "주문 ID"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            }
        ]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        도구 실행

        Args:
            tool_name: 실행할 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            실행 결과

        Raises:
            ValueError: 알 수 없는 도구
        """
        try:
            if tool_name == "create_split_order":
                result = await self._create_split_order(**kwargs)
            elif tool_name == "create_conditional_order":
                result = await self._create_conditional_order(**kwargs)
            elif tool_name == "create_trailing_stop":
                result = await self._create_trailing_stop(**kwargs)
            elif tool_name == "create_bracket_order":
                result = await self._create_bracket_order(**kwargs)
            elif tool_name == "get_pending_orders":
                result = await self._get_pending_orders(**kwargs)
            elif tool_name == "cancel_pending_order":
                result = await self._cancel_pending_order(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트 (무료)
            self._track_call(success=True, cost_usd=0.0)

            return result

        except Exception as e:
            # 오류 추적
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _create_split_order(
        self,
        ticker: str,
        action: str,
        total_quantity: int,
        num_splits: int = 5,
        interval_minutes: int = 5,
        order_type: str = "market"
    ) -> Dict[str, Any]:
        """
        분할 주문 생성

        Args:
            ticker: 종목 티커
            action: BUY/SELL
            total_quantity: 총 수량
            num_splits: 분할 횟수
            interval_minutes: 분할 간격
            order_type: 주문 유형

        Returns:
            분할 주문 정보
        """
        # 분할 수량 계산
        quantity_per_split = total_quantity // num_splits
        remainder = total_quantity % num_splits

        splits = []
        for i in range(num_splits):
            quantity = quantity_per_split
            if i < remainder:
                quantity += 1

            execution_time = datetime.now() + timedelta(minutes=interval_minutes * i)

            split = {
                "split_id": f"{ticker}_{action}_split_{i+1}",
                "ticker": ticker,
                "action": action,
                "quantity": quantity,
                "order_type": order_type,
                "execution_time": execution_time.isoformat(),
                "status": "pending"
            }

            splits.append(split)
            self._pending_orders.append(split)

        logger.info(
            f"Split order created: {ticker} {action} {total_quantity} "
            f"into {num_splits} splits over {interval_minutes * num_splits} minutes"
        )

        return {
            "success": True,
            "order_type": "split_order",
            "ticker": ticker,
            "action": action,
            "total_quantity": total_quantity,
            "num_splits": num_splits,
            "interval_minutes": interval_minutes,
            "splits": splits,
            "estimated_completion": splits[-1]["execution_time"]
        }

    async def _create_conditional_order(
        self,
        ticker: str,
        action: str,
        quantity: int,
        condition_type: str,
        trigger_price: float,
        execution_price: Optional[float] = None,
        expire_minutes: int = 0
    ) -> Dict[str, Any]:
        """
        조건부 주문 생성

        Args:
            ticker: 종목 티커
            action: BUY/SELL
            quantity: 수량
            condition_type: 조건 유형
            trigger_price: 트리거 가격
            execution_price: 실행 가격
            expire_minutes: 만료 시간

        Returns:
            조건부 주문 정보
        """
        import uuid

        order_id = f"conditional_{uuid.uuid4().hex[:8]}"

        order = {
            "order_id": order_id,
            "order_type": "conditional",
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "condition_type": condition_type,
            "trigger_price": trigger_price,
            "execution_price": execution_price,
            "created_at": datetime.now().isoformat(),
            "expire_at": (
                (datetime.now() + timedelta(minutes=expire_minutes)).isoformat()
                if expire_minutes > 0 else None
            ),
            "status": "pending"
        }

        self._pending_orders.append(order)

        logger.info(
            f"Conditional order created: {ticker} {action} {quantity} "
            f"when price {condition_type.replace('_', ' ')} {trigger_price}"
        )

        return {
            "success": True,
            "order_id": order_id,
            "message": f"Conditional order created. Will execute when {condition_type.replace('_', ' ')} {trigger_price}",
            **order
        }

    async def _create_trailing_stop(
        self,
        ticker: str,
        quantity: int,
        trail_type: str = "percent",
        trail_value: float = 5.0,
        initial_stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        트레일링 스톱 생성

        Args:
            ticker: 종목 티커
            quantity: 수량
            trail_type: 트레일링 유형
            trail_value: 트레일링 값
            initial_stop_price: 초기 손절가

        Returns:
            트레일링 스톱 정보
        """
        import uuid

        order_id = f"trailing_{uuid.uuid4().hex[:8]}"

        # 현재가 조회 (실제로는 KISSkill 사용)
        # 여기서는 시뮬레이션
        current_price = 100.0  # TODO: 실제 가격 조회

        if initial_stop_price is None:
            if trail_type == "percent":
                initial_stop_price = current_price * (1 - trail_value / 100)
            else:
                initial_stop_price = current_price - trail_value

        order = {
            "order_id": order_id,
            "order_type": "trailing_stop",
            "ticker": ticker,
            "quantity": quantity,
            "trail_type": trail_type,
            "trail_value": trail_value,
            "current_stop_price": initial_stop_price,
            "highest_price": current_price,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

        self._active_trailing_stops.append(order)

        logger.info(
            f"Trailing stop created: {ticker} {quantity} shares, "
            f"trail {trail_value}{'%' if trail_type == 'percent' else '$'}"
        )

        return {
            "success": True,
            "order_id": order_id,
            "message": f"Trailing stop activated at {initial_stop_price:.2f}",
            **order
        }

    async def _create_bracket_order(
        self,
        ticker: str,
        action: str,
        quantity: int,
        take_profit_price: float,
        stop_loss_price: float,
        entry_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        브래킷 주문 생성

        Args:
            ticker: 종목 티커
            action: BUY/SELL
            quantity: 수량
            take_profit_price: 익절가
            stop_loss_price: 손절가
            entry_price: 진입가

        Returns:
            브래킷 주문 정보
        """
        import uuid

        order_id = f"bracket_{uuid.uuid4().hex[:8]}"

        # 브래킷 주문은 3개의 주문으로 구성
        # 1. 진입 주문 (Entry)
        # 2. 익절 주문 (Take Profit)
        # 3. 손절 주문 (Stop Loss)

        bracket = {
            "order_id": order_id,
            "order_type": "bracket",
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "entry": {
                "order_type": "market" if entry_price is None else "limit",
                "price": entry_price,
                "status": "pending"
            },
            "take_profit": {
                "price": take_profit_price,
                "status": "waiting"  # 진입 완료 후 활성화
            },
            "stop_loss": {
                "price": stop_loss_price,
                "status": "waiting"
            },
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        self._pending_orders.append(bracket)

        # 수익/손실 비율 계산
        if entry_price:
            if action == "BUY":
                profit_pct = ((take_profit_price - entry_price) / entry_price) * 100
                loss_pct = ((entry_price - stop_loss_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - take_profit_price) / entry_price) * 100
                loss_pct = ((stop_loss_price - entry_price) / entry_price) * 100

            risk_reward = profit_pct / loss_pct if loss_pct > 0 else 0
        else:
            profit_pct = loss_pct = risk_reward = None

        logger.info(
            f"Bracket order created: {ticker} {action} {quantity} "
            f"TP: {take_profit_price}, SL: {stop_loss_price}"
        )

        return {
            "success": True,
            "order_id": order_id,
            "message": "Bracket order created with entry, take profit, and stop loss",
            **bracket,
            "analysis": {
                "potential_profit_pct": profit_pct,
                "potential_loss_pct": loss_pct,
                "risk_reward_ratio": risk_reward
            }
        }

    async def _get_pending_orders(
        self,
        ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        대기 중인 주문 조회

        Args:
            ticker: 종목 티커 (optional)

        Returns:
            주문 목록
        """
        if ticker:
            orders = [o for o in self._pending_orders if o.get("ticker") == ticker]
        else:
            orders = self._pending_orders

        return {
            "success": True,
            "total_orders": len(orders),
            "orders": orders,
            "trailing_stops": self._active_trailing_stops if not ticker else [
                ts for ts in self._active_trailing_stops if ts.get("ticker") == ticker
            ]
        }

    async def _cancel_pending_order(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """
        대기 중인 주문 취소

        Args:
            order_id: 주문 ID

        Returns:
            취소 결과
        """
        # 주문 찾기
        order = None
        for o in self._pending_orders:
            if o.get("order_id") == order_id:
                order = o
                break

        if not order:
            # 트레일링 스톱에서 찾기
            for ts in self._active_trailing_stops:
                if ts.get("order_id") == order_id:
                    order = ts
                    self._active_trailing_stops.remove(ts)
                    break

        if not order:
            return {
                "success": False,
                "message": f"Order not found: {order_id}"
            }

        # 주문 제거
        if order in self._pending_orders:
            self._pending_orders.remove(order)

        logger.info(f"Order cancelled: {order_id}")

        return {
            "success": True,
            "message": f"Order {order_id} cancelled successfully",
            "cancelled_order": order
        }
