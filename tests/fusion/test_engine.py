
import unittest
from backend.fusion.engine import FusionEngine, TradingIntent
from backend.fusion.normalizer import BaseSignal

class TestFusionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FusionEngine()
        
    def test_weighted_sum(self):
        # Chart (0.5 score * 1.0 conf * 0.4 weight) = 0.2
        # News (1.0 score * 1.0 conf * 0.6 weight) = 0.6
        # Total Score = 0.2 + 0.6 = 0.8
        signals = [
            BaseSignal("CHART", 0.5, 1.0),
            BaseSignal("NEWS", 1.0, 1.0)
        ]
        weights = {"CHART": 0.4, "NEWS": 0.6}
        
        # Must provide volume > min_volume (default 10000) for Chart signal to pass LiquidityGate
        market_state = {"volume": 50000}
        
        intent = self.engine.fuse(signals, weights=weights, market_state=market_state)

        # NOTE: News Score 1.0 > Event Gate Threshold (0.8) -> Chart Confidence dampened (0.5x)
        # Chart: 0.5 * (1.0 * 0.5) * 0.4 = 0.1
        # News: 1.0 * 1.0 * 0.6 = 0.6
        # Total = 0.7
        self.assertAlmostEqual(intent.score, 0.7)
        self.assertEqual(intent.direction, "BUY")

    def test_gated_fusion(self):
        # Low volume -> Chart gate should zero out chart signal
        signals = [
            BaseSignal("CHART", 0.8, 1.0, metadata={"ticker": "AAPL"}),
        ]
        market_state = {"volume": 100} # Low volume
        
        # Engine should have default gates or we inject them
        # Assuming engine uses internal gates for this test integration
        intent = self.engine.fuse(signals, market_state=market_state)
        
        # Chart confidence becomes 0 -> Score 0
        self.assertEqual(intent.score, 0.0)
        self.assertEqual(intent.direction, "HOLD")

    def test_intent_structure(self):
        signals = [BaseSignal("CHART", -0.9, 1.0, metadata={"ticker": "TSLA"})]
        # Need volume for Liquidity Gate
        market_state = {"volume": 20000}
        intent = self.engine.fuse(signals, market_state=market_state)
        
        self.assertEqual(intent.ticker, "TSLA")
        self.assertEqual(intent.direction, "SELL") # Score < 0
        self.assertLess(intent.score, -0.5)

if __name__ == '__main__':
    unittest.main()
