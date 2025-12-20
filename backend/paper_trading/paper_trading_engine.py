"""
Paper Trading Engine - Real-time Trading Simulation

Simulates live trading with real market data but without real money.

Features:
- Real-time market data integration
- AI-driven decision making
- Live portfolio tracking
- Metrics and alerting
- Execution simulation with slippage

Author: AI Trading System Team
Date: 2025-11-15
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from .market_data_fetcher import MarketDataFetcher, MarketQuote
from .live_portfolio import LivePortfolio, Order, OrderStatus

# Try to import AI and execution components
try:
    from strategies import EnsembleStrategy
    from execution import SmartExecutor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    EnsembleStrategy = None
    SmartExecutor = None

# Try to import monitoring
try:
    from monitoring import MetricsCollector, AlertManager
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    MetricsCollector = None
    AlertManager = None

# Try to import notifications
try:
    from notifications import NotificationManager
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    NotificationManager = None

logger = logging.getLogger(__name__)


@dataclass
class PaperTradingConfig:
    """Paper trading configuration."""
    initial_cash: float = 100000.0
    tickers: List[str] = None
    decision_interval_seconds: int = 60  # Make decisions every minute
    max_positions: int = 10
    commission_rate: float = 0.001
    slippage_bps: float = 2.0
    enable_ai: bool = True
    enable_monitoring: bool = True
    enable_notifications: bool = True  # Enable Telegram notifications

    def __post_init__(self):
        if self.tickers is None:
            self.tickers = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"]


class PaperTradingEngine:
    """
    Paper trading engine for real-time simulation.

    Features:
    - Real-time data fetching
    - AI decision making
    - Order execution simulation
    - Performance tracking
    """

    def __init__(self, config: PaperTradingConfig):
        """
        Initialize paper trading engine.

        Args:
            config: Paper trading configuration
        """
        self.config = config

        # Core components
        self.market_data = MarketDataFetcher(cache_ttl_seconds=15)
        self.portfolio = LivePortfolio(
            initial_cash=config.initial_cash,
            commission_rate=config.commission_rate,
            max_positions=config.max_positions,
        )

        # AI components (optional)
        self.ai_strategy = None
        if config.enable_ai and AI_AVAILABLE:
            try:
                self.ai_strategy = EnsembleStrategy()
                logger.info("AI Strategy enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize AI strategy: {e}")

        # Monitoring components (optional)
        self.metrics_collector = None
        self.alert_manager = None
        if config.enable_monitoring and MONITORING_AVAILABLE:
            try:
                self.metrics_collector = MetricsCollector()
                self.alert_manager = AlertManager()
                logger.info("Monitoring enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize monitoring: {e}")

        # Notification components (optional)
        self.notification_manager = None
        if config.enable_notifications and NOTIFICATIONS_AVAILABLE:
            try:
                # Get Telegram config from environment
                import os
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                chat_id = os.getenv("TELEGRAM_CHAT_ID")

                if bot_token and chat_id:
                    self.notification_manager = NotificationManager(
                        bot_token=bot_token,
                        chat_id=chat_id
                    )
                    logger.info("Telegram notifications enabled")
                else:
                    logger.warning("Telegram credentials not found in environment")
            except Exception as e:
                logger.warning(f"Failed to initialize notifications: {e}")

        # State
        self.running = False
        self.decision_count = 0
        self.execution_count = 0
        self.start_time = None

        # Custom strategy function
        self._custom_strategy_func: Optional[Callable] = None

        logger.info(f"Paper Trading Engine initialized with ${config.initial_cash:,.0f}")
        logger.info(f"Trading tickers: {', '.join(config.tickers)}")

    # ===== Strategy Functions =====

    def set_custom_strategy(self, strategy_func: Callable):
        """
        Set a custom strategy function.

        The function should take (engine, market_data) and return list of decisions.
        Each decision is a dict: {"ticker": str, "action": str, "position_size": float}
        """
        self._custom_strategy_func = strategy_func
        logger.info("Custom strategy function set")

    async def _make_decisions(self, market_data: Dict[str, MarketQuote]) -> List[Dict]:
        """
        Make trading decisions based on current market data.

        Args:
            market_data: Current market quotes

        Returns:
            List of trading decisions
        """
        # Use custom strategy if provided
        if self._custom_strategy_func:
            try:
                decisions = await self._custom_strategy_func(self, market_data)
                return decisions if decisions else []
            except Exception as e:
                logger.error(f"Custom strategy error: {e}")
                return []

        # Use AI strategy if available
        if self.ai_strategy:
            try:
                # This would call the actual AI ensemble
                # For now, use mock decisions
                logger.debug("Using AI strategy (mock)")
                return await self._mock_ai_decisions(market_data)
            except Exception as e:
                logger.error(f"AI strategy error: {e}")
                return []

        # Default: mock strategy
        return await self._mock_ai_decisions(market_data)

    async def _mock_ai_decisions(self, market_data: Dict[str, MarketQuote]) -> List[Dict]:
        """
        Mock AI decisions for testing.

        This is a simple momentum-based strategy for demonstration.
        """
        import random

        decisions = []

        # Random decision making (15% chance per ticker)
        for ticker, quote in market_data.items():
            if random.random() < 0.15:
                # Check if we have a position
                position = self.portfolio.get_position(ticker)

                if position:
                    # Consider selling if we have gains
                    if position.unrealized_pnl_pct > 5.0:
                        decisions.append({
                            "ticker": ticker,
                            "action": "SELL",
                            "position_size": 50.0,  # Sell 50%
                            "conviction": 0.7,
                            "reason": f"Take profit: +{position.unrealized_pnl_pct:.1f}%",
                        })
                    elif position.unrealized_pnl_pct < -3.0:
                        decisions.append({
                            "ticker": ticker,
                            "action": "SELL",
                            "position_size": 100.0,  # Sell all
                            "conviction": 0.8,
                            "reason": f"Stop loss: {position.unrealized_pnl_pct:.1f}%",
                        })
                else:
                    # Consider buying new position
                    if self.portfolio.cash > 5000 and len(self.portfolio.positions) < self.config.max_positions:
                        decisions.append({
                            "ticker": ticker,
                            "action": "BUY",
                            "position_size": random.uniform(2.0, 5.0),  # 2-5% of portfolio
                            "conviction": random.uniform(0.6, 0.9),
                            "reason": "Entry signal",
                        })

        return decisions

    # ===== Execution =====

    async def _execute_decision(self, decision: Dict, market_data: Dict[str, MarketQuote]) -> bool:
        """
        Execute a trading decision.

        Args:
            decision: Trading decision
            market_data: Current market data

        Returns:
            True if executed successfully
        """
        ticker = decision["ticker"]
        action = decision["action"]
        position_size = decision["position_size"]  # Percentage

        # Get current price
        if ticker not in market_data:
            logger.error(f"No market data for {ticker}")
            return False

        current_price = market_data[ticker].price

        # Calculate shares to trade
        if action == "BUY":
            # Calculate shares based on position size percentage of portfolio
            total_value = self.portfolio.get_total_value()
            target_value = (position_size / 100) * total_value
            shares = int(target_value / current_price)

            if shares == 0:
                logger.debug(f"Position size too small for {ticker}")
                return False

        elif action == "SELL":
            position = self.portfolio.get_position(ticker)
            if not position:
                logger.warning(f"No position to sell: {ticker}")
                return False

            # Calculate shares to sell based on percentage
            shares = int((position_size / 100) * position.shares)

            if shares == 0:
                logger.debug(f"Sell size too small for {ticker}")
                return False

        else:
            logger.error(f"Invalid action: {action}")
            return False

        # Create order
        order = self.portfolio.create_order(ticker, action, shares, current_price)

        if not order:
            logger.warning(f"Failed to create order: {action} {shares} {ticker}")
            return False

        # Simulate fill with slippage
        slippage_factor = self.config.slippage_bps / 10000
        if action == "BUY":
            fill_price = current_price * (1 + slippage_factor)
        else:
            fill_price = current_price * (1 - slippage_factor)

        # Fill order
        success = self.portfolio.fill_order(order, fill_price, self.config.slippage_bps)

        if success:
            self.execution_count += 1

            # Record metrics
            if self.metrics_collector:
                self.metrics_collector.record_execution(
                    ticker=ticker,
                    action=action,
                    shares=shares,
                    price=fill_price,
                    slippage_bps=self.config.slippage_bps,
                    algorithm="PAPER_TRADING",
                    commission=order.commission,
                )

            # Send alert
            if self.alert_manager:
                await self.alert_manager.alert_trade_executed(
                    ticker=ticker,
                    action=action,
                    shares=shares,
                    price=fill_price,
                )

            # Send Telegram notification
            if self.notification_manager:
                try:
                    await self.notification_manager.notifier.send_execution_report(
                        ticker=ticker,
                        side=action,
                        quantity=shares,
                        avg_price=fill_price,
                        total_value=shares * fill_price,
                        algorithm="PAPER_TRADING",
                        slippage_bps=self.config.slippage_bps,
                        commission=order.commission,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send Telegram notification: {e}")

            logger.info(f"EXECUTED: {action} {shares} {ticker} @ ${fill_price:.2f}")
            return True

        return False

    # ===== Main Loop =====

    async def _trading_loop(self):
        """Main trading loop."""
        logger.info("Trading loop started")

        while self.running:
            try:
                loop_start = datetime.now()

                # 1. Fetch market data
                market_data = await self.market_data.get_quotes_batch(self.config.tickers)

                if not market_data:
                    logger.warning("No market data available")
                    await asyncio.sleep(self.config.decision_interval_seconds)
                    continue

                # 2. Update portfolio prices
                prices = {ticker: quote.price for ticker, quote in market_data.items()}
                self.portfolio.update_prices(prices)

                # 3. Make decisions
                decisions = await self._make_decisions(market_data)
                self.decision_count += len(decisions)

                # 4. Execute decisions
                if decisions:
                    logger.info(f"Making {len(decisions)} trading decisions")

                    for decision in decisions:
                        await self._execute_decision(decision, market_data)

                # 5. Update metrics
                if self.metrics_collector:
                    summary = self.portfolio.get_summary()
                    self.metrics_collector.update_portfolio(
                        total_value=summary["total_value"],
                        num_positions=summary["positions_count"],
                        total_pnl=summary["total_pnl"],
                        cash=summary["cash"],
                        return_pct=summary["total_return_pct"],
                    )
                    self.metrics_collector.heartbeat()

                # 6. Log status
                self._log_status()

                # Wait for next interval
                elapsed = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(0, self.config.decision_interval_seconds - elapsed)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.decision_interval_seconds)

        logger.info("Trading loop stopped")

    def _log_status(self):
        """Log current status."""
        summary = self.portfolio.get_summary()

        logger.info(f"Portfolio: ${summary['total_value']:,.2f} | "
                   f"P&L: ${summary['total_pnl']:+,.2f} ({summary['total_return_pct']:+.2f}%) | "
                   f"Positions: {summary['positions_count']} | "
                   f"Cash: ${summary['cash']:,.2f}")

    # ===== Control =====

    async def start(self):
        """Start paper trading."""
        if self.running:
            logger.warning("Paper trading already running")
            return

        self.running = True
        self.start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("PAPER TRADING STARTED")
        logger.info("=" * 70)
        logger.info(f"Initial Capital: ${self.config.initial_cash:,.0f}")
        logger.info(f"Tickers: {', '.join(self.config.tickers)}")
        logger.info(f"Decision Interval: {self.config.decision_interval_seconds}s")
        logger.info("=" * 70)

        # Send startup alert
        if self.alert_manager:
            await self.alert_manager.send_alert(
                level=self.alert_manager.AlertLevel.LOW,
                category=self.alert_manager.AlertCategory.SYSTEM,
                title="Paper Trading Started",
                message=f"Started with ${self.config.initial_cash:,.0f}",
            )

        # Send Telegram startup notification
        if self.notification_manager:
            try:
                await self.notification_manager.notifier.send_startup_message(
                    version="Paper Trading v1.0",
                    mode="Paper Trading",
                    initial_capital=self.config.initial_cash,
                    tickers=self.config.tickers,
                )
            except Exception as e:
                logger.warning(f"Failed to send Telegram startup notification: {e}")

        # Start trading loop
        await self._trading_loop()

    def stop(self):
        """Stop paper trading."""
        if not self.running:
            logger.warning("Paper trading not running")
            return

        self.running = False
        logger.info("Stopping paper trading...")

    async def run_for_duration(self, duration_seconds: int):
        """
        Run paper trading for a specific duration.

        Args:
            duration_seconds: How long to run in seconds
        """
        # Start trading in background
        trading_task = asyncio.create_task(self.start())

        # Wait for duration
        await asyncio.sleep(duration_seconds)

        # Stop trading
        self.stop()
        await trading_task

        # Print final report
        self.print_summary()

    # ===== Reporting =====

    def get_status(self) -> Dict:
        """Get current status."""
        if not self.start_time:
            return {"status": "not_started"}

        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "status": "running" if self.running else "stopped",
            "uptime_seconds": uptime,
            "decision_count": self.decision_count,
            "execution_count": self.execution_count,
            "portfolio": self.portfolio.get_summary(),
            "market_data_cache": self.market_data.get_cache_stats(),
        }

    def print_summary(self):
        """Print trading summary."""
        summary = self.portfolio.get_summary()

        print("\n" + "=" * 70)
        print("PAPER TRADING SUMMARY")
        print("=" * 70)
        print(f"Duration: {summary['uptime']:.0f} seconds")
        print(f"\nInitial Capital: ${self.config.initial_cash:,.2f}")
        print(f"Final Value:     ${summary['total_value']:,.2f}")
        print(f"Total Return:    ${summary['total_pnl']:+,.2f} ({summary['total_return_pct']:+.2f}%)")
        print(f"\nRealized P&L:    ${summary['realized_pnl']:+,.2f}")
        print(f"Unrealized P&L:  ${summary['unrealized_pnl']:+,.2f}")
        print(f"\nCurrent Cash:    ${summary['cash']:,.2f}")
        print(f"Positions:       {summary['positions_count']}")
        print(f"Exposure:        {summary['exposure_pct']:.1f}%")
        print(f"\nTotal Trades:    {summary['total_trades']}")
        print(f"Commissions:     ${summary['total_commissions']:.2f}")
        print(f"Decisions Made:  {self.decision_count}")
        print("=" * 70)

        # Print positions
        if self.portfolio.positions:
            print("\nCurrent Positions:")
            print("-" * 70)
            for pos in self.portfolio.positions.values():
                print(f"{pos.ticker:6} | {pos.shares:4} shares @ ${pos.avg_cost:7.2f} | "
                      f"Current: ${pos.current_price:7.2f} | "
                      f"P&L: ${pos.unrealized_pnl:+8.2f} ({pos.unrealized_pnl_pct:+6.2f}%)")
            print("-" * 70)
