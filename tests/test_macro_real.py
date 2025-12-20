"""
Macro Analyzer 실전 데이터 테스트
FRED API를 사용한 실제 거시경제 지표 분석
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.ai.macro.macro_analyzer_agent import MacroAnalyzerAgent

async def test():
    print("=== Macro Analyzer Agent (Real Data) Test ===\n")
    
    agent = MacroAnalyzerAgent(weight=1.5)
    
    # 시장 체제 분석 (실제 데이터)
    analysis = await agent.analyze_market_regime()
    
    print(f"🌍 Market Regime: {analysis.regime.value.upper()}")
    print(f"💪 Strength: {analysis.strength.value}")
    print(f"📊 Stock Allocation: {analysis.stock_allocation:.0%}")
    print(f"🎯 Confidence: {analysis.confidence:.0%}")
    print()
    
    print("🔑 Key Signals:")
    for signal in analysis.key_signals:
        print(f"   {signal}")
    print()
    
    if analysis.warnings:
        print("⚠️  Warnings:")
        for warning in analysis.warnings:
            print(f"   - {warning}")
        print()
    
    print("📈 Analysis:")
    print(analysis.analysis)
    print()
    
    # 거래 지시
    directive = agent.get_trading_directive(analysis)
    print("🎯 Trading Directive:")
    for key, value in directive.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Macro Analyzer Agent (Real Data) test completed!")

asyncio.run(test())
