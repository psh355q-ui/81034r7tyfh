import asyncio
import logging
from backend.ai.reporters.annual_reporter import AnnualReporter

logging.basicConfig(level=logging.INFO)

async def main():
    print("============================================================")
    print("Annual Report Generator Verification")
    print("============================================================")
    
    reporter = AnnualReporter()
    
    try:
        report_path = await reporter.generate_annual_report(year=2026)
        print(f"\n✅ SUCCESS: Report generated at {report_path}")
        
        with open(report_path, 'r', encoding='utf-8') as f:
            print("\nPreview (First 15 lines):")
            print("-" * 30)
            print("".join(f.readlines()[:15]))
            print("-" * 30)
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
