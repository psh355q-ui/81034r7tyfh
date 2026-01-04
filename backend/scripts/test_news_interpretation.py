"""
News Agent Enhancement 성능 테스트

War Room 실행 후 news_interpretations 테이블 확인
"""
import requests
import time
import psycopg2
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_trading')
DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

def test_war_room_news_interpretation():
    """War Room 실행하여 뉴스 해석 기능 테스트"""
    print("="*60)
    print("News Agent Enhancement 성능 테스트")
    print("="*60)
    
    # 1. War Room 실행
    print("\n🚀 War Room 실행 중 (NVDA)...")
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:8001/api/war-room-mvp/deliberate',
            json={
                'symbol': 'NVDA',
                'action_context': 'new_position'
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  응답 시간: {elapsed:.2f}초")
        
        if response.status_code == 200:
            print(f"✅ War Room 정상 실행 (200 OK)")
            result = response.json()
            print(f"   - 최종 결정: {result.get('final_decision', 'N/A')}")
            print(f"   - 전체 신뢰도: {result.get('overall_confidence', 'N/A')}")
        else:
            print(f"❌ War Room 실행 실패 ({response.status_code})")
            print(f"   - 에러: {response.text[:200]}")
            return
            
    except Exception as e:
        print(f"❌ War Room 실행 중 오류: {e}")
        return
    
    # 2. DB에서 새로 생성된 해석 확인
    print("\n📊 뉴스 해석 데이터 확인...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 최근 5분간 생성된 해석 개수
        cursor.execute("""
            SELECT COUNT(*) FROM news_interpretations 
            WHERE interpreted_at >= NOW() - INTERVAL '5 minutes'
        """)
        
        new_count = cursor.fetchone()[0]
        print(f"✅ 새로 생성된 해석: {new_count}개")
        
        # 3. 최근 해석 상세 조회
        if new_count > 0:
            print("\n📝 해석 내용:")
            cursor.execute("""
                SELECT 
                    ticker,
                    headline_bias,
                    expected_impact,
                    time_horizon,
                    confidence,
                    reasoning,
                    interpreted_at
                FROM news_interpretations 
                WHERE interpreted_at >= NOW() - INTERVAL '5 minutes'
                ORDER BY interpreted_at DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            for i, r in enumerate(results, 1):
                print(f"\n{i}. Ticker: {r[0]}")
                print(f"   Bias: {r[1]} | Impact: {r[2]} | Horizon: {r[3]}")
                print(f"   Confidence: {r[4]}")
                print(f"   Reasoning: {r[5][:100]}...")
                print(f"   Time: {r[6]}")
        else:
            print("\n⚠️  새로 생성된 해석이 없습니다.")
            print("   확인 사항:")
            print("   1. ENABLE_NEWS_INTERPRETATION=true 설정 확인")
            print("   2. Macro Context가 오늘 날짜로 존재하는지 확인")
            print("   3. NVDA 관련 뉴스가 있는지 확인")
        
        # 4. 전체 해석 개수 확인
        cursor.execute("SELECT COUNT(*) FROM news_interpretations")
        total = cursor.fetchone()[0]
        print(f"\n📊 총 해석 개수: {total}개")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ DB 조회 중 오류: {e}")
    
    finally:
        if 'conn' in locals():
            conn.close()
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)

if __name__ == "__main__":
    test_war_room_news_interpretation()
