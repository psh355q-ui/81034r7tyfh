"""
SEC Alert Notifications

SEC 모니터링 알림을 Telegram/Slack으로 전송

Author: AI Trading System
Date: 2025-11-21
Phase: 14
"""

import os
import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


# ============================================================================
# Alert Formatters
# ============================================================================

def format_sec_alert_telegram(alert) -> str:
    """
    Telegram 형식으로 알림 포맷팅
    
    Args:
        alert: SECAlert 객체
        
    Returns:
        포맷된 메시지
    """
    # Severity에 따른 이모지
    emoji_map = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "WARNING": "⚡",
        "INFO": "ℹ️"
    }
    
    emoji = emoji_map.get(alert.severity, "📄")
    
    # 메시지 구성
    msg = f"{emoji} **SEC Alert: {alert.severity}**\n\n"
    msg += f"**Ticker:** {alert.ticker}\n"
    msg += f"**Form:** {alert.form_type}\n"
    msg += f"**Type:** {alert.alert_type}\n"
    msg += f"**Reason:** {alert.reason}\n\n"
    
    # 추가 정보
    if alert.metadata:
        if 'red_flags' in alert.metadata:
            flags = alert.metadata['red_flags'][:3]  # 상위 3개만
            msg += f"**Red Flags:** {', '.join(flags)}\n"
        
        if 'total_value' in alert.metadata:
            value = alert.metadata['total_value']
            msg += f"**Trade Value:** ${value:,.0f}\n"
        
        if 'insider_name' in alert.metadata:
            msg += f"**Insider:** {alert.metadata['insider_name']}\n"
    
    # URL
    msg += f"\n[View Filing]({alert.filing.filing_url})"
    
    # 타임스탬프
    msg += f"\n\n_Filed: {alert.filing.filing_date.strftime('%Y-%m-%d %H:%M UTC')}_"
    
    return msg


def format_sec_alert_slack(alert) -> dict:
    """
    Slack 형식으로 알림 포맷팅
    
    Args:
        alert: SECAlert 객체
        
    Returns:
        Slack 메시지 페이로드
    """
    # Severity에 따른 색상
    color_map = {
        "CRITICAL": "#d32f2f",  # Red
        "HIGH": "#f57c00",      # Orange
        "WARNING": "#fbc02d",   # Yellow
        "INFO": "#1976d2"       # Blue
    }
    
    color = color_map.get(alert.severity, "#757575")
    
    # Slack Attachment
    attachment = {
        "color": color,
        "title": f"SEC Alert: {alert.ticker} - {alert.form_type}",
        "title_link": alert.filing.filing_url,
        "text": alert.reason,
        "fields": [
            {
                "title": "Severity",
                "value": alert.severity,
                "short": True
            },
            {
                "title": "Alert Type",
                "value": alert.alert_type,
                "short": True
            },
            {
                "title": "Company",
                "value": alert.filing.company_name,
                "short": True
            },
            {
                "title": "Filed",
                "value": alert.filing.filing_date.strftime('%Y-%m-%d %H:%M'),
                "short": True
            }
        ],
        "footer": "AI Trading System - SEC Monitor",
        "ts": int(alert.timestamp.timestamp())
    }
    
    # 추가 필드
    if alert.metadata:
        if 'red_flags' in alert.metadata:
            flags = alert.metadata['red_flags'][:5]
            attachment['fields'].append({
                "title": "Red Flags",
                "value": ", ".join(flags),
                "short": False
            })
        
        if 'total_value' in alert.metadata:
            value = alert.metadata['total_value']
            attachment['fields'].append({
                "title": "Trade Value",
                "value": f"${value:,.0f}",
                "short": True
            })
    
    return {
        "text": f"🚨 SEC Filing Alert: {alert.ticker}",
        "attachments": [attachment]
    }


# ============================================================================
# Notification Senders
# ============================================================================

async def send_telegram_alert(message: str) -> bool:
    """
    Telegram으로 알림 전송
    
    Args:
        message: 전송할 메시지
        
    Returns:
        성공 여부
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info("Telegram alert sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Telegram send failed: {response.status} - {error_text}")
                    return False
    
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return False


async def send_slack_alert(payload: dict) -> bool:
    """
    Slack으로 알림 전송
    
    Args:
        payload: Slack 메시지 페이로드
        
    Returns:
        성공 여부
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured")
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    logger.info("Slack alert sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Slack send failed: {response.status} - {error_text}")
                    return False
    
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        return False


async def send_sec_alert(alert) -> dict:
    """
    SEC 알림을 모든 채널로 전송
    
    Args:
        alert: SECAlert 객체
        
    Returns:
        전송 결과
    """
    results = {
        "telegram": False,
        "slack": False
    }
    
    # Severity 필터링 (INFO는 너무 많으므로 제외)
    if alert.severity == "INFO":
        logger.debug(f"Skipping INFO alert for {alert.ticker}")
        return results
    
    # Telegram 전송
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_msg = format_sec_alert_telegram(alert)
        results["telegram"] = await send_telegram_alert(telegram_msg)
    
    # Slack 전송
    if SLACK_WEBHOOK_URL:
        slack_payload = format_sec_alert_slack(alert)
        results["slack"] = await send_slack_alert(slack_payload)
    
    # 로깅
    channels_sent = [ch for ch, success in results.items() if success]
    if channels_sent:
        logger.info(
            f"SEC alert sent to {', '.join(channels_sent)}: "
            f"{alert.ticker} {alert.form_type} ({alert.severity})"
        )
    else:
        logger.warning(f"Failed to send SEC alert for {alert.ticker}")
    
    return results


# ============================================================================
# Test Functions
# ============================================================================

async def test_telegram_connection():
    """Telegram 연결 테스트"""
    test_msg = "🧪 **SEC Monitor Test**\n\nThis is a test message from AI Trading System."
    
    success = await send_telegram_alert(test_msg)
    
    if success:
        print("✅ Telegram connection successful!")
    else:
        print("❌ Telegram connection failed. Check credentials.")
    
    return success


async def test_slack_connection():
    """Slack 연결 테스트"""
    test_payload = {
        "text": "🧪 SEC Monitor Test",
        "attachments": [{
            "color": "#1976d2",
            "text": "This is a test message from AI Trading System.",
            "footer": "AI Trading System - SEC Monitor"
        }]
    }
    
    success = await send_slack_alert(test_payload)
    
    if success:
        print("✅ Slack connection successful!")
    else:
        print("❌ Slack connection failed. Check webhook URL.")
    
    return success


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Testing notification channels...\n")
        
        # Telegram 테스트
        print("1. Testing Telegram...")
        await test_telegram_connection()
        
        print("\n2. Testing Slack...")
        await test_slack_connection()
    
    asyncio.run(main())
