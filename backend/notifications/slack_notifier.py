"""
Slack Webhook Notification System for AI Trading System

Features:
- Rich Block Kit formatting
- News sentiment alerts
- Trading signal notifications
- Color-coded priority levels
- Interactive buttons (view article, approve signal)

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import aiohttp

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack Incoming Webhook notification system.
    
    Features:
    - Block Kit rich formatting
    - Color-coded attachments
    - Interactive action buttons
    - Rate limiting
    """
    
    def __init__(
        self,
        webhook_url: str,
        enabled: bool = True,
        rate_limit_per_minute: int = 30,
        channel_overrides: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack Incoming Webhook URL
            enabled: Enable/disable notifications
            rate_limit_per_minute: Max messages per minute
            channel_overrides: Override channels for specific priorities
                e.g., {"CRITICAL": "#trading-critical", "HIGH": "#trading-alerts"}
        """
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.rate_limit = rate_limit_per_minute
        self.channel_overrides = channel_overrides or {}
        
        # Rate limiting
        self._message_times: List[datetime] = []
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "failed": 0,
            "rate_limited": 0,
            "news_alerts": 0,
            "signal_alerts": 0,
        }
        
        logger.info(f"SlackNotifier initialized: enabled={enabled}")
    
    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limit"""
        now = datetime.now()
        self._message_times = [
            t for t in self._message_times
            if (now - t).total_seconds() < 60
        ]
        
        if len(self._message_times) >= self.rate_limit:
            self.stats["rate_limited"] += 1
            logger.warning(f"Slack rate limit reached ({self.rate_limit}/min)")
            return False
        
        return True
    
    async def send_message(
        self,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Send a message to Slack via webhook.
        
        Args:
            payload: Slack message payload (Block Kit format)
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping")
            return False
        
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        if not await self._check_rate_limit():
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10,
                ) as response:
                    if response.status == 200:
                        self._message_times.append(datetime.now())
                        self.stats["total_sent"] += 1
                        logger.info(f"Slack message sent (total: {self.stats['total_sent']})")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack webhook error: {response.status} - {error_text}")
                        self.stats["failed"] += 1
                        return False
        
        except Exception as e:
            logger.error(f"Slack send error: {e}")
            self.stats["failed"] += 1
            return False
    
    # =========================================================================
    # News Alert Methods
    # =========================================================================
    
    async def send_news_alert(
        self,
        analysis: Dict[str, Any],
        priority: str = "HIGH",
    ) -> bool:
        """
        Send news analysis alert to Slack.
        
        Args:
            analysis: NewsAnalysis data
            priority: Alert priority (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            True if sent successfully
        """
        payload = self._build_news_payload(analysis, priority)
        success = await self.send_message(payload)
        
        if success:
            self.stats["news_alerts"] += 1
        
        return success
    
    def _build_news_payload(
        self,
        analysis: Dict[str, Any],
        priority: str,
    ) -> Dict[str, Any]:
        """Build Slack Block Kit payload for news alert"""
        
        # Determine color based on sentiment and priority
        sentiment = analysis.get("sentiment_overall", "NEUTRAL")
        
        if priority == "CRITICAL":
            color = "#FF0000"  # Red
        elif sentiment == "NEGATIVE":
            color = "#FF6B6B"  # Light red
        elif sentiment == "POSITIVE":
            color = "#51CF66"  # Green
        else:
            color = "#FCC419"  # Yellow
        
        # Build blocks
        blocks = []
        
        # Header
        title = analysis.get("title", "News Alert")
        urgency = analysis.get("urgency", "MEDIUM")
        
        urgency_emoji = {
            "IMMEDIATE": "🚨",
            "HIGH": "⚡",
            "MEDIUM": "📊",
            "LOW": "ℹ️",
        }.get(urgency, "📊")
        
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{urgency_emoji} High Impact News Alert",
                "emoji": True,
            }
        })
        
        # Title section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*",
            }
        })
        
        # Metrics fields
        sentiment_score = analysis.get("sentiment_score", 0)
        impact = analysis.get("impact_magnitude", 0)
        risk = analysis.get("risk_category", "LOW")
        
        # Sentiment emoji
        if sentiment == "POSITIVE":
            sent_emoji = "🟢"
        elif sentiment == "NEGATIVE":
            sent_emoji = "🔴"
        else:
            sent_emoji = "⚪"
        
        # Risk emoji
        risk_emoji = {
            "CRITICAL": "☠️",
            "HIGH": "⚠️",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }.get(risk, "🟢")
        
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*{sent_emoji} Sentiment:*\n{sentiment} ({sentiment_score:+.2f})",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*📊 Impact:*\n{impact:.0%}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*⚡ Urgency:*\n{urgency}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*{risk_emoji} Risk:*\n{risk}",
                },
            ]
        })
        
        # Key facts
        key_facts = analysis.get("key_facts", [])
        if key_facts:
            facts_text = "\n".join(f"• {fact}" for fact in key_facts[:5])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔑 Key Facts:*\n{facts_text}",
                }
            })
        
        # Affected sectors and tickers
        context_elements = []
        
        sectors = analysis.get("affected_sectors", [])
        if sectors:
            sectors_text = ", ".join(sectors[:5])
            context_elements.append({
                "type": "mrkdwn",
                "text": f"*Sectors:* {sectors_text}",
            })
        
        tickers = analysis.get("related_tickers", [])
        if tickers:
            if isinstance(tickers[0], dict):
                ticker_symbols = [t.get("ticker_symbol", "") for t in tickers[:5]]
            else:
                ticker_symbols = tickers[:5]
            tickers_text = " ".join(f"`${t}`" for t in ticker_symbols if t)
            context_elements.append({
                "type": "mrkdwn",
                "text": f"*Tickers:* {tickers_text}",
            })
        
        if context_elements:
            blocks.append({
                "type": "context",
                "elements": context_elements,
            })
        
        # Warnings
        warnings = analysis.get("key_warnings", [])
        if warnings:
            warnings_text = "\n".join(f"⚠️ {w}" for w in warnings[:3])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Warnings:*\n{warnings_text}",
                }
            })
        
        # Action button (View Article)
        url = analysis.get("url", "")
        if url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔗 View Article",
                            "emoji": True,
                        },
                        "url": url,
                        "action_id": "view_article",
                    }
                ]
            })
        
        # Timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | AI Trading System",
                }
            ]
        })
        
        # Build final payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks,
                }
            ]
        }
        
        # Add channel override if specified
        if priority in self.channel_overrides:
            payload["channel"] = self.channel_overrides[priority]
        
        return payload
    
    async def send_trading_signal(
        self,
        signal: Dict[str, Any],
        priority: str = "HIGH",
    ) -> bool:
        """
        Send trading signal notification to Slack.
        
        Args:
            signal: TradingSignal data
            priority: Alert priority
            
        Returns:
            True if sent successfully
        """
        payload = self._build_signal_payload(signal, priority)
        success = await self.send_message(payload)
        
        if success:
            self.stats["signal_alerts"] += 1
        
        return success
    
    def _build_signal_payload(
        self,
        signal: Dict[str, Any],
        priority: str,
    ) -> Dict[str, Any]:
        """Build Slack Block Kit payload for trading signal"""
        
        action = signal.get("action", "HOLD")
        ticker = signal.get("ticker", "???")
        confidence = signal.get("confidence", 0)
        position_size = signal.get("position_size", 0)
        
        # Color based on action
        if action == "BUY":
            color = "#51CF66"  # Green
            action_emoji = "🟢"
        elif action == "SELL":
            color = "#FF6B6B"  # Red
            action_emoji = "🔴"
        else:
            color = "#868E96"  # Gray
            action_emoji = "⚪"
        
        blocks = []
        
        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{action_emoji} Trading Signal: {action}",
                "emoji": True,
            }
        })
        
        # Signal details
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Ticker:*\n`${ticker}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Action:*\n{action}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Confidence:*\n{confidence:.0%}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Position Size:*\n{position_size:.1%}",
                },
            ]
        })
        
        # Execution details
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Execution Type:*\n{signal.get('execution_type', 'LIMIT')}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Urgency:*\n{signal.get('urgency', 'MEDIUM')}",
                },
            ]
        })
        
        # Reason
        reason = signal.get("reason", "No reason provided")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📝 Reason:*\n{reason}",
            }
        })
        
        # Auto-execute warning
        auto_execute = signal.get("auto_execute", False)
        if auto_execute:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚡ *AUTO-EXECUTION ENABLED* - Signal will be executed automatically",
                }
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "👆 *Manual approval required*",
                }
            })
        
        # Timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | AI Trading System",
                }
            ]
        })
        
        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks,
                }
            ]
        }
    
    async def send_risk_warning(
        self,
        warning_type: str,
        details: Dict[str, Any],
    ) -> bool:
        """Send risk warning to Slack"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 RISK WARNING 🚨",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{warning_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{details.get('severity', 'HIGH')}",
                    },
                ]
            },
        ]
        
        # Details
        details_text = "\n".join(f"• *{k}:* {v}" for k, v in details.items() if k != "severity")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Details:*\n{details_text}",
            }
        })
        
        # Recommendation
        recommendation = details.get("recommendation", "Review immediately")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚡ Action Required:*\n{recommendation}",
            }
        })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                }
            ]
        })
        
        payload = {
            "attachments": [
                {
                    "color": "#FF0000",
                    "blocks": blocks,
                }
            ]
        }
        
        return await self.send_message(payload)
    
    async def send_test_notification(self) -> bool:
        """Send a test notification"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Test Notification",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your Slack webhook is configured correctly!\n\n*Status:*\n• Connection: OK\n• Webhook: Valid\n• Formatting: Working",
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "AI Trading System - Phase 9",
                    }
                ]
            }
        ]
        
        payload = {
            "attachments": [
                {
                    "color": "#51CF66",
                    "blocks": blocks,
                }
            ]
        }
        
        return await self.send_message(payload)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return {
            **self.stats,
            "enabled": self.enabled,
            "rate_limit_per_minute": self.rate_limit,
            "messages_in_last_minute": len(self._message_times),
        }
    
    def update_settings(
        self,
        enabled: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        rate_limit: Optional[int] = None,
    ):
        """Update notifier settings"""
        if enabled is not None:
            self.enabled = enabled
            logger.info(f"Slack notifications {'enabled' if enabled else 'disabled'}")
        
        if webhook_url is not None:
            self.webhook_url = webhook_url
            logger.info("Slack webhook URL updated")
        
        if rate_limit is not None:
            self.rate_limit = rate_limit
            logger.info(f"Rate limit set to: {rate_limit}/min")


# ============================================================================
# Factory function
# ============================================================================

def create_slack_notifier(
    webhook_url: Optional[str] = None,
) -> SlackNotifier:
    """
    Create a SlackNotifier instance from environment variables.
    
    Environment variables:
        SLACK_WEBHOOK_URL: Incoming Webhook URL
        SLACK_ENABLED: "true" or "false" (default: true)
        SLACK_RATE_LIMIT: Max messages per minute (default: 30)
        SLACK_CHANNEL_CRITICAL: Override channel for CRITICAL alerts
        SLACK_CHANNEL_HIGH: Override channel for HIGH alerts
    """
    import os
    
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
    
    if not url:
        logger.warning("Slack webhook URL not configured")
        return SlackNotifier(
            webhook_url="",
            enabled=False,
        )
    
    enabled = os.getenv("SLACK_ENABLED", "true").lower() == "true"
    rate_limit = int(os.getenv("SLACK_RATE_LIMIT", "30"))
    
    # Channel overrides
    channel_overrides = {}
    if os.getenv("SLACK_CHANNEL_CRITICAL"):
        channel_overrides["CRITICAL"] = os.getenv("SLACK_CHANNEL_CRITICAL")
    if os.getenv("SLACK_CHANNEL_HIGH"):
        channel_overrides["HIGH"] = os.getenv("SLACK_CHANNEL_HIGH")
    
    return SlackNotifier(
        webhook_url=url,
        enabled=enabled,
        rate_limit_per_minute=rate_limit,
        channel_overrides=channel_overrides,
    )
