"""
미국 시장 브리핑 생성 및 텔레그램 전송 테스트

작성일: 2026-01-23
목적: 미국 시장 시작 전 브리핑 생성 후 텔레그램으로 전송
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 환경 변수 로드
load_dotenv()

from backend.ai.reporters.enhanced_daily_reporter import EnhancedDailyReporter
from backend.notifications.telegram_notifier import TelegramNotifier


async def generate_and_send_briefing():
    """
    미국 시장 브리핑 생성 및 텔레그램 전송
    """
    print("=" * 80)
    print("미국 시장 브리핑 생성 및 텔레그램 전송 테스트")
    print("=" * 80)
    print(f"\n현재 시간 (KST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"미국 시장 시작 전 브리핑 생성\n")

    # 1. EnhancedDailyReporter 초기화
    print("[1/3] EnhancedDailyReporter 초기화 중...")
    reporter = EnhancedDailyReporter()
    print("✅ EnhancedDailyReporter 초기화 완료\n")

    # 2. 브리핑 생성
    print("[2/3] 미국 시장 브리핑 생성 중...")
    try:
        filename = await reporter.generate_enhanced_briefing()
        print(f"✅ 브리핑 생성 완료: {filename}\n")
    except Exception as e:
        print(f"❌ 브리핑 생성 실패: {e}\n")
        return

    # 3. 브리핑 내용 읽기
    print("[3/3] 브리핑 내용 읽기 중...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            briefing_content = f.read()
        print(f"✅ 브리핑 내용 읽기 완료 ({len(briefing_content)}자)\n")
    except Exception as e:
        print(f"❌ 브리핑 내용 읽기 실패: {e}\n")
        return

    # 4. TelegramNotifier 초기화
    print("TelegramNotifier 초기화 중...")
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    print("✅ TelegramNotifier 초기화 완료\n")

    # 5. 텔레그램으로 전송
    print("텔레그램으로 브리핑 전송 중...")
    
    # 메시지 분할 (텔레그램 4096자 제한)
    max_length = 4000  # 안전 마진
    if len(briefing_content) > max_length:
        messages = []
        for i in range(0, len(briefing_content), max_length):
            part = briefing_content[i:i+max_length]
            if i > 0:
                part = f"... (계속)\n\n{part}"
            if i + max_length < len(briefing_content):
                part += "\n\n(계속됨 ...)"
            messages.append(part)
    else:
        messages = [briefing_content]

    print(f"메시지 분할: {len(messages)}개 파트\n")

    # 각 파트 전송
    success_count = 0
    for i, message in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] 파트 전송 중...")
        
        # 헤더 추가
        header = f"📢 미국 시장 브리핑 ({datetime.now().strftime('%Y-%m-%d')})\n"
        if i > 1:
            header = f"📢 미국 시장 브리핑 ({datetime.now().strftime('%Y-%m-%d')}) - 파트 {i}/{len(messages)}\n"
        
        full_message = header + message
        
        try:
            success = await telegram_notifier.send_message(
                text=full_message,
                parse_mode="HTML",
                disable_notification=False,
            )
            
            if success:
                success_count += 1
                print(f"  ✅ 파트 {i} 전송 성공")
            else:
                print(f"  ❌ 파트 {i} 전송 실패")
            
            # Rate limiting (2초 대기)
            if i < len(messages):
                await asyncio.sleep(2)
        
        except Exception as e:
            print(f"  ❌ 파트 {i} 전송 중 오류: {e}")

    # 결과 요약
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"브리핑 파일: {filename}")
    print(f"브리핑 길이: {len(briefing_content)}자")
    print(f"메시지 파트: {len(messages)}개")
    print(f"전송 성공: {success_count}/{len(messages)}")
    
    if success_count == len(messages):
        print("\n✅ 모든 메시지 전송 성공!")
    else:
        print(f"\n⚠️ 일부 메시지 전송 실패 ({len(messages) - success_count}개)")
    
    print("=" * 80)


if __name__ == "__main__":
    print("\n미국 시장 브리핑 생성 및 텔레그램 전송 테스트")
    print("시간: 23:10 KST (미국 시장 시작 전)\n")
    
    asyncio.run(generate_and_send_briefing())
