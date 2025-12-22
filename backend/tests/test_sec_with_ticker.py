"""Test SEC EDGAR Monitor with CIK Mapper Integration"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.data.crawlers.sec_edgar_monitor import SECEdgarMonitor


async def main():
    print("🧪 SEC EDGAR Monitor + CIK Mapper Test\n")

    async with SECEdgarMonitor(use_cik_mapper=True) as monitor:
        print("=" * 80)
        print("Collecting latest SEC 8-K filings...")
        print("=" * 80)

        # Collect latest filings
        filings = await monitor.collect(min_score=0)  # Get all to see ticker mapping

        print(f"\n✅ Collected {len(filings)} filings\n")

        # Show first 10 with ticker info
        print("=" * 80)
        print("First 10 Filings (with Ticker Mapping)")
        print("=" * 80)

        for i, filing in enumerate(filings[:10], 1):
            ticker_status = "✅" if filing.ticker else "❌"
            print(f"\n{i}. {filing.company_name}")
            print(f"   CIK: {filing.cik}")
            print(f"   Ticker: {ticker_status} {filing.ticker or 'NOT FOUND'}")
            print(f"   Impact: {filing.impact_category} ({filing.impact_score})")
            print(f"   Items: {', '.join(filing.items)}")

        # Statistics
        print("\n" + "=" * 80)
        print("Ticker Mapping Statistics")
        print("=" * 80)

        total = len(filings)
        with_ticker = sum(1 for f in filings if f.ticker)
        without_ticker = total - with_ticker

        print(f"  Total filings: {total}")
        print(f"  With ticker: {with_ticker} ({with_ticker/total*100:.1f}%)")
        print(f"  Without ticker: {without_ticker} ({without_ticker/total*100:.1f}%)")

        # Show some companies without tickers
        if without_ticker > 0:
            print(f"\n  Sample companies without tickers:")
            no_ticker_filings = [f for f in filings if not f.ticker][:5]
            for f in no_ticker_filings:
                print(f"    - {f.company_name} (CIK: {f.cik})")

        print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
