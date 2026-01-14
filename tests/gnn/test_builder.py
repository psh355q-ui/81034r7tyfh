
import unittest
from backend.gnn.builder import NewsCooccurrenceBuilder

class TestNewsCooccurrenceBuilder(unittest.TestCase):
    def setUp(self):
        # Mock Ticker List
        self.known_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "AMD"]
        self.builder = NewsCooccurrenceBuilder(self.known_tickers)

    def test_single_mention(self):
        # Only one ticker -> No edge
        text = "Apple (AAPL) released new iPhone today."
        edges = self.builder.extract_edges(text)
        self.assertEqual(len(edges), 0)

    def test_double_mention(self):
        # Two tickers -> 1 edge
        text = "NVIDIA (NVDA) and AMD are competing in AI chip market."
        edges = self.builder.extract_edges(text)
        
        self.assertEqual(len(edges), 1)
        # Check edge content
        # We expect undirected edge logic, but usually represented as (A, B) and (B, A) or canonical (min, max)
        # Let's assume canonical set for now
        u, v, weight = edges[0]
        self.assertTrue((u == "NVDA" and v == "AMD") or (u == "AMD" and v == "NVDA"))
        self.assertEqual(weight, 1.0)

    def test_multi_mention(self):
        # Three tickers -> 3 edges (Triangle: A-B, B-C, A-C)
        text = "Big Tech rally: MSFT, NVDA, and TSLA all surged."
        edges = self.builder.extract_edges(text)
        
        # 3C2 = 3 edges
        self.assertEqual(len(edges), 3)

    def test_no_mention(self):
        text = "The market is volatile today."
        edges = self.builder.extract_edges(text)
        self.assertEqual(len(edges), 0)

if __name__ == '__main__':
    unittest.main()
