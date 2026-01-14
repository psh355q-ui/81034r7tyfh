
import unittest
from unittest.mock import MagicMock
import numpy as np
from backend.execution.rl.env import ExecutionEnv

class TestExecutionEnv(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_tick_flow = MagicMock()
        self.mock_vwap = MagicMock()
        
        # Setup mock behavior
        self.mock_tick_flow.get_flow.return_value = 1000.0  # Positive flow
        self.mock_vwap.get_vwap.return_value = 100.0        # Arrival VWAP
        
        # Environment Config
        self.config = {
            "total_shares": 1000,
            "max_duration_seconds": 1800, # 30 mins
            "initial_price": 100.0
        }
        
        self.env = ExecutionEnv(
            config=self.config,
            tick_flow_source=self.mock_tick_flow,
            vwap_source=self.mock_vwap
        )

    def test_reset(self):
        obs, info = self.env.reset()
        
        # Check Observation Shape: [remaining_ratio, time_ratio, flow10, flow30]
        self.assertEqual(len(obs), 4)
        self.assertEqual(obs[0], 1.0) # Remaining 100%
        self.assertEqual(obs[1], 0.0) # Time 0%
        
        # Internal state reset
        self.assertEqual(self.env.remaining_shares, 1000)
        self.assertEqual(self.env.elapsed_seconds, 0)
        
    def test_step_hold(self):
        self.env.reset()
        
        # Action 0: HOLD
        obs, reward, terminated, truncated, info = self.env.step(0)
        
        # Only time passes
        self.assertEqual(self.env.remaining_shares, 1000)
        self.assertGreater(self.env.elapsed_seconds, 0)
        self.assertFalse(terminated)
        
    def test_step_aggressive_buy(self):
        self.env.reset()
        
        # Action 2: AGGRESSIVE_BUY (Assume fill at Ask)
        # We need to mock 'current market' behavior inside env or inject it
        # For this test, we assume Env simulates fills internally or uses a data feed
        # Let's assume Env has a simple internal simulation for MVP
        
        obs, reward, terminated, truncated, info = self.env.step(2)
        
        # Shares reduced
        self.assertLess(self.env.remaining_shares, 1000)
        
    def test_done_condition(self):
        self.env.reset()
        self.env.remaining_shares = 0 # Force done
        
        obs, reward, terminated, truncated, info = self.env.step(0)
        
        self.assertTrue(terminated)

if __name__ == '__main__':
    unittest.main()
