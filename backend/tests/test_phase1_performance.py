"""
Phase 1 성능 측정 스크립트
War Room MVP DB 쿼리 시간 및 전체 응답 시간 측정

최적화 내용:
- 복합 인덱스 5개 추가
- N+1 쿼리 패턴 제거 (ON CONFLICT)
- TTL 캐싱 추가 (5분)

목표: DB 쿼리 0.5-1.0s → 0.3-0.5s 단축
"""
import time
import requests
import statistics
from typing import List, Dict

# War Room MVP API
BASE_URL = "http://localhost:8001"
TEST_TICKER = "NVDA"

def measure_api_response_time(ticker: str, runs: int = 5) -> Dict:
    """War Room MVP API 응답 시간 측정"""
    times = []
    
    print(f"\n{'='*80}")
    print(f"📊 War Room MVP Performance Test - {ticker}")
    print(f"{'='*80}\n")
    
    for i in range(runs):
        try:
            start = time.time()
            
            response = requests.post(
                f"{BASE_URL}/api/war-room-mvp/deliberate",
                json={"symbol": ticker},
                timeout=30
            )
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  Run {i+1}/{runs}: {elapsed:.2f}s {status}")
            
            if response.status_code == 200:
                data = response.json()
                exec_mode = data.get('execution_mode', 'unknown')
                print(f"           Execution Mode: {exec_mode}")
            
            # API 부하 방지
            time.sleep(1)
            
        except Exception as e:
            print(f"  Run {i+1}/{runs}: Error - {e}")
            continue
    
    if not times:
        return {"error": "All requests failed"}
    
    return {
        "avg": statistics.mean(times),
        "min": min(times),
        "max": max(times),
        "median": statistics.median(times),
        "count": len(times)
    }

def print_performance_results(results: Dict):
    """성능 측정 결과 출력"""
    print(f"\n{'='*80}")
    print("📈 Performance Results")
    print(f"{'='*80}\n")
    
    if "error" in results:
        print(f"❌ {results['error']}")
        return
    
    print(f"  Average:  {results['avg']:.2f}s")
    print(f"  Median:   {results['median']:.2f}s")
    print(f"  Min:      {results['min']:.2f}s")
    print(f"  Max:      {results['max']:.2f}s")
    print(f"  Samples:  {results['count']}")
    
    # 목표 달성 여부
    print(f"\n{'='*80}")
    print("🎯 Goal Assessment")
    print(f"{'='*80}\n")
    
    target = 15.0  # 15초 목표
    if results['avg'] < target:
        improvement = target - results['avg']
        print(f"  ✅ SUCCESS: {results['avg']:.2f}s < {target}s")
        print(f"  ⚡ {improvement:.2f}s faster than target!")
    else:
        gap = results['avg'] - target
        print(f"  ⚠️  NEEDS IMPROVEMENT: {results['avg']:.2f}s > {target}s")
        print(f"  🔧 Need {gap:.2f}s more optimization")
    
    # Phase 1 최적화 예상 효과
    print(f"\n{'='*80}")
    print("📊 Phase 1 Optimization Impact")
    print(f"{'='*80}\n")
    print("  Expected DB query reduction: 0.5-0.8s")
    print("  - Composite indexes: 0.3-0.4s")
    print("  - N+1 query fix: 0.1-0.2s")
    print("  - Query caching: 0.1-0.2s")
    print(f"\n{'='*80}\n")

def check_server_health():
    """서버 상태 확인"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not accessible: {e}")
        print(f"\n💡 Start the server:")
        print(f"   cd backend && python main.py")
        return False

if __name__ == "__main__":
    print("\n🚀 War Room MVP Performance Measurement")
    print("   Phase 1: Database Optimization Test\n")
    
    # 1. 서버 상태 확인
    if not check_server_health():
        exit(1)
    
    # 2. War Room MVP API 테스트
    results = measure_api_response_time(TEST_TICKER, runs=3)
    
    # 3. 결과 출력
    print_performance_results(results)
    
    print("\n✅ Performance measurement complete!")
    print("\n📝 Next steps:")
    print("  - Review walkthrough.md for complete optimization summary")
    print("  - Consider Phase 2 optimizations if needed")
    print()
