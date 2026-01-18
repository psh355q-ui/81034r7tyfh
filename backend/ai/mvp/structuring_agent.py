"""
Structuring Agent - Stage 2 of Two-Stage Architecture

Phase: MVP Consolidation
Date: 2026-01-17

Purpose:
    Reasoning Agent의 자연어 출력을 JSON으로 변환하는 구조화 에이전트
    - 텍스트에서 필수 필드 추출
    - Pydantic 스키마 준수
    - 누락 필드는 기본값으로 대체
    - 낮은 temperature로 안정적 출력

Two-Stage Architecture:
    Stage 1: ReasoningAgent → GLM-4.7 추론 → 자연어 텍스트
    Stage 2: StructuringAgent (this file) → 텍스트를 JSON으로 변환 → Pydantic 스키마
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Type, TypeVar
from datetime import datetime
from pydantic import BaseModel

try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class StructuringAgent:
    """
    Converts natural language reasoning to structured JSON

    Uses lightweight prompt engineering for reliable JSON extraction.
    Low temperature (0.1) ensures consistent output.
    """

    def __init__(self):
        """Initialize Structuring Agent"""
        if not GLM_AVAILABLE:
            raise ImportError("GLM client not available. Install with: pip install zhipuai")

        api_key = os.getenv('GLM_API_KEY')
        if not api_key:
            raise ValueError("GLM_API_KEY not found in environment variables")

        # Stage 2 (Structuring) uses GLM-4.6V-FlashX for fast JSON extraction
        self.model = os.getenv('GLM_MODEL_STRUCTURING', 'glm-4.6v-flashx')
        self.glm_client = GLMClient(api_key=api_key, model=self.model)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load structuring system prompt"""
        return """당신은 JSON 구조화 전문가입니다.

## 작업
제공된 텍스트에서 JSON 스키마에 맞는 정보를 추출하십시오.

## 규칙
1. 반드시 유효한 JSON만 출력하십시오 (마크다운 코드 블록 없이)
2. 텍스트에 없는 필드는 기본값을 사용하십시오
3. 수치 필드는 반드시 숫자로 변환하십시오
4. confidence는 0.0 ~ 1.0 사이의 값이어야 합니다
5. action은 'buy', 'sell', 'hold', 'pass' 중 하나여야 합니다
6. risk_level은 'low', 'medium', 'high', 'extreme' 중 하나여야 합니다

## 출력 형식
JSON 객체만 출력하십시오. 설명이나 추가 텍스트 없이 JSON만 반환하십시오.

## 중요
- 응답은 반드시 {로 시작하고 }로 끝나는 JSON 형식이어야 합니다
- 마크다운 코드 블록(\`\`\`)을 사용하지 마십시오
- JSON 앞뒤에 아무런 텍스트도 추가하지 마십시오"""

    async def structure(
        self,
        reasoning_text: str,
        schema_definition: Dict[str, Any],
        agent_type: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Convert reasoning text to structured JSON

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

        # Call GLM with low temperature for consistent JSON
        try:
            response = await self.glm_client.chat(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1  # Low temp for consistent JSON
            )

            # Extract JSON from response
            message = response["choices"][0]["message"]

            # GLM reasoning models use 'reasoning_content', regular models use 'content'
            response_text = (
                message.get("content") or
                message.get("reasoning_content") or
                ""
            ).strip()

            # Log raw response for debugging
            logger.info(f"GLM-4.5-Flash response for {agent_type}: {response_text[:500]}...")

            # Parse JSON
            result_dict = self._extract_json(response_text)

            # Log extraction result
            if result_dict.get('confidence', 0) > 0:
                logger.info(f"✅ {agent_type} structuring successful: action={result_dict.get('action')}, confidence={result_dict.get('confidence')}")
            else:
                logger.warning(f"⚠️ {agent_type} structuring produced low confidence: {result_dict}")

            # Add metadata
            result_dict['agent'] = f'{agent_type}_mvp'
            result_dict['timestamp'] = datetime.utcnow().isoformat()
            result_dict['symbol'] = symbol
            result_dict['stage'] = 'structured'

            return result_dict

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Structuring failed: {e}")

            # Fallback: Try to extract from reasoning text directly if API balance issue
            if '잔액 부족' in error_msg or 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                logger.warning(f"GLM API balance insufficient, attempting fallback extraction from reasoning text...")
                return self._fallback_extraction(reasoning_text, agent_type, symbol, error_msg)

            # Return safe default based on agent type for other errors
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
        """Extract JSON from response text"""
        # Log the raw response for debugging
        logger.debug(f"GLM-4.5-Flash raw response: {text[:500]}...")

        # Try direct JSON parsing first
        try:
            result = json.loads(text)
            logger.info("Direct JSON parsing successful")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")

        # Try to extract from markdown code block (various patterns)
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

        # Pattern 2: ``` ... ``` (without json keyword)
        json_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                logger.info("JSON extracted from ``` block (no json keyword)")
                return result
            except json.JSONDecodeError:
                logger.debug("``` block parsing failed")

        # Pattern 3: Just find first { ... } pattern
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                logger.info("JSON extracted using regex pattern")
                return result
            except json.JSONDecodeError:
                logger.debug("Regex pattern parsing failed")

        # Find JSON object by brace counting (most robust)
        brace_count = 0
        start_idx = None
        result = None

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    try:
                        candidate = text[start_idx:i+1]
                        parsed = json.loads(candidate)
                        result = parsed  # Keep LAST valid JSON
                        logger.info(f"JSON extracted via brace counting at position {start_idx}")
                    except json.JSONDecodeError:
                        pass
                    start_idx = None

        if result:
            return result

        # If all fails, return minimal valid JSON
        logger.warning(f"Could not extract JSON from response. Response was: {text[:200]}")
        return {"action": "pass", "confidence": 0.0}

    def _fallback_extraction(
        self,
        reasoning_text: str,
        agent_type: str,
        symbol: str,
        error_msg: str
    ) -> Dict[str, Any]:
        """
        Fallback extraction from reasoning text when GLM API is unavailable.

        Uses regex patterns to extract structured data from reasoning text.
        This is used when API balance is insufficient or other API errors occur.

        Args:
            reasoning_text: Natural language reasoning from Stage 1
            agent_type: Type of agent ('trader', 'risk', 'analyst')
            symbol: Stock symbol
            error_msg: Original error message

        Returns:
            Dict with structured data extracted from reasoning text
        """
        import re

        logger.info(f"🔄 Using fallback extraction for {agent_type} agent")

        # Initialize result with base metadata
        result = {
            'agent': f'{agent_type}_mvp',
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'stage': 'structured_fallback',
            'fallback_reason': error_msg,
            'reasoning': reasoning_text[:2000] + '...' if len(reasoning_text) > 2000 else reasoning_text
        }

        # Extract action/decision using keyword patterns
        text_lower = reasoning_text.lower()

        # Common action patterns (Korean + English)
        buy_patterns = [
            r'(매수|buy|long|진입|구매|추천)',
            r'(기회|opportunity|매수\s*기회)',
            r'(긍정적|positive|bullish|상승|강세)'
        ]
        sell_patterns = [
            r'(매도|sell|short|청산|판매)',
            r'(위험|risk|리스크|하락|약세|bearish)'
        ]
        hold_patterns = [
            r'(관망|hold|holdings|유지|대기)'
        ]
        pass_patterns = [
            r'(pass|건너뜀|제외|무시)'
        ]

        # Score each pattern
        buy_score = sum(1 for p in buy_patterns if re.search(p, text_lower, re.IGNORECASE))
        sell_score = sum(1 for p in sell_patterns if re.search(p, text_lower, re.IGNORECASE))
        hold_score = sum(1 for p in hold_patterns if re.search(p, text_lower, re.IGNORECASE))
        pass_score = sum(1 for p in pass_patterns if re.search(p, text_lower, re.IGNORECASE))

        # Determine action based on highest score
        scores = {'buy': buy_score, 'sell': sell_score, 'hold': hold_score, 'pass': pass_score}
        action = max(scores, key=scores.get)

        # If all scores are 0, default to pass
        if scores[action] == 0:
            action = 'pass'

        # Agent-specific extraction
        if agent_type == 'trader':
            result.update({
                'action': action,
                'confidence': min(0.6, 0.3 + scores[action] * 0.1),  # Base 0.3, +0.1 per match
                'opportunity_score': min(100, 30 + buy_score * 20 - sell_score * 10),
                'momentum_strength': 'strong' if buy_score >= 2 else 'moderate' if buy_score == 1 else 'weak',
                'risk_reward_ratio': 1.5 if buy_score >= 2 else 1.2 if buy_score == 1 else 1.0
            })

        elif agent_type == 'risk':
            # Risk agent: more buy patterns = lower risk, more sell patterns = higher risk
            risk_keywords = re.findall(r'(극도|extreme|매우|very|높음|high)', text_lower, re.IGNORECASE)
            risk_level = 'extreme' if len(risk_keywords) >= 3 or sell_score >= 3 else \
                        'high' if len(risk_keywords) >= 2 or sell_score >= 2 else \
                        'medium' if sell_score >= 1 else 'low'

            result.update({
                'risk_level': risk_level,
                'confidence': min(0.6, 0.3 + sell_score * 0.1),  # More risk signals = more confident
                'stop_loss_pct': 0.03 if risk_level == 'low' else 0.05 if risk_level == 'medium' else 0.07,
                'take_profit_pct': 0.06 if risk_level == 'low' else 0.10 if risk_level == 'medium' else 0.15,
                'max_position_pct': 0.10 if risk_level == 'low' else 0.05 if risk_level == 'medium' else 0.02,
                'recommendation': 'approve' if buy_score >= 2 and risk_level in ['low', 'medium'] else 'reject'
            })

        elif agent_type == 'analyst':
            # Analyst: look for sentiment keywords
            positive_keywords = re.findall(
                r'(긍정적|positive|좋음|good|성장|growth|기회|opportunity)',
                text_lower, re.IGNORECASE
            )
            negative_keywords = re.findall(
                r'(부정적|negative|나쁨|bad|위험|risk|리스크|우려)',
                text_lower, re.IGNORECASE
            )

            sentiment = 'positive' if len(positive_keywords) > len(negative_keywords) else \
                       'negative' if len(negative_keywords) > len(positive_keywords) else 'neutral'

            overall_score = 5 + len(positive_keywords) * 1.5 - len(negative_keywords) * 1.0
            overall_score = max(0, min(10, overall_score))  # Clamp between 0-10

            result.update({
                'action': 'buy' if sentiment == 'positive' and overall_score >= 6 else 'pass',
                'confidence': min(0.6, 0.3 + abs(len(positive_keywords) - len(negative_keywords)) * 0.1),
                'news_headline': reasoning_text[:100] + '...' if len(reasoning_text) > 100 else reasoning_text,
                'news_sentiment': sentiment,
                'overall_score': overall_score
            })

        logger.info(f"✅ Fallback extraction successful: action={action}, confidence={result.get('confidence', 0):.2f}")
        return result

    def _get_default_result(self, agent_type: str, symbol: str, error: str) -> Dict[str, Any]:
        """Return safe default result on error"""
        if agent_type == 'trader':
            return {
                'agent': 'trader_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'opportunity_score': 0.0,
                'momentum_strength': 'weak',
                'risk_reward_ratio': 1.0,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'error': error
            }
        elif agent_type == 'risk':
            return {
                'agent': 'risk_mvp',
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
                'error': error
            }
        elif agent_type == 'analyst':
            return {
                'agent': 'analyst_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'news_headline': '분석 실패',
                'news_sentiment': 'neutral',
                'overall_score': 0.0,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'error': error
            }
        else:
            return {
                'agent': f'{agent_type}_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'구조화 실패: {error}',
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'structured',
                'error': error
            }

    async def close(self):
        """Close GLM client session."""
        if hasattr(self, 'glm_client') and self.glm_client:
            await self.glm_client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'StructuringAgent',
            'role': 'JSON 구조화 전문가',
            'stage': 'structuring',
            'model': self.model,
            'focus': '텍스트를 JSON으로 변환',
            'output_format': 'valid JSON only',
            'responsibilities': [
                '추론 텍스트에서 필드 추출',
                'Pydantic 스키마 준수',
                '누락 필드 기본값 처리',
                '안정적 JSON 출력'
            ]
        }
