"""
Risk Skill

리스크 관리 및 포지션 사이징 Skill

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
import math

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class RiskSkill(BaseSkill):
    """
    리스크 관리 Skill

    기능:
    - 포지션 사이징 (Kelly Criterion, Fixed Percentage)
    - 포트폴리오 리스크 계산 (VaR, CVaR)
    - Stop Loss / Take Profit 자동 계산
    - 상관관계 리스크 분석
    - 최대 드로우다운 모니터링

    Usage:
        skill = RiskSkill()
        result = await skill.execute(
            "calculate_position_size",
            account_balance=10000,
            risk_per_trade=2.0,
            entry_price=100,
            stop_loss_price=95
        )
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Trading.Risk",
            category=SkillCategory.TRADING,
            description="리스크 관리 - 포지션 사이징, VaR, 손절/익절 계산",
            keywords=[
                "리스크", "risk", "포지션", "position", "사이징", "sizing",
                "손절", "stop loss", "익절", "take profit", "VaR", "CVaR",
                "켈리", "kelly", "드로우다운", "drawdown", "상관관계", "correlation"
            ],
            cost_tier=CostTier.FREE,
            requires_api_key=False,
            rate_limit_per_min=None,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Risk Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculate_position_size",
                    "description": "포지션 사이징 계산. 계좌 잔고와 리스크 허용도를 기반으로 적정 매수 수량 산출.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_balance": {
                                "type": "number",
                                "description": "계좌 잔고 (USD)"
                            },
                            "risk_per_trade": {
                                "type": "number",
                                "description": "거래당 리스크 (%, 예: 2.0 = 2%)",
                                "default": 2.0
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "진입 가격"
                            },
                            "stop_loss_price": {
                                "type": "number",
                                "description": "손절 가격"
                            },
                            "method": {
                                "type": "string",
                                "enum": ["fixed_percentage", "kelly", "volatility_based"],
                                "description": "포지션 사이징 방법",
                                "default": "fixed_percentage"
                            }
                        },
                        "required": ["account_balance", "entry_price", "stop_loss_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_stop_loss_take_profit",
                    "description": "자동 손절/익절가 계산. ATR, 지지/저항, 리스크/보상 비율 기반.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entry_price": {
                                "type": "number",
                                "description": "진입 가격"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["BUY", "SELL"],
                                "description": "매수/매도"
                            },
                            "method": {
                                "type": "string",
                                "enum": ["atr", "percentage", "support_resistance"],
                                "description": "계산 방법",
                                "default": "percentage"
                            },
                            "stop_loss_percent": {
                                "type": "number",
                                "description": "손절 비율 (%, percentage 방식)",
                                "default": 2.0
                            },
                            "risk_reward_ratio": {
                                "type": "number",
                                "description": "리스크/보상 비율 (예: 2.0 = 1:2)",
                                "default": 2.0
                            },
                            "atr_value": {
                                "type": "number",
                                "description": "ATR 값 (atr 방식에서 사용)",
                                "default": None
                            },
                            "atr_multiplier": {
                                "type": "number",
                                "description": "ATR 승수",
                                "default": 2.0
                            }
                        },
                        "required": ["entry_price", "action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_portfolio_risk",
                    "description": "포트폴리오 전체 리스크 계산 (VaR, CVaR, 베타, 변동성).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "positions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "ticker": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "entry_price": {"type": "number"},
                                        "current_price": {"type": "number"}
                                    }
                                },
                                "description": "현재 포지션 목록"
                            },
                            "confidence_level": {
                                "type": "number",
                                "description": "신뢰 수준 (예: 0.95 = 95%)",
                                "default": 0.95
                            },
                            "time_horizon_days": {
                                "type": "integer",
                                "description": "시간 범위 (일)",
                                "default": 1
                            }
                        },
                        "required": ["positions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_correlation_risk",
                    "description": "포지션 간 상관관계 리스크 분석. 과도한 집중도 경고.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "positions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "ticker": {"type": "string"},
                                        "weight": {"type": "number"}
                                    }
                                },
                                "description": "포지션 목록 (weight: 포트폴리오 비중 %)"
                            },
                            "max_single_position": {
                                "type": "number",
                                "description": "단일 포지션 최대 비중 (%)",
                                "default": 20.0
                            },
                            "max_sector_exposure": {
                                "type": "number",
                                "description": "섹터별 최대 노출 (%)",
                                "default": 40.0
                            }
                        },
                        "required": ["positions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_max_drawdown",
                    "description": "최대 드로우다운 계산 및 모니터링.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "equity_curve": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "자산 가치 시계열 (시간 순서)"
                            },
                            "threshold_percent": {
                                "type": "number",
                                "description": "경고 임계값 (%, 예: 10.0 = 10%)",
                                "default": 10.0
                            }
                        },
                        "required": ["equity_curve"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_risk_limits",
                    "description": "리스크 한도 체크. 새로운 거래가 리스크 정책을 위반하는지 확인.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_balance": {
                                "type": "number",
                                "description": "계좌 잔고"
                            },
                            "current_positions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "ticker": {"type": "string"},
                                        "value": {"type": "number"}
                                    }
                                },
                                "description": "현재 포지션 목록"
                            },
                            "new_trade": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string"},
                                    "action": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "price": {"type": "number"}
                                },
                                "description": "새로운 거래"
                            },
                            "risk_limits": {
                                "type": "object",
                                "description": "리스크 한도 설정",
                                "properties": {
                                    "max_position_size_pct": {"type": "number", "default": 20.0},
                                    "max_total_exposure_pct": {"type": "number", "default": 100.0},
                                    "max_leverage": {"type": "number", "default": 1.0}
                                }
                            }
                        },
                        "required": ["account_balance", "current_positions", "new_trade"]
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
            if tool_name == "calculate_position_size":
                result = await self._calculate_position_size(**kwargs)
            elif tool_name == "calculate_stop_loss_take_profit":
                result = await self._calculate_stop_loss_take_profit(**kwargs)
            elif tool_name == "calculate_portfolio_risk":
                result = await self._calculate_portfolio_risk(**kwargs)
            elif tool_name == "calculate_correlation_risk":
                result = await self._calculate_correlation_risk(**kwargs)
            elif tool_name == "calculate_max_drawdown":
                result = await self._calculate_max_drawdown(**kwargs)
            elif tool_name == "check_risk_limits":
                result = await self._check_risk_limits(**kwargs)
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

    async def _calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = 2.0,
        method: str = "fixed_percentage"
    ) -> Dict[str, Any]:
        """
        포지션 사이징 계산

        Args:
            account_balance: 계좌 잔고
            entry_price: 진입 가격
            stop_loss_price: 손절 가격
            risk_per_trade: 거래당 리스크 (%)
            method: 계산 방법

        Returns:
            포지션 사이즈 정보
        """
        # 거래당 리스크 금액
        risk_amount = account_balance * (risk_per_trade / 100)

        # 주당 리스크
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            return {
                "success": False,
                "message": "Entry price and stop loss price cannot be the same"
            }

        # Fixed Percentage 방식
        if method == "fixed_percentage":
            position_size = risk_amount / risk_per_share

        # Kelly Criterion 방식 (간소화)
        elif method == "kelly":
            # Kelly = (Win% * Avg Win / Avg Loss) - Loss%
            # 여기서는 간단히 Fixed의 절반으로 보수적으로 계산
            position_size = (risk_amount / risk_per_share) * 0.5

        # Volatility-based 방식
        elif method == "volatility_based":
            # 변동성이 높으면 포지션 크기 축소
            # 여기서는 시뮬레이션 (실제로는 ATR 기반)
            volatility_factor = 0.8  # 임의값
            position_size = (risk_amount / risk_per_share) * volatility_factor

        else:
            position_size = risk_amount / risk_per_share

        # 정수로 반올림
        position_size = int(position_size)

        # 포지션 가치
        position_value = position_size * entry_price

        # 레버리지 비율
        leverage = position_value / account_balance

        logger.info(
            f"Position sizing: {position_size} shares, "
            f"value ${position_value:.2f}, leverage {leverage:.2f}x"
        )

        return {
            "success": True,
            "method": method,
            "position_size": position_size,
            "position_value": position_value,
            "risk_amount": risk_amount,
            "risk_per_share": risk_per_share,
            "leverage": leverage,
            "recommendation": (
                "Safe" if leverage <= 1.0 else
                "Moderate" if leverage <= 2.0 else
                "High Risk"
            )
        }

    async def _calculate_stop_loss_take_profit(
        self,
        entry_price: float,
        action: str,
        method: str = "percentage",
        stop_loss_percent: float = 2.0,
        risk_reward_ratio: float = 2.0,
        atr_value: Optional[float] = None,
        atr_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        손절/익절가 계산

        Args:
            entry_price: 진입 가격
            action: BUY/SELL
            method: 계산 방법
            stop_loss_percent: 손절 비율
            risk_reward_ratio: 리스크/보상 비율
            atr_value: ATR 값
            atr_multiplier: ATR 승수

        Returns:
            손절/익절가 정보
        """
        if method == "percentage":
            # 비율 기반
            if action == "BUY":
                stop_loss = entry_price * (1 - stop_loss_percent / 100)
                take_profit = entry_price * (1 + stop_loss_percent * risk_reward_ratio / 100)
            else:  # SELL
                stop_loss = entry_price * (1 + stop_loss_percent / 100)
                take_profit = entry_price * (1 - stop_loss_percent * risk_reward_ratio / 100)

        elif method == "atr":
            # ATR 기반
            if atr_value is None:
                return {
                    "success": False,
                    "message": "ATR value required for ATR-based calculation"
                }

            atr_distance = atr_value * atr_multiplier

            if action == "BUY":
                stop_loss = entry_price - atr_distance
                take_profit = entry_price + (atr_distance * risk_reward_ratio)
            else:
                stop_loss = entry_price + atr_distance
                take_profit = entry_price - (atr_distance * risk_reward_ratio)

        elif method == "support_resistance":
            # 지지/저항 기반 (시뮬레이션)
            # 실제로는 차트 분석 필요
            if action == "BUY":
                stop_loss = entry_price * 0.95  # 5% 아래
                take_profit = entry_price * 1.15  # 15% 위
            else:
                stop_loss = entry_price * 1.05
                take_profit = entry_price * 0.85

        else:
            return {
                "success": False,
                "message": f"Unknown method: {method}"
            }

        # 손실/이익 계산
        if action == "BUY":
            loss_per_share = entry_price - stop_loss
            profit_per_share = take_profit - entry_price
        else:
            loss_per_share = stop_loss - entry_price
            profit_per_share = entry_price - take_profit

        actual_risk_reward = profit_per_share / loss_per_share if loss_per_share > 0 else 0

        logger.info(
            f"SL/TP calculated: Entry ${entry_price:.2f}, "
            f"SL ${stop_loss:.2f}, TP ${take_profit:.2f}"
        )

        return {
            "success": True,
            "method": method,
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "loss_per_share": loss_per_share,
            "profit_per_share": profit_per_share,
            "risk_reward_ratio": actual_risk_reward,
            "recommendation": (
                "Excellent" if actual_risk_reward >= 3.0 else
                "Good" if actual_risk_reward >= 2.0 else
                "Fair" if actual_risk_reward >= 1.5 else
                "Poor"
            )
        }

    async def _calculate_portfolio_risk(
        self,
        positions: List[Dict[str, Any]],
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> Dict[str, Any]:
        """
        포트폴리오 리스크 계산

        Args:
            positions: 포지션 목록
            confidence_level: 신뢰 수준
            time_horizon_days: 시간 범위

        Returns:
            포트폴리오 리스크 분석
        """
        if not positions:
            return {
                "success": False,
                "message": "No positions to analyze"
            }

        # 포트폴리오 가치 계산
        total_value = sum(p['quantity'] * p['current_price'] for p in positions)
        total_pnl = sum(
            p['quantity'] * (p['current_price'] - p['entry_price'])
            for p in positions
        )

        # 간단한 VaR 계산 (Historical Simulation 방식 시뮬레이션)
        # 실제로는 과거 수익률 데이터 필요
        avg_volatility = 0.02  # 2% 일일 변동성 (가정)
        z_score = 1.65 if confidence_level == 0.95 else 2.33  # 95% or 99%

        var = total_value * avg_volatility * z_score * math.sqrt(time_horizon_days)
        cvar = var * 1.3  # CVaR는 VaR보다 약 30% 높음 (경험적)

        # 개별 포지션 분석
        position_analysis = []
        for p in positions:
            position_value = p['quantity'] * p['current_price']
            position_pnl = p['quantity'] * (p['current_price'] - p['entry_price'])
            position_pnl_pct = (position_pnl / (p['quantity'] * p['entry_price'])) * 100

            position_analysis.append({
                "ticker": p['ticker'],
                "value": position_value,
                "weight": (position_value / total_value) * 100,
                "pnl": position_pnl,
                "pnl_pct": position_pnl_pct
            })

        return {
            "success": True,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / (total_value - total_pnl)) * 100,
            "risk_metrics": {
                "var": var,
                "var_pct": (var / total_value) * 100,
                "cvar": cvar,
                "cvar_pct": (cvar / total_value) * 100,
                "confidence_level": confidence_level,
                "time_horizon_days": time_horizon_days
            },
            "positions": position_analysis,
            "recommendation": (
                "Low Risk" if (var / total_value) < 0.02 else
                "Moderate Risk" if (var / total_value) < 0.05 else
                "High Risk"
            )
        }

    async def _calculate_correlation_risk(
        self,
        positions: List[Dict[str, Any]],
        max_single_position: float = 20.0,
        max_sector_exposure: float = 40.0
    ) -> Dict[str, Any]:
        """
        상관관계 리스크 분석

        Args:
            positions: 포지션 목록
            max_single_position: 단일 포지션 최대 비중
            max_sector_exposure: 섹터별 최대 노출

        Returns:
            상관관계 리스크 분석
        """
        warnings = []
        violations = []

        # 집중도 분석
        for p in positions:
            if p['weight'] > max_single_position:
                violations.append({
                    "type": "position_concentration",
                    "ticker": p['ticker'],
                    "weight": p['weight'],
                    "limit": max_single_position,
                    "excess": p['weight'] - max_single_position
                })

        # 섹터 노출 분석 (실제로는 섹터 정보 필요, 여기서는 시뮬레이션)
        # TODO: 실제 섹터 데이터 연동

        # HHI (Herfindahl-Hirschman Index) 계산
        # HHI가 높으면 집중도가 높음
        hhi = sum(p['weight'] ** 2 for p in positions)

        concentration_level = (
            "Low" if hhi < 1500 else
            "Moderate" if hhi < 2500 else
            "High"
        )

        return {
            "success": True,
            "concentration_metrics": {
                "hhi": hhi,
                "concentration_level": concentration_level,
                "num_positions": len(positions),
                "max_single_weight": max(p['weight'] for p in positions)
            },
            "violations": violations,
            "warnings": warnings,
            "recommendation": (
                "Diversified" if not violations and hhi < 2000 else
                "Review Concentration" if violations and hhi < 2500 else
                "High Concentration Risk - Rebalance Recommended"
            )
        }

    async def _calculate_max_drawdown(
        self,
        equity_curve: List[float],
        threshold_percent: float = 10.0
    ) -> Dict[str, Any]:
        """
        최대 드로우다운 계산

        Args:
            equity_curve: 자산 가치 시계열
            threshold_percent: 경고 임계값

        Returns:
            드로우다운 분석
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "success": False,
                "message": "Insufficient data for drawdown calculation"
            }

        peak = equity_curve[0]
        max_dd = 0
        max_dd_start_idx = 0
        max_dd_end_idx = 0
        current_dd_start_idx = 0

        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                current_dd_start_idx = i
            else:
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
                    max_dd_start_idx = current_dd_start_idx
                    max_dd_end_idx = i

        max_dd_pct = max_dd * 100
        current_value = equity_curve[-1]
        current_peak = max(equity_curve)
        current_dd_pct = ((current_peak - current_value) / current_peak) * 100

        is_warning = current_dd_pct >= threshold_percent

        return {
            "success": True,
            "max_drawdown_pct": max_dd_pct,
            "max_drawdown_period": {
                "start_index": max_dd_start_idx,
                "end_index": max_dd_end_idx,
                "duration": max_dd_end_idx - max_dd_start_idx
            },
            "current_drawdown_pct": current_dd_pct,
            "current_peak": current_peak,
            "current_value": current_value,
            "threshold_percent": threshold_percent,
            "is_warning": is_warning,
            "recommendation": (
                "Normal" if current_dd_pct < threshold_percent / 2 else
                "Monitor Closely" if current_dd_pct < threshold_percent else
                "Risk Limit Breached - Consider Reducing Exposure"
            )
        }

    async def _check_risk_limits(
        self,
        account_balance: float,
        current_positions: List[Dict[str, Any]],
        new_trade: Dict[str, Any],
        risk_limits: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        리스크 한도 체크

        Args:
            account_balance: 계좌 잔고
            current_positions: 현재 포지션
            new_trade: 새로운 거래
            risk_limits: 리스크 한도 설정

        Returns:
            리스크 한도 체크 결과
        """
        risk_limits = risk_limits or {}
        max_position_size_pct = risk_limits.get("max_position_size_pct", 20.0)
        max_total_exposure_pct = risk_limits.get("max_total_exposure_pct", 100.0)
        max_leverage = risk_limits.get("max_leverage", 1.0)

        # 현재 총 노출
        current_total_value = sum(p['value'] for p in current_positions)

        # 새 거래 가치
        new_trade_value = new_trade['quantity'] * new_trade['price']

        # 새 총 노출
        if new_trade['action'] == "BUY":
            new_total_value = current_total_value + new_trade_value
        else:  # SELL
            new_total_value = current_total_value - new_trade_value

        # 단일 포지션 크기 체크
        new_position_pct = (new_trade_value / account_balance) * 100

        # 총 노출 체크
        new_exposure_pct = (new_total_value / account_balance) * 100

        # 레버리지 체크
        new_leverage = new_total_value / account_balance

        violations = []

        if new_position_pct > max_position_size_pct:
            violations.append({
                "type": "position_size",
                "limit": max_position_size_pct,
                "actual": new_position_pct,
                "message": f"Position size {new_position_pct:.1f}% exceeds limit {max_position_size_pct:.1f}%"
            })

        if new_exposure_pct > max_total_exposure_pct:
            violations.append({
                "type": "total_exposure",
                "limit": max_total_exposure_pct,
                "actual": new_exposure_pct,
                "message": f"Total exposure {new_exposure_pct:.1f}% exceeds limit {max_total_exposure_pct:.1f}%"
            })

        if new_leverage > max_leverage:
            violations.append({
                "type": "leverage",
                "limit": max_leverage,
                "actual": new_leverage,
                "message": f"Leverage {new_leverage:.2f}x exceeds limit {max_leverage:.2f}x"
            })

        is_approved = len(violations) == 0

        return {
            "success": True,
            "is_approved": is_approved,
            "new_position_pct": new_position_pct,
            "new_exposure_pct": new_exposure_pct,
            "new_leverage": new_leverage,
            "risk_limits": {
                "max_position_size_pct": max_position_size_pct,
                "max_total_exposure_pct": max_total_exposure_pct,
                "max_leverage": max_leverage
            },
            "violations": violations,
            "recommendation": (
                "Trade Approved" if is_approved else
                f"Trade Rejected - {len(violations)} risk limit(s) violated"
            )
        }
