"""
API Authentication Module for AI Trading System

Features:
- API Key based authentication
- Multiple key support (admin, readonly, trading)
- Rate limiting per key
- Audit logging

Author: AI Trading System
Date: 2025-11-15
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from functools import wraps

from fastapi import Security, Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class APIKeyConfig:
    """API Key configuration from environment variables"""
    
    def __init__(self):
        # Main API key for all operations
        self.MASTER_KEY = os.getenv("API_MASTER_KEY", "")
        
        # Trading operations (execute, signals)
        self.TRADING_KEY = os.getenv("API_TRADING_KEY", "")
        
        # Read-only operations (monitoring, stats)
        self.READONLY_KEY = os.getenv("API_READONLY_KEY", "")
        
        # Webhook key for external services (Telegram, Slack)
        self.WEBHOOK_KEY = os.getenv("API_WEBHOOK_KEY", "")
        
        # Development mode - disable auth for local testing
        self.DEV_MODE = os.getenv("API_AUTH_DISABLED", "false").lower() == "true"
        
        if self.DEV_MODE:
            logger.warning("⚠️  API Authentication is DISABLED (DEV_MODE)")
        
        # Rate limiting (requests per minute per key)
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT", "60"))
        
        # Track rate limits
        self._rate_tracker: Dict[str, List[datetime]] = {}
    
    def validate_key(self, api_key: str, required_level: str = "readonly") -> bool:
        """
        Validate API key against required permission level.
        
        Levels (hierarchical):
        - master: Full access to everything
        - trading: Can execute trades, approve signals
        - webhook: External service callbacks
        - readonly: View data, stats, monitoring
        """
        if self.DEV_MODE:
            return True
        
        if not api_key:
            return False
        
        # Master key has all permissions
        if api_key == self.MASTER_KEY and self.MASTER_KEY:
            return True
        
        # Check specific level
        if required_level == "trading":
            return api_key in [self.TRADING_KEY, self.MASTER_KEY] and self.TRADING_KEY
        
        if required_level == "webhook":
            return api_key in [self.WEBHOOK_KEY, self.MASTER_KEY] and self.WEBHOOK_KEY
        
        if required_level == "readonly":
            return api_key in [
                self.READONLY_KEY,
                self.TRADING_KEY,
                self.WEBHOOK_KEY,
                self.MASTER_KEY
            ] and (self.READONLY_KEY or self.TRADING_KEY or self.WEBHOOK_KEY or self.MASTER_KEY)
        
        return False
    
    def check_rate_limit(self, api_key: str) -> bool:
        """Check if key is within rate limit"""
        if self.DEV_MODE:
            return True
        
        now = datetime.now()
        
        # Clean old entries
        if api_key not in self._rate_tracker:
            self._rate_tracker[api_key] = []
        
        self._rate_tracker[api_key] = [
            t for t in self._rate_tracker[api_key]
            if (now - t).total_seconds() < 60
        ]
        
        # Check limit
        if len(self._rate_tracker[api_key]) >= self.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Record this request
        self._rate_tracker[api_key].append(now)
        return True
    
    def get_key_identity(self, api_key: str) -> str:
        """Get identity/name for the API key (for logging)"""
        if api_key == self.MASTER_KEY:
            return "MASTER"
        if api_key == self.TRADING_KEY:
            return "TRADING"
        if api_key == self.READONLY_KEY:
            return "READONLY"
        if api_key == self.WEBHOOK_KEY:
            return "WEBHOOK"
        return "UNKNOWN"


# Global configuration instance
api_config = APIKeyConfig()


# ============================================================================
# FastAPI Security Dependencies
# ============================================================================

# Support both header and query parameter for API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """
    Extract API key from header or query parameter.
    Header takes precedence.
    """
    if header_key:
        return header_key
    if query_key:
        return query_key
    return ""


async def verify_readonly_access(
    api_key: str = Depends(get_api_key),
    request: Request = None,
) -> str:
    """
    Verify API key has at least readonly access.
    Use this for: stats, monitoring, data viewing endpoints.
    """
    if not api_config.validate_key(api_key, "readonly"):
        logger.warning(f"Unauthorized access attempt from {request.client.host if request else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not api_config.check_rate_limit(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({api_config.RATE_LIMIT_PER_MINUTE} requests/minute)",
        )
    
    identity = api_config.get_key_identity(api_key)
    logger.debug(f"API access granted: {identity}")
    
    return api_key


async def verify_trading_access(
    api_key: str = Depends(get_api_key),
    request: Request = None,
) -> str:
    """
    Verify API key has trading permissions.
    Use this for: execute trades, approve signals, modify positions.
    
    ⚠️  CRITICAL: This must be applied to all trading endpoints!
    """
    if not api_config.validate_key(api_key, "trading"):
        logger.error(
            f"🚨 UNAUTHORIZED TRADING ATTEMPT from {request.client.host if request else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Trading API Key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not api_config.check_rate_limit(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({api_config.RATE_LIMIT_PER_MINUTE} requests/minute)",
        )
    
    identity = api_config.get_key_identity(api_key)
    logger.info(f"🔐 Trading access granted: {identity}")
    
    return api_key


async def verify_webhook_access(
    api_key: str = Depends(get_api_key),
    request: Request = None,
) -> str:
    """
    Verify API key for webhook callbacks.
    Use this for: Telegram bot webhooks, Slack callbacks.
    """
    if not api_config.validate_key(api_key, "webhook"):
        logger.warning(f"Invalid webhook access from {request.client.host if request else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook API Key required",
        )
    
    if not api_config.check_rate_limit(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    
    return api_key


async def verify_master_access(
    api_key: str = Depends(get_api_key),
    request: Request = None,
) -> str:
    """
    Verify API key has master/admin access.
    Use this for: system configuration, kill switch, etc.
    """
    if api_key != api_config.MASTER_KEY or not api_config.MASTER_KEY:
        logger.error(f"🚨 MASTER KEY ACCESS DENIED from {request.client.host if request else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master API Key required",
        )
    
    logger.info("🔑 Master access granted")
    return api_key


# ============================================================================
# Audit Logging
# ============================================================================

class APIAuditLog(BaseModel):
    """Audit log entry for API access"""
    timestamp: datetime
    endpoint: str
    method: str
    key_identity: str
    client_ip: str
    success: bool
    details: Optional[str] = None


# In-memory audit log (for production, use database or file)
_audit_log: List[APIAuditLog] = []
MAX_AUDIT_LOG_SIZE = 1000


def log_api_access(
    endpoint: str,
    method: str,
    api_key: str,
    client_ip: str,
    success: bool,
    details: Optional[str] = None,
):
    """Log API access for auditing"""
    entry = APIAuditLog(
        timestamp=datetime.now(),
        endpoint=endpoint,
        method=method,
        key_identity=api_config.get_key_identity(api_key),
        client_ip=client_ip,
        success=success,
        details=details,
    )
    
    _audit_log.append(entry)
    
    # Keep log size manageable
    if len(_audit_log) > MAX_AUDIT_LOG_SIZE:
        _audit_log.pop(0)
    
    if not success:
        logger.warning(f"API Access Failed: {entry.dict()}")
    else:
        logger.debug(f"API Access: {entry.dict()}")


def get_audit_log(limit: int = 100) -> List[APIAuditLog]:
    """Get recent audit log entries"""
    return _audit_log[-limit:]


# ============================================================================
# Helper Functions
# ============================================================================

def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    import secrets
    return secrets.token_urlsafe(length)


def setup_env_template():
    """
    Print template for .env file with API keys.
    Run this once to generate keys for your setup.
    """
    print("# ============================================")
    print("# API Authentication Keys for AI Trading System")
    print("# ============================================")
    print("")
    print("# Master key - full access (admin)")
    print(f"API_MASTER_KEY={generate_api_key()}")
    print("")
    print("# Trading key - execute trades, approve signals")
    print(f"API_TRADING_KEY={generate_api_key()}")
    print("")
    print("# Readonly key - view data, monitoring")
    print(f"API_READONLY_KEY={generate_api_key()}")
    print("")
    print("# Webhook key - external service callbacks")
    print(f"API_WEBHOOK_KEY={generate_api_key()}")
    print("")
    print("# Rate limit (requests per minute per key)")
    print("API_RATE_LIMIT=60")
    print("")
    print("# Disable auth for local development (NEVER in production!)")
    print("API_AUTH_DISABLED=false")
    print("")
    print("# ============================================")


# ============================================================================
# Example Usage in Routers
# ============================================================================

"""
Example: How to protect your endpoints

from core.auth import (
    verify_readonly_access,
    verify_trading_access,
    verify_master_access,
)

# Readonly endpoint (stats, monitoring)
@router.get("/stats", dependencies=[Depends(verify_readonly_access)])
async def get_stats():
    return {"status": "ok"}

# Trading endpoint (execute, approve signals)
@router.post("/execute", dependencies=[Depends(verify_trading_access)])
async def execute_trade(signal_id: int):
    # ⚠️  This is protected by trading API key
    return {"executed": True}

# Admin endpoint (kill switch, system config)
@router.post("/kill-switch", dependencies=[Depends(verify_master_access)])
async def activate_kill_switch():
    return {"killed": True}

# Get API key in endpoint for logging
@router.post("/analyze")
async def analyze(api_key: str = Depends(verify_readonly_access)):
    identity = api_config.get_key_identity(api_key)
    logger.info(f"Analysis requested by {identity}")
    return {"analyzed": True}
"""


if __name__ == "__main__":
    # Generate API keys template
    setup_env_template()
