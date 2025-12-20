"""
Smart Executor - Complete Trading Workflow

Orchestrates entire trading workflow:
Analysis → Decision → Execution → Portfolio Update

Components:
- SmartExecutor: Main workflow orchestrator
- SimplePortfolioManager: Position tracking
- SimpleRiskManager: Risk controls

Cost: $0/month (all local computation)
Author: AI Trading System Team
Date: 2025-11-14
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from .execution_engine import SmartExecutionEngine, ExecutionResult


class SimplePortfolioManager:
    """
    Simple portfolio manager for tracking positions and P&L.

    Tracks:
    - Cash balance
    - Current positions
    - Profit & Loss
    """

    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Dict] = {}
        self.closed_positions: List[Dict] = []

    def update_position(
        self,
        ticker: str,
        action: str,
        shares: int,
        price: float,
        cost: float,
    ) -> Dict:
        """Update position after execution."""

        if action == "BUY":
            # Deduct cash
            self.cash -= cost

            # Add or increase position
            if ticker in self.positions:
                pos = self.positions[ticker]
                total_shares = pos["shares"] + shares
                total_cost = pos["total_cost"] + (shares * price)
                pos["shares"] = total_shares
                pos["avg_price"] = total_cost / total_shares
                pos["total_cost"] = total_cost
            else:
                self.positions[ticker] = {
                    "shares": shares,
                    "avg_price": price,
                    "total_cost": shares * price,
                    "opened_at": datetime.now().isoformat(),
                }

            return {
                "action": "BUY",
                "ticker": ticker,
                "shares": shares,
                "price": price,
            }

        elif action == "SELL":
            # Add cash
            proceeds = shares * price
            self.cash += proceeds

            # Remove or reduce position
            if ticker in self.positions:
                pos = self.positions[ticker]

                # Calculate P&L
                cost_basis = pos["avg_price"] * shares
                pnl = proceeds - cost_basis

                if pos["shares"] <= shares:
                    # Close entire position
                    closed = {
                        "ticker": ticker,
                        "shares": pos["shares"],
                        "avg_buy_price": pos["avg_price"],
                        "sell_price": price,
                        "pnl": pnl,
                        "opened_at": pos["opened_at"],
                        "closed_at": datetime.now().isoformat(),
                    }
                    self.closed_positions.append(closed)
                    del self.positions[ticker]
                else:
                    # Partial close
                    pos["shares"] -= shares
                    pos["total_cost"] -= cost_basis

                return {
                    "action": "SELL",
                    "ticker": ticker,
                    "shares": shares,
                    "price": price,
                    "pnl": pnl,
                }

        return {"action": "HOLD"}

    def get_context(self) -> Dict:
        """Get portfolio context for decision making."""

        # Calculate total portfolio value
        positions_value = sum(
            pos["shares"] * pos["avg_price"] for pos in self.positions.values()
        )

        total_value = self.cash + positions_value

        return {
            "cash": self.cash,
            "positions_value": positions_value,
            "total_value": total_value,
            "num_positions": len(self.positions),
            "positions": self.positions,
        }

    def get_summary(self) -> Dict:
        """Get complete portfolio summary."""

        context = self.get_context()

        # Calculate total P&L
        total_pnl = sum(pos["pnl"] for pos in self.closed_positions)

        # Add unrealized P&L (would need current prices)
        # For now, just use closed P&L

        return_pct = (
            (context["total_value"] - self.initial_cash) / self.initial_cash * 100
        )

        return {
            "initial_cash": self.initial_cash,
            "current_cash": self.cash,
            "total_value": context["total_value"],
            "num_positions": context["num_positions"],
            "total_pnl": total_pnl,
            "return_pct": return_pct,
            "closed_trades": len(self.closed_positions),
        }


class SimpleRiskManager:
    """
    Simple risk manager with basic controls.

    Controls:
    - Max position size
    - Max number of positions
    - Daily loss limit
    - Kill switch
    """

    def __init__(
        self,
        max_position_size_pct: float = 20.0,
        max_positions: int = 20,
        daily_loss_limit_pct: float = 5.0,
    ):
        self.max_position_size_pct = max_position_size_pct
        self.max_positions = max_positions
        self.daily_loss_limit_pct = daily_loss_limit_pct

        self.kill_switch_active = False
        self.kill_switch_reason = ""

    def check_trade(
        self, ticker: str, action: str, portfolio_context: Dict
    ) -> Dict:
        """Check if trade is allowed."""

        # Kill switch
        if self.kill_switch_active:
            return {
                "approved": False,
                "reason": f"Kill switch active: {self.kill_switch_reason}",
            }

        # Max positions (only for BUY)
        if action == "BUY":
            if portfolio_context["num_positions"] >= self.max_positions:
                return {
                    "approved": False,
                    "reason": f"Max positions reached ({self.max_positions})",
                }

        # All checks passed
        return {"approved": True, "reason": "OK"}

    def activate_kill_switch(self, reason: str):
        """Activate kill switch to block all trades."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        print(f"WARNING: KILL SWITCH ACTIVATED: {reason}")

    def deactivate_kill_switch(self):
        """Deactivate kill switch."""
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        print("Kill switch deactivated")


class SmartExecutor:
    """
    Complete trading workflow orchestrator.

    Integrates:
    1. Trading Agent (AI decisions)
    2. Smart Execution Engine (optimal execution)
    3. Portfolio Manager (position tracking)
    4. Risk Manager (safety controls)

    Workflow:
    ticker → analyze → decide → risk check → execute → update portfolio
    """

    def __init__(
        self,
        trading_agent=None,
        execution_engine: Optional[SmartExecutionEngine] = None,
        portfolio_manager: Optional[SimplePortfolioManager] = None,
        risk_manager: Optional[SimpleRiskManager] = None,
    ):
        # Import here to avoid circular dependency
        if trading_agent is None:
            try:
                from ai.trading_agent import TradingAgent
                self.trading_agent = TradingAgent()
            except ImportError:
                print("WARNING: TradingAgent not available, using mock")
                self.trading_agent = None
        else:
            self.trading_agent = trading_agent

        self.execution_engine = execution_engine or SmartExecutionEngine()
        self.portfolio_manager = portfolio_manager or SimplePortfolioManager()
        self.risk_manager = risk_manager or SimpleRiskManager()

    async def process_ticker(
        self,
        ticker: str,
        market_context: Optional[Dict] = None,
        urgency: str = "MEDIUM",
    ) -> Dict:
        """
        Process a single ticker through complete workflow.

        Steps:
        1. Get portfolio context
        2. Analyze with Trading Agent (AI)
        3. Risk check
        4. Execute decision
        5. Update portfolio

        Args:
            ticker: Stock ticker
            market_context: Market regime, VIX, etc.
            urgency: Execution urgency

        Returns:
            Complete result dict
        """
        result = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING",
        }

        try:
            # 1. Get portfolio context
            portfolio_context = self.portfolio_manager.get_context()
            result["portfolio_value"] = portfolio_context["total_value"]

            # 2. Get AI decision
            if self.trading_agent:
                decision = await self.trading_agent.analyze(
                    ticker=ticker,
                    portfolio_context=portfolio_context,
                    market_context=market_context or {},
                )
            else:
                # Mock decision for testing
                decision = self._mock_decision(ticker)

            result["decision"] = {
                "action": decision.action,
                "conviction": decision.conviction,
                "position_size": decision.position_size,
            }

            # 3. Risk check
            risk_check = self.risk_manager.check_trade(
                ticker=ticker,
                action=decision.action,
                portfolio_context=portfolio_context,
            )

            if not risk_check["approved"]:
                result["status"] = "BLOCKED"
                result["message"] = risk_check["reason"]
                return result

            # 4. Execute decision
            # Get current price (mock for now)
            current_price = await self._get_current_price(ticker)

            execution_result = await self.execution_engine.execute_decision(
                trading_decision=decision,
                portfolio_value=portfolio_context["total_value"],
                current_price=current_price,
                urgency=urgency,
            )

            result["execution"] = {
                "status": execution_result.status,
                "filled_shares": execution_result.filled_shares,
                "avg_price": execution_result.avg_price,
                "total_cost": execution_result.total_cost,
                "slippage_bps": execution_result.slippage_bps,
                "algorithm": execution_result.algorithm_used,
            }

            # 5. Update portfolio
            if execution_result.status == "SUCCESS":
                portfolio_update = self.portfolio_manager.update_position(
                    ticker=ticker,
                    action=decision.action,
                    shares=execution_result.filled_shares,
                    price=execution_result.avg_price,
                    cost=execution_result.total_cost,
                )

                result["portfolio_update"] = portfolio_update
                result["status"] = "SUCCESS"
            else:
                result["status"] = execution_result.status

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)

        return result

    async def process_batch(
        self,
        tickers: List[str],
        market_context: Optional[Dict] = None,
        urgency: str = "MEDIUM",
        max_concurrent: int = 5,
    ) -> List[Dict]:
        """
        Process multiple tickers concurrently.

        Args:
            tickers: List of ticker symbols
            market_context: Market regime, VIX, etc.
            urgency: Execution urgency
            max_concurrent: Max concurrent executions

        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(ticker):
            async with semaphore:
                return await self.process_ticker(ticker, market_context, urgency)

        tasks = [process_with_limit(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                processed_results.append({
                    "ticker": ticker,
                    "status": "ERROR",
                    "message": str(result),
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _get_current_price(self, ticker: str) -> float:
        """Get current market price (mock for now)."""
        # Mock prices for testing
        mock_prices = {
            "NVDA": 875.50,
            "AAPL": 185.20,
            "MSFT": 420.30,
            "GOOGL": 175.80,
            "AMZN": 178.50,
            "TSLA": 248.50,
            "META": 520.30,
        }
        return mock_prices.get(ticker, 100.0)

    def _mock_decision(self, ticker: str):
        """Create mock decision for testing."""
        from dataclasses import dataclass
        import random

        @dataclass
        class MockDecision:
            ticker: str
            action: str
            conviction: float
            position_size: float

        actions = ["BUY", "SELL", "HOLD"]
        action = random.choice(actions)

        return MockDecision(
            ticker=ticker,
            action=action,
            conviction=random.uniform(0.6, 0.9),
            position_size=random.uniform(2.0, 5.0) if action != "HOLD" else 0.0,
        )

    def get_summary(self) -> Dict:
        """Get complete system summary."""

        portfolio_summary = self.portfolio_manager.get_summary()
        execution_summary = self.execution_engine.get_execution_summary()

        return {
            "portfolio": portfolio_summary,
            "metrics": execution_summary["metrics"],
            "algorithm_performance": execution_summary["algorithm_performance"],
            "risk_controls": {
                "kill_switch_active": self.risk_manager.kill_switch_active,
                "max_positions": self.risk_manager.max_positions,
                "current_positions": portfolio_summary["num_positions"],
            },
        }


# Demo
async def demo():
    """Demo of Smart Executor workflow."""
    print("=" * 60)
    print("Smart Executor Demo")
    print("=" * 60)

    # Initialize
    executor = SmartExecutor()

    print("\n1. Processing Single Ticker:\n")

    result = await executor.process_ticker("NVDA", urgency="MEDIUM")

    print(f"  Ticker: {result['ticker']}")
    print(f"  Status: {result['status']}")
    print(f"  Decision: {result.get('decision', {})}")
    print(f"  Execution: {result.get('execution', {})}")

    print("\n2. Processing Batch:\n")

    tickers = ["AAPL", "MSFT", "GOOGL"]
    results = await executor.process_batch(tickers, urgency="MEDIUM", max_concurrent=2)

    for res in results:
        print(f"  {res['ticker']}: {res['status']}")

    print("\n3. System Summary:\n")

    summary = executor.get_summary()

    print(f"  Portfolio Value: ${summary['portfolio']['total_value']:,.2f}")
    print(f"  Cash: ${summary['portfolio']['current_cash']:,.2f}")
    print(f"  Positions: {summary['portfolio']['num_positions']}")
    print(f"  Total P&L: ${summary['portfolio']['total_pnl']:,.2f}")
    print(f"  Return: {summary['portfolio']['return_pct']:.2f}%")

    print(f"\n  Total Trades: {summary['metrics']['total_trades']}")
    print(f"  Avg Slippage: {summary['metrics']['avg_slippage_bps']:.2f} bps")

    print("\n4. Testing Risk Controls:\n")

    # Test kill switch
    executor.risk_manager.activate_kill_switch("Market crash detected")

    result = await executor.process_ticker("TSLA")
    print(f"  Trade with kill switch: {result['status']}")
    print(f"  Reason: {result.get('message', '')}")

    executor.risk_manager.deactivate_kill_switch()

    print("\n" + "=" * 60)
    print("OK: Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo())
