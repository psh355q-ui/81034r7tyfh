"""
Live Portfolio - Real-time Portfolio Tracking

Tracks portfolio state in real-time for paper trading.

Features:
- Position tracking with live P&L
- Order execution simulation
- Transaction history
- Real-time portfolio valuation
- Performance metrics

Author: AI Trading System Team
Date: 2025-11-15
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Position:
    """Stock position."""
    ticker: str
    shares: int
    avg_cost: float
    current_price: float
    last_update: datetime

    @property
    def market_value(self) -> float:
        """Current market value."""
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost basis."""
        return self.shares * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L."""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class Order:
    """Trading order."""
    order_id: str
    ticker: str
    action: str  # BUY or SELL
    shares: int
    order_price: float
    filled_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    commission: float = 0.0
    slippage_bps: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "order_id": self.order_id,
            "ticker": self.ticker,
            "action": self.action,
            "shares": self.shares,
            "order_price": self.order_price,
            "filled_price": self.filled_price,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "commission": self.commission,
            "slippage_bps": self.slippage_bps,
        }


@dataclass
class Trade:
    """Completed trade record."""
    trade_id: str
    ticker: str
    action: str
    shares: int
    price: float
    commission: float
    timestamp: datetime

    @property
    def gross_amount(self) -> float:
        """Gross transaction amount."""
        return self.shares * self.price

    @property
    def net_amount(self) -> float:
        """Net transaction amount (including commission)."""
        return self.gross_amount + self.commission

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "trade_id": self.trade_id,
            "ticker": self.ticker,
            "action": self.action,
            "shares": self.shares,
            "price": self.price,
            "commission": self.commission,
            "gross_amount": self.gross_amount,
            "net_amount": self.net_amount,
            "timestamp": self.timestamp.isoformat(),
        }


class LivePortfolio:
    """
    Live portfolio tracker for paper trading.

    Features:
    - Position tracking
    - Order management
    - P&L calculation
    - Transaction history
    """

    def __init__(
        self,
        initial_cash: float,
        commission_rate: float = 0.001,  # 0.1%
        max_positions: int = 10,
    ):
        """
        Initialize live portfolio.

        Args:
            initial_cash: Initial cash balance
            commission_rate: Commission rate per trade
            max_positions: Maximum number of positions
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_rate = commission_rate
        self.max_positions = max_positions

        # Portfolio state
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

        # Stats
        self.total_commissions = 0.0
        self.realized_pnl = 0.0
        self.start_time = datetime.now()

        logger.info(f"Live Portfolio initialized with ${initial_cash:,.2f}")

    # ===== Order Management =====

    def create_order(
        self,
        ticker: str,
        action: str,
        shares: int,
        current_price: float,
    ) -> Optional[Order]:
        """
        Create a new order.

        Args:
            ticker: Stock ticker
            action: BUY or SELL
            shares: Number of shares
            current_price: Current market price

        Returns:
            Order object or None if rejected
        """
        # Validate action
        if action not in ["BUY", "SELL"]:
            logger.error(f"Invalid action: {action}")
            return None

        # Check if we can buy
        if action == "BUY":
            estimated_cost = shares * current_price * (1 + self.commission_rate)

            if estimated_cost > self.cash:
                logger.warning(f"Insufficient cash for {ticker}: need ${estimated_cost:.2f}, have ${self.cash:.2f}")
                return None

            if len(self.positions) >= self.max_positions and ticker not in self.positions:
                logger.warning(f"Max positions reached: {self.max_positions}")
                return None

        # Check if we can sell
        elif action == "SELL":
            if ticker not in self.positions:
                logger.warning(f"No position to sell: {ticker}")
                return None

            if self.positions[ticker].shares < shares:
                logger.warning(f"Insufficient shares to sell {ticker}: have {self.positions[ticker].shares}, trying to sell {shares}")
                return None

        # Create order
        order_id = f"{ticker}_{action}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        order = Order(
            order_id=order_id,
            ticker=ticker,
            action=action,
            shares=shares,
            order_price=current_price,
        )

        self.orders.append(order)
        logger.info(f"Created order: {action} {shares} {ticker} @ ${current_price:.2f}")

        return order

    def fill_order(
        self,
        order: Order,
        fill_price: float,
        slippage_bps: float = 0.0,
    ) -> bool:
        """
        Fill an order.

        Args:
            order: Order to fill
            fill_price: Actual fill price
            slippage_bps: Slippage in basis points

        Returns:
            True if successful
        """
        if order.status != OrderStatus.PENDING:
            logger.error(f"Order {order.order_id} is not pending")
            return False

        # Calculate commission
        gross_amount = order.shares * fill_price
        commission = gross_amount * self.commission_rate

        # Execute trade
        if order.action == "BUY":
            net_cost = gross_amount + commission

            if net_cost > self.cash:
                logger.error(f"Insufficient cash to fill order: need ${net_cost:.2f}, have ${self.cash:.2f}")
                order.status = OrderStatus.REJECTED
                return False

            # Update cash
            self.cash -= net_cost

            # Update position
            if order.ticker in self.positions:
                pos = self.positions[order.ticker]
                # Update average cost
                total_shares = pos.shares + order.shares
                total_cost = (pos.shares * pos.avg_cost) + (order.shares * fill_price)
                pos.avg_cost = total_cost / total_shares
                pos.shares = total_shares
                pos.current_price = fill_price
                pos.last_update = datetime.now()
            else:
                # Create new position
                self.positions[order.ticker] = Position(
                    ticker=order.ticker,
                    shares=order.shares,
                    avg_cost=fill_price,
                    current_price=fill_price,
                    last_update=datetime.now(),
                )

            logger.info(f"BOUGHT {order.shares} {order.ticker} @ ${fill_price:.2f} (cost: ${net_cost:.2f})")

        elif order.action == "SELL":
            if order.ticker not in self.positions:
                logger.error(f"No position to sell: {order.ticker}")
                order.status = OrderStatus.REJECTED
                return False

            pos = self.positions[order.ticker]

            if pos.shares < order.shares:
                logger.error(f"Insufficient shares: have {pos.shares}, trying to sell {order.shares}")
                order.status = OrderStatus.REJECTED
                return False

            # Calculate realized P&L
            proceeds = gross_amount - commission
            cost = order.shares * pos.avg_cost
            pnl = proceeds - cost

            # Update cash
            self.cash += proceeds

            # Update realized P&L
            self.realized_pnl += pnl

            # Update position
            pos.shares -= order.shares
            pos.current_price = fill_price
            pos.last_update = datetime.now()

            # Remove position if fully closed
            if pos.shares == 0:
                del self.positions[order.ticker]
                logger.info(f"Position CLOSED: {order.ticker} (P&L: ${pnl:+.2f})")
            else:
                logger.info(f"SOLD {order.shares} {order.ticker} @ ${fill_price:.2f} (P&L: ${pnl:+.2f})")

        # Update order
        order.filled_price = fill_price
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.now()
        order.commission = commission
        order.slippage_bps = slippage_bps

        # Record trade
        trade = Trade(
            trade_id=order.order_id,
            ticker=order.ticker,
            action=order.action,
            shares=order.shares,
            price=fill_price,
            commission=commission,
            timestamp=datetime.now(),
        )
        self.trades.append(trade)

        # Update stats
        self.total_commissions += commission

        return True

    # ===== Portfolio Queries =====

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.

        Args:
            prices: Dictionary mapping ticker to current price
        """
        for ticker, position in self.positions.items():
            if ticker in prices:
                position.current_price = prices[ticker]
                position.last_update = datetime.now()

    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for a ticker."""
        return self.positions.get(ticker)

    def get_total_value(self) -> float:
        """Get total portfolio value (cash + positions)."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.get_unrealized_pnl()

    def get_total_return_pct(self) -> float:
        """Get total return percentage."""
        if self.initial_cash == 0:
            return 0.0
        return ((self.get_total_value() - self.initial_cash) / self.initial_cash) * 100

    def get_exposure_pct(self) -> float:
        """Get portfolio exposure percentage (invested / total value)."""
        total_value = self.get_total_value()
        if total_value == 0:
            return 0.0
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return (positions_value / total_value) * 100

    # ===== Reporting =====

    def get_summary(self) -> Dict:
        """Get portfolio summary."""
        total_value = self.get_total_value()
        unrealized_pnl = self.get_unrealized_pnl()
        total_pnl = self.get_total_pnl()

        return {
            "cash": self.cash,
            "positions_count": len(self.positions),
            "positions_value": sum(pos.market_value for pos in self.positions.values()),
            "total_value": total_value,
            "initial_cash": self.initial_cash,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "total_return_pct": self.get_total_return_pct(),
            "exposure_pct": self.get_exposure_pct(),
            "total_trades": len(self.trades),
            "total_commissions": self.total_commissions,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
        }

    def get_positions_dict(self) -> List[Dict]:
        """Get all positions as list of dictionaries."""
        return [pos.to_dict() for pos in self.positions.values()]

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades."""
        recent = self.trades[-limit:] if len(self.trades) > limit else self.trades
        return [trade.to_dict() for trade in recent]

    def to_dict(self) -> Dict:
        """Convert entire portfolio state to dictionary."""
        return {
            "summary": self.get_summary(),
            "positions": self.get_positions_dict(),
            "recent_trades": self.get_recent_trades(),
        }
