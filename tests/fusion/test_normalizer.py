
import unittest
from backend.fusion.normalizer import SignalNormalizer, BaseSignal

class TestSignalNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = SignalNormalizer()

    def test_base_signal_creation(self):
        sig = BaseSignal(source="NEWS", score=0.8, confidence=0.9)
        self.assertEqual(sig.source, "NEWS")
        self.assertEqual(sig.score, 0.8)
        self.assertEqual(sig.confidence, 0.9)

    def test_score_clipping(self):
        # Should clip to [-1.0, 1.0]
        self.assertEqual(self.normalizer.normalize_score(1.5), 1.0)
        self.assertEqual(self.normalizer.normalize_score(-2.0), -1.0)
        self.assertEqual(self.normalizer.normalize_score(0.5), 0.5)

    def test_confidence_clipping(self):
        # Should clip to [0.0, 1.0]
        self.assertEqual(self.normalizer.normalize_confidence(1.2), 1.0)
        self.assertEqual(self.normalizer.normalize_confidence(-0.1), 0.0)
        self.assertEqual(self.normalizer.normalize_confidence(0.8), 0.8)

    def test_create_signal_with_validation(self):
        # Auto-normalization during creation
        sig = self.normalizer.create_signal("CHART", score=2.0, confidence=1.5)
        self.assertEqual(sig.score, 1.0)
        self.assertEqual(sig.confidence, 1.0)

if __name__ == '__main__':
    unittest.main()
