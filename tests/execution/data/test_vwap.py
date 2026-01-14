
import unittest
from backend.execution.data.vwap import ArrivalVWAP

class TestArrivalVWAP(unittest.TestCase):
    def setUp(self):
        self.vwap = ArrivalVWAP()

    def test_initial_state(self):
        self.assertEqual(self.vwap.total_volume, 0)
        self.assertEqual(self.vwap.total_turnover, 0.0)
        self.assertIsNone(self.vwap.get_vwap())

    def test_vwap_calculation(self):
        # Trade 1: 100 shares @ $10
        self.vwap.update(price=10.0, volume=100)
        # VWAP = (100 * 10) / 100 = 10.0
        self.assertEqual(self.vwap.get_vwap(), 10.0)

        # Trade 2: 200 shares @ $20
        self.vwap.update(price=20.0, volume=200)
        # Total Volume = 300
        # Total Turnover = 1000 + 4000 = 5000
        # VWAP = 5000 / 300 = 16.66...
        self.assertAlmostEqual(self.vwap.get_vwap(), 16.66666667)

    def test_reset(self):
        self.vwap.update(10.0, 100)
        self.vwap.reset()
        self.assertEqual(self.vwap.total_volume, 0)
        self.assertIsNone(self.vwap.get_vwap())

if __name__ == '__main__':
    unittest.main()
