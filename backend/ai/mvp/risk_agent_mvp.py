"""
Risk Agent MVP - Defense (35% weight)

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    전문 리스크 관리자의 방어적 관점
    - 포지션 사이즈 결정 (NEW - ChatGPT 제안)
    - 리스크 평가 및 Stop Loss 설정
    - 감정/심리 분석 통합
    - 배당 리스크 평가

Key Responsibilities:
    1. 포지션 사이즈 계산 (Kelly Criterion + Risk-based)
    2. Stop Loss / Take Profit 설정
    3. 시장 감정 및 심리 분석
    4. 배당 일정 리스크 체크
    5. 최대 포지션 한도 검증

Absorbed Legacy Agents:
    - Risk Agent (100%)
    - Sentiment Agent (100%)
    - DividendRisk Agent (100%)
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai


class RiskAgentMVP:
    """MVP Risk Agent - 방어적 리스크 관리 + Position Sizing"""

    def __init__(self):
        """Initialize Risk Agent MVP"""
        # Gemini API 설정
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Agent configuration
        self.weight = 0.35  # 35% voting weight
        self.role = "방어적 리스크 관리자"

        # Risk parameters (Hard Rules)
        self.ACCOUNT_RISK_PER_TRADE = 0.01  # 1% of account per trade
        self.MAX_POSITION_SIZE = 0.20  # 20% of portfolio max
        self.ABSOLUTE_MAX_POSITION = 0.30  # 30% hard cap (Hard Rule)
        self.MIN_CONFIDENCE_FOR_FULL_SIZE = 0.80  # 80% confidence required

        # System prompt
        self.system_prompt = """당신은 전문 리스크 관리자입니다.

역할:
1. 리스크 평가 및 Stop Loss/Take Profit 설정
2. 시장 감정 및 심리 분석
3. 배당 일정 리스크 체크
4. 포지션 사이즈 추천 (최종 계산은 코드가 수행)

분석 원칙:
- 손실 방지 최우선
- 감정/심리적 요소 고려 (공포/탐욕 지수, 변동성)
- 배당락일 전후 리스크 평가
- Stop Loss는 기술적 지지선 기반

출력 형식:
{
    "risk_level": "low" | "medium" | "high" | "extreme",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "구체적 리스크 근거",
    "stop_loss_pct": 손실 한도 (예: 0.02 = 2%),
    "take_profit_pct": 목표 수익 (예: 0.10 = 10%),
    "max_position_pct": 최대 포지션 비율 추천 (예: 0.15 = 15%),
    "sentiment_score": -1.0 ~ 1.0 (부정 ~ 긍정),
    "volatility_risk": 0.0 ~ 10.0,
    "dividend_risk": "none" | "ex-dividend-near" | "cut-risk",
    "fear_greed_index": 0 ~ 100 (공포 ~ 탐욕),
    "recommendation": "approve" | "reduce_size" | "reject"
}

중요:
- **반드시 한글로 응답할 것** (reasoning 필드는 한국어로 작성)
- risk_level이 "extreme"이면 recommendation은 "reject"
- Stop Loss는 반드시 설정 (최소 1%, 최대 10%)
- 감정 지표가 극단적이면 경고
"""

    def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        trader_opinion: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        dividend_info: Optional[Dict[str, Any]] = None,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        리스크 분석 및 포지션 사이즈 계산

        Args:
            symbol: 종목 심볼
            price_data: 가격 데이터
                {
                    'current_price': float,
                    'high_52w': float,
                    'low_52w': float,
                    'volatility': float (annualized)
                }
            trader_opinion: Trader Agent의 의견 (optional)
                {
                    'action': str,
                    'confidence': float,
                    'opportunity_score': float
                }
            market_data: 시장 데이터 (optional)
                {
                    'vix': float,
                    'market_sentiment': float,
                    'sector_volatility': float
                }
            dividend_info: 배당 정보 (optional)
                {
                    'ex_dividend_date': str,
                    'days_until_ex_div': int,
                    'dividend_yield': float
                }
            portfolio_context: 포트폴리오 맥락 (optional)
                {
                    'current_cash': float,
                    'total_value': float,
                    'current_positions': int,
                    'existing_position_size': float (if exists)
                }

        Returns:
            Dict containing:
                - risk_level: low/medium/high/extreme
                - confidence: 0.0 ~ 1.0
                - reasoning: 리스크 근거
                - stop_loss_pct: Stop Loss %
                - take_profit_pct: Take Profit %
                - max_position_pct: 최대 포지션 비율
                - position_size_usd: 계산된 포지션 크기 (USD)
                - position_size_shares: 계산된 주식 수
                - sentiment_score: 감정 점수
                - volatility_risk: 변동성 리스크
                - dividend_risk: 배당 리스크
                - recommendation: approve/reduce_size/reject
        """
        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            price_data=price_data,
            trader_opinion=trader_opinion,
            market_data=market_data,
            dividend_info=dividend_info
        )

        # Call Gemini API
        try:
            response = self.model.generate_content([
                self.system_prompt,
                prompt
            ])

            # Parse response
            result = self._parse_response(response.text)

            # Calculate position size (code-based, not AI)
            if portfolio_context and trader_opinion:
                position_sizing = self._calculate_position_size(
                    stop_loss_pct=result['stop_loss_pct'],
                    confidence=trader_opinion.get('confidence', 0.5),
                    portfolio_context=portfolio_context,
                    current_price=price_data['current_price'],
                    risk_level=result['risk_level']
                )
                result.update(position_sizing)

            # Add metadata
            result['agent'] = 'risk_mvp'
            result['weight'] = self.weight
            result['timestamp'] = datetime.utcnow().isoformat()
            result['symbol'] = symbol

            return result

        except Exception as e:
            # Error handling - return safe default (reject)
            return {
                'agent': 'risk_mvp',
                'risk_level': 'extreme',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}',
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.10,
                'max_position_pct': 0.0,
                'position_size_usd': 0.0,
                'position_size_shares': 0,
                'sentiment_score': 0.0,
                'volatility_risk': 10.0,
                'dividend_risk': 'none',
                'recommendation': 'reject',
                'weight': self.weight,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': str(e)
            }

    def _build_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        trader_opinion: Optional[Dict[str, Any]],
        market_data: Optional[Dict[str, Any]],
        dividend_info: Optional[Dict[str, Any]]
    ) -> str:
        """Build analysis prompt"""
        prompt_parts = [
            f"종목: {symbol}",
            f"현재가: ${price_data.get('current_price', 'N/A')}",
            f"52주 고가: ${price_data.get('high_52w', 'N/A')}",
            f"52주 저가: ${price_data.get('low_52w', 'N/A')}",
            f"변동성 (연): {(price_data.get('volatility', 0) * 100):.1f}%",
        ]

        # Trader opinion
        if trader_opinion:
            prompt_parts.append("\nTrader Agent 의견:")
            prompt_parts.append(f"- 액션: {trader_opinion.get('action', 'N/A')}")
            prompt_parts.append(f"- 신뢰도: {trader_opinion.get('confidence', 0):.2f}")
            prompt_parts.append(f"- 기회 점수: {trader_opinion.get('opportunity_score', 0):.1f}")

        # Market data
        if market_data:
            prompt_parts.append("\n시장 데이터:")
            if 'vix' in market_data:
                prompt_parts.append(f"- VIX: {market_data['vix']:.2f}")
            if 'market_sentiment' in market_data:
                prompt_parts.append(f"- 시장 심리: {market_data['market_sentiment']:.2f}")
            if 'sector_volatility' in market_data:
                prompt_parts.append(f"- 섹터 변동성: {market_data['sector_volatility']:.2f}%")

        # Dividend info
        if dividend_info:
            prompt_parts.append("\n배당 정보:")
            if 'ex_dividend_date' in dividend_info:
                prompt_parts.append(f"- 배당락일: {dividend_info['ex_dividend_date']}")
            if 'days_until_ex_div' in dividend_info:
                days = dividend_info['days_until_ex_div']
                prompt_parts.append(f"- 배당락일까지: {days}일")
                if 0 <= days <= 5:
                    prompt_parts.append("  ⚠️ 배당락일 임박!")
            if 'dividend_yield' in dividend_info:
                prompt_parts.append(f"- 배당 수익률: {dividend_info['dividend_yield']:.2f}%")

        prompt_parts.append("\n위 정보를 바탕으로 리스크를 분석하고 JSON 형식으로 답변하세요.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response"""
        import json
        import re

        # Extract JSON from response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

        # Validate required fields
        required_fields = ['risk_level', 'confidence', 'reasoning', 'stop_loss_pct',
                          'take_profit_pct', 'max_position_pct', 'sentiment_score',
                          'volatility_risk', 'dividend_risk', 'recommendation']
        for field in required_fields:
            if field not in result:
                # Provide defaults
                if field == 'risk_level':
                    result[field] = 'medium'
                elif field in ['confidence', 'sentiment_score']:
                    result[field] = 0.5
                elif field in ['stop_loss_pct', 'take_profit_pct', 'max_position_pct']:
                    result[field] = 0.02
                elif field == 'volatility_risk':
                    result[field] = 5.0
                elif field == 'dividend_risk':
                    result[field] = 'none'
                elif field == 'recommendation':
                    result[field] = 'reduce_size'
                elif field == 'reasoning':
                    result[field] = 'Default reasoning'

        # Validate values
        valid_risk_levels = ['low', 'medium', 'high', 'extreme']
        if result['risk_level'] not in valid_risk_levels:
            result['risk_level'] = 'medium'

        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
        result['stop_loss_pct'] = max(0.01, min(0.10, float(result['stop_loss_pct'])))
        result['take_profit_pct'] = max(0.02, min(1.0, float(result['take_profit_pct'])))
        result['max_position_pct'] = max(0.0, min(0.30, float(result['max_position_pct'])))
        result['sentiment_score'] = max(-1.0, min(1.0, float(result['sentiment_score'])))
        result['volatility_risk'] = max(0.0, min(10.0, float(result['volatility_risk'])))

        valid_div_risk = ['none', 'ex-dividend-near', 'cut-risk']
        if result['dividend_risk'] not in valid_div_risk:
            result['dividend_risk'] = 'none'

        valid_rec = ['approve', 'reduce_size', 'reject']
        if result['recommendation'] not in valid_rec:
            result['recommendation'] = 'reduce_size'

        return result

    def _calculate_position_size(
        self,
        stop_loss_pct: float,
        confidence: float,
        portfolio_context: Dict[str, Any],
        current_price: float,
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Calculate position size using Kelly Criterion + Risk-based approach

        Formula:
        1. Base Size = (Account Risk % / Stop Loss %) * Account Value
        2. Confidence Adjustment = Base Size * Confidence
        3. Risk Level Adjustment = Adjusted Size * Risk Multiplier
        4. Hard Cap = min(Final Size, ABSOLUTE_MAX_POSITION)

        Args:
            stop_loss_pct: Stop loss percentage (e.g., 0.02 = 2%)
            confidence: Trader confidence (0.0 ~ 1.0)
            portfolio_context: Portfolio information
            current_price: Current stock price
            risk_level: low/medium/high/extreme

        Returns:
            Dict with position_size_usd, position_size_shares, position_size_pct
        """
        total_value = portfolio_context.get('total_value', 100000)  # Default $100k
        current_cash = portfolio_context.get('current_cash', total_value)

        # Step 1: Base position size (Kelly-like)
        base_size_pct = self.ACCOUNT_RISK_PER_TRADE / max(stop_loss_pct, 0.01)
        base_size_usd = total_value * base_size_pct

        # Step 2: Confidence adjustment
        confidence_adjusted_usd = base_size_usd * confidence

        # Step 3: Risk level adjustment
        risk_multipliers = {
            'low': 1.0,
            'medium': 0.7,
            'high': 0.4,
            'extreme': 0.0  # No position on extreme risk
        }
        risk_multiplier = risk_multipliers.get(risk_level, 0.5)
        risk_adjusted_usd = confidence_adjusted_usd * risk_multiplier

        # Step 4: Apply hard caps
        risk_adjusted_pct = risk_adjusted_usd / total_value
        final_pct = min(risk_adjusted_pct, self.MAX_POSITION_SIZE, self.ABSOLUTE_MAX_POSITION)
        final_usd = total_value * final_pct

        # Step 5: Check available cash
        final_usd = min(final_usd, current_cash)

        # Step 6: Calculate shares
        shares = int(final_usd / current_price) if current_price > 0 else 0
        actual_usd = shares * current_price

        return {
            'position_size_usd': round(actual_usd, 2),
            'position_size_shares': shares,
            'position_size_pct': round(actual_usd / total_value, 4),
            'position_sizing_breakdown': {
                'base_size_usd': round(base_size_usd, 2),
                'confidence_adjusted_usd': round(confidence_adjusted_usd, 2),
                'risk_adjusted_usd': round(risk_adjusted_usd, 2),
                'final_usd': round(actual_usd, 2),
                'risk_multiplier': risk_multiplier,
                'hard_cap_applied': final_pct >= self.ABSOLUTE_MAX_POSITION
            }
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'RiskAgentMVP',
            'role': self.role,
            'weight': self.weight,
            'focus': '방어적 리스크 관리 + Position Sizing',
            'absorbed_agents': ['Risk Agent', 'Sentiment Agent', 'DividendRisk Agent'],
            'responsibilities': [
                '포지션 사이즈 계산 (Kelly + Risk-based)',
                'Stop Loss / Take Profit 설정',
                '시장 감정 및 심리 분석',
                '배당 일정 리스크 체크',
                '최대 포지션 한도 검증'
            ],
            'hard_rules': {
                'account_risk_per_trade': f'{self.ACCOUNT_RISK_PER_TRADE * 100}%',
                'max_position_size': f'{self.MAX_POSITION_SIZE * 100}%',
                'absolute_max_position': f'{self.ABSOLUTE_MAX_POSITION * 100}%',
                'min_confidence_for_full_size': f'{self.MIN_CONFIDENCE_FOR_FULL_SIZE * 100}%'
            }
        }


# Example usage
if __name__ == "__main__":
    agent = RiskAgentMVP()

    # Test data
    price_data = {
        'current_price': 150.25,
        'high_52w': 180.00,
        'low_52w': 120.00,
        'volatility': 0.25
    }

    trader_opinion = {
        'action': 'buy',
        'confidence': 0.75,
        'opportunity_score': 7.5
    }

    portfolio_context = {
        'current_cash': 50000,
        'total_value': 100000,
        'current_positions': 3
    }

    result = agent.analyze(
        symbol='AAPL',
        price_data=price_data,
        trader_opinion=trader_opinion,
        portfolio_context=portfolio_context
    )

    print(f"Risk Level: {result['risk_level']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Position Size: ${result.get('position_size_usd', 0):,.2f} ({result.get('position_size_shares', 0)} shares)")
    print(f"Stop Loss: {(result['stop_loss_pct'] * 100):.1f}%")
    print(f"Reasoning: {result['reasoning']}")
