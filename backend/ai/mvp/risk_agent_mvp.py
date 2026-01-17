"""
Risk Agent MVP (Two-Stage Architecture)

Phase: MVP Consolidation
Date: 2026-01-17

Purpose:
    Two-Stage 리스크 관리 에이전트 구현
    - Stage 1: Reasoning Agent (GLM-4.7) → 자연어 추론
    - Stage 2: Structuring Agent → JSON 변환

Two-Stage Architecture:
    1. ReasoningAgent: GLM-4.7으로 자연어 리스크 분석 생성
    2. StructuringAgent: 추론 텍스트를 RiskOpinion 스키마로 변환
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.ai.mvp.reasoning_agent_base import ReasoningAgentBase
from backend.ai.mvp.structuring_agent import StructuringAgent
from backend.ai.schemas.war_room_schemas import RiskOpinion

logger = logging.getLogger(__name__)


class RiskReasoningAgent(ReasoningAgentBase):
    """
    Stage 1: Risk Reasoning Agent

    Uses GLM-4.7 for natural language reasoning only.
    No JSON output required.
    """

    def __init__(self):
        super().__init__(
            agent_name='risk',
            role='방어적 리스크 관리자'
        )
        self.weight = 0.30  # 30% voting weight

    def _build_reasoning_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Build reasoning prompt for risk analysis"""
        prompt_parts = [
            f"종목: {symbol}",
            f"현재가: ${price_data.get('current_price', 'N/A')}",
            f"변동률: {price_data.get('change_pct', 0):+.2f}%" if 'change_pct' in price_data else "",
        ]

        # Technical indicators for risk assessment
        if technical_data:
            prompt_parts.append("\n기술적 지표:")
            if 'rsi' in technical_data:
                rsi = technical_data['rsi']
                if rsi > 70:
                    prompt_parts.append(f"- RSI {rsi:.1f}: 과매수 구간 (급락 리스크)")
                elif rsi < 30:
                    prompt_parts.append(f"- RSI {rsi:.1f}: 과매도 구간 (반등 가능성)")
                else:
                    prompt_parts.append(f"- RSI {rsi:.1f}: 중립")
            if 'volatility' in technical_data:
                prompt_parts.append(f"- 변동성: {technical_data['volatility']:.2f} (1-10 척도)")
            if 'bollinger_bands' in technical_data:
                bb = technical_data['bollinger_bands']
                price = price_data.get('current_price', 0)
                if price > bb.get('upper', 0):
                    prompt_parts.append(f"- 볼린저 상단 돌파: 급락 리스크 높음")
                elif price < bb.get('lower', 0):
                    prompt_parts.append(f"- 볼린저 하단 이탈: 추가 하락 가능성")

        # Position size info
        position_size = kwargs.get('position_size_pct')
        if position_size:
            prompt_parts.append(f"\n현재 포지션: {position_size}%")

        # Market context
        market_context = kwargs.get('market_context')
        if market_context:
            prompt_parts.append("\n시장 맥락:")
            if 'market_trend' in market_context:
                prompt_parts.append(f"- 시장 트렌드: {market_context['market_trend']}")
            if 'volatility_index' in market_context:
                prompt_parts.append(f"- VIX: {market_context['volatility_index']}")

        return "\n".join(prompt_parts)


class RiskAgentMVP:
    """
    Two-Stage Risk Agent

    Orchestrates:
    1. Reasoning (GLM-4.7) → Natural language risk analysis
    2. Structuring → JSON conversion

    This is the main entry point for risk analysis.
    """

    def __init__(self):
        """Initialize Two-Stage Risk Agent"""
        self.reasoning_agent = RiskReasoningAgent()
        self.structuring_agent = StructuringAgent()
        self.weight = 0.30  # 30% voting weight

        # RiskOpinion schema definition for structuring
        self.schema_definition = {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high", "extreme"]},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reasoning": {"type": "string"},
                "stop_loss_pct": {"type": "number"},
                "take_profit_pct": {"type": "number"},
                "max_position_pct": {"type": "number"},
                "sentiment_score": {"type": "number", "minimum": -5.0, "maximum": 5.0},
                "volatility_risk": {"type": "number", "minimum": 1.0, "maximum": 10.0},
                "dividend_risk": {"type": "string", "enum": ["none", "low", "medium", "high"]},
                "recommendation": {"type": "string", "enum": ["approve", "reduce_size", "reject"]}
            },
            "required": ["risk_level", "confidence", "reasoning", "recommendation"]
        }

    async def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        position_size_pct: Optional[float] = None,
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Two-stage risk analysis:
        1. Generate reasoning with GLM-4.7
        2. Structure reasoning into JSON

        Args:
            symbol: Stock symbol
            price_data: Current price data
            technical_data: Technical indicators
            position_size_pct: Current position size percentage
            market_context: Market context data

        Returns:
            Dict matching RiskOpinion schema
        """
        import time
        start_time = time.time()

        try:
            # Stage 1: Generate reasoning
            reasoning_result = await self.reasoning_agent.reason(
                symbol=symbol,
                price_data=price_data,
                technical_data=technical_data,
                position_size_pct=position_size_pct,
                market_context=market_context
            )

            if 'error' in reasoning_result:
                return {
                    'agent': 'risk_mvp',
                    'risk_level': 'high',
                    'confidence': 0.0,
                    'reasoning': f'추론 실패: {reasoning_result.get("error", "Unknown error")}',
                    'stop_loss_pct': 0.05,
                    'take_profit_pct': 0.10,
                    'max_position_pct': 0.05,
                    'recommendation': 'reject',
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
                agent_type='risk',
                symbol=symbol
            )

            # Add weight and timing metadata
            structured_result['weight'] = self.weight
            structured_result['latency_seconds'] = round(time.time() - start_time, 2)
            structured_result['reasoning_text'] = reasoning_text

            return structured_result

        except Exception as e:
            logger.error(f"Two-stage risk analysis failed: {e}")
            return {
                'agent': 'risk_mvp',
                'risk_level': 'high',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}',
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'max_position_pct': 0.05,
                'recommendation': 'reject',
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
            'name': 'RiskAgentMVP (Two-Stage)',
            'role': '방어적 리스크 관리자',
            'weight': self.weight,
            'architecture': 'two-stage',
            'focus': '리스크 평가 및 포지션 사이징',
            'stages': {
                'reasoning': 'GLM-4.7 → 자연어 리스크 분석',
                'structuring': 'Lightweight → JSON 변환'
            },
            'responsibilities': [
                '최악의 시나리오 분석',
                '손절가/목표가 계산',
                '포지션 사이징 제안',
                '변동성 리스크 평가'
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
        agent = RiskAgentMVP()

        price_data = {
            'current_price': 150.25,
            'change_pct': 2.5
        }

        technical_data = {
            'rsi': 65.0,
            'volatility': 6.5,
            'bollinger_bands': {'upper': 152, 'lower': 148}
        }

        result = await agent.analyze(
            symbol='AAPL',
            price_data=price_data,
            technical_data=technical_data,
            position_size_pct=10.0
        )

        print(f"Risk Level: {result['risk_level']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Stop Loss: {result.get('stop_loss_pct', 0)*100}%")
        print(f"Max Position: {result.get('max_position_pct', 0)*100}%")

    asyncio.run(test())
