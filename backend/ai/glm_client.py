"""
GLM-4.7 Client for News Analysis

Purpose: Extract tickers and sectors from news articles
Cost: ~$0.001 per article (significantly cheaper than Claude/Gemini)
Speed: < 2s per article
Role: News entity extraction for trading signals

Phase: 1 (GLM Client Implementation)
Task: T1.1

Reference: Based on Z.AI API module provided by user
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


class GLMClient:
    """
    GLM-4.7 Flash client for news analysis (ticker & sector extraction).

    Uses direct HTTP calls to Z.AI API (async/await pattern).

    API Endpoint: https://api.z.ai/api/coding/paas/v4/chat/completions
    Model: glm-4.7 (flagship) or glm-4.5-flash (fast)

    Use Cases:
    1. Extract stock tickers from news articles
    2. Identify relevant sectors
    3. Provide reasoning confidence scores

    Output Format:
    {
        "tickers": ["AAPL", "TSLA"],
        "sectors": ["Technology", "Semiconductors"],
        "confidence": 0.87,
        "reasoning": "애플과 테슬라가 AI 칩 개발에 협력",
        "analyzed_at": "2026-01-15T10:30:00Z",
        "model": "glm-4.7",
        "latency_ms": 150,
        "cost_usd": 0.001
    }
    """

    # Pricing (as of 2025-01)
    # GLM-4.7: ~1 RMB/1M tokens (~$0.001 per request)
    COST_PER_REQUEST = 0.001

    # API Configuration
    DEFAULT_API_URL = "https://api.z.ai/api/coding/paas/v4/chat/completions"
    DEFAULT_MODEL = "GLM-4.7"  # FIXED: GLM-4.7 reasoning model (Max Plan supported)
    DEFAULT_TIMEOUT = 120  # INCREASED: 30s → 120s for GLM-4.7 reasoning
    CONNECT_TIMEOUT = 15   # Connection timeout
    READ_TIMEOUT = 100     # Read timeout
    MAX_RETRY = 3
    BASE_RETRY_DELAY = 0.5  # Exponential backoff base
    MAX_RETRY_DELAY = 5      # Maximum retry delay

    # Connection pooling
    MAX_CONNECTIONS = 10   # Maximum concurrent connections
    MAX_PER_HOST = 5       # Maximum connections per host

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize GLM client with GLM-4.7 reasoning model.

        Args:
            api_key: GLM API key (default: from GLM_API_KEY env var)
            model: Model name (FIXED to GLM-4.7 for consistency)

        Requires:
            GLM_API_KEY environment variable

        Model:
            - GLM-4.7 (FIXED - reasoning model for Max Plan users)
        """
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY environment variable not set")

        # FIXED: Always use GLM-4.7 for consistency (Max Plan supported)
        self.model = model or os.environ.get("GLM_MODEL", "GLM-4.7")
        self.api_url = os.environ.get("GLM_API_URL", self.DEFAULT_API_URL)
        self.timeout = int(os.environ.get("GLM_TIMEOUT", self.DEFAULT_TIMEOUT))

        # Initialize HTTP session (lazy) with connection pooling
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None

        # Metrics tracking
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "success_count": 0,
            "error_count": 0,
            "timeout_count": 0,
        }

        logger.info(f"GLMClient initialized: model={self.model}, timeout={self.timeout}s")

    async def _get_connector(self) -> aiohttp.TCPConnector:
        """Get or create connection pool."""
        if self._connector is None or self._connector.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self.MAX_CONNECTIONS,
                limit_per_host=self.MAX_PER_HOST,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
        return self._connector

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = await self._get_connector()
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=self.CONNECT_TIMEOUT,
                sock_read=self.READ_TIMEOUT
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True,
            )
        return self._session

    async def close(self):
        """Close HTTP session and connector properly."""
        if self._session and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0.25)

        if self._connector and not self._connector.closed:
            await self._connector.close()
            await asyncio.sleep(0.1)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.3,
        json_parser_callback = None
    ) -> Dict:
        """
        Streaming chat completions with real-time JSON extraction.

        This method streams the response and extracts JSON from each chunk,
        allowing early detection of complete JSON objects before the full response.

        Args:
            messages: Message list in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            json_parser_callback: Optional callback function to parse JSON from chunks
                Signature: (chunk_text: str) -> Optional[Dict]

        Returns:
            API response dict with "choices" key, but with JSON extracted from stream

        Example:
            response = await glm_client.chat_stream(
                messages=[
                    {"role": "system", "content": "You are a trader..."},
                    {"role": "user", "content": "Analyze AAPL..."}
                ],
                json_parser_callback=lambda x: parse_json_forward_scan(x, ['action', 'confidence'])
            )
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "stream": True  # Enable streaming
        }

        session = await self._get_session()

        # Accumulated reasoning content
        accumulated_content = ""
        extracted_json = None

        try:
            async with session.post(
                self.api_url,
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API 오류: {response.status} - {error_text}")

                # Process SSE stream line by line
                buffer = ""
                async for chunk in response.content.iter_chunked(1024):
                    buffer += chunk.decode('utf-8', errors='ignore')

                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()

                        # SSE format: "data: {...}"
                        if not line or not line.startswith('data: '):
                            continue

                        data_str = line[6:]  # Remove "data: " prefix

                        # Stream end marker
                        if data_str == '[DONE]':
                            break

                        try:
                            chunk_data = json.loads(data_str)

                            # Extract reasoning_content from chunk
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})

                                # Accumulate reasoning_content or content
                                if 'reasoning_content' in delta:
                                    accumulated_content += delta['reasoning_content']
                                elif 'content' in delta:
                                    accumulated_content += delta['content']

                                # Try to extract JSON from accumulated content
                                if json_parser_callback:
                                    result = json_parser_callback(accumulated_content)
                                    if result:
                                        extracted_json = result
                                        logger.debug("JSON found in stream, continuing to accumulate...")

                        except json.JSONDecodeError:
                            # Skip invalid JSON chunks
                            continue

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            # Fallback to non-streaming if streaming fails
            logger.info("Falling back to non-streaming mode")
            return await self.chat(messages, max_tokens, temperature)

        # Construct response in standard format
        if extracted_json:
            logger.info("Successfully extracted JSON from stream")
            # Return in standard OpenAI format
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps(extracted_json, ensure_ascii=False),
                        "reasoning_content": accumulated_content,
                        "role": "assistant"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {},  # Usage info not available in stream mode
                "model": self.model
            }
        else:
            # No JSON found, return accumulated content
            logger.warning("No JSON found in stream, returning accumulated content")
            return {
                "choices": [{
                    "message": {
                        "content": "",
                        "reasoning_content": accumulated_content,
                        "role": "assistant"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {},
                "model": self.model
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> Dict:
        """
        General chat completions for MVP agents.

        This is the main entry point for War Room agents (Analyst, Trader, Risk).

        Args:
            messages: Message list in OpenAI format
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 ~ 1.0)

        Returns:
            API response dict with "choices" key (OpenAI compatible)

        Example:
            response = await glm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a trader..."},
                    {"role": "user", "content": "Analyze AAPL..."}
                ],
                max_tokens=2048,
                temperature=0.3
            )
            content = response["choices"][0]["message"]["content"]
        """
        return await self._call_api(messages, max_tokens, temperature)

    async def analyze_news(
        self,
        news_text: str,
        **kwargs
    ) -> Dict:
        """
        뉴스 기사에서 종목과 섹터를 추출합니다 (async).

        Args:
            news_text: 뉴스 기사 내용
            **kwargs: 추가 옵션 (예: max_tokens, temperature)

        Returns:
            {
                "tickers": List[str],
                "sectors": List[str],
                "confidence": float (0.0-1.0),
                "reasoning": str,
                "analyzed_at": str (ISO 8601),
                "model": str,
                "latency_ms": int,
                "cost_usd": float
            }

        Raises:
            ValueError: news_text가 빈 문자열인 경우
            Exception: API 호출 실패 시
        """
        if not news_text or not news_text.strip():
            raise ValueError("news_text cannot be empty")

        start_time = time.time()

        try:
            logger.info(f"Analyzing news with GLM (length: {len(news_text)} chars)")

            # Build prompt
            prompt = self._build_prompt(news_text)

            # Call GLM API (async)
            response = await self._call_api(
                messages=[
                    {"role": "system", "content": "You are a financial analyst extracting stock tickers and sectors from news articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get("max_tokens", 500),
                temperature=kwargs.get("temperature", 0.3)
            )

            # Parse response
            result = self._parse_response(response, news_text[:100])

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms
            result["cost_usd"] = self.COST_PER_REQUEST

            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_cost_usd"] += self.COST_PER_REQUEST
            self.metrics["success_count"] += 1
            self.metrics["avg_latency_ms"] = (
                (self.metrics["avg_latency_ms"] * (self.metrics["total_requests"] - 1) + latency_ms)
                / self.metrics["total_requests"]
            )

            logger.info(
                f"GLM analysis complete: "
                f"tickers={len(result['tickers'])}, "
                f"sectors={len(result['sectors'])}, "
                f"confidence={result['confidence']:.2f}, "
                f"latency={latency_ms}ms"
            )

            return result

        except ValueError:
            # Re-raise validation errors
            self.metrics["error_count"] += 1
            raise

        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Error analyzing news with GLM: {e}")

            # On API error, return fallback result
            # This allows the pipeline to continue gracefully
            return {
                "tickers": [],
                "sectors": [],
                "confidence": 0.0,
                "reasoning": f"API error: {str(e)}",
                "analyzed_at": datetime.now().isoformat(),
                "model": self.model,
                "latency_ms": int((time.time() - start_time) * 1000),
                "cost_usd": 0.0,
                "error": str(e)
            }

    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> Dict:
        """
        API 호출 (async with exponential backoff retry).

        Args:
            messages: 메시지 리스트 (OpenAI 호환 형식)
            max_tokens: 최대 토큰 수
            temperature: 온도 설정

        Returns:
            API 응답 딕셔너리

        Raises:
            Exception: 재시도 실패 시
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        session = await self._get_session()

        for attempt in range(self.MAX_RETRY):
            try:
                logger.debug(f"API 호출 시도 {attempt + 1}/{self.MAX_RETRY}")

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise ValueError("인증 실패: API 키를 확인해주세요.")
                    elif response.status == 429:
                        text = await response.text()
                        # Check if it's a balance issue (error code 1113)
                        if "1113" in text or "余额不足" in text:
                            logger.error("GLM API 잔액 부족: 계정을 충전해주세요.")
                            raise ValueError("GLM API 잔액 부족. 계정을 충전해주세요: https://z.ai/manage-apikey/billing")
                        else:
                            # Exponential backoff for rate limit
                            delay = self._calculate_retry_delay(attempt)
                            logger.warning(f"Rate limit 초과, {delay:.1f}초 후 재시도...")
                            await asyncio.sleep(delay)
                            continue
                    else:
                        text = await response.text()
                        raise Exception(f"API 오류: {response.status} - {text}")

            except asyncio.TimeoutError:
                self.metrics["timeout_count"] += 1
                delay = self._calculate_retry_delay(attempt)
                logger.warning(f"타임아웃 ({self.timeout}s), {delay:.1f}초 후 재시도 {attempt + 1}/{self.MAX_RETRY}")

                if attempt < self.MAX_RETRY - 1:
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"타임아웃: {self.MAX_RETRY}회 재시도 후 실패")

            except ValueError as e:
                # Re-raise validation errors immediately
                raise

            except Exception as e:
                logger.error(f"요청 실패: {e}")
                if attempt == self.MAX_RETRY - 1:
                    raise

                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)

        raise Exception(f"최대 재시도 횟수 ({self.MAX_RETRY}) 초과")

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Formula: min(BASE_DELAY * 2^attempt, MAX_DELAY)

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.BASE_RETRY_DELAY * (2 ** attempt)
        return min(delay, self.MAX_RETRY_DELAY)

    def _build_prompt(self, news_text: str) -> str:
        """
        GLM 프롬프트를 빌드합니다.

        Prompt Engineering:
        - 명확한 역할 정의 (금융 애널리스트)
        - JSON 출력 형식 요구
        - 종목/섹터 추출 가이드
        """
        # Truncate news text if too long
        truncated_text = news_text[:2000] if len(news_text) > 2000 else news_text

        prompt = f"""당신은 뉴스 기사에서 관련 종목과 섹터를 식별하는 금융 애널리스트입니다.

다음 뉴스 기사를 분석하여:
1. 언급된 종목 심볼 (예: AAPL, TSLA, NVDA)
2. 관련 섹터 (예: Technology, Semiconductors, Financials)
3. 분석 신뢰도 (0.0 ~ 1.0)
4. 분석 근거

**뉴스 기사:**
{truncated_text}

**출력 형식 (JSON):**
{{
    "tickers": ["AAPL", "TSLA"],
    "sectors": ["Technology", "Semiconductors"],
    "confidence": 0.87,
    "reasoning": "분석 근거 설명"
}}

**지침:**
- ticker는 반드시 대문자 심볼로 (예: AAPL, not Apple)
- 섹터는 영문 표준 이름 사용
- 신뢰도는 뉴스가 종목과 직접 관련된 정도에 따라 0~1 사이 값
- 관련 종목이 없으면 tickers를 빈 배열로 반환
"""
        return prompt

    def _parse_response(self, response: Dict, news_preview: str) -> Dict:
        """
        GLM API 응답을 파싱합니다.

        Args:
            response: API 응답 JSON (OpenAI 호환 형식)
            news_preview: 뉴스 미리보기 (reasoning용)

        Returns:
            파싱된 결과 딕셔너리
        """
        try:
            # OpenAI 호환 응답 형식
            message = response["choices"][0]["message"]
            # GLM-4.7 uses reasoning_content for reasoning models
            content = message.get("content") or message.get("reasoning_content", "")

            # Try to parse as JSON
            try:
                parsed = json.loads(content)

                # Validate structure
                tickers = parsed.get("tickers", [])
                sectors = parsed.get("sectors", [])
                confidence = float(parsed.get("confidence", 0.5))
                reasoning = parsed.get("reasoning", "")

                # Normalize tickers to uppercase
                tickers = [t.upper() for t in tickers if isinstance(t, str) and t.strip()]

                return {
                    "tickers": tickers,
                    "sectors": sectors,
                    "confidence": max(0.0, min(1.0, confidence)),  # Clamp to [0, 1]
                    "reasoning": reasoning or f"Analysis based on: {news_preview}",
                    "analyzed_at": datetime.now().isoformat(),
                    "model": self.model,
                }

            except json.JSONDecodeError:
                # JSON parsing failed, try to extract from text
                logger.warning(f"Failed to parse GLM response as JSON, using fallback extraction")

                # Fallback: look for ticker patterns
                import re
                ticker_pattern = r'\b[A-Z]{2,5}\b'
                potential_tickers = list(set(re.findall(ticker_pattern, content)))

                return {
                    "tickers": potential_tickers[:10],  # Limit to 10
                    "sectors": [],
                    "confidence": 0.3,  # Low confidence for fallback
                    "reasoning": f"Fallback extraction from: {content[:200]}",
                    "analyzed_at": datetime.now().isoformat(),
                    "model": self.model,
                }

        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Error parsing GLM response: {e}")

            # Return empty result on parse error
            return {
                "tickers": [],
                "sectors": [],
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}",
                "analyzed_at": datetime.now().isoformat(),
                "model": self.model,
            }

    def get_metrics(self) -> Dict:
        """
        현재 메트릭을 반환합니다.

        Returns:
            {
                "total_requests": int,
                "total_cost_usd": float,
                "avg_latency_ms": float,
                "success_count": int,
                "error_count": int,
                "success_rate": float
            }
        """
        total = self.metrics["total_requests"]
        success_rate = (
            self.metrics["success_count"] / total
            if total > 0 else 0.0
        )

        return {
            **self.metrics,
            "success_rate": success_rate,
        }

    def reset_metrics(self):
        """메트릭을 초기화합니다."""
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "success_count": 0,
            "error_count": 0,
            "timeout_count": 0,
        }
        logger.info("GLMClient metrics reset")


class MockGLMClient:
    """
    Mock GLMClient for testing (no API calls).

    Uses predefined mock responses based on news content keywords.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize mock client (api_key ignored)."""
        self.model = "glm-4-flash-mock"
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "success_count": 0,
            "error_count": 0,
        }

        # Keyword-based mock responses
        self.mock_responses = {
            "apple": {"tickers": ["AAPL"], "sectors": ["Technology"], "confidence": 0.9},
            "tesla": {"tickers": ["TSLA"], "sectors": ["Technology", "Automotive"], "confidence": 0.9},
            "nvidia": {"tickers": ["NVDA"], "sectors": ["Technology", "Semiconductors"], "confidence": 0.95},
            "google": {"tickers": ["GOOGL"], "sectors": ["Technology"], "confidence": 0.85},
            "microsoft": {"tickers": ["MSFT"], "sectors": ["Technology"], "confidence": 0.85},
            "amazon": {"tickers": ["AMZN"], "sectors": ["Technology", "E-Commerce"], "confidence": 0.85},
        }

    async def analyze_news(self, news_text: str, **kwargs) -> Dict:
        """Mock news analysis."""
        if not news_text or not news_text.strip():
            raise ValueError("news_text cannot be empty")

        start_time = time.time()
        news_lower = news_text.lower()

        # Find matching tickers based on keywords
        tickers = []
        sectors = []
        max_confidence = 0.0

        for keyword, response in self.mock_responses.items():
            if keyword in news_lower:
                tickers.extend(response["tickers"])
                sectors.extend(response["sectors"])
                max_confidence = max(max_confidence, response["confidence"])

        # Remove duplicates
        tickers = list(set(tickers))
        sectors = list(set(sectors))

        latency_ms = int((time.time() - start_time) * 1000) + 100  # Add mock latency

        self.metrics["total_requests"] += 1
        self.metrics["success_count"] += 1
        self.metrics["avg_latency_ms"] = latency_ms

        return {
            "tickers": tickers,
            "sectors": sectors,
            "confidence": max_confidence if tickers else 0.3,
            "reasoning": f"Mock analysis based on keywords: {list(self.mock_responses.keys())}",
            "analyzed_at": datetime.now().isoformat(),
            "model": self.model,
            "latency_ms": latency_ms,
            "cost_usd": 0.0,
        }

    async def close(self):
        """Mock close (no-op)."""
        pass

    def get_metrics(self) -> Dict:
        """Get mock metrics."""
        return {
            **self.metrics,
            "success_rate": 1.0,  # Mock never fails
        }

    def reset_metrics(self):
        """Reset mock metrics."""
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "success_count": 0,
            "error_count": 0,
        }


# Convenience function for synchronous usage
async def analyze_news_async(news_text: str, api_key: Optional[str] = None) -> Dict:
    """
    Async convenience function for news analysis.

    Args:
        news_text: 뉴스 기사 내용
        api_key: GLM API key (optional)

    Returns:
        분석 결과 딕셔너리
    """
    client = GLMClient(api_key=api_key)
    try:
        return await client.analyze_news(news_text)
    finally:
        await client.close()
