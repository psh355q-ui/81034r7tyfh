
import requests
import json
import urllib3
import logging

# Disable warnings
urllib3.disable_warnings()

# Configuration
BASE_URL = "http://127.0.0.1:8001"
HEADERS = {"Content-Type": "application/json"}

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_emergency_status():
    """Test /api/emergency/status (checks portfolio integration)"""
    url = f"{BASE_URL}/api/emergency/status"
    try:
        logger.info(f"Testing {url}...")
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Emergency Status API: SUCCESS")
            # Check for portfolio data
            if "portfolio_data" in data:
                logger.info(f"   Portfolio Data: {json.dumps(data['portfolio_data'])}")
            else:
                logger.warning("   ⚠️ Portfolio data missing in response")
            return True
        else:
            logger.error(f"❌ Emergency Status API Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Emergency Status API Exception: {e}")
        return False

def test_analysis(ticker="NVDA"):
    """Test /api/analyze for NVDA (checks structure and data)"""
    url = f"{BASE_URL}/api/analyze"
    payload = {"ticker": ticker}
    
    try:
        logger.info(f"Testing {url} with ticker={ticker}...")
        response = requests.post(url, json=payload, verify=False, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Analyze API: SUCCESS")
            
            # Verify Top-Level Fields
            errors = []
            
            action = data.get("action")
            if not action: errors.append("Missing 'action'")
            
            conviction = data.get("conviction")
            if conviction is None: errors.append("Missing 'conviction'")
            
            pos_size = data.get("position_size")
            if pos_size is None: errors.append("Missing 'position_size'")
            
            reasoning = data.get("reasoning")
            if not reasoning: errors.append("Missing 'reasoning'")
            
            if errors:
                logger.error(f"❌ Validation Errors: {', '.join(errors)}")
                logger.error(f"🔍 FULL RESPONSE: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return False
            else:
                logger.info("✅ ALL VALIDATION CHECKS PASSED")
                return True
        else:
            logger.error(f"❌ Analyze API Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Analyze API Exception: {e}")
        return False

if __name__ == "__main__":
    print("==================================================")
    print("🚀 STARTING VERIFICATION TEST")
    print("==================================================")
    
    emergency_success = test_emergency_status()
    print("-" * 50)
    analysis_success = test_analysis()
    
    print("==================================================")
    if emergency_success and analysis_success:
        print("✅ VERIFICATION SUCCESSFUL")
    else:
        print("❌ VERIFICATION FAILED")
    print("==================================================")
