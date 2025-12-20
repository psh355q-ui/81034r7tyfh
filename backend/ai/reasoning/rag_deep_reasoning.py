"""
RAG + Deep Reasoning Integration (Phase 15)
============================================

SEC 문서 검색 + 3-Step CoT 추론 결합

워크플로우:
1. 사용자 쿼리: "Microsoft's AI strategy - hidden beneficiaries?"
2. RAG 검색: Microsoft SEC filings + 최근 뉴스
3. Context 구축: CEO 발언, 파트너십 정보 추출
4. Deep Reasoning: 3-step CoT로 숨은 수혜자 발굴
5. Knowledge Graph: 기업 관계 검증

예시:
    Input: "Microsoft mentions Nvidia 50 times in 10-K"
    → RAG finds: Microsoft-OpenAI partnership, $13B investment
    → Deep Reasoning: OpenAI uses Nvidia GPUs
    → Hidden Beneficiary: NVDA (Microsoft's capex → OpenAI → Nvidia demand)
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from backend.ai.reasoning.deep_reasoning import (
    DeepReasoningStrategy,
    DeepReasoningResult
)
from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph


@dataclass
class RAGDeepReasoningResult:
    """RAG + Deep Reasoning 결과"""
    # Deep Reasoning 결과
    reasoning_result: DeepReasoningResult

    # RAG 컨텍스트
    rag_sources: List[Dict]  # SEC filings, news articles
    ceo_quotes: List[str]    # CEO 발언
    partnership_info: List[Dict]  # 파트너십 정보

    # Knowledge Graph
    verified_relationships: List[Dict]  # 검증된 기업 관계
    confidence_boost: float  # RAG로 인한 신뢰도 증가


class RAGDeepReasoningStrategy:
    """
    RAG + Deep Reasoning 통합 전략

    SEC 문서에서 추출한 정보를 Deep Reasoning에 주입하여
    더 정확한 숨은 수혜자 발굴
    """

    def __init__(self):
        self.deep_reasoning = DeepReasoningStrategy()
        self.knowledge_graph = KnowledgeGraph()

    async def analyze_with_rag(
        self,
        ticker: str,
        user_query: str,
        rag_context: Optional[str] = None
    ) -> RAGDeepReasoningResult:
        """
        RAG 컨텍스트를 활용한 심층 추론

        Args:
            ticker: 분석 대상 티커
            user_query: 사용자 질문
            rag_context: RAG로 검색된 문서들 (SEC filings, news)

        Returns:
            RAGDeepReasoningResult: RAG + Deep Reasoning 결과
        """

        # 1. RAG 컨텍스트에서 핵심 정보 추출
        ceo_quotes = self._extract_ceo_quotes(rag_context or "")
        partnership_info = self._extract_partnerships(rag_context or "")

        # 2. Enhanced news text 생성 (RAG context 포함)
        enhanced_news = self._build_enhanced_news(
            ticker=ticker,
            user_query=user_query,
            ceo_quotes=ceo_quotes,
            partnership_info=partnership_info,
            rag_context=rag_context
        )

        # 3. Deep Reasoning 실행
        reasoning_result = await self.deep_reasoning.analyze_news(enhanced_news)

        # 4. Knowledge Graph로 관계 검증
        verified_relationships = await self._verify_with_knowledge_graph(
            reasoning_result
        )

        # 5. RAG로 인한 신뢰도 증가 계산
        confidence_boost = self._calculate_confidence_boost(
            rag_sources=len(partnership_info),
            verified_relationships=len(verified_relationships)
        )

        return RAGDeepReasoningResult(
            reasoning_result=reasoning_result,
            rag_sources=[],  # TODO: RAG 소스 추적
            ceo_quotes=ceo_quotes,
            partnership_info=partnership_info,
            verified_relationships=verified_relationships,
            confidence_boost=confidence_boost
        )

    def _extract_ceo_quotes(self, rag_context: str) -> List[str]:
        """CEO 발언 추출"""
        # 간단한 패턴 매칭 (실제로는 NER 사용)
        quotes = []
        lines = rag_context.split('\n')

        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'ceo said', 'ceo stated', 'ceo mentioned',
                'chief executive', 'ceo', 'chairman'
            ]):
                quotes.append(line.strip())

        return quotes[:5]  # Top 5 quotes

    def _extract_partnerships(self, rag_context: str) -> List[Dict]:
        """파트너십 정보 추출"""
        partnerships = []
        lines = rag_context.split('\n')

        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'partnership', 'collaboration', 'joint venture',
                'strategic alliance', 'investment in'
            ]):
                partnerships.append({
                    'text': line.strip(),
                    'type': 'partnership'
                })

        return partnerships[:10]

    def _build_enhanced_news(
        self,
        ticker: str,
        user_query: str,
        ceo_quotes: List[str],
        partnership_info: List[Dict],
        rag_context: Optional[str]
    ) -> str:
        """
        RAG 컨텍스트로 강화된 뉴스 텍스트 생성
        """
        enhanced = f"Analysis Request: {user_query}\n\n"
        enhanced += f"Company: {ticker}\n"
        enhanced += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"

        if ceo_quotes:
            enhanced += "=== CEO Statements ===\n"
            for quote in ceo_quotes:
                enhanced += f"- {quote}\n"
            enhanced += "\n"

        if partnership_info:
            enhanced += "=== Strategic Partnerships ===\n"
            for info in partnership_info:
                enhanced += f"- {info['text']}\n"
            enhanced += "\n"

        if rag_context:
            # 컨텍스트 요약 (너무 길면 잘라냄)
            context_summary = rag_context[:1000]
            enhanced += f"=== Recent Context ===\n{context_summary}\n\n"

        return enhanced

    async def _verify_with_knowledge_graph(
        self,
        reasoning_result: DeepReasoningResult
    ) -> List[Dict]:
        """
        Knowledge Graph로 발견된 관계 검증
        """
        verified = []

        # Primary beneficiary 검증
        if reasoning_result.primary_beneficiary:
            ticker = reasoning_result.primary_beneficiary.get('ticker')
            if ticker:
                relations = await self.knowledge_graph.get_relationships(ticker)
                verified.extend(relations[:3])

        # Hidden beneficiary 검증
        if reasoning_result.hidden_beneficiary:
            ticker = reasoning_result.hidden_beneficiary.get('ticker')
            if ticker:
                relations = await self.knowledge_graph.get_relationships(ticker)
                verified.extend(relations[:3])

        return verified

    def _calculate_confidence_boost(
        self,
        rag_sources: int,
        verified_relationships: int
    ) -> float:
        """
        RAG와 Knowledge Graph 검증으로 인한 신뢰도 증가

        - RAG 소스 많을수록: +0.05 per source (max +0.15)
        - 검증된 관계 많을수록: +0.03 per relation (max +0.15)
        """
        rag_boost = min(rag_sources * 0.05, 0.15)
        kg_boost = min(verified_relationships * 0.03, 0.15)

        return rag_boost + kg_boost


# ============================================
# Demo & Testing
# ============================================

async def demo():
    """RAG + Deep Reasoning 데모"""
    print("=" * 80)
    print("Phase 15: RAG + Deep Reasoning Demo")
    print("=" * 80)

    strategy = RAGDeepReasoningStrategy()

    # Mock RAG context (실제로는 vector search 결과)
    mock_rag_context = """
    Microsoft CEO Satya Nadella said: "Our partnership with OpenAI represents
    the most significant strategic investment in AI infrastructure."

    SEC Filing 10-K: Microsoft invested $13 billion in OpenAI over multiple rounds.
    The partnership includes exclusive cloud computing arrangements on Azure.

    Recent News: OpenAI's GPT-4 training required over 25,000 Nvidia A100 GPUs.
    Microsoft Azure provides the compute infrastructure for all OpenAI workloads.

    Strategic Alliance: Microsoft and Nvidia announced joint AI platform development,
    with Microsoft committing to purchase $5B worth of Nvidia H100 GPUs for Azure.
    """

    result = await strategy.analyze_with_rag(
        ticker="MSFT",
        user_query="What are the hidden beneficiaries of Microsoft's AI strategy?",
        rag_context=mock_rag_context
    )

    print("\n=== Analysis Result ===")
    print(f"Theme: {result.reasoning_result.theme}")

    if result.reasoning_result.hidden_beneficiary:
        hb = result.reasoning_result.hidden_beneficiary
        print(f"\nHidden Beneficiary: {hb.get('ticker', 'N/A')}")
        print(f"  Action: {hb.get('action', 'N/A')}")
        print(f"  Confidence: {hb.get('confidence', 0):.0%}")
        print(f"  Confidence Boost from RAG: +{result.confidence_boost:.1%}")

    print(f"\n=== RAG Context ===")
    print(f"CEO Quotes Found: {len(result.ceo_quotes)}")
    for quote in result.ceo_quotes[:2]:
        print(f"  - {quote[:80]}...")

    print(f"\nPartnership Info: {len(result.partnership_info)}")
    for info in result.partnership_info[:2]:
        print(f"  - {info['text'][:80]}...")

    print(f"\n=== Knowledge Graph Verification ===")
    print(f"Verified Relationships: {len(result.verified_relationships)}")
    for rel in result.verified_relationships[:3]:
        print(f"  - {rel.get('subject', 'N/A')} -> {rel.get('object', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(demo())
