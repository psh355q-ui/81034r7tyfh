"""
Trader Agent MVP (Two-Stage Architecture - Gemini Edition)

Phase: MVP Consolidation - Gemini Integration
Date: 2026-01-17

Purpose:
    Two-Stage 트레이딩 에이전트 구현 (Gemini 버전)
    - Stage 1: GeminiReasoningAgent → 자연어 추론
    - Stage 2: GeminiStructuringAgent → JSON 변환

Two-Stage Architecture:
    1. GeminiReasoningAgent: Gemini로 자연어 분석 생성
    2. GeminiStructuringAgent: 추론 텍스트를 TraderOpinion 스키마로 변환

Benefits:
    - 높은 Concurrency 제한 (60+ vs GLM 3)
    - 빠른 응답 속도
    - 비용 절감
    - JSON 안정성 확보 (Stage 2에서 담당)
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.ai.mvp.gemini_reasoning_agent_base import GeminiReasoningAgentBase
from backend.ai.mvp.gemini_structuring_agent import GeminiStructuringAgent
from backend.ai.schemas.war_room_schemas import TraderOpinion

logger = logging.getLogger(__name__)


class TraderReasoningAgent(GeminiReasoningAgentBase):
    """
    Stage 1: Trader Reasoning Agent (Gemini 버전)

    Uses Gemini 2.0 Flash for natural language reasoning only.
    No JSON output required.

    Benefits:
    - Higher concurrency limit (60+ vs GLM 3)
    - Faster response time
    - Cost-effective
    """

    def __init__(self):
        super().__init__(
            agent_name='trader',
            role='공격적 트레이더'
        )
        self.weight = 0.35  # 35% voting weight

    def _build_reasoning_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[list] = None,
        market_context: Optional[Dict[str, Any]] = None,
        multi_timeframe_data: Optional[Dict[str, Any]] = None,
        option_data: Optional[Dict[str, Any]] = None,
        action_context: str = "new_position"
    ) -> str:
        """Build reasoning prompt for trader analysis"""
        prompt_parts = [
            f"종목: {symbol}",
            f"분석 관점: {'신규 진입 (New Entry)' if action_context == 'new_position' else '보유 중 (Existing Position)'}",
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

        # Multi-Timeframe Analysis
        if multi_timeframe_data:
            prompt_parts.append("\n멀티 타임프레임 분석:")
            for tf, data in multi_timeframe_data.items():
                if data:
                    prompt_parts.append(f"- [{tf}] Price: {data.get('current_price')}, RSI: {data.get('rsi')}, Trend: {data.get('trend')}")

        # Option Data
        if option_data:
            prompt_parts.append("\n옵션 데이터 분석:")
            prompt_parts.append(f"- P/C Ratio: {option_data.get('put_call_ratio', 'N/A')}")
            prompt_parts.append(f"- Max Pain: {option_data.get('max_pain', 'N/A')}")
            prompt_parts.append(f"- Volume: Call {option_data.get('total_call_volume', 0)} vs Put {option_data.get('total_put_volume', 0)}")

        # Context-Specific Instructions
        if action_context == "existing_position":
            prompt_parts.append("\n[보유자 관점 분석 지침]")
            prompt_parts.append("1. 현재 추세가 꺾일 징후가 있는지 확인하세요. (Exit Signal)")
            prompt_parts.append("2. 지지선이 견고하여 홀딩이 가능한지 판단하세요. (Hold Validity)")
            prompt_parts.append("3. 추가 매수(불타기)가 유효한 강력한 상승장인지 확인하세요. (Add-on Opportunity)")
        else:
            prompt_parts.append("\n[신규 진입 관점 분석 지침]")
            prompt_parts.append("1. 진입 타이밍이 적절한지 확인하세요. (Entry Timing)")
            prompt_parts.append("2. 손익비(Risk/Reward)가 유리한 구간인지 확인하세요.")
            prompt_parts.append("3. 돌파 또는 지지 반등 시그널이 명확한지 확인하세요.")

        return "\n".join(prompt_parts)


class TraderAgentMVP:
    """
    Two-Stage Trader Agent (Gemini Edition)

    Orchestrates:
    1. Reasoning (Gemini 2.0 Flash) → Natural language analysis
    2. Structuring (Gemini JSON mode) → JSON conversion

    This is the main entry point for trading analysis.

    Benefits:
    - Higher concurrency limit (60+ vs GLM 3)
    - Faster response time
    - Cost-effective
    """

    def __init__(self):
        """Initialize Two-Stage Trader Agent with Gemini"""
        self.reasoning_agent = TraderReasoningAgent()
        self.structuring_agent = GeminiStructuringAgent()
        self.weight = 0.35  # 35% voting weight

        # TraderOpinion schema definition for structuring
        self.schema_definition = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["buy", "sell", "hold", "pass"]},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reasoning": {"type": "string"},
                "opportunity_score": {"type": "number", "minimum": 0.0, "maximum": 100.0},
                "momentum_strength": {"type": "string", "enum": ["weak", "moderate", "strong", "very_strong"]},
                "risk_reward_ratio": {"type": "number"},
                "entry_price": {"type": "number"},
                "stop_loss": {"type": "number"},
                "take_profit": {"type": "number"}
            },
            "required": ["action", "confidence", "reasoning"]
        }

    async def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[list] = None,
        market_context: Optional[Dict[str, Any]] = None,
        multi_timeframe_data: Optional[Dict[str, Any]] = None,
        option_data: Optional[Dict[str, Any]] = None,
        action_context: str = "new_position"
    ) -> Dict[str, Any]:
        """
        Two-stage analysis:
        1. Generate reasoning with GLM-4.7
        2. Structure reasoning into JSON

        Args:
            symbol: Stock symbol
            price_data: Current price data
            technical_data: Technical indicators
            chipwar_events: ChipWar related events
            market_context: Market context data
            multi_timeframe_data: Multi-timeframe analysis data
            option_data: Options data

        Returns:
            Dict matching TraderOpinion schema
        """
        import time
        start_time = time.time()

        try:
            # Stage 1: Generate reasoning (can be parallelized in future)
            reasoning_result = await self.reasoning_agent.reason(
                symbol=symbol,
                price_data=price_data,
                technical_data=technical_data,
                chipwar_events=chipwar_events,
                market_context=market_context,
                multi_timeframe_data=multi_timeframe_data,
                option_data=option_data,
                action_context=action_context
            )

            if 'error' in reasoning_result:
                # Reasoning failed, return safe default
                return {
                    'agent': 'trader_mvp',
                    'action': 'pass',
                    'confidence': 0.0,
                    'reasoning': f'추론 실패: {reasoning_result.get("error", "Unknown error")}',
                    'opportunity_score': 0.0,
                    'momentum_strength': 'weak',
                    'weight': self.weight,
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'stage': 'failed',
                    'error': reasoning_result.get('error')
                }

            reasoning_text = reasoning_result['reasoning']

            # Stage 2: Structure reasoning into JSON
            structured_result = await self.structuring_agent.structure(
                reasoning_text=reasoning_text,
                schema_definition=self.schema_definition,
                agent_type='trader',
                symbol=symbol
            )

            # Add weight and timing metadata
            structured_result['weight'] = self.weight
            structured_result['latency_seconds'] = round(time.time() - start_time, 2)
            structured_result['reasoning_text'] = reasoning_text  # Include original reasoning for debugging

            return structured_result

        except Exception as e:
            logger.error(f"Two-stage analysis failed: {e}")
            return {
                'agent': 'trader_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}',
                'opportunity_score': 0.0,
                'momentum_strength': 'weak',
                'weight': self.weight,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'failed',
                'error': str(e),
                'latency_seconds': round(time.time() - start_time, 2)
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'TraderAgentMVP (Two-Stage Gemini)',
            'role': '공격적 트레이더',
            'weight': self.weight,
            'architecture': 'two-stage',
            'llm_provider': 'gemini',
            'focus': '공격적 트레이딩 기회 포착',
            'stages': {
                'reasoning': 'Gemini 2.0 Flash → 자연어 추론',
                'structuring': 'Gemini JSON mode → JSON 변환'
            },
            'benefits': [
                '높은 Concurrency 제한 (60+ vs GLM 3)',
                '빠른 응답 속도',
                '비용 효율성'
            ],
            'responsibilities': [
                '단기 트레이딩 기회 식별',
                '기술적 진입/청산 시그널',
                '칩워 관련 기회 평가',
                '모멘텀 및 트렌드 분석'
            ]
        }

    async def close(self):
        """Close all GLM client sessions."""
        await self.reasoning_agent.close()
        await self.structuring_agent.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Example usage
if __name__ == "__main__":
    async def test():
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

        result = await agent.analyze(
            symbol='AAPL',
            price_data=price_data,
            technical_data=technical_data
        )

        print(f"Action: {result['action']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        print(f"Opportunity Score: {result.get('opportunity_score', 0):.1f}")
        print(f"Latency: {result.get('latency_seconds', 'N/A')}s")

    asyncio.run(test())
