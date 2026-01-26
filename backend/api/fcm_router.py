"""
FCM (Firebase Cloud Messaging) Token Management API

Phase 4 - Real-time Execution
Date: 2026-01-25

Features:
- Register FCM tokens for push notifications
- Unregister tokens on logout/uninstall
- List user's registered devices
- Update token status
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.database.repository import get_sync_session
from backend.database.models import UserFCMToken

router = APIRouter(prefix="/api/fcm", tags=["FCM Push Notifications"])


# ==================
# Pydantic Schemas
# ==================

class FCMTokenRegisterRequest(BaseModel):
    """FCM 토큰 등록 요청"""
    user_id: str = Field(..., description="사용자 ID")
    token: str = Field(..., description="FCM 토큰", min_length=50, max_length=300)
    device_type: Optional[str] = Field(None, description="디바이스 타입 (ios, android, web)")
    device_id: Optional[str] = Field(None, description="디바이스 고유 ID")
    device_name: Optional[str] = Field(None, description="사용자 정의 디바이스 이름")
    app_version: Optional[str] = Field(None, description="앱 버전")
    os_version: Optional[str] = Field(None, description="OS 버전")


class FCMTokenResponse(BaseModel):
    """FCM 토큰 응답"""
    id: int
    user_id: str
    token: str
    device_type: Optional[str]
    device_id: Optional[str]
    device_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================
# API Endpoints
# ==================

@router.post("/register", response_model=FCMTokenResponse)
async def register_fcm_token(
    request: FCMTokenRegisterRequest,
    db: Session = Depends(get_sync_session)
):
    """
    FCM 토큰 등록
    
    - 새로운 토큰을 등록하거나 기존 토큰을 업데이트합니다.
    - 동일한 토큰이 이미 존재하면 업데이트합니다.
    """
    # 기존 토큰 확인
    existing_token = db.query(UserFCMToken).filter(
        UserFCMToken.token == request.token
    ).first()
    
    if existing_token:
        # 기존 토큰 업데이트
        existing_token.user_id = request.user_id
        existing_token.device_type = request.device_type
        existing_token.device_id = request.device_id
        existing_token.device_name = request.device_name
        existing_token.app_version = request.app_version
        existing_token.os_version = request.os_version
        existing_token.is_active = True
        existing_token.updated_at = datetime.now()
        
        db.commit()
        db.refresh(existing_token)
        
        return existing_token
    
    # 새로운 토큰 생성
    new_token = UserFCMToken(
        user_id=request.user_id,
        token=request.token,
        device_type=request.device_type,
        device_id=request.device_id,
        device_name=request.device_name,
        app_version=request.app_version,
        os_version=request.os_version,
        is_active=True
    )
    
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    
    return new_token


@router.delete("/unregister")
async def unregister_fcm_token(
    token: str = Query(..., description="FCM 토큰"),
    db: Session = Depends(get_sync_session)
):
    """
    FCM 토큰 등록 해제
    
    - 토큰을 비활성화합니다 (삭제하지 않음, 이력 유지)
    """
    fcm_token = db.query(UserFCMToken).filter(
        UserFCMToken.token == token
    ).first()
    
    if not fcm_token:
        raise HTTPException(404, "Token not found")
    
    fcm_token.is_active = False
    fcm_token.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": "Token unregistered successfully"}


@router.get("/tokens", response_model=List[FCMTokenResponse])
async def get_user_fcm_tokens(
    user_id: str = Query(..., description="사용자 ID"),
    active_only: bool = Query(True, description="활성 토큰만 조회"),
    db: Session = Depends(get_sync_session)
):
    """
    사용자의 FCM 토큰 목록 조회
    
    - 사용자가 등록한 모든 디바이스의 토큰을 조회합니다.
    """
    query = db.query(UserFCMToken).filter(
        UserFCMToken.user_id == user_id
    )
    
    if active_only:
        query = query.filter(UserFCMToken.is_active == True)
    
    tokens = query.order_by(UserFCMToken.created_at.desc()).all()
    
    return tokens


@router.put("/tokens/{token_id}/deactivate")
async def deactivate_fcm_token(
    token_id: int,
    db: Session = Depends(get_sync_session)
):
    """
    특정 FCM 토큰 비활성화
    
    - 토큰 ID로 토큰을 비활성화합니다.
    """
    fcm_token = db.query(UserFCMToken).filter(
        UserFCMToken.id == token_id
    ).first()
    
    if not fcm_token:
        raise HTTPException(404, "Token not found")
    
    fcm_token.is_active = False
    fcm_token.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": "Token deactivated successfully"}


@router.get("/stats")
async def get_fcm_stats(
    db: Session = Depends(get_sync_session)
):
    """
    FCM 토큰 통계
    
    - 전체 등록된 토큰 수, 활성 토큰 수, 디바이스별 분포 등을 조회합니다.
    """
    total_tokens = db.query(UserFCMToken).count()
    active_tokens = db.query(UserFCMToken).filter(UserFCMToken.is_active == True).count()
    
    # 디바이스 타입별 분포
    from sqlalchemy import func
    device_distribution = db.query(
        UserFCMToken.device_type,
        func.count(UserFCMToken.id).label('count')
    ).filter(
        UserFCMToken.is_active == True
    ).group_by(
        UserFCMToken.device_type
    ).all()
    
    return {
        "total_tokens": total_tokens,
        "active_tokens": active_tokens,
        "inactive_tokens": total_tokens - active_tokens,
        "device_distribution": [
            {"device_type": dt[0], "count": dt[1]}
            for dt in device_distribution
        ]
    }
