"""
Live Trading Engine - Real Broker Integration

Connects AI Trading Agent decisions to real broker execution via KIS API.

Safety Features:
- Dry-run mode (log only, no execution)
- Position size limits
- Daily trade count limits
- Kill switch integration
- Confirmation prompts

Author: AI Trading System Team
Date: 2025-11-15
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Core components
from ai.trading_agent import TradingAgent
from brokers.kis_broker import KISBroker
from models.trading_decision import TradingDecision

# Optional components
try:
    from notifications import NotificationManager
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    NotificationManager = None

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading mode options."""
    DRY_RUN = "dry_run"  # Log decisions, no execution
    PAPER = "paper"  # Execute in virtual trading account
    LIVE = "live"  # Execute in real trading account


@dataclass
class LiveTradingConfig:
    """Live trading configuration."""

    # Broker settings
    kis_account_no: str
    kis_product_code: str = "01"
    mode: TradingMode = TradingMode.PAPER

    # Trading parameters
    tickers: List[str] = field(default_factory=lambda: ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"])
    decision_interval_seconds: int = 300  # 5 minutes between decisions
    max_positions: int = 10

    # Safety limits
    max_position_size_usd: float = 10000.0  # Max $10k per position
    max_daily_trades: int = 20
    max_daily_loss_pct: float = 2.0  # -2% daily loss triggers kill switch
    require_confirmation: bool = True  # Require manual confirmation for trades

    # Notifications
    enable_notifications: bool = True

    # Trading hours (US Eastern Time)
    trading_start_hour: int = 9  # 9:30 AM ET
    trading_end_hour: int = 16  # 4:00 PM ET


@dataclass
class TradingMetrics:
    """Trading session metrics."""
    session_start: datetime = field(default_factory=datetime.now)
    total_decisions: int = 0
    total_executions: int = 0
    buy_count: int = 0
    sell_count: int = 0
    hold_count: int = 0
    rejected_count: int = 0
    error_count: int = 0
    total_pnl: float = 0.0


class LiveTradingEngine:
    """
    Live trading engine with real broker integration.

    Features:
    - AI-driven decision making via TradingAgent
    - Real broker execution via KIS Broker
    - Multiple trading modes (Dry-run, Paper, Live)
    - Safety checks and confirmations
    - Kill switch integration
    - Telegram notifications
    """

    def __init__(self, config: LiveTradingConfig):
        """
        Initialize live trading engine.

        Args:
            config: Live trading configuration
        """
        self.config = config

        # Initialize AI Trading Agent
        self.agent = TradingAgent()
        logger.info("TradingAgent initialized")

        # Initialize KIS Broker
        is_virtual = (config.mode != TradingMode.LIVE)
        self.broker = KISBroker(
            account_no=config.kis_account_no,
            product_code=config.kis_product_code,
            is_virtual=is_virtual,
        )
        logger.info(f"KIS Broker initialized (mode: {config.mode.value})")

        # Initialize notifications
        self.notification_manager = None
        if config.enable_notifications and NOTIFICATIONS_AVAILABLE:
            try:
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
        self.kill_switch_active = False
        self.metrics = TradingMetrics()
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()

        # Track executed trades
        self.executed_trades: List[Dict] = []

        logger.info(f"LiveTradingEngine initialized - Mode: {config.mode.value}")
        logger.info(f"Tickers: {config.tickers}")
        logger.info(f"Decision interval: {config.decision_interval_seconds}s")

        # Rate limit warnings
        self._check_rate_limit_configuration()

    async def start(self):
        """
        Start the live trading engine.

        Runs continuously, making decisions at configured intervals.
        """
        self.running = True
        self.metrics.session_start = datetime.now()

        logger.info("=" * 80)
        logger.info("LIVE TRADING ENGINE STARTED")
        logger.info("=" * 80)
        logger.info(f"Mode: {self.config.mode.value.upper()}")
        logger.info(f"Account: {self.config.kis_account_no}")
        logger.info(f"Tickers: {', '.join(self.config.tickers)}")
        logger.info(f"Max Daily Trades: {self.config.max_daily_trades}")
        logger.info(f"Max Position Size: ${self.config.max_position_size_usd:,.2f}")
        logger.info(f"Kill Switch Threshold: -{self.config.max_daily_loss_pct}%")
        logger.info("=" * 80)

        # Send startup notification
        if self.notification_manager:
            try:
                await self.notification_manager.notifier.send_startup_message(
                    version="Live Trading Engine v1.0",
                    mode=self.config.mode.value.upper(),
                    initial_capital=self.config.max_position_size_usd * self.config.max_positions,
                    tickers=self.config.tickers,
                )
            except Exception as e:
                logger.warning(f"Failed to send startup notification: {e}")

        # Main trading loop
        try:
            while self.running:
                # Reset daily counters if new day
                self._check_daily_reset()

                # Check kill switch
                if self.kill_switch_active:
                    logger.warning("Kill switch is active - pausing trading")
                    await asyncio.sleep(60)
                    continue

                # Check trading hours
                if not self._is_market_hours():
                    logger.info("Outside trading hours - waiting")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue

                # Make decisions for each ticker
                for ticker in self.config.tickers:
                    try:
                        await self._process_ticker(ticker)
                    except Exception as e:
                        logger.error(f"Error processing {ticker}: {e}")
                        self.metrics.error_count += 1

                # Log session metrics
                self._log_metrics()

                # Wait for next decision cycle
                logger.info(f"Waiting {self.config.decision_interval_seconds}s until next decision cycle...")
                await asyncio.sleep(self.config.decision_interval_seconds)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt - shutting down gracefully")
        except Exception as e:
            logger.error(f"Fatal error in trading engine: {e}")
        finally:
            await self.stop()

    async def _process_ticker(self, ticker: str):
        """
        Process a single ticker: analyze → decide → execute.

        Args:
            ticker: Stock ticker symbol
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {ticker}")
        logger.info(f"{'='*60}")

        # Step 1: Get current market data
        try:
            price_data = self.broker.get_price(ticker)
            if not price_data:
                logger.warning(f"No price data for {ticker} - skipping")
                return

            current_price = price_data["current_price"]
            logger.info(f"Current price: ${current_price:.2f}")
        except Exception as e:
            logger.error(f"Failed to get price for {ticker}: {e}")
            return

        # Step 2: Get account balance
        try:
            balance = self.broker.get_account_balance()
            if not balance:
                logger.warning("Failed to get account balance")
                return

            logger.info(f"Account value: ${balance['total_value']:,.2f}")
            logger.info(f"Cash: ${balance.get('cash', 0):,.2f}")
            logger.info(f"Positions: {len(balance['positions'])}")
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return

        # Step 3: AI analysis and decision
        try:
            decision = await self.agent.analyze(
                ticker=ticker,
                market_context=None,  # Can add VIX, sector info, etc.
                portfolio_context=balance,
            )
            self.metrics.total_decisions += 1

            logger.info(f"\nDecision: {decision.action}")
            logger.info(f"Conviction: {decision.conviction:.2f}")
            logger.info(f"Position Size: {decision.position_size:.1f}%")
            logger.info(f"Reasoning: {decision.reasoning}")

            if decision.risk_factors:
                logger.info(f"Risk Factors: {', '.join(decision.risk_factors)}")

        except Exception as e:
            logger.error(f"AI analysis failed for {ticker}: {e}")
            self.metrics.error_count += 1
            return

        # Step 4: Update metrics
        if decision.action == "BUY":
            self.metrics.buy_count += 1
        elif decision.action == "SELL":
            self.metrics.sell_count += 1
        else:
            self.metrics.hold_count += 1

        # Step 5: Execute decision (if actionable)
        if decision.is_actionable:
            await self._execute_decision(decision, current_price, balance)
        else:
            logger.info(f"HOLD decision - no action taken")

    async def _execute_decision(
        self,
        decision: TradingDecision,
        current_price: float,
        balance: Dict,
    ):
        """
        Execute a trading decision.

        Args:
            decision: Trading decision from AI agent
            current_price: Current market price
            balance: Account balance information
        """
        # Safety check: daily trade limit
        if self.daily_trades >= self.config.max_daily_trades:
            logger.warning(f"Daily trade limit reached ({self.config.max_daily_trades}) - skipping execution")
            self.metrics.rejected_count += 1
            return

        # Calculate shares based on position size
        total_value = balance['total_value']
        position_value = (decision.position_size / 100.0) * total_value

        # Safety check: max position size
        if position_value > self.config.max_position_size_usd:
            logger.warning(
                f"Position size capped: ${position_value:,.2f} → ${self.config.max_position_size_usd:,.2f}"
            )
            position_value = self.config.max_position_size_usd

        shares = int(position_value / current_price)

        if shares <= 0:
            logger.warning("Calculated shares <= 0 - skipping execution")
            return

        logger.info(f"\n{'='*60}")
        logger.info(f"EXECUTION PLAN")
        logger.info(f"{'='*60}")
        logger.info(f"Action: {decision.action}")
        logger.info(f"Ticker: {decision.ticker}")
        logger.info(f"Shares: {shares}")
        logger.info(f"Price: ${current_price:.2f}")
        logger.info(f"Total Value: ${shares * current_price:,.2f}")
        logger.info(f"Conviction: {decision.conviction:.2f}")
        logger.info(f"Mode: {self.config.mode.value.upper()}")
        logger.info(f"{'='*60}")

        # Confirmation prompt (if enabled)
        if self.config.require_confirmation and self.config.mode == TradingMode.LIVE:
            confirmation = input("\nExecute this trade? (yes/no): ").strip().lower()
            if confirmation not in ["yes", "y"]:
                logger.info("Trade cancelled by user")
                self.metrics.rejected_count += 1
                return

        # Execute based on mode
        if self.config.mode == TradingMode.DRY_RUN:
            logger.info("[DRY RUN] Would have executed trade (no actual execution)")
            result = {"status": "DRY_RUN", "symbol": decision.ticker}
        else:
            # Execute via broker
            try:
                if decision.action == "BUY":
                    result = self.broker.buy_market_order(
                        symbol=decision.ticker,
                        quantity=shares,
                        exchange="NASDAQ",
                    )
                elif decision.action == "SELL":
                    result = self.broker.sell_market_order(
                        symbol=decision.ticker,
                        quantity=shares,
                        exchange="NASDAQ",
                    )
                else:
                    logger.error(f"Unknown action: {decision.action}")
                    return

                if result:
                    logger.info(f"OK: Order executed - {result['status']}")
                    self.metrics.total_executions += 1
                    self.daily_trades += 1

                    # Track execution
                    self.executed_trades.append({
                        "timestamp": datetime.now(),
                        "ticker": decision.ticker,
                        "action": decision.action,
                        "shares": shares,
                        "price": current_price,
                        "value": shares * current_price,
                        "conviction": decision.conviction,
                        "result": result,
                    })

                    # Send notification
                    if self.notification_manager:
                        try:
                            await self.notification_manager.notifier.send_execution_report(
                                ticker=decision.ticker,
                                side=decision.action,
                                quantity=shares,
                                avg_price=current_price,
                                total_value=shares * current_price,
                                algorithm=f"LIVE_{self.config.mode.value.upper()}",
                                slippage_bps=0.0,
                                commission=0.0,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send execution notification: {e}")
                else:
                    logger.error("Order execution failed")
                    self.metrics.error_count += 1

            except Exception as e:
                logger.error(f"Execution error: {e}")
                self.metrics.error_count += 1

    def _check_rate_limit_configuration(self):
        """
        Check configuration against KIS API rate limits and warn if suboptimal.

        Official KIS API Rate Limits:
        - Real Trading: 20 calls/second per account
        - Virtual Trading: 2 calls/second per account
        - Token Issuance: 1 call/second
        """
        is_virtual = (self.config.mode != TradingMode.LIVE)
        max_calls_per_second = 2.0 if is_virtual else 20.0

        # Each ticker needs: 1 price call + 1 balance call = 2 calls
        # Plus 1 execution call if actionable
        num_tickers = len(self.config.tickers)
        estimated_calls_per_cycle = num_tickers * 2 + num_tickers  # Worst case: all execute

        # Calculate minimum safe interval
        min_safe_interval = estimated_calls_per_cycle / max_calls_per_second

        logger.info("")
        logger.info("=" * 60)
        logger.info("KIS API RATE LIMIT CONFIGURATION CHECK")
        logger.info("=" * 60)
        logger.info(f"Trading Mode: {self.config.mode.value.upper()}")
        logger.info(f"Rate Limit: {max_calls_per_second} calls/second")
        logger.info(f"Tickers: {num_tickers}")
        logger.info(f"Estimated calls/cycle: {estimated_calls_per_cycle}")
        logger.info(f"Minimum safe interval: {min_safe_interval:.1f}s")
        logger.info(f"Configured interval: {self.config.decision_interval_seconds}s")

        # Check if configuration is safe
        if self.config.decision_interval_seconds < min_safe_interval:
            logger.warning("")
            logger.warning("WARNING: RATE LIMIT RISK DETECTED!")
            logger.warning(f"Current interval ({self.config.decision_interval_seconds}s) may cause rate limit errors")
            logger.warning(f"Recommended minimum: {min_safe_interval:.1f}s")
            logger.warning("")
            logger.warning("Suggestions:")
            logger.warning(f"  1. Increase --interval to {int(min_safe_interval) + 60}")
            logger.warning(f"  2. Reduce tickers to {int(max_calls_per_second / 3)}")
            logger.warning("  3. Use multiple KIS accounts (appkeys) for higher throughput")
            logger.warning("")
        else:
            logger.info("OK: Configuration is within rate limits")

        # Additional warnings for virtual trading
        if is_virtual and num_tickers > 2:
            logger.warning("")
            logger.warning("NOTICE: Virtual Trading has strict rate limits (2 calls/second)")
            logger.warning(f"With {num_tickers} tickers, consider:")
            logger.warning("  - Increasing decision_interval_seconds to 600+ (10 minutes)")
            logger.warning("  - Reducing tickers to 2 for smoother operation")
            logger.warning("")

        logger.info("=" * 60)
        logger.info("")

    def _check_daily_reset(self):
        """Reset daily counters if new day."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            logger.info(f"New day - resetting daily counters")
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = today

    def _is_market_hours(self) -> bool:
        """Check if within trading hours."""
        now = datetime.now()

        # Weekend check
        if now.weekday() >= 5:
            return False

        # Trading hours check (simplified - ignores timezone)
        hour = now.hour
        return self.config.trading_start_hour <= hour < self.config.trading_end_hour

    def _log_metrics(self):
        """Log current session metrics."""
        logger.info(f"\n{'='*60}")
        logger.info("SESSION METRICS")
        logger.info(f"{'='*60}")
        logger.info(f"Runtime: {datetime.now() - self.metrics.session_start}")
        logger.info(f"Total Decisions: {self.metrics.total_decisions}")
        logger.info(f"Total Executions: {self.metrics.total_executions}")
        logger.info(f"  BUY: {self.metrics.buy_count}")
        logger.info(f"  SELL: {self.metrics.sell_count}")
        logger.info(f"  HOLD: {self.metrics.hold_count}")
        logger.info(f"Rejected: {self.metrics.rejected_count}")
        logger.info(f"Errors: {self.metrics.error_count}")
        logger.info(f"Daily Trades: {self.daily_trades}/{self.config.max_daily_trades}")
        logger.info(f"{'='*60}\n")

    def activate_kill_switch(self, reason: str):
        """
        Activate emergency kill switch.

        Args:
            reason: Reason for activation
        """
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        self.kill_switch_active = True

        # Send alert notification
        if self.notification_manager:
            try:
                asyncio.create_task(
                    self.notification_manager.notifier.send_risk_alert(
                        alert_type="KILL_SWITCH",
                        severity="CRITICAL",
                        message=f"Trading halted: {reason}",
                        details={"daily_pnl": self.daily_pnl},
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send kill switch notification: {e}")

    def deactivate_kill_switch(self):
        """Deactivate kill switch."""
        logger.info("Kill switch deactivated - resuming trading")
        self.kill_switch_active = False

    async def stop(self):
        """Stop the trading engine gracefully."""
        self.running = False

        logger.info("\n" + "=" * 80)
        logger.info("LIVE TRADING ENGINE STOPPED")
        logger.info("=" * 80)

        # Final metrics
        self._log_metrics()

        # Log executed trades
        if self.executed_trades:
            logger.info("\nExecuted Trades:")
            for trade in self.executed_trades:
                logger.info(
                    f"  {trade['timestamp'].strftime('%H:%M:%S')} | "
                    f"{trade['action']:4s} {trade['shares']:3d} {trade['ticker']:5s} @ "
                    f"${trade['price']:.2f} = ${trade['value']:,.2f}"
                )

        logger.info("=" * 80)

    def get_metrics(self) -> Dict:
        """Get current metrics."""
        return {
            "session_start": self.metrics.session_start.isoformat(),
            "runtime_seconds": (datetime.now() - self.metrics.session_start).total_seconds(),
            "total_decisions": self.metrics.total_decisions,
            "total_executions": self.metrics.total_executions,
            "buy_count": self.metrics.buy_count,
            "sell_count": self.metrics.sell_count,
            "hold_count": self.metrics.hold_count,
            "rejected_count": self.metrics.rejected_count,
            "error_count": self.metrics.error_count,
            "daily_trades": self.daily_trades,
            "kill_switch_active": self.kill_switch_active,
            "executed_trades": len(self.executed_trades),
        }
