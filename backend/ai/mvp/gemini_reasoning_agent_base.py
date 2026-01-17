"""
Gemini Reasoning Agent Base - Stage 1 of Two-Stage Architecture

Phase: MVP Consolidation - Gemini Integration
Date: 2026-01-17

Purpose:
    Gemini를 사용하여 자연어 기반 추론만 수행하는 기본 에이전트
    - JSON 출력 없이 자연어로만 생각 전개
    - 인과관계 분석 및 논리적 근거 서술
    - Stage 2 (Structuring Agent)에 전달할 텍스트 생성

Two-Stage Architecture:
    Stage 1: GeminiReasoningAgent (this file) → Gemini 추론 → 자연어 텍스트
    Stage 2: GeminiStructuringAgent → 텍스트를 JSON으로 변환 → Pydantic 스키마

Benefits:
    - 높은 Concurrency 제한 (GLM: 3 vs Gemini: 60+)
    - 빠른 응답 속도
    - 비용 절감
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeminiReasoningAgentBase(ABC):
    """
    Base class for all reasoning agents using Gemini

    Key responsibilities:
    - Generate natural language reasoning (NO JSON output)
    - Analyze cause and effect relationships
    - Provide logical arguments for decisions
    - Output text for Stage 2 structuring

    Benefits over GLM:
    - Higher concurrency limit (60+ vs 3)
    - Faster response time
    - Cost-effective
    """

    def __init__(self, agent_name: str, role: str):
        """
        Initialize Gemini Reasoning Agent

        Args:
            agent_name: Agent identifier (e.g., 'trader', 'analyst')
            role: Agent role description (e.g., '공격적 트레이더')
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI not available. Install with: pip install google-generativeai")

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Use Gemini 2.5 Flash Lite for fast reasoning (latest, not deprecated)
        self.model_name = os.getenv('GEMINI_MODEL_REASONING', 'gemini-2.5-flash-lite')
        self.model = genai.GenerativeModel(self.model_name)
        self.agent_name = agent_name
        self.role = role

        # Load reasoning-only system prompt
        self.system_prompt = self._load_system_prompt()

        logger.info(f"GeminiReasoningAgent initialized: {agent_name} with model {self.model_name}")

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
분석 결과를 자연어로 상세히 설명하십시오.

## 중요 지침
- JSON이나 코드 블록을 사용하지 마십시오
- 자연어 텍스트로만 분석 결과를 서술하십시오
- 논리적 근거와 인과관계를 중심으로 설명하십시오"""
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
            str: Prompt for Gemini reasoning
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
        Generate natural language reasoning using Gemini

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
            # Run Gemini in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            full_prompt = f"{self.system_prompt}\n\n{prompt}"

            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(full_prompt)
            )

            reasoning_text = response.text.strip()

            logger.info(f"Gemini reasoning completed for {self.agent_name}: {len(reasoning_text)} chars")

            return {
                'agent': f'{self.agent_name}_gemini_reasoning',
                'reasoning': reasoning_text,
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'model': self.model_name,
                'stage': 'reasoning',
                'llm_provider': 'gemini'
            }

        except Exception as e:
            logger.error(f"Gemini reasoning failed for {self.agent_name}: {e}")
            return {
                'agent': f'{self.agent_name}_gemini_reasoning',
                'reasoning': f'추론 실패: {str(e)}',
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'model': self.model_name,
                'stage': 'reasoning',
                'llm_provider': 'gemini',
                'error': str(e)
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': f'{self.agent_name.title()}GeminiReasoningAgent',
            'role': self.role,
            'stage': 'reasoning',
            'model': self.model_name,
            'llm_provider': 'gemini',
            'focus': '자연어 기반 추론 및 논리 전개',
            'output_format': 'plain text (no JSON)',
            'benefits_over_glm': [
                '높은 Concurrency 제한 (60+ vs 3)',
                '빠른 응답 속도',
                '비용 효율성'
            ],
            'responsibilities': [
                '자연어로 생각 전개',
                '인과관계 분석',
                '논리적 근거 서술',
                'Stage 2 구조화 에이전트에 텍스트 제공'
            ]
        }
