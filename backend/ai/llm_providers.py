"""
LLM API Provider Wrapper

Market Intelligence v2.0에서 사용하는 통합 LLM API 인터페이스입니다.
OpenAI와 Anthropic 클라이언트를 추상화하여 일관된 방식으로 사용합니다.

Usage:
    from backend.ai.llm_providers import LLMProvider, ModelConfig

    # Provider 생성
    provider = LLMProvider()

    # Stage 1: 가벼운 모델 (필터링용)
    config = ModelConfig(model="gpt-4o-mini", max_tokens=100)

    # Stage 2: 강력한 모델 (심층 분석용)
    config_deep = ModelConfig(model="claude-sonnet-4-20250514", max_tokens=2000)

    # 비동기 호출
    result = await provider.complete("What is the market sentiment today?", config)
"""

import os
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import aiohttp


class ModelProvider(Enum):
    """LLM 제공자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # 테스트용
    OLLAMA = "ollama"  # 로컬 LLM (Ollama)
    GLM = "glm"  # Z.AI GLM-4.7


@dataclass
class ModelConfig:
    """
    모델 설정

    Attributes:
        model: 모델 이름 (예: "gpt-4o-mini", "claude-sonnet-4-20250514")
        max_tokens: 최대 토큰 수
        temperature: 온도 (0.0 ~ 1.0)
        provider: LLM 제공자
        system_prompt: 시스템 프롬프트
        top_p: Top-p 샘플링
        frequency_penalty: 빈도 패널티 (OpenAI)
        presence_penalty: 존재 패널티 (OpenAI)
    """
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    provider: ModelProvider = ModelProvider.OPENAI
    system_prompt: Optional[str] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    def to_openai_dict(self) -> Dict[str, Any]:
        """OpenAI API용 딕셔너리 변환"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

    def to_anthropic_dict(self) -> Dict[str, Any]:
        """Anthropic API용 딕셔너리 변환"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }


@dataclass
class LLMResponse:
    """
    LLM 응답 표준 형식

    Attributes:
        content: 생성된 텍스트
        model: 사용된 모델 이름
        provider: 사용된 제공자
        tokens_used: 사용된 토큰 수
        latency_ms: 응답 시간 (밀리초)
        finish_reason: 종료 이유
        metadata: 추가 메타데이터
    """
    content: str
    model: str
    provider: ModelProvider
    tokens_used: int = 0
    latency_ms: int = 0
    finish_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider.value,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
        }


class BaseLLMClient:
    """LLM 클라이언트 기본 클래스"""

    def __init__(self, api_key: str):
        """
        초기화

        Args:
            api_key: API 키
        """
        self.api_key = api_key

    async def complete(
        self,
        prompt: str,
        config: ModelConfig
    ) -> LLMResponse:
        """
        텍스트 완성 (추상 메서드)

        Args:
            prompt: 사용자 프롬프트
            config: 모델 설정

        Returns:
            LLMResponse: 생성 결과
        """
        raise NotImplementedError

    async def complete_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig
    ) -> LLMResponse:
        """
        시스템 프롬프트와 함께 텍스트 완성

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            config: 모델 설정

        Returns:
            LLMResponse: 생성 결과
        """
        config.system_prompt = system_prompt
        return await self.complete(user_prompt, config)


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""

    BASE_URL = "https://api.openai.com/v1"

    async def complete(self, prompt: str, config: ModelConfig) -> LLMResponse:
        """OpenAI 텍스트 완성"""
        start_time = datetime.now()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = config.to_openai_dict()
        payload["messages"] = messages

        if HTTPX_AVAILABLE:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    response = response

        if response.status_code != 200:
            error_text = response.text if hasattr(response, 'text') else await response.text()
            raise Exception(f"OpenAI API error: {response.status_code} - {error_text}")

        data = response.json()
        latency = (datetime.now() - start_time).total_seconds() * 1000

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=config.model,
            provider=ModelProvider.OPENAI,
            tokens_used=usage.get("total_tokens", 0),
            latency_ms=int(latency),
            finish_reason=choice.get("finish_reason", ""),
        )


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API 클라이언트"""

    BASE_URL = "https://api.anthropic.com/v1"

    async def complete(self, prompt: str, config: ModelConfig) -> LLMResponse:
        """Anthropic 텍스트 완성"""
        start_time = datetime.now()

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = config.to_anthropic_dict()
        payload["messages"] = [{"role": "user", "content": prompt}]

        if config.system_prompt:
            payload["system"] = config.system_prompt

        if HTTPX_AVAILABLE:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                )
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                ) as response:
                    response = response

        if response.status_code != 200:
            error_text = response.text if hasattr(response, 'text') else await response.text()
            raise Exception(f"Anthropic API error: {response.status_code} - {error_text}")

        data = response.json()
        latency = (datetime.now() - start_time).total_seconds() * 1000

        usage = data.get("usage", {})

        return LLMResponse(
            content=data["content"][0]["text"],
            model=config.model,
            provider=ModelProvider.ANTHROPIC,
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            latency_ms=int(latency),
            finish_reason=data.get("stop_reason", ""),
        )


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM 클라이언트 (테스트용)

    API 호출 없이 미리 정의된 응답을 반환합니다.
    """

    def __init__(self, api_key: str = "mock"):
        super().__init__(api_key)
        self._responses = {
            "default": "This is a mock response for testing purposes.",
            "sentiment": "The market sentiment appears to be cautiously optimistic.",
            "filter": "YES",  # For NewsFilter stage 1
            "narrative": "The emerging narrative centers around AI infrastructure investments.",
        }

    async def complete(self, prompt: str, config: ModelConfig) -> LLMResponse:
        """Mock 텍스트 완성"""
        await asyncio.sleep(0.1)  # Simulate network latency

        start_time = datetime.now()

        # 프롬프트에 따라 다른 응답 반환
        content = self._responses["default"]
        prompt_lower = prompt.lower()

        if "sentiment" in prompt_lower or "feeling" in prompt_lower:
            content = self._responses["sentiment"]
        elif "relevant" in prompt_lower or "investment" in prompt_lower:
            content = self._responses["filter"]
        elif "narrative" in prompt_lower or "theme" in prompt_lower:
            content = self._responses["narrative"]

        latency = (datetime.now() - start_time).total_seconds() * 1000

        return LLMResponse(
            content=content,
            model=f"mock-{config.model}",
            provider=ModelProvider.MOCK,
            tokens_used=len(content.split()) * 2,
            latency_ms=int(latency),
            finish_reason="stop",
        )


class OllamaClient(BaseLLMClient):
    """
    Ollama 로컬 LLM 클라이언트

    로컬에서 실행되는 Ollama 모델을 사용합니다.
    Ollama 설치: https://ollama.ai/download
    """

    BASE_URL = "http://localhost:11434"

    def __init__(self, api_key: str = "ollama", base_url: Optional[str] = None):
        """
        초기화

        Args:
            api_key: 사용하지 않지만 인터페이스 호환성 위해 유지
            base_url: Ollama 서버 URL (기본: localhost:11434)
        """
        super().__init__(api_key)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", self.BASE_URL)
        self._logger = logging.getLogger(__name__) if "logging" in globals() else None

    async def complete(self, prompt: str, config: ModelConfig) -> LLMResponse:
        """Ollama 텍스트 완성"""
        start_time = datetime.now()

        headers = {
            "Content-Type": "application/json",
        }

        # Ollama API 형식
        payload = {
            "model": config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            }
        }

        # 시스템 프롬프트가 있는 경우
        if config.system_prompt:
            payload["system"] = config.system_prompt

        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        headers=headers,
                        json=payload,
                    )
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        headers=headers,
                        json=payload,
                    ) as response:
                        response = response

            if response.status_code != 200:
                error_text = response.text if hasattr(response, 'text') else await response.text()
                raise Exception(f"Ollama API error: {response.status_code} - {error_text}")

            data = response.json()
            latency = (datetime.now() - start_time).total_seconds() * 1000

            # 토큰 수 추정 (Ollama는 토큰 수를 정확히 제공하지 않음)
            content = data.get("response", "")
            estimated_tokens = len(content.split()) * 1.3  # 대략적인 추정

            return LLMResponse(
                content=content,
                model=config.model,
                provider=ModelProvider.OLLAMA,
                tokens_used=int(estimated_tokens),
                latency_ms=int(latency),
                finish_reason=data.get("done_reason", "stop"),
            )

        except Exception as e:
            if self._logger:
                self._logger.error(f"Ollama error: {e}")
            raise Exception(f"Ollama connection failed: {e}. Make sure Ollama is running with: ollama serve")


class GLMClient(BaseLLMClient):
    """
    Z.AI GLM-4.7 클라이언트

    Z.AI (智谱AI) GLM-4.7 API 클라이언트입니다.
    API Key: https://open.bigmodel.cn/usercenter/apikeys
    Docs: https://open.bigmodel.cn/dev/api
    """

    BASE_URL = os.getenv("ZAI_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")

    def __init__(self, api_key: str):
        """
        초기화

        Args:
            api_key: Z.AI API 키
        """
        super().__init__(api_key)
        self._logger = logging.getLogger(__name__) if "logging" in globals() else None

    async def complete(self, prompt: str, config: ModelConfig) -> LLMResponse:
        """GLM 텍스트 완성"""
        start_time = datetime.now()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        # GLM API 형식 (OpenAI 호환)
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
        }

        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.BASE_URL,
                        headers=headers,
                        json=payload,
                    )
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.BASE_URL,
                        headers=headers,
                        json=payload,
                    ) as response:
                        response = response

            if response.status_code != 200:
                error_text = response.text if hasattr(response, 'text') else await response.text()
                # GLM 에러 메시지 분석
                error_data = {}
                try:
                    error_data = response.json() if isinstance(error_text, str) else error_text
                except:
                    pass

                error_msg = error_data.get("error", {}).get("message", error_text)
                raise Exception(f"GLM API error: {response.status_code} - {error_msg}")

            data = response.json()
            latency = (datetime.now() - start_time).total_seconds() * 1000

            choice = data["choices"][0]
            usage = data.get("usage", {})

            return LLMResponse(
                content=choice["message"]["content"],
                model=config.model,
                provider=ModelProvider.GLM,
                tokens_used=usage.get("total_tokens", 0),
                latency_ms=int(latency),
                finish_reason=choice.get("finish_reason", ""),
            )

        except Exception as e:
            if self._logger:
                self._logger.error(f"GLM error: {e}")
            raise


class LLMProvider:
    """
    통합 LLM Provider

    여러 LLM 제공자를 일관된 인터페이스로 사용할 수 있습니다.
    """

    def __init__(self, default_config: Optional[ModelConfig] = None):
        """
        초기화

        Args:
            default_config: 기본 모델 설정
        """
        self.default_config = default_config or ModelConfig(
            model="GLM-4.7",  # GLM-4.7 reasoning model (consistent with glm_client.py)
            provider=ModelProvider.GLM,
            max_tokens=1000,  # Conservative limit to avoid rate issues
            temperature=0.7,
        )

        # API 키 로드
        self._openai_key = os.getenv("OPENAI_API_KEY", "")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._glm_key = os.getenv("GLM_API_KEY", "") or os.getenv("ZAI_API_KEY", "")

        # 클라이언트 초기화
        self._clients: Dict[ModelProvider, BaseLLMClient] = {}

    def _get_client(self, provider: ModelProvider) -> BaseLLMClient:
        """클라이언트 가져오기 (지연 초기화)"""
        if provider in self._clients:
            return self._clients[provider]

        if provider == ModelProvider.OPENAI:
            if not self._openai_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            client = OpenAIClient(self._openai_key)
        elif provider == ModelProvider.ANTHROPIC:
            if not self._anthropic_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            client = AnthropicClient(self._anthropic_key)
        elif provider == ModelProvider.MOCK:
            client = MockLLMClient()
        elif provider == ModelProvider.OLLAMA:
            # Ollama는 API 키가 필요 없음
            client = OllamaClient()
        elif provider == ModelProvider.GLM:
            if not self._glm_key:
                raise ValueError("GLM_API_KEY or ZAI_API_KEY not found in environment")
            client = GLMClient(self._glm_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self._clients[provider] = client
        return client

    async def complete(
        self,
        prompt: str,
        config: Optional[ModelConfig] = None
    ) -> LLMResponse:
        """
        텍스트 완성

        Args:
            prompt: 사용자 프롬프트
            config: 모델 설정 (없으면 기본 설정 사용)

        Returns:
            LLMResponse: 생성 결과
        """
        cfg = config or self.default_config
        client = self._get_client(cfg.provider)
        return await client.complete(prompt, cfg)

    async def complete_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[ModelConfig] = None
    ) -> LLMResponse:
        """
        시스템 프롬프트와 함께 텍스트 완성

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            config: 모델 설정 (없으면 기본 설정 사용)

        Returns:
            LLMResponse: 생성 결과
        """
        cfg = config or self.default_config
        client = self._get_client(cfg.provider)
        return await client.complete_with_system(system_prompt, user_prompt, cfg)

    def create_stage1_config(self) -> ModelConfig:
        """
        Stage 1 필터링용 설정 (가벼운 모델)

        Returns:
            ModelConfig: Stage 1 설정
        """
        return ModelConfig(
            model="gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            max_tokens=50,
            temperature=0.3,
        )

    def create_stage2_config(self) -> ModelConfig:
        """
        Stage 2 심층 분석용 설정 (강력한 모델)

        Returns:
            ModelConfig: Stage 2 설정
        """
        return ModelConfig(
            model="claude-sonnet-4-20250514",
            provider=ModelProvider.ANTHROPIC,
            max_tokens=2000,
            temperature=0.7,
        )

    def create_mock_config(self) -> ModelConfig:
        """
        테스트용 Mock 설정

        Returns:
            ModelConfig: Mock 설정
        """
        return ModelConfig(
            model="mock-model",
            provider=ModelProvider.MOCK,
            max_tokens=100,
            temperature=0.5,
        )

    def create_ollama_config(self, model: str = "llama2") -> ModelConfig:
        """
        Ollama 로컬 LLM 설정

        Args:
            model: Ollama 모델 이름 (llama2, mistral, codellama, etc.)

        Returns:
            ModelConfig: Ollama 설정

        Note:
            Ollama 모델 설치: ollama pull <model>
            예: ollama pull llama2
        """
        return ModelConfig(
            model=model,
            provider=ModelProvider.OLLAMA,
            max_tokens=2000,
            temperature=0.7,
        )

    def create_glm_config(self, model: str = "glm-4.7") -> ModelConfig:
        """
        GLM-4.7 설정

        Args:
            model: GLM 모델 이름 (glm-4.7, glm-4-plus, glm-4-flash, etc.)

        Returns:
            ModelConfig: GLM 설정

        Note:
            GLM-4.7: 심층 추론용 (Concurrency: 3)
            glm-4-plus: 뉴스 처리용 (Concurrency: 20)
            glm-4-flash: 일반용 (Concurrency: 20)
        """
        return ModelConfig(
            model=model,
            provider=ModelProvider.GLM,
            max_tokens=2000,
            temperature=0.7,
        )


# 싱글톤 인스턴스
_llm_provider_instance = None


def get_llm_provider() -> LLMProvider:
    """LLM Provider 싱글톤 반환"""
    global _llm_provider_instance
    if _llm_provider_instance is None:
        _llm_provider_instance = LLMProvider()
    return _llm_provider_instance


# 테스트 헬퍼 함수
async def test_llm_provider():
    """LLM Provider 테스트"""
    provider = get_llm_provider()

    # Mock으로 테스트
    mock_config = provider.create_mock_config()
    result = await provider.complete("Test prompt", mock_config)
    print(f"Mock result: {result.content}")

    return result


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_llm_provider())
