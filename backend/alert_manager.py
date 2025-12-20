"""
Alert Manager
Manages system alerts and notifications
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class AlertLevel(str, Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertCategory(str, Enum):
    """Alert categories"""
    TRADING = "TRADING"
    RISK = "RISK"
    SYSTEM = "SYSTEM"
    MARKET = "MARKET"
    COMPLIANCE = "COMPLIANCE"

class Alert(BaseModel):
    """Alert model"""
    id: str
    level: AlertLevel
    category: AlertCategory
    title: str
    message: str
    timestamp: str
    acknowledged: bool = False

class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, max_alerts: int = 100):
        self.alerts: List[Alert] = []
        self.max_alerts = max_alerts

    def send_alert(
        self,
        level: AlertLevel,
        category: AlertCategory,
        title: str,
        message: str
    ) -> Alert:
        """Create and store a new alert"""
        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            category=category,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            acknowledged=False
        )

        self.alerts.insert(0, alert)

        # Keep only the most recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[:self.max_alerts]

        # Log critical alerts
        if level == AlertLevel.CRITICAL:
            print(f"CRITICAL ALERT: {title} - {message}")

        return alert

    def get_alerts(
        self,
        limit: Optional[int] = None,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        filtered = self.alerts

        if level:
            filtered = [a for a in filtered if a.level == level]

        if category:
            filtered = [a for a in filtered if a.category == category]

        if limit:
            filtered = filtered[:limit]

        return filtered

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def clear_acknowledged(self):
        """Remove acknowledged alerts"""
        self.alerts = [a for a in self.alerts if not a.acknowledged]

    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts"""
        return sum(1 for a in self.alerts if not a.acknowledged)
