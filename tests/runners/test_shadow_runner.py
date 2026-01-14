
import unittest
from unittest.mock import MagicMock, patch
import asyncio
from backend.runners.shadow_runner import ShadowRunner
from backend.fusion.engine import TradingIntent

class TestShadowRunner(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_gnn = MagicMock()
        self.mock_fusion = MagicMock()
        self.mock_rl = MagicMock()
        
        self.runner = ShadowRunner(
            gnn_builder=self.mock_gnn,
            fusion_engine=self.mock_fusion,
            rl_agent=self.mock_rl
        )

    def test_run_cycle_buy(self):
        # Scenario: Fusion says BUY
        intent = TradingIntent(
            ticker="AAPL",
            direction="BUY",
            score=0.8,
            confidence=0.9,
            rationale=["Good News"]
        )
        self.mock_fusion.fuse.return_value = intent
        
        # RL should be called for "Virtual Execution"
        self.mock_rl.predict.return_value = 1 # Passive Buy
        
        # Run sync wrapper for async method if needed, or just test logic if synchronous
        # Assuming async run_tick
        dataset = {"news": "...", "price": 100}
        
        result = asyncio.run(self.runner.run_tick("AAPL", dataset))
        
        self.assertEqual(result["status"], "SHADOW_FILLED")
        self.assertEqual(result["intent"], intent)
        # Verify RL was consulted
        self.mock_rl.predict.assert_called()

    def test_run_cycle_hold(self):
        # Scenario: Fusion says HOLD
        intent = TradingIntent("AAPL", "HOLD", 0.1, 0.5)
        self.mock_fusion.fuse.return_value = intent
        
        result = asyncio.run(self.runner.run_tick("AAPL", {}))
        
        self.assertEqual(result["status"], "SKIPPED")
        self.mock_rl.predict.assert_not_called()

if __name__ == '__main__':
    unittest.main()
