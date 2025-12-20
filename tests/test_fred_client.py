"""
FRED Client 테스트 스크립트
.env 파일에서 API 키를 로드합니다
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# .env 로드
from dotenv import load_dotenv
load_dotenv()

# FRED Client 테스트
from backend.data.collectors.api_clients.fred_client import FREDClient

print("=== FRED Client Test (with .env) ===\n")

try:
    client = FREDClient()
    
    # Test 1: 국채 금리
    print("Test 1: Treasury Yields")
    treasury_2y = client.get_treasury_yield("2Y")
    treasury_10y = client.get_treasury_yield("10Y")
    
    if treasury_2y and treasury_10y:
        yield_curve = treasury_10y - treasury_2y
        print(f"✅ 2Y Treasury: {treasury_2y}%")
        print(f"✅ 10Y Treasury: {treasury_10y}%")
        print(f"✅ Yield Curve: {yield_curve:+.2f}%")
    
    # Test 2: VIX
    print("\nTest 2: VIX")
    vix = client.get_vix()
    if vix:
        print(f"✅ VIX: {vix}")
    
    # Test 3: 달러 지수
    print("\nTest 3: Dollar Index")
    dxy = client.get_dxy()
    if dxy:
        print(f"✅ DXY: {dxy}")
    
    # Test 4: 전체 지표
    print("\nTest 4: All Macro Indicators")
    indicators = client.get_all_macro_indicators()
    print(f"✅ Retrieved {len(indicators)} indicators:")
    for key, value in indicators.items():
        print(f"  - {key}: {value}")
    
    print("\n🎉 FRED Client test PASSED!")
    
except ValueError as e:
    print(f"❌ Error: {e}")
    print("\nPlease make sure FRED_API_KEY is in .env file")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
