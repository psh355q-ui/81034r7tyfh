import asyncio
import logging
from backend.ai.reporters.weekly_reporter import WeeklyReporter

logging.basicConfig(level=logging.INFO)

async def main():
    print("============================================================")
    print("Weekly Report Generator Verification")
    print("============================================================")
    
    reporter = WeeklyReporter()
    
    try:
        report_path = await reporter.generate_weekly_report()
        print(f"\n✅ SUCCESS: Report generated at {report_path}")
        
        with open(report_path, 'r', encoding='utf-8') as f:
            print("\nPreview (First 10 lines):")
            print("-" * 30)
            print("".join(f.readlines()[:10]))
            print("-" * 30)
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
