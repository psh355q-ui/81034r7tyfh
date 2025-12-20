"""
Alert System - Telegram & Slack Integration

High-confidence trading signals를 실시간으로 알림

Features:
- Telegram bot notifications
- Slack webhook integration
- Email alerts (SMTP)
- Signal filtering (confidence threshold)
- Rate limiting (avoid spam)
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class TradingSignal:
    """Trading signal data"""
    ticker: str
    action: str  # BUY, SELL, TRIM, HOLD
    signal_type: str  # PRIMARY, HIDDEN, LOSER
    confidence: float
    reasoning: str
    news_title: str
    timestamp: datetime


class AlertSystem:
    """
    통합 알림 시스템

    지원하는 알림 채널:
    - Telegram
    - Slack
    - Email

    Usage:
        alert_system = AlertSystem(
            telegram_bot_token="...",
            telegram_chat_id="...",
            slack_webhook_url="..."
        )
        await alert_system.send_signal_alert(signal)
    """

    def __init__(
        self,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        smtp_config: Optional[Dict] = None,
        confidence_threshold: float = 0.85,
        rate_limit_seconds: int = 300  # 5분당 최대 알림 수
    ):
        """
        Args:
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat/channel ID
            slack_webhook_url: Slack incoming webhook URL
            smtp_config: Email 설정 {host, port, username, password, from_email, to_emails}
            confidence_threshold: 알림 전송 최소 신뢰도
            rate_limit_seconds: Rate limiting 간격
        """
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.slack_webhook_url = slack_webhook_url
        self.smtp_config = smtp_config or {}
        self.confidence_threshold = confidence_threshold
        self.rate_limit_seconds = rate_limit_seconds

        # Rate limiting
        self.last_alert_times: Dict[str, datetime] = {}

    def _should_send_alert(self, signal: TradingSignal) -> bool:
        """
        알림 전송 여부 판단

        조건:
        1. Confidence >= threshold
        2. Rate limit 통과 (같은 ticker는 N분에 1회만)
        """
        # Confidence check
        if signal.confidence < self.confidence_threshold:
            return False

        # Rate limit check
        key = f"{signal.ticker}_{signal.signal_type}"
        last_time = self.last_alert_times.get(key)

        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < self.rate_limit_seconds:
                return False

        # 통과
        self.last_alert_times[key] = datetime.now()
        return True

    def _format_signal_message(self, signal: TradingSignal, format_type: str = "telegram") -> str:
        """
        Signal을 메시지 포맷으로 변환

        Args:
            format_type: "telegram", "slack", "email"
        """
        emoji_map = {
            "PRIMARY": "🎯",
            "HIDDEN": "⭐",
            "LOSER": "⚠️",
            "BUY": "📈",
            "SELL": "📉",
            "TRIM": "✂️",
            "HOLD": "🔒"
        }

        if format_type == "telegram":
            return f"""
{emoji_map.get(signal.signal_type, '')} *{signal.signal_type} SIGNAL* {emoji_map.get(signal.signal_type, '')}

💼 *Ticker*: {signal.ticker}
{emoji_map.get(signal.action, '')} *Action*: {signal.action}
📊 *Confidence*: {signal.confidence:.0%}

📰 *News*: {signal.news_title}

💡 *Reasoning*:
{signal.reasoning[:200]}...

⏰ {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

        elif format_type == "slack":
            return {
                "text": f"{signal.signal_type} Signal: {signal.ticker} {signal.action}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji_map.get(signal.signal_type, '')} {signal.signal_type} SIGNAL"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Ticker:*\n{signal.ticker}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Action:*\n{signal.action}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Confidence:*\n{signal.confidence:.0%}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Type:*\n{signal.signal_type}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*News:* {signal.news_title}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Reasoning:*\n{signal.reasoning[:200]}..."
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Generated at {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }

        elif format_type == "email":
            return f"""
<html>
<body>
<h2>{signal.signal_type} SIGNAL</h2>
<table>
<tr><td><strong>Ticker:</strong></td><td>{signal.ticker}</td></tr>
<tr><td><strong>Action:</strong></td><td>{signal.action}</td></tr>
<tr><td><strong>Confidence:</strong></td><td>{signal.confidence:.0%}</td></tr>
<tr><td><strong>Type:</strong></td><td>{signal.signal_type}</td></tr>
</table>
<h3>News</h3>
<p>{signal.news_title}</p>
<h3>Reasoning</h3>
<p>{signal.reasoning}</p>
<p><em>Generated at {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</em></p>
</body>
</html>
"""

    async def send_telegram(self, signal: TradingSignal) -> bool:
        """Telegram으로 알림 전송"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            message = self._format_signal_message(signal, "telegram")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }) as response:
                    return response.status == 200

        except Exception as e:
            print(f"[ERROR] Telegram alert failed: {e}")
            return False

    async def send_slack(self, signal: TradingSignal) -> bool:
        """Slack으로 알림 전송"""
        if not self.slack_webhook_url:
            return False

        try:
            message = self._format_signal_message(signal, "slack")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=message
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"[ERROR] Slack alert failed: {e}")
            return False

    def send_email(self, signal: TradingSignal) -> bool:
        """Email로 알림 전송 (동기)"""
        if not self.smtp_config.get('host'):
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[AI Trading] {signal.signal_type}: {signal.ticker} {signal.action}"
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])

            html_content = self._format_signal_message(signal, "email")
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(
                self.smtp_config['host'],
                self.smtp_config.get('port', 587)
            ) as server:
                server.starttls()
                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"[ERROR] Email alert failed: {e}")
            return False

    async def send_signal_alert(self, signal: TradingSignal) -> Dict[str, bool]:
        """
        모든 활성화된 채널로 알림 전송

        Returns:
            Dict with channel: success mapping
        """
        # Check if should send
        if not self._should_send_alert(signal):
            return {'skipped': True}

        results = {}

        # Send to all channels
        if self.telegram_bot_token:
            results['telegram'] = await self.send_telegram(signal)

        if self.slack_webhook_url:
            results['slack'] = await self.send_slack(signal)

        if self.smtp_config.get('host'):
            # Email은 동기이므로 executor에서 실행
            loop = asyncio.get_event_loop()
            results['email'] = await loop.run_in_executor(
                None,
                self.send_email,
                signal
            )

        return results


# ============================================
# Alert Manager (Batch Processing)
# ============================================

class AlertManager:
    """
    여러 signal을 배치로 처리하는 매니저

    Usage:
        manager = AlertManager(alert_system)
        await manager.process_signals(signals_list)
    """

    def __init__(self, alert_system: AlertSystem):
        self.alert_system = alert_system
        self.sent_count = 0
        self.failed_count = 0

    async def process_signals(self, signals: List[TradingSignal]) -> Dict:
        """
        여러 signal을 한번에 처리

        Args:
            signals: TradingSignal 리스트

        Returns:
            처리 결과 통계
        """
        print(f"\n[AlertManager] Processing {len(signals)} signals...")

        for i, signal in enumerate(signals, 1):
            print(f"  [{i}/{len(signals)}] {signal.ticker} {signal.action} ({signal.confidence:.0%})")

            results = await self.alert_system.send_signal_alert(signal)

            if results.get('skipped'):
                print(f"    → Skipped (threshold or rate limit)")
                continue

            success = any(results.values())
            if success:
                self.sent_count += 1
                print(f"    → Sent via: {', '.join([k for k, v in results.items() if v])}")
            else:
                self.failed_count += 1
                print(f"    → Failed to send")

        return {
            'total': len(signals),
            'sent': self.sent_count,
            'failed': self.failed_count
        }


# ============================================
# Demo & Testing
# ============================================

async def demo():
    """Alert system 데모"""
    print("=" * 80)
    print("Alert System Demo")
    print("=" * 80)

    # Mock signal
    signal = TradingSignal(
        ticker="NVDA",
        action="BUY",
        signal_type="HIDDEN",
        confidence=0.90,
        reasoning="Google TPU v6 announcement → Nvidia supplies GPU alternatives → "
                  "Hidden beneficiary through datacenter infrastructure demand",
        news_title="Google announces TPU v6 with major cloud partners",
        timestamp=datetime.now()
    )

    # Alert system (without real credentials for demo)
    alert_system = AlertSystem(
        confidence_threshold=0.85
    )

    print("\n[TEST] Checking if alert should be sent...")
    should_send = alert_system._should_send_alert(signal)
    print(f"  Should send: {should_send}")

    print("\n[TEST] Formatting messages...")

    # Telegram format
    print("\n--- Telegram Format ---")
    telegram_msg = alert_system._format_signal_message(signal, "telegram")
    print(telegram_msg)

    # Slack format
    print("\n--- Slack Format (JSON) ---")
    slack_msg = alert_system._format_signal_message(signal, "slack")
    import json
    print(json.dumps(slack_msg, indent=2))

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nTo enable real alerts, set:")
    print("  - TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID")
    print("  - SLACK_WEBHOOK_URL")
    print("  - SMTP settings (host, port, username, password)")


if __name__ == "__main__":
    asyncio.run(demo())
