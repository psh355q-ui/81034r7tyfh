"""
GLM-4.7 Client (Improved Version)

Improvements:
1. Better timeout configuration (configurable per request)
2. Connection pooling with limit
3. Proper session context management
4. Exponential backoff retry
5. Better error handling and logging
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import aiohttp

logger = logging.getLogger(__name__)


class GLMClient:
    """
    Improved GLM-4.7 client with better connection management.
    """

    # Pricing
    COST_PER_REQUEST = 0.001

    # API Configuration
    DEFAULT_API_URL = "https://api.z.ai/api/coding/paas/v4/chat/completions"
    DEFAULT_MODEL = "GLM-4.7"

    # Improved timeouts (in seconds)
    DEFAULT_TIMEOUT = 30  # Reduced from 60 to 30
    CONNECT_TIMEOUT = 10  # Connection timeout
    READ_TIMEOUT = 20     # Read timeout

    # Retry configuration
    MAX_RETRY = 3
    BASE_RETRY_DELAY = 0.5  # Base delay for exponential backoff
    MAX_RETRY_DELAY = 5     # Maximum retry delay

    # Connection pooling
    MAX_CONNECTIONS = 10    # Maximum concurrent connections
    MAX_PER_HOST = 5        # Maximum connections per host

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize GLM client with improved configuration.

        Args:
            api_key: GLM API key (default: from GLM_API_KEY env var)
            model: Model name (default: GLM-4.7)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY environment variable not set")

        self.model = model or os.environ.get("GLM_MODEL", self.DEFAULT_MODEL)
        self.api_url = os.environ.get("GLM_API_URL", self.DEFAULT_API_URL)
        self.timeout = timeout or int(os.environ.get("GLM_TIMEOUT", self.DEFAULT_TIMEOUT))

        # Session management with connection pooling
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
                ttl_dns_cache=300,  # Cache DNS for 5 minutes
                enable_cleanup_closed=True,  # Clean up closed connections
            )
        return self._connector

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration."""
        if self._session is None or self._session.closed:
            connector = await self._get_connector()

            # Configure timeout with separate connect/read timeouts
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=self.CONNECT_TIMEOUT,
                sock_read=self.READ_TIMEOUT
            )

            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True,  # Respect proxy settings from environment
            )

        return self._session

    @asynccontextmanager
    async def _get_session_context(self):
        """
        Context manager for session usage.
        Ensures proper cleanup even on errors.
        """
        session = await self._get_session()
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            raise

    async def close(self):
        """
        Close HTTP session and connector properly.

        This should be called when done using the client.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            # Wait for connections to close
            try:
                await asyncio.sleep(0.25)
            except Exception:
                pass

        if self._connector and not self._connector.closed:
            await self._connector.close()
            try:
                await asyncio.sleep(0.1)
            except Exception:
                pass

        logger.debug("GLMClient session closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.3,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Chat completions with improved error handling.

        Args:
            messages: Message list in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Override default timeout for this request

        Returns:
            API response dict with "choices" key
        """
        return await self._call_api(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )

    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.3,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        API 호출 with exponential backoff retry.

        Args:
            messages: 메시지 리스트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            timeout: 이 요청의 타임아웃 (기본값 사용)

        Returns:
            API 응답 딕셔너리
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

        request_timeout = timeout or self.timeout

        for attempt in range(self.MAX_RETRY):
            try:
                logger.debug(f"API 호출 시도 {attempt + 1}/{self.MAX_RETRY}")

                async with self._get_session_context() as session:
                    # Override timeout for this specific request
                    if timeout:
                        session_timeout = aiohttp.ClientTimeout(
                            total=timeout,
                            connect=self.CONNECT_TIMEOUT,
                            sock_read=min(timeout - 5, self.READ_TIMEOUT)
                        )
                    else:
                        session_timeout = None

                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=session_timeout
                    ) as response:
                        if response.status == 200:
                            return await response.json()

                        elif response.status == 401:
                            raise ValueError("인증 실패: API 키를 확인해주세요.")

                        elif response.status == 429:
                            text = await response.text()
                            # Check if it's a balance issue
                            if "1113" in text or "余额不足" in text:
                                logger.error("GLM API 잔액 부족")
                                raise ValueError("GLM API 잔액 부족. 충전이 필요합니다.")

                            # Rate limit - use exponential backoff
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
                logger.warning(f"타임아웃 ({request_timeout}s), {delay:.1f}초 후 재시도 {attempt + 1}/{self.MAX_RETRY}")

                if attempt < self.MAX_RETRY - 1:
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"타임아웃: {self.MAX_RETRY}회 재시도 후 실패")

            except ValueError:
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

    async def analyze_news(
        self,
        news_text: str,
        **kwargs
    ) -> Dict:
        """
        뉴스 기사 분석 (개선된 버전).

        Args:
            news_text: 뉴스 기사 내용
            **kwargs: 추가 옵션

        Returns:
            분석 결과 딕셔너리
        """
        if not news_text or not news_text.strip():
            raise ValueError("news_text cannot be empty")

        start_time = time.time()

        try:
            prompt = self._build_prompt(news_text)

            response = await self._call_api(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst extracting stock tickers and sectors from news articles."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get("max_tokens", 500),
                temperature=kwargs.get("temperature", 0.3)
            )

            result = self._parse_response(response, news_text[:100])
            latency_ms = int((time.time() - start_time) * 1000)

            result["latency_ms"] = latency_ms
            result["cost_usd"] = self.COST_PER_REQUEST

            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_cost_usd"] += self.COST_PER_REQUEST
            self.metrics["success_count"] += 1

            logger.info(f"GLM analysis complete: latency={latency_ms}ms")

            return result

        except Exception as e:
            self.metrics["error_count"] += 1
            logger.error(f"Error analyzing news: {e}")

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

    def _build_prompt(self, news_text: str) -> str:
        """Build analysis prompt."""
        truncated_text = news_text[:2000] if len(news_text) > 2000 else news_text

        prompt = f"""Extract stock tickers and sectors from this news:

{truncated_text}

Return JSON format:
{{
    "tickers": ["AAPL", "TSLA"],
    "sectors": ["Technology", "Semiconductors"],
    "confidence": 0.87,
    "reasoning": "Analysis explanation"
}}
"""
        return prompt

    def _parse_response(self, response: Dict, news_preview: str) -> Dict:
        """Parse API response."""
        try:
            message = response["choices"][0]["message"]
            content = message.get("content") or message.get("reasoning_content", "")

            try:
                parsed = json.loads(content)
                return {
                    "tickers": parsed.get("tickers", []),
                    "sectors": parsed.get("sectors", []),
                    "confidence": float(parsed.get("confidence", 0.5)),
                    "reasoning": parsed.get("reasoning", ""),
                    "analyzed_at": datetime.now().isoformat(),
                    "model": self.model,
                }
            except json.JSONDecodeError:
                # Fallback extraction
                import re
                ticker_pattern = r'\b[A-Z]{2,5}\b'
                tickers = list(set(re.findall(ticker_pattern, content)))

                return {
                    "tickers": tickers[:10],
                    "sectors": [],
                    "confidence": 0.3,
                    "reasoning": f"Fallback extraction",
                    "analyzed_at": datetime.now().isoformat(),
                    "model": self.model,
                }

        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Error parsing response: {e}")
            return {
                "tickers": [],
                "sectors": [],
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}",
                "analyzed_at": datetime.now().isoformat(),
                "model": self.model,
            }

    def get_metrics(self) -> Dict:
        """Get current metrics."""
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
        """Reset metrics."""
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "success_count": 0,
            "error_count": 0,
            "timeout_count": 0,
        }
        logger.info("GLMClient metrics reset")


# Singleton instance for reuse
_glm_client_instance: Optional[GLMClient] = None


def get_glm_client() -> GLMClient:
    """
    Get or create singleton GLM client instance.

    This allows reusing connections across multiple calls.

    Returns:
        GLMClient instance

    Example:
        client = get_glm_client()
        try:
            result = await client.analyze_news(news_text)
        finally:
            await client.close()
    """
    global _glm_client_instance
    if _glm_client_instance is None:
        _glm_client_instance = GLMClient()
    return _glm_client_instance


async def close_glm_client():
    """Close the singleton GLM client."""
    global _glm_client_instance
    if _glm_client_instance is not None:
        await _glm_client_instance.close()
        _glm_client_instance = None
