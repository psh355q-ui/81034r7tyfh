
import unittest
from datetime import datetime, timedelta
from backend.execution.data.tick_flow import TickFlow

class TestTickFlow(unittest.TestCase):
    def setUp(self):
        self.tick_flow = TickFlow()
        self.now = datetime.now()

    def test_add_tick_and_calculate_flow(self):
        # 1. Add Buy Tick (Buyer Initiated) -> Flow + (100 * 10) = +1000
        self.tick_flow.add_tick(
            timestamp=self.now,
            price=100.0,
            volume=10,
            is_buy_initiated=True
        )
        
        # 2. Add Sell Tick (Seller Initiated) -> Flow - (100 * 5) = -500
        self.tick_flow.add_tick(
            timestamp=self.now + timedelta(seconds=1),
            price=100.0,
            volume=5,
            is_buy_initiated=False
        )

        # Net Flow = 1000 - 500 = 500
        flow_10s = self.tick_flow.get_flow(window_seconds=10, current_time=self.now + timedelta(seconds=2))
        self.assertEqual(flow_10s, 500)

    def test_window_sliding(self):
        # Tick A: 20 seconds ago (Buy 10) -> Should be ignored for 10s window
        self.tick_flow.add_tick(
            timestamp=self.now - timedelta(seconds=20),
            price=100.0,
            volume=10,
            is_buy_initiated=True
        )

        # Tick B: 5 seconds ago (Buy 5) -> Should be included
        self.tick_flow.add_tick(
            timestamp=self.now - timedelta(seconds=5),
            price=100.0,
            volume=5,
            is_buy_initiated=True
        )

        current_time = self.now
        
        # 10s Window: Only Tick B (5 * 100 = 500)
        flow_10s = self.tick_flow.get_flow(window_seconds=10, current_time=current_time)
        self.assertEqual(flow_10s, 500) # Volume 5 * Price 100 = 500

        # 30s Window: Tick A + Tick B (1000 + 500 = 1500)
        flow_30s = self.tick_flow.get_flow(window_seconds=30, current_time=current_time)
        self.assertEqual(flow_30s, 1500)

    def test_cleanup(self):
        # Add very old tick
        self.tick_flow.add_tick(
            timestamp=self.now - timedelta(seconds=100),
            price=100.0,
            volume=10,
            is_buy_initiated=True
        )
        
        # Add recent tick
        self.tick_flow.add_tick(
            timestamp=self.now,
            price=100.0,
            volume=10,
            is_buy_initiated=True
        )
        
        # Before cleanup (assuming default max_window is 60s or manually triggerable)
        # Using internal list check for white-box testing
        self.assertEqual(len(self.tick_flow.ticks), 2)
        
        # Call get_flow with implicit cleanup or explicit cleanup method
        # Here assuming get_flow triggers lazy cleanup or we check logic
        self.tick_flow.cleanup(current_time=self.now, max_age_seconds=60)
        
        self.assertEqual(len(self.tick_flow.ticks), 1)

if __name__ == '__main__':
    unittest.main()
