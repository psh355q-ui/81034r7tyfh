"""
Smart Order Execution Algorithms (Phase 6)

MASTER_GUIDE.md (Section 3.5) based implementation:
- TWAP (Time-Weighted Average Price): Uniform distribution over time
- VWAP (Volume-Weighted Average Price): Distribution based on historical volume profile
- Liquidity-Aware: Adjust slice size based on real-time market depth

This code does NOT use AI APIs (zero cost).
"""

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


class Fill:
    """Represents an executed order fill."""

    def __init__(
        self,
        timestamp: datetime,
        ticker: str,
        quantity: float,
        fill_price: float,
        commission: float = 0.0,
    ):
        self.timestamp = timestamp
        self.ticker = ticker
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.cost = abs(quantity * fill_price) + commission

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "ticker": self.ticker,
            "quantity": self.quantity,
            "fill_price": self.fill_price,
            "commission": self.commission,
            "cost": self.cost,
        }


# =============================================================================
# BROKER API ABSTRACTION
# =============================================================================


class BrokerAPI(ABC):
    """
    Abstract broker API interface.
    Implement this for specific brokers (KIS, IB, etc.)
    """

    @abstractmethod
    async def place_order(
        self,
        ticker: str,
        quantity: float,
        order_type: str = "MKT",
        limit_price: Optional[float] = None,
    ) -> Fill:
        """
        Place an order and return fill information.

        Args:
            ticker: Stock symbol
            quantity: Number of shares (positive=buy, negative=sell)
            order_type: 'MKT' (market) or 'LMT' (limit)
            limit_price: Price for limit orders

        Returns:
            Fill object with execution details
        """
        pass

    @abstractmethod
    async def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current market price for ticker."""
        pass

    @abstractmethod
    async def get_historical_volume_profile(
        self, ticker: str, days: int = 5
    ) -> pd.Series:
        """
        Get historical volume profile (minute-level).

        Returns:
            pd.Series indexed by time of day (09:00 - 15:30)
        """
        pass


class SimulatedBroker(BrokerAPI):
    """
    Simulated broker for testing (Phase 4-5).
    Will be replaced with real broker API in Phase 6.
    """

    def __init__(self, commission_rate: float = 0.00015):
        self.commission_rate = commission_rate
        logger.info("SimulatedBroker initialized (testing mode)")

    async def place_order(
        self,
        ticker: str,
        quantity: float,
        order_type: str = "MKT",
        limit_price: Optional[float] = None,
    ) -> Fill:
        """Simulate order execution."""
        # Simulate random slippage (±0.1%)
        base_price = limit_price or 100.0  # Fake price
        slippage = base_price * np.random.uniform(-0.001, 0.001)
        fill_price = base_price + slippage

        commission = abs(quantity * fill_price) * self.commission_rate

        logger.debug(
            f"[SimBroker] FILL: {order_type} {quantity} {ticker} @ ${fill_price:.2f}"
        )

        return Fill(
            timestamp=datetime.now(),
            ticker=ticker,
            quantity=quantity,
            fill_price=fill_price,
            commission=commission,
        )

    async def get_current_price(self, ticker: str) -> Optional[float]:
        """Return simulated price."""
        return 100.0 + np.random.randn() * 5.0

    async def get_historical_volume_profile(
        self, ticker: str, days: int = 5
    ) -> pd.Series:
        """
        Return simulated U-shaped volume profile.
        (High at open/close, low midday)
        """
        times = pd.date_range("09:00", "15:30", freq="1min").time
        profile = np.ones(len(times))

        # Heavy volume at open (first 30 min)
        profile[:30] = 5.0
        # Heavy volume at close (last 30 min)
        profile[-30:] = 7.0

        # Normalize
        profile = profile / profile.sum()

        return pd.Series(profile, index=times)


# =============================================================================
# ABSTRACT EXECUTOR
# =============================================================================


class OrderExecutor(ABC):
    """
    Base class for order execution algorithms.
    """

    def __init__(self, broker: BrokerAPI):
        self.broker = broker
        self.fills: List[Fill] = []

    @abstractmethod
    async def execute(
        self,
        ticker: str,
        total_quantity: float,
        **kwargs,
    ) -> List[Fill]:
        """
        Execute order using specific algorithm.

        Args:
            ticker: Stock symbol
            total_quantity: Total shares to trade
            **kwargs: Algorithm-specific parameters

        Returns:
            List of Fill objects
        """
        pass

    def get_execution_summary(self) -> dict:
        """Calculate execution statistics."""
        if not self.fills:
            return {"error": "No fills executed"}

        total_qty = sum(f.quantity for f in self.fills)
        total_cost = sum(f.cost for f in self.fills)
        total_commission = sum(f.commission for f in self.fills)

        avg_price = (total_cost - total_commission) / total_qty if total_qty != 0 else 0

        return {
            "total_quantity": total_qty,
            "avg_fill_price": avg_price,
            "total_commission": total_commission,
            "num_slices": len(self.fills),
            "fills": [f.to_dict() for f in self.fills],
        }


# =============================================================================
# TWAP EXECUTOR
# =============================================================================


class TWAPExecutor(OrderExecutor):
    """
    Time-Weighted Average Price executor.

    Distributes order uniformly over time period.
    Best for: Consistent execution without information leakage.
    """

    async def execute(
        self,
        ticker: str,
        total_quantity: float,
        duration_minutes: int = 30,
        slice_interval_seconds: int = 60,
    ) -> List[Fill]:
        """
        Execute TWAP order.

        Args:
            ticker: Stock symbol
            total_quantity: Total shares to trade
            duration_minutes: Total execution time in minutes
            slice_interval_seconds: Time between each slice (default: 60s)

        Returns:
            List of fills
        """
        logger.info(
            f"[TWAP] Starting: {ticker} {total_quantity} shares over {duration_minutes}min"
        )

        # 1. Calculate number of slices
        num_slices = max(1, (duration_minutes * 60) // slice_interval_seconds)

        # 2. Calculate quantity per slice
        base_qty = total_quantity // num_slices
        remainder = total_quantity % num_slices

        quantities = [base_qty] * num_slices

        # Distribute remainder to first N slices
        for i in range(int(abs(remainder))):
            quantities[i] += 1 if total_quantity > 0 else -1

        # Remove zero quantities
        quantities = [q for q in quantities if q != 0]

        logger.info(
            f"[TWAP] Plan: {len(quantities)} slices, avg {total_quantity/len(quantities):.2f} per slice"
        )

        # 3. Execute slices
        for i, qty in enumerate(quantities):
            try:
                fill = await self.broker.place_order(ticker, qty, order_type="MKT")
                self.fills.append(fill)

                logger.info(
                    f"[TWAP] Slice {i+1}/{len(quantities)}: {qty} @ ${fill.fill_price:.2f}"
                )

                # Wait for next slice (except after last one)
                if i < len(quantities) - 1:
                    await asyncio.sleep(slice_interval_seconds)

            except Exception as e:
                logger.error(f"[TWAP] Error on slice {i+1}: {e}")
                break

        # 4. Summary
        summary = self.get_execution_summary()
        logger.info(
            f"[TWAP] Completed: {summary['total_quantity']} @ avg ${summary['avg_fill_price']:.2f}"
        )

        return self.fills


# =============================================================================
# VWAP EXECUTOR
# =============================================================================


class VWAPExecutor(OrderExecutor):
    """
    Volume-Weighted Average Price executor.

    Distributes order proportionally to historical volume profile.
    Best for: Minimizing market impact by trading with natural flow.
    """

    async def execute(
        self,
        ticker: str,
        total_quantity: float,
        start_time_str: str = "09:00",
        end_time_str: str = "15:30",
        slice_interval_seconds: int = 60,
        volume_profile_days: int = 5,
    ) -> List[Fill]:
        """
        Execute VWAP order.

        Args:
            ticker: Stock symbol
            total_quantity: Total shares to trade
            start_time_str: Start time (HH:MM)
            end_time_str: End time (HH:MM)
            slice_interval_seconds: Time between slices
            volume_profile_days: Historical days for volume profile

        Returns:
            List of fills
        """
        logger.info(
            f"[VWAP] Starting: {ticker} {total_quantity} shares from {start_time_str} to {end_time_str}"
        )

        # 1. Get historical volume profile
        try:
            profile = await self.broker.get_historical_volume_profile(
                ticker, days=volume_profile_days
            )
        except Exception as e:
            logger.error(f"[VWAP] Failed to get volume profile: {e}")
            return []

        # 2. Slice profile to execution window
        start_time = time.fromisoformat(start_time_str)
        end_time = time.fromisoformat(end_time_str)

        # Filter profile to execution window
        execution_profile = profile.loc[start_time:end_time]

        if execution_profile.empty:
            logger.error("[VWAP] No volume data for specified time range")
            return []

        # 3. Calculate quantities proportional to volume
        total_volume = execution_profile.sum()
        quantities = (execution_profile / total_volume) * total_quantity

        # Convert to integers (maintaining total)
        quantities_int = np.floor(quantities.abs()) * np.sign(total_quantity)
        remainder = total_quantity - quantities_int.sum()

        # Distribute remainder to largest slices
        if remainder != 0:
            top_indices = quantities.abs().nlargest(int(abs(remainder))).index
            for idx in top_indices:
                quantities_int[idx] += 1 if total_quantity > 0 else -1

        # Remove zero quantities
        quantities_int = quantities_int[quantities_int != 0]

        logger.info(
            f"[VWAP] Plan: {len(quantities_int)} slices based on {volume_profile_days}-day profile"
        )

        # 4. Execute slices at scheduled times
        current_time = datetime.now().time()

        for slice_time, qty in quantities_int.items():
            # Wait until slice time if needed
            if current_time < slice_time:
                wait_seconds = (
                    datetime.combine(datetime.today(), slice_time)
                    - datetime.combine(datetime.today(), current_time)
                ).total_seconds()

                if wait_seconds > 0:
                    logger.debug(
                        f"[VWAP] Waiting {wait_seconds:.0f}s for {slice_time}..."
                    )
                    await asyncio.sleep(wait_seconds)

            try:
                fill = await self.broker.place_order(ticker, qty, order_type="MKT")
                self.fills.append(fill)

                logger.info(
                    f"[VWAP] {slice_time}: {qty} @ ${fill.fill_price:.2f}"
                )

            except Exception as e:
                logger.error(f"[VWAP] Error at {slice_time}: {e}")
                break

            current_time = datetime.now().time()

            # Stop if past end time
            if current_time > end_time:
                logger.info("[VWAP] End time reached, stopping")
                break

        # 5. Summary
        summary = self.get_execution_summary()
        logger.info(
            f"[VWAP] Completed: {summary['total_quantity']} @ avg ${summary['avg_fill_price']:.2f}"
        )

        return self.fills


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def execute_twap(
    ticker: str,
    total_quantity: float,
    duration_minutes: int = 30,
    slice_interval_seconds: int = 60,
    broker: Optional[BrokerAPI] = None,
) -> List[Fill]:
    """
    Execute TWAP order (convenience function).

    Args:
        ticker: Stock symbol
        total_quantity: Total shares
        duration_minutes: Execution duration
        slice_interval_seconds: Time between slices
        broker: Custom broker (defaults to SimulatedBroker)

    Returns:
        List of fills
    """
    if broker is None:
        settings = get_settings()
        broker = SimulatedBroker(commission_rate=0.00015)

    executor = TWAPExecutor(broker)
    return await executor.execute(
        ticker=ticker,
        total_quantity=total_quantity,
        duration_minutes=duration_minutes,
        slice_interval_seconds=slice_interval_seconds,
    )


async def execute_vwap(
    ticker: str,
    total_quantity: float,
    start_time_str: str = "09:00",
    end_time_str: str = "15:30",
    slice_interval_seconds: int = 60,
    broker: Optional[BrokerAPI] = None,
) -> List[Fill]:
    """
    Execute VWAP order (convenience function).

    Args:
        ticker: Stock symbol
        total_quantity: Total shares
        start_time_str: Start time (HH:MM)
        end_time_str: End time (HH:MM)
        slice_interval_seconds: Time between slices
        broker: Custom broker (defaults to SimulatedBroker)

    Returns:
        List of fills
    """
    if broker is None:
        broker = SimulatedBroker(commission_rate=0.00015)

    executor = VWAPExecutor(broker)
    return await executor.execute(
        ticker=ticker,
        total_quantity=total_quantity,
        start_time_str=start_time_str,
        end_time_str=end_time_str,
        slice_interval_seconds=slice_interval_seconds,
    )


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    """
    Run demo when executed directly.
    """

    async def run_demo():
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

        broker = SimulatedBroker()

        # --- TWAP Demo ---
        logger.info("\n" + "=" * 60)
        logger.info("TWAP DEMO")
        logger.info("=" * 60)

        twap_executor = TWAPExecutor(broker)
        fills = await twap_executor.execute(
            ticker="AAPL",
            total_quantity=100,
            duration_minutes=5,
            slice_interval_seconds=60,
        )

        summary = twap_executor.get_execution_summary()
        logger.info(f"\nTWAP Summary: {summary}")

        # --- VWAP Demo ---
        logger.info("\n" + "=" * 60)
        logger.info("VWAP DEMO (Simulated)")
        logger.info("=" * 60)

        vwap_executor = VWAPExecutor(broker)
        # Note: In production, this should run during market hours
        # For demo, we'll skip the time waits
        logger.info("[VWAP] Demo would execute based on volume profile")
        logger.info("[VWAP] Requires market hours for real execution")

        logger.info("\n" + "=" * 60)
        logger.info("DEMO COMPLETE")
        logger.info("=" * 60)

    asyncio.run(run_demo())
