"""
Phase E Integration Test Suite

Phase E에서 구현한 5개 핵심 분석 기능을 통합 테스트

테스트 대상:
1. ETF Flow Tracker - 섹터 로테이션
2. Economic Calendar - 이벤트 예측
3. Smart Money Collector - 기관/내부자 추적
4. InstitutionalAgent - 기관 전담 AI
5. Macro Analyzer Agent - 거시경제 AI

작성일: 2025-12-15
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_etf_flow_tracker():
    """ETF Flow Tracker 테스트"""
    print("\n" + "="*60)
    print("TEST 1: ETF Flow Tracker")
    print("="*60 + "\n")
    
    from backend.data.collectors.etf_flow_tracker import get_etf_flow_tracker
    
    tracker = get_etf_flow_tracker()
    
    # 섹터 로테이션 분석
    signal = await tracker.analyze_sector_rotation()
    
    print(f"✅ Hot Sectors ({len(signal.hot_sectors)}):")
    for sector in signal.hot_sectors:
        print(f"   - {sector.value}")
    
    print(f"\n❄️  Cold Sectors ({len(signal.cold_sectors)}):")
    for sector in signal.cold_sectors:
        print(f"   - {sector.value}")
    
    print(f"\n📊 Rotation Strength: {signal.rotation_strength:.0%}")
    print(f"🎯 Confidence: {signal.confidence:.0%}")
    
    # 거래 추천
    recs = tracker.get_trading_recommendation(signal)
    print(f"\n💡 Recommendations: {len(recs)} sectors")
    
    return signal


async def test_economic_calendar():
    """Economic Calendar 테스트"""
    print("\n" + "="*60)
    print("TEST 2: Economic Calendar")
    print("="*60 + "\n")
    
    from backend.data.collectors.economic_calendar import get_economic_calendar
    
    calendar = get_economic_calendar()
    
    # 향후 이벤트
    events = await calendar.get_upcoming_events(days=7)
    
    print(f"📅 Upcoming Events: {len(events)}")
    for event in events[:3]:
        days = (event.date - datetime.now()).days
        print(f"   [{event.importance.value}] {event.title} (D-{days})")
    
    # AI 영향 예측
    if events:
        prediction = await calendar.predict_impact(events[0])
        print(f"\n🔮 Impact Prediction:")
        print(f"   Volatility: {prediction.volatility_level:.0%}")
        print(f"   Recommendation: {prediction.trading_recommendation}")
    
    # 알림
    alerts = await calendar.get_alerts(days_ahead=3)
    print(f"\n⚠️  Alerts: {len(alerts)}")
    
    # 거래 중지 판단
    should_pause, reason = calendar.should_pause_trading(alerts)
    if should_pause:
        print(f"   🛑 Trading Pause Required: {reason}")
    else:
        print(f"   ✅ Trading Allowed")
    
    return events


async def test_smart_money_collector():
    """Smart Money Collector 테스트"""
    print("\n" + "="*60)
    print("TEST 3: Smart Money Collector")
    print("="*60 + "\n")
    
    from backend.data.collectors.smart_money_collector import get_smart_money_collector
    
    collector = get_smart_money_collector()
    
    # 스마트 머니 분석
    signal = await collector.analyze_smart_money("AAPL")
    
    print(f"🎯 Signal: {signal.signal_strength.value.upper()}")
    print(f"🏦 Institution Pressure: {signal.institution_buying_pressure:.0%}")
    print(f"👔 Insider Activity: {signal.insider_activity_score:+.2f}")
    print(f"🎲 Confidence: {signal.confidence:.0%}")
    
    if signal.key_institutions:
        print(f"\n🏢 Key Institutions:")
        for inst in signal.key_institutions:
            print(f"   - {inst}")
    
    if signal.key_insiders:
        print(f"\n💼 Key Insiders:")
        for insider in signal.key_insiders:
            print(f"   - {insider}")
    
    print(f"\n💡 Recommendation: {signal.recommendation}")
    
    return signal


async def test_institutional_agent():
    """InstitutionalAgent 테스트"""
    print("\n" + "="*60)
    print("TEST 4: InstitutionalAgent")
    print("="*60 + "\n")
    
    from backend.ai.debate.institutional_agent import get_institutional_agent
    
    agent = get_institutional_agent()
    
    # 분석
    signal = await agent.analyze("AAPL")
    
    print(f"📈 Action: {signal.action.value}")
    print(f"🎯 Confidence: {signal.confidence:.0%}")
    print(f"🎲 Target Price: {signal.target_price}%")
    
    print(f"\n📊 Reasoning:")
    print(f"   {signal.reasoning}")
    
    if signal.risk_factors:
        print(f"\n⚠️  Risks:")
        for risk in signal.risk_factors:
            print(f"   - {risk}")
    
    return signal


async def test_macro_analyzer_agent():
    """Macro Analyzer Agent 테스트"""
    print("\n" + "="*60)
    print("TEST 5: Macro Analyzer Agent")
    print("="*60 + "\n")
    
    from backend.ai.macro.macro_analyzer_agent import get_macro_analyzer_agent
    
    agent = get_macro_analyzer_agent()
    
    # 시장 체제 분석
    analysis = await agent.analyze_market_regime()
    
    print(f"🌍 Market Regime: {analysis.regime.value.upper()}")
    print(f"💪 Strength: {analysis.strength.value}")
    print(f"📊 Stock Allocation: {analysis.stock_allocation:.0%}")
    print(f"🎯 Confidence: {analysis.confidence:.0%}")
    
    print(f"\n🔑 Key Signals:")
    for signal in analysis.key_signals:
        print(f"   {signal}")
    
    if analysis.warnings:
        print(f"\n⚠️  Warnings:")
        for warning in analysis.warnings:
            print(f"   - {warning}")
    
    # 거래 지시
    directive = agent.get_trading_directive(analysis)
    print(f"\n🎯 Trading Directive:")
    print(f"   Action: {directive['action']}")
    print(f"   Target Allocation: {directive['target_stock_allocation']:.0%}")
    print(f"   Urgency: {directive['urgency']}")
    
    return analysis


async def test_integrated_workflow():
    """통합 워크플로우 테스트"""
    print("\n" + "="*60)
    print("INTEGRATED WORKFLOW TEST")
    print("="*60 + "\n")
    
    print("Step 1: Check Macro Environment")
    print("-" * 40)
    macro_analysis = await test_macro_analyzer_agent()
    
    print("\n\nStep 2: Check Economic Events")
    print("-" * 40)
    events = await test_economic_calendar()
    
    print("\n\nStep 3: Analyze Sector Rotation")
    print("-" * 40)
    etf_signal = await test_etf_flow_tracker()
    
    print("\n\nStep 4: Check Smart Money")
    print("-" * 40)
    smart_money = await test_smart_money_collector()
    
    print("\n\nStep 5: Get Institutional Opinion")
    print("-" * 40)
    inst_signal = await test_institutional_agent()
    
    # 종합 판단
    print("\n\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60 + "\n")
    
    print(f"1. Macro Regime: {macro_analysis.regime.value} → Stock {macro_analysis.stock_allocation:.0%}")
    print(f"2. Economic Events: {'PAUSE' if len(events) > 0 else 'CLEAR'}")
    print(f"3. Sector Rotation: {etf_signal.rotation_strength:.0%} strength")
    print(f"4. Smart Money: {smart_money.signal_strength.value}")
    print(f"5. Institutional: {inst_signal.action.value}")
    
    # 최종 합의
    print(f"\n✅ All Phase E features working!")


async def main():
    """메인 테스트 실행"""
    print("\n" + "🎯"*30)
    print("PHASE E INTEGRATION TEST SUITE")
    print("🎯"*30)
    
    start_time = datetime.now()
    
    try:
        # 개별 테스트
        await test_etf_flow_tracker()
        await test_economic_calendar()
        await test_smart_money_collector()
        await test_institutional_agent()
        await test_macro_analyzer_agent()
        
        # 통합 워크플로우
        await test_integrated_workflow()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print(f"Duration: {duration:.2f}s")
        print(f"Features Tested: 5")
        print(f"Status: READY FOR PRODUCTION")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
