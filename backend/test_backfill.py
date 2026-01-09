"""
뉴스 백필 테스트 스크립트
"""
import httpx
import json
from datetime import datetime

def test_news_backfill():
    """Ollama 기반 뉴스 백필 테스트"""
    print("=" * 80)
    print("뉴스 백필 테스트 (Ollama)")
    print("=" * 80)
    print()
    
    url = "http://localhost:8001/api/backfill/news"
    data = {
        "start_date": "2026-01-08",
        "end_date": "2026-01-09"
    }
    
    print(f"📡 요청 URL: {url}")
    print(f"📅 기간: {data['start_date']} ~ {data['end_date']}")
    print()
    
    try:
        print("⏳ 백필 시작...")
        response = httpx.post(
            url,
            json=data,
            timeout=300.0  # 5분 타임아웃
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 백필 완료!")
            print(f"\n결과:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 백필 실패: HTTP {response.status_code}")
            print(f"응답: {response.text}")
            
    except httpx.TimeoutException:
        print("\n⏱️ 타임아웃: 백필이 5분 이상 소요되고 있습니다.")
        print("백그라운드에서 계속 실행 중일 수 있습니다.")
    except Exception as e:
        print(f"\n❌ 오류: {e}")

if __name__ == "__main__":
    test_news_backfill()
