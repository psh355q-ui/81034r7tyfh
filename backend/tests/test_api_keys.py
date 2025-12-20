"""
API 키 검증 스크립트

모든 필수 API 키가 설정되어 있는지 확인
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def test_api_keys():
    """API 키 검증"""
    
    # .env 파일 로드 (프로젝트 루트에서)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    print("="*60)
    print("🔑 API 키 검증")
    print("="*60)
    print()
    
    keys_to_check = {
        "GEMINI_API_KEY": "Gemini (Deep Reasoning, Search)",
        "ANTHROPIC_API_KEY": "Claude (Skeptic Agent, Analysis)",
        "OPENAI_API_KEY": "OpenAI (Whisper STT - 선택)",
        "NEWSAPI_KEY": "News API (뉴스 수집)",
    }
    
    results = {}
    
    for key_name, description in keys_to_check.items():
        key_value = os.getenv(key_name)
        
        if key_value and len(key_value) > 10:
            status = "✅"
            masked = key_value[:8] + "..." + key_value[-4:]
            results[key_name] = True
        else:
            status = "❌"
            masked = "NOT SET"
            results[key_name] = False
        
        print(f"{status} {key_name}")
        print(f"   Description: {description}")
        print(f"   Value: {masked}")
        print()
    
    # 요약
    print("="*60)
    total = len(results)
    passed = sum(results.values())
    
    print(f"📊 요약: {passed}/{total} API 키 설정됨")
    print()
    
    if passed == total:
        print("✅ 모든 API 키가 설정되었습니다!")
        return True
    else:
        print("⚠️  일부 API 키가 누락되었습니다.")
        print()
        print("설정 방법:")
        print("1. 프로젝트 루트의 .env 파일 편집")
        print("2. 누락된 키를 추가:")
        for key_name, is_set in results.items():
            if not is_set:
                print(f"   {key_name}=your_api_key_here")
        return False

if __name__ == "__main__":
    test_api_keys()
