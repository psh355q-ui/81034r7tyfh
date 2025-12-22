"""Test SEC CIK Mapper"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.data.sec_cik_mapper import SECCIKMapper


async def main():
    print("🧪 SEC CIK Mapper Test\n")

    # Use memory-only mode (no Redis)
    mapper = SECCIKMapper(use_redis=False)
    await mapper.initialize()

    try:
        # Test 1: CIK to Ticker
        print("=" * 60)
        print("Test 1: CIK to Ticker")
        print("=" * 60)

        test_cases = [
            ("0000320193", "AAPL", "Apple"),
            ("0000789019", "MSFT", "Microsoft"),
            ("0001018724", "AMZN", "Amazon"),
        ]

        for cik, expected_ticker, company_name in test_cases:
            ticker = await mapper.cik_to_ticker_symbol(cik)
            company = await mapper.get_company_info(cik)

            print(f"\nCIK: {cik}")
            print(f"  Expected: {expected_ticker}")
            print(f"  Got: {ticker}")
            print(f"  Match: {'✅' if ticker == expected_ticker else '❌'}")
            if company:
                print(f"  Company: {company.name}")

        # Test 2: Ticker to CIK
        print("\n" + "=" * 60)
        print("Test 2: Ticker to CIK")
        print("=" * 60)

        for expected_cik, ticker, _ in test_cases:
            cik = await mapper.ticker_to_cik_number(ticker)
            print(f"\nTicker: {ticker}")
            print(f"  Expected CIK: {expected_cik}")
            print(f"  Got CIK: {cik}")
            print(f"  Match: {'✅' if cik == expected_cik else '❌'}")

        # Stats
        print("\n" + "=" * 60)
        print("Mapper Statistics")
        print("=" * 60)
        stats = mapper.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n✅ All tests completed!")

    finally:
        await mapper.close()


if __name__ == "__main__":
    asyncio.run(main())
