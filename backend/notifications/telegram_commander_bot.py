"""
Telegram Commander Bot - 제안 승인/거부 봇

Commander가 텔레그램으로 AI 제안을 승인/거부할 수 있습니다.

작성일: 2025-12-15
헌법: 제3조 (최종 실행권은 인간)
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from sqlalchemy.orm import Session

from backend.data.models.proposal import Proposal
from backend.backtest.shadow_trade_tracker import ShadowTradeTracker

logger = logging.getLogger(__name__)


class TelegramCommanderBot:
    """
    Telegram Commander Bot
    
    AI 제안을 텔레그램으로 전송하고
    Commander(사용자)의 승인/거부를 받습니다.
    
    Usage:
        bot = TelegramCommanderBot(bot_token, db_session)
        await bot.send_proposal(proposal)
    """
    
    def __init__(
        self,
        bot_token: str,
        db_session: Session,
        shadow_tracker: Optional[ShadowTradeTracker] = None,
        commander_chat_id: Optional[str] = None
    ):
        """
        초기화
        
        Args:
            bot_token: Telegram Bot Token
            db_session: DB 세션
            shadow_tracker: Shadow Trade Tracker
            commander_chat_id: Commander의 Telegram Chat ID
        """
        self.bot_token = bot_token
        self.db = db_session
        self.shadow_tracker = shadow_tracker
        self.commander_chat_id = commander_chat_id
        
        # Application 생성
        self.application = Application.builder().token(bot_token).build()
        
        # Handlers 등록
        self._register_handlers()
        
        logger.info("🤖 Telegram Commander Bot 초기화 완료")
    
    def _register_handlers(self):
        """핸들러 등록"""
        # 명령어 핸들러
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("constitution", self.cmd_constitution))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("pending", self.cmd_pending))
        
        # 버튼 콜백 핸들러
        self.application.add_handler(CallbackQueryHandler(self.handle_approval))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start 명령어"""
        await update.message.reply_text(
            "🏛️ *AI Investment Committee*\n\n"
            "당신은 이제 *Commander*입니다.\n"
            "AI 위원회의 제안을 승인하거나 거부할 수 있습니다.\n\n"
            "헌법 제3조:\n"
            "\"최종 실행권은 인간에게 있다\"\n\n"
            "명령어:\n"
            "/help - 도움말\n"
            "/constitution - 헌법 보기\n"
            "/status - 시스템 상태\n"
            "/pending - 대기 중인 제안",
            parse_mode='Markdown'
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말"""
        await update.message.reply_text(
            "*Commander Mode 사용법*\n\n"
            "1. AI 위원회가 제안을 보내면\n"
            "2. [승인] 또는 [거부] 버튼이 표시됩니다\n"
            "3. 버튼을 눌러 최종 결정하세요\n\n"
            "*주요 명령어*:\n"
            "• /pending - 승인 대기 중인 제안\n"
            "• /constitution - 시스템 헌법\n"
            "• /status - 포트폴리오 상태\n\n"
            "*헌법 제3조*:\n"
            "모든 거래는 Commander의 승인이 필요합니다.",
            parse_mode='Markdown'
        )
    
    async def cmd_constitution(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """헌법 조회"""
        from backend.constitution import Constitution
        
        const = Constitution()
        summary = const.get_constitution_summary()
        
        await update.message.reply_text(
            f"{summary}\n\n"
            f"버전: {const.VERSION}\n"
            f"제정일: {const.ENACTED_DATE}",
            parse_mode='Markdown'
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시스템 상태"""
        # 대기 중인 제안 수
        pending_count = self.db.query(Proposal).filter(
            Proposal.status == 'PENDING'
        ).count()
        
        # 오늘 승인/거부
        today = datetime.utcnow().date()
        approved_today = self.db.query(Proposal).filter(
            Proposal.status == 'APPROVED',
            Proposal.approved_at >= datetime(today.year, today.month, today.day)
        ).count()
        
        rejected_today = self.db.query(Proposal).filter(
            Proposal.status == 'REJECTED',
            Proposal.rejected_at >= datetime(today.year, today.month, today.day)
        ).count()
        
        await update.message.reply_text(
            f"📊 *시스템 상태*\n\n"
            f"⏳ 대기 중인 제안: {pending_count}건\n"
            f"✅ 오늘 승인: {approved_today}건\n"
            f"❌ 오늘 거부: {rejected_today}건\n\n"
            f"🏛️ 헌법: 활성\n"
            f"🛡️ Shield Report: 가동 중",
            parse_mode='Markdown'
        )
    
    async def cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """대기 중인 제안 조회"""
        pending = self.db.query(Proposal).filter(
            Proposal.status == 'PENDING'
        ).order_by(Proposal.created_at.desc()).limit(5).all()
        
        if not pending:
            await update.message.reply_text("대기 중인 제안이 없습니다. ✅")
            return
        
        message = f"⏳ *대기 중인 제안* ({len(pending)}건)\n\n"
        
        for p in pending:
            age = (datetime.utcnow() - p.created_at).total_seconds() / 60
            message += (
                f"{p.get_action_emoji()} *{p.ticker}* {p.action}\n"
                f"  가격: ${p.target_price:.2f}\n"
                f"  신뢰도: {p.confidence:.0%}\n"
                f"  대기: {age:.0f}분\n\n"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def send_proposal(
        self,
        proposal: Proposal,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        제안 전송
        
        Args:
            proposal: 제안 객체
            chat_id: Chat ID (None이면 기본 Commander)
        
        Returns:
            전송 성공 여부
        """
        target_chat_id = chat_id or self.commander_chat_id
        
        if not target_chat_id:
            logger.error("Commander Chat ID가 설정되지 않았습니다")
            return False
        
        # 메시지 구성
        message = self._format_proposal_message(proposal)
        
        # 버튼 구성
        keyboard = self._create_approval_keyboard(proposal.id)
        
        try:
            # 메시지 전송
            sent_message = await self.application.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # 메시지 ID 저장
            proposal.telegram_message_id = str(sent_message.message_id)
            self.db.commit()
            
            logger.info(f"📤 제안 전송: {proposal.ticker} {proposal.action} to {target_chat_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"제안 전송 실패: {e}")
            return False
    
    def _format_proposal_message(self, proposal: Proposal) -> str:
        """제안 메시지 포맷"""
        # 헌법 상태
        constitutional_status = "✅ 헌법 준수" if proposal.is_constitutional else "⚠️ 헌법 경고"
        
        if not proposal.is_constitutional and proposal.violated_articles:
            constitutional_status += f"\n위반 조항: {proposal.violated_articles}"
        
        message = (
            f"🎯 *새로운 제안이 상정되었습니다*\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{proposal.get_action_emoji()} *{proposal.action}: {proposal.ticker}*\n\n"
            f"📍 목표 가격: ${proposal.target_price:.2f}\n"
            f"💰 주문 금액: ${proposal.order_value_usd:,.0f}\n"
            f"📊 포지션: {proposal.position_size:.1%}\n\n"
            f"🤖 *AI 분석*\n"
            f"신뢰도: {proposal.confidence:.0%}\n"
            f"합의 수준: {proposal.consensus_level:.0%}\n\n"
        )
        
        if proposal.reasoning:
            reasoning_short = proposal.reasoning[:200] + "..." if len(proposal.reasoning) > 200 else proposal.reasoning
            message += f"💬 근거:\n{reasoning_short}\n\n"
        
        message += (
            f"🏛️ *헌법 검증*\n"
            f"{constitutional_status}\n\n"
        )
        
        if proposal.market_regime:
            message += f"🌍 시장 체제: {proposal.market_regime}\n"
        
        if proposal.vix:
            message += f"📈 VIX: {proposal.vix:.1f}\n"
        
        message += (
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ 제안 시각: {proposal.created_at.strftime('%H:%M:%S')}\n\n"
            f"*헌법 제3조*: 최종 실행권은 Commander에게 있습니다."
        )
        
        return message
    
    def _create_approval_keyboard(self, proposal_id: str) -> InlineKeyboardMarkup:
        """승인/거부 버튼 생성"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ 승인 (Approve)",
                    callback_data=f"approve:{proposal_id}"
                ),
                InlineKeyboardButton(
                    "❌ 거부 (Reject)",
                    callback_data=f"reject:{proposal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 상세 보기",
                    callback_data=f"detail:{proposal_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_approval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """승인/거부 버튼 처리"""
        query = update.callback_query
        await query.answer()
        
        # Callback data 파싱
        action, proposal_id = query.data.split(':', 1)
        
        # Proposal 조회
        proposal = self.db.query(Proposal).filter(
            Proposal.id == proposal_id
        ).first()
        
        if not proposal:
            await query.edit_message_text("❌ 제안을 찾을 수 없습니다.")
            return
        
        # 이미 처리됨
        if proposal.status != 'PENDING':
            await query.edit_message_text(
                f"{proposal.get_status_emoji()} 이미 처리된 제안입니다: {proposal.status}"
            )
            return
        
        # 액션 처리
        username = query.from_user.username or query.from_user.first_name
        
        if action == 'approve':
            await self._handle_approve(query, proposal, username)
        
        elif action == 'reject':
            await self._handle_reject(query, proposal, username)
        
        elif action == 'detail':
            await self._handle_detail(query, proposal)
    
    async def _handle_approve(self, query, proposal: Proposal, username: str):
        """승인 처리"""
        proposal.approve(username)
        self.db.commit()
        
        logger.info(f"✅ 제안 승인: {proposal.ticker} {proposal.action} by {username}")
        
        message = (
            f"✅ *제안 승인됨*\n\n"
            f"{proposal.ticker} {proposal.action}\n"
            f"승인자: @{username}\n"
            f"승인 시각: {proposal.approved_at.strftime('%H:%M:%S')}\n\n"
            f"🚀 주문 실행 준비 중..."
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def _handle_reject(self, query, proposal: Proposal, username: str):
        """거부 처리"""
        reason = "Commander 거부"
        proposal.reject(reason, username)
        self.db.commit()
        
        logger.info(f"❌ 제안 거부: {proposal.ticker} {proposal.action} by {username}")
        
        # Shadow Trade 생성
        if self.shadow_tracker:
            try:
                shadow_proposal = {
                    'ticker': proposal.ticker,
                    'action': proposal.action,
                    'entry_price': proposal.target_price,
                    'shares': proposal.shares
                }
                
                shadow = self.shadow_tracker.create_shadow_trade(
                    proposal=shadow_proposal,
                    rejection_reason=reason,
                    violated_articles=[],
                    tracking_days=7
                )
                
                logger.info(f"🛡️ Shadow Trade 생성: {shadow.id}")
            
            except Exception as e:
                logger.error(f"Shadow Trade 생성 실패: {e}")
        
        message = (
            f"❌ *제안 거부됨*\n\n"
            f"{proposal.ticker} {proposal.action}\n"
            f"거부자: @{username}\n"
            f"거부 시각: {proposal.rejected_at.strftime('%H:%M:%S')}\n\n"
            f"🛡️ Shadow Trade 추적 시작\n"
            f"(방어 성과 측정 중)"
        )
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def _handle_detail(self, query, proposal: Proposal):
        """상세 정보 표시"""
        detail = (
            f"📊 *제안 상세 정보*\n\n"
            f"ID: `{proposal.id}`\n"
            f"Ticker: {proposal.ticker}\n"
            f"Action: {proposal.action}\n\n"
            f"AI Debate 요약:\n"
        )
        
        if proposal.debate_summary:
            detail += f"{proposal.debate_summary[:300]}...\n"
        
        if proposal.model_votes:
            detail += f"\nModel Votes:\n{proposal.model_votes}\n"
        
        await query.message.reply_text(detail, parse_mode='Markdown')
    
    async def start_polling(self):
        """봇 시작 (Polling)"""
        logger.info("🤖 Telegram Bot 시작 (Polling)...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
    
    async def stop(self):
        """봇 중지"""
        logger.info("🤖 Telegram Bot 중지...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()


if __name__ == "__main__":
    print("=== Telegram Commander Bot ===\n")
    
    print("이 모듈은 DB 세션과 Bot Token이 필요합니다.")
    print("\n환경 변수:")
    print("  TELEGRAM_BOT_TOKEN")
    print("  TELEGRAM_COMMANDER_CHAT_ID")
    
    print("\n사용 예시:\n")
    print("""
    bot = TelegramCommanderBot(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        db_session=db,
        commander_chat_id=os.getenv('TELEGRAM_COMMANDER_CHAT_ID')
    )
    
    # 제안 전송
    await bot.send_proposal(proposal)
    
    # 봇 시작
    await bot.start_polling()
    """)
    
    print("\n✅ Telegram Commander Bot 구현 완료!")
