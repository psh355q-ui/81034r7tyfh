
import asyncio
import logging
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.market_scanner.massive_api_client import MassiveAPIClient, RateLimitConfig
from backend.services.market_scanner.filters.volume_filter import VolumeFilter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_scanner_fix():
    print("="*60)
    print("🔍 Market Scanner Optimization Verification")
    print("="*60)
    
    # 1. Verify Rate Limiter Timeout
    print("\n[1] Testing Rate Limiter Timeout...")
    client = MassiveAPIClient(rate_limit=RateLimitConfig(calls_per_minute=5, window_seconds=60))
    
    start_time = time.time()
    for i in range(1, 8):
        # We use a short timeout for test speed
        success = await client.rate_limiter.acquire(timeout=2.0)
        elapsed = time.time() - start_time
        status = "✅ Acquired" if success else "⚠️ Skipped (Timeout)"
        print(f"  Call {i}: {status} (Elapsed: {elapsed:.1f}s)")
        
        if not success:
            print("  -> Confirmed: Rate limiter correctly skipped instead of waiting indefinitely.")
            break
            
    if i == 8:
        print("  ❌ Failed: Rate limiter did not timeout as expected.")

    # 2. Verify $PARA (Delisted) Handling
    print("\n[2] Testing Delisted Ticker ($PARA)...")
    filter = VolumeFilter()
    
    # Capture stdout/stderr to check for noise
    # Note: yfinance writes to stderr via logging
    
    print("  Checking $PARA...")
    result = await filter.check("$PARA")
    
    print(f"  Result Reason: {result.reason}")
    print(f"  Passed: {result.passed}")
    
    if "상장폐지" in result.reason or "데이터 부족" in result.reason:
        print("  ✅ Confirmed: Correctly identified as data missing/delisted.")
    else:
        print(f"  ❌ Failed: Unexpected reason: {result.reason}")

    print("\n✅ Verification Complete")

if __name__ == "__main__":
    asyncio.run(verify_scanner_fix())
