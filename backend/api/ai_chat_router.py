"""
AI Chat API Router

Features:
- Claude/Gemini API 프록시
- 실시간 토큰 사용량 추적
- 비용 계산
- API 요청/응답 원문 반환
- 히스토리 저장
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

# Anthropic SDK
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Google Generative AI SDK
try:
    import google.generativeai as genai
except ImportError:
    genai = None

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])


# ============================================================================
# Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    model: str  # "claude" or "gemini"
    message: str
    history: list[ChatMessage] = []
    max_tokens: int = 1000
    temperature: float = 0.7
    show_raw_request: bool = False  # API 요청 원문 반환 여부


class ChatResponse(BaseModel):
    response: str
    model_used: str
    token_usage: dict
    cost_estimate: dict
    response_time_ms: int
    raw_request: Optional[dict] = None  # API 요청 원문
    raw_response: Optional[dict] = None  # API 응답 원문
    chat_id: str


class ChatHistory(BaseModel):
    chat_id: str
    model: str
    messages: list[ChatMessage]
    total_tokens: int
    total_cost: float
    created_at: str
    updated_at: str


# ============================================================================
# Pricing (2025 Latest)
# ============================================================================

PRICING = {
    "claude-haiku-4.5": {
        "input_per_1m": 1.00,
        "output_per_1m": 5.00,
        "display_name": "Claude Haiku 4.5"
    },
    "claude-sonnet-4": {
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
        "display_name": "Claude Sonnet 4"
    },
    "gemini-1.5-flash": {
        "input_per_1m": 0.075,
        "output_per_1m": 0.30,
        "display_name": "Gemini 1.5 Flash"
    },
    "gemini-1.5-pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
        "display_name": "Gemini 1.5 Pro"
    }
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
    """토큰 사용량 기반 비용 계산"""
    pricing = PRICING.get(model, {})
    if not pricing:
        return {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "currency": "USD"
        }
    
    input_cost = (input_tokens / 1_000_000) * pricing.get("input_per_1m", 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get("output_per_1m", 0)
    
    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(input_cost + output_cost, 6),
        "currency": "USD"
    }


# ============================================================================
# Chat History Storage
# ============================================================================

# Docker 컨테이너 호환 경로 (상대 경로 또는 /app 기반)
CHAT_HISTORY_DIR = Path("/app/data/ai_chat_history")
try:
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # 폴백: /tmp 디렉토리 사용
    CHAT_HISTORY_DIR = Path("/tmp/ai_chat_history")
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_chat_history(chat_id: str, model: str, messages: list, tokens: int, cost: float):
    """채팅 히스토리 저장"""
    history_file = CHAT_HISTORY_DIR / f"{chat_id}.json"
    
    now = datetime.utcnow().isoformat()
    
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["messages"] = messages
        data["total_tokens"] += tokens
        data["total_cost"] += cost
        data["updated_at"] = now
    else:
        data = {
            "chat_id": chat_id,
            "model": model,
            "messages": messages,
            "total_tokens": tokens,
            "total_cost": cost,
            "created_at": now,
            "updated_at": now
        }
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data


def load_chat_history(chat_id: str) -> Optional[dict]:
    """채팅 히스토리 로드"""
    history_file = CHAT_HISTORY_DIR / f"{chat_id}.json"
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_chat_histories(limit: int = 20) -> list[dict]:
    """최근 채팅 히스토리 목록"""
    histories = []
    for file in sorted(CHAT_HISTORY_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(histories) >= limit:
            break
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            histories.append({
                "chat_id": data["chat_id"],
                "model": data["model"],
                "message_count": len(data["messages"]),
                "total_tokens": data["total_tokens"],
                "total_cost": data["total_cost"],
                "updated_at": data["updated_at"]
            })
    return histories


# ============================================================================
# Claude API Client
# ============================================================================

async def chat_with_claude(
    message: str,
    history: list[ChatMessage],
    max_tokens: int = 1000,
    temperature: float = 0.7,
    model: str = "claude-3-5-haiku-20241022"
) -> dict:
    """Claude API 호출"""
    
    if Anthropic is None:
        raise HTTPException(status_code=500, detail="Anthropic SDK not installed")
    
    import time
    start_time = time.time()
    
    # 히스토리 구성
    messages = []
    for msg in history:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 현재 메시지 추가
    messages.append({
        "role": "user",
        "content": message
    })
    
    # API 요청 구성
    request_body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages
    }
    
    # Claude API 호출
    client = Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    
    response = client.messages.create(**request_body)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # 응답 파싱
    assistant_message = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    
    # 비용 계산
    model_key = "claude-haiku-4.5" if "haiku" in model else "claude-sonnet-4"
    cost = calculate_cost(model_key, input_tokens, output_tokens)
    
    return {
        "response": assistant_message,
        "model_used": model,
        "model_key": model_key,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        },
        "cost_estimate": cost,
        "response_time_ms": elapsed_ms,
        "raw_request": request_body,
        "raw_response": {
            "id": response.id,
            "type": response.type,
            "role": response.role,
            "content": [{"type": c.type, "text": c.text} for c in response.content],
            "model": response.model,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        }
    }


# ============================================================================
# Gemini API Client
# ============================================================================

async def chat_with_gemini(
    message: str,
    history: list[ChatMessage],
    max_tokens: int = 1000,
    temperature: float = 0.7,
    model: str = "gemini-1.5-flash"
) -> dict:
    """Gemini API 호출"""
    
    if genai is None:
        raise HTTPException(status_code=500, detail="Google Generative AI SDK not installed")
    
    import time
    start_time = time.time()
    
    # Gemini 모델 설정
    genai_model = genai.GenerativeModel(model)
    
    # 히스토리 구성 (Gemini 형식)
    chat_history = []
    for msg in history:
        if msg.role == "user":
            chat_history.append({"role": "user", "parts": [msg.content]})
        else:
            chat_history.append({"role": "model", "parts": [msg.content]})
    
    # API 요청 구성
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    
    request_body = {
        "model": model,
        "history": chat_history,
        "message": message,
        "generation_config": generation_config
    }
    
    # Gemini API 호출
    chat = genai_model.start_chat(history=chat_history)
    response = chat.send_message(
        message,
        generation_config=genai.GenerationConfig(**generation_config)
    )
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # 응답 파싱
    assistant_message = response.text
    
    # 토큰 사용량 추정 (Gemini는 직접 제공하지 않을 수 있음)
    # 대략적인 추정: 1 토큰 ≈ 4 문자
    input_tokens = len(message) // 4
    for msg in history:
        input_tokens += len(msg.content) // 4
    output_tokens = len(assistant_message) // 4
    
    # 실제 usage_metadata가 있는 경우 사용
    if hasattr(response, 'usage_metadata'):
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
    
    # 비용 계산
    model_key = "gemini-1.5-flash" if "flash" in model else "gemini-1.5-pro"
    cost = calculate_cost(model_key, input_tokens, output_tokens)
    
    return {
        "response": assistant_message,
        "model_used": model,
        "model_key": model_key,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        },
        "cost_estimate": cost,
        "response_time_ms": elapsed_ms,
        "raw_request": request_body,
        "raw_response": {
            "text": assistant_message,
            "model": model,
            "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else "unknown",
            "safety_ratings": [
                {"category": str(r.category), "probability": str(r.probability)}
                for r in response.candidates[0].safety_ratings
            ] if response.candidates and response.candidates[0].safety_ratings else []
        }
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI와 대화
    
    - model: "claude" 또는 "gemini"
    - message: 사용자 메시지
    - history: 이전 대화 내역
    - max_tokens: 최대 출력 토큰
    - temperature: 창의성 (0.0-1.0)
    - show_raw_request: API 원문 표시 여부
    """
    
    chat_id = str(uuid.uuid4())
    
    try:
        if request.model.lower() in ["claude", "claude-haiku", "claude-sonnet"]:
            # Claude 모델 선택
            if "sonnet" in request.model.lower():
                model_name = "claude-sonnet-4-20250514"
            else:
                model_name = "claude-3-5-haiku-20241022"
            
            result = await chat_with_claude(
                message=request.message,
                history=request.history,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                model=model_name
            )
        
        elif request.model.lower() in ["gemini", "gemini-flash", "gemini-pro"]:
            # Gemini 모델 선택
            if "pro" in request.model.lower():
                model_name = "gemini-1.5-pro"
            else:
                model_name = "gemini-1.5-flash"
            
            result = await chat_with_gemini(
                message=request.message,
                history=request.history,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                model=model_name
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model: {request.model}. Use 'claude' or 'gemini'"
            )
        
        # 히스토리 업데이트
        updated_history = list(request.history)
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=result["response"]))
        
        # 히스토리 저장
        save_chat_history(
            chat_id=chat_id,
            model=result["model_key"],
            messages=[msg.dict() for msg in updated_history],
            tokens=result["token_usage"]["total_tokens"],
            cost=result["cost_estimate"]["total_cost"]
        )
        
        # 응답 구성
        response_data = {
            "response": result["response"],
            "model_used": result["model_used"],
            "token_usage": result["token_usage"],
            "cost_estimate": result["cost_estimate"],
            "response_time_ms": result["response_time_ms"],
            "chat_id": chat_id
        }
        
        # 원문 요청/응답 포함 (옵션)
        if request.show_raw_request:
            response_data["raw_request"] = result["raw_request"]
            response_data["raw_response"] = result["raw_response"]
        
        return ChatResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI Chat Error: {str(e)}"
        )


@router.get("/history")
async def get_chat_history_list(limit: int = 20):
    """채팅 히스토리 목록 조회"""
    return list_chat_histories(limit=limit)


@router.get("/history/{chat_id}")
async def get_chat_history(chat_id: str):
    """특정 채팅 히스토리 조회"""
    history = load_chat_history(chat_id)
    if not history:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return history


@router.get("/pricing")
async def get_pricing():
    """모델별 가격표 조회"""
    return PRICING


@router.get("/models")
async def get_available_models():
    """사용 가능한 모델 목록"""
    return {
        "claude": [
            {
                "id": "claude-haiku",
                "name": "Claude Haiku 4.5",
                "description": "빠르고 저렴 (추천)",
                "pricing": PRICING["claude-haiku-4.5"]
            },
            {
                "id": "claude-sonnet",
                "name": "Claude Sonnet 4",
                "description": "고성능, 복잡한 분석용",
                "pricing": PRICING["claude-sonnet-4"]
            }
        ],
        "gemini": [
            {
                "id": "gemini-flash",
                "name": "Gemini 1.5 Flash",
                "description": "최저가, 무료 티어 가능",
                "pricing": PRICING["gemini-1.5-flash"]
            },
            {
                "id": "gemini-pro",
                "name": "Gemini 1.5 Pro",
                "description": "고성능, 긴 컨텍스트",
                "pricing": PRICING["gemini-1.5-pro"]
            }
        ]
    }
