
import unittest
from backend.gnn.gate import KnowledgeGate

class TestKnowledgeGate(unittest.TestCase):
    def setUp(self):
        # Mock Data Sources
        self.sector_map = {
            "AAPL": "Technology",
            "NVDA": "Technology",
            "MSFT": "Technology",
            "XOM": "Energy"
        }
        
        # Mock Correlation Matrix (or fetcher function)
        self.correlation_map = {
            ("AAPL", "NVDA"): 0.8,
            ("AAPL", "XOM"): 0.1
        }
        
        self.gate = KnowledgeGate(sector_map=self.sector_map, corr_map=self.correlation_map)

    def test_sector_match(self):
        # Same sector -> Bonus? Or just pass?
        # Logic: If sector matches, boost or keep.
        # Let's say we keep 1.0
        weight = self.gate.apply_gate("AAPL", "NVDA", initial_weight=1.0)
        self.assertGreaterEqual(weight, 1.0)

    def test_correlation_filter(self):
        # Low correlation -> Block
        # AAPL-XOM corr is 0.1
        weight = self.gate.apply_gate("AAPL", "XOM", initial_weight=1.0)
        self.assertEqual(weight, 0.0)

    def test_unknown_ticker(self):
        # Unknown ticker -> Conservative approach (0.0 or 0.5?)
        # Let's verify spec says "Gate"
        weight = self.gate.apply_gate("AAPL", "UNKNOWN", initial_weight=1.0)
        self.assertEqual(weight, 0.0)

if __name__ == '__main__':
    unittest.main()
