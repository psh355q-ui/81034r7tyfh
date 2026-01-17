"""
Reasoning Agent Base - Stage 1 of Two-Stage Architecture

Phase: MVP Consolidation
Date: 2026-01-17

Purpose:
    GLM-4.7을 사용하여 자연어 기반 추론만 수행하는 기본 에이전트
    - JSON 출력 없이 자연어로만 생각 전개
    - 인과관계 분석 및 논리적 근거 서술
    - Stage 2 (Structuring Agent)에 전달할 텍스트 생성

Two-Stage Architecture:
    Stage 1: ReasoningAgent (this file) → GLM-4.7 추론 → 자연어 텍스트
    Stage 2: StructuringAgent → 텍스트를 JSON으로 변환 → Pydantic 스키마
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReasoningAgentBase(ABC):
    """
    Base class for all reasoning agents using GLM-4.7

    Key responsibilities:
    - Generate natural language reasoning (NO JSON output)
    - Analyze cause and effect relationships
    - Provide logical arguments for decisions
    - Output text for Stage 2 structuring
    """

    def __init__(self, agent_name: str, role: str):
        """
        Initialize Reasoning Agent

        Args:
            agent_name: Agent identifier (e.g., 'trader', 'risk', 'analyst')
            role: Agent role description (e.g., '공격적 트레이더')
        """
        if not GLM_AVAILABLE:
            raise ImportError("GLM client not available. Install with: pip install zhipuai")

        api_key = os.getenv('GLM_API_KEY')
        if not api_key:
            raise ValueError("GLM_API_KEY not found in environment variables")

        # Stage 1 (Reasoning) uses GLM-4.7 for deep reasoning
        self.model = os.getenv('GLM_MODEL_REASONING', 'glm-4.7')
        self.glm_client = GLMClient(api_key=api_key, model=self.model)
        self.agent_name = agent_name
        self.role = role

        # Load reasoning-only system prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load reasoning-only system prompt from docs/prompts/{agent_name}_reasoning.md"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            prompt_path = os.path.join(project_root, 'docs', 'prompts', f'{self.agent_name}_reasoning.md')

            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content.strip()

        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_path}, using fallback")
            return f"""당신은 'War Room'의 {self.role}입니다.
분석 결과를 자연어로 상세히 설명하십시오."""
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return f"""당신은 'War Room'의 {self.role}입니다.
분석 결과를 자연어로 상세히 설명하십시오."""

    @abstractmethod
    def _build_reasoning_prompt(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Build reasoning prompt for the agent.

        Subclasses must implement this to provide agent-specific prompt structure.

        Returns:
            str: Prompt for GLM-4.7 reasoning
        """
        pass

    async def reason(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate natural language reasoning using GLM-4.7

        This is Stage 1 of the two-stage architecture.
        Output is plain text reasoning, not JSON.

        Args:
            symbol: Stock symbol
            price_data: Current price data
            technical_data: Technical indicators
            **kwargs: Additional agent-specific data

        Returns:
            Dict with reasoning text and metadata:
            {
                'agent': str,
                'reasoning': str,  # Natural language analysis
                'symbol': str,
                'timestamp': str,
                'model': str
            }
        """
        prompt = self._build_reasoning_prompt(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            **kwargs
        )

        try:
            response = await self.glm_client.chat(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.7  # Higher temp for more creative reasoning
            )

            # Extract reasoning from response
            message = response["choices"][0]["message"]
            reasoning_text = (message.get("content") or message.get("reasoning_content", "")).strip()

            return {
                'agent': f'{self.agent_name}_reasoning',
                'reasoning': reasoning_text,
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'model': self.model,
                'stage': 'reasoning'
            }

        except Exception as e:
            logger.error(f"Reasoning failed for {self.agent_name}: {e}")
            return {
                'agent': f'{self.agent_name}_reasoning',
                'reasoning': f'추론 실패: {str(e)}',
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'model': self.model,
                'stage': 'reasoning',
                'error': str(e)
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
            'name': f'{self.agent_name.title()}ReasoningAgent',
            'role': self.role,
            'stage': 'reasoning',
            'model': self.model,
            'focus': '자연어 기반 추론 및 논리 전개',
            'output_format': 'plain text (no JSON)',
            'responsibilities': [
                '자연어로 생각 전개',
                '인과관계 분석',
                '논리적 근거 서술',
                'Stage 2 구조화 에이전트에 텍스트 제공'
            ]
        }
