"""
Event-Driven Backtest Engine (Phase 4)

MASTER_GUIDE.md (Section 3.4, 5.6) based implementation:
- Event-driven simulation
- Slippage and commission modeling
- Performance metrics (Sharpe, MDD, Win Rate)
- Constitution rules integration

This code does NOT use AI APIs (zero cost).
"""

import asyncio
import json
import logging
import math
import queue
from datetime import datetime
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT CLASSES
# =============================================================================


class Event:
    """Base class for all events."""

    @property
    def type(self) -> str:
        return self.__class__.__name__


class MarketEvent(Event):
    """
    Triggered when new market data (bar) arrives.
    Triggers: Strategy
    """

    def __init__(self, timestamp: datetime, data: Dict[str, pd.Series]):
        self.timestamp = timestamp
        self.data = data  # {'AAPL': pd.Series(...), 'MSFT': ...}


class SignalEvent(Event):
    """
    Triggered when strategy generates trading signal.
    Triggers: Portfolio
    """

    def __init__(
        self,
        timestamp: datetime,
        symbol: str,
        action: str,
        strength: float = 1.0,
        conviction: float = 0.0,
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.action = action  # 'BUY', 'SELL', 'EXIT'
        self.strength = strength
        self.conviction = conviction


class OrderEvent(Event):
    """
    Triggered when portfolio creates an order.
    Triggers: Broker
    """

    def __init__(
        self,
        timestamp: datetime,
        symbol: str,
        quantity: float,
        order_type: str = "MKT",
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.quantity = quantity  # Positive: buy, Negative: sell
        self.order_type = order_type


class FillEvent(Event):
    """
    Triggered when broker executes an order.
    Triggers: Portfolio (updates cash & positions)
    """

    def __init__(
        self,
        timestamp: datetime,
        symbol: str,
        quantity: float,
        fill_price: float,
        commission: float,
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.cost = abs(quantity * fill_price) + commission

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "fill_price": self.fill_price,
            "commission": self.commission,
            "cost": self.cost,
        }


# =============================================================================
# ABSTRACT COMPONENTS
# =============================================================================


class DataHandler:
    """
    Loads data and generates MarketEvents.
    Must be subclassed with specific data source (CSV, DB, etc.)
    """

    def __init__(self, event_queue: queue.Queue):
        self.event_queue = event_queue

    async def next(self) -> bool:
        """
        Add next MarketEvent to queue.
        Returns False when data stream ends.
        """
        raise NotImplementedError("Subclass must implement next()")

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol (for broker simulation)."""
        raise NotImplementedError("Subclass must implement get_latest_price()")

    def get_latest_data(self) -> Dict[str, pd.Series]:
        """Get latest market data for all symbols."""
        raise NotImplementedError("Subclass must implement get_latest_data()")


class Strategy:
    """
    Receives MarketEvents and generates SignalEvents.
    Subclass to implement specific strategy (Claude, ChatGPT, Gemini, etc.)
    """

    def __init__(self, event_queue: queue.Queue, data_handler: DataHandler):
        self.event_queue = event_queue
        self.data_handler = data_handler

    async def on_market(self, event: MarketEvent):
        """Called when MarketEvent occurs."""
        raise NotImplementedError("Subclass must implement on_market()")


# =============================================================================
# CONCRETE COMPONENTS
# =============================================================================


class Broker:
    """
    Simulated broker that executes orders.
    Applies slippage and commission.
    """

    def __init__(
        self,
        event_queue: queue.Queue,
        data_handler: DataHandler,
        commission_rate: float,
        slippage_bps: float,
    ):
        self.event_queue = event_queue
        self.data_handler = data_handler
        self.commission_rate = commission_rate  # e.g., 0.00015 (0.015%)
        self.slippage_bps = slippage_bps  # e.g., 1 (1bp = 0.01%)

    async def on_order(self, event: OrderEvent):
        """Process order and create fill event."""
        try:
            price = self.data_handler.get_latest_price(event.symbol)
        except AttributeError:
            logger.error(
                "DataHandler must implement 'get_latest_price(symbol)' method"
            )
            return

        if price is None:
            logger.warning(
                f"[{event.timestamp}] No price data for {event.symbol}, skipping order"
            )
            return

        # 1. Simulate slippage
        slippage = (price * (self.slippage_bps / 10000.0)) * np.random.choice(
            [-1, 1]
        )
        fill_price = price + slippage

        # 2. Calculate commission
        cost = abs(event.quantity * fill_price)
        commission = cost * self.commission_rate

        # 3. Create fill event
        fill_event = FillEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            quantity=event.quantity,
            fill_price=fill_price,
            commission=commission,
        )
        self.event_queue.put(fill_event)


class Portfolio:
    """
    Manages positions based on SignalEvents (creates OrderEvents).
    Updates cash and positions based on FillEvents.
    Enforces Constitution rules.
    """

    def __init__(
        self,
        event_queue: queue.Queue,
        initial_capital: float,
        constitution_rules: Optional[dict] = None,
    ):
        self.event_queue = event_queue
        self.initial_capital = initial_capital

        # Constitution rules from config
        self.rules = constitution_rules or {}
        self.max_position_size_pct = self.rules.get("max_position_size_pct", 5.0)
        self.max_positions = self.rules.get("max_positions", 10)
        self.conviction_threshold_buy = self.rules.get("conviction_threshold_buy", 0.7)
        self.conviction_threshold_sell = self.rules.get(
            "conviction_threshold_sell", 0.6
        )

        # Portfolio state
        self.positions: Dict[str, float] = {}  # {'AAPL': 10.0, ...}
        self.cash: float = initial_capital

        # Performance tracking
        self.history: List[Dict] = []
        self.history.append(
            {
                "timestamp": None,
                "total_value": initial_capital,
                "cash": initial_capital,
                "positions": {},
            }
        )

        # Trade tracking for win rate calculation
        self.trades: List[Dict] = []  # Each trade with entry/exit

    def get_total_value(self, current_data: Dict[str, pd.Series]) -> float:
        """Calculate total portfolio value (cash + positions)."""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            if symbol in current_data and "close" in current_data[symbol]:
                total_value += quantity * current_data[symbol]["close"]
        return total_value

    def _check_constitution_rules(
        self,
        signal: SignalEvent,
        current_data: Dict[str, pd.Series],
    ) -> tuple[bool, str]:
        """
        Check if signal passes Constitution rules (pre-check filter).
        Returns (pass: bool, reason: str)
        """
        symbol = signal.symbol
        action = signal.action
        conviction = signal.conviction

        # Rule 1: Conviction threshold
        if action == "BUY" and conviction < self.conviction_threshold_buy:
            return False, f"Low conviction {conviction:.2%} < {self.conviction_threshold_buy:.2%}"

        if action == "SELL" and conviction < self.conviction_threshold_sell:
            return False, f"Low conviction {conviction:.2%} < {self.conviction_threshold_sell:.2%}"

        # Rule 2: Max positions
        if action == "BUY" and len(self.positions) >= self.max_positions:
            if symbol not in self.positions:
                return False, f"Max positions reached ({self.max_positions})"

        # Rule 3: Position size check (pre-check)
        if action == "BUY" and symbol in current_data:
            price = current_data[symbol].get("close", 0)
            if price > 0:
                max_position_value = self.initial_capital * (
                    self.max_position_size_pct / 100.0
                )
                # Check if we have enough capital
                if max_position_value > self.cash:
                    return False, f"Insufficient cash (need ${max_position_value:.2f}, have ${self.cash:.2f})"

        return True, "PASS"

    async def on_signal(
        self, event: SignalEvent, current_data: Dict[str, pd.Series]
    ):
        """
        Process signal and create order if Constitution rules pass.
        """
        symbol = event.symbol
        action = event.action

        if symbol not in current_data or "close" not in current_data[symbol]:
            logger.warning(f"[Portfolio] No data for {symbol}, skipping signal")
            return

        # Check Constitution rules
        passed, reason = self._check_constitution_rules(event, current_data)
        if not passed:
            logger.info(
                f"[{event.timestamp}] Signal rejected by Constitution: {reason}"
            )
            return

        current_price = current_data[symbol]["close"]
        current_holding = self.positions.get(symbol, 0.0)

        quantity = 0.0

        if action == "BUY" and current_holding == 0:
            # Calculate position size based on max_position_size_pct
            max_position_value = self.initial_capital * (
                self.max_position_size_pct / 100.0
            )
            quantity = math.floor(max_position_value / current_price)

            # Ensure we don't exceed available cash
            cost_estimate = quantity * current_price
            if cost_estimate > self.cash:
                quantity = math.floor(self.cash / current_price)

        elif action == "SELL" and current_holding > 0:
            quantity = -current_holding  # Sell all

        elif action == "EXIT":
            quantity = -current_holding  # Close position

        if quantity != 0:
            order = OrderEvent(
                timestamp=event.timestamp, symbol=symbol, quantity=quantity
            )
            self.event_queue.put(order)
            logger.info(
                f"[{event.timestamp}] Order created: {action} {abs(quantity)} {symbol}"
            )

    async def on_fill(self, event: FillEvent, current_data: Dict[str, pd.Series]):
        """
        Update portfolio after order execution.
        """
        # 1. Update cash
        if event.quantity > 0:  # Buy
            self.cash -= event.cost
        else:  # Sell
            self.cash += abs(event.quantity * event.fill_price) - event.commission

        # 2. Update positions
        current_quantity = self.positions.get(event.symbol, 0.0)
        new_quantity = current_quantity + event.quantity

        # Track trade for win rate calculation
        if current_quantity > 0 and new_quantity == 0:
            # Position closed - record trade
            # Find entry price from history
            entry_fill = None
            for hist in reversed(self.history):
                if "fill" in hist and hist.get("fill", {}).get("symbol") == event.symbol:
                    if hist.get("fill", {}).get("quantity", 0) > 0:
                        entry_fill = hist["fill"]
                        break

            if entry_fill:
                entry_price = entry_fill.get("fill_price", event.fill_price)
                pnl = (event.fill_price - entry_price) * current_quantity - event.commission
                self.trades.append(
                    {
                        "symbol": event.symbol,
                        "entry_price": entry_price,
                        "exit_price": event.fill_price,
                        "quantity": current_quantity,
                        "pnl": pnl,
                        "exit_timestamp": event.timestamp,
                    }
                )

        if new_quantity == 0:
            if event.symbol in self.positions:
                del self.positions[event.symbol]
        else:
            self.positions[event.symbol] = new_quantity

        # 3. Record history
        total_value = self.get_total_value(current_data)
        self.history.append(
            {
                "timestamp": event.timestamp,
                "total_value": total_value,
                "cash": self.cash,
                "positions": self.positions.copy(),
                "fill": event.to_dict(),
            }
        )

        logger.info(
            f"[{event.timestamp}] Fill executed: {event.quantity} {event.symbol} @ ${event.fill_price:.2f}, "
            f"Portfolio: ${total_value:.2f} (Cash: ${self.cash:.2f})"
        )


# =============================================================================
# MAIN ENGINE
# =============================================================================


class BacktestEngine:
    """
    Event-Driven Backtest Engine orchestrator.
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float,
        DataHandlerCls: type,
        StrategyCls: type,
        commission_rate: float = 0.00015,  # 0.015% (KRX standard)
        slippage_bps: float = 1.0,  # 1bp = 0.01%
        data_kwargs: Optional[dict] = None,
        strategy_kwargs: Optional[dict] = None,
        constitution_rules: Optional[dict] = None,
    ):
        self.event_queue = queue.Queue()
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        # Load Constitution rules from config if not provided
        if constitution_rules is None:
            settings = get_settings()
            constitution_rules = {
                "max_position_size_pct": settings.max_position_size_pct,
                "max_positions": settings.max_positions,
                "conviction_threshold_buy": settings.conviction_threshold_buy,
                "conviction_threshold_sell": settings.conviction_threshold_sell,
                "kill_switch_daily_loss_pct": settings.kill_switch_daily_loss_pct,
            }

        # Initialize components
        self.data_handler = DataHandlerCls(
            self.event_queue, **(data_kwargs or {})
        )
        self.strategy = StrategyCls(
            self.event_queue, self.data_handler, **(strategy_kwargs or {})
        )
        self.portfolio = Portfolio(
            self.event_queue, self.initial_capital, constitution_rules
        )
        self.broker = Broker(
            self.event_queue, self.data_handler, commission_rate, slippage_bps
        )

        logger.info(
            f"BacktestEngine initialized: {start_date} to {end_date}, "
            f"Capital: ${initial_capital:,.2f}"
        )

    async def run(self) -> Dict:
        """Execute event loop and return performance metrics."""
        logger.info(f"Backtest starting: {self.start_date} ~ {self.end_date}")

        event_count = 0
        while True:
            # 1. Get next market data
            if not await self.data_handler.next():
                logger.info("Data stream ended, terminating backtest")
                break

            # 2. Process event queue
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get(block=False)
                    event_count += 1
                except queue.Empty:
                    break

                # Get current market data for portfolio/broker
                current_data = self.data_handler.get_latest_data()

                if event.type == "MarketEvent":
                    logger.debug(f"[{event.timestamp}] MarketEvent")
                    await self.strategy.on_market(event)

                elif event.type == "SignalEvent":
                    logger.debug(
                        f"[{event.timestamp}] SignalEvent: {event.action} {event.symbol}"
                    )
                    await self.portfolio.on_signal(event, current_data)

                elif event.type == "OrderEvent":
                    logger.debug(
                        f"[{event.timestamp}] OrderEvent: {event.quantity} {event.symbol}"
                    )
                    await self.broker.on_order(event)

                elif event.type == "FillEvent":
                    logger.debug(
                        f"[{event.timestamp}] FillEvent: {event.quantity} {event.symbol} @ ${event.fill_price:.2f}"
                    )
                    await self.portfolio.on_fill(event, current_data)

        logger.info(f"Event loop complete. Processed {event_count} events.")
        return self.calculate_performance()

    def calculate_performance(self) -> Dict:
        """
        Calculate performance metrics:
        - Total Return
        - Sharpe Ratio (annualized)
        - Max Drawdown (MDD)
        - Win Rate
        - Number of trades
        """
        if len(self.portfolio.history) < 2:
            return {"error": "No trades executed or insufficient data"}

        history_df = pd.DataFrame(self.portfolio.history)
        history_df = history_df[history_df["timestamp"].notna()]

        if history_df.empty:
            return {"error": "No valid trade history"}

        history_df["returns"] = (
            history_df["total_value"].pct_change().fillna(0.0)
        )

        # 1. Total Return
        final_value = history_df["total_value"].iloc[-1]
        total_return = (final_value / self.initial_capital) - 1.0

        # 2. Sharpe Ratio (annualized, assuming 252 trading days)
        mean_return = history_df["returns"].mean()
        std_return = history_df["returns"].std()

        sharpe_ratio = 0.0
        if std_return > 0:
            sharpe_ratio = (mean_return / std_return) * math.sqrt(252)

        # 3. Max Drawdown
        cumulative_max = history_df["total_value"].cummax()
        drawdown = (history_df["total_value"] - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()

        # 4. Win Rate (from trades)
        win_rate = 0.0
        total_trades = len(self.portfolio.trades)
        if total_trades > 0:
            winning_trades = sum(1 for trade in self.portfolio.trades if trade["pnl"] > 0)
            win_rate = winning_trades / total_trades

        # 5. Total PnL
        total_pnl = sum(trade["pnl"] for trade in self.portfolio.trades)

        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return_pct": total_return * 100.0,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown * 100.0,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "constitution_rules": self.portfolio.rules,
        }


# =============================================================================
# DEMO IMPLEMENTATION (for testing)
# =============================================================================


class DemoDataHandler(DataHandler):
    """Demo data handler with synthetic price data."""

    def __init__(self, event_queue: queue.Queue, symbols: List[str] = None):
        super().__init__(event_queue)
        symbols = symbols or ["AAPL"]

        # Generate synthetic data
        dates = pd.date_range("2023-01-01", "2023-01-31")
        self.data = {}
        for symbol in symbols:
            prices = 100 + np.random.randn(len(dates)).cumsum()
            self.data[symbol] = pd.DataFrame(
                {
                    "close": prices,
                    "volume": np.random.randint(1000000, 10000000, len(dates)),
                },
                index=dates,
            )

        self.data_stream = iter(dates)
        self.latest_data = {}

    async def next(self) -> bool:
        try:
            timestamp = next(self.data_stream)
            self.latest_data = {
                symbol: self.data[symbol].loc[timestamp]
                for symbol in self.data.keys()
            }
            self.event_queue.put(MarketEvent(timestamp, self.latest_data))
            return True
        except StopIteration:
            return False

    def get_latest_price(self, symbol: str) -> Optional[float]:
        if symbol in self.latest_data and "close" in self.latest_data[symbol]:
            return float(self.latest_data[symbol]["close"])
        return None

    def get_latest_data(self) -> Dict[str, pd.Series]:
        return self.latest_data


class DemoStrategy(Strategy):
    """Demo strategy: simple moving average crossover."""

    def __init__(
        self,
        event_queue: queue.Queue,
        data_handler: DataHandler,
        window: int = 3,
    ):
        super().__init__(event_queue, data_handler)
        self.window = window
        self.prices = {symbol: [] for symbol in ["AAPL"]}

    async def on_market(self, event: MarketEvent):
        for symbol, data in event.data.items():
            price = data["close"]
            self.prices[symbol].append(price)

            if len(self.prices[symbol]) > self.window:
                ma = np.mean(self.prices[symbol][-self.window :])

                # Simple crossover logic
                if price > ma * 1.02:  # 2% above MA
                    signal = SignalEvent(
                        timestamp=event.timestamp,
                        symbol=symbol,
                        action="BUY",
                        conviction=0.75,
                    )
                    self.event_queue.put(signal)

                elif price < ma * 0.98:  # 2% below MA
                    signal = SignalEvent(
                        timestamp=event.timestamp,
                        symbol=symbol,
                        action="SELL",
                        conviction=0.65,
                    )
                    self.event_queue.put(signal)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    """
    Run demo backtest when executed directly.
    """

    async def run_demo():
        # Setup logging
        logging.basicConfig(level=logging.INFO)

        engine = BacktestEngine(
            start_date="2023-01-01",
            end_date="2023-01-31",
            initial_capital=100000.0,
            DataHandlerCls=DemoDataHandler,
            StrategyCls=DemoStrategy,
            commission_rate=0.00015,  # 0.015%
            slippage_bps=1.0,  # 1bp
            data_kwargs={"symbols": ["AAPL"]},
            strategy_kwargs={"window": 3},
        )

        results = await engine.run()

        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(json.dumps(results, indent=2))
        print("=" * 60)

    asyncio.run(run_demo())
