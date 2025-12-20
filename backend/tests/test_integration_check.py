"""
Simple Integration Check - Management Credibility Factor

이 스크립트는 통합이 올바르게 되었는지 빠르게 확인합니다.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_imports():
    """Check if all required imports work."""
    print("\n" + "="*80)
    print("Step 1: Checking Imports")
    print("="*80 + "\n")
    
    try:
        print("✓ Importing config...")
        from config import get_settings
        settings = get_settings()
        
        print("✓ Importing management_credibility...")
        from data.features.management_credibility import ManagementCredibilityCalculator
        
        print("✓ Importing trading_agent...")
        from ai.trading_agent import TradingAgent
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config():
    """Check if config has new settings."""
    print("\n" + "="*80)
    print("Step 2: Checking Config")
    print("="*80 + "\n")
    
    try:
        from config import get_settings
        settings = get_settings()
        
        # Check new settings
        checks = [
            ("min_management_credibility", 0.3),
            ("management_credibility_position_scaling", True),
            ("management_credibility_use_ai", True),
            ("feature_cache_ttl_management_credibility", 90 * 24 * 3600),
        ]
        
        all_good = True
        for setting_name, expected_default in checks:
            if hasattr(settings, setting_name):
                value = getattr(settings, setting_name)
                print(f"✓ {setting_name}: {value}")
            else:
                print(f"❌ Missing: {setting_name}")
                all_good = False
        
        if all_good:
            print("\n✅ Config check passed!")
        else:
            print("\n⚠️  Some config settings missing - please add them to config.py")
        
        return all_good
        
    except Exception as e:
        print(f"\n❌ Config check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_trading_agent():
    """Check if TradingAgent has management credibility integration."""
    print("\n" + "="*80)
    print("Step 3: Checking Trading Agent Integration")
    print("="*80 + "\n")

    try:
        from ai.trading_agent import TradingAgent
        from ai.claude_client import MockClaudeClient

        # Use mock client to avoid API key requirement
        mock_client = MockClaudeClient()
        agent = TradingAgent(claude_client=mock_client)
        
        # Check if management_credibility_calc exists
        if hasattr(agent, 'management_credibility_calc'):
            print("✓ management_credibility_calc initialized")
        else:
            print("❌ management_credibility_calc not found in TradingAgent.__init__")
            return False
        
        # Check if management_credibility in standard_features
        if "management_credibility" in agent.standard_features:
            print("✓ management_credibility in standard_features")
        else:
            print("❌ management_credibility not in standard_features")
            return False
        
        print("\n✅ Trading Agent integration check passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Trading Agent check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all checks."""
    print("\n" + "="*80)
    print("🔍 Management Credibility Integration Check")
    print("="*80)
    
    results = {
        "Imports": check_imports(),
        "Config": check_config(),
        "Trading Agent": check_trading_agent(),
    }
    
    print("\n" + "="*80)
    print("📊 Final Results")
    print("="*80 + "\n")
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:20s} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All checks passed! Integration is complete.")
        print("\nNext steps:")
        print("  1. Run: python test_mock_credibility.py")
        print("  2. Run: python test_trading_agent_with_mgmt.py (requires API keys)")
    else:
        print("\n⚠️  Some checks failed. Please review the integration guide:")
        print("  - STEP_BY_STEP_INTEGRATION_GUIDE.md")
        print("  - QUICK_INTEGRATION_SUMMARY.md")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())