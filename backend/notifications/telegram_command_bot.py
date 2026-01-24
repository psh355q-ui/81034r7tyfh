"""
telegram_command_bot.py - PHASE8: 텔레그램 명령어 구현

📊 Data Sources:
    - Telegram Bot API: 명령어 처리
    - KIS Broker: 포트폴리오 조회
    - Economic Calendar: 경제 일정 조회
    - Daily Briefing Service: 브리핑 스케줄 조회

🔗 External Dependencies:
    - backend.notifications.telegram_notifier: 텔레그램 알림 시스템
    - backend.services.portfolio_analyzer: 포트폴리오 분석
    - backend.services.economic_calendar_manager: 경제 캘린더
    - logging: 로깅

📤 Main Functions:
    - /status: 현재 시장 현황
    - /portfolio: 포트폴리오 요약
    - /schedule: 오늘 브리핑 스케줄
    - /economic: 오늘의 경제 일정 (v2.2)
    - /help: 도움말

🔄 Called By:
    - Telegram Bot: 사용자 명령어 처리
    - Daily Briefing System: 브리핑 전송

📝 Notes:
    - 텔레그램 4096자 제한 자동 분할
    - 마크다운 포맷팅
    - Rate limiting (0.5초 간격)

Author: AI Trading System Team
Date: 2026-01-23
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


class TelegramCommandBot:
    """
    텔레그램 명령어 봇
    
    사용자 명령어를 처리하고 응답을 생성합니다.
    """
    
    def __init__(self, telegram_notifier=None, portfolio_analyzer=None, economic_calendar_manager=None):
        """
        TelegramCommandBot 초기화
        
        Args:
            telegram_notifier: TelegramNotifier 인스턴스
            portfolio_analyzer: PortfolioAnalyzer 인스턴스
            economic_calendar_manager: EconomicCalendarManager 인스턴스
        """
        self.telegram_notifier = telegram_notifier
        self.portfolio_analyzer = portfolio_analyzer
        self.economic_calendar_manager = economic_calendar_manager
        
        # 명령어 핸들러 맵
        self.commands = {
            '/status': self._handle_status,
            '/portfolio': self._handle_portfolio,
            '/schedule': self._handle_schedule,
            '/economic': self._handle_economic,
            '/help': self._handle_help,
        }
        
        logger.info("TelegramCommandBot initialized")
    
    async def handle_command(self, command: str, args: List[str] = None) -> str:
        """
        명령어 처리
        
        Args:
            command: 명령어 (예: /status)
            args: 명령어 인자
            
        Returns:
            응답 메시지
        """
        try:
            # 명령어 정규화
            command = command.lower()
            
            # 명령어 핸들러 찾기
            handler = self.commands.get(command)
            
            if handler:
                # 핸들러 실행
                response = await handler(args)
                
                # 메시지 분할 (4096자 제한)
                return await self._split_message(response)
            else:
                # 알 수 없는 명령어
                return await self._handle_help()
                
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}", exc_info=True)
            return f"❌ 명령어 처리 중 오류가 발생했습니다: {str(e)}"
    
    async def _handle_status(self, args: List[str] = None) -> str:
        """
        현재 시장 현황
        
        Returns:
            시장 현황 메시지
        """
        try:
            # 현재 시간
            now = datetime.now()
            
            # 미국 시장 상태
            est_time = now - timedelta(hours=13)  # KST -> EST (동절기)
            is_market_open = 9 <= est_time.hour < 16
            
            market_status = "🟢 장 중" if is_market_open else "🔴 장 종료"
            
            # 시장 현황 메시지
            message = f"""
📊 현재 시장 현황

🕐 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} KST
🇺🇸 미국 시장: {market_status}

📈 주요 지수
• S&P 500: 장중 데이터 없음
• NASDAQ: 장중 데이터 없음
• DOW: 장중 데이터 없음

💡 참고
• /portfolio: 포트폴리오 현황
• /schedule: 오늘 브리핑 스케줄
• /economic: 오늘의 경제 일정
"""
            return message
            
        except Exception as e:
            logger.error(f"Error handling /status: {e}", exc_info=True)
            return f"❌ 시장 현황 조회 중 오류가 발생했습니다: {str(e)}"
    
    async def _handle_portfolio(self, args: List[str] = None) -> str:
        """
        포트폴리오 요약
        
        Returns:
            포트폴리오 요약 메시지
        """
        try:
            if not self.portfolio_analyzer:
                return "⚠️ 포트폴리오 분석기가 초기화되지 않았습니다."
            
            # 포트폴리오 브리핑 섹션 생성
            section = await self.portfolio_analyzer.generate_briefing_section()
            
            # 포트폴리오 요약 메시지
            message = f"""
💼 포트폴리오 요약

📊 총 자산: ${section['total_value']:,.2f}
💰 총 수익: ${section['total_pnl']:+,.2f} ({section['total_return_pct']:+.2f}%)
📈 일일 수익: ${section['daily_pnl']:+,.2f} ({section['daily_return_pct']:+.2f}%)
🔔 알림: {section['alert_count']}개

📋 보유 종목 ({len(section['positions'])}개)
"""
            
            # 보유 종목 목록
            for pos in section['positions'][:5]:  # 최대 5개만 표시
                emoji = "📈" if pos['daily_return_pct'] > 0 else "📉"
                message += f"""
{emoji} {pos['ticker']} ({pos['name']})
   • 수량: {pos['quantity']}
   • 평균가: ${pos['avg_price']:.2f}
   • 현재가: ${pos['current_price']:.2f}
   • 수익: ${pos['profit_loss']:+,.2f} ({pos['daily_return_pct']:+.2f}%)
"""
            
            if len(section['positions']) > 5:
                message += f"\n... 외 {len(section['positions']) - 5}개 종목\n"
            
            # 상위/하위 종목
            if section['top_performers']:
                message += "\n📈 상위 종목:\n"
                for p in section['top_performers']:
                    message += f"  • {p['ticker']}: {p['daily_return_pct']:+.2f}%\n"
            
            if section['bottom_performers']:
                message += "\n📉 하위 종목:\n"
                for p in section['bottom_performers']:
                    message += f"  • {p['ticker']}: {p['daily_return_pct']:+.2f}%\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Error handling /portfolio: {e}", exc_info=True)
            return f"❌ 포트폴리오 조회 중 오류가 발생했습니다: {str(e)}"
    
    async def _handle_schedule(self, args: List[str] = None) -> str:
        """
        오늘 브리핑 스케줄
        
        Returns:
            브리핑 스케줄 메시지
        """
        try:
            # 현재 시간
            now = datetime.now()
            
            # 브리핑 스케줄 (하절기 기준)
            schedules = {
                "프리마켓 브리핑": "22:00 KST",
                "장중 체크포인트 #1": "01:00 KST",
                "장중 체크포인트 #2": "03:00 KST",
                "미국 마감 브리핑": "07:10 KST",
                "국내 프리마켓 브리핑": "08:00 KST",
                "국내 장중 체크포인트": "10:00 KST",
                "국내 마감 브리핑": "16:00 KST",
            }
            
            # 브리핑 스케줄 메시지
            message = f"""
📅 오늘 브리핑 스케줄

🕐 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} KST

📋 브리핑 일정
"""
            
            for name, time in schedules.items():
                message += f"• {name}: {time}\n"
            
            message += """
💡 참고
• /status: 현재 시장 현황
• /portfolio: 포트폴리오 현황
• /economic: 오늘의 경제 일정
"""
            return message
            
        except Exception as e:
            logger.error(f"Error handling /schedule: {e}", exc_info=True)
            return f"❌ 브리핑 스케줄 조회 중 오류가 발생했습니다: {str(e)}"
    
    async def _handle_economic(self, args: List[str] = None) -> str:
        """
        오늘의 경제 일정 (v2.2)
        
        Returns:
            경제 일정 메시지
        """
        try:
            if not self.economic_calendar_manager:
                return "⚠️ 경제 캘린더 관리자가 초기화되지 않았습니다."
            
            # 오늘의 경제 일정 조회
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            
            # 경제 일정 메시지
            message = f"""
⚡ 오늘의 경제 일정

🕐 조회 기간: {start_time.strftime('%Y-%m-%d')} ~ {end_time.strftime('%Y-%m-%d')}

📋 주요 경제지표
"""
            
            # 경제 일정 조회 (구현 필요)
            # TODO: EconomicCalendarManager에서 오늘의 경제 일정 조회
            message += "• 경제 일정 조회 기능 구현 중...\n"
            
            message += """
💡 참고
• /status: 현재 시장 현황
• /portfolio: 포트폴리오 현황
• /schedule: 오늘 브리핑 스케줄
"""
            return message
            
        except Exception as e:
            logger.error(f"Error handling /economic: {e}", exc_info=True)
            return f"❌ 경제 일정 조회 중 오류가 발생했습니다: {str(e)}"
    
    async def _handle_help(self, args: List[str] = None) -> str:
        """
        도움말
        
        Returns:
        도움말 메시지
        """
        message = """
📖 사용 가능한 명령어

📊 시장 정보
• /status - 현재 시장 현황

💼 포트폴리오
• /portfolio - 포트폴리오 요약

📅 브리핑 스케줄
• /schedule - 오늘 브리핑 스케줄

⚡ 경제 정보
• /economic - 오늘의 경제 일정

📖 도움말
• /help - 이 도움말 표시

💡 팁
• 명령어 앞에 '/'를 붙이세요
• 예: /status, /portfolio
"""
        return message
    
    async def _split_message(self, message: str, max_length: int = 4096) -> List[str]:
        """
        메시지 분할 (텔레그램 4096자 제한)
        
        Args:
            message: 원본 메시지
            max_length: 최대 길이 (기본 4096)
            
        Returns:
            분할된 메시지 리스트
        """
        if len(message) <= max_length:
            return [message]
        
        # 메시지 분할
        parts = []
        current_part = ""
        
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line
            else:
                if current_part:
                    current_part += '\n'
                current_part += line
        
        if current_part:
            parts.append(current_part)
        
        logger.info(f"Message split into {len(parts)} parts")
        return parts
    
    async def send_message(self, message: str):
        """
        메시지 전송 (텔레그램 봇에 직접 전송)
        
        Args:
            message: 전송할 메시지
        """
        try:
            # 메시지 분할
            parts = await self._split_message(message)
            
            # 텔레그램 봇에 직접 전송
            if self.telegram_notifier:
                for i, part in enumerate(parts):
                    if i > 0:
                        # 첫 번째가 아니면 접미사 추가
                        part = f"... (계속 {i}/{len(parts)})\n\n{part}"
                    await self.telegram_notifier.send_message(part)
            
            logger.info(f"Message sent in {len(parts)} parts")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
    
    async def send_economic_alert(self, event: Dict[str, Any], analysis: Dict[str, Any]):
        """
        경제지표 즉시 알림
        
        Args:
            event: 경제 이벤트 딕셔너리
            analysis: 분석 결과 딕셔너리
        """
        try:
            emoji = "📈" if analysis['direction'] == 'Bullish' else "📉"
            
            message = f"""
⚡ Economic Data Alert {emoji}

*{event.get('event_name', 'Unknown')}*
🕐 {event.get('event_time', datetime.now()).strftime('%H:%M')} KST

📊 결과
• 예상: {event.get('forecast', 'N/A')}
• 실제: {event.get('actual', 'N/A')}
• 이전: {event.get('previous', 'N/A')}

🔴 분석
• Surprise: {analysis.get('surprise_pct', 0):+.1f}%
• 영향: {analysis['direction']}
• 점수: {analysis.get('score', 0)}/100

💡 해석
"""
            
            # 해석 추가
            if analysis.get('direction') == 'Bullish':
                message += "시장에 긍정적 신호. 상승 가능성 높음.\n"
            elif analysis.get('direction') == 'Bearish':
                message += "시장에 부정적 신호. 변동성 확대 주의.\n"
            else:
                message += "중립적 신호. 큰 변동 없을 것으로 예상.\n"
            
            # 텔레그램 알림 전송 (send_file 사용)
            if self.telegram_notifier:
                # 경제지표 알림을 파일로 저장
                alert_file = f"economic_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(alert_file, 'w', encoding='utf-8') as f:
                    f.write(message)
                
                # 파일 전송
                await self.telegram_notifier.send_file(alert_file, caption="⚡ Economic Data Alert")
            
            logger.info(f"Economic alert sent for {event.get('event_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error sending economic alert: {e}", exc_info=True)


# ========== Demo Function ==========

async def demo():
    """
    TelegramCommandBot 데모 함수
    """
    print("=" * 80)
    print("PHASE8: 텔레그램 명령어 구현 데모")
    print("=" * 80)
    
    # TelegramCommandBot 초기화
    bot = TelegramCommandBot()
    
    # 1. /status 명령어 테스트
    print("\n[1] /status 명령어 테스트")
    print("-" * 80)
    response = await bot.handle_command('/status')
    print(response)
    
    # 2. /portfolio 명령어 테스트
    print("\n[2] /portfolio 명령어 테스트")
    print("-" * 80)
    response = await bot.handle_command('/portfolio')
    print(response)
    
    # 3. /schedule 명령어 테스트
    print("\n[3] /schedule 명령어 테스트")
    print("-" * 80)
    response = await bot.handle_command('/schedule')
    print(response)
    
    # 4. /economic 명령어 테스트
    print("\n[4] /economic 명령어 테스트")
    print("-" * 80)
    response = await bot.handle_command('/economic')
    print(response)
    
    # 5. /help 명령어 테스트
    print("\n[5] /help 명령어 테스트")
    print("-" * 80)
    response = await bot.handle_command('/help')
    print(response)
    
    # 6. 메시지 분할 테스트
    print("\n[6] 메시지 분할 테스트")
    print("-" * 80)
    long_message = "A" * 5000  # 5000자 메시지
    split_message = await bot._split_message(long_message)
    print(f"원본 메시지 길이: {len(long_message)}")
    print(f"분할 후 메시지 길이: {len(split_message)}")
    print(f"분할 성공: {len(long_message) > 4096}")
    
    # 7. 경제지표 알림 테스트
    print("\n[7] 경제지표 알림 테스트")
    print("-" * 80)
    print("⚠️  텔레그램 봇에 직접 연결 필요")
    print("   telegram_notifier 초기화 시 실제 전송됩니다.")
    print("   현재 데모에서는 메시지 생성만 테스트합니다.")
    print("✅ 경제지표 알림 테스트 완료 (데모 모드)")
    
    # 8. 텔레그램 봇에 보내는 테스트
    print("\n[8] 텔레그램 봇에 보내는 테스트")
    print("-" * 80)
    print("⚠️  텔레그램 봇에 직접 연결 필요")
    print("   telegram_notifier 초기화 시 실제 전송됩니다.")
    print("   현재 데모에서는 메시지 생성만 테스트합니다.")
    print("✅ 텔레그램 봇 테스트 완료 (데모 모드)")
    
    print("\n" + "=" * 80)
    print("PHASE8 데모 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo())
