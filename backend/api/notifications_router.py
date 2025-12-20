"""
Notifications API Router for AI Trading System

Features:
- Get/Update notification settings
- Send test notifications
- View notification history
- Statistics

Author: AI Trading System
Date: 2025-11-15
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Import notification manager
from backend.notifications.notification_manager import (
    create_notification_manager,
    NotificationChannel,
)

# Import auth if available
# from auth import require_read, require_write

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Global notification manager instance
_notification_manager = None


def get_manager():
    """Get or create notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = create_notification_manager()
    return _notification_manager


# ============================================================================
# Request/Response Models
# ============================================================================

class TelegramSettings(BaseModel):
    enabled: Optional[bool] = None
    min_priority: Optional[str] = None  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    rate_limit_per_minute: Optional[int] = None
    throttle_minutes: Optional[int] = None


class SlackSettings(BaseModel):
    enabled: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = None


class NotificationSettingsRequest(BaseModel):
    telegram: Optional[TelegramSettings] = None
    slack: Optional[SlackSettings] = None


class NotificationSettingsResponse(BaseModel):
    telegram: Dict[str, Any]
    slack: Dict[str, Any]


class AlertHistoryResponse(BaseModel):
    timestamp: str
    alert_type: str
    channels: List[str]
    success: bool
    priority: str
    data_summary: str


class TestNotificationRequest(BaseModel):
    channel: str = "all"  # "telegram", "slack", "all"


class TestNotificationResponse(BaseModel):
    success: Dict[str, bool]
    message: str


class NotificationStatsResponse(BaseModel):
    telegram: Dict[str, Any]
    slack: Dict[str, Any]
    history_size: int
    alert_counts: Dict[str, int]
    success_counts: Dict[str, int]
    overall_success_rate: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    # api_key: str = Depends(require_read),
):
    """
    Get current notification settings for all channels.
    """
    manager = get_manager()
    settings = manager.get_settings()
    return NotificationSettingsResponse(**settings)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings: NotificationSettingsRequest,
    # api_key: str = Depends(require_write),
):
    """
    Update notification settings.
    
    Only provided fields will be updated.
    """
    manager = get_manager()
    
    update_dict = {}
    
    if settings.telegram:
        update_dict["telegram"] = {}
        if settings.telegram.enabled is not None:
            update_dict["telegram"]["enabled"] = settings.telegram.enabled
        if settings.telegram.min_priority is not None:
            update_dict["telegram"]["min_priority"] = settings.telegram.min_priority
        if settings.telegram.rate_limit_per_minute is not None:
            update_dict["telegram"]["rate_limit_per_minute"] = settings.telegram.rate_limit_per_minute
        if settings.telegram.throttle_minutes is not None:
            update_dict["telegram"]["throttle_minutes"] = settings.telegram.throttle_minutes
    
    if settings.slack:
        update_dict["slack"] = {}
        if settings.slack.enabled is not None:
            update_dict["slack"]["enabled"] = settings.slack.enabled
        if settings.slack.rate_limit_per_minute is not None:
            update_dict["slack"]["rate_limit_per_minute"] = settings.slack.rate_limit_per_minute
    
    success = manager.update_settings(update_dict)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    return NotificationSettingsResponse(**manager.get_settings())


@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    request: TestNotificationRequest,
    # api_key: str = Depends(require_write),
):
    """
    Send test notification to verify configuration.
    
    - **channel**: "telegram", "slack", or "all"
    """
    manager = get_manager()
    
    # Map channel string to enum
    channel_map = {
        "telegram": NotificationChannel.TELEGRAM,
        "slack": NotificationChannel.SLACK,
        "all": NotificationChannel.ALL,
    }
    
    channel = channel_map.get(request.channel.lower())
    if not channel:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel: {request.channel}. Use 'telegram', 'slack', or 'all'"
        )
    
    results = await manager.send_test_notification(channel)
    
    if not results:
        message = "No notifications sent. Check if channels are enabled."
    elif all(results.values()):
        message = "All test notifications sent successfully!"
    elif any(results.values()):
        message = "Some test notifications sent. Check individual results."
    else:
        message = "All test notifications failed. Check configuration."
    
    return TestNotificationResponse(
        success=results,
        message=message,
    )


@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_notification_history(
    limit: int = 50,
    alert_type: Optional[str] = None,
    # api_key: str = Depends(require_read),
):
    """
    Get recent notification history.
    
    - **limit**: Maximum number of records (default: 50, max: 500)
    - **alert_type**: Filter by type (NEWS, SIGNAL, RISK_WARNING)
    """
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500")
    
    if alert_type and alert_type not in ["NEWS", "SIGNAL", "RISK_WARNING"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid alert_type. Use NEWS, SIGNAL, or RISK_WARNING"
        )
    
    manager = get_manager()
    history = manager.get_alert_history(limit=limit, alert_type=alert_type)
    
    return [AlertHistoryResponse(**record) for record in history]


@router.get("/statistics", response_model=NotificationStatsResponse)
async def get_notification_statistics(
    # api_key: str = Depends(require_read),
):
    """
    Get notification statistics.
    """
    manager = get_manager()
    stats = manager.get_statistics()
    return NotificationStatsResponse(**stats)


@router.delete("/history")
async def clear_notification_history(
    # api_key: str = Depends(require_write),
):
    """
    Clear notification history.
    
    ⚠️ This action cannot be undone.
    """
    manager = get_manager()
    manager.clear_history()
    
    return {
        "status": "cleared",
        "message": "Notification history cleared",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def notifications_health():
    """
    Check notification system health.
    """
    manager = get_manager()
    settings = manager.get_settings()
    stats = manager.get_statistics()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "telegram": {
            "enabled": settings["telegram"]["enabled"],
            "messages_sent": stats["telegram"]["total_sent"],
            "failed": stats["telegram"]["failed"],
        },
        "slack": {
            "enabled": settings["slack"]["enabled"],
            "messages_sent": stats["slack"]["total_sent"],
            "failed": stats["slack"]["failed"],
        },
        "total_alerts": stats["history_size"],
        "success_rate": f"{stats['overall_success_rate']:.1%}",
    }


# ============================================================================
# Manual Alert Endpoints (for testing or admin use)
# ============================================================================

class ManualNewsAlertRequest(BaseModel):
    title: str
    url: Optional[str] = ""
    sentiment_overall: str = "NEUTRAL"
    sentiment_score: float = 0.0
    impact_magnitude: float = 0.5
    urgency: str = "MEDIUM"
    risk_category: str = "MEDIUM"
    key_facts: List[str] = []
    affected_sectors: List[str] = []
    related_tickers: List[str] = []
    key_warnings: List[str] = []
    priority: str = "HIGH"
    channel: str = "all"


@router.post("/manual/news")
async def send_manual_news_alert(
    request: ManualNewsAlertRequest,
    # api_key: str = Depends(require_write),
):
    """
    Send manual news alert (for testing or admin purposes).
    """
    manager = get_manager()
    
    analysis = {
        "title": request.title,
        "url": request.url,
        "sentiment_overall": request.sentiment_overall,
        "sentiment_score": request.sentiment_score,
        "impact_magnitude": request.impact_magnitude,
        "urgency": request.urgency,
        "risk_category": request.risk_category,
        "key_facts": request.key_facts,
        "affected_sectors": request.affected_sectors,
        "related_tickers": request.related_tickers,
        "key_warnings": request.key_warnings,
    }
    
    channel_map = {
        "telegram": NotificationChannel.TELEGRAM,
        "slack": NotificationChannel.SLACK,
        "all": NotificationChannel.ALL,
    }
    channel = channel_map.get(request.channel.lower(), NotificationChannel.ALL)
    
    results = await manager.send_news_alert(analysis, request.priority, channel)
    
    return {
        "status": "sent",
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }


class ManualSignalAlertRequest(BaseModel):
    ticker: str
    action: str  # BUY, SELL, HOLD
    position_size: float = 0.05
    confidence: float = 0.7
    execution_type: str = "LIMIT"
    reason: str = "Manual signal"
    urgency: str = "MEDIUM"
    auto_execute: bool = False
    priority: str = "HIGH"
    channel: str = "all"


@router.post("/manual/signal")
async def send_manual_signal_alert(
    request: ManualSignalAlertRequest,
    # api_key: str = Depends(require_write),
):
    """
    Send manual trading signal alert (for testing).
    """
    manager = get_manager()
    
    signal = {
        "ticker": request.ticker,
        "action": request.action,
        "position_size": request.position_size,
        "confidence": request.confidence,
        "execution_type": request.execution_type,
        "reason": request.reason,
        "urgency": request.urgency,
        "auto_execute": request.auto_execute,
    }
    
    channel_map = {
        "telegram": NotificationChannel.TELEGRAM,
        "slack": NotificationChannel.SLACK,
        "all": NotificationChannel.ALL,
    }
    channel = channel_map.get(request.channel.lower(), NotificationChannel.ALL)
    
    results = await manager.send_trading_signal(signal, request.priority, channel)
    
    return {
        "status": "sent",
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }


class ManualRiskWarningRequest(BaseModel):
    warning_type: str
    severity: str = "HIGH"
    details: Dict[str, Any] = {}
    recommendation: str = "Review immediately"
    channel: str = "all"


@router.post("/manual/risk-warning")
async def send_manual_risk_warning(
    request: ManualRiskWarningRequest,
    # api_key: str = Depends(require_write),
):
    """
    Send manual risk warning (for testing).
    """
    manager = get_manager()
    
    details = {
        "severity": request.severity,
        "recommendation": request.recommendation,
        **request.details,
    }
    
    channel_map = {
        "telegram": NotificationChannel.TELEGRAM,
        "slack": NotificationChannel.SLACK,
        "all": NotificationChannel.ALL,
    }
    channel = channel_map.get(request.channel.lower(), NotificationChannel.ALL)
    
    results = await manager.send_risk_warning(request.warning_type, details, channel)
    
    return {
        "status": "sent",
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }
