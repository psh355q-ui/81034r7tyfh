import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.reporters.weekly_reporter import WeeklyReporter
from backend.ai.reporters.monthly_reporter import MonthlyReporter
from backend.ai.reporters.quarterly_reporter import QuarterlyReporter
from backend.ai.reporters.annual_reporter import AnnualReporter
from dotenv import load_dotenv

# Load env for API keys
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_all_test_reports():
    print("\n" + "="*50)
    print("🚀 Generating Test Reports with New Prompts")
    print("="*50)

    # 1. Monthly Report (2026-01)
    logger.info("Generating Monthly Report for 2026-01...")
    monthly = MonthlyReporter()
    try:
        f_monthly = await monthly.generate_monthly_report(2026, 1)
        print(f"✅ Monthly Report Generated: {f_monthly}")
    except Exception as e:
        print(f"❌ Monthly Report Failed: {e}")

    # 2. Quarterly Report (2026-Q1)
    logger.info("Generating Quarterly Report for 2026-Q1...")
    quarterly = QuarterlyReporter()
    try:
        f_quarterly = await quarterly.generate_quarterly_report(2026, 1)
        print(f"✅ Quarterly Report Generated: {f_quarterly}")
    except Exception as e:
        print(f"❌ Quarterly Report Failed: {e}")

    # 3. Annual Report (2026)
    logger.info("Generating Annual Report for 2026...")
    annual = AnnualReporter()
    try:
        f_annual = await annual.generate_annual_report(2026)
        print(f"✅ Annual Report Generated: {f_annual}")
    except Exception as e:
        print(f"❌ Annual Report Failed: {e}")
        
    # 4. Weekly Report (Current Week)
    logger.info("Generating Weekly Report (Current)...")
    weekly = WeeklyReporter()
    try:
        f_weekly = await weekly.generate_weekly_report()
        print(f"✅ Weekly Report Generated: {f_weekly}")
    except Exception as e:
        print(f"❌ Weekly Report Failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(generate_all_test_reports())
    except KeyboardInterrupt:
        pass
