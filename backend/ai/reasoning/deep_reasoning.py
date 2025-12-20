"""
Deep Reasoning Strategy (Phase 14)
===================================

"꼬리에 꼬리를 무는" 3단계 심층 추론 전략

핵심 기능:
1. Step 1: Direct Impact - 뉴스의 직접 영향 분석
2. Step 2: Secondary Impact - 파트너/경쟁사 파생 효과 (꼬리 물기)
3. Step 3: Strategic Conclusion - Bull/Bear 시나리오 + Hidden Beneficiary

차별점:
- 단순 뉴스 분석: "TPU 출시 → Google 호재" (1차원)
- Deep Reasoning: "TPU → Nvidia 의존↓ → Broadcom 설계 수혜 → AVGO 매수" (다차원)

사용 예시:
    strategy = DeepReasoningStrategy()
    result = await strategy.analyze_news(
        "Google announced Gemini 3 trained entirely on TPUs"
    )
    print(result['hidden_beneficiary'])  # {'ticker': 'AVGO', 'action': 'BUY'}
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# 프로젝트 모듈
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config_phase14 import (
    settings, get_model_config, AIRole, SEED_KNOWLEDGE
)
from backend.ai.ai_client_factory import AIClientFactory, BaseAIClient
from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph


@dataclass
class ReasoningStep:
    """추론 단계 결과"""
    step_name: str
    input_context: str
    reasoning: str
    entities_identified: List[str] = field(default_factory=list)
    relationships_found: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DeepReasoningResult:
    """심층 추론 최종 결과"""
    # 메타데이터
    news_text: str
    analyzed_at: datetime
    model_used: str
    
    # 추론 단계
    step1_direct: ReasoningStep
    step2_secondary: ReasoningStep
    step3_strategy: ReasoningStep
    
    # 최종 결론
    theme: str
    primary_beneficiary: Dict  # {"ticker": "GOOGL", "action": "BUY", "confidence": 0.85}
    hidden_beneficiary: Optional[Dict] = None  # 숨은 수혜자
    loser: Optional[Dict] = None  # 피해자
    
    # Bull/Bear 시나리오
    bull_case: str = ""
    bear_case: str = ""
    
    # 추론 흔적
    reasoning_trace: List[str] = field(default_factory=list)
    verified_relationships: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['analyzed_at'] = self.analyzed_at.isoformat()
        return result
    
    def get_action_items(self) -> List[Dict]:
        """실행 가능한 액션 리스트"""
        actions = []
        if self.primary_beneficiary:
            actions.append(self.primary_beneficiary)
        if self.hidden_beneficiary:
            actions.append(self.hidden_beneficiary)
        if self.loser:
            actions.append(self.loser)
        return actions


class DeepReasoningStrategy:
    """
    Deep Reasoning Strategy
    
    "구글 TPU 발표" 뉴스를 보고:
    1. 직접 영향: Google 호재
    2. 파생 효과: Nvidia 의존도 감소 → Nvidia 장기 악재
    3. 숨은 수혜자: Broadcom (TPU 설계 파트너) → 진짜 수혜자!
    
    이런 다단계 추론을 수행합니다.
    """
    
    def __init__(
        self,
        ai_client: Optional[BaseAIClient] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None
    ):
        # 설정된 AI 모델 로드 (하드코딩 제거)
        self.settings = settings
        
        if ai_client:
            self.ai_client = ai_client
        else:
            config = get_model_config(AIRole.REASONING)
            self.ai_client = AIClientFactory.create(
                config["model"],
                config["provider"].value
            )
        
        self.model_name = self.ai_client.model_name
        
        # Knowledge Graph
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        
        # 캐시
        self._reasoning_cache: Dict[str, DeepReasoningResult] = {}
        
        # 통계
        self.analysis_count = 0
        self.total_tokens = 0
        
        print(f"DeepReasoningStrategy initialized. Brain: {self.model_name}")
    
    # ============================================
    # Entity Extraction
    # ============================================
    
    def _extract_entities(self, text: str) -> List[str]:
        """뉴스에서 핵심 엔티티(기업명) 추출"""
        # 알려진 기업명 매칭
        known_entities = list(SEED_KNOWLEDGE.keys())
        
        # 추가 패턴
        patterns = [
            r'\b(Google|Alphabet|GOOGL)\b',
            r'\b(Nvidia|NVDA)\b',
            r'\b(Broadcom|AVGO)\b',
            r'\b(Microsoft|MSFT)\b',
            r'\b(Amazon|AMZN|AWS)\b',
            r'\b(Apple|AAPL)\b',
            r'\b(OpenAI)\b',
            r'\b(Anthropic|Claude)\b',
            r'\b(Meta|Facebook)\b',
            r'\b(Samsung)\b',
            r'\b(SK Hynix)\b',
            r'\b(Micron|MU)\b',
            r'\b(AMD)\b',
            r'\b(Intel|INTC)\b',
            r'\b(TSMC)\b',
            r'\b(TPU|GPU|HBM)\b',
        ]
        
        entities = set()
        
        # 알려진 기업 매칭
        for entity in known_entities:
            if entity.lower() in text.lower():
                entities.add(entity)
        
        # 패턴 매칭
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(matches)
        
        return list(entities)
    
    # ============================================
    # Knowledge Verification
    # ============================================
    
    async def _verify_relationships(self, entities: List[str]) -> str:
        """
        [Step 0: 지식 검증]
        뉴스에 등장한 기업들의 현재 관계가 지식 베이스와 일치하는지
        실시간 검색을 통해 확인합니다.
        """
        if not self.settings.ENABLE_LIVE_KNOWLEDGE_CHECK:
            return "Live knowledge check disabled. Using cached knowledge."
        
        if len(entities) < 2:
            return "Not enough entities for relationship verification."
        
        # 검색 쿼리 생성
        search_query = f"Latest partnership relationship status between {', '.join(entities[:3])} 2025"
        print(f"  [Verify] Searching: '{search_query}'...")
        
        # AI 클라이언트의 검색 기능 사용
        search_result = await self.ai_client.search_web(search_query)
        
        return search_result
    
    async def _get_knowledge_context(self, entities: List[str]) -> str:
        """Knowledge Graph에서 관련 관계 조회"""
        context_parts = []
        
        for entity in entities[:5]:  # 최대 5개 엔티티
            relations = await self.knowledge_graph.get_relationships(entity)
            
            if relations:
                context_parts.append(f"\n[{entity}]:")
                for rel in relations[:3]:  # 각 엔티티당 최대 3개 관계
                    context_parts.append(
                        f"  - {rel['subject']} --[{rel['relation']}]--> {rel['object']}"
                    )
                    if rel.get('evidence_text'):
                        context_parts.append(f"    Evidence: {rel['evidence_text'][:100]}")
        
        return "\n".join(context_parts) if context_parts else "No cached knowledge found."
    
    # ============================================
    # Prompt Engineering
    # ============================================
    
    def _build_reasoning_prompt(
        self,
        news_text: str,
        verified_context: str,
        knowledge_context: str
    ) -> str:
        """심층 추론 프롬프트 구성"""
        
        prompt = f"""
Role: You are the Lead Strategy AI ({self.model_name}).
Task: Perform a 3-Step Deep Reasoning analysis on the NEWS provided.

=== LATEST CONTEXT (From Live Search) ===
{verified_context}

=== KNOWLEDGE GRAPH (Cached Relationships) ===
{knowledge_context}

=== NEWS ===
{news_text}

=== INSTRUCTIONS ===
Do not rely solely on training data. Use the LATEST CONTEXT and KNOWLEDGE GRAPH above.
If the context says a partnership changed, trust that over your internal memory.

Perform the following 3-step analysis:

STEP 1: DIRECT IMPACT
- Identify key players/entities in this news
- What is the immediate/direct impact on each entity?
- Cite evidence from the context if available

STEP 2: SECONDARY IMPACT (꼬리 물기 - Chain Reasoning)  
- Who are the partners/suppliers/competitors of the directly impacted entities?
- How does the news ripple through the value chain?
- Identify HIDDEN BENEFICIARIES who might not be mentioned but benefit indirectly
- Example: "TPU success → Nvidia dependency↓ → Broadcom (TPU designer) benefits"

STEP 3: STRATEGIC CONCLUSION
- Summarize the macro theme
- Identify:
  * Primary Beneficiary (most obvious winner)
  * Hidden Beneficiary (non-obvious winner from value chain analysis)
  * Loser (who loses from this development)
- Provide Bull Case and Bear Case scenarios
- Give action recommendations with confidence scores (0.0-1.0)

=== OUTPUT FORMAT ===
Respond in valid JSON only. No markdown, no explanation outside JSON.

{{
  "theme": "Brief macro theme (e.g., 'Rise of Custom AI Silicon')",
  
  "step1_direct": {{
    "entities": ["Entity1", "Entity2"],
    "impacts": [
      {{"entity": "Entity1", "impact": "description", "sentiment": "positive/negative/neutral"}}
    ],
    "evidence_ids": ["any cited evidence"]
  }},
  
  "step2_secondary": {{
    "value_chain_analysis": "Explanation of ripple effects",
    "beneficiaries": [
      {{"entity": "Hidden Company", "reason": "Why they benefit indirectly"}}
    ],
    "losers": [
      {{"entity": "Company", "reason": "Why they lose"}}
    ],
    "reasoning_trace": ["Step-by-step reasoning chain"]
  }},
  
  "step3_strategy": {{
    "primary_beneficiary": {{"ticker": "SYMBOL", "action": "BUY/HOLD/SELL", "confidence": 0.85, "reason": "..."}},
    "hidden_beneficiary": {{"ticker": "SYMBOL", "action": "BUY", "confidence": 0.80, "reason": "..."}},
    "loser": {{"ticker": "SYMBOL", "action": "TRIM/SELL", "confidence": 0.60, "reason": "..."}},
    "bull_case": "Best case scenario description",
    "bear_case": "Worst case scenario description"
  }},
  
  "hypothesis_flags": ["Any claims marked as hypothesis (no evidence)"],
  "overall_confidence": 0.75
}}

CRITICAL RULES:
1. If a claim has no evidence in LATEST CONTEXT or KNOWLEDGE GRAPH, add it to "hypothesis_flags"
2. Hidden beneficiary should NOT be the same as primary beneficiary
3. All tickers must be valid stock symbols (e.g., GOOGL not Google)
4. Confidence scores should reflect evidence strength
"""
        return prompt
    
    # ============================================
    # Main Analysis
    # ============================================
    
    async def analyze_news(self, news_text: str) -> DeepReasoningResult:
        """
        뉴스에 대한 심층 추론 수행
        
        Args:
            news_text: 분석할 뉴스 텍스트
            
        Returns:
            DeepReasoningResult: 심층 추론 결과
        """
        print(f"\n{'='*60}")
        print(f"[DeepReasoning] Analyzing: '{news_text[:80]}...'")
        print(f"{'='*60}")
        
        # 캐시 확인
        cache_key = hash(news_text)
        if cache_key in self._reasoning_cache:
            print("  [Cache] Returning cached result")
            return self._reasoning_cache[cache_key]
        
        # Step 0: 엔티티 추출
        entities = self._extract_entities(news_text)
        print(f"  [Step 0] Entities detected: {entities}")
        
        # Step 0.5: 관계 검증 (실시간 검색)
        verified_context = await self._verify_relationships(entities)
        print(f"  [Step 0.5] Verification complete")
        
        # Step 0.6: Knowledge Graph 컨텍스트
        knowledge_context = await self._get_knowledge_context(entities)
        
        # 프롬프트 생성
        prompt = self._build_reasoning_prompt(
            news_text, verified_context, knowledge_context
        )
        
        # AI 호출
        print(f"  [Reasoning] Calling {self.model_name}...")
        response = await self.ai_client.call_api(
            prompt,
            max_tokens=self.settings.MAX_REASONING_TOKENS,
            temperature=0.3
        )
        
        # 응답 파싱
        result = self._parse_response(news_text, response, entities)
        
        # 캐싱
        self._reasoning_cache[cache_key] = result
        self.analysis_count += 1
        
        # 로그
        if self.settings.VERBOSE_REASONING:
            self._print_result(result)
        
        return result
    
    def _parse_response(
        self,
        news_text: str,
        response: str,
        entities: List[str]
    ) -> DeepReasoningResult:
        """AI 응답 파싱"""
        try:
            # JSON 추출 (마크다운 제거)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            # ReasoningStep 생성
            step1 = ReasoningStep(
                step_name="direct_impact",
                input_context=news_text,
                reasoning=str(data.get("step1_direct", {})),
                entities_identified=data.get("step1_direct", {}).get("entities", entities),
                confidence=0.8
            )
            
            step2_data = data.get("step2_secondary", {})
            step2 = ReasoningStep(
                step_name="secondary_impact",
                input_context=str(step1.entities_identified),
                reasoning=step2_data.get("value_chain_analysis", ""),
                entities_identified=[
                    b.get("entity", "") for b in step2_data.get("beneficiaries", [])
                ],
                confidence=0.75
            )
            
            step3_data = data.get("step3_strategy", {})
            step3 = ReasoningStep(
                step_name="strategy",
                input_context="",
                reasoning=f"Bull: {step3_data.get('bull_case', '')} | Bear: {step3_data.get('bear_case', '')}",
                confidence=data.get("overall_confidence", 0.7)
            )
            
            # 최종 결과 생성
            result = DeepReasoningResult(
                news_text=news_text,
                analyzed_at=datetime.now(),
                model_used=self.model_name,
                
                step1_direct=step1,
                step2_secondary=step2,
                step3_strategy=step3,
                
                theme=data.get("theme", "Unknown"),
                primary_beneficiary=step3_data.get("primary_beneficiary", {}),
                hidden_beneficiary=step3_data.get("hidden_beneficiary"),
                loser=step3_data.get("loser"),
                
                bull_case=step3_data.get("bull_case", ""),
                bear_case=step3_data.get("bear_case", ""),
                
                reasoning_trace=step2_data.get("reasoning_trace", [])
            )
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [Error] Failed to parse response: {e}")
            print(f"  [Response] {response[:500]}...")
            
            # 기본 결과 반환
            return DeepReasoningResult(
                news_text=news_text,
                analyzed_at=datetime.now(),
                model_used=self.model_name,
                step1_direct=ReasoningStep("direct", news_text, "Parse error", entities),
                step2_secondary=ReasoningStep("secondary", "", "Parse error"),
                step3_strategy=ReasoningStep("strategy", "", "Parse error"),
                theme="Parse Error",
                primary_beneficiary={},
                reasoning_trace=[f"Error: {str(e)}"]
            )
    
    def _print_result(self, result: DeepReasoningResult):
        """결과 출력"""
        print(f"\n{'='*60}")
        print(f"[RESULT] Theme: {result.theme}")
        print(f"{'='*60}")
        
        print(f"\n[PRIMARY] Primary Beneficiary:")
        if result.primary_beneficiary:
            pb = result.primary_beneficiary
            print(f"   {pb.get('ticker', 'N/A')} -> {pb.get('action', 'N/A')} "
                  f"(Confidence: {pb.get('confidence', 0):.0%})")
            print(f"   Reason: {pb.get('reason', 'N/A')}")

        print(f"\n[HIDDEN] Hidden Beneficiary:")
        if result.hidden_beneficiary:
            hb = result.hidden_beneficiary
            print(f"   {hb.get('ticker', 'N/A')} -> {hb.get('action', 'N/A')} "
                  f"(Confidence: {hb.get('confidence', 0):.0%})")
            print(f"   Reason: {hb.get('reason', 'N/A')}")
        else:
            print("   None identified")

        print(f"\n[LOSER] Loser:")
        if result.loser:
            l = result.loser
            print(f"   {l.get('ticker', 'N/A')} -> {l.get('action', 'N/A')} "
                  f"(Confidence: {l.get('confidence', 0):.0%})")
            print(f"   Reason: {l.get('reason', 'N/A')}")

        print(f"\n[BULL] Bull Case: {result.bull_case[:100]}...")
        print(f"[BEAR] Bear Case: {result.bear_case[:100]}...")

        if result.reasoning_trace:
            print(f"\n[TRACE] Reasoning Trace:")
            for i, trace in enumerate(result.reasoning_trace[:5], 1):
                print(f"   {i}. {trace}")
    
    # ============================================
    # Batch Analysis
    # ============================================
    
    async def analyze_news_batch(
        self,
        news_items: List[str],
        max_concurrent: int = 3
    ) -> List[DeepReasoningResult]:
        """여러 뉴스 배치 분석"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_analyze(news: str):
            async with semaphore:
                return await self.analyze_news(news)
        
        tasks = [limited_analyze(news) for news in news_items]
        return await asyncio.gather(*tasks)
    
    # ============================================
    # Statistics
    # ============================================
    
    def get_stats(self) -> Dict:
        """전략 통계"""
        return {
            "model": self.model_name,
            "analysis_count": self.analysis_count,
            "cache_size": len(self._reasoning_cache),
            "ai_client_stats": self.ai_client.get_usage_stats()
        }


# ============================================
# Demo
# ============================================

async def demo():
    """데모 실행"""
    print("=== Deep Reasoning Strategy Demo ===\n")
    
    # Mock 클라이언트로 테스트
    from backend.ai.ai_client_factory import MockAIClient
    
    mock_client = MockAIClient("mock-reasoning")
    mock_client.set_mock_response("tpu", json.dumps({
        "theme": "Rise of Custom AI Silicon - Anti-Nvidia Alliance",
        "step1_direct": {
            "entities": ["Google", "Nvidia"],
            "impacts": [
                {"entity": "Google", "impact": "Vertical integration success", "sentiment": "positive"},
                {"entity": "Nvidia", "impact": "Loss of inference market share", "sentiment": "negative"}
            ]
        },
        "step2_secondary": {
            "value_chain_analysis": "Google's TPU success reduces reliance on Nvidia GPUs. Broadcom, as the TPU design partner, gains from increased TPU production.",
            "beneficiaries": [
                {"entity": "Broadcom", "reason": "TPU chip design partner - royalty increase"}
            ],
            "losers": [
                {"entity": "Nvidia", "reason": "Losing monopoly in AI inference market"}
            ],
            "reasoning_trace": [
                "1. Google TPU v6 achieves 2x efficiency vs Nvidia H100",
                "2. Anthropic signs 1M TPU contract → validates non-CUDA path",
                "3. Broadcom designs TPU interconnects → direct beneficiary",
                "4. Nvidia loses 'AI tax' revenue from hyperscalers"
            ]
        },
        "step3_strategy": {
            "primary_beneficiary": {"ticker": "GOOGL", "action": "BUY", "confidence": 0.85, "reason": "Full-stack AI advantage"},
            "hidden_beneficiary": {"ticker": "AVGO", "action": "BUY", "confidence": 0.90, "reason": "TPU design partner - hidden winner"},
            "loser": {"ticker": "NVDA", "action": "TRIM", "confidence": 0.60, "reason": "Long-term moat erosion"},
            "bull_case": "TPU ecosystem becomes AI industry standard, Google dominates AI infrastructure",
            "bear_case": "CUDA ecosystem too entrenched, TPU remains Google-only solution"
        },
        "overall_confidence": 0.78
    }))
    
    strategy = DeepReasoningStrategy(ai_client=mock_client)
    
    # 테스트 뉴스
    test_news = [
        "Google announced that Gemini 3.0 was trained entirely on TPU v6, achieving 2x efficiency compared to Nvidia GPUs. Anthropic also signed a contract to use 1 million TPUs.",
        "OpenAI is reportedly working with Broadcom to design custom AI chips for their Stargate project, potentially reducing reliance on Nvidia.",
        "Samsung Electronics reports breakthrough in 2nm foundry yield, potentially winning major AI chip contracts."
    ]
    
    # 분석 실행
    for news in test_news:
        result = await strategy.analyze_news(news)
        print("\n" + "="*60 + "\n")
    
    # 통계
    print("\n=== Strategy Stats ===")
    stats = strategy.get_stats()
    print(f"  Analysis Count: {stats['analysis_count']}")
    print(f"  Cache Size: {stats['cache_size']}")


if __name__ == "__main__":
    asyncio.run(demo())
