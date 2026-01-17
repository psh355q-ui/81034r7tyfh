"""
Analyst Agent MVP (Two-Stage Architecture - Gemini Edition)

Phase: MVP Consolidation - Gemini Integration
Date: 2026-01-17

Purpose:
    Two-Stage 정보 분석 에이전트 구현 (Gemini 버전)
    - Stage 1: GeminiReasoningAgent → 자연어 추론
    - Stage 2: GeminiStructuringAgent → JSON 변환

Two-Stage Architecture:
    1. GeminiReasoningAgent: Gemini로 자연어 정보 분석 생성
    2. GeminiStructuringAgent: 추론 텍스트를 AnalystOpinion 스키마로 변환

Benefits:
    - 높은 Concurrency 제한 (60+ vs GLM 3)
    - 빠른 응답 속도
    - 비용 절감
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.ai.mvp.gemini_reasoning_agent_base import GeminiReasoningAgentBase
from backend.ai.mvp.gemini_structuring_agent import GeminiStructuringAgent
from backend.ai.schemas.war_room_schemas import AnalystOpinion

logger = logging.getLogger(__name__)


class AnalystReasoningAgent(GeminiReasoningAgentBase):
    """
    Stage 1: Analyst Reasoning Agent (Gemini 버전)

    Uses Gemini 2.0 Flash for natural language reasoning only.
    No JSON output required.

    Benefits:
    - Higher concurrency limit (60+ vs GLM 3)
    - Faster response time
    - Cost-effective
    """

    def __init__(self):
        super().__init__(
            agent_name='analyst',
            role='수석 정보 분석가'
        )
        self.weight = 0.35  # 35% voting weight

    def _build_reasoning_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Build reasoning prompt for analyst analysis"""
        prompt_parts = [
            f"종목: {symbol}",
            f"현재가: ${price_data.get('current_price', 'N/A')}",
        ]

        # News data
        news_data = kwargs.get('news_data')
        if news_data:
            prompt_parts.append("\n최근 뉴스:")
            for article in news_data[:5]:  # Top 5
                prompt_parts.append(f"- {article.get('title', 'N/A')}")
                if 'sentiment' in article:
                    prompt_parts.append(f"  심리: {article['sentiment']}")
                if 'impact_score' in article:
                    prompt_parts.append(f"  영향: {article['impact_score']}")

        # Macro data
        macro_data = kwargs.get('macro_data')
        if macro_data:
            prompt_parts.append("\n거시경제 상황:")
            if 'interest_rate' in macro_data:
                prompt_parts.append(f"- 금리: {macro_data['interest_rate']}%")
            if 'gdp_growth' in macro_data:
                prompt_parts.append(f"- GDP 성장: {macro_data['gdp_growth']}%")
            if 'trend' in macro_data:
                prompt_parts.append(f"- 경기 트렌드: {macro_data['trend']}")

        # Institutional flow
        institutional_flow = kwargs.get('institutional_flow')
        if institutional_flow:
            prompt_parts.append("\n기관 동향:")
            if 'net_flow' in institutional_flow:
                flow = institutional_flow['net_flow']
                if flow > 0:
                    prompt_parts.append(f"- 기관 순매수: +{flow:.2f}%")
                else:
                    prompt_parts.append(f"- 기관 순매도: {flow:.2f}%")
            if 'top_buyers' in institutional_flow:
                prompt_parts.append(f"- 주요 매수자: {', '.join(institutional_flow['top_buyers'][:3])}")

        # Geopolitical risks
        geopolitical_risks = kwargs.get('geopolitical_risks')
        if geopolitical_risks:
            prompt_parts.append("\n지정학적 리스크:")
            for risk in geopolitical_risks[:3]:
                prompt_parts.append(f"- {risk.get('event', 'N/A')}: {risk.get('impact', 'N/A')}")

        # Sector context
        sector_context = kwargs.get('sector_context')
        if sector_context:
            prompt_parts.append("\n섹터 맥락:")
            if 'sector_name' in sector_context:
                prompt_parts.append(f"- 섹터: {sector_context['sector_name']}")
            if 'sector_performance' in sector_context:
                prompt_parts.append(f"- 섹터 성과: {sector_context['sector_performance']:+.2f}%")
            if 'relative_strength' in sector_context:
                prompt_parts.append(f"- 상대적 강도: {sector_context['relative_strength']}")

        return "\n".join(prompt_parts)


class AnalystAgentMVP:
    """
    Two-Stage Analyst Agent (Gemini Edition)

    Orchestrates:
    1. Reasoning (Gemini 2.0 Flash) → Natural language information analysis
    2. Structuring (Gemini JSON mode) → JSON conversion

    This is the main entry point for analyst analysis.

    Benefits:
    - Higher concurrency limit (60+ vs GLM 3)
    - Faster response time
    - Cost-effective
    """

    def __init__(self):
        """Initialize Two-Stage Analyst Agent with Gemini"""
        self.reasoning_agent = AnalystReasoningAgent()
        self.structuring_agent = GeminiStructuringAgent()
        self.weight = 0.35  # 35% voting weight

        # AnalystOpinion schema definition for structuring
        self.schema_definition = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["buy", "sell", "hold", "pass"]},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "reasoning": {"type": "string"},
                "news_headline": {"type": "string"},
                "news_sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "news_impact_score": {"type": "number", "minimum": -5.0, "maximum": 5.0},
                "macro_trend": {"type": "string", "enum": ["expansion", "contraction", "stable"]},
                "macro_score": {"type": "number", "minimum": -10.0, "maximum": 10.0},
                "overall_information_score": {"type": "number", "minimum": -10.0, "maximum": 10.0},
                "key_catalyst": {"type": "string"},
                "red_flag": {"type": "string"},
                "time_horizon": {"type": "string", "enum": ["short", "medium", "long"]}
            },
            "required": ["action", "confidence", "reasoning"]
        }

    async def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        news_data: Optional[List[Dict]] = None,
        macro_data: Optional[Dict[str, Any]] = None,
        institutional_flow: Optional[Dict[str, Any]] = None,
        geopolitical_risks: Optional[List[Dict]] = None,
        sector_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Two-stage analyst analysis:
        1. Generate reasoning with GLM-4.7
        2. Structure reasoning into JSON

        Args:
            symbol: Stock symbol
            price_data: Current price data
            technical_data: Technical indicators
            news_data: Recent news articles
            macro_data: Macro economic data
            institutional_flow: Institutional trading flow
            geopolitical_risks: Geopolitical risk events
            sector_context: Sector performance context

        Returns:
            Dict matching AnalystOpinion schema
        """
        import time
        start_time = time.time()

        try:
            # Stage 1: Generate reasoning
            reasoning_result = await self.reasoning_agent.reason(
                symbol=symbol,
                price_data=price_data,
                technical_data=technical_data,
                news_data=news_data,
                macro_data=macro_data,
                institutional_flow=institutional_flow,
                geopolitical_risks=geopolitical_risks,
                sector_context=sector_context
            )

            if 'error' in reasoning_result:
                return {
                    'agent': 'analyst_mvp',
                    'action': 'pass',
                    'confidence': 0.0,
                    'reasoning': f'추론 실패: {reasoning_result.get("error", "Unknown error")}',
                    'news_headline': '분석 실패',
                    'news_sentiment': 'neutral',
                    'overall_information_score': 0.0,
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
                agent_type='analyst',
                symbol=symbol
            )

            # Add weight and timing metadata
            structured_result['weight'] = self.weight
            structured_result['latency_seconds'] = round(time.time() - start_time, 2)
            structured_result['reasoning_text'] = reasoning_text

            return structured_result

        except Exception as e:
            logger.error(f"Two-stage analyst analysis failed: {e}")
            return {
                'agent': 'analyst_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}',
                'news_headline': '분석 실패',
                'news_sentiment': 'neutral',
                'overall_information_score': 0.0,
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
            'name': 'AnalystAgentMVP (Two-Stage Gemini)',
            'role': '수석 정보 분석가',
            'weight': self.weight,
            'architecture': 'two-stage',
            'llm_provider': 'gemini',
            'focus': '정보 통합 및 종합 분석',
            'stages': {
                'reasoning': 'Gemini 2.0 Flash → 자연어 정보 분석',
                'structuring': 'Gemini JSON mode → JSON 변환'
            },
            'benefits': [
                '높은 Concurrency 제한 (60+ vs GLM 3)',
                '빠른 응답 속도',
                '비용 효율성'
            ],
            'responsibilities': [
                '뉴스 감성 분석',
                '거시경제 통합',
                '기관 동향 파악',
                '지정학적 리스크 평가'
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
        agent = AnalystAgentMVP()

        price_data = {'current_price': 150.25}

        news_data = [
            {'title': 'AAPL, AI 기능 탑재로 2026년 성장 전망', 'sentiment': 'positive', 'impact_score': 3.5},
            {'title': '연준, 금리 인상 속도 완화 시사', 'sentiment': 'positive', 'impact_score': 2.0}
        ]

        macro_data = {'interest_rate': 5.25, 'gdp_growth': 2.1, 'trend': 'stable'}

        result = await agent.analyze(
            symbol='AAPL',
            price_data=price_data,
            news_data=news_data,
            macro_data=macro_data
        )

        print(f"Action: {result['action']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"News Headline: {result.get('news_headline', 'N/A')}")
        print(f"Overall Score: {result.get('overall_information_score', 0):.1f}")
        print(f"Time Horizon: {result.get('time_horizon', 'N/A')}")

    asyncio.run(test())
