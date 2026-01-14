
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_risk_logic():
    print("="*60)
    print("🔍 CountryRiskEngine Logic Verification")
    print("="*60)
    
    try:
        from backend.ai.macro.country_risk_engine import CountryRiskEngine, Country
        engine = CountryRiskEngine()
        print("✅ Engine initialized")
        
        country_codes = ["US", "JP", "CN", "EU", "KR"]
        risks = []
        
        for code in country_codes:
            print(f"Processing {code}...")
            c_enum = Country(code)
            score_obj = engine.calculate_risk_score(c_enum)
            
            components = {
                "interest": score_obj.interest_rate_risk,
                "inflation": score_obj.inflation_risk,
                "currency": score_obj.currency_risk,
                "growth": score_obj.growth_risk,
                "stock": score_obj.equity_risk
            }
            
            risk_item = {
                "country": code,
                "score": round(score_obj.composite_score, 2),
                "components": components,
                "trend": "stable"
            }
            risks.append(risk_item)
            print(f"  -> Score: {risk_item['score']}")
            
        print("\n✅ Verification Successful: All countries processed.")
        print(f"Total Risks Calculated: {len(risks)}")

    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_risk_logic()
