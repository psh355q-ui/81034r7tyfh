"""
Smart Execution Engine

Converts trading decisions into optimal order execution.
Selects algorithms based on urgency and market conditions.

Algorithm Selection:
- CRITICAL → Market Order (immediate)
- HIGH → Aggressive TWAP (5 min)
- MEDIUM → Standard TWAP (30 min)
- LOW → VWAP (volume-based)

Cost: $0/month (all local computation)
Author: AI Trading System Team
Date: 2025-11-14
"""

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ExecutionRequest:
    """Request to execute an order."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    shares: int
    urgency: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW


@dataclass
class ExecutionResult:
    """Result of order execution."""
    ticker: str
    action: str
    status: str  # SUCCESS, FAILED, NO_ACTION
    filled_shares: int
    avg_price: float
    total_cost: float
    slippage_bps: float
    commission: float
    algorithm_used: str
    child_orders: List[Dict]
    execution_time_ms: float
    timestamp: str


class SmartExecutionEngine:
    """
    Smart execution engine with algorithm selection.

    Converts TradingDecision into optimal order execution,
    minimizing slippage and market impact.

    Features:
    - Algorithm selection based on urgency
    - Market impact estimation
    - Slippage tracking
    - Execution quality metrics
    """

    def __init__(self):
        self.execution_history: List[ExecutionResult] = []

    async def execute_decision(
        self,
        trading_decision,
        portfolio_value: float,
        current_price: float,
        urgency: str = "MEDIUM",
    ) -> ExecutionResult:
        """
        Execute a trading decision.

        Args:
            trading_decision: TradingDecision from AI agent
            portfolio_value: Current portfolio value
            current_price: Current market price
            urgency: Execution urgency (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()

        # Handle HOLD
        if trading_decision.action == "HOLD":
            return ExecutionResult(
                ticker=trading_decision.ticker,
                action="HOLD",
                status="NO_ACTION",
                filled_shares=0,
                avg_price=current_price,
                total_cost=0.0,
                slippage_bps=0.0,
                commission=0.0,
                algorithm_used="NONE",
                child_orders=[],
                execution_time_ms=0.0,
                timestamp=datetime.now().isoformat(),
            )

        # Calculate order size
        shares = self._calculate_order_size(
            trading_decision, portfolio_value, current_price
        )

        if shares == 0:
            return ExecutionResult(
                ticker=trading_decision.ticker,
                action=trading_decision.action,
                status="NO_ACTION",
                filled_shares=0,
                avg_price=current_price,
                total_cost=0.0,
                slippage_bps=0.0,
                commission=0.0,
                algorithm_used="NONE",
                child_orders=[],
                execution_time_ms=0.0,
                timestamp=datetime.now().isoformat(),
            )

        # Create execution request
        request = ExecutionRequest(
            ticker=trading_decision.ticker,
            action=trading_decision.action,
            shares=shares,
            urgency=urgency,
        )

        # Execute with selected algorithm
        result = await self._execute_with_algorithm(request, current_price)

        # Calculate execution time
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.execution_time_ms = execution_time_ms

        # Store in history
        self.execution_history.append(result)

        return result

    async def _execute_with_algorithm(
        self, request: ExecutionRequest, current_price: float
    ) -> ExecutionResult:
        """Select and execute with appropriate algorithm."""

        if request.urgency == "CRITICAL":
            # Market order - immediate execution
            return await self._execute_market_order(request, current_price)

        elif request.urgency == "HIGH":
            # Aggressive TWAP - 5 minutes, 5 slices
            return await self._simulate_twap(
                request, current_price, duration=5, slices=5
            )

        elif request.urgency == "MEDIUM":
            # Standard TWAP - 30 minutes, 10 slices
            return await self._simulate_twap(
                request, current_price, duration=30, slices=10
            )

        else:  # LOW
            # VWAP - volume-based
            return await self._simulate_vwap(request, current_price)

    async def _execute_market_order(
        self, request: ExecutionRequest, current_price: float
    ) -> ExecutionResult:
        """Execute market order (immediate, higher slippage)."""

        # Simulate market impact (higher for immediate execution)
        slippage_pct = 0.05 + random.uniform(0, 0.05)  # 5-10 bps

        if request.action == "BUY":
            fill_price = current_price * (1 + slippage_pct / 100)
        else:
            fill_price = current_price * (1 - slippage_pct / 100)

        total_cost = request.shares * fill_price
        commission = request.shares * 0.005  # $0.005 per share

        slippage_bps = abs(fill_price - current_price) / current_price * 10000

        return ExecutionResult(
            ticker=request.ticker,
            action=request.action,
            status="SUCCESS",
            filled_shares=request.shares,
            avg_price=fill_price,
            total_cost=total_cost + commission,
            slippage_bps=slippage_bps,
            commission=commission,
            algorithm_used="MARKET",
            child_orders=[{
                "slice": 1,
                "shares": request.shares,
                "price": fill_price,
            }],
            execution_time_ms=0.0,
            timestamp=datetime.now().isoformat(),
        )

    async def _simulate_twap(
        self,
        request: ExecutionRequest,
        current_price: float,
        duration: int,
        slices: int,
    ) -> ExecutionResult:
        """Simulate TWAP execution."""

        shares_per_slice = request.shares // slices
        remaining = request.shares - (shares_per_slice * slices)

        child_orders = []
        total_filled = 0
        total_cost = 0.0

        # Simulate each slice
        for i in range(slices):
            shares = shares_per_slice + (remaining if i == slices - 1 else 0)

            # Price walks randomly (mean-reverting)
            price_change_pct = random.uniform(-0.02, 0.02)  # ±2 bps per slice
            slice_price = current_price * (1 + price_change_pct / 100)

            if request.action == "BUY":
                # Slight adverse selection
                slice_price *= (1 + 0.01 / 100)  # +1 bps
            else:
                slice_price *= (1 - 0.01 / 100)  # -1 bps

            child_orders.append({
                "slice": i + 1,
                "shares": shares,
                "price": slice_price,
            })

            total_filled += shares
            total_cost += shares * slice_price

            # Simulate time delay
            await asyncio.sleep(0.001)  # Minimal delay for simulation

        avg_price = total_cost / total_filled
        commission = total_filled * 0.005
        slippage_bps = abs(avg_price - current_price) / current_price * 10000

        algo_name = "TWAP_AGGRESSIVE" if duration <= 5 else "TWAP_STANDARD"

        return ExecutionResult(
            ticker=request.ticker,
            action=request.action,
            status="SUCCESS",
            filled_shares=total_filled,
            avg_price=avg_price,
            total_cost=total_cost + commission,
            slippage_bps=slippage_bps,
            commission=commission,
            algorithm_used=algo_name,
            child_orders=child_orders,
            execution_time_ms=0.0,
            timestamp=datetime.now().isoformat(),
        )

    async def _simulate_vwap(
        self, request: ExecutionRequest, current_price: float
    ) -> ExecutionResult:
        """Simulate VWAP execution (volume-weighted)."""

        # Typical intraday volume curve (U-shaped)
        volume_curve = [0.15, 0.08, 0.06, 0.05, 0.05, 0.05, 0.05, 0.06, 0.08, 0.37]

        child_orders = []
        total_filled = 0
        total_cost = 0.0

        for i, vol_pct in enumerate(volume_curve):
            shares = int(request.shares * vol_pct)
            if shares == 0:
                continue

            # Price walks with volume (higher volume = better execution)
            if vol_pct > 0.1:  # High volume periods
                price_impact = 0.005  # 0.5 bps
            else:
                price_impact = 0.015  # 1.5 bps

            if request.action == "BUY":
                slice_price = current_price * (1 + price_impact / 100)
            else:
                slice_price = current_price * (1 - price_impact / 100)

            # Add random noise
            slice_price *= (1 + random.uniform(-0.01, 0.01) / 100)

            child_orders.append({
                "slice": i + 1,
                "shares": shares,
                "price": slice_price,
                "volume_pct": vol_pct,
            })

            total_filled += shares
            total_cost += shares * slice_price

            await asyncio.sleep(0.001)

        # Handle rounding remainder
        if total_filled < request.shares:
            remaining = request.shares - total_filled
            last_price = child_orders[-1]["price"]
            child_orders[-1]["shares"] += remaining
            total_filled += remaining
            total_cost += remaining * last_price

        avg_price = total_cost / total_filled
        commission = total_filled * 0.005
        slippage_bps = abs(avg_price - current_price) / current_price * 10000

        return ExecutionResult(
            ticker=request.ticker,
            action=request.action,
            status="SUCCESS",
            filled_shares=total_filled,
            avg_price=avg_price,
            total_cost=total_cost + commission,
            slippage_bps=slippage_bps,
            commission=commission,
            algorithm_used="VWAP",
            child_orders=child_orders,
            execution_time_ms=0.0,
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_order_size(
        self, trading_decision, portfolio_value: float, current_price: float
    ) -> int:
        """
        Calculate number of shares to trade.

        Args:
            trading_decision: TradingDecision with position_size (%)
            portfolio_value: Total portfolio value
            current_price: Current stock price

        Returns:
            Number of shares to trade
        """
        position_size_pct = trading_decision.position_size
        dollar_amount = portfolio_value * (position_size_pct / 100.0)
        shares = int(dollar_amount / current_price)
        return shares

    def _estimate_market_impact(self, shares: int, style: str) -> float:
        """
        Estimate market impact in basis points.

        Simple model: base 0.5 bps per 100 shares,
        multiplied by execution style.
        """
        base_impact = (shares / 100) * 0.5

        multipliers = {
            "PASSIVE": 0.5,
            "MODERATE": 1.0,
            "AGGRESSIVE": 2.0,
        }

        multiplier = multipliers.get(style, 1.0)
        return base_impact * multiplier

    def get_execution_summary(self) -> Dict:
        """Get summary of all executions."""

        if not self.execution_history:
            return {
                "metrics": {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "avg_slippage_bps": 0.0,
                    "total_volume_traded": 0,
                    "total_commission": 0.0,
                },
                "algorithm_performance": {},
            }

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.status == "SUCCESS")

        avg_slippage = sum(r.slippage_bps for r in self.execution_history) / total
        total_volume = sum(r.filled_shares for r in self.execution_history)
        total_commission = sum(r.commission for r in self.execution_history)

        # Algorithm performance
        algo_stats = {}
        for result in self.execution_history:
            algo = result.algorithm_used
            if algo not in algo_stats:
                algo_stats[algo] = {
                    "count": 0,
                    "total_slippage": 0.0,
                    "total_volume": 0,
                }

            algo_stats[algo]["count"] += 1
            algo_stats[algo]["total_slippage"] += result.slippage_bps
            algo_stats[algo]["total_volume"] += result.filled_shares

        # Calculate averages
        for algo, stats in algo_stats.items():
            stats["avg_slippage_bps"] = stats["total_slippage"] / stats["count"]

        return {
            "metrics": {
                "total_executions": total,
                "successful_executions": successful,
                "avg_slippage_bps": avg_slippage,
                "total_volume_traded": total_volume,
                "total_commission": total_commission,
            },
            "algorithm_performance": algo_stats,
        }


# Demo
async def demo():
    """Demo of Smart Execution Engine."""
    print("=" * 60)
    print("Smart Execution Engine Demo")
    print("=" * 60)

    from dataclasses import dataclass

    @dataclass
    class MockDecision:
        ticker: str
        action: str
        position_size: float
        conviction: float = 0.8

    engine = SmartExecutionEngine()

    # Test cases
    test_cases = [
        ("NVDA", "BUY", 5.0, "MEDIUM", 875.50),
        ("AAPL", "BUY", 3.0, "HIGH", 185.20),
        ("MSFT", "SELL", 4.0, "LOW", 420.30),
        ("GOOGL", "HOLD", 0.0, "MEDIUM", 175.80),
    ]

    print("\n1. Executing Trading Decisions:\n")

    for ticker, action, pos_size, urgency, price in test_cases:
        decision = MockDecision(
            ticker=ticker,
            action=action,
            position_size=pos_size,
        )

        result = await engine.execute_decision(
            trading_decision=decision,
            portfolio_value=100000.0,
            current_price=price,
            urgency=urgency,
        )

        print(f"  Test: {ticker}")
        print(f"    Action: {action}")
        print(f"    Position Size: {pos_size}%")
        print(f"    Urgency: {urgency}")
        print(f"    Result: {result.status}")

        if result.status == "SUCCESS":
            print(f"    Shares: {result.filled_shares}")
            print(f"    Avg Price: ${result.avg_price:.2f}")
            print(f"    Slippage: {result.slippage_bps:.2f} bps")
            print(f"    Algorithm: {result.algorithm_used}")
            print(f"    Child Orders: {len(result.child_orders)}")

        print()

    # Summary
    summary = engine.get_execution_summary()

    print("\n2. Execution Summary:")
    print(f"  Total Executions: {summary['metrics']['total_executions']}")
    print(f"  Successful: {summary['metrics']['successful_executions']}")
    print(f"  Average Slippage: {summary['metrics']['avg_slippage_bps']:.2f} bps")
    print(f"  Total Volume: {summary['metrics']['total_volume_traded']} shares")
    print(f"  Total Commission: ${summary['metrics']['total_commission']:.2f}")

    print("\n3. Algorithm Performance:")
    for algo, stats in summary['algorithm_performance'].items():
        print(f"  {algo}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg Slippage: {stats['avg_slippage_bps']:.2f} bps")
        print(f"    Total Volume: {stats['total_volume']} shares")

    print("\n" + "=" * 60)
    print("✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo())
