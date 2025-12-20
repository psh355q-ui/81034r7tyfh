"""
Gemini Free API Router

Gemini 1.5 Flash 무료 티어:
- 15 RPM (분당 15요청)
- 1,500 RPD (일당 1,500요청)
- 1M TPM (분당 1M 토큰)

비용: $0
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Google Generative AI SDK
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

router = APIRouter(prefix="/gemini-free", tags=["Gemini Free"])


# ============================================================================
# Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    content: str


class GeminiRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    max_tokens: int = 1000
    temperature: float = 0.7


class GeminiResponse(BaseModel):
    response: str
    token_usage: dict
    response_time_ms: int
    request_id: str
    daily_usage: dict  # 일일 사용량 추적


# ============================================================================
# Daily Usage Tracking (무료 티어 1,500회/일 제한)
# ============================================================================

# Docker 컨테이너 호환 경로
USAGE_FILE = Path("/app/data/gemini_daily_usage.json")
try:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    USAGE_FILE = Path("/tmp/gemini_daily_usage.json")
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_daily_usage() -> dict:
    """오늘의 사용량 조회"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    if USAGE_FILE.exists():
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
        
        if data.get("date") == today:
            return data
    
    # 새로운 날
    return {
        "date": today,
        "request_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "last_request_time": None
    }


def update_daily_usage(input_tokens: int, output_tokens: int):
    """일일 사용량 업데이트"""
    usage = get_daily_usage()
    
    usage["request_count"] += 1
    usage["total_input_tokens"] += input_tokens
    usage["total_output_tokens"] += output_tokens
    usage["last_request_time"] = datetime.utcnow().isoformat()
    
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)
    
    return usage


def check_rate_limit():
    """무료 티어 제한 확인"""
    usage = get_daily_usage()
    
    if usage["request_count"] >= 1500:
        raise HTTPException(
            status_code=429,
            detail=f"일일 무료 요청 한도 초과 (1,500회/일). 내일 다시 시도하세요. 현재: {usage['request_count']}회"
        )
    
    return usage


# ============================================================================
# Chat History Storage
# ============================================================================

# Docker 컨테이너 호환 경로
HISTORY_DIR = Path("/app/data/gemini_chat_history")
try:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    HISTORY_DIR = Path("/tmp/gemini_chat_history")
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_chat(request_id: str, messages: list, input_tokens: int, output_tokens: int):
    """채팅 저장"""
    data = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "messages": messages,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }
    
    file_path = HISTORY_DIR / f"{request_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_recent_chats(limit: int = 20) -> list:
    """최근 채팅 목록"""
    chats = []
    files = sorted(HISTORY_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for file in files[:limit]:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            chats.append({
                "request_id": data["request_id"],
                "timestamp": data["timestamp"],
                "message_count": len(data["messages"]),
                "tokens": data["input_tokens"] + data["output_tokens"]
            })
    
    return chats


# ============================================================================
# Gemini API Client
# ============================================================================

async def chat_with_gemini(
    message: str,
    history: list[ChatMessage],
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> dict:
    """Gemini 1.5 Flash API 호출 (무료)"""
    
    if not GENAI_AVAILABLE:
        raise HTTPException(
            status_code=500, 
            detail="google-generativeai 패키지를 설치하세요: pip install google-generativeai"
        )
    
    import time
    start_time = time.time()
    
    # 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 히스토리 구성 (Gemini 형식)
    chat_history = []
    for msg in history:
        role = "user" if msg.role == "user" else "model"
        chat_history.append({
            "role": role,
            "parts": [msg.content]
        })
    
    # Generation 설정
    generation_config = genai.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    
    # 채팅 시작
    chat = model.start_chat(history=chat_history)
    
    # 메시지 전송
    response = chat.send_message(message, generation_config=generation_config)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # 응답 텍스트
    response_text = response.text
    
    # 토큰 사용량 (Gemini가 제공하는 경우)
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
    else:
        # 추정 (1 토큰 ≈ 4 문자)
        input_tokens = len(message) // 4
        for msg in history:
            input_tokens += len(msg.content) // 4
        output_tokens = len(response_text) // 4
    
    return {
        "response": response_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "response_time_ms": elapsed_ms
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/chat", response_model=GeminiResponse)
async def chat(request: GeminiRequest):
    """
    Gemini 무료 API로 대화
    
    - 무료: 1,500회/일
    - 모델: gemini-1.5-flash
    - 비용: $0
    """
    
    # Rate limit 확인
    check_rate_limit()
    
    request_id = str(uuid.uuid4())[:8]
    
    try:
        # Gemini API 호출
        result = await chat_with_gemini(
            message=request.message,
            history=request.history,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # 일일 사용량 업데이트
        daily_usage = update_daily_usage(
            result["input_tokens"],
            result["output_tokens"]
        )
        
        # 히스토리 저장
        all_messages = [msg.dict() for msg in request.history]
        all_messages.append({"role": "user", "content": request.message})
        all_messages.append({"role": "model", "content": result["response"]})
        
        save_chat(
            request_id=request_id,
            messages=all_messages,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"]
        )
        
        return GeminiResponse(
            response=result["response"],
            token_usage={
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "total_tokens": result["input_tokens"] + result["output_tokens"]
            },
            response_time_ms=result["response_time_ms"],
            request_id=request_id,
            daily_usage={
                "requests_today": daily_usage["request_count"],
                "remaining": 1500 - daily_usage["request_count"],
                "total_tokens_today": daily_usage["total_input_tokens"] + daily_usage["total_output_tokens"]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 오류: {str(e)}")


@router.get("/usage")
async def get_usage():
    """오늘의 사용량 조회"""
    usage = get_daily_usage()
    return {
        "date": usage["date"],
        "requests": {
            "used": usage["request_count"],
            "remaining": 1500 - usage["request_count"],
            "limit": 1500
        },
        "tokens": {
            "input": usage["total_input_tokens"],
            "output": usage["total_output_tokens"],
            "total": usage["total_input_tokens"] + usage["total_output_tokens"]
        },
        "last_request": usage["last_request_time"],
        "cost": "$0.00 (무료 티어)"
    }


@router.get("/history")
async def get_history(limit: int = 20):
    """최근 채팅 히스토리"""
    return list_recent_chats(limit=limit)


@router.get("/status")
async def get_status():
    """API 상태 확인"""
    return {
        "gemini_sdk_available": GENAI_AVAILABLE,
        "model": "gemini-1.5-flash",
        "tier": "FREE",
        "limits": {
            "requests_per_day": 1500,
            "requests_per_minute": 15,
            "tokens_per_minute": 1_000_000
        },
        "cost": "$0.00"
    }


@router.post("/analyze-news")
async def analyze_news(news_content: str, ticker: str = ""):
    """
    뉴스 자동 분석 (무료)
    
    Trading System이 자동으로 호출하는 엔드포인트
    """
    
    check_rate_limit()
    
    prompt = f"""
다음 뉴스를 분석해주세요:

{news_content}

{f"관련 티커: {ticker}" if ticker else ""}

JSON 형식으로 답변해주세요:
{{
  "sentiment": "positive" | "negative" | "neutral",
  "sentiment_score": -1.0 ~ 1.0,
  "key_points": ["주요 포인트 1", "주요 포인트 2"],
  "risk_factors": ["리스크 1", "리스크 2"],
  "market_impact": "short_term_impact 설명",
  "recommendation": "행동 제안"
}}
"""
    
    request_id = str(uuid.uuid4())[:8]
    
    result = await chat_with_gemini(
        message=prompt,
        history=[],
        max_tokens=500,
        temperature=0.3  # 일관된 응답
    )
    
    # 사용량 업데이트
    daily_usage = update_daily_usage(result["input_tokens"], result["output_tokens"])
    
    # JSON 파싱 시도
    try:
        # 마크다운 코드 블록 제거
        response_text = result["response"]
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        analysis = json.loads(response_text.strip())
    except:
        analysis = {"raw_response": result["response"]}
    
    return {
        "analysis": analysis,
        "request_id": request_id,
        "tokens_used": result["input_tokens"] + result["output_tokens"],
        "remaining_requests": 1500 - daily_usage["request_count"],
        "cost": "$0.00"
    }
