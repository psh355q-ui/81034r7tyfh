"""
Authentication Management API Router

Features:
- View API key info
- View audit logs
- Test authentication
- System health check

Author: AI Trading System
Date: 2025-11-15
"""

from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import (
    get_api_key,
    verify_readonly_access,
    verify_trading_access,
    verify_master_access,
    api_config,
    get_audit_log,
)

from backend.ai.skills.common.logging_decorator import log_endpoint


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Response Models
# ============================================================================

class AuthStatusResponse(BaseModel):
    total_keys: int
    enabled_keys: int
    recent_failed_attempts: int
    audit_log_size: int


class ApiKeyInfoResponse(BaseModel):
    name: str
    permissions: List[str]
    rate_limit_per_hour: int
    enabled: bool
    created_at: str
    last_used: str | None
    remaining_requests: int


class AuditLogEntry(BaseModel):
    timestamp: str
    api_key_name: str
    endpoint: str
    method: str
    permission_required: str
    success: bool
    client_ip: str
    details: str


class TestAuthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    api_key_name: str
    permissions: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=AuthStatusResponse)
@log_endpoint("auth", "system")
async def get_authentication_status(
    api_key: str = Depends(verify_readonly_access)
):
    """
    Get authentication system status.
    Requires: READ permission
    """
    logs = get_audit_log(limit=1000)
    failed_24h = sum(1 for log in logs if not log.success)

    return AuthStatusResponse(
        total_keys=4,  # MASTER, TRADING, READONLY, WEBHOOK
        enabled_keys=sum(1 for k in [api_config.MASTER_KEY, api_config.TRADING_KEY,
                                     api_config.READONLY_KEY, api_config.WEBHOOK_KEY] if k),
        recent_failed_attempts=failed_24h,
        audit_log_size=len(logs)
    )


@router.get("/me", response_model=ApiKeyInfoResponse)
@log_endpoint("auth", "system")
async def get_my_api_key_info(
    api_key: str = Depends(get_api_key)
):
    """
    Get information about the current API key.
    Requires: Valid API key
    """
    identity = api_config.get_key_identity(api_key)

    # Determine permissions
    permissions = []
    if api_config.validate_key(api_key, "readonly"):
        permissions.append("READ")
    if api_config.validate_key(api_key, "trading"):
        permissions.append("TRADE")
    if api_key == api_config.MASTER_KEY and api_config.MASTER_KEY:
        permissions.append("MASTER")

    return ApiKeyInfoResponse(
        name=identity,
        permissions=permissions,
        rate_limit_per_hour=api_config.RATE_LIMIT_PER_MINUTE * 60,
        enabled=True,
        created_at="N/A",
        last_used=None,
        remaining_requests=api_config.RATE_LIMIT_PER_MINUTE
    )


@router.get("/audit-logs", response_model=List[AuditLogEntry])
@log_endpoint("auth", "system")
async def get_audit_logs(
    limit: int = 100,
    api_key: str = Depends(verify_trading_access)
):
    """
    Get recent audit logs.
    Requires: TRADING permission
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

    logs = get_audit_log(limit=limit)
    return [
        AuditLogEntry(
            timestamp=log.timestamp.isoformat(),
            api_key_name=log.key_identity,
            endpoint=log.endpoint,
            method=log.method,
            permission_required="",
            success=log.success,
            client_ip=log.client_ip,
            details=log.details or ""
        )
        for log in logs
    ]


@router.get("/failed-attempts", response_model=List[AuditLogEntry])
@log_endpoint("auth", "system")
async def get_failed_attempts(
    hours: int = 24,
    api_key: str = Depends(verify_trading_access)
):
    """
    Get failed authentication attempts in last N hours.
    Requires: TRADING permission
    """
    if hours < 1 or hours > 168:  # Max 1 week
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")

    logs = get_audit_log(limit=1000)
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=hours)

    failed_logs = [
        AuditLogEntry(
            timestamp=log.timestamp.isoformat(),
            api_key_name=log.key_identity,
            endpoint=log.endpoint,
            method=log.method,
            permission_required="",
            success=log.success,
            client_ip=log.client_ip,
            details=log.details or ""
        )
        for log in logs
        if not log.success and log.timestamp >= cutoff
    ]

    return failed_logs


@router.get("/test/read", response_model=TestAuthResponse)
@log_endpoint("auth", "system")
async def test_read_permission(
    api_key: str = Depends(verify_readonly_access)
):
    """
    Test READ permission.
    Requires: READ permission
    """
    identity = api_config.get_key_identity(api_key)
    permissions = []
    if api_config.validate_key(api_key, "readonly"):
        permissions.append("READ")
    if api_config.validate_key(api_key, "trading"):
        permissions.append("TRADE")

    return TestAuthResponse(
        status="success",
        message="READ permission verified",
        timestamp=datetime.now().isoformat(),
        api_key_name=identity,
        permissions=permissions,
    )


@router.get("/test/write", response_model=TestAuthResponse)
@log_endpoint("auth", "system")
async def test_write_permission(
    api_key: str = Depends(verify_trading_access)
):
    """
    Test TRADING permission.
    Requires: TRADING permission
    """
    identity = api_config.get_key_identity(api_key)
    permissions = ["READ", "TRADE"]

    return TestAuthResponse(
        status="success",
        message="TRADING permission verified",
        timestamp=datetime.now().isoformat(),
        api_key_name=identity,
        permissions=permissions,
    )


@router.get("/test/execute", response_model=TestAuthResponse)
@log_endpoint("auth", "system")
async def test_execute_permission(
    api_key: str = Depends(verify_master_access)
):
    """
    Test MASTER permission (highest level).
    Requires: MASTER permission

    ⚠️ This is the permission level required for system administration!
    """
    identity = api_config.get_key_identity(api_key)
    permissions = ["READ", "TRADE", "MASTER"]

    return TestAuthResponse(
        status="success",
        message="MASTER permission verified - You have full system access!",
        timestamp=datetime.now().isoformat(),
        api_key_name=identity,
        permissions=permissions,
    )


@router.get("/health")
@log_endpoint("auth", "system")
async def auth_health_check():
    """
    Public health check endpoint (no auth required).
    """
    logs = get_audit_log(limit=1000)
    failed_24h = sum(1 for log in logs if not log.success)

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "auth_system": "operational",
        "total_api_keys": 4,
        "recent_failed_attempts_24h": failed_24h,
    }
