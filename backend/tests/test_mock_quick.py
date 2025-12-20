
import sys
sys.path.insert(0, str(sys.path[0] + '/../'))

# Mock Gemini client for testing
class MockGeminiClient:
    def __init__(self):
        pass
    
    async def screen_risk(self, ticker, news_headlines, recent_events=None):
        # Simple mock: slightly different from rule-based
        import random
        base_score = 0.2 + random.random() * 0.3
        return {
            "ticker": ticker,
            "risk_score": base_score,
            "risk_level": "LOW" if base_score < 0.3 else "MODERATE",
            "categories": {
                "legal": base_score * 0.8,
                "regulatory": base_score * 1.2,
                "management": base_score,
                "operational": base_score * 0.9,
                "social": base_score * 1.1,
            },
            "reasoning": "Mock Gemini analysis",
            "timestamp": "2025-11-12"
        }

# Patch Gemini in non_standard_risk_dual
import data.features.non_standard_risk_dual as nsr_module
nsr_module.GeminiClient = MockGeminiClient

# Now run the test
from data.features.non_standard_risk_dual import NonStandardRiskCalculator, RiskMode
import asyncio

async def quick_test():
    calculator = NonStandardRiskCalculator(mode=RiskMode.DUAL)
    
    result = await calculator.calculate(
        ticker="AAPL",
        news_headlines=["Apple reports strong earnings", "New iPhone launch"],
    )
    
    print("Quick Test Result:")
    print(f"Ticker: {result['ticker']}")
    if 'v1_result' in result:
        print(f"V1 (Rule): {result['v1_result']['risk_level']} ({result['v1_result']['risk_score']:.2f})")
    if 'v2_result' in result:
        print(f"V2 (Mock): {result['v2_result']['risk_level']} ({result['v2_result']['risk_score']:.2f})")
    print(f"Agreement: {result.get('agreement', 'N/A')}")
    print(f"
DUAL mode is working!
")

asyncio.run(quick_test())
