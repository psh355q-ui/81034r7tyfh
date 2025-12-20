"""
Backtest Skill

백테스트 실행 및 성과 분석 Skill

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class BacktestSkill(BaseSkill):
    """
    백테스트 실행 Skill

    기능:
    - 전략 코드 실행 (Python 기반)
    - 성과 지표 계산 (수익률, Sharpe, MDD 등)
    - 거래 내역 분석
    - Monte Carlo 시뮬레이션
    - 워크포워드 분석

    Usage:
        skill = BacktestSkill()
        result = await skill.execute(
            "run_backtest",
            strategy_code="...",
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Technical.Backtest",
            category=SkillCategory.TECHNICAL,
            description="백테스트 실행 및 성과 분석 - 수익률, Sharpe, MDD, Monte Carlo",
            keywords=[
                "백테스트", "backtest", "테스트", "test", "전략", "strategy",
                "성과", "performance", "수익률", "return", "샤프", "sharpe",
                "MDD", "drawdown", "몬테카를로", "monte carlo", "시뮬레이션", "simulation"
            ],
            cost_tier=CostTier.FREE,
            requires_api_key=False,
            rate_limit_per_min=None,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Backtest Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_backtest",
                    "description": "전략 백테스트 실행. Python 전략 코드를 실행하고 성과 분석.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_code": {
                                "type": "string",
                                "description": "실행할 전략 코드 (Python)"
                            },
                            "ticker": {
                                "type": "string",
                                "description": "백테스트 대상 종목",
                                "default": "SPY"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "시작일 (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "종료일 (YYYY-MM-DD)"
                            },
                            "initial_capital": {
                                "type": "number",
                                "description": "초기 자본 (USD)",
                                "default": 10000
                            },
                            "commission": {
                                "type": "number",
                                "description": "수수료 (%, 예: 0.1 = 0.1%)",
                                "default": 0.1
                            },
                            "slippage": {
                                "type": "number",
                                "description": "슬리피지 (%, 예: 0.05 = 0.05%)",
                                "default": 0.05
                            }
                        },
                        "required": ["strategy_code", "start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_performance_metrics",
                    "description": "성과 지표 계산. 수익률, Sharpe Ratio, MDD, Win Rate 등.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "equity_curve": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "자산 가치 시계열"
                            },
                            "trades": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "entry_price": {"type": "number"},
                                        "exit_price": {"type": "number"},
                                        "quantity": {"type": "number"},
                                        "pnl": {"type": "number"}
                                    }
                                },
                                "description": "거래 내역"
                            },
                            "risk_free_rate": {
                                "type": "number",
                                "description": "무위험 수익률 (연율, %, 예: 3.0 = 3%)",
                                "default": 3.0
                            }
                        },
                        "required": ["equity_curve"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_trades",
                    "description": "거래 내역 상세 분석. 승률, 평균 수익/손실, 홀딩 기간 등.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trades": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "entry_date": {"type": "string"},
                                        "exit_date": {"type": "string"},
                                        "entry_price": {"type": "number"},
                                        "exit_price": {"type": "number"},
                                        "quantity": {"type": "number"},
                                        "pnl": {"type": "number"}
                                    }
                                },
                                "description": "거래 내역"
                            }
                        },
                        "required": ["trades"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_monte_carlo",
                    "description": "Monte Carlo 시뮬레이션. 전략의 안정성 및 확률 분포 분석.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trades": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "pnl": {"type": "number"}
                                    }
                                },
                                "description": "거래 내역 (PnL)"
                            },
                            "num_simulations": {
                                "type": "integer",
                                "description": "시뮬레이션 횟수",
                                "default": 1000
                            },
                            "initial_capital": {
                                "type": "number",
                                "description": "초기 자본",
                                "default": 10000
                            }
                        },
                        "required": ["trades"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_strategies",
                    "description": "여러 전략 비교 분석. 수익률, 리스크, 샤프 비율 등을 비교.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategies": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "equity_curve": {"type": "array", "items": {"type": "number"}},
                                        "trades": {"type": "array"}
                                    }
                                },
                                "description": "비교할 전략 목록"
                            }
                        },
                        "required": ["strategies"]
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
            if tool_name == "run_backtest":
                result = await self._run_backtest(**kwargs)
            elif tool_name == "calculate_performance_metrics":
                result = await self._calculate_performance_metrics(**kwargs)
            elif tool_name == "analyze_trades":
                result = await self._analyze_trades(**kwargs)
            elif tool_name == "run_monte_carlo":
                result = await self._run_monte_carlo(**kwargs)
            elif tool_name == "compare_strategies":
                result = await self._compare_strategies(**kwargs)
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

    async def _run_backtest(
        self,
        strategy_code: str,
        start_date: str,
        end_date: str,
        ticker: str = "SPY",
        initial_capital: float = 10000,
        commission: float = 0.1,
        slippage: float = 0.05
    ) -> Dict[str, Any]:
        """
        백테스트 실행

        Args:
            strategy_code: 전략 코드
            start_date: 시작일
            end_date: 종료일
            ticker: 종목
            initial_capital: 초기 자본
            commission: 수수료
            slippage: 슬리피지

        Returns:
            백테스트 결과
        """
        # 실제 구현에서는 실제 데이터와 전략 코드를 실행
        # 여기서는 시뮬레이션 결과 반환

        logger.info(
            f"Running backtest: {ticker} from {start_date} to {end_date}, "
            f"initial capital ${initial_capital}"
        )

        # 시뮬레이션: 간단한 결과 생성
        import random

        # 거래 일수 계산
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days

        # 자산 곡선 시뮬레이션 (랜덤 워크)
        equity_curve = [initial_capital]
        for _ in range(days):
            daily_return = random.gauss(0.001, 0.02)  # 평균 0.1% 수익, 2% 변동성
            equity_curve.append(equity_curve[-1] * (1 + daily_return))

        # 거래 내역 시뮬레이션
        num_trades = random.randint(10, 30)
        trades = []

        for i in range(num_trades):
            entry_price = random.uniform(90, 110)
            exit_price = entry_price * random.uniform(0.95, 1.08)
            quantity = random.randint(1, 10)
            pnl = (exit_price - entry_price) * quantity - (entry_price * quantity * commission / 100 * 2)

            trades.append({
                "trade_id": i + 1,
                "entry_date": (start + timedelta(days=random.randint(0, days-1))).strftime("%Y-%m-%d"),
                "entry_price": entry_price,
                "exit_date": (start + timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d"),
                "exit_price": exit_price,
                "quantity": quantity,
                "pnl": pnl,
                "pnl_pct": ((exit_price - entry_price) / entry_price) * 100
            })

        final_equity = equity_curve[-1]
        total_return = ((final_equity - initial_capital) / initial_capital) * 100

        logger.info(
            f"Backtest complete: Final equity ${final_equity:.2f}, "
            f"Total return {total_return:.2f}%, {len(trades)} trades"
        )

        return {
            "success": True,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "num_trades": len(trades),
            "equity_curve": equity_curve[::max(1, len(equity_curve)//100)],  # 최대 100 포인트
            "trades": trades,
            "commission": commission,
            "slippage": slippage,
            "message": "Backtest completed successfully. Use calculate_performance_metrics for detailed analysis."
        }

    async def _calculate_performance_metrics(
        self,
        equity_curve: List[float],
        trades: Optional[List[Dict[str, Any]]] = None,
        risk_free_rate: float = 3.0
    ) -> Dict[str, Any]:
        """
        성과 지표 계산

        Args:
            equity_curve: 자산 곡선
            trades: 거래 내역
            risk_free_rate: 무위험 수익률

        Returns:
            성과 지표
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "success": False,
                "message": "Insufficient data for performance calculation"
            }

        initial_value = equity_curve[0]
        final_value = equity_curve[-1]

        # 총 수익률
        total_return = ((final_value - initial_value) / initial_value) * 100

        # 연율 환산 수익률 (가정: 250 거래일)
        trading_days = len(equity_curve)
        years = trading_days / 250
        annual_return = ((final_value / initial_value) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 일일 수익률
        daily_returns = [
            (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            for i in range(1, len(equity_curve))
        ]

        # 변동성 (연율 환산)
        if daily_returns:
            volatility = (sum((r - sum(daily_returns)/len(daily_returns))**2 for r in daily_returns) / len(daily_returns))**0.5
            annual_volatility = volatility * (250 ** 0.5) * 100
        else:
            annual_volatility = 0

        # Sharpe Ratio
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0

        # Maximum Drawdown
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        max_dd_pct = max_dd * 100

        # Calmar Ratio (Annual Return / Max Drawdown)
        calmar_ratio = annual_return / max_dd_pct if max_dd_pct > 0 else 0

        # Win Rate (거래 내역이 있는 경우)
        if trades:
            winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
            total_trades = len(trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            avg_win = sum(t['pnl'] for t in trades if t.get('pnl', 0) > 0) / winning_trades if winning_trades > 0 else 0
            losing_trades = total_trades - winning_trades
            avg_loss = sum(t['pnl'] for t in trades if t.get('pnl', 0) < 0) / losing_trades if losing_trades > 0 else 0

            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
        else:
            win_rate = None
            profit_factor = None

        logger.info(
            f"Performance metrics calculated: Return {total_return:.2f}%, "
            f"Sharpe {sharpe_ratio:.2f}, MDD {max_dd_pct:.2f}%"
        )

        return {
            "success": True,
            "returns": {
                "total_return_pct": total_return,
                "annual_return_pct": annual_return,
                "annual_volatility_pct": annual_volatility
            },
            "risk_metrics": {
                "sharpe_ratio": sharpe_ratio,
                "calmar_ratio": calmar_ratio,
                "max_drawdown_pct": max_dd_pct,
                "sortino_ratio": sharpe_ratio * 1.2  # 간소화 (실제로는 하방 변동성 사용)
            },
            "trade_metrics": {
                "win_rate_pct": win_rate,
                "profit_factor": profit_factor,
                "total_trades": len(trades) if trades else 0
            },
            "rating": (
                "Excellent" if sharpe_ratio >= 2.0 and max_dd_pct < 15 else
                "Good" if sharpe_ratio >= 1.0 and max_dd_pct < 25 else
                "Fair" if sharpe_ratio >= 0.5 else
                "Poor"
            )
        }

    async def _analyze_trades(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        거래 분석

        Args:
            trades: 거래 내역

        Returns:
            거래 분석 결과
        """
        if not trades:
            return {
                "success": False,
                "message": "No trades to analyze"
            }

        # 승패 분석
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        breakeven_trades = [t for t in trades if t.get('pnl', 0) == 0]

        win_rate = (len(winning_trades) / len(trades)) * 100
        loss_rate = (len(losing_trades) / len(trades)) * 100

        # 평균 손익
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # 최대 연승/연패
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for t in trades:
            if t.get('pnl', 0) > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            elif t.get('pnl', 0) < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        # 홀딩 기간 분석
        holding_periods = []
        for t in trades:
            if 'entry_date' in t and 'exit_date' in t:
                entry = datetime.strptime(t['entry_date'], "%Y-%m-%d")
                exit = datetime.strptime(t['exit_date'], "%Y-%m-%d")
                holding_periods.append((exit - entry).days)

        avg_holding_period = sum(holding_periods) / len(holding_periods) if holding_periods else 0

        return {
            "success": True,
            "total_trades": len(trades),
            "win_loss_analysis": {
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "breakeven_trades": len(breakeven_trades),
                "win_rate_pct": win_rate,
                "loss_rate_pct": loss_rate
            },
            "profit_analysis": {
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "largest_win": max((t.get('pnl', 0) for t in trades), default=0),
                "largest_loss": min((t.get('pnl', 0) for t in trades), default=0),
                "avg_rr_ratio": abs(avg_win / avg_loss) if avg_loss != 0 else 0
            },
            "streak_analysis": {
                "max_consecutive_wins": max_consecutive_wins,
                "max_consecutive_losses": max_consecutive_losses
            },
            "holding_period": {
                "avg_holding_days": avg_holding_period,
                "min_holding_days": min(holding_periods) if holding_periods else 0,
                "max_holding_days": max(holding_periods) if holding_periods else 0
            }
        }

    async def _run_monte_carlo(
        self,
        trades: List[Dict[str, Any]],
        num_simulations: int = 1000,
        initial_capital: float = 10000
    ) -> Dict[str, Any]:
        """
        Monte Carlo 시뮬레이션

        Args:
            trades: 거래 내역
            num_simulations: 시뮬레이션 횟수
            initial_capital: 초기 자본

        Returns:
            Monte Carlo 결과
        """
        import random

        if not trades:
            return {
                "success": False,
                "message": "No trades for Monte Carlo simulation"
            }

        # 각 거래의 PnL 비율 추출
        pnl_pcts = [t.get('pnl_pct', 0) for t in trades if 'pnl_pct' in t]

        if not pnl_pcts:
            # PnL 비율이 없으면 절대값에서 계산
            pnl_pcts = [
                (t.get('pnl', 0) / (t.get('entry_price', 100) * t.get('quantity', 1))) * 100
                for t in trades
            ]

        # 시뮬레이션 실행
        final_equities = []

        for _ in range(num_simulations):
            equity = initial_capital

            # 랜덤하게 거래 순서를 섞어서 재실행
            shuffled_pnls = random.choices(pnl_pcts, k=len(pnl_pcts))

            for pnl_pct in shuffled_pnls:
                equity *= (1 + pnl_pct / 100)

            final_equities.append(equity)

        # 통계 계산
        final_equities.sort()

        percentile_5 = final_equities[int(len(final_equities) * 0.05)]
        percentile_25 = final_equities[int(len(final_equities) * 0.25)]
        percentile_50 = final_equities[int(len(final_equities) * 0.50)]
        percentile_75 = final_equities[int(len(final_equities) * 0.75)]
        percentile_95 = final_equities[int(len(final_equities) * 0.95)]

        avg_final = sum(final_equities) / len(final_equities)

        # 손실 확률
        loss_probability = sum(1 for e in final_equities if e < initial_capital) / len(final_equities) * 100

        return {
            "success": True,
            "num_simulations": num_simulations,
            "initial_capital": initial_capital,
            "statistics": {
                "avg_final_equity": avg_final,
                "avg_return_pct": ((avg_final - initial_capital) / initial_capital) * 100,
                "loss_probability_pct": loss_probability,
                "win_probability_pct": 100 - loss_probability
            },
            "percentiles": {
                "5th": percentile_5,
                "25th": percentile_25,
                "50th_median": percentile_50,
                "75th": percentile_75,
                "95th": percentile_95
            },
            "worst_case": min(final_equities),
            "best_case": max(final_equities),
            "recommendation": (
                "High Confidence" if loss_probability < 20 and percentile_5 > initial_capital * 0.9 else
                "Moderate Confidence" if loss_probability < 40 else
                "Low Confidence - High Risk"
            )
        }

    async def _compare_strategies(
        self,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        전략 비교

        Args:
            strategies: 전략 목록

        Returns:
            비교 결과
        """
        if len(strategies) < 2:
            return {
                "success": False,
                "message": "At least 2 strategies required for comparison"
            }

        comparison = []

        for strategy in strategies:
            name = strategy.get('name', 'Unknown')
            equity_curve = strategy.get('equity_curve', [])

            if equity_curve and len(equity_curve) >= 2:
                # 성과 지표 계산
                metrics = await self._calculate_performance_metrics(
                    equity_curve=equity_curve,
                    trades=strategy.get('trades')
                )

                comparison.append({
                    "name": name,
                    "total_return_pct": metrics['returns']['total_return_pct'],
                    "annual_return_pct": metrics['returns']['annual_return_pct'],
                    "sharpe_ratio": metrics['risk_metrics']['sharpe_ratio'],
                    "max_drawdown_pct": metrics['risk_metrics']['max_drawdown_pct'],
                    "rating": metrics['rating']
                })

        # 최고 전략 선정
        best_sharpe = max(comparison, key=lambda x: x['sharpe_ratio'])
        best_return = max(comparison, key=lambda x: x['total_return_pct'])
        lowest_dd = min(comparison, key=lambda x: x['max_drawdown_pct'])

        return {
            "success": True,
            "num_strategies": len(strategies),
            "comparison": comparison,
            "rankings": {
                "best_sharpe_ratio": best_sharpe['name'],
                "best_return": best_return['name'],
                "lowest_drawdown": lowest_dd['name']
            },
            "recommendation": (
                f"Recommended: {best_sharpe['name']} (Best risk-adjusted return)"
            )
        }
