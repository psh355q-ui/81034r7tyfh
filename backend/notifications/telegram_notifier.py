"""
Telegram Bot Notification System for AI Trading System

Features:
- Trading signal alerts (BUY/SELL/HOLD)
- Risk warnings (CRITICAL, HIGH)
- Paper trading performance reports
- System health alerts
- Daily/Weekly summaries

Author: AI Trading System
Date: 2025-11-15
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Alert priority levels"""
    CRITICAL = "🚨"      # System failures, kill switch
    HIGH = "⚠️"          # Risk warnings, large losses
    MEDIUM = "📊"        # Trading signals
    LOW = "ℹ️"           # Info, daily reports
    SUCCESS = "✅"       # Successful trades


class AlertPriority(Enum):
    """Alert priority levels (compatible with smart_alerts)"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TelegramNotifier:
    """
    Telegram Bot notification system for AI Trading alerts.
    
    Usage:
        notifier = TelegramNotifier(bot_token, chat_id)
        await notifier.send_trade_alert(decision)
        await notifier.send_daily_report(portfolio)
    """
    
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool = True,
        rate_limit_per_minute: int = 20,
        min_priority: Optional['AlertPriority'] = None,
        throttle_minutes: int = 5,
    ):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram Bot API token from @BotFather
            chat_id: Chat ID to send messages (user or group)
            enabled: Enable/disable notifications
            rate_limit_per_minute: Max messages per minute
            min_priority: Minimum priority level to send (defaults to NORMAL)
            throttle_minutes: Message throttle window in minutes
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.rate_limit = rate_limit_per_minute
        self.min_priority = min_priority or AlertPriority.MEDIUM
        self.throttle_minutes = throttle_minutes
        
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Rate limiting
        self._message_times: List[datetime] = []
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "failed": 0,
            "rate_limited": 0,
        }
        
        logger.info(f"TelegramNotifier initialized (enabled={enabled})")
    
    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limit"""
        now = datetime.now()
        # Remove messages older than 1 minute
        self._message_times = [
            t for t in self._message_times
            if (now - t).total_seconds() < 60
        ]
        
        if len(self._message_times) >= self.rate_limit:
            self.stats["rate_limited"] += 1
            logger.warning(f"Rate limit reached ({self.rate_limit}/min)")
            return False
        
        return True
    
    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a message via Telegram.
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: "HTML" or "Markdown"
            disable_notification: Silent message
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Notifications disabled, skipping")
            return False
        
        if not await self._check_rate_limit():
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self._message_times.append(datetime.now())
                        self.stats["total_sent"] += 1
                        logger.info(f"Telegram message sent (total: {self.stats['total_sent']})")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error: {response.status} - {error_text}")
                        self.stats["failed"] += 1
                        return False
        
        except asyncio.TimeoutError:
            logger.error("Telegram API timeout")
            self.stats["failed"] += 1
            return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            self.stats["failed"] += 1
            return False
    
    async def send_file(
        self,
        file_path: str,
        caption: Optional[str] = None,
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a file (document) via Telegram.
        
        Args:
            file_path: Path to the file to send
            caption: Optional caption for the file
            disable_notification: Silent message
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
            
        if not await self._check_rate_limit():
            return False
            
        try:
            url = f"{self.base_url}/sendDocument"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', self.chat_id)
            if caption:
                data.add_field('caption', caption)
            if disable_notification:
                data.add_field('disable_notification', 'true')
                
            # Open file and add to form data
            f = open(file_path, 'rb')
            # Extract filename regardless of OS path separator
            filename = file_path.replace('\\', '/').split('/')[-1]
            data.add_field('document', f, filename=filename)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=30) as response:
                    f.close() # Close file after request
                    
                    if response.status == 200:
                        self._message_times.append(datetime.now())
                        self.stats["total_sent"] += 1
                        logger.info(f"Telegram file sent: {file_path}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error (sendDocument): {response.status} - {error_text}")
                        self.stats["failed"] += 1
                        return False
                        
        except Exception as e:
            logger.error(f"Telegram file send error: {e}")
            self.stats["failed"] += 1
            return False

    # ==================== Trading Alerts ====================
    
    async def send_trade_signal(
        self,
        ticker: str,
        action: str,
        conviction: float,
        reasoning: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        position_size: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> bool:
        """
        Send trading signal alert.
        
        Args:
            ticker: Stock symbol
            action: BUY/SELL/HOLD
            conviction: 0-1 confidence score
            reasoning: AI reasoning
            target_price: Target price
            stop_loss: Stop loss price
            position_size: Position size %
            current_price: Current stock price
        """
        # Emoji based on action
        if action == "BUY":
            emoji = "🟢"
            alert_type = AlertType.MEDIUM
        elif action == "SELL":
            emoji = "🔴"
            alert_type = AlertType.MEDIUM
        else:  # HOLD
            emoji = "⚪"
            alert_type = AlertType.LOW
        
        # Build message
        lines = [
            f"<b>{emoji} {action} Signal: ${ticker}</b>",
            f"",
            f"<b>Conviction:</b> {conviction:.1%}",
        ]
        
        if current_price:
            lines.append(f"<b>Current Price:</b> ${current_price:.2f}")
        
        if target_price and action == "BUY":
            lines.append(f"<b>Target Price:</b> ${target_price:.2f}")
            if current_price:
                upside = ((target_price - current_price) / current_price) * 100
                lines.append(f"<b>Upside:</b> {upside:.1f}%")
        
        if stop_loss:
            lines.append(f"<b>Stop Loss:</b> ${stop_loss:.2f}")
            if current_price:
                downside = ((current_price - stop_loss) / current_price) * 100
                lines.append(f"<b>Risk:</b> {downside:.1f}%")
        
        if position_size:
            lines.append(f"<b>Position Size:</b> {position_size:.1f}% of portfolio")
        
        lines.extend([
            f"",
            f"<b>Reasoning:</b>",
            f"<i>{reasoning[:500]}{'...' if len(reasoning) > 500 else ''}</i>",
            f"",
            f"<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>",
        ])
        
        message = "\n".join(lines)
        
        return await self.send_message(
            message,
            disable_notification=(action == "HOLD"),
        )
    
    async def send_risk_alert(
        self,
        ticker: str,
        risk_type: str,
        risk_score: float,
        risk_factors: List[str],
        action_taken: str,
    ) -> bool:
        """
        Send risk warning alert.
        
        Args:
            ticker: Stock symbol
            risk_type: CRITICAL/HIGH/MODERATE
            risk_score: 0-1 risk score
            risk_factors: List of risk factors
            action_taken: What action was taken
        """
        if risk_score >= 0.6:
            emoji = "🚨"
            level = "CRITICAL"
        elif risk_score >= 0.3:
            emoji = "⚠️"
            level = "HIGH"
        else:
            emoji = "📝"
            level = "MODERATE"
        
        factors_text = "\n".join([f"  • {f}" for f in risk_factors[:5]])
        
        message = f"""
<b>{emoji} RISK ALERT: ${ticker}</b>

<b>Risk Level:</b> {level}
<b>Risk Score:</b> {risk_score:.2f}
<b>Type:</b> {risk_type}

<b>Risk Factors:</b>
{factors_text}

<b>Action Taken:</b> {action_taken}

<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>
""".strip()
        
        return await self.send_message(message)
    
    async def send_execution_report(
        self,
        ticker: str,
        side: str,  # BUY/SELL
        quantity: int,
        avg_price: float,
        total_value: float,
        algorithm: str,  # TWAP/VWAP
        slippage_bps: Optional[float] = None,
        commission: Optional[float] = None,
    ) -> bool:
        """
        Send order execution report.
        """
        emoji = "📈" if side == "BUY" else "📉"
        
        lines = [
            f"<b>{emoji} Order Executed: ${ticker}</b>",
            f"",
            f"<b>Side:</b> {side}",
            f"<b>Quantity:</b> {quantity:,}",
            f"<b>Avg Price:</b> ${avg_price:.2f}",
            f"<b>Total Value:</b> ${total_value:,.2f}",
            f"<b>Algorithm:</b> {algorithm}",
        ]
        
        if slippage_bps is not None:
            lines.append(f"<b>Slippage:</b> {slippage_bps:.2f} bps")
        
        if commission is not None:
            lines.append(f"<b>Commission:</b> ${commission:.2f}")
        
        lines.extend([
            f"",
            f"<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>",
        ])
        
        return await self.send_message("\n".join(lines))
    
    # ==================== Portfolio Reports ====================
    
    async def send_daily_report(
        self,
        portfolio_value: float,
        daily_pnl: float,
        daily_pnl_pct: float,
        total_return_pct: float,
        positions: List[Dict[str, Any]],
        cash: float,
        trades_today: int = 0,
    ) -> bool:
        """
        Send daily portfolio summary.
        """
        # Overall performance emoji
        if daily_pnl_pct >= 1.0:
            emoji = "🚀"
        elif daily_pnl_pct >= 0:
            emoji = "📈"
        elif daily_pnl_pct >= -1.0:
            emoji = "📉"
        else:
            emoji = "🔻"
        
        # Top positions
        top_positions = ""
        if positions:
            sorted_pos = sorted(positions, key=lambda x: x.get("value", 0), reverse=True)[:5]
            pos_lines = []
            for pos in sorted_pos:
                ticker = pos.get("ticker", "???")
                value = pos.get("value", 0)
                pnl_pct = pos.get("pnl_pct", 0)
                pnl_emoji = "🟢" if pnl_pct >= 0 else "🔴"
                pos_lines.append(f"  {pnl_emoji} ${ticker}: ${value:,.0f} ({pnl_pct:+.1f}%)")
            top_positions = "\n".join(pos_lines)
        else:
            top_positions = "  No positions"
        
        message = f"""
<b>{emoji} Daily Report - {datetime.now().strftime('%Y-%m-%d')}</b>

<b>Portfolio Value:</b> ${portfolio_value:,.2f}
<b>Daily P&amp;L:</b> ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%)
<b>Total Return:</b> {total_return_pct:+.2f}%

<b>Top Positions:</b>
{top_positions}

<b>Cash Available:</b> ${cash:,.2f}
<b>Trades Today:</b> {trades_today}

<code>Generated at {datetime.now().strftime('%H:%M:%S')}</code>
""".strip()
        
        return await self.send_message(message)
    
    async def send_weekly_report(
        self,
        start_value: float,
        end_value: float,
        weekly_return_pct: float,
        sharpe_ratio: float,
        max_drawdown_pct: float,
        win_rate: float,
        total_trades: int,
        best_trade: Dict[str, Any],
        worst_trade: Dict[str, Any],
    ) -> bool:
        """
        Send weekly performance summary.
        """
        if weekly_return_pct >= 2.0:
            emoji = "🏆"
        elif weekly_return_pct >= 0:
            emoji = "📊"
        else:
            emoji = "📉"
        
        message = f"""
<b>{emoji} Weekly Report</b>
<b>{datetime.now().strftime('%Y-%m-%d')}</b>

<b>Performance:</b>
  Start: ${start_value:,.2f}
  End: ${end_value:,.2f}
  Return: {weekly_return_pct:+.2f}%

<b>Risk Metrics:</b>
  Sharpe Ratio: {sharpe_ratio:.2f}
  Max Drawdown: {max_drawdown_pct:.2f}%

<b>Trading Stats:</b>
  Total Trades: {total_trades}
  Win Rate: {win_rate:.1f}%

<b>Best Trade:</b>
  ${best_trade.get('ticker', 'N/A')}: {best_trade.get('return_pct', 0):+.2f}%

<b>Worst Trade:</b>
  ${worst_trade.get('ticker', 'N/A')}: {worst_trade.get('return_pct', 0):+.2f}%

<code>Generated at {datetime.now().strftime('%H:%M:%S')}</code>
""".strip()
        
        return await self.send_message(message)
    
    # ==================== System Alerts ====================
    
    async def send_system_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        action_required: Optional[str] = None,
    ) -> bool:
        """
        Send system health/error alert.
        """
        lines = [
            f"<b>{alert_type.value} {title}</b>",
            f"",
            message,
        ]
        
        if action_required:
            lines.extend([
                f"",
                f"<b>Action Required:</b> {action_required}",
            ])
        
        lines.extend([
            f"",
            f"<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>",
        ])
        
        full_message = "\n".join(lines)
        
        # Don't silence critical alerts
        silent = alert_type in [AlertType.LOW, AlertType.SUCCESS]
        
        return await self.send_message(full_message, disable_notification=silent)
    
    async def send_kill_switch_alert(
        self,
        reason: str,
        daily_loss_pct: float,
        threshold_pct: float,
    ) -> bool:
        """
        Send kill switch activation alert.
        """
        message = f"""
<b>🚨🚨🚨 KILL SWITCH ACTIVATED 🚨🚨🚨</b>

<b>Reason:</b> {reason}
<b>Daily Loss:</b> {daily_loss_pct:.2f}%
<b>Threshold:</b> {threshold_pct:.2f}%

<b>ALL TRADING HAS BEEN STOPPED</b>

Manual intervention required to resume trading.

<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>
""".strip()
        
        return await self.send_message(message)
    
    async def send_startup_message(
        self,
        version: str = "1.0.0",
        mode: str = "Paper Trading",
    ) -> bool:
        """
        Send system startup notification.
        """
        message = f"""
<b>🤖 AI Trading System Started</b>

<b>Version:</b> {version}
<b>Mode:</b> {mode}
<b>Status:</b> ✅ Online

<b>Features:</b>
  • Multi-AI Ensemble (Claude + ChatGPT + Gemini)
  • Constitution Rules Active
  • Smart Execution (TWAP/VWAP)
  • Risk Management Active

Ready to receive trading signals.

<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>
""".strip()
        
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """
        Test bot connection by sending a test message.
        """
        return await self.send_message(
            "🔔 <b>Test Connection</b>\n\n"
            "AI Trading System notification test successful!\n\n"
            f"<code>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get notification statistics"""
        return self.stats.copy()


# Convenience function for quick notifications
async def send_quick_alert(
    bot_token: str,
    chat_id: str,
    message: str,
) -> bool:
    """
    Send a quick one-off notification.
    
    Usage:
        await send_quick_alert(token, chat_id, "Test message")
    """
    notifier = TelegramNotifier(bot_token, chat_id)
    return await notifier.send_message(message)


def create_telegram_notifier(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    enabled: bool = True,
    min_priority: AlertPriority = AlertPriority.HIGH
) -> Optional[TelegramNotifier]:
    """
    Factory function to create TelegramNotifier instance.

    Args:
        bot_token: Telegram bot token (from environment if not provided)
        chat_id: Telegram chat ID (from environment if not provided)
        enabled: Whether notifications are enabled
        min_priority: Minimum priority level for notifications

    Returns:
        TelegramNotifier instance or None if credentials not available
    """
    import os

    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        logger.warning("Telegram credentials not configured")
        return None

    return TelegramNotifier(
        bot_token=token,
        chat_id=chat,
        enabled=enabled
    )