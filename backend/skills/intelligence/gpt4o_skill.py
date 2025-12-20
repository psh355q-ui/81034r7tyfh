"""
GPT-4o Skill

GPT-4o 분석 및 생성 Skill (전략 생성 및 코드 작성용)

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
import os

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class GPT4oSkill(BaseSkill):
    """
    GPT-4o 분석 및 생성 Skill

    기능:
    - 트레이딩 전략 생성 (Code Generation)
    - 백테스트 코드 작성 (Python Code)
    - 지표 계산 로직 생성 (Technical Analysis)
    - 데이터 처리 스크립트 작성 (Data Pipeline)

    Usage:
        skill = GPT4oSkill()
        tools = skill.get_tools()
        result = await skill.execute("generate_strategy_code", strategy_idea="...")
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Intelligence.GPT4o",
            category=SkillCategory.INTELLIGENCE,
            description="GPT-4o - 전략 코드 생성, 백테스트 스크립트 작성",
            keywords=[
                "코드", "code", "생성", "generate", "작성", "write",
                "전략", "strategy", "백테스트", "backtest", "지표", "indicator",
                "gpt", "gpt-4", "gpt4o", "스크립트", "script", "python"
            ],
            cost_tier=CostTier.MEDIUM,  # GPT-4o 기준
            requires_api_key=True,
            rate_limit_per_min=500,  # Tier 2 기준
        )

        # OpenAI 클라이언트 초기화 (지연 로딩)
        self._client = None

    def _get_client(self):
        """OpenAI 클라이언트 가져오기 (지연 로딩)"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")

                self._client = AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.error("Failed to import openai library")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                raise

        return self._client

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        GPT-4o Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_strategy_code",
                    "description": "트레이딩 전략 아이디어를 실행 가능한 Python 코드로 생성",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_idea": {
                                "type": "string",
                                "description": "전략 아이디어 설명 (예: 'RSI 30 이하 매수, 70 이상 매도')"
                            },
                            "code_framework": {
                                "type": "string",
                                "description": "사용할 프레임워크 (backtrader, vectorbt, custom)",
                                "enum": ["backtrader", "vectorbt", "custom"],
                                "default": "custom"
                            },
                            "include_comments": {
                                "type": "boolean",
                                "description": "주석 포함 여부",
                                "default": True
                            }
                        },
                        "required": ["strategy_idea"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_backtest_script",
                    "description": "백테스트를 위한 완전한 Python 스크립트 생성",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_code": {
                                "type": "string",
                                "description": "백테스트할 전략 코드"
                            },
                            "data_source": {
                                "type": "string",
                                "description": "데이터 소스 (yfinance, csv, database)",
                                "default": "yfinance"
                            },
                            "date_range": {
                                "type": "object",
                                "description": "백테스트 기간 (start_date, end_date)",
                                "properties": {
                                    "start_date": {"type": "string"},
                                    "end_date": {"type": "string"}
                                },
                                "default": {"start_date": "2023-01-01", "end_date": "2024-12-31"}
                            },
                            "initial_capital": {
                                "type": "number",
                                "description": "초기 자본 (USD)",
                                "default": 10000
                            }
                        },
                        "required": ["strategy_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_indicator_code",
                    "description": "커스텀 기술적 지표 계산 코드 생성",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "indicator_description": {
                                "type": "string",
                                "description": "지표 설명 (예: '20일 이동평균과 볼린저 밴드의 조합')"
                            },
                            "input_data": {
                                "type": "string",
                                "description": "입력 데이터 형식 (pandas DataFrame, numpy array)",
                                "default": "pandas DataFrame"
                            },
                            "optimize_performance": {
                                "type": "boolean",
                                "description": "성능 최적화 코드 포함 (numba, vectorization)",
                                "default": False
                            }
                        },
                        "required": ["indicator_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_data_pipeline",
                    "description": "데이터 수집, 정제, 저장을 위한 파이프라인 코드 생성",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_sources": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "데이터 소스 목록 (예: ['yfinance', 'alpha_vantage', 'news_api'])"
                            },
                            "processing_steps": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "처리 단계 (예: ['normalize', 'handle_missing', 'feature_engineering'])",
                                "default": []
                            },
                            "storage_format": {
                                "type": "string",
                                "description": "저장 형식 (csv, parquet, database)",
                                "default": "parquet"
                            }
                        },
                        "required": ["data_sources"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fix_code_error",
                    "description": "에러가 발생한 코드를 분석하고 수정된 코드 제공",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "error_code": {
                                "type": "string",
                                "description": "에러가 발생한 코드"
                            },
                            "error_message": {
                                "type": "string",
                                "description": "에러 메시지"
                            },
                            "context": {
                                "type": "string",
                                "description": "추가 컨텍스트 (optional)",
                                "default": ""
                            }
                        },
                        "required": ["error_code", "error_message"]
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
            if tool_name == "generate_strategy_code":
                result = await self._generate_strategy_code(**kwargs)
            elif tool_name == "create_backtest_script":
                result = await self._create_backtest_script(**kwargs)
            elif tool_name == "generate_indicator_code":
                result = await self._generate_indicator_code(**kwargs)
            elif tool_name == "create_data_pipeline":
                result = await self._create_data_pipeline(**kwargs)
            elif tool_name == "fix_code_error":
                result = await self._fix_code_error(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트 (GPT-4o 기준)
            # Input: $2.5/MTok, Output: $10/MTok
            # 평균 3K input + 2K output 가정
            estimated_cost = (3000 * 2.5 / 1_000_000) + (2000 * 10 / 1_000_000)
            self._track_call(success=True, cost_usd=estimated_cost)

            return result

        except Exception as e:
            # 오류 추적
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _generate_strategy_code(
        self,
        strategy_idea: str,
        code_framework: str = "custom",
        include_comments: bool = True
    ) -> Dict[str, Any]:
        """
        전략 코드 생성

        Args:
            strategy_idea: 전략 아이디어
            code_framework: 프레임워크
            include_comments: 주석 포함 여부

        Returns:
            생성된 코드
        """
        client = self._get_client()

        system_prompt = f"""당신은 전문 트레이딩 전략 개발자입니다.
사용자가 제시한 전략 아이디어를 실행 가능한 Python 코드로 변환해주세요.

프레임워크: {code_framework}
주석 포함: {'예' if include_comments else '아니오'}

코드는 다음 구조를 따라야 합니다:
1. 필요한 라이브러리 임포트
2. 전략 클래스 또는 함수 정의
3. 진입/청산 로직
4. 포지션 관리
5. 사용 예시

코드는 깔끔하고 재사용 가능해야 합니다."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"전략 아이디어:\n{strategy_idea}"}
            ],
            temperature=0.3,  # 코드 생성은 낮은 temperature
            max_tokens=2000
        )

        code = response.choices[0].message.content

        return {
            "success": True,
            "strategy_idea": strategy_idea,
            "framework": code_framework,
            "generated_code": code,
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }

    async def _create_backtest_script(
        self,
        strategy_code: str,
        data_source: str = "yfinance",
        date_range: Dict[str, str] = None,
        initial_capital: float = 10000
    ) -> Dict[str, Any]:
        """
        백테스트 스크립트 생성

        Args:
            strategy_code: 전략 코드
            data_source: 데이터 소스
            date_range: 백테스트 기간
            initial_capital: 초기 자본

        Returns:
            백테스트 스크립트
        """
        client = self._get_client()
        date_range = date_range or {"start_date": "2023-01-01", "end_date": "2024-12-31"}

        system_prompt = f"""당신은 백테스트 전문가입니다.
제공된 전략 코드를 사용하여 완전한 백테스트 스크립트를 작성해주세요.

스크립트는 다음을 포함해야 합니다:
1. 데이터 로딩 ({data_source})
2. 전략 실행
3. 성과 측정 (수익률, Sharpe Ratio, MDD 등)
4. 시각화 (가격 차트, 포지션, 손익 곡선)
5. 결과 출력

초기 자본: ${initial_capital:,.0f}
백테스트 기간: {date_range['start_date']} ~ {date_range['end_date']}

실행 가능한 완전한 스크립트를 제공해주세요."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"전략 코드:\n```python\n{strategy_code}\n```"}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        script = response.choices[0].message.content

        return {
            "success": True,
            "backtest_script": script,
            "configuration": {
                "data_source": data_source,
                "date_range": date_range,
                "initial_capital": initial_capital
            },
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }

    async def _generate_indicator_code(
        self,
        indicator_description: str,
        input_data: str = "pandas DataFrame",
        optimize_performance: bool = False
    ) -> Dict[str, Any]:
        """
        지표 코드 생성

        Args:
            indicator_description: 지표 설명
            input_data: 입력 데이터 형식
            optimize_performance: 성능 최적화 여부

        Returns:
            지표 코드
        """
        client = self._get_client()

        system_prompt = f"""당신은 기술적 지표 개발 전문가입니다.
제공된 설명을 바탕으로 커스텀 지표 계산 코드를 작성해주세요.

입력 데이터 형식: {input_data}
성능 최적화: {'예 (numba, vectorization 활용)' if optimize_performance else '아니오'}

코드는 다음을 포함해야 합니다:
1. 지표 계산 함수
2. 파라미터 설명 (docstring)
3. 입력 유효성 검사
4. 사용 예시
5. 테스트 케이스

깔끔하고 재사용 가능한 코드를 작성해주세요."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"지표 설명:\n{indicator_description}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        code = response.choices[0].message.content

        return {
            "success": True,
            "indicator_description": indicator_description,
            "generated_code": code,
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }

    async def _create_data_pipeline(
        self,
        data_sources: List[str],
        processing_steps: List[str] = None,
        storage_format: str = "parquet"
    ) -> Dict[str, Any]:
        """
        데이터 파이프라인 생성

        Args:
            data_sources: 데이터 소스 목록
            processing_steps: 처리 단계
            storage_format: 저장 형식

        Returns:
            파이프라인 코드
        """
        client = self._get_client()
        processing_steps = processing_steps or []

        sources_str = ", ".join(data_sources)
        steps_str = ", ".join(processing_steps) if processing_steps else "기본 정제"

        system_prompt = f"""당신은 데이터 파이프라인 아키텍트입니다.
다음 데이터 소스에서 데이터를 수집하고 처리하는 파이프라인을 작성해주세요.

데이터 소스: {sources_str}
처리 단계: {steps_str}
저장 형식: {storage_format}

파이프라인은 다음을 포함해야 합니다:
1. 각 소스에서 데이터 수집
2. 데이터 정제 및 변환
3. 데이터 통합 (여러 소스)
4. 에러 핸들링
5. 로깅
6. 저장 ({storage_format})

모듈화되고 확장 가능한 코드를 작성해주세요."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "완전한 데이터 파이프라인 코드를 작성해주세요."}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        pipeline_code = response.choices[0].message.content

        return {
            "success": True,
            "data_sources": data_sources,
            "pipeline_code": pipeline_code,
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }

    async def _fix_code_error(
        self,
        error_code: str,
        error_message: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        코드 에러 수정

        Args:
            error_code: 에러 코드
            error_message: 에러 메시지
            context: 추가 컨텍스트

        Returns:
            수정된 코드
        """
        client = self._get_client()

        system_prompt = """당신은 디버깅 전문가입니다.
제공된 에러 코드와 메시지를 분석하여 수정된 코드를 제공해주세요.

응답 형식:
1. 에러 원인 분석
2. 수정된 코드 (전체)
3. 변경 사항 설명
4. 추가 개선 제안 (있다면)

명확하고 실행 가능한 해결책을 제공해주세요."""

        user_prompt = f"""에러 코드:
```python
{error_code}
```

에러 메시지:
{error_message}

{f'추가 컨텍스트: {context}' if context else ''}

이 에러를 분석하고 수정된 코드를 제공해주세요."""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        fix_result = response.choices[0].message.content

        return {
            "success": True,
            "original_error": error_message,
            "fix_result": fix_result,
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens
            }
        }
