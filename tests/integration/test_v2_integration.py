
import unittest
import asyncio
from unittest.mock import MagicMock

# M1
from backend.execution.rl.agent import ExecutionAgent
from backend.execution.rl.env import ExecutionEnv

# M2
from backend.gnn.builder import NewsCooccurrenceBuilder
from backend.gnn.propagator import GraphPropagator

# M3
from backend.fusion.engine import FusionEngine, TradingIntent
from backend.fusion.normalizer import SignalNormalizer

# M4
from backend.runners.shadow_runner import ShadowRunner

class TestV2SystemIntegration(unittest.TestCase):
    def setUp(self):
        # 1. Initialize Components
        self.known_tickers = ["AAPL", "NVDA", "TSLA"]
        self.gnn_builder = NewsCooccurrenceBuilder(self.known_tickers)
        self.propagator = GraphPropagator()
        
        self.fusion_engine = FusionEngine() # Contains default gates
        
        # Mocking Env for Agent (since we don't need real RL training here)
        self.mock_env = MagicMock()
        self.mock_env.observation_space.shape = (4,)
        self.mock_env.action_space.n = 3
        
        self.rl_agent = ExecutionAgent(env=self.mock_env)
        # Force mock model to avoid loading file
        self.rl_agent.model = MagicMock()
        self.rl_agent.model.predict.return_value = (1, None) # Always Passive Buy
        
        self.shadow_runner = ShadowRunner(
            gnn_builder=self.gnn_builder,
            fusion_engine=self.fusion_engine,
            rl_agent=self.rl_agent
        )

    def test_full_cycle_buy_scenario(self):
        """
        Scenario:
        1. News: "NVDA and TSLA partnership announced." (Strong Co-occurrence)
        2. Market: High Volume (Pass Liquidity Gate)
        3. Expectation: 
           - Fusion Engine sees News + GNN impact
           - Intent is BUY
           - Shadow Runner executes trade
        """
        
        # 1. Simulate Data
        ticker = "NVDA"
        news_text = "NVDA and TSLA partnership announced. Major breakthrough."
        news_score = 0.9 # High positive sentiment
        
        market_data = {
            "price": 100.0,
            "volume": 50000, # Pass Liquidity Gate (min 10000)
            "news": news_text,
            "news_score": news_score,
            "price_score": 0.5 # Moderate technical score
        }
        
        # 2. Run Shadow Pipeline
        result = asyncio.run(self.shadow_runner.run_tick(ticker, market_data))
        
        # 3. Verification
        print(f"DEBUG: Pipeline Result: {result}")
        
        # Check Intent
        intent = result["intent"]
        self.assertIsInstance(intent, TradingIntent)
        self.assertEqual(intent.ticker, ticker)
        self.assertEqual(intent.direction, "BUY")
        self.assertGreater(intent.score, 0.5)
        
        # Check Execution (Shadow)
        self.assertEqual(result["status"], "SHADOW_FILLED")
        self.assertIsNotNone(result["execution"])
        self.assertEqual(result["execution"]["action"], 1) # Predicted action

    def test_liquidity_gate_blocking(self):
        """
        Scenario:
        1. Market: Very Low Volume
        2. Expectation: Gate blocks signal -> HOLD
        """
        ticker = "AAPL"
        market_data = {
            "price": 150.0,
            "volume": 100, # Fail Liquidity Gate
            "price_score": 0.9 # Strong technical buy
        }
        
        result = asyncio.run(self.shadow_runner.run_tick(ticker, market_data))
        
        intent = result["intent"]
        # Chart signal blocked -> Score 0 -> HOLD
        self.assertEqual(intent.direction, "HOLD")
        self.assertEqual(result["status"], "SKIPPED")

if __name__ == '__main__':
    unittest.main()
