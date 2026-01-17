"""
Trader Agent MVP - Attack (35% weight)

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    전문 트레이더의 공격적 관점
    - 단기 기회 포착 (Trader Agent 흡수)
    - 칩워 관련 기회 포착 (ChipWar Agent 일부 흡수)
    - 진입/청산 타이밍 제안

Key Responsibilities:
    1. 단기 트레이딩 기회 식별
    2. 기술적 진입/청산 시그널 생성
    3. 칩워 관련 단기 기회 포착
    4. 모멘텀 및 트렌드 분석

Absorbed Legacy Agents:
    - Trader Agent (100%)
    - ChipWar Agent (기회 포착 부분만)

API: Uses GLM-4.7 for cost efficiency (replaced Gemini)
"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Use GLM instead of Gemini for cost efficiency
try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False

from backend.ai.schemas.war_room_schemas import TraderOpinion

logger = logging.getLogger(__name__)


class TraderAgentMVP:
    """MVP Trader Agent - 공격적 트레이딩 기회 포착 (GLM-powered)"""

    def __init__(self):
        """Initialize Trader Agent MVP with GLM"""
        # GLM API 설정 (replaced Gemini)
        if not GLM_AVAILABLE:
            raise ImportError("GLM client not available. Install with: pip install zhipuai")

        api_key = os.getenv('GLM_API_KEY')
        if not api_key:
            raise ValueError("GLM_API_KEY not found in environment variables")

        self.glm_client = GLMClient(api_key=api_key)
        self.model = os.getenv('GLM_MODEL', 'glm-4-flash')

        # Agent configuration
        self.weight = 0.35  # 35% voting weight
        self.role = "공격적 트레이더"

        # Load system prompt from file (like CLAUDE.md)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from docs/prompts/trader_agent_mvp.md"""
        try:
            # Get project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            prompt_path = os.path.join(project_root, 'docs', 'prompts', 'trader_agent_mvp.md')

            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove the title line and extract the prompt
            lines = content.split('\n')
            prompt_lines = []
            for line in lines[1:]:  # Skip first line (title)
                prompt_lines.append(line)

            return '\n'.join(prompt_lines).strip()

        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_path}, using fallback prompt")
            return """당신은 'War Room'의 공격적 트레이더(Aggressive Trader)입니다.
분석 후 JSON으로 답변하세요."""
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return """당신은 'War Room'의 공격적 트레이더(Aggressive Trader)입니다.
분석 후 JSON으로 답변하세요."""

    async def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[list] = None,
        market_context: Optional[Dict[str, Any]] = None,
        multi_timeframe_data: Optional[Dict[str, Any]] = None, # [Phase 3]
        option_data: Optional[Dict[str, Any]] = None           # [Phase 3]
    ) -> Dict[str, Any]:
        """
        트레이딩 기회 분석
        
        Returns:
            Dict (compatible with TraderOpinion model)
        """
        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            chipwar_events=chipwar_events,

            market_context=market_context,
            multi_timeframe_data=multi_timeframe_data,
            option_data=option_data
        )

        # Call GLM API with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await self.glm_client.chat(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.3
                )

                # Parse response
                message = response["choices"][0]["message"]
                # GLM-4.7 uses reasoning_content for reasoning models
                response_text = (message.get("content") or message.get("reasoning_content", "")).strip()

                # Try to parse JSON
                try:
                    opinion = self._parse_response(response_text)

                    # Convert to dict for compatibility
                    result = opinion.model_dump()

                    # Add metadata (that are not in schema or overwrite defaults)
                    result['weight'] = self.weight
                    result['timestamp'] = datetime.utcnow().isoformat()
                    result['symbol'] = symbol

                    return result
                except ValueError as e:
                    # JSON parsing failed, retry
                    if str(e) == "No valid JSON found in response":
                        logger.warning(f"Attempt {attempt + 1}/{max_retries}: No JSON found, retrying...")
                        await asyncio.sleep(0.5)  # Brief delay before retry
                        continue
                    else:
                        raise

            except Exception as e:
                if attempt == max_retries - 1:
                    # Final retry failed, return safe default
                    return {
                        'agent': 'trader_mvp',
                        'action': 'pass',
                        'confidence': 0.0,
                        'reasoning': f'분석 실패 (재시도 {max_retries}회 후 실패): {str(e)}',
                        'opportunity_score': 0.0,
                        'momentum_strength': 'weak',
                        'weight': self.weight,
                        'timestamp': datetime.utcnow().isoformat(),
                        'symbol': symbol,
                        'error': str(e)
                    }
                else:
                    continue

        # Should not reach here, but just in case
        return {
            'agent': 'trader_mvp',
            'action': 'pass',
            'confidence': 0.0,
            'reasoning': '분석 실패: 알 수 없는 오류',
            'opportunity_score': 0.0,
            'momentum_strength': 'weak',
            'weight': self.weight,
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'error': 'Unknown error'
        }

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """
        Extract JSON from text for streaming callback.
        Returns the last valid JSON object with expected fields.
        """
        import json
        import re

        # Try direct JSON parsing first
        try:
            result = json.loads(text)
            # Validate it has expected fields
            if 'action' in result and 'confidence' in result:
                return result
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                if 'action' in result and 'confidence' in result:
                    return result
            except json.JSONDecodeError:
                pass

        # Find the LAST valid JSON object by forward scanning
        brace_count = 0
        start_idx = None

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    # Found a complete JSON object
                    try:
                        candidate = text[start_idx:i+1]
                        parsed = json.loads(candidate)
                        # Validate it has expected fields for our schema
                        expected_fields = ['action', 'confidence']
                        if any(field in parsed for field in expected_fields):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    # Reset for potential later JSON (we want the LAST one)
                    start_idx = None

        return None

    def _build_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]],
        chipwar_events: Optional[list],
        market_context: Optional[Dict[str, Any]],
        multi_timeframe_data: Optional[Dict[str, Any]] = None,
        option_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build analysis prompt"""
        prompt_parts = [
            f"종목: {symbol}",
            f"현재가: ${price_data.get('current_price', 'N/A')}",
            f"시가: ${price_data.get('open', 'N/A')}",
            f"고가: ${price_data.get('high', 'N/A')}",
            f"저가: ${price_data.get('low', 'N/A')}",
            f"거래량: {price_data.get('volume', 0):,}" if isinstance(price_data.get('volume'), (int, float)) else f"거래량: {price_data.get('volume', 'N/A')}",
        ]

        # Technical indicators
        if technical_data:
            prompt_parts.append("\n기술적 지표:")
            if 'rsi' in technical_data:
                prompt_parts.append(f"- RSI: {technical_data['rsi']:.2f}")
            if 'macd' in technical_data:
                macd = technical_data['macd']
                prompt_parts.append(f"- MACD: {macd.get('value', 0):.2f} (Signal: {macd.get('signal', 0):.2f})")
            if 'moving_averages' in technical_data:
                ma = technical_data['moving_averages']
                prompt_parts.append(f"- MA50: ${ma.get('ma50', 0):.2f}, MA200: ${ma.get('ma200', 0):.2f}")
            if 'bollinger_bands' in technical_data:
                bb = technical_data['bollinger_bands']
                prompt_parts.append(f"- Bollinger Bands: Upper ${bb.get('upper', 0):.2f}, Lower ${bb.get('lower', 0):.2f}")

        # ChipWar events
        if chipwar_events and len(chipwar_events) > 0:
            prompt_parts.append("\n칩워 관련 이벤트:")
            for event in chipwar_events[:3]:  # Top 3
                prompt_parts.append(f"- {event.get('event', 'N/A')} (영향: {event.get('impact', 'N/A')})")

        # Market context
        if market_context:
            prompt_parts.append("\n시장 맥락:")
            if 'market_trend' in market_context:
                prompt_parts.append(f"- 시장 트렌드: {market_context['market_trend']}")
            if 'sector_performance' in market_context:
                prompt_parts.append(f"- 섹터 성과: {market_context['sector_performance']:+.2f}%")
            if 'news_sentiment' in market_context:
                prompt_parts.append(f"- 뉴스 심리: {market_context['news_sentiment']:.2f}")
                
        # [Phase 3] Multi-Timeframe Analysis
        if multi_timeframe_data:
            prompt_parts.append("\n멀티 타임프레임 분석:")
            for tf, data in multi_timeframe_data.items():
                if data:
                    prompt_parts.append(f"- [{tf}] Price: {data.get('current_price')}, RSI: {data.get('rsi')}, Trend: {data.get('trend')}")

        # [Phase 3] Option Data
        if option_data:
            prompt_parts.append("\n옵션 데이터 분석:")
            prompt_parts.append(f"- P/C Ratio: {option_data.get('put_call_ratio', 'N/A')}")
            prompt_parts.append(f"- Max Pain: {option_data.get('max_pain', 'N/A')}")
            prompt_parts.append(f"- Volume: Call {option_data.get('total_call_volume', 0)} vs Put {option_data.get('total_put_volume', 0)}")

        prompt_parts.append("\n위 정보를 바탕으로 트레이딩 기회를 분석하고 JSON 형식으로 답변하세요.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> TraderOpinion:
        """Parse GLM response using Pydantic with default values for missing fields

        Extracts JSON from reasoning_content by finding the LAST valid JSON object,
        since GLM-4.7 outputs chain-of-thought first, then JSON at the end.
        """
        import json
        import re

        result_dict = None

        # Try direct JSON parsing first (response is pure JSON)
        try:
            result_dict = json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        if not result_dict:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    result_dict = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

        # Find the LAST valid JSON object by forward scanning
        # This is crucial for GLM-4.7 reasoning model which outputs: reasoning... then JSON
        # We scan forward and keep track of the LAST valid JSON (overwrites previous)
        if not result_dict:
            brace_count = 0
            start_idx = None

            for i, char in enumerate(response_text):
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx is not None:
                        # Found a complete JSON object
                        try:
                            candidate = response_text[start_idx:i+1]
                            parsed = json.loads(candidate)
                            # Validate it has expected fields for our schema
                            expected_fields = ['action', 'confidence']
                            if any(field in parsed for field in expected_fields):
                                # Keep overwriting with the LAST valid JSON
                                result_dict = parsed
                        except json.JSONDecodeError:
                            pass
                        # Reset for potential later JSON (we want the LAST one)
                        start_idx = None

        if not result_dict:
            raise ValueError("No valid JSON found in response")

        # Set default values for required fields if missing
        # This handles cases where GLM doesn't return all fields
        result_dict.setdefault('agent', 'trader_mvp')
        result_dict.setdefault('action', 'pass')
        result_dict.setdefault('confidence', 0.0)
        result_dict.setdefault('opportunity_score', 0.0)
        result_dict.setdefault('reasoning', 'No reasoning provided')

        # Normalize fields for Pydantic
        if 'momentum_strength' in result_dict:
             result_dict['momentum_strength'] = result_dict['momentum_strength'].lower()

        # Handle risk_reward_ratio - GLM might return "1:3" or "1:3.75" as string
        if 'risk_reward_ratio' in result_dict:
            ratio = result_dict['risk_reward_ratio']
            if isinstance(ratio, str):
                # Parse "1:3.75" format -> extract the number after colon
                if ':' in ratio:
                    try:
                        parts = ratio.split(':')
                        if len(parts) == 2:
                            result_dict['risk_reward_ratio'] = float(parts[1])
                        else:
                            result_dict['risk_reward_ratio'] = 1.0
                    except (ValueError, IndexError):
                        result_dict['risk_reward_ratio'] = 1.0
                else:
                    try:
                        result_dict['risk_reward_ratio'] = float(ratio)
                    except ValueError:
                        result_dict['risk_reward_ratio'] = 1.0

        # Ensure numeric fields are correct type
        if 'confidence' in result_dict and not isinstance(result_dict['confidence'], (int, float)):
            result_dict['confidence'] = 0.0
        if 'opportunity_score' in result_dict and not isinstance(result_dict['opportunity_score'], (int, float)):
            result_dict['opportunity_score'] = 0.0
        if 'risk_reward_ratio' in result_dict and not isinstance(result_dict['risk_reward_ratio'], (int, float)):
            result_dict['risk_reward_ratio'] = 1.0

        # Instantiate and Validate with Pydantic
        return TraderOpinion(**result_dict)

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'TraderAgentMVP',
            'role': self.role,
            'weight': self.weight,
            'focus': '공격적 트레이딩 기회 포착',
            'absorbed_agents': ['Trader Agent', 'ChipWar Agent (opportunity)'],
            'responsibilities': [
                '단기 트레이딩 기회 식별',
                '기술적 진입/청산 시그널',
                '칩워 관련 기회 평가',
                '모멘텀 및 트렌드 분석'
            ]
        }


# Example usage
if __name__ == "__main__":
    agent = TraderAgentMVP()

    # Test data
    price_data = {
        'current_price': 150.25,
        'open': 148.50,
        'high': 151.00,
        'low': 147.80,
        'volume': 45000000
    }

    technical_data = {
        'rsi': 62.5,
        'macd': {'value': 1.2, 'signal': 0.8},
        'moving_averages': {'ma50': 145.00, 'ma200': 140.00}
    }

    result = agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        technical_data=technical_data
    )

    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Opportunity Score: {result['opportunity_score']:.1f}")
