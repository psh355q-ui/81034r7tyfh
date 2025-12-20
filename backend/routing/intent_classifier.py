"""
Intent Classifier

사용자 입력에서 의도(Intent)를 분류하는 모듈

Stage 1 of Semantic Router:
- 규칙 기반 패턴 매칭 (무료, 빠름)
- Local LLM 지원 (선택적)

Author: AI Trading System
Date: 2025-12-04
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """지원하는 Intent 목록"""

    NEWS_ANALYSIS = "news_analysis"          # 뉴스/기사 분석
    TRADING_EXECUTION = "trading_execution"  # 매매 실행
    STRATEGY_GENERATION = "strategy_generation"  # 전략 생성/백테스트
    MARKET_RESEARCH = "market_research"      # 시장/기업 조사
    PORTFOLIO_MANAGEMENT = "portfolio_management"  # 포트폴리오 관리
    DATA_QUERY = "data_query"                # 데이터 조회
    GENERAL_QUERY = "general_query"          # 일반 질문


class IntentClassifier:
    """
    규칙 기반 Intent 분류기

    패턴 매칭을 사용하여 사용자 입력의 의도를 빠르게 분류

    Usage:
        classifier = IntentClassifier()
        intent, confidence = classifier.classify("삼성전자 뉴스 분석해줘")
        # intent: Intent.NEWS_ANALYSIS, confidence: 0.9
    """

    # Intent별 패턴 정의
    INTENT_PATTERNS: Dict[Intent, List[str]] = {
        Intent.NEWS_ANALYSIS: [
            r"뉴스.*분석",
            r"기사.*분석",
            r"최근.*소식",
            r"언론.*보도",
            r"what.*news",
            r"analyze.*article",
            r"analyze.*news",
            r"news.*about",
            r"뉴스.*검색",
            r"기사.*검색",
        ],
        Intent.TRADING_EXECUTION: [
            r"매수|매도",
            r"주문.*실행",
            r"거래.*실행",
            r"사|팔",
            r"buy|sell",
            r"execute.*order",
            r"place.*order",
            r"주문.*넣",
            r"매매.*실행",
        ],
        Intent.STRATEGY_GENERATION: [
            r"전략.*생성",
            r"전략.*만들",
            r"백테스트",
            r"backtest",
            r"strategy.*generat",
            r"create.*strategy",
            r"전략.*개발",
            r"알고리즘.*트레이딩",
        ],
        Intent.MARKET_RESEARCH: [
            r"시장.*조사",
            r"시장.*분석",
            r"경쟁사.*분석",
            r"섹터.*분석",
            r"산업.*분석",
            r"market.*research",
            r"market.*analysis",
            r"competitor.*analysis",
            r"공시.*확인",
            r"재무제표",
        ],
        Intent.PORTFOLIO_MANAGEMENT: [
            r"포트폴리오",
            r"자산.*배분",
            r"리밸런싱",
            r"portfolio",
            r"asset.*allocation",
            r"rebalanc",
            r"계좌.*조회",
            r"잔고.*확인",
        ],
        Intent.DATA_QUERY: [
            r"현재가",
            r"주가.*조회",
            r"시세.*확인",
            r"price.*check",
            r"stock.*price",
            r"얼마",
            r"데이터.*조회",
            r"차트.*보",
        ],
    }

    # Intent별 키워드 (추가 매칭용)
    INTENT_KEYWORDS: Dict[Intent, List[str]] = {
        Intent.NEWS_ANALYSIS: ["뉴스", "기사", "언론", "news", "article"],
        Intent.TRADING_EXECUTION: ["매수", "매도", "주문", "buy", "sell", "order"],
        Intent.STRATEGY_GENERATION: ["전략", "백테스트", "strategy", "backtest"],
        Intent.MARKET_RESEARCH: ["시장", "조사", "분석", "market", "research", "공시"],
        Intent.PORTFOLIO_MANAGEMENT: ["포트폴리오", "portfolio", "계좌", "account"],
        Intent.DATA_QUERY: ["현재가", "주가", "시세", "price", "얼마"],
    }

    def __init__(self):
        """초기화"""
        logger.info("IntentClassifier initialized (rule-based)")

    def classify(self, user_input: str) -> Tuple[Intent, float]:
        """
        사용자 입력에서 Intent 분류

        Args:
            user_input: 사용자 입력 텍스트

        Returns:
            (intent, confidence): 분류된 Intent와 신뢰도 (0-1)
        """
        if not user_input or not user_input.strip():
            return Intent.GENERAL_QUERY, 0.0

        user_lower = user_input.lower()

        # 1단계: 패턴 매칭
        pattern_scores: Dict[Intent, float] = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, user_lower):
                    score += 1.0

            if score > 0:
                # 패턴 매칭 점수 정규화 (0-1)
                pattern_scores[intent] = min(score / len(patterns), 1.0)

        # 2단계: 키워드 매칭 (보조)
        keyword_scores: Dict[Intent, float] = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in user_lower)
            if count > 0:
                keyword_scores[intent] = count / len(keywords)

        # 3단계: 점수 결합 (패턴 70%, 키워드 30%)
        final_scores: Dict[Intent, float] = {}

        for intent in Intent:
            if intent == Intent.GENERAL_QUERY:
                continue

            pattern_score = pattern_scores.get(intent, 0.0)
            keyword_score = keyword_scores.get(intent, 0.0)

            # 가중 평균
            final_score = pattern_score * 0.7 + keyword_score * 0.3
            if final_score > 0:
                final_scores[intent] = final_score

        # 4단계: 최고 점수 Intent 선택
        if final_scores:
            best_intent = max(final_scores.items(), key=lambda x: x[1])
            intent, confidence = best_intent

            logger.debug(
                f"Intent classified: {intent.value} (confidence={confidence:.2f}, "
                f"input=\"{user_input[:50]}...\")"
            )

            return intent, confidence
        else:
            # 매칭 실패 시 일반 질문
            logger.debug(f"No intent matched, using GENERAL_QUERY: \"{user_input[:50]}...\"")
            return Intent.GENERAL_QUERY, 0.3

    def classify_batch(self, inputs: List[str]) -> List[Tuple[Intent, float]]:
        """여러 입력을 배치로 분류"""
        return [self.classify(inp) for inp in inputs]

    def get_intent_info(self, intent: Intent) -> Dict[str, any]:
        """Intent 정보 조회"""
        return {
            "intent": intent.value,
            "patterns": self.INTENT_PATTERNS.get(intent, []),
            "keywords": self.INTENT_KEYWORDS.get(intent, []),
        }


# ============================================================================
# Local LLM Intent Classifier (선택적)
# ============================================================================

class LocalLLMIntentClassifier:
    """
    로컬 LLM 기반 Intent 분류

    Ollama를 사용한 고급 Intent 분류
    (규칙 기반보다 정확하지만 응답 시간 증가)

    Requirements:
        - Ollama 설치 및 실행
        - 모델: llama3.2:3b 또는 phi-3-mini
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Args:
            ollama_url: Ollama API URL
            model: 사용할 모델 (llama3.2:3b, phi-3-mini 등)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.available = self._check_availability()

        if self.available:
            logger.info(f"LocalLLMIntentClassifier initialized (model={model})")
        else:
            logger.warning(f"Ollama not available at {ollama_url}, falling back to rule-based")

    def _check_availability(self) -> bool:
        """Ollama 서버 사용 가능 여부 확인"""
        try:
            import httpx
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    async def classify(self, user_input: str) -> Tuple[Intent, float]:
        """
        로컬 LLM으로 Intent 분류

        Args:
            user_input: 사용자 입력

        Returns:
            (intent, confidence)
        """
        if not self.available:
            # Fallback to rule-based
            fallback = IntentClassifier()
            return fallback.classify(user_input)

        import httpx

        # Prompt 구성
        prompt = self._build_prompt(user_input)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # 낮은 온도로 일관성 확보
                            "num_predict": 50,
                        }
                    },
                    timeout=10.0
                )

            result = response.json()
            intent_str = result.get("response", "").strip().lower()

            # Intent 파싱
            intent, confidence = self._parse_llm_response(intent_str)

            logger.debug(
                f"LLM Intent classified: {intent.value} (confidence={confidence:.2f})"
            )

            return intent, confidence

        except Exception as e:
            logger.error(f"LLM classification error: {e}, falling back to rule-based")
            fallback = IntentClassifier()
            return fallback.classify(user_input)

    def _build_prompt(self, user_input: str) -> str:
        """LLM용 프롬프트 생성"""
        return f"""Classify the user's intent into ONE category.

Categories:
- news_analysis: Analyzing news or articles
- trading_execution: Executing trades (buy/sell orders)
- strategy_generation: Creating or backtesting trading strategies
- market_research: Researching markets, companies, or sectors
- portfolio_management: Managing portfolios or checking accounts
- data_query: Querying stock prices or market data
- general_query: Other general questions

User input: "{user_input}"

Respond with ONLY the category name (one word, lowercase).
Category:"""

    def _parse_llm_response(self, response: str) -> Tuple[Intent, float]:
        """LLM 응답 파싱"""
        # Intent 목록
        valid_intents = {
            "news_analysis": Intent.NEWS_ANALYSIS,
            "trading_execution": Intent.TRADING_EXECUTION,
            "strategy_generation": Intent.STRATEGY_GENERATION,
            "market_research": Intent.MARKET_RESEARCH,
            "portfolio_management": Intent.PORTFOLIO_MANAGEMENT,
            "data_query": Intent.DATA_QUERY,
            "general_query": Intent.GENERAL_QUERY,
        }

        # 응답에서 Intent 추출
        for intent_str, intent_enum in valid_intents.items():
            if intent_str in response:
                # LLM은 일반적으로 높은 신뢰도
                return intent_enum, 0.85

        # 파싱 실패 시 기본값
        return Intent.GENERAL_QUERY, 0.3


# ============================================================================
# Factory Function
# ============================================================================

def create_intent_classifier(use_local_llm: bool = False) -> IntentClassifier | LocalLLMIntentClassifier:
    """
    Intent Classifier 생성 (Factory)

    Args:
        use_local_llm: Local LLM 사용 여부

    Returns:
        IntentClassifier 인스턴스
    """
    if use_local_llm:
        return LocalLLMIntentClassifier()
    else:
        return IntentClassifier()
