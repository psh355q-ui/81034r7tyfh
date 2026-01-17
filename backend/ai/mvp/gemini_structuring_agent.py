"""
Gemini Structuring Agent - Stage 2 of Two-Stage Architecture

Phase: MVP Consolidation - Gemini Integration
Date: 2026-01-17

Purpose:
    Reasoning Agent의 자연어 출력을 JSON으로 변환하는 구조화 에이전트
    - 텍스트에서 필수 필드 추출
    - Pydantic 스키마 준수
    - 누락 필드는 기본값으로 대체
    - 낮은 temperature로 안정적 출력

Two-Stage Architecture:
    Stage 1: GeminiReasoningAgent → Gemini 추론 → 자연어 텍스트
    Stage 2: GeminiStructuringAgent (this file) → 텍스트를 JSON으로 변환 → Pydantic 스키마

Benefits:
    - 높은 Concurrency 제한
    - 빠른 JSON 추출
    - 비용 절감
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Type, TypeVar
from datetime import datetime
from pydantic import BaseModel

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class GeminiStructuringAgent:
    """
    Converts natural language reasoning to structured JSON using Gemini

    Uses JSON response mode for reliable extraction.
    Low temperature (0.1) ensures consistent output.
    """

    def __init__(self):
        """Initialize Gemini Structuring Agent"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI not available. Install with: pip install google-generativeai")

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Stage 2 (Structuring) uses Gemini 2.5 Flash Lite with JSON mode (latest, not deprecated)
        self.model_name = os.getenv('GEMINI_MODEL_STRUCTURING', 'gemini-2.5-flash-lite')

        # Use JSON response mode
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        )

        self.system_prompt = self._load_system_prompt()

        logger.info(f"GeminiStructuringAgent initialized with model {self.model_name}")

    def _load_system_prompt(self) -> str:
        """Load structuring system prompt"""
        return """당신은 JSON 구조화 전문가입니다.

## 작업
제공된 텍스트에서 JSON 스키마에 맞는 정보를 추출하십시오.

## 규칙
1. 반드시 유효한 JSON만 출력하십시오
2. 텍스트에 없는 필드는 기본값을 사용하십시오
3. 수치 필드는 반드시 숫자로 변환하십시오
4. confidence는 0.0 ~ 1.0 사이의 값이어야 합니다
5. action은 'buy', 'sell', 'hold', 'pass' 중 하나여야 합니다
6. risk_level은 'low', 'medium', 'high', 'extreme' 중 하나여야 합니다

## 중요
- 응답은 반드시 JSON 형식이어야 합니다
- JSON 앞뒤에 아무런 텍스트도 추가하지 마십시오"""

    async def structure(
        self,
        reasoning_text: str,
        schema_definition: Dict[str, Any],
        agent_type: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Convert reasoning text to structured JSON using Gemini

        Args:
            reasoning_text: Natural language output from Reasoning Agent
            schema_definition: JSON schema definition showing expected fields
            agent_type: Type of agent ('trader', 'risk', 'analyst')
            symbol: Stock symbol

        Returns:
            Dict with structured data matching schema
        """
        # Build structuring prompt
        prompt = self._build_structuring_prompt(
            reasoning_text=reasoning_text,
            schema_definition=schema_definition,
            agent_type=agent_type
        )

        # Call Gemini with JSON response mode
        try:
            # Run Gemini in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            full_prompt = f"{self.system_prompt}\n\n{prompt}"

            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(full_prompt)
            )

            response_text = response.text.strip()

            # Log raw response for debugging
            logger.info(f"Gemini response for {agent_type}: {response_text[:200]}...")

            # Parse JSON (Gemini with JSON mode should return clean JSON)
            try:
                result_dict = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback to extraction method
                result_dict = self._extract_json(response_text)

            # Log extraction result
            confidence = result_dict.get('confidence', 0)
            if confidence > 0:
                logger.info(f"✅ {agent_type} Gemini structuring successful: action={result_dict.get('action')}, confidence={confidence}")
            else:
                logger.warning(f"⚠️ {agent_type} Gemini structuring produced low confidence: {result_dict}")

            # Add metadata
            result_dict['agent'] = f'{agent_type}_gemini_mvp'
            result_dict['timestamp'] = datetime.utcnow().isoformat()
            result_dict['symbol'] = symbol
            result_dict['stage'] = 'structured'
            result_dict['llm_provider'] = 'gemini'

            return result_dict

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini structuring failed: {e}")

            # Return safe default based on agent type for errors
            return self._get_default_result(agent_type, symbol, error_msg)

    def _build_structuring_prompt(
        self,
        reasoning_text: str,
        schema_definition: Dict[str, Any],
        agent_type: str
    ) -> str:
        """Build structuring prompt"""
        prompt = f"""## 추론 텍스트
{reasoning_text}

## JSON 스키마
{json.dumps(schema_definition, ensure_ascii=False, indent=2)}

## 작업
위 추론 텍스트를 분석하여 JSON 스키마에 맞는 객체를 생성하십시오.
텍스트에 언급되지 않은 필드는 기본값을 사용하십시오.

반드시 유효한 JSON만 출력하십시오."""

        return prompt

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response text (fallback method)"""
        # Try direct JSON parsing first
        try:
            result = json.loads(text)
            logger.info("Direct JSON parsing successful")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")

        # Try to extract from markdown code block
        import re

        # Pattern 1: ```json ... ```
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                logger.info("JSON extracted from ```json block")
                return result
            except json.JSONDecodeError:
                logger.debug("```json block parsing failed")

        # Pattern 2: Just find first { ... } pattern
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                logger.info("JSON extracted using regex pattern")
                return result
            except json.JSONDecodeError:
                logger.debug("Regex pattern parsing failed")

        # If all fails, return minimal valid JSON
        logger.warning(f"Could not extract JSON from response. Response was: {text[:200]}")
        return {"action": "pass", "confidence": 0.0}

    def _get_default_result(self, agent_type: str, symbol: str, error: str) -> Dict[str, Any]:
        """Return safe default result on error"""
        if agent_type == 'trader':
            return {
                'agent': 'trader_gemini_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'opportunity_score': 0.0,
                'momentum_strength': 'weak',
                'risk_reward_ratio': 1.0,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'llm_provider': 'gemini',
                'error': error
            }
        elif agent_type == 'risk':
            return {
                'agent': 'risk_gemini_mvp',
                'risk_level': 'high',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'max_position_pct': 0.05,
                'recommendation': 'reject',
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'llm_provider': 'gemini',
                'error': error
            }
        elif agent_type == 'analyst':
            return {
                'agent': 'analyst_gemini_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'news_headline': '분석 실패',
                'news_sentiment': 'neutral',
                'overall_score': 0.0,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'llm_provider': 'gemini',
                'error': error
            }
        else:
            return {
                'agent': f'{agent_type}_gemini_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'llm_provider': 'gemini',
                'error': error
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'GeminiStructuringAgent',
            'role': 'JSON 구조화 전문가',
            'stage': 'structuring',
            'model': self.model_name,
            'llm_provider': 'gemini',
            'focus': '텍스트를 JSON으로 변환',
            'output_format': 'valid JSON only',
            'benefits_over_glm': [
                '높은 Concurrency 제한 (60+ vs 3)',
                'JSON response mode 지원',
                '빠른 응답 속도',
                '비용 효율성'
            ],
            'responsibilities': [
                '추론 텍스트에서 필드 추출',
                'Pydantic 스키마 준수',
                '누락 필드 기본값 처리',
                '안정적 JSON 출력'
            ]
        }
