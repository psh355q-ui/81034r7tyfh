
"""
Generate Daily Briefing Script
==============================
Runs the ReportOrchestrator to generate a comprehensive Daily Briefing markdown report.
"""
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.reporters.report_orchestrator import ReportOrchestrator

async def main():
    print("🚀 Starting Daily Briefing Generation...")
    
    orchestrator = ReportOrchestrator()
    
    try:
        report_path = await orchestrator.generate_daily_briefing()
        print(f"\n✅ Report Generated Successfully: {report_path}")
        
        # Read and print the report content
        with open(report_path, "r", encoding="utf-8") as f:
            print("\n--- Report Content ---")
            print(f.read())
            print("----------------------")
            
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")

if __name__ == "__main__":
    asyncio.run(main())
