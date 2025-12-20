# Architecture Integration Plan
## AI Trading System - Token Optimization & NAS Deployment

**목표**: NAS + Docker 기반 24/7 자동매매 시스템 구축 및 토큰 비용 최적화

**현재 API 사용 현황**:
- OpenAI GPT-4o
- Google Gemini
- Anthropic Claude
- News API
- KIS (한국투자증권) API

---

## 1. Skill Layer Architecture

### 1.1 현재 구조 문제점

현재 시스템은 모든 API를 개별적으로 호출하며, 컨텍스트 창에 모든 도구 정의를 로드합니다.

**문제**:
- 매 요청마다 불필요한 도구 정의 전송 → 토큰 낭비
- API 간 역할 구분 불명확
- 동적 도구 선택 불가

### 1.2 제안: 5개 Skill Group

```
backend/skills/
├── __init__.py
├── base_skill.py                    # Base Skill 클래스
├── market_data/
│   ├── __init__.py
│   ├── news_skill.py                # News API, 뉴스 크롤링
│   ├── search_skill.py              # 웹 검색, 시장 데이터
│   └── calendar_skill.py            # 경제 캘린더, 이벤트
├── fundamental/
│   ├── __init__.py
│   ├── sec_skill.py                 # SEC 공시, 기업 정보
│   ├── financials_skill.py          # 재무제표 분석
│   └── value_chain_skill.py         # 공급망, 경쟁사 분석
├── technical/
│   ├── __init__.py
│   ├── chart_skill.py               # 차트 분석, 기술적 지표
│   ├── backtest_skill.py            # 백테스팅
│   └── statistics_skill.py          # 통계 분석
├── trading/
│   ├── __init__.py
│   ├── kis_skill.py                 # KIS API 주문 실행
│   ├── order_skill.py               # 주문 관리
│   └── risk_skill.py                # 리스크 관리, 포지션 계산
└── intelligence/
    ├── __init__.py
    ├── claude_skill.py              # Claude (복잡한 추론)
    ├── gemini_skill.py              # Gemini (뉴스 분석)
    ├── gpt4o_skill.py               # GPT-4o (전략 생성)
    └── local_llm_skill.py           # Local LLM (라우팅용)
```

### 1.3 Base Skill 인터페이스

```python
# backend/skills/base_skill.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseSkill(ABC):
    """모든 Skill의 기본 클래스"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """이 Skill이 제공하는 도구 목록 반환"""
        pass

    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """도구 실행"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Skill 메타데이터 (라우팅용)"""
        return {
            "name": self.name,
            "description": self.description,
            "keywords": self._get_keywords(),
            "estimated_cost": self._estimate_cost(),
        }

    @abstractmethod
    def _get_keywords(self) -> List[str]:
        """라우팅을 위한 키워드"""
        pass

    def _estimate_cost(self) -> str:
        """예상 비용 (low/medium/high)"""
        return "medium"
```

### 1.4 구현 예시: News Skill

```python
# backend/skills/market_data/news_skill.py
from backend.skills.base_skill import BaseSkill
from backend.data.news_crawler import NaverNewsCrawler
from typing import List, Dict, Any

class NewsSkill(BaseSkill):
    """뉴스 수집 및 검색 Skill"""

    def __init__(self):
        super().__init__(
            name="MarketData.News",
            description="실시간 뉴스 수집, 검색, 필터링"
        )
        self.crawler = NaverNewsCrawler()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "키워드로 뉴스 검색",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string"},
                            "max_results": {"type": "integer", "default": 20}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_latest_news",
                    "description": "최신 뉴스 가져오기",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["all", "economy", "stock"]},
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            }
        ]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        if tool_name == "search_news":
            return await self._search_news(**kwargs)
        elif tool_name == "get_latest_news":
            return await self._get_latest_news(**kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _get_keywords(self) -> List[str]:
        return ["뉴스", "news", "기사", "언론", "보도", "뉴스검색"]

    async def _search_news(self, keyword: str, max_results: int = 20):
        articles = await self.crawler.search_news(keyword, max_results)
        return {"articles": [a.to_dict() for a in articles]}

    async def _get_latest_news(self, category: str = "all", limit: int = 10):
        articles = await self.crawler.get_latest(category, limit)
        return {"articles": [a.to_dict() for a in articles]}
```

### 1.5 토큰 절감 효과

**현재 (모든 도구 로드)**:
- 도구 정의: ~3,000 토큰 (30개 도구 × 100토큰)
- 매 요청마다 전송

**Skill Layer 적용 후**:
- 필요한 Skill만 로드: ~500 토큰 (5개 도구 × 100토큰)
- **절감: ~2,500 토큰/요청 (83% 감소)**

---

## 2. Semantic Router - 3단계 라우팅

### 2.1 라우팅 흐름

```
사용자 요청
    ↓
[Stage 1: Intent Classification]  ← Local LLM (무료)
    ↓
Intent: "news_analysis" / "trading_execution" / "strategy_generation"
    ↓
[Stage 2: Tool Group Selection]  ← Rule-based (무료)
    ↓
Tool Groups: ["MarketData.News", "Intelligence.Gemini"]
    ↓
[Stage 3: Model Selection]  ← Rule-based (무료)
    ↓
Model: Gemini-1.5-Flash (뉴스 분석용)
    ↓
실행 및 응답
```

### 2.2 구현: Intent Classifier

```python
# backend/routing/intent_classifier.py
from typing import Dict, List
import re

class IntentClassifier:
    """로컬 LLM 또는 규칙 기반 Intent 분류"""

    INTENT_PATTERNS = {
        "news_analysis": [
            r"뉴스.*분석",
            r"기사.*분석",
            r"최근.*소식",
            r"what.*news",
            r"analyze.*article"
        ],
        "trading_execution": [
            r"매수|매도|주문",
            r"거래.*실행",
            r"buy|sell|order",
            r"execute.*trade"
        ],
        "strategy_generation": [
            r"전략.*생성",
            r"백테스트",
            r"포트폴리오",
            r"strategy.*generate",
            r"backtest"
        ],
        "market_research": [
            r"시장.*조사",
            r"경쟁사.*분석",
            r"섹터.*분석",
            r"market.*research"
        ]
    }

    def classify(self, user_input: str) -> str:
        """사용자 입력에서 Intent 추출"""
        user_lower = user_input.lower()

        # Rule-based matching
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_lower):
                    return intent

        # Default
        return "general_query"

    def get_confidence(self, user_input: str, intent: str) -> float:
        """Intent 신뢰도 (0-1)"""
        # 간단한 매칭 개수 기반
        matches = sum(
            1 for pattern in self.INTENT_PATTERNS.get(intent, [])
            if re.search(pattern, user_input.lower())
        )
        return min(matches * 0.3, 1.0)
```

### 2.3 구현: Tool Group Selector

```python
# backend/routing/tool_selector.py
from typing import List, Dict
from backend.skills import SKILL_REGISTRY

class ToolGroupSelector:
    """Intent에 따라 필요한 Skill Group 선택"""

    INTENT_TO_SKILLS = {
        "news_analysis": [
            "MarketData.News",
            "Intelligence.Gemini"  # 뉴스 분석에 특화
        ],
        "trading_execution": [
            "Trading.KIS",
            "Trading.Order",
            "Trading.Risk"
        ],
        "strategy_generation": [
            "Technical.Backtest",
            "Technical.Statistics",
            "Intelligence.GPT4o"  # 전략 생성에 특화
        ],
        "market_research": [
            "MarketData.Search",
            "Fundamental.SEC",
            "Fundamental.ValueChain",
            "Intelligence.Claude"  # 복잡한 추론에 특화
        ],
        "general_query": [
            "Intelligence.GPT4o"  # 범용
        ]
    }

    def select_skills(self, intent: str) -> List[str]:
        """Intent에 맞는 Skill 목록 반환"""
        return self.INTENT_TO_SKILLS.get(intent, ["Intelligence.GPT4o"])

    def get_tools_for_intent(self, intent: str) -> List[Dict]:
        """선택된 Skill들의 도구 정의 병합"""
        skill_names = self.select_skills(intent)
        tools = []

        for skill_name in skill_names:
            skill = SKILL_REGISTRY.get(skill_name)
            if skill:
                tools.extend(skill.get_tools())

        return tools
```

### 2.4 구현: Model Selector

```python
# backend/routing/model_selector.py
from typing import Dict

class ModelSelector:
    """Intent와 Skill에 따라 최적 모델 선택"""

    MODEL_CONFIGS = {
        "news_analysis": {
            "provider": "gemini",
            "model": "gemini-1.5-flash",
            "reason": "뉴스 분석에 특화, 저렴한 비용"
        },
        "trading_execution": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "reason": "빠른 응답 속도, 안정성"
        },
        "strategy_generation": {
            "provider": "openai",
            "model": "gpt-4o",
            "reason": "복잡한 전략 생성, 높은 품질"
        },
        "market_research": {
            "provider": "claude",
            "model": "claude-sonnet-4-5",
            "reason": "긴 컨텍스트, 심층 분석"
        }
    }

    def select_model(self, intent: str) -> Dict[str, str]:
        """Intent에 최적화된 모델 선택"""
        return self.MODEL_CONFIGS.get(intent, {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "reason": "범용 모델"
        })
```

### 2.5 통합: Semantic Router

```python
# backend/routing/semantic_router.py
from backend.routing.intent_classifier import IntentClassifier
from backend.routing.tool_selector import ToolGroupSelector
from backend.routing.model_selector import ModelSelector
from typing import Dict, Any

class SemanticRouter:
    """3단계 라우팅 시스템"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.tool_selector = ToolGroupSelector()
        self.model_selector = ModelSelector()

    def route(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 라우팅"""

        # Stage 1: Intent Classification
        intent = self.intent_classifier.classify(user_input)
        confidence = self.intent_classifier.get_confidence(user_input, intent)

        # Stage 2: Tool Group Selection
        skill_names = self.tool_selector.select_skills(intent)
        tools = self.tool_selector.get_tools_for_intent(intent)

        # Stage 3: Model Selection
        model_config = self.model_selector.select_model(intent)

        return {
            "intent": intent,
            "confidence": confidence,
            "skills": skill_names,
            "tools": tools,
            "model": model_config,
            "metadata": {
                "total_tools": len(tools),
                "estimated_tokens": len(tools) * 100  # 근사치
            }
        }
```

### 2.6 토큰 절감 효과

**현재 (전체 도구 로드)**:
- 30개 도구 × 100토큰 = 3,000 토큰

**Semantic Router 적용 후**:
- Intent Classification: 0 토큰 (로컬/규칙 기반)
- Tool Selection: 평균 5개 도구 × 100토큰 = 500 토큰
- **절감: 2,500 토큰/요청 (83% 감소)**

---

## 3. Docker Sandbox - 3계층 분리

### 3.1 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Code Execution Sandbox                        │
│ - AI가 생성한 Python 스크립트 실행                        │
│ - 네트워크 격리 (인터넷 접근 불가)                         │
│ - 읽기 전용 파일시스템                                    │
│ - 리소스 제한 (CPU, Memory)                              │
└─────────────────────────────────────────────────────────┘
                        ↓ (Unix Socket)
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Data Pipeline                                 │
│ - 뉴스 크롤링, DB 저장                                    │
│ - AI 분석 결과 저장                                       │
│ - 외부 API 호출 (News, SEC 등)                           │
│ - 인터넷 접근 허용 (읽기 전용 API만)                       │
└─────────────────────────────────────────────────────────┘
                        ↓ (Unix Socket)
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Trading API Gateway                           │
│ - KIS API 주문 실행                                       │
│ - 계좌 조회                                               │
│ - 인증 토큰 관리                                          │
│ - 거래 로그 기록                                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Docker Compose 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Layer 1: Code Execution Sandbox
  code-sandbox:
    build:
      context: .
      dockerfile: docker/Dockerfile.sandbox
    container_name: ai-trading-sandbox
    networks:
      - isolated  # 외부 접근 차단
    volumes:
      - sandbox-workspace:/workspace:ro  # 읽기 전용
      - ./backend/sandbox:/app/sandbox:ro
    environment:
      - PYTHONUNBUFFERED=1
      - MAX_EXECUTION_TIME=30
      - MAX_MEMORY=512M
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  # Layer 2: Data Pipeline
  data-pipeline:
    build:
      context: .
      dockerfile: docker/Dockerfile.pipeline
    container_name: ai-trading-pipeline
    networks:
      - isolated
      - external  # 외부 API 접근 허용
    volumes:
      - ./backend:/app/backend
      - pipeline-data:/data
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - NEWS_API_KEY=${NEWS_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - postgres
      - code-sandbox

  # Layer 3: Trading Gateway
  trading-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.trading
    container_name: ai-trading-gateway
    networks:
      - isolated
      - external
    volumes:
      - ./backend/trading:/app/trading:ro
      - trading-logs:/logs
    environment:
      - KIS_APP_KEY=${KIS_APP_KEY}
      - KIS_APP_SECRET=${KIS_APP_SECRET}
      - KIS_ACCOUNT_NUMBER=${KIS_ACCOUNT_NUMBER}
      - ENABLE_PAPER_TRADING=true  # 기본값: 모의투자
    depends_on:
      - data-pipeline

  # Main API Server
  api-server:
    build: .
    container_name: ai-trading-api
    ports:
      - "8000:8000"
    networks:
      - isolated
      - external
    volumes:
      - ./backend:/app/backend
      - ./frontend:/app/frontend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    depends_on:
      - postgres
      - data-pipeline
      - trading-gateway

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ai-trading-db
    networks:
      - isolated
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=trading_db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

networks:
  isolated:
    driver: bridge
    internal: true  # 외부 접근 차단
  external:
    driver: bridge

volumes:
  sandbox-workspace:
  pipeline-data:
  trading-logs:
  postgres-data:
```

### 3.3 Code Sandbox Dockerfile

```dockerfile
# docker/Dockerfile.sandbox
FROM python:3.11-slim

# 보안 강화
RUN useradd -m -u 1000 sandbox && \
    chmod 755 /home/sandbox

# 최소 패키지만 설치
COPY requirements-sandbox.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-sandbox.txt

# 작업 디렉토리
WORKDIR /workspace
USER sandbox

# 실행 스크립트
COPY --chown=sandbox:sandbox docker/sandbox-runner.py /app/
CMD ["python", "/app/sandbox-runner.py"]
```

### 3.4 Sandbox Runner

```python
# docker/sandbox-runner.py
import os
import sys
import signal
import resource
from pathlib import Path

# 리소스 제한 설정
def set_limits():
    # CPU 시간 제한: 30초
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

    # 메모리 제한: 512MB
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

    # 프로세스 수 제한
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

def execute_code(code: str, timeout: int = 30):
    """격리된 환경에서 코드 실행"""

    # 타임아웃 설정
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        # 리소스 제한 적용
        set_limits()

        # 제한된 globals (위험한 모듈 차단)
        safe_globals = {
            "__builtins__": {
                k: v for k, v in __builtins__.items()
                if k not in ['open', 'eval', 'exec', '__import__', 'compile']
            }
        }

        # 코드 실행
        exec(code, safe_globals)

        return {"success": True, "result": safe_globals.get("result")}

    except TimeoutError:
        return {"success": False, "error": "Timeout"}
    except MemoryError:
        return {"success": False, "error": "Memory limit exceeded"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        signal.alarm(0)

# Unix Socket으로 요청 수신
# (구현 생략 - 실제로는 socket 서버 구현)
```

### 3.5 보안 효과

**현재**: 모든 코드가 단일 컨테이너에서 실행 → 높은 위험

**3계층 분리 후**:
1. Code Sandbox: 네트워크 격리, 읽기 전용, 리소스 제한
2. Data Pipeline: API 호출만 허용, KIS API 접근 불가
3. Trading Gateway: KIS API만 접근, 코드 실행 불가

→ **공격 표면 최소화, 권한 분리**

---

## 4. Tool Definition 캐싱

### 4.1 문제점

매 요청마다 동일한 도구 정의를 전송:
- 30개 도구 × 100토큰 = 3,000 토큰
- 하루 1,000 요청 시: 3,000,000 토큰 낭비

### 4.2 해결: 도구 정의 캐싱

```python
# backend/utils/tool_cache.py
import hashlib
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

class ToolDefinitionCache:
    """도구 정의 캐싱 시스템"""

    def __init__(self, ttl_hours: int = 24):
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(hours=ttl_hours)

    def get_or_create_cache_key(self, tools: List[Dict]) -> str:
        """도구 목록의 해시 생성"""
        tools_json = json.dumps(tools, sort_keys=True)
        return hashlib.sha256(tools_json.encode()).hexdigest()[:16]

    def cache_tools(self, tools: List[Dict]) -> str:
        """도구 정의 캐싱 및 캐시 키 반환"""
        cache_key = self.get_or_create_cache_key(tools)

        self.cache[cache_key] = {
            "tools": tools,
            "cached_at": datetime.now(),
            "expires_at": datetime.now() + self.ttl
        }

        return cache_key

    def get_cached_tools(self, cache_key: str) -> List[Dict] | None:
        """캐시된 도구 정의 조회"""
        cached = self.cache.get(cache_key)

        if not cached:
            return None

        # 만료 체크
        if datetime.now() > cached["expires_at"]:
            del self.cache[cache_key]
            return None

        return cached["tools"]

    def cleanup_expired(self):
        """만료된 캐시 제거"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if now > value["expires_at"]
        ]
        for key in expired_keys:
            del self.cache[key]

# 전역 캐시 인스턴스
_tool_cache = ToolDefinitionCache()

def get_tool_cache() -> ToolDefinitionCache:
    return _tool_cache
```

### 4.3 API 요청 시 캐싱 활용

```python
# backend/ai/base_client.py (수정)
from backend.utils.tool_cache import get_tool_cache

class BaseAIClient:
    def __init__(self):
        self.tool_cache = get_tool_cache()

    async def chat_completion(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        use_cache: bool = True
    ):
        """캐싱을 활용한 API 호출"""

        if tools and use_cache:
            # 도구 정의 캐싱
            cache_key = self.tool_cache.cache_tools(tools)

            # 첫 요청: 전체 도구 정의 전송
            # 이후 요청: 캐시 키만 전송 (토큰 절감)
            if self._is_first_request(cache_key):
                # 전체 전송
                request_tools = tools
            else:
                # 캐시 참조 (프로바이더에 따라 구현 다름)
                request_tools = [{"cache_ref": cache_key}]
        else:
            request_tools = tools

        # API 호출
        response = await self._make_api_call(messages, request_tools)
        return response
```

### 4.4 OpenAI Prompt Caching 활용

OpenAI는 프롬프트 캐싱을 지원합니다 (2024년 10월 출시).

```python
# backend/ai/openai_client.py
from openai import AsyncOpenAI

class OpenAIClient:
    async def chat_with_caching(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ):
        """OpenAI Prompt Caching 활용"""

        # 시스템 메시지와 도구 정의를 캐싱 대상으로 표시
        system_message = {
            "role": "system",
            "content": "You are a trading assistant.",
            "cache_control": {"type": "ephemeral"}  # 캐싱 활성화
        }

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[system_message] + messages,
            tools=tools,
            # 도구 정의도 캐싱됨
        )

        return response
```

**효과**:
- 첫 요청: 3,000 토큰
- 캐시 히트: 300 토큰 (90% 절감)
- 캐시 유효 기간: 5분 (OpenAI 기본값)

### 4.5 전체 토큰 절감

**시나리오**: 하루 1,000 요청, 캐시 히트율 80%

**현재**:
- 1,000 요청 × 3,000 토큰 = 3,000,000 토큰

**캐싱 적용**:
- 200 요청 (캐시 미스) × 3,000 토큰 = 600,000 토큰
- 800 요청 (캐시 히트) × 300 토큰 = 240,000 토큰
- **총합: 840,000 토큰**

**절감: 2,160,000 토큰/일 (72% 감소)**

---

## 5. Local LLM for Routing

### 5.1 라우팅에 Local LLM 사용

Intent Classification은 간단한 작업이므로 로컬 LLM으로 처리 가능.

**추천 모델**:
- Llama 3.2 3B (3GB VRAM)
- Phi-3-mini (2GB VRAM)
- TinyLlama 1.1B (1GB VRAM)

### 5.2 Docker 컨테이너 추가

```yaml
# docker-compose.yml에 추가
services:
  local-llm:
    image: ollama/ollama:latest
    container_name: ai-trading-local-llm
    networks:
      - isolated
    volumes:
      - ollama-models:/root/.ollama
    environment:
      - OLLAMA_MODELS=llama3.2:3b
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]  # GPU 사용 (선택)

volumes:
  ollama-models:
```

### 5.3 Intent Classifier 수정

```python
# backend/routing/intent_classifier.py (Local LLM 버전)
import httpx

class LocalLLMIntentClassifier:
    """로컬 LLM 기반 Intent 분류"""

    def __init__(self, ollama_url: str = "http://local-llm:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"

    async def classify(self, user_input: str) -> str:
        """Ollama API로 Intent 분류"""

        prompt = f"""Classify the user's intent into ONE of these categories:
- news_analysis: User wants to analyze news or articles
- trading_execution: User wants to execute trades (buy/sell)
- strategy_generation: User wants to create or backtest strategies
- market_research: User wants market or company research
- general_query: Other queries

User input: "{user_input}"

Intent (one word only):"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10.0
            )

        result = response.json()
        intent = result["response"].strip().lower()

        # Validation
        valid_intents = ["news_analysis", "trading_execution", "strategy_generation", "market_research", "general_query"]
        return intent if intent in valid_intents else "general_query"
```

### 5.4 비용 절감

**현재 (GPT-4o-mini로 라우팅)**:
- 1,000 요청/일 × 100 토큰 × $0.00015/1K = **$0.015/일**
- 월간: **$0.45**

**Local LLM 적용**:
- 비용: **$0** (완전 무료)
- 응답 속도: ~500ms (GPU) / ~2s (CPU)

**연간 절감: $5.4**

---

## 6. MCP Gateway Pattern

### 6.1 MCP (Model Context Protocol)

MCP는 AI 모델과 데이터 소스를 연결하는 표준 프로토콜입니다.

**적용 방법**:
1. 각 Skill을 MCP Server로 구현
2. AI 모델은 필요한 MCP Server만 연결
3. 동적 도구 로딩 가능

### 6.2 MCP Server 구조

```
backend/mcp_servers/
├── news_server.py          # News API MCP Server
├── kis_server.py           # KIS API MCP Server
├── analysis_server.py      # AI Analysis MCP Server
└── database_server.py      # Database Query MCP Server
```

### 6.3 News MCP Server 예시

```python
# backend/mcp_servers/news_server.py
from mcp.server import Server, Tool
from backend.data.news_crawler import NaverNewsCrawler

class NewsMCPServer(Server):
    """뉴스 API MCP Server"""

    def __init__(self):
        super().__init__(name="news-server")
        self.crawler = NaverNewsCrawler()

        # 도구 등록
        self.add_tool(Tool(
            name="search_news",
            description="Search news articles by keyword",
            parameters={
                "keyword": {"type": "string", "required": True},
                "max_results": {"type": "integer", "default": 20}
            },
            handler=self.search_news
        ))

        self.add_tool(Tool(
            name="get_latest_news",
            description="Get latest news articles",
            parameters={
                "category": {"type": "string", "default": "all"},
                "limit": {"type": "integer", "default": 10}
            },
            handler=self.get_latest_news
        ))

    async def search_news(self, keyword: str, max_results: int = 20):
        articles = await self.crawler.search_news(keyword, max_results)
        return {"articles": [a.to_dict() for a in articles]}

    async def get_latest_news(self, category: str = "all", limit: int = 10):
        articles = await self.crawler.get_latest(category, limit)
        return {"articles": [a.to_dict() for a in articles]}
```

### 6.4 MCP Gateway

```python
# backend/mcp/gateway.py
from typing import List, Dict
from mcp.client import MCPClient

class MCPGateway:
    """MCP Server들을 관리하는 게이트웨이"""

    def __init__(self):
        self.servers: Dict[str, MCPClient] = {}

    async def connect_server(self, server_name: str, server_url: str):
        """MCP Server 연결"""
        client = MCPClient(server_url)
        await client.connect()
        self.servers[server_name] = client

    async def get_tools_for_intent(self, intent: str) -> List[Dict]:
        """Intent에 필요한 도구만 로드"""

        # Intent → 필요한 MCP Server 매핑
        server_mapping = {
            "news_analysis": ["news-server"],
            "trading_execution": ["kis-server", "database-server"],
            "market_research": ["news-server", "analysis-server"]
        }

        required_servers = server_mapping.get(intent, [])
        tools = []

        for server_name in required_servers:
            if server_name in self.servers:
                server_tools = await self.servers[server_name].list_tools()
                tools.extend(server_tools)

        return tools
```

### 6.5 효과

**장점**:
1. 동적 도구 로딩: 필요한 도구만 로드
2. 서버 독립성: 각 MCP Server 독립 배포 가능
3. 확장성: 새로운 Server 추가 용이

**단점**:
- MCP 프로토콜 구현 필요
- 네트워크 오버헤드 증가 (Unix Socket 사용 시 최소화)

---

## 7. Code Model Pattern

### 7.1 개념

AI가 직접 API를 호출하는 대신, **Python 스크립트를 생성**하고 Docker Sandbox에서 실행.

**장점**:
- 복잡한 데이터 처리 로직을 코드로 표현
- API 호출 횟수 감소 (한 번에 여러 작업 수행)
- 코드 재사용 가능

### 7.2 워크플로우

```
1. 사용자 요청: "최근 1주일 삼성전자 뉴스 분석해줘"
    ↓
2. AI가 Python 스크립트 생성:
    ```python
    from news_api import search_news
    from analyzer import analyze_sentiment

    articles = search_news("삼성전자", days=7)
    results = [analyze_sentiment(a) for a in articles]
    result = {"summary": results}
    ```
    ↓
3. Sandbox에서 스크립트 실행
    ↓
4. 결과 반환 및 AI가 최종 응답 생성
```

### 7.3 구현: Code Generator

```python
# backend/ai/code_generator.py
from typing import Dict, Any

class CodeGenerator:
    """AI가 데이터 처리 코드를 생성"""

    def __init__(self, ai_client):
        self.ai_client = ai_client

    async def generate_code(self, user_request: str, available_apis: List[str]) -> str:
        """사용자 요청에서 Python 코드 생성"""

        prompt = f"""You are a code generator for a trading system.

Available APIs:
{self._format_apis(available_apis)}

User request: "{user_request}"

Generate Python code to fulfill this request. The code should:
1. Use only the available APIs
2. Store the final result in a variable called 'result'
3. Be safe to execute in a sandbox (no file I/O, no network calls)

Python code:"""

        response = await self.ai_client.chat_completion([
            {"role": "user", "content": prompt}
        ])

        code = self._extract_code(response["content"])
        return code

    def _format_apis(self, apis: List[str]) -> str:
        """API 목록 포맷팅"""
        return "\n".join([f"- {api}" for api in apis])

    def _extract_code(self, response: str) -> str:
        """응답에서 코드 추출"""
        # ```python ... ``` 블록 추출
        import re
        match = re.search(r"```python\n(.*?)\n```", response, re.DOTALL)
        return match.group(1) if match else response
```

### 7.4 구현: Code Executor

```python
# backend/services/code_executor.py
import httpx
from typing import Dict, Any

class CodeExecutor:
    """Sandbox에서 코드 실행"""

    def __init__(self, sandbox_url: str = "http://code-sandbox:8001"):
        self.sandbox_url = sandbox_url

    async def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """코드 실행 및 결과 반환"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.sandbox_url}/execute",
                json={
                    "code": code,
                    "timeout": timeout
                },
                timeout=timeout + 5
            )

        return response.json()
```

### 7.5 통합 예시

```python
# backend/services/code_model_service.py
from backend.ai.code_generator import CodeGenerator
from backend.services.code_executor import CodeExecutor

class CodeModelService:
    """Code Model Pattern 서비스"""

    def __init__(self, ai_client):
        self.code_gen = CodeGenerator(ai_client)
        self.executor = CodeExecutor()

    async def process_request(self, user_request: str) -> Dict[str, Any]:
        """사용자 요청 처리"""

        # 1. 코드 생성
        available_apis = ["search_news", "analyze_sentiment", "get_stock_price"]
        code = await self.code_gen.generate_code(user_request, available_apis)

        # 2. 코드 실행
        result = await self.executor.execute(code)

        if not result["success"]:
            return {"error": result["error"]}

        # 3. 최종 응답 생성 (AI가 결과 해석)
        final_response = await self._generate_response(user_request, result["result"])

        return {
            "success": True,
            "code": code,
            "result": result["result"],
            "response": final_response
        }

    async def _generate_response(self, request: str, result: Any) -> str:
        """AI가 결과를 자연어로 변환"""
        prompt = f"""User asked: "{request}"

Code execution result: {result}

Provide a natural language summary:"""

        response = await self.code_gen.ai_client.chat_completion([
            {"role": "user", "content": prompt}
        ])

        return response["content"]
```

### 7.6 토큰 절감 효과

**시나리오**: "최근 1주일 삼성전자, SK하이닉스, NAVER 뉴스 분석"

**현재 (Function Calling)**:
- search_news("삼성전자") → 응답 → 다시 요청
- search_news("SK하이닉스") → 응답 → 다시 요청
- search_news("NAVER") → 응답 → 다시 요청
- **총 6회 왕복** (요청 3 + 응답 3)

**Code Model**:
- 코드 생성: 1회 요청
- 코드 실행: 로컬 (무료)
- 결과 해석: 1회 요청
- **총 2회 왕복**

**절감: 67% API 호출 감소**

---

## 8. 통합 구현 우선순위

### Phase 1: 즉시 적용 가능 (1주)
1. **Tool Definition 캐싱** - 가장 빠른 효과
2. **Semantic Router (규칙 기반)** - Local LLM 없이 패턴 매칭으로 시작

### Phase 2: 단기 개선 (2-3주)
3. **Skill Layer 아키텍처** - 코드 재구성
4. **Local LLM for Routing** - Ollama 도입

### Phase 3: 중장기 개선 (1-2개월)
5. **Docker Sandbox 3계층 분리** - 보안 강화
6. **Code Model Pattern** - 복잡한 워크플로우 최적화

### Phase 4: 선택적 적용
7. **MCP Gateway** - 필요 시 고려 (현재는 Skill Layer로 충분)

---

## 9. 예상 토큰 절감 효과

### 현재 상태 (일일 1,000 요청 기준)

| 항목 | 토큰/요청 | 총 토큰/일 |
|------|----------|-----------|
| 도구 정의 | 3,000 | 3,000,000 |
| 시스템 프롬프트 | 500 | 500,000 |
| 사용자 입력 | 100 | 100,000 |
| AI 응답 | 200 | 200,000 |
| **총합** | **3,800** | **3,800,000** |

### 최적화 후

| 항목 | 개선 방법 | 토큰/요청 | 총 토큰/일 | 절감률 |
|------|----------|----------|-----------|-------|
| 도구 정의 | Semantic Router + 캐싱 | 300 | 300,000 | **90%** |
| 시스템 프롬프트 | 프롬프트 캐싱 | 50 | 50,000 | **90%** |
| 사용자 입력 | - | 100 | 100,000 | 0% |
| AI 응답 | - | 200 | 200,000 | 0% |
| **총합** | | **650** | **650,000** | **83%** |

### 비용 절감 (GPT-4o 기준)

**현재**:
- 입력: 3,600 토큰 × 1,000 요청 × $2.50/1M = **$9.00/일**
- 출력: 200 토큰 × 1,000 요청 × $10.00/1M = **$2.00/일**
- **총합: $11.00/일 = $330/월**

**최적화 후**:
- 입력: 450 토큰 × 1,000 요청 × $2.50/1M = **$1.13/일**
- 출력: 200 토큰 × 1,000 요청 × $10.00/1M = **$2.00/일**
- **총합: $3.13/일 = $94/월**

**월간 절감: $236 (72% 감소)**

---

## 10. NAS 배포 가이드

### 10.1 Synology NAS 요구사항

**최소 사양**:
- CPU: Intel/AMD 4코어 이상
- RAM: 16GB 이상
- 저장공간: 100GB 이상 (SSD 권장)
- Docker 지원 NAS 모델

**권장 모델**:
- DS920+, DS1522+, DS1821+ 이상

### 10.2 NAS 설정

1. **Docker 패키지 설치**
   - Synology Package Center → Docker 설치

2. **Docker Compose 설치**
   ```bash
   # SSH로 NAS 접속
   ssh admin@nas-ip

   # Docker Compose 설치
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **프로젝트 배포**
   ```bash
   # Git Clone
   cd /volume1/docker
   git clone https://github.com/your-repo/ai-trading-system.git
   cd ai-trading-system

   # 환경 변수 설정
   cp .env.example .env
   nano .env

   # Docker Compose 실행
   docker-compose up -d
   ```

4. **자동 시작 설정**
   - Synology Task Scheduler → Boot-up 스크립트 추가:
   ```bash
   cd /volume1/docker/ai-trading-system && docker-compose up -d
   ```

### 10.3 모니터링 설정

```yaml
# docker-compose.yml에 추가
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

### 10.4 백업 전략

1. **데이터베이스 백업** (매일 02:00)
   ```bash
   # Synology Task Scheduler
   docker exec ai-trading-db pg_dump -U postgres trading_db > /volume1/backups/db_$(date +%Y%m%d).sql
   ```

2. **로그 로테이션**
   ```yaml
   # docker-compose.yml에 추가
   services:
     api-server:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

---

## 11. 구현 체크리스트

### Phase 1 (1주)
- [ ] Tool Definition 캐싱 구현
  - [ ] ToolDefinitionCache 클래스 작성
  - [ ] BaseAIClient에 캐싱 통합
  - [ ] OpenAI Prompt Caching 활성화
- [ ] Semantic Router (규칙 기반)
  - [ ] IntentClassifier 패턴 매칭 구현
  - [ ] ToolGroupSelector 구현
  - [ ] ModelSelector 구현

### Phase 2 (2-3주)
- [ ] Skill Layer 아키텍처
  - [ ] BaseSkill 클래스 작성
  - [ ] 5개 Skill Group 구현
    - [ ] MarketData Skills
    - [ ] Fundamental Skills
    - [ ] Technical Skills
    - [ ] Trading Skills
    - [ ] Intelligence Skills
  - [ ] 기존 코드 마이그레이션
- [ ] Local LLM for Routing
  - [ ] Ollama Docker 컨테이너 추가
  - [ ] LocalLLMIntentClassifier 구현
  - [ ] 성능 테스트

### Phase 3 (1-2개월)
- [ ] Docker Sandbox 3계층 분리
  - [ ] Dockerfile.sandbox 작성
  - [ ] Dockerfile.pipeline 작성
  - [ ] Dockerfile.trading 작성
  - [ ] docker-compose.yml 수정
  - [ ] Unix Socket 통신 구현
- [ ] Code Model Pattern
  - [ ] CodeGenerator 구현
  - [ ] CodeExecutor 구현
  - [ ] Sandbox Runner 보안 강화
  - [ ] 테스트 케이스 작성

### NAS 배포
- [ ] NAS 환경 준비
  - [ ] Docker 설치
  - [ ] Docker Compose 설치
- [ ] 배포 스크립트 작성
- [ ] 모니터링 설정
  - [ ] Prometheus 설정
  - [ ] Grafana 대시보드
- [ ] 백업 자동화
- [ ] 알림 설정 (거래 실행, 에러 발생 시)

---

## 12. 다음 단계

**즉시 시작 가능한 작업**:

1. **Tool Definition 캐싱 구현**
   - 파일: `backend/utils/tool_cache.py`
   - 예상 시간: 2-3시간
   - 효과: 즉시 토큰 40% 절감

2. **Semantic Router 프로토타입**
   - 파일: `backend/routing/semantic_router.py`
   - 예상 시간: 4-5시간
   - 효과: 도구 로딩 83% 감소

어떤 작업부터 시작하시겠습니까?
