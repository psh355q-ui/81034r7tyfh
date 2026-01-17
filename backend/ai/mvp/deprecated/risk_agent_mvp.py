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

API: Uses GLM-4.7 for cost efficiency (replaced Gemini)
"""

import os
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

from backend.ai.schemas.war_room_schemas import RiskOpinion

logger = logging.getLogger(__name__)


class RiskAgentMVP:
    """MVP Risk Agent - 방어적 리스크 관리 + Position Sizing (GLM-powered)"""

    def __init__(self):
        """Initialize Risk Agent MVP with GLM"""
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
        self.role = "방어적 리스크 관리자"

        # Risk parameters (Hard Rules)
        self.ACCOUNT_RISK_PER_TRADE = 0.01  # 1% of account per trade
        self.MAX_POSITION_SIZE = 0.20  # 20% of portfolio max
        self.ABSOLUTE_MAX_POSITION = 0.30  # 30% hard cap (Hard Rule)
        self.MIN_CONFIDENCE_FOR_FULL_SIZE = 0.80  # 80% confidence required

        # Load system prompt from file (like CLAUDE.md)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from docs/prompts/risk_agent_mvp.md"""
        try:
            # Get project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            prompt_path = os.path.join(project_root, 'docs', 'prompts', 'risk_agent_mvp.md')

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
            return """당신은 'War Room'의 방어적 리스크 관리자(Defensive Risk Manager)입니다.
분석 후 JSON으로 답변하세요."""
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return """당신은 'War Room'의 방어적 리스크 관리자(Defensive Risk Manager)입니다.
분석 후 JSON으로 답변하세요."""

    async def analyze(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        trader_opinion: Optional[Dict[str, Any]] = None,
        market_conditions: Optional[Dict[str, Any]] = None,
        dividend_info: Optional[str] = None,
        portfolio_state: Optional[Dict[str, Any]] = None,
        option_data: Optional[Dict[str, Any]] = None # [Phase 3]
    ) -> Dict[str, Any]:
        """
        리스크 분석 및 포지션 사이즈 계산
        
        Returns:
            Dict (compatible with RiskOpinion model)
        """
        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            price_data=price_data,
            trader_opinion=trader_opinion,
            market_conditions=market_conditions,
            dividend_info=dividend_info,
            portfolio_state=portfolio_state,
            option_data=option_data
        )
        try:
            # Call GLM API
            response = await self.glm_client.chat(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.3
            )

            # Parse response (Initial dict parsing)
            message = response["choices"][0]["message"]
            # GLM-4.7 uses reasoning_content for reasoning models
            response_text = (message.get("content") or message.get("reasoning_content", "")).strip()
            result_dict = self._parse_json_response(response_text)

            # Calculate position size (code-based, not AI)
            position_size_pct = 0.0
            kelly_breakdown = {}
            
            if portfolio_state and trader_opinion:
                position_sizing = self._calculate_position_size(
                    stop_loss_pct=result_dict.get('stop_loss_pct', 0.02),
                    confidence=trader_opinion.get('confidence', 0.5),
                    portfolio_context=portfolio_state,
                    current_price=price_data['current_price'],
                    risk_level=result_dict.get('risk_level', 'medium')
                )
                result_dict.update(position_sizing)
                position_size_pct = position_sizing.get('position_size_pct', 0.0)
                kelly_breakdown = position_sizing.get('position_sizing_breakdown', {})

            # Map fields for Schema
            current_price = price_data.get('current_price', 0)
            stop_loss_pct = result_dict.get('stop_loss_pct', 0.02)
            
            # Action Mapping
            recommendation = result_dict.get('recommendation', 'reduce_size')
            action_map = {
                'approve': 'approve',
                'reduce_size': 'reduce_size',
                'reject': 'reject'
            }
            action = action_map.get(recommendation, 'reduce_size')

            # Calculate Stop Loss Price if missing
            stop_loss_price = current_price * (1 - stop_loss_pct)

            # Construct RiskOpinion for validation
            risk_opinion_data = {
                'agent': 'risk_mvp',
                'action': action,
                'confidence': result_dict.get('confidence', 0.5),
                'position_size': position_size_pct * 100, # % value (0-100)
                'risk_level': result_dict.get('risk_level', 'medium'),
                'stop_loss': stop_loss_price,
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': result_dict.get('take_profit_pct'),
                'reasoning': result_dict.get('reasoning', 'No reasoning'),
                'sentiment_score': result_dict.get('sentiment_score'),
                'volatility_risk': result_dict.get('volatility_risk'),
                'dividend_risk': result_dict.get('dividend_risk'),
                'kelly_calculation': kelly_breakdown,
                'position_sizing_recommendation': result_dict.get('position_sizing'),
                'var_95': result_dict.get('var_95'),
                'beta': result_dict.get('beta'),
                'max_loss_scenario': result_dict.get('max_loss_scenario'),
                'risk_decomposition': result_dict.get('risk_decomposition'),
                'warnings': []
            }
            
            # Validate with Pydantic
            opinion = RiskOpinion(**risk_opinion_data)
            
            # Convert back to dict for compatibility
            result = opinion.model_dump()
            
            # Add extra fields expected by War Room
            result.update(result_dict) # Keep original fields like position_size_usd
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

    # ... _build_prompt kept ...

    def _build_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        trader_opinion: Optional[Dict[str, Any]] = None,
        market_conditions: Optional[Dict[str, Any]] = None,
        dividend_info: Optional[str] = None,
        portfolio_state: Optional[Dict[str, Any]] = None,
        option_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct risk analysis prompt"""
        prompt_parts = [f"Analyze risk for {symbol} based on the following data:\n"]

        # 1. Price Volatility
        prompt_parts.append("1. Price & Volatility:")
        prompt_parts.append(f"- Current Price: {price_data.get('current_price')}")
        prompt_parts.append(f"- 52W High: {price_data.get('high_52w')}")
        prompt_parts.append(f"- 52W Low: {price_data.get('low_52w')}")
        prompt_parts.append(f"- Volatility: {price_data.get('volatility', 'Unknown')}\n")

        # 2. Trader Opinion (Attack view)
        prompt_parts.append("2. Trader Opinion (Attack View):")
        if trader_opinion:
            prompt_parts.append(f"- Action: {trader_opinion.get('action')}")
            prompt_parts.append(f"- Confidence: {trader_opinion.get('confidence')}")
            prompt_parts.append(f"- Reasoning: {trader_opinion.get('reasoning')}")
        else:
            prompt_parts.append("No trader opinion available.")
        prompt_parts.append("\n")

        # 3. Market Sentiment
        prompt_parts.append("3. Market Conditions:")
        if market_conditions:
            sentiment = market_conditions.get('market_sentiment', 'Neutral')
            vix = market_conditions.get('vix', 'Unknown')
            prompt_parts.append(f"- Market Sentiment: {sentiment}")
            prompt_parts.append(f"- VIX: {vix}")
        else:
             prompt_parts.append("No market data.")
        prompt_parts.append("\n")
        
        # 4. Dividend Info
        prompt_parts.append("4. Dividend Information:")
        if dividend_info:
            prompt_parts.append(f"배당 정보: {dividend_info}")
        else:
            prompt_parts.append("No dividend info.")
        prompt_parts.append("\n")

        # [Phase 3] Option Data Volatility Check
        if option_data:
            prompt_parts.append("\n옵션 내재변동성(IV) 및 리스크:")
            prompt_parts.append(f"- Put/Call Ratio: {option_data.get('put_call_ratio', 'N/A')}")
            prompt_parts.append(f"- Max Pain Price: ${option_data.get('max_pain', 'N/A')}")
            current_price = price_data.get('current_price', 0)
            max_pain = float(option_data.get('max_pain', 0))
            if max_pain > 0 and current_price > 0:
                deviation = (current_price - max_pain) / current_price * 100
                prompt_parts.append(f"- Current vs Max Pain: {deviation:+.2f}% (Deviation)")
            prompt_parts.append("\n")

        prompt_parts.append("위 정보를 바탕으로 리스크를 분석하고 JSON 형식으로 답변하세요.")
            
        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Deprecated: Use _parse_json_response and Pydantic validation in analyze"""
        return self._parse_json_response(response_text)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response text with comprehensive defaults and field mapping

        Extracts JSON from reasoning_content by finding the LAST valid JSON object,
        since GLM-4.7 outputs chain-of-thought first, then JSON at the end.
        """
        import json
        import re

        result = None

        # Try direct JSON parsing first
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        if not result:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

        # Find the LAST valid JSON object by forward scanning
        # This is crucial for GLM-4.7 reasoning model which outputs: reasoning... then JSON
        # We scan forward and keep track of the LAST valid JSON (overwrites previous)
        if not result:
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
                            expected_fields = ['risk_level', 'confidence', 'recommendation']
                            if any(field in parsed for field in expected_fields):
                                # Keep overwriting with the LAST valid JSON
                                result = parsed
                        except json.JSONDecodeError:
                            pass
                        # Reset for potential later JSON (we want the LAST one)
                        start_idx = None

        if not result:
            raise ValueError("No valid JSON found in response")

        # Handle nested JSON structure from GLM (e.g., risk_analysis.risk_level)
        # Flatten nested structures
        if 'risk_analysis' in result:
            ra = result['risk_analysis']
            if 'overall_risk_level' in ra:
                result['risk_level'] = self._map_risk_level(ra['overall_risk_level'])
            if 'executive_summary' in ra:
                result.setdefault('reasoning', ra['executive_summary'])

        # Map common alternative field names
        field_mappings = {
            'overall_risk_level': ('risk_level', lambda x: self._map_risk_level(x)),
            'stop_loss_strategy': ('stop_loss_pct', None),
            'take_profit': ('take_profit_pct', None),
            'position_sizing': ('max_position_pct', None),
        }

        for alt_field, (target_field, mapper) in field_mappings.items():
            if alt_field in result and target_field not in result:
                value = result[alt_field]
                if mapper:
                    value = mapper(value)
                result[target_field] = value

        # Comprehensive default values for all required fields
        result.setdefault('risk_level', 'medium')
        result.setdefault('confidence', 0.5)
        result.setdefault('reasoning', 'Default reasoning')
        result.setdefault('stop_loss_pct', 0.02)
        result.setdefault('take_profit_pct', 0.10)
        result.setdefault('max_position_pct', 0.05)
        result.setdefault('sentiment_score', 0.0)
        result.setdefault('volatility_risk', 5.0)
        result.setdefault('dividend_risk', 'none')
        result.setdefault('recommendation', 'reduce_size')

        # Ensure numeric fields are correct type
        for field in ['confidence', 'stop_loss_pct', 'take_profit_pct', 'max_position_pct',
                      'sentiment_score', 'volatility_risk']:
            if field in result and not isinstance(result[field], (int, float)):
                result[field] = 0.0

        return result

    def _map_risk_level(self, raw_level: str) -> str:
        """Map various risk level strings to standard values"""
        level_map = {
            'low': 'low',
            'medium': 'medium',
            'moderate': 'medium',
            'moderate-high': 'high',
            'high': 'high',
            'extreme': 'extreme',
            'elevated': 'high',
            'warning': 'high',
        }
        level_lower = raw_level.lower() if isinstance(raw_level, str) else raw_level
        for key, value in level_map.items():
            if key in level_lower:
                return value
        return 'medium'

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
