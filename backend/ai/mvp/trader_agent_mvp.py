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
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai


class TraderAgentMVP:
    """MVP Trader Agent - 공격적 트레이딩 기회 포착"""

    def __init__(self):
        """Initialize Trader Agent MVP"""
        # Gemini API 설정
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Agent configuration
        self.weight = 0.35  # 35% voting weight
        self.role = "공격적 트레이더"

        # System prompt
        self.system_prompt = """당신은 전문 공격적 트레이더입니다.

역할:
1. 단기 트레이딩 기회 포착
2. 기술적 진입/청산 타이밍 제안
3. 칩워 관련 기회 평가
4. 모멘텀 및 트렌드 분석

분석 원칙:
- 단기 수익 기회에 집중
- 기술적 패턴 및 모멘텀 중시
- 리스크는 Risk Agent가 담당 (당신은 기회만 제시)
- 칩워 이벤트의 단기 영향 평가

출력 형식:
{
    "action": "buy" | "sell" | "hold" | "pass",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "구체적 근거 (기술적/모멘텀/칩워 기회)",
    "entry_price": 목표 진입가 (action=buy일 때),
    "exit_price": 목표 청산가 (action=sell일 때),
    "timeframe": "단기 예상 보유기간 (예: 1d, 1w, 2w)",
    "opportunity_score": 0.0 ~ 10.0,
    "momentum_strength": "weak" | "moderate" | "strong"
}

중요:
- 리스크/포지션 사이즈는 제안하지 말 것 (Risk Agent 담당)
- 기회 포착에만 집중
- Confidence < 0.5이면 "pass" 권장
- **반드시 한글로 응답할 것** (reasoning 필드는 한국어로 작성)
"""

    def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[list] = None,
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        트레이딩 기회 분석

        Args:
            symbol: 종목 심볼 (예: AAPL, NVDA)
            price_data: 가격 데이터
                {
                    'current_price': float,
                    'open': float,
                    'high': float,
                    'low': float,
                    'volume': int,
                    'price_history': [list of prices]
                }
            technical_data: 기술적 지표 (optional)
                {
                    'rsi': float,
                    'macd': {'value': float, 'signal': float},
                    'moving_averages': {'ma50': float, 'ma200': float},
                    'bollinger_bands': {'upper': float, 'lower': float}
                }
            chipwar_events: 칩워 관련 이벤트 (optional)
                [
                    {'event': str, 'impact': str, 'date': str}
                ]
            market_context: 시장 맥락 (optional)
                {
                    'market_trend': str,
                    'sector_performance': float,
                    'news_sentiment': float
                }

        Returns:
            Dict containing:
                - action: buy/sell/hold/pass
                - confidence: 0.0 ~ 1.0
                - reasoning: 구체적 근거
                - entry_price/exit_price: 목표가
                - timeframe: 예상 보유기간
                - opportunity_score: 0.0 ~ 10.0
                - momentum_strength: weak/moderate/strong
        """
        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            chipwar_events=chipwar_events,
            market_context=market_context
        )

        # Call Gemini API
        try:
            response = self.model.generate_content([
                self.system_prompt,
                prompt
            ])

            # Parse response
            result = self._parse_response(response.text)

            # Add metadata
            result['agent'] = 'trader_mvp'
            result['weight'] = self.weight
            result['timestamp'] = datetime.utcnow().isoformat()
            result['symbol'] = symbol

            return result

        except Exception as e:
            # Error handling - return safe default
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
                'error': str(e)
            }

    def _build_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]],
        chipwar_events: Optional[list],
        market_context: Optional[Dict[str, Any]]
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

        prompt_parts.append("\n위 정보를 바탕으로 트레이딩 기회를 분석하고 JSON 형식으로 답변하세요.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response"""
        import json
        import re

        # Extract JSON from response
        try:
            # Try direct JSON parsing first
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Extract JSON from markdown code block
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Last resort: find JSON-like structure
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

        # Validate required fields
        required_fields = ['action', 'confidence', 'reasoning', 'opportunity_score', 'momentum_strength']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Validate action
        valid_actions = ['buy', 'sell', 'hold', 'pass']
        if result['action'] not in valid_actions:
            result['action'] = 'pass'

        # Validate confidence
        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))

        # Validate opportunity_score
        result['opportunity_score'] = max(0.0, min(10.0, float(result['opportunity_score'])))

        # Validate momentum_strength
        valid_momentum = ['weak', 'moderate', 'strong']
        if result['momentum_strength'] not in valid_momentum:
            result['momentum_strength'] = 'weak'

        return result

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
