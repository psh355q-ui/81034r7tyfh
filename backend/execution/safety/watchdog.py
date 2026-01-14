"""
Execution Watchdog (Fail-safe)

Monitors the execution process and triggers a fallback mechanism 
if anomalies (Price Deviation, Time Mismatch, Errors) are detected.
"""

from typing import Optional

class ExecutionWatchdog:
    """
    Safety mechanism for Execution RL.
    """
    def __init__(
        self, 
        max_price_deviation: float = 0.02, # 2%
        min_fill_rate_threshold: float = 0.1, # Min fill rate at near end
        max_error_count: int = 5
    ):
        self.max_price_deviation = max_price_deviation
        self.min_fill_rate_threshold = min_fill_rate_threshold
        self.max_error_count = max_error_count
        
        self.error_count = 0
        self.last_trigger_reason: Optional[str] = None
        
    def report_error(self):
        """Report a system error (e.g., API failure)."""
        self.error_count += 1
        
    def reset(self):
        """Reset counters."""
        self.error_count = 0
        self.last_trigger_reason = None
        
    def check(
        self, 
        current_price: float, 
        arrival_vwap: float, 
        elapsed_time_ratio: float, 
        fill_rate: float
    ) -> bool:
        """
        Check safety conditions.
        Returns:
            True if Safe
            False if Unsafe (Trigger Fallback)
        """
        # 1. Error Count Check
        if self.error_count >= self.max_error_count:
            self.last_trigger_reason = "TOO_MANY_ERRORS"
            return False
            
        # 2. Price Deviation Check (Buying too expensive?)
        if arrival_vwap > 0:
            deviation = (current_price - arrival_vwap) / arrival_vwap
            if deviation > self.max_price_deviation:
                self.last_trigger_reason = "PRICE_DEVIATION"
                return False
                
        # 3. Time/Fill Mismatch (Too slow?)
        # If 90% time passed but less than 10% filled -> Panic
        if elapsed_time_ratio > 0.9 and fill_rate < self.min_fill_rate_threshold:
            self.last_trigger_reason = "TIME_FILL_MISMATCH"
            return False
            
        return True
