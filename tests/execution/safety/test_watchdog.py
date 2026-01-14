
import unittest
from backend.execution.safety.watchdog import ExecutionWatchdog

class TestExecutionWatchdog(unittest.TestCase):
    def setUp(self):
        self.watchdog = ExecutionWatchdog(
            max_price_deviation=0.01, # 1%
            min_fill_rate_threshold=0.1, # 10% fill required at 90% time
            max_error_count=3
        )

    def test_normal_check(self):
        # Normal case
        self.assertTrue(self.watchdog.check(
            current_price=100.0,
            arrival_vwap=100.0,
            elapsed_time_ratio=0.5,
            fill_rate=0.5
        ))
        
    def test_price_deviation(self):
        # Price surged 2% above VWAP -> Danger
        self.assertFalse(self.watchdog.check(
            current_price=102.0,
            arrival_vwap=100.0,
            elapsed_time_ratio=0.5,
            fill_rate=0.5
        ))
        self.assertEqual(self.watchdog.last_trigger_reason, "PRICE_DEVIATION")
        
    def test_time_mismatch(self):
        # Time 95% passed, but only 5% filled -> Too slow execution
        self.assertFalse(self.watchdog.check(
            current_price=100.0,
            arrival_vwap=100.0,
            elapsed_time_ratio=0.95,
            fill_rate=0.05
        ))
        self.assertEqual(self.watchdog.last_trigger_reason, "TIME_FILL_MISMATCH")
        
    def test_error_count(self):
        # Errors occurred
        self.watchdog.report_error()
        self.watchdog.report_error()
        self.assertTrue(self.watchdog.check(100, 100, 0.5, 0.5))
        
        # 3rd error -> Trigger
        self.watchdog.report_error()
        self.assertFalse(self.watchdog.check(100, 100, 0.5, 0.5))
        self.assertEqual(self.watchdog.last_trigger_reason, "TOO_MANY_ERRORS")

if __name__ == '__main__':
    unittest.main()
