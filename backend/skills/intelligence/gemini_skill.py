"""
Gemini Intelligence Skill

Google Gemini를 활용한 AI 분석

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class GeminiSkill(BaseSkill):
    """
    Gemini AI Skill

    기능:
    - 뉴스 감성 분석
    - 리스크 스크리닝
    - 텍스트 요약
    - Q&A

    Usage:
        skill = GeminiSkill()
        tools = skill.get_tools()
        result = await skill.execute("analyze_sentiment", text="...")
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="Intelligence.Gemini",
            category=SkillCategory.INTELLIGENCE,
            description="Gemini AI를 활용한 뉴스 분석, 감성 분석, 리스크 스크리닝",
            keywords=[
                "AI", "분석", "analysis", "sentiment", "감성분석",
                "뉴스분석", "news analysis", "리스크", "risk", "Gemini"
            ],
            cost_tier=CostTier.LOW,  # Gemini Flash는 저렴
            requires_api_key=True,
            rate_limit_per_min=60,  # Gemini 무료 티어
        )

        # Gemini 클라이언트 초기화 (지연 로딩)
        self._gemini_client = None

    def _get_gemini_client(self):
        """Gemini 클라이언트 가져오기 (지연 로딩)"""
        if self._gemini_client is None:
            try:
                from backend.ai.gemini_client import GeminiClient
                self._gemini_client = GeminiClient()
                logger.info("Gemini client initialized")
            except ImportError:
                logger.error("Failed to import GeminiClient")
                raise

        return self._gemini_client

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Gemini Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_sentiment",
                    "description": "텍스트의 감성(긍정/부정/중립) 분석",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "분석할 텍스트 (뉴스 기사, 리포트 등)"
                            },
                            "context": {
                                "type": "string",
                                "description": "추가 컨텍스트 (선택)"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "screen_risk",
                    "description": "뉴스/텍스트에서 투자 리스크 요인 스크리닝",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "분석할 텍스트"
                            },
                            "ticker": {
                                "type": "string",
                                "description": "관련 종목 티커 (선택)"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_text",
                    "description": "긴 텍스트를 요약",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "요약할 텍스트"
                            },
                            "max_sentences": {
                                "type": "integer",
                                "description": "최대 문장 수 (기본값: 3)",
                                "default": 3
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "answer_question",
                    "description": "텍스트 기반 Q&A",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "질문"
                            },
                            "context": {
                                "type": "string",
                                "description": "컨텍스트 (문서, 뉴스 등)"
                            }
                        },
                        "required": ["question", "context"]
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
        """
        try:
            if tool_name == "analyze_sentiment":
                result = await self._analyze_sentiment(**kwargs)
            elif tool_name == "screen_risk":
                result = await self._screen_risk(**kwargs)
            elif tool_name == "summarize_text":
                result = await self._summarize_text(**kwargs)
            elif tool_name == "answer_question":
                result = await self._answer_question(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트 (Gemini Flash 비용 추정)
            cost = self._estimate_gemini_cost(result)
            self._track_call(success=True, cost_usd=cost)

            return result

        except Exception as e:
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _analyze_sentiment(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        감성 분석

        Args:
            text: 분석할 텍스트
            context: 추가 컨텍스트

        Returns:
            감성 분석 결과
        """
        gemini = self._get_gemini_client()

        prompt = f"""다음 텍스트의 감성을 분석하세요.

텍스트:
{text}

{f'컨텍스트: {context}' if context else ''}

다음 형식으로 응답하세요:
- 감성: POSITIVE/NEGATIVE/NEUTRAL
- 신뢰도: 0-1 (숫자)
- 이유: 한 문장으로 설명
"""

        response = await gemini.generate_text(prompt)

        # 응답 파싱 (간단한 구현)
        sentiment = "NEUTRAL"
        confidence = 0.5
        reason = response

        if "POSITIVE" in response.upper():
            sentiment = "POSITIVE"
            confidence = 0.8
        elif "NEGATIVE" in response.upper():
            sentiment = "NEGATIVE"
            confidence = 0.8

        return {
            "success": True,
            "sentiment": sentiment,
            "confidence": confidence,
            "reason": reason[:200],  # 200자로 제한
            "tokens_used": len(text) + len(response),
        }

    async def _screen_risk(
        self,
        text: str,
        ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        리스크 스크리닝

        Args:
            text: 분석할 텍스트
            ticker: 종목 티커

        Returns:
            리스크 평가 결과
        """
        gemini = self._get_gemini_client()

        prompt = f"""다음 텍스트에서 투자 리스크 요인을 스크리닝하세요.

{f'종목: {ticker}' if ticker else ''}

텍스트:
{text}

다음 항목을 평가하세요:
- 리스크 레벨: LOW/MEDIUM/HIGH/CRITICAL
- 리스크 카테고리: LEGAL, REGULATORY, OPERATIONAL, FINANCIAL, MARKET
- 심각도 점수: 0-1 (숫자)
- 주요 리스크 요인: 간단히 설명
"""

        response = await gemini.generate_text(prompt)

        # 응답 파싱
        risk_level = "MEDIUM"
        risk_score = 0.5

        if "CRITICAL" in response.upper():
            risk_level = "CRITICAL"
            risk_score = 0.9
        elif "HIGH" in response.upper():
            risk_level = "HIGH"
            risk_score = 0.7
        elif "LOW" in response.upper():
            risk_level = "LOW"
            risk_score = 0.2

        return {
            "success": True,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "analysis": response[:300],
            "ticker": ticker,
            "tokens_used": len(text) + len(response),
        }

    async def _summarize_text(
        self,
        text: str,
        max_sentences: int = 3
    ) -> Dict[str, Any]:
        """
        텍스트 요약

        Args:
            text: 요약할 텍스트
            max_sentences: 최대 문장 수

        Returns:
            요약 결과
        """
        gemini = self._get_gemini_client()

        prompt = f"""다음 텍스트를 {max_sentences}문장 이내로 요약하세요.

텍스트:
{text}

요약:
"""

        response = await gemini.generate_text(prompt)

        return {
            "success": True,
            "summary": response.strip(),
            "original_length": len(text),
            "summary_length": len(response),
            "compression_ratio": len(response) / len(text) if len(text) > 0 else 0,
            "tokens_used": len(text) + len(response),
        }

    async def _answer_question(
        self,
        question: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Q&A

        Args:
            question: 질문
            context: 컨텍스트

        Returns:
            답변
        """
        gemini = self._get_gemini_client()

        prompt = f"""다음 컨텍스트를 바탕으로 질문에 답하세요.

컨텍스트:
{context}

질문: {question}

답변:
"""

        response = await gemini.generate_text(prompt)

        return {
            "success": True,
            "question": question,
            "answer": response.strip(),
            "tokens_used": len(question) + len(context) + len(response),
        }

    def _estimate_gemini_cost(self, result: Dict) -> float:
        """
        Gemini 비용 추정

        Args:
            result: 실행 결과

        Returns:
            비용 (USD)
        """
        # Gemini Flash 가격: $0.075 / 1M input tokens, $0.30 / 1M output tokens
        tokens_used = result.get("tokens_used", 0)

        # 간단히: 입력/출력 비율 50:50 가정
        input_tokens = tokens_used * 0.5
        output_tokens = tokens_used * 0.5

        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30

        return input_cost + output_cost
