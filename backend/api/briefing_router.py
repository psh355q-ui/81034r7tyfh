"""
Daily Briefing Router
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict
from datetime import date

from backend.services.daily_briefing_service import DailyBriefingService
from backend.ai.skills.common.logging_decorator import log_endpoint

router = APIRouter(prefix="/api/briefing", tags=["Daily Briefing"])

# Singleton service
_service = None

def get_service():
    global _service
    if _service is None:
        _service = DailyBriefingService()
    return _service

@router.get("/latest")
@log_endpoint("briefing", "read")
async def get_latest_briefing():
    """Get the latest daily briefing, generating it if missing for today"""
    service = get_service()
    briefing = await service.get_latest_briefing()
    
    today = date.today()
    
    # If no briefing or briefing is old, generate a new one
    if not briefing or briefing.date != today:
        briefing_data = await service.generate_briefing()
        # The service returns a dict, not the ORM object directly in generate_briefing return
        return briefing_data
    
    return {
        "id": briefing.id,
        "date": briefing.date,
        "content": briefing.content,
        "metrics": briefing.metrics,
        "updated_at": briefing.updated_at
    }

@router.post("/generate")
@log_endpoint("briefing", "generate")
async def generate_briefing(background_tasks: BackgroundTasks):
    """Trigger generation of daily briefing"""
    service = get_service()
    
    # Run in background to avoid timeout
    # But for MVP testing, wait? 
    # Let's await it for immediate feedback in this version
    result = await service.generate_briefing()
    return result
