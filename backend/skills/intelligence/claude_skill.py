"""
Claude Skill

Claude AI 분석 및 추론 Skill (복잡한 전략 수립용)

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
import os

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class ClaudeSkill(BaseSkill):
    """
    Claude AI 분석 및 추론 Skill

    기능:
    - 복잡한 전략 수립 (Chain-of-Thought Reasoning)
    - 리스크 분석 (Deep Analysis)
    - 시장 트렌드 예측 (Long-form Analysis)
    - 포트폴리오 최적화 (Complex Reasoning)

    Usage:
        skill = ClaudeSkill()
        tools = skill.get_tools()
        result = await skill.execute("analyze_strategy", strategy_description="...")
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Intelligence.Claude",
            category=SkillCategory.INTELLIGENCE,
            description="Claude AI - 복잡한 전략 수립, 리스크 분석, 장문 추론",
            keywords=[
                "전략", "strategy", "추론", "reasoning", "분석", "analysis",
                "리스크", "risk", "포트폴리오", "portfolio", "최적화", "optimization",
                "claude", "복잡한", "complex", "심층", "deep"
            ],
            cost_tier=CostTier.HIGH,  # Claude Sonnet 기준
            requires_api_key=True,
            rate_limit_per_min=50,
        )

        # Claude 클라이언트 초기화 (지연 로딩)
        self._client = None

    def _get_client(self):
        """Claude 클라이언트 가져오기 (지연 로딩)"""
        if self._client is None:
            try:
                import anthropic

                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")

                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info("Claude client initialized")
            except ImportError:
                logger.error("Failed to import anthropic library")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
                raise

        return self._client

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Claude Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_strategy",
                    "description": "복잡한 투자 전략을 심층 분석하고 개선 방안 제시. Chain-of-Thought 추론 사용.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_description": {
                                "type": "string",
                                "description": "분석할 전략 설명 (상세할수록 좋음)"
                            },
                            "market_conditions": {
                                "type": "string",
                                "description": "현재 시장 상황 (optional)",
                                "default": ""
                            },
                            "constraints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "제약 조건 리스트 (예: 리스크 한도, 투자 기간)",
                                "default": []
                            }
                        },
                        "required": ["strategy_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "deep_risk_analysis",
                    "description": "포트폴리오 또는 전략의 심층 리스크 분석. 다양한 시나리오 검토.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "portfolio": {
                                "type": "object",
                                "description": "포트폴리오 구성 (ticker: weight 형태)",
                                "additionalProperties": {"type": "number"}
                            },
                            "risk_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["market", "credit", "liquidity", "operational", "all"]
                                },
                                "description": "분석할 리스크 유형",
                                "default": ["all"]
                            },
                            "time_horizon": {
                                "type": "string",
                                "description": "분석 기간 (예: '1 month', '1 year')",
                                "default": "3 months"
                            }
                        },
                        "required": ["portfolio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_portfolio",
                    "description": "주어진 제약 조건 하에서 포트폴리오 최적화 제안",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_portfolio": {
                                "type": "object",
                                "description": "현재 포트폴리오 (ticker: weight)",
                                "additionalProperties": {"type": "number"}
                            },
                            "target_return": {
                                "type": "number",
                                "description": "목표 수익률 (%)",
                                "default": 10.0
                            },
                            "max_risk": {
                                "type": "number",
                                "description": "최대 허용 리스크 (표준편차, %)",
                                "default": 15.0
                            },
                            "constraints": {
                                "type": "object",
                                "description": "제약 조건 (max_single_position, sector_limits 등)",
                                "default": {}
                            }
                        },
                        "required": ["current_portfolio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "predict_market_trend",
                    "description": "시장 데이터와 뉴스를 종합하여 중장기 트렌드 예측",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "market_data": {
                                "type": "string",
                                "description": "시장 데이터 요약 (가격, 거래량, 지표 등)"
                            },
                            "news_summary": {
                                "type": "string",
                                "description": "최근 뉴스 요약"
                            },
                            "prediction_period": {
                                "type": "string",
                                "description": "예측 기간 (예: '1 week', '1 month', '3 months')",
                                "default": "1 month"
                            }
                        },
                        "required": ["market_data"]
                    }
                }
            }
        ]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        도구 실행

        Args:
            tool_name: 실행할 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            실행 결과

        Raises:
            ValueError: 알 수 없는 도구
        """
        try:
            if tool_name == "analyze_strategy":
                result = await self._analyze_strategy(**kwargs)
            elif tool_name == "deep_risk_analysis":
                result = await self._deep_risk_analysis(**kwargs)
            elif tool_name == "optimize_portfolio":
                result = await self._optimize_portfolio(**kwargs)
            elif tool_name == "predict_market_trend":
                result = await self._predict_market_trend(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트 (Claude Sonnet 4.5 기준)
            # Input: $3/MTok, Output: $15/MTok
            # 평균 4K input + 2K output 가정
            estimated_cost = (4000 * 3 / 1_000_000) + (2000 * 15 / 1_000_000)
            self._track_call(success=True, cost_usd=estimated_cost)

            return result

        except Exception as e:
            # 오류 추적
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _analyze_strategy(
        self,
        strategy_description: str,
        market_conditions: str = "",
        constraints: List[str] = None
    ) -> Dict[str, Any]:
        """
        전략 심층 분석

        Args:
            strategy_description: 전략 설명
            market_conditions: 시장 상황
            constraints: 제약 조건

        Returns:
            분석 결과
        """
        client = self._get_client()
        constraints = constraints or []

        # 프롬프트 구성
        prompt = f"""당신은 전문 투자 전략가입니다. 다음 투자 전략을 심층 분석하고 개선 방안을 제시해주세요.

전략 설명:
{strategy_description}

시장 상황:
{market_conditions if market_conditions else "정보 없음"}

제약 조건:
{chr(10).join(f"- {c}" for c in constraints) if constraints else "제약 없음"}

다음 항목을 포함하여 분석해주세요:
1. 전략의 핵심 논리 및 가정
2. 강점과 약점
3. 시장 상황에 따른 적합성
4. 잠재적 리스크
5. 개선 방안 (구체적인 액션 아이템)
6. 예상 성과 (정량적 추정)

분석은 체계적이고 논리적으로 진행해주세요."""

        # Claude API 호출
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis = message.content[0].text

        return {
            "success": True,
            "strategy_description": strategy_description,
            "analysis": analysis,
            "tokens_used": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        }

    async def _deep_risk_analysis(
        self,
        portfolio: Dict[str, float],
        risk_types: List[str] = None,
        time_horizon: str = "3 months"
    ) -> Dict[str, Any]:
        """
        심층 리스크 분석

        Args:
            portfolio: 포트폴리오 구성
            risk_types: 분석할 리스크 유형
            time_horizon: 분석 기간

        Returns:
            리스크 분석 결과
        """
        client = self._get_client()
        risk_types = risk_types or ["all"]

        # 포트폴리오 요약
        portfolio_str = "\n".join(f"- {ticker}: {weight*100:.1f}%" for ticker, weight in portfolio.items())

        prompt = f"""당신은 전문 리스크 분석가입니다. 다음 포트폴리오의 리스크를 심층 분석해주세요.

포트폴리오:
{portfolio_str}

분석 대상 리스크: {', '.join(risk_types)}
분석 기간: {time_horizon}

다음 항목을 포함하여 분석해주세요:
1. 각 리스크 유형별 평가 (시장, 신용, 유동성, 운영)
2. 시나리오 분석 (최선, 기본, 최악)
3. 상관관계 리스크
4. 집중도 리스크
5. 헤지 전략 제안
6. 종합 리스크 점수 (1-10점)

정량적 데이터와 정성적 판단을 모두 활용해주세요."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis = message.content[0].text

        return {
            "success": True,
            "portfolio": portfolio,
            "risk_analysis": analysis,
            "tokens_used": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        }

    async def _optimize_portfolio(
        self,
        current_portfolio: Dict[str, float],
        target_return: float = 10.0,
        max_risk: float = 15.0,
        constraints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        포트폴리오 최적화

        Args:
            current_portfolio: 현재 포트폴리오
            target_return: 목표 수익률
            max_risk: 최대 리스크
            constraints: 제약 조건

        Returns:
            최적화 제안
        """
        client = self._get_client()
        constraints = constraints or {}

        portfolio_str = "\n".join(f"- {ticker}: {weight*100:.1f}%" for ticker, weight in current_portfolio.items())
        constraints_str = "\n".join(f"- {k}: {v}" for k, v in constraints.items()) if constraints else "제약 없음"

        prompt = f"""당신은 포트폴리오 최적화 전문가입니다. 다음 포트폴리오를 최적화해주세요.

현재 포트폴리오:
{portfolio_str}

목표:
- 목표 수익률: {target_return}% (연환산)
- 최대 리스크: {max_risk}% (표준편차)

제약 조건:
{constraints_str}

다음 항목을 제공해주세요:
1. 최적화된 포트폴리오 구성 (ticker: weight)
2. 예상 수익률 및 리스크
3. 현재 대비 변경 사항 설명
4. 리밸런싱 액션 플랜
5. 최적화 논리 및 가정
6. 대안 포트폴리오 (보수적 / 공격적)

실행 가능한 구체적인 제안을 해주세요."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        optimization = message.content[0].text

        return {
            "success": True,
            "current_portfolio": current_portfolio,
            "optimization_result": optimization,
            "tokens_used": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        }

    async def _predict_market_trend(
        self,
        market_data: str,
        news_summary: str = "",
        prediction_period: str = "1 month"
    ) -> Dict[str, Any]:
        """
        시장 트렌드 예측

        Args:
            market_data: 시장 데이터
            news_summary: 뉴스 요약
            prediction_period: 예측 기간

        Returns:
            트렌드 예측 결과
        """
        client = self._get_client()

        prompt = f"""당신은 시장 분석 전문가입니다. 제공된 데이터를 바탕으로 향후 {prediction_period} 동안의 시장 트렌드를 예측해주세요.

시장 데이터:
{market_data}

최근 뉴스:
{news_summary if news_summary else "정보 없음"}

다음 항목을 포함하여 예측해주세요:
1. 주요 트렌드 방향 (상승/하락/횡보)
2. 신뢰도 (높음/중간/낮음)
3. 핵심 영향 요인
4. 리스크 시나리오
5. 섹터별 전망
6. 투자 액션 아이템

데이터 기반의 논리적 예측을 제공해주세요."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        prediction = message.content[0].text

        return {
            "success": True,
            "prediction_period": prediction_period,
            "prediction": prediction,
            "tokens_used": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        }
