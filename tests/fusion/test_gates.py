
import unittest
from backend.fusion.normalizer import BaseSignal
from backend.fusion.gates.liquidity import LiquidityGate
from backend.fusion.gates.event_priority import EventPriorityGate

class TestLogicGates(unittest.TestCase):
    
    def test_liquidity_gate(self):
        gate = LiquidityGate(min_volume=1000)
        
        # Scenario 1: High Volume -> Signal Passes
        signal = BaseSignal("CHART", 0.8, 0.9)
        market_state = {"volume": 5000}
        
        processed = gate.process(signal, market_state)
        # Should be unchanged or roughly same weight
        self.assertIsNotNone(processed)
        self.assertEqual(processed.score, 0.8)

        # Scenario 2: Low Volume -> Signal Blocked or Dampened
        low_vol_state = {"volume": 500}
        processed_low = gate.process(signal, low_vol_state)
        
        # Either return None (block) or 0 score/confidence
        if processed_low:
             self.assertEqual(processed_low.confidence, 0.0)
        else:
             self.assertIsNone(processed_low)

    def test_event_priority_gate(self):
        gate = EventPriorityGate(news_impact_threshold=0.8)
        
        # Scenario: Breaking News (Impact 1.0)
        # Chart signal should be dampened
        chart_signal = BaseSignal("CHART", 0.5, 0.8)
        gnn_signal = BaseSignal("NEWS", 1.0, 0.9) # Strong news
        
        signals = [chart_signal, gnn_signal]
        
        processed_signals = gate.process_batch(signals)
        
        # Check Chart Signal Confidence
        chart_processed = next(s for s in processed_signals if s.source == "CHART")
        # Should be dampened (e.g., * 0.5)
        self.assertLess(chart_processed.confidence, 0.8)
        
        # News Signal should stay high
        news_processed = next(s for s in processed_signals if s.source == "NEWS")
        self.assertEqual(news_processed.confidence, 0.9)

if __name__ == '__main__':
    unittest.main()
