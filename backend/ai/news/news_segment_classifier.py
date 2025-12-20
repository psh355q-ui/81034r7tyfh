"""
NewsSegmentClassifier - AI 반도체 뉴스 시장 세그먼트 분류기

뉴스 헤드라인/본문을 분석하여 Training vs Inference 시장으로 분류하고
해당 시장의 수혜 종목을 추천한다.

핵심 기능:
1. 뉴스 → Training/Inference/Both 분류
2. 분류 결과 → 수혜 종목 추천
3. 시장 세그먼트별 모멘텀 트래킹

사용 예시:
- "Google announces TPU v6e for inference" → Inference → GOOGL, AVGO Long
- "NVIDIA Blackwell breaks training records" → Training → NVDA Long
- "Meta builds massive AI cluster" → Both → NVDA, TSM Long

비용: $0/월 (키워드 기반 룰)
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import BaseSchema
from backend.schemas.base_schema import NewsFeatures, MarketSegment
from backend.data.knowledge.ai_value_chain import AIValueChainGraph

logger = logging.getLogger(__name__)


class NewsSegmentClassifier:
    """
    뉴스 시장 세그먼트 분류기

    Training vs Inference 시장을 구분하고 수혜 종목을 추천

    Phase 0 통합:
    - NewsFeatures 스키마 출력
    - MarketSegment Enum 사용
    """

    # Training 시장 키워드 (가중치 포함)
    TRAINING_KEYWORDS = {
        # NVIDIA Training 칩
        "h100": 1.0,
        "h200": 1.0,
        "b200": 1.0,
        "blackwell": 1.0,
        "hopper": 0.9,
        "dgx": 0.9,
        "nvlink": 0.8,

        # Training 관련 용어
        "training": 0.9,
        "pre-training": 1.0,
        "pretraining": 1.0,
        "foundation model": 0.9,
        "large language model": 0.8,
        "llm training": 1.0,
        "gpu cluster": 0.8,
        "supercomputer": 0.7,
        "exaflop": 0.8,

        # 대규모 학습 관련
        "data center build": 0.7,
        "massive compute": 0.8,
        "trillion parameter": 0.9,
    }

    # Inference 시장 키워드 (가중치 포함)
    INFERENCE_KEYWORDS = {
        # Google TPU
        "tpu": 1.0,
        "tpu v5": 1.0,
        "tpu v5p": 1.0,
        "tpu v6": 1.0,
        "tpu v6e": 1.0,

        # AMD Inference
        "mi300": 0.9,
        "mi300x": 0.9,
        "mi325": 0.9,
        "mi325x": 0.9,
        "rocm": 0.7,

        # Intel Inference
        "gaudi": 0.8,
        "gaudi 3": 0.9,

        # AWS Inference
        "inferentia": 0.9,
        "trainium": 0.8,

        # Inference 용어
        "inference": 0.9,
        "serving": 0.7,
        "deployment": 0.6,
        "edge ai": 0.8,
        "on-device": 0.7,
        "latency optimization": 0.8,
        "tokens per second": 0.8,
        "cost per token": 0.9,
    }

    # 티커 패턴
    TICKER_PATTERNS = {
        "nvidia": "NVDA",
        "nvda": "NVDA",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "googl": "GOOGL",
        "broadcom": "AVGO",
        "avgo": "AVGO",
        "amd": "AMD",
        "intel": "INTC",
        "tsmc": "TSM",
        "taiwan semiconductor": "TSM",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "aws": "AMZN",
        "meta": "META",
        "openai": None,  # Not public
        "anthropic": None,  # Not public
    }

    def __init__(self, value_chain: Optional[AIValueChainGraph] = None):
        """
        Args:
            value_chain: AIValueChainGraph 인스턴스 (수혜 분석용)
        """
        self.value_chain = value_chain or AIValueChainGraph()

    def classify(self, headline: str, body: str = "") -> NewsFeatures:
        """
        뉴스를 분류하고 NewsFeatures 스키마로 반환

        Args:
            headline: 뉴스 제목
            body: 뉴스 본문 (선택)

        Returns:
            NewsFeatures 스키마
        """
        combined_text = f"{headline} {body}".lower()

        # 키워드 매칭
        training_score, training_keywords = self._match_keywords(
            combined_text, self.TRAINING_KEYWORDS
        )
        inference_score, inference_keywords = self._match_keywords(
            combined_text, self.INFERENCE_KEYWORDS
        )

        # 세그먼트 결정
        segment, confidence = self._determine_segment(
            training_score, inference_score
        )

        # 언급된 티커 추출
        tickers_mentioned = self._extract_tickers(combined_text)

        # 모든 키워드
        all_keywords = training_keywords + inference_keywords

        return NewsFeatures(
            headline=headline,
            body=body,
            segment=segment,
            sentiment=confidence,  # 신뢰도를 sentiment로 사용
            keywords=all_keywords,
            tickers_mentioned=tickers_mentioned
        )

    def classify_legacy(self, title: str, content: str = "") -> Dict[str, Any]:
        """
        레거시 딕셔너리 형식 분류 (하위 호환성)

        Returns:
            분류 결과 딕셔너리
        """
        combined_text = f"{title} {content}".lower()

        # 키워드 매칭
        training_score, training_keywords = self._match_keywords(
            combined_text, self.TRAINING_KEYWORDS
        )
        inference_score, inference_keywords = self._match_keywords(
            combined_text, self.INFERENCE_KEYWORDS
        )

        # 세그먼트 결정
        segment, confidence = self._determine_segment(
            training_score, inference_score
        )

        # 언급된 티커 추출
        tickers_mentioned = self._extract_tickers(combined_text)

        # 수혜 종목 분석
        beneficiaries = self._analyze_beneficiaries(
            segment, tickers_mentioned
        )

        # 투자 시그널 생성
        investment_signal = self._generate_signal(
            segment, beneficiaries, confidence
        )

        return {
            "title": title,
            "segment": segment.value,
            "confidence": confidence,
            "matched_keywords": training_keywords + inference_keywords,
            "tickers_mentioned": tickers_mentioned,
            "beneficiaries": beneficiaries,
            "investment_signal": investment_signal,
            "classified_at": datetime.now().isoformat()
        }

    def _match_keywords(
        self,
        text: str,
        keywords: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """
        키워드 매칭 및 점수 계산

        Returns:
            (총 점수, 매칭된 키워드 리스트)
        """
        score = 0.0
        matched = []

        for keyword, weight in keywords.items():
            if keyword in text:
                score += weight
                matched.append(keyword)

        return score, matched

    def _determine_segment(
        self,
        training_score: float,
        inference_score: float
    ) -> Tuple[MarketSegment, float]:
        """
        점수 기반 세그먼트 결정

        Returns:
            (세그먼트, 신뢰도)
        """
        total = training_score + inference_score

        if total == 0:
            return MarketSegment.TRAINING, 0.3  # 기본값, 낮은 신뢰도

        training_ratio = training_score / total
        inference_ratio = inference_score / total

        # 70% 이상 한 쪽으로 기울면 해당 세그먼트
        if training_ratio >= 0.7:
            confidence = min(0.5 + training_score * 0.1, 0.95)
            return MarketSegment.TRAINING, confidence
        elif inference_ratio >= 0.7:
            confidence = min(0.5 + inference_score * 0.1, 0.95)
            return MarketSegment.INFERENCE, confidence
        else:
            # 혼합 - Training을 기본으로
            confidence = min(0.4 + total * 0.05, 0.8)
            return MarketSegment.TRAINING, confidence

    def _extract_tickers(self, text: str) -> List[str]:
        """텍스트에서 언급된 티커 추출"""
        tickers = []

        for pattern, ticker in self.TICKER_PATTERNS.items():
            if pattern in text and ticker and ticker not in tickers:
                tickers.append(ticker)

        return tickers

    def _analyze_beneficiaries(
        self,
        segment: MarketSegment,
        tickers_mentioned: List[str]
    ) -> List[str]:
        """세그먼트 기반 수혜 종목 분석"""
        beneficiaries = list(tickers_mentioned)  # 언급된 종목은 일단 포함

        # 세그먼트별 기본 수혜 종목 추가
        if segment == MarketSegment.TRAINING:
            default_beneficiaries = ["NVDA", "TSM"]
        elif segment == MarketSegment.INFERENCE:
            default_beneficiaries = ["GOOGL", "AVGO", "AMD"]
        else:  # 기본
            default_beneficiaries = ["NVDA", "TSM", "GOOGL"]

        for ticker in default_beneficiaries:
            if ticker not in beneficiaries:
                beneficiaries.append(ticker)

        # Value Chain에서 간접 수혜자 추가
        for ticker in tickers_mentioned:
            result = self.value_chain.find_beneficiaries(ticker, "positive")
            for indirect in result.get("indirect_beneficiaries", []):
                if indirect not in beneficiaries:
                    beneficiaries.append(indirect)

        return beneficiaries

    def _generate_signal(
        self,
        segment: MarketSegment,
        beneficiaries: List[str],
        confidence: float
    ) -> Dict[str, Any]:
        """투자 시그널 생성"""

        # 세그먼트별 기본 포지션
        if segment == MarketSegment.TRAINING:
            long_priority = ["NVDA", "TSM"]
            hold_priority = ["AMD", "INTC"]
            rationale = "Training market momentum favors NVIDIA ecosystem"
        elif segment == MarketSegment.INFERENCE:
            long_priority = ["GOOGL", "AVGO"]
            hold_priority = ["NVDA", "AMD"]
            rationale = "Inference market growth benefits TPU and custom silicon"
        else:
            long_priority = ["NVDA", "TSM", "GOOGL"]
            hold_priority = ["AMD", "AVGO"]
            rationale = "Broad AI infrastructure demand benefits multiple players"

        # 수혜 종목과 교차
        long_tickers = [t for t in long_priority if t in beneficiaries]
        # 수혜 종목 중 long_priority에 없는 것도 추가
        for t in beneficiaries:
            if t not in long_tickers and t not in hold_priority:
                long_tickers.append(t)

        hold_tickers = [t for t in hold_priority if t not in long_tickers]

        return {
            "segment": segment.value,
            "long": long_tickers[:5],  # 최대 5개
            "hold": hold_tickers[:3],
            "avoid": [],  # 이 분류에서는 avoid 없음
            "rationale": rationale,
            "confidence": confidence,
            "signal_strength": "STRONG" if confidence >= 0.7 else "MODERATE" if confidence >= 0.5 else "WEAK"
        }

    def get_segment_momentum(
        self,
        news_features_list: List[NewsFeatures]
    ) -> Dict[str, Any]:
        """
        뉴스 분류 결과에서 세그먼트별 모멘텀 분석

        Args:
            news_features_list: NewsFeatures 리스트

        Returns:
            {
                "training_momentum": 0.65,
                "inference_momentum": 0.35,
                "dominant_segment": "training",
                "signal": "Overweight Training (NVDA, TSM)"
            }
        """
        if not news_features_list:
            return {
                "training_momentum": 0.5,
                "inference_momentum": 0.5,
                "dominant_segment": "balanced",
                "signal": "Balanced exposure recommended"
            }

        training_count = sum(
            1 for nf in news_features_list
            if nf.segment == MarketSegment.TRAINING
        )
        inference_count = sum(
            1 for nf in news_features_list
            if nf.segment == MarketSegment.INFERENCE
        )

        total = len(news_features_list)

        training_momentum = training_count / total
        inference_momentum = inference_count / total

        if training_momentum > inference_momentum + 0.2:
            dominant = "training"
            signal = "Overweight Training (NVDA, TSM)"
        elif inference_momentum > training_momentum + 0.2:
            dominant = "inference"
            signal = "Overweight Inference (GOOGL, AVGO)"
        else:
            dominant = "balanced"
            signal = "Balanced exposure (NVDA, GOOGL, TSM)"

        return {
            "training_momentum": round(training_momentum, 2),
            "inference_momentum": round(inference_momentum, 2),
            "dominant_segment": dominant,
            "signal": signal,
            "news_count": {
                "training": training_count,
                "inference": inference_count
            }
        }


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    classifier = NewsSegmentClassifier()

    print("=" * 70)
    print("News Segment Classifier Demo")
    print("=" * 70)

    # 테스트 뉴스
    test_news = [
        {
            "title": "Google announces TPU v6e for inference workloads",
            "content": "The new TPU v6e offers 50% better cost per token compared to previous generation"
        },
        {
            "title": "NVIDIA Blackwell B200 breaks training performance records",
            "content": "The B200 GPU cluster trained a trillion parameter model in record time"
        },
        {
            "title": "Meta builds massive AI data center with 100,000 GPUs",
            "content": "Meta's new supercomputer will use both NVIDIA H200 and custom inference chips"
        },
        {
            "title": "AMD MI325X gains traction in inference market",
            "content": "AMD's latest GPU offers competitive tokens per second at lower cost"
        },
        {
            "title": "TSMC expands CoWoS capacity for AI chip demand",
            "content": "Advanced packaging capacity will increase 2x to meet NVIDIA and AMD orders"
        }
    ]

    # 개별 분류 (BaseSchema)
    print("\n### News Classification (BaseSchema) ###")
    news_features_list = []

    for news in test_news:
        result = classifier.classify(news["title"], news["content"])
        news_features_list.append(result)

        print(f"\nHeadline: {result.headline}")
        print(f"  Segment: {result.segment}")
        print(f"  Confidence: {result.sentiment:.0%}")
        print(f"  Keywords: {', '.join(result.keywords[:5])}")
        print(f"  Tickers: {', '.join(result.tickers_mentioned)}")

    # 모멘텀 분석
    print("\n### Segment Momentum Analysis ###")
    momentum = classifier.get_segment_momentum(news_features_list)

    print(f"\nTraining Momentum: {momentum['training_momentum']:.0%}")
    print(f"Inference Momentum: {momentum['inference_momentum']:.0%}")
    print(f"Dominant: {momentum['dominant_segment']}")
    print(f"Signal: {momentum['signal']}")
    print(f"News Count: Training={momentum['news_count']['training']}, "
          f"Inference={momentum['news_count']['inference']}")
