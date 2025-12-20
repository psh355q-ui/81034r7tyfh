"""
Phase E Integration Test - Simplified Version

Phase E 핵심 기능 간단 테스트 (API 의존성 제거)

작성일: 2025-12-15
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio


async def test_all():
    print("\n" + "="*60)
    print("PHASE E INTEGRATION TEST - Simple Version")
    print("="*60 + "\n")
    
    results = []
    
    # Test 1: ETF Flow Tracker
    print("TEST 1: ETF Flow Tracker")
    try:
        from backend.data.collectors.etf_flow_tracker import ETFFlowTracker
        tracker = ETFFlowTracker()
        signal = await tracker.analyze_sector_rotation()
        print(f"✅ ETF Flow Tracker: {len(signal.hot_sectors)} hot sectors")
        results.append(("ETF Tracker", True))
    except Exception as e:
        print(f"❌ ETF Flow Tracker failed: {e}")
        results.append(("ETF Tracker", False))
    
    # Test 2: Economic Calendar  
    print("\nTEST 2: Economic Calendar")
    try:
        from backend.data.collectors.economic_calendar import EconomicCalendar
        calendar = EconomicCalendar()
        events = await calendar.get_upcoming_events(days=7)
        print(f"✅ Economic Calendar: {len(events)} events found")
        results.append(("Economic Calendar", True))
    except Exception as e:
        print(f"❌ Economic Calendar failed: {e}")
        results.append(("Economic Calendar", False))
    
    # Test 3: Smart Money Collector
    print("\nTEST 3: Smart Money Collector")
    try:
        from backend.data.collectors.smart_money_collector import SmartMoneyCollector
        collector = SmartMoneyCollector()
        signal = await collector.analyze_smart_money("AAPL")
        print(f"✅ Smart Money: {signal.signal_strength.value}")
        results.append(("Smart Money", True))
    except Exception as e:
        print(f"❌ Smart Money failed: {e}")
        results.append(("Smart Money", False))
    
    # Test 4: Institutional Agent
    print("\nTEST 4: Institutional Agent")
    try:
        # Direct import to avoid circular dependency with AIDebateEngine
        import sys
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "institutional_agent",
            "backend/ai/debate/institutional_agent.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["institutional_agent"] = module
        spec.loader.exec_module(module)
        
        agent = module.InstitutionalAgent()
        signal = await agent.analyze("AAPL")
        print(f"✅ Institutional Agent: {signal.action.value}")
        results.append(("Institutional Agent", True))
    except Exception as e:
        print(f"❌ Institutional Agent failed: {e}")
        results.append(("Institutional Agent", False))
    
    # Test 5: Macro Analyzer
    print("\nTEST 5: Macro Analyzer Agent")
    try:
        from backend.ai.macro.macro_analyzer_agent import MacroAnalyzerAgent
        agent = MacroAnalyzerAgent()
        analysis = await agent.analyze_market_regime()
        print(f"✅ Macro Analyzer: {analysis.regime.value} (Stock: {analysis.stock_allocation:.0%})")
        results.append(("Macro Analyzer", True))
    except Exception as e:
        print(f"❌ Macro Analyzer failed: {e}")
        results.append(("Macro Analyzer", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - PHASE E READY!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(test_all())
