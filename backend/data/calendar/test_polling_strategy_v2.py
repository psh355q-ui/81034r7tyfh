"""
수정된 폴링 전략 시뮬레이션
(Forex Factory bot 차단 회피)
"""

def get_polling_interval_v2(time_diff_seconds: float) -> int:
    """
    수정된 폴링 간격
    
    핵심 변경:
    - 발표 후 3분까지만 집중 모니터링
    - 3분 후에는 5분 간격 (bot 차단 회피)
    """
    # 발표 후 3분 경과 시 5분 간격으로 변경
    if time_diff_seconds < -180:  # T+3분 이후
        return 300  # 5분마다 (느리게)
    
    # 집중 모니터링 구간
    elif time_diff_seconds < 0:  # T ~ T+3분 (발표 직후)
        return 30   # 30초마다
    elif time_diff_seconds < 180:  # T-3분 ~ T (발표 직전)
        return 10   # 10초마다 (가장 집중!)
    elif time_diff_seconds < 300:  # T-5분 ~ T-3분
        return 30   # 30초마다
    elif time_diff_seconds < 900:  # T-15분 ~ T-5분
        return 60   # 1분마다
    else:  # T-15분 이전
        return 300  # 5분마다


print("=" * 70)
print("  수정된 폴링 전략 (Forex Factory bot 차단 회피)")
print("=" * 70)
print()

test_times = [
    -1200,  # T-20분
    -900,   # T-15분
    -300,   # T-5분
    -180,   # T-3분
    -60,    # T-1분
    0,      # T (발표!)
    +60,    # T+1분
    +180,   # T+3분 ⭐ 여기부터 5분 간격!
    +300,   # T+5분
    +600,   # T+10분 (타임아웃)
]

for seconds in test_times:
    interval = get_polling_interval_v2(seconds)
    
    if seconds < 0:
        time_str = f"T-{abs(seconds)//60}분"
    elif seconds == 0:
        time_str = "T (발표!)"
    else:
        time_str = f"T+{seconds//60}분"
    
    print(f"  {time_str:<12} → {interval}초마다 체크", end="")
    
    if interval == 10:
        print("  ⚡⚡⚡ (집중 모니터링!)")
    elif interval == 30:
        print("  ⚡")
    elif interval == 300 and seconds > 0:
        print("  🐢 (bot 차단 회피)")
    else:
        print()

print()
print("=" * 70)
print("  변경 사항 요약")
print("=" * 70)
print()
print("✅ 발표 후 3분까지:")
print("   - 10-30초 간격으로 집중 모니터링")
print("   - 결과 빠르게 수집")
print()
print("✅ 발표 후 3분 이후:")
print("   - 5분 간격으로 변경 (300초)")
print("   - Forex Factory bot 차단 회피")
print("   - Rate limit 준수")
print()
print("✅ 타임아웃:")
print("   - 기존: 30분")
print("   - 변경: 10분 (3분 집중 + 7분 여유)")
print()
print("💡 장점:")
print("   - 중요한 3분 동안 집중 모니터링")
print("   - 이후에는 느리게 체크하여 bot 차단 회피")
print("   - 대부분의 결과는 3분 내 수집 가능")
