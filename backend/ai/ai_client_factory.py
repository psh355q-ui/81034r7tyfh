"""
AI Client Factory - Model Agnostic Design
==========================================

특정 AI 모델에 종속되지 않는 추상화 레이어

지원 공급자:
- Claude (Anthropic)
- Gemini (Google)
- OpenAI (GPT)

사용법:
    client = AIClientFactory.create("gemini-1.5-pro")
    response = await client.call_api("your prompt")
    search_result = await client.search_web("your query")
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
import asyncio
import os
from datetime import datetime


class BaseAIClient(ABC):
    """AI 클라이언트 기본 인터페이스"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.call_count = 0
        self.total_tokens = 0
        
    @abstractmethod
    async def call_api(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        """AI API 호출"""
        pass
    
    @abstractmethod
    async def search_web(self, query: str) -> str:
        """웹 검색 (지식 검증용)"""
        pass
    
    def get_usage_stats(self) -> Dict:
        """사용량 통계"""
        return {
            "model": self.model_name,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens
        }


class ClaudeClient(BaseAIClient):
    """Anthropic Claude 클라이언트"""
    
    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        super().__init__(model_name)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
    async def call_api(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a financial analyst AI.",
                messages=messages
            )
            
            self.call_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.input_tokens + response.usage.output_tokens
            
            return response.content[0].text
            
        except Exception as e:
            return f"Claude API Error: {str(e)}"
    
    async def search_web(self, query: str) -> str:
        """Claude는 직접 웹 검색 불가 - 외부 검색 API 사용"""
        # TODO: Perplexity, Tavily, 또는 Google Search API 연동
        return f"[Search Placeholder] Query: {query}"


class GeminiClient(BaseAIClient):
    """Google Gemini 클라이언트"""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        super().__init__(model_name)
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    async def call_api(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt or "You are a financial analyst AI."
            )
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            self.call_count += 1
            if hasattr(response, 'usage_metadata'):
                self.total_tokens += (
                    response.usage_metadata.prompt_token_count + 
                    response.usage_metadata.candidates_token_count
                )
            
            return response.text
            
        except Exception as e:
            return f"Gemini API Error: {str(e)}"
    
    async def search_web(self, query: str) -> str:
        """Gemini 그라운딩 검색 사용"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(self.model_name)
            
            # Google Search 그라운딩 사용
            response = model.generate_content(
                f"Search the web and provide factual information about: {query}",
                tools=[genai.protos.Tool(google_search_retrieval={})]
            )
            
            return response.text
            
        except Exception as e:
            # 그라운딩 실패 시 일반 응답
            return f"[Search via Gemini] {query}"


class OpenAIClient(BaseAIClient):
    """OpenAI GPT 클라이언트"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name)
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def call_api(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            self.call_count += 1
            if response.usage:
                self.total_tokens += response.usage.total_tokens
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"OpenAI API Error: {str(e)}"
    
    async def search_web(self, query: str) -> str:
        """OpenAI는 직접 웹 검색 불가"""
        return f"[Search Placeholder] Query: {query}"


class MockAIClient(BaseAIClient):
    """테스트용 Mock 클라이언트"""
    
    def __init__(self, model_name: str = "mock-model"):
        super().__init__(model_name)
        self.mock_responses = {}
        
    def set_mock_response(self, prompt_contains: str, response: str):
        """Mock 응답 설정"""
        self.mock_responses[prompt_contains] = response
        
    async def call_api(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        self.call_count += 1
        
        # Mock 응답 매칭
        for key, response in self.mock_responses.items():
            if key.lower() in prompt.lower():
                return response
        
        # 기본 응답 (Deep Reasoning JSON)
        return json.dumps({
            "theme": "AI Infrastructure Shift",
            "step1_direct": {
                "entities": ["Google", "Broadcom", "Nvidia"],
                "impacts": [
                    {"entity": "Google", "impact": "TPU advancement", "sentiment": "positive"},
                    {"entity": "Broadcom", "impact": "TPU chip design partnership", "sentiment": "positive"},
                    {"entity": "Nvidia", "impact": "Reduced dependency", "sentiment": "negative"}
                ],
                "evidence_ids": []
            },
            "step2_secondary": {
                "value_chain_analysis": "Google TPU reduces Nvidia dependency. Broadcom designs TPU chips for Google.",
                "beneficiaries": [
                    {"entity": "Broadcom", "reason": "TPU chip design partnership with Google"}
                ],
                "losers": [
                    {"entity": "Nvidia", "reason": "Reduced cloud provider dependency on Nvidia GPUs"}
                ],
                "reasoning_trace": [
                    "Google announces TPU advancement",
                    "TPU is custom AI chip alternative to Nvidia GPUs",
                    "Broadcom is primary TPU chip designer",
                    "This reduces cloud providers' Nvidia dependency"
                ]
            },
            "step3_strategy": {
                "primary_beneficiary": {
                    "ticker": "GOOGL",
                    "action": "BUY",
                    "confidence": 0.85,
                    "reason": "Own AI silicon gives cost advantage and independence"
                },
                "hidden_beneficiary": {
                    "ticker": "AVGO",
                    "action": "BUY",
                    "confidence": 0.90,
                    "reason": "Primary TPU chip designer, benefits from Google's AI infrastructure growth"
                },
                "loser": {
                    "ticker": "NVDA",
                    "action": "TRIM",
                    "confidence": 0.60,
                    "reason": "Long-term risk from cloud providers developing custom AI chips"
                },
                "bull_case": "Custom AI chips become industry standard, Broadcom becomes critical infrastructure",
                "bear_case": "Nvidia maintains dominance through CUDA ecosystem and software moat"
            },
            "hypothesis_flags": [],
            "overall_confidence": 0.75
        })
    
    async def search_web(self, query: str) -> str:
        """Mock 검색 결과"""
        return f"[Mock Search] Verified: {query}. Partnership is active."


class AIClientFactory:
    """AI 클라이언트 팩토리"""
    
    _clients: Dict[str, BaseAIClient] = {}
    
    @classmethod
    def create(
        cls, 
        model_name: str, 
        provider: Optional[str] = None
    ) -> BaseAIClient:
        """
        모델 이름으로 적절한 클라이언트 생성
        
        Args:
            model_name: 모델 이름 (예: "gemini-1.5-pro", "claude-3-haiku-20240307")
            provider: 명시적 공급자 지정 (선택)
        
        Returns:
            BaseAIClient: AI 클라이언트 인스턴스
        """
        # 캐싱된 클라이언트 반환
        cache_key = f"{provider or 'auto'}:{model_name}"
        if cache_key in cls._clients:
            return cls._clients[cache_key]
        
        # 공급자 자동 감지
        if provider is None:
            provider = cls._detect_provider(model_name)
        
        # 클라이언트 생성
        if provider == "claude":
            client = ClaudeClient(model_name)
        elif provider == "gemini":
            client = GeminiClient(model_name)
        elif provider == "openai":
            client = OpenAIClient(model_name)
        elif provider == "mock":
            client = MockAIClient(model_name)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        cls._clients[cache_key] = client
        return client
    
    @classmethod
    def _detect_provider(cls, model_name: str) -> str:
        """모델 이름에서 공급자 자동 감지"""
        model_lower = model_name.lower()
        
        if "claude" in model_lower or "anthropic" in model_lower:
            return "claude"
        elif "gemini" in model_lower:
            return "gemini"
        elif "gpt" in model_lower or "o1" in model_lower:
            return "openai"
        elif "mock" in model_lower:
            return "mock"
        else:
            # 기본값: Gemini (무료 티어)
            return "gemini"
    
    @classmethod
    def get_all_stats(cls) -> List[Dict]:
        """모든 클라이언트 사용량 통계"""
        return [client.get_usage_stats() for client in cls._clients.values()]
    
    @classmethod
    def clear_cache(cls):
        """클라이언트 캐시 초기화"""
        cls._clients.clear()


# ============================================
# Convenience Functions
# ============================================

def get_reasoning_client() -> BaseAIClient:
    """심층 추론용 클라이언트 가져오기"""
    from backend.config_phase14 import settings
    return AIClientFactory.create(
        settings.REASONING_MODEL_NAME,
        settings.REASONING_MODEL_PROVIDER.value
    )


def get_screener_client() -> BaseAIClient:
    """스크리닝용 클라이언트 가져오기"""
    from backend.config_phase14 import settings
    return AIClientFactory.create(
        settings.SCREENER_MODEL_NAME,
        settings.SCREENER_MODEL_PROVIDER.value
    )


async def test_all_clients():
    """모든 클라이언트 테스트"""
    print("=== AI Client Factory Test ===\n")
    
    # Mock 클라이언트 테스트
    mock = AIClientFactory.create("mock-test", "mock")
    result = await mock.call_api("Test prompt about Google TPU")
    print(f"Mock Client: {result[:100]}...")
    
    # 자동 감지 테스트
    providers = [
        ("claude-3-haiku-20240307", "claude"),
        ("gemini-1.5-pro", "gemini"),
        ("gpt-4o-mini", "openai")
    ]
    
    for model, expected_provider in providers:
        detected = AIClientFactory._detect_provider(model)
        status = "✓" if detected == expected_provider else "✗"
        print(f"{status} {model} → {detected} (expected: {expected_provider})")
    
    # 사용량 통계
    print(f"\n=== Usage Stats ===")
    for stat in AIClientFactory.get_all_stats():
        print(f"  {stat['model']}: {stat['call_count']} calls, {stat['total_tokens']} tokens")


if __name__ == "__main__":
    asyncio.run(test_all_clients())
