"""
Two-Stage TraderAgentMVP Integration Tests

Tests the new two-stage architecture:
- Stage 1: ReasoningAgent (GLM-4.7) → Natural language
- Stage 2: StructuringAgent → JSON conversion

Run with:
    python -m pytest backend/tests/test_twostage_trader_agent.py -v
"""

import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Set environment variables before importing
os.environ.setdefault('GLM_API_KEY', 'test_key')


class TestTraderReasoningAgent:
    """Test Stage 1: Reasoning Agent"""

    @pytest.fixture
    def reasoning_agent(self):
        from backend.ai.mvp.trader_agent_twostage import TraderReasoningAgent
        return TraderReasoningAgent()

    def test_initialization(self, reasoning_agent):
        """Test agent initializes correctly"""
        assert reasoning_agent.agent_name == 'trader'
        assert reasoning_agent.role == '공격적 트레이더'
        assert reasoning_agent.weight == 0.35

    def test_build_reasoning_prompt(self, reasoning_agent):
        """Test prompt building"""
        price_data = {
            'current_price': 150.25,
            'open': 148.50,
            'high': 151.00,
            'low': 147.80,
            'volume': 45000000
        }

        technical_data = {
            'rsi': 62.5,
            'macd': {'value': 1.2, 'signal': 0.8}
        }

        prompt = reasoning_agent._build_reasoning_prompt(
            symbol='AAPL',
            price_data=price_data,
            technical_data=technical_data
        )

        assert 'AAPL' in prompt
        assert '150.25' in prompt
        assert 'RSI' in prompt
        assert '62.5' in prompt

    @pytest.mark.asyncio
    async def test_reasoning_generates_text(self, reasoning_agent):
        """Test reasoning generates natural language (not JSON)"""
        # Mock GLM response with natural language reasoning
        mock_response = {
            "choices": [{
                "message": {
                    "content": "기술적 상태: RSI 62.5로 중립 영역입니다.\n모멘텀 분석: 현재 상승 모멘텀이 있습니다.\n트레이딩 제안: BUY 권장."
                }
            }]
        }

        with patch.object(reasoning_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_response)):
            result = await reasoning_agent.reason(
                symbol='AAPL',
                price_data={'current_price': 150.0},
                technical_data=None
            )

            assert result['agent'] == 'trader_reasoning'
            assert 'reasoning' in result
            assert isinstance(result['reasoning'], str)
            assert len(result['reasoning']) > 0
            # Should be plain text, not JSON
            assert not result['reasoning'].strip().startswith('{')


class TestStructuringAgent:
    """Test Stage 2: Structuring Agent"""

    @pytest.fixture
    def structuring_agent(self):
        from backend.ai.mvp.structuring_agent import StructuringAgent
        return StructuringAgent()

    def test_initialization(self, structuring_agent):
        """Test agent initializes correctly"""
        assert structuring_agent.model == 'glm-4-flash'
        assert structuring_agent.system_prompt is not None

    def test_extract_json_direct(self, structuring_agent):
        """Test JSON extraction from direct JSON string"""
        json_str = '{"action": "buy", "confidence": 0.8}'
        result = structuring_agent._extract_json(json_str)
        assert result['action'] == 'buy'
        assert result['confidence'] == 0.8

    def test_extract_json_from_markdown(self, structuring_agent):
        """Test JSON extraction from markdown code block"""
        markdown_text = '''```json
{
    "action": "sell",
    "confidence": 0.7
}
```'''
        result = structuring_agent._extract_json(markdown_text)
        assert result['action'] == 'sell'
        assert result['confidence'] == 0.7

    def test_extract_json_with_text(self, structuring_agent):
        """Test JSON extraction from text with JSON embedded"""
        text_with_json = '''분석 결과:
일부 설명 텍스트입니다.
{"action": "hold", "confidence": 0.5}
추가 설명'''
        result = structuring_agent._extract_json(text_with_json)
        assert result['action'] == 'hold'
        assert result['confidence'] == 0.5

    def test_get_default_result_trader(self, structuring_agent):
        """Test default result generation for trader agent"""
        result = structuring_agent._get_default_result('trader', 'AAPL', 'Test error')
        assert result['agent'] == 'trader_mvp'
        assert result['action'] == 'pass'
        assert result['confidence'] == 0.0
        assert 'Test error' in result['reasoning']

    def test_get_default_result_risk(self, structuring_agent):
        """Test default result generation for risk agent"""
        result = structuring_agent._get_default_result('risk', 'AAPL', 'Test error')
        assert result['agent'] == 'risk_mvp'
        assert result['risk_level'] == 'high'
        assert result['recommendation'] == 'reject'

    @pytest.mark.asyncio
    async def test_structure_converts_text_to_json(self, structuring_agent):
        """Test structuring converts reasoning text to JSON"""
        reasoning_text = """
        기술적 상태: RSI 62.5로 중립 영역입니다.
        모멘텀 분석: 현재 상승 모멘텀이 있습니다.
        트레이딩 제안: BUY 권장, 진입가 $150, 손절가 $147, 목표가 $155.
        기회 등급: 72점.
        리스크-리워드: 1:2.5
        """

        schema_definition = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"}
            }
        }

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"action": "buy", "confidence": 0.72, "reasoning": "기술적 강세와 모멘텀 확인"}'
                }
            }]
        }

        with patch.object(structuring_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_response)):
            result = await structuring_agent.structure(
                reasoning_text=reasoning_text,
                schema_definition=schema_definition,
                agent_type='trader',
                symbol='AAPL'
            )

            assert result['agent'] == 'trader_mvp'
            assert result['action'] == 'buy'
            assert result['confidence'] == 0.72
            assert result['stage'] == 'structured'
            assert 'symbol' in result


class TestTraderAgentMVPTwoStage:
    """Test Two-Stage Trader Agent Integration"""

    @pytest.fixture
    def trader_agent(self):
        from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP
        return TraderAgentMVP()

    def test_initialization(self, trader_agent):
        """Test agent initializes correctly"""
        assert trader_agent.weight == 0.35
        assert trader_agent.reasoning_agent is not None
        assert trader_agent.structuring_agent is not None

    @pytest.mark.asyncio
    async def test_analyze_two_stage_pipeline(self, trader_agent):
        """Test complete two-stage analysis pipeline"""

        # Mock Stage 1: Reasoning
        mock_reasoning_response = {
            "choices": [{
                "message": {
                    "content": """
                    기술적 상태: RSI 62.5로 중립 영역입니다.
                    모멘텀 분석: 현재 강한 상승 모멘텀입니다.
                    트레이딩 제안: BUY, 진입가 $150, 손절가 $147, 목표가 $155.
                    기회 등급: 72점.
                    리스크-리워드: 1:2.5
                    """
                }
            }]
        }

        # Mock Stage 2: Structuring
        mock_structuring_response = {
            "choices": [{
                "message": {
                    "content": '{"action": "buy", "confidence": 0.72, "reasoning": "기술적 강세와 모멘텀 확인", "opportunity_score": 72.0, "momentum_strength": "strong", "risk_reward_ratio": 2.5}'
                }
            }]
        }

        price_data = {
            'current_price': 150.25,
            'open': 148.50,
            'high': 151.00,
            'low': 147.80,
            'volume': 45000000
        }

        technical_data = {
            'rsi': 62.5,
            'macd': {'value': 1.2, 'signal': 0.8}
        }

        # Apply mocks
        with patch.object(trader_agent.reasoning_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_reasoning_response)):
            with patch.object(trader_agent.structuring_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_structuring_response)):
                result = await trader_agent.analyze(
                    symbol='AAPL',
                    price_data=price_data,
                    technical_data=technical_data
                )

                # Verify result
                assert result['agent'] == 'trader_mvp'
                assert result['action'] == 'buy'
                assert result['confidence'] == 0.72
                assert result['opportunity_score'] == 72.0
                assert result['weight'] == 0.35
                assert 'latency_seconds' in result
                assert result['stage'] == 'structured'
                assert 'reasoning_text' in result

    @pytest.mark.asyncio
    async def test_analyze_handles_reasoning_failure(self, trader_agent):
        """Test error handling when reasoning stage fails"""

        # Mock reasoning failure
        mock_error_response = {
            "choices": [{
                "message": {
                    "content": ""
                }
            }]
        }

        price_data = {'current_price': 150.0}

        with patch.object(trader_agent.reasoning_agent.glm_client, 'chat', new=AsyncMock(side_effect=Exception("API Error"))):
            result = await trader_agent.analyze(
                symbol='AAPL',
                price_data=price_data
            )

            # Should return safe default
            assert result['action'] == 'pass'
            assert result['confidence'] == 0.0
            assert 'error' in result
            assert result['stage'] == 'failed'

    @pytest.mark.asyncio
    async def test_analyze_handles_structuring_failure(self, trader_agent):
        """Test error handling when structuring stage fails"""

        # Mock successful reasoning
        mock_reasoning_response = {
            "choices": [{
                "message": {
                    "content": "BUY 권장, 기회 등급 72점"
                }
            }]
        }

        price_data = {'current_price': 150.0}

        # Reasoning succeeds, but structuring fails
        with patch.object(trader_agent.reasoning_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_reasoning_response)):
            with patch.object(trader_agent.structuring_agent.glm_client, 'chat', new=AsyncMock(side_effect=Exception("Structuring Error"))):
                result = await trader_agent.analyze(
                    symbol='AAPL',
                    price_data=price_data
                )

                # Should return safe default from structuring agent
                assert 'error' in result
                # Either stage failed or structuring default returned
                assert result.get('stage') in ['failed', 'structured']

    def test_get_agent_info(self, trader_agent):
        """Test agent info returns correct structure"""
        info = trader_agent.get_agent_info()

        assert info['name'] == 'TraderAgentMVP (Two-Stage)'
        assert info['weight'] == 0.35
        assert info['architecture'] == 'two-stage'
        assert 'stages' in info
        assert info['stages']['reasoning'] == 'GLM-4.7 → 자연어 추론'
        assert info['stages']['structuring'] == 'Lightweight → JSON 변환'


class TestLatencyMeasurement:
    """Test latency measurement and performance"""

    @pytest.fixture
    def trader_agent(self):
        from backend.ai.mvp.trader_agent_twostage import TraderAgentMVP
        return TraderAgentMVP()

    @pytest.mark.asyncio
    async def test_latency_is_measured(self, trader_agent):
        """Test that latency is measured and included in result"""
        mock_reasoning_response = {
            "choices": [{
                "message": {
                    "content": "BUY 권장"
                }
            }]
        }

        mock_structuring_response = {
            "choices": [{
                "message": {
                    "content": '{"action": "buy", "confidence": 0.7, "reasoning": "test"}'
                }
            }]
        }

        with patch.object(trader_agent.reasoning_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_reasoning_response)):
            with patch.object(trader_agent.structuring_agent.glm_client, 'chat', new=AsyncMock(return_value=mock_structuring_response)):
                result = await trader_agent.analyze(
                    symbol='AAPL',
                    price_data={'current_price': 150.0}
                )

                assert 'latency_seconds' in result
                assert isinstance(result['latency_seconds'], (int, float))
                assert result['latency_seconds'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
