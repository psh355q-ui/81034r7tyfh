"""
KIS (Korea Investment & Securities) Trading Skill

한국투자증권 API를 통한 실제 거래 실행

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class KISSkill(BaseSkill):
    """
    KIS API Trading Skill

    기능:
    - 계좌 조회 (잔고, 보유 종목)
    - 주문 실행 (매수/매도)
    - 주문 취소
    - 거래 내역 조회

    Usage:
        skill = KISSkill(use_paper_trading=True)
        tools = skill.get_tools()
        result = await skill.execute("get_account_balance")
    """

    def __init__(self, use_paper_trading: bool = True):
        """
        초기화

        Args:
            use_paper_trading: 모의투자 사용 여부 (기본값: True, 안전)
        """
        super().__init__(
            name="Trading.KIS",
            category=SkillCategory.TRADING,
            description="한국투자증권 API를 통한 실시간 거래 실행 및 계좌 관리",
            keywords=[
                "KIS", "한국투자증권", "거래", "trading", "주문", "order",
                "매수", "매도", "buy", "sell", "계좌", "account", "잔고", "balance"
            ],
            cost_tier=CostTier.FREE,  # API 자체는 무료 (거래 수수료 별도)
            requires_api_key=True,
            rate_limit_per_min=20,  # KIS API 제한
        )

        self.use_paper_trading = use_paper_trading

        # KIS 클라이언트 초기화 (지연 로딩)
        self._kis_client = None

        logger.info(f"KISSkill initialized (paper_trading={use_paper_trading})")

    def _get_kis_client(self):
        """KIS 클라이언트 가져오기 (지연 로딩)"""
        if self._kis_client is None:
            try:
                from backend.execution.broker import KISBroker
                self._kis_client = KISBroker(use_paper_trading=self.use_paper_trading)
                logger.info("KIS client initialized")
            except ImportError:
                logger.error("Failed to import KISBroker")
                raise

        return self._kis_client

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        KIS Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "계좌 잔고 및 보유 종목 조회",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "계좌번호 (선택, 기본값: 환경변수에서 로드)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_order",
                    "description": "주식 매수/매도 주문 실행",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 코드 (예: '005930' - 삼성전자)"
                            },
                            "action": {
                                "type": "string",
                                "description": "매매 방향",
                                "enum": ["BUY", "SELL"]
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "주문 수량"
                            },
                            "order_type": {
                                "type": "string",
                                "description": "주문 유형",
                                "enum": ["MARKET", "LIMIT"],
                                "default": "MARKET"
                            },
                            "price": {
                                "type": "number",
                                "description": "지정가 (LIMIT 주문 시 필수)"
                            }
                        },
                        "required": ["ticker", "action", "quantity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_order",
                    "description": "미체결 주문 취소",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "취소할 주문 ID"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order_history",
                    "description": "거래 내역 조회",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "조회 기간 (일)",
                                "default": 7
                            },
                            "status": {
                                "type": "string",
                                "description": "주문 상태 필터",
                                "enum": ["ALL", "FILLED", "PENDING", "CANCELLED"],
                                "default": "ALL"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_price",
                    "description": "종목 현재가 조회",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 코드"
                            }
                        },
                        "required": ["ticker"]
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
        """
        try:
            if tool_name == "get_account_balance":
                result = await self._get_account_balance(**kwargs)
            elif tool_name == "execute_order":
                result = await self._execute_order(**kwargs)
            elif tool_name == "cancel_order":
                result = await self._cancel_order(**kwargs)
            elif tool_name == "get_order_history":
                result = await self._get_order_history(**kwargs)
            elif tool_name == "get_current_price":
                result = await self._get_current_price(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트 (거래 실행 시 비용 추적)
            cost = self._estimate_execution_cost(tool_name, result)
            self._track_call(success=True, cost_usd=cost)

            return result

        except Exception as e:
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _get_account_balance(
        self,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Args:
            account_number: 계좌번호 (선택)

        Returns:
            계좌 정보
        """
        kis = self._get_kis_client()

        # 계좌 조회
        balance = await kis.get_account_balance(account_number)

        return {
            "success": True,
            "account_number": balance.get("account_number"),
            "total_value": balance.get("total_value", 0),
            "cash": balance.get("cash", 0),
            "positions": [
                {
                    "ticker": pos.get("ticker"),
                    "name": pos.get("name"),
                    "quantity": pos.get("quantity"),
                    "avg_cost": pos.get("avg_cost"),
                    "current_price": pos.get("current_price"),
                    "market_value": pos.get("market_value"),
                    "pnl": pos.get("pnl"),
                    "pnl_pct": pos.get("pnl_pct"),
                }
                for pos in balance.get("positions", [])
            ],
            "is_paper_trading": self.use_paper_trading,
        }

    async def _execute_order(
        self,
        ticker: str,
        action: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        주문 실행

        Args:
            ticker: 종목 코드
            action: BUY/SELL
            quantity: 수량
            order_type: MARKET/LIMIT
            price: 지정가 (LIMIT 시)

        Returns:
            주문 결과
        """
        kis = self._get_kis_client()

        # 주문 실행
        result = await kis.place_order(
            ticker=ticker,
            side=action,
            quantity=quantity,
            order_type=order_type,
            price=price
        )

        return {
            "success": result.get("success", False),
            "order_id": result.get("order_id"),
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "order_type": order_type,
            "status": result.get("status"),
            "avg_price": result.get("avg_price"),
            "filled_quantity": result.get("filled_quantity"),
            "message": result.get("message"),
            "is_paper_trading": self.use_paper_trading,
        }

    async def _cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        주문 취소

        Args:
            order_id: 주문 ID

        Returns:
            취소 결과
        """
        kis = self._get_kis_client()

        result = await kis.cancel_order(order_id)

        return {
            "success": result.get("success", False),
            "order_id": order_id,
            "message": result.get("message"),
        }

    async def _get_order_history(
        self,
        days: int = 7,
        status: str = "ALL"
    ) -> Dict[str, Any]:
        """
        거래 내역 조회

        Args:
            days: 조회 기간
            status: 상태 필터

        Returns:
            거래 내역
        """
        kis = self._get_kis_client()

        orders = await kis.get_order_history(days=days, status=status)

        return {
            "success": True,
            "total_orders": len(orders),
            "orders": [
                {
                    "order_id": order.get("order_id"),
                    "ticker": order.get("ticker"),
                    "action": order.get("action"),
                    "quantity": order.get("quantity"),
                    "price": order.get("price"),
                    "status": order.get("status"),
                    "created_at": order.get("created_at"),
                }
                for order in orders
            ],
        }

    async def _get_current_price(self, ticker: str) -> Dict[str, Any]:
        """
        현재가 조회

        Args:
            ticker: 종목 코드

        Returns:
            현재가 정보
        """
        kis = self._get_kis_client()

        price_info = await kis.get_current_price(ticker)

        return {
            "success": True,
            "ticker": ticker,
            "current_price": price_info.get("current_price"),
            "change": price_info.get("change"),
            "change_pct": price_info.get("change_pct"),
            "volume": price_info.get("volume"),
            "timestamp": price_info.get("timestamp"),
        }

    def _estimate_execution_cost(self, tool_name: str, result: Dict) -> float:
        """
        실행 비용 추정

        Args:
            tool_name: 도구 이름
            result: 실행 결과

        Returns:
            비용 (USD)
        """
        # 실제 거래 시 수수료 계산
        if tool_name == "execute_order" and result.get("success"):
            # 한국 주식 수수료: 약 0.015%
            avg_price = result.get("avg_price", 0)
            quantity = result.get("quantity", 0)
            trade_value = avg_price * quantity

            # KRW to USD (근사치: 1300)
            commission_krw = trade_value * 0.00015
            commission_usd = commission_krw / 1300

            return commission_usd

        return 0.0
