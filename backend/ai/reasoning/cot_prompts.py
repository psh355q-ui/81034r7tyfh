"""
Chain of Thought (CoT) Prompt Templates
========================================

3개 AI 모델별 최적화된 심층 추론 프롬프트

특징:
- Claude: 간결하고 체계적, 증거 기반
- Gemini: 상세한 추론 과정, 숫자 기반 근거
- GPT: 실용적, 안전 체크 포함

사용법:
    template = get_prompt_template("claude")
    prompt = template.format(
        evidence_blocks="...",
        news_text="..."
    )
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class PromptStyle(str, Enum):
    """프롬프트 스타일"""
    CLAUDE = "claude"
    GEMINI = "gemini"
    GPT = "gpt"


# ============================================
# Claude Template (간결 · 체계적)
# ============================================

CLAUDE_SYSTEM_PROMPT = """You are an industry macro strategist specializing in AI infrastructure and semiconductor sectors. 
Use evidence provided below. ALWAYS follow the 3-step Chain-of-Thought procedure and output JSON only.
Be concise but precise. Cite evidence_ids for all claims."""

CLAUDE_COT_TEMPLATE = """
{evidence_blocks}

=== TASK ===
Analyze the following NEWS using 3-step Chain-of-Thought:

NEWS: {news_text}

=== PROCEDURE ===
1) STEP1_DIRECT: List directly impacted companies and why.
   - Link evidence_ids to support claims
   - Sentiment: positive/negative/neutral

2) STEP2_SECONDARY: List secondary beneficiaries/losers.
   - Trace value chain (supplier → customer → competitor)
   - Mark unverified claims as hypothesis:true
   - Identify HIDDEN BENEFICIARIES (non-obvious winners)

3) STEP3_STRATEGY: Produce actionable recommendations.
   - primary_beneficiary: most obvious winner
   - hidden_beneficiary: non-obvious winner (value chain insight)
   - loser: who loses from this news
   - Include confidence scores (0.0-1.0)

=== RULES ===
- Must cite evidence_ids for claims (e.g., "E1", "E2")
- If no evidence, set hypothesis:true
- Use valid stock tickers (GOOGL not Google)
- Hidden beneficiary ≠ primary beneficiary

=== OUTPUT SCHEMA ===
{{
  "theme": "string",
  "step1_direct": {{
    "entities": ["string"],
    "impacts": [{{"entity": "string", "impact": "string", "sentiment": "string", "evidence_ids": ["E1"]}}]
  }},
  "step2_secondary": {{
    "value_chain_analysis": "string",
    "beneficiaries": [{{"entity": "string", "ticker": "string", "reason": "string", "hypothesis": false}}],
    "losers": [{{"entity": "string", "ticker": "string", "reason": "string", "hypothesis": false}}],
    "reasoning_trace": ["string"]
  }},
  "step3_strategy": {{
    "primary_beneficiary": {{"ticker": "string", "action": "BUY/HOLD/SELL", "confidence": 0.85, "reason": "string"}},
    "hidden_beneficiary": {{"ticker": "string", "action": "BUY", "confidence": 0.80, "reason": "string"}},
    "loser": {{"ticker": "string", "action": "TRIM/SELL", "confidence": 0.60, "reason": "string"}},
    "bull_case": "string",
    "bear_case": "string"
  }},
  "hypothesis_flags": ["string"],
  "overall_confidence": 0.75
}}
"""


# ============================================
# Gemini Template (상세 · 숫자 기반)
# ============================================

GEMINI_SYSTEM_PROMPT = """You are a senior macro equity strategist with 20+ years of experience in AI infrastructure investing.
Your specialty is uncovering hidden value chain beneficiaries that retail investors miss.
Evidence blocks are provided below. Always reason step-by-step with quantitative justification where possible."""

GEMINI_COT_TEMPLATE = """
{evidence_blocks}

=== ROLE ===
Senior Macro Equity Strategist - AI Infrastructure Specialist

=== TASK ===
Analyze the following NEWS with comprehensive Chain-of-Thought reasoning:

NEWS: {news_text}

=== DETAILED INSTRUCTIONS ===

**STEP 1: DIRECT IMPACT ANALYSIS**
For each step, produce numbered reasoning paragraphs.
- Identify all mentioned entities
- Quantify impact if possible (e.g., "~$X billion revenue exposure")
- Cite specific evidence with evidence_ids

**STEP 2: VALUE CHAIN DEEP DIVE (꼬리 물기)**
Expand partner→function mapping in detail:
- Example: "Broadcom: TPU interconnect design + ASIC integration → 5-7% of Google TPU cost"
- Trace 2-3 levels deep in the value chain
- CRITICAL: Identify the "pick and shovel" plays others miss

**STEP 3: STRATEGIC RECOMMENDATIONS**
- Provide confidence score with rationale
- Minimum one sentence of quantitative reasoning
- Example: "Expected revenue exposure ~15% of Broadcom's segment revenue"

=== OUTPUT FORMAT ===
JSON with same schema as standard. Also include:
- "reasoning_trace": ["sentence1", "sentence2", ...] for each logical step
- "quantitative_notes": any numerical estimates

{{
  "theme": "string (specific, e.g., 'Custom ASIC Era Begins')",
  
  "step1_direct": {{
    "entities": ["string"],
    "impacts": [
      {{
        "entity": "string",
        "impact": "string",
        "sentiment": "positive/negative/neutral",
        "quantitative_note": "optional: $X billion exposure",
        "evidence_ids": ["E1", "E2"]
      }}
    ]
  }},
  
  "step2_secondary": {{
    "value_chain_analysis": "Detailed explanation with specific company roles",
    "partner_function_map": [
      {{"company": "Broadcom", "function": "TPU interconnect + ASIC design", "estimated_exposure": "5-7% of chip cost"}}
    ],
    "beneficiaries": [
      {{"entity": "string", "ticker": "string", "reason": "string", "confidence": 0.85, "hypothesis": false}}
    ],
    "losers": [
      {{"entity": "string", "ticker": "string", "reason": "string", "confidence": 0.60, "hypothesis": false}}
    ],
    "reasoning_trace": [
      "1. Google TPU v6 announced with 2x efficiency",
      "2. TPU uses Broadcom's interconnect technology",
      "3. More TPU adoption → More Broadcom royalty revenue",
      "4. Nvidia loses inference market share"
    ]
  }},
  
  "step3_strategy": {{
    "primary_beneficiary": {{
      "ticker": "string",
      "action": "BUY/HOLD/SELL",
      "confidence": 0.85,
      "reason": "string",
      "target_position_size": "2-3% of portfolio"
    }},
    "hidden_beneficiary": {{
      "ticker": "string",
      "action": "BUY",
      "confidence": 0.80,
      "reason": "Non-obvious value chain winner",
      "why_hidden": "Not mentioned in news but benefits from supply chain"
    }},
    "loser": {{
      "ticker": "string",
      "action": "TRIM/SELL",
      "confidence": 0.60,
      "reason": "string"
    }},
    "bull_case": "Best case: X% upside over 12 months if...",
    "bear_case": "Worst case: X% downside if..."
  }},
  
  "quantitative_notes": ["Any numerical estimates made"],
  "hypothesis_flags": ["Claims without direct evidence"],
  "overall_confidence": 0.75
}}
"""


# ============================================
# GPT Template (실용적 · 안전 체크)
# ============================================

GPT_SYSTEM_PROMPT = """You are a strategic reasoner for institutional trading decisions.
Perform 3-step analysis using RAG evidence. Prioritize reputable sources.
Include safety checks and risk assessment for all recommendations."""

GPT_COT_TEMPLATE = """
{evidence_blocks}

=== PROMPT ===
You must perform 3-step Chain-of-Thought analysis on the following news:

NEWS: {news_text}

=== STEP-BY-STEP ===

**Step 1: Direct Impact**
For each entity mentioned:
- Company name
- Direct impact (positive/negative/neutral)
- One-line evidence summary
- Source quality (high/medium/low)

**Step 2: Secondary Impact**
Trace the ripple effects:
- Partner companies affected
- Competitor implications
- Supply chain disruptions
- HIDDEN BENEFICIARIES: Who wins that isn't mentioned?

**Step 3: Strategy & Risk Assessment**
For each recommendation:
- Action (BUY/HOLD/SELL/TRIM)
- Position sizing suggestion
- Stop-loss level if applicable
- Key risks to monitor

=== CONSTRAINTS ===
- If claims are not backed by evidence, mark hypothesis:true
- Confidence score formula: min(0.9, 0.3 + 0.15*evidence_count + 0.15*has_high_quality_source)
- Always include at least one risk factor per recommendation
- Never recommend > 5% position size for single names

=== OUTPUT ===
Return JSON only. Schema:

{{
  "theme": "string",
  
  "step1_direct": {{
    "entities": ["string"],
    "impacts": [
      {{
        "entity": "string",
        "impact": "string",
        "sentiment": "string",
        "source_quality": "high/medium/low",
        "evidence_summary": "string"
      }}
    ]
  }},
  
  "step2_secondary": {{
    "value_chain_analysis": "string",
    "beneficiaries": [
      {{"entity": "string", "ticker": "string", "reason": "string", "hypothesis": false}}
    ],
    "losers": [
      {{"entity": "string", "ticker": "string", "reason": "string", "hypothesis": false}}
    ],
    "reasoning_trace": ["string"]
  }},
  
  "step3_strategy": {{
    "primary_beneficiary": {{
      "ticker": "string",
      "action": "BUY/HOLD/SELL",
      "confidence": 0.85,
      "reason": "string",
      "position_size": "1-3%",
      "stop_loss": "-10% from entry",
      "risks": ["Risk 1", "Risk 2"]
    }},
    "hidden_beneficiary": {{
      "ticker": "string",
      "action": "BUY",
      "confidence": 0.80,
      "reason": "string",
      "risks": ["Risk 1"]
    }},
    "loser": {{
      "ticker": "string",
      "action": "TRIM/SELL",
      "confidence": 0.60,
      "reason": "string"
    }},
    "bull_case": "string",
    "bear_case": "string"
  }},
  
  "risk_assessment": {{
    "overall_risk_level": "low/medium/high",
    "key_risks": ["Risk 1", "Risk 2"],
    "monitoring_triggers": ["What to watch for"]
  }},
  
  "hypothesis_flags": ["string"],
  "overall_confidence": 0.75
}}
"""


# ============================================
# Template Manager
# ============================================

@dataclass
class PromptTemplate:
    """프롬프트 템플릿"""
    style: PromptStyle
    system_prompt: str
    user_template: str
    
    def format(
        self,
        news_text: str,
        evidence_blocks: str = "",
        **kwargs
    ) -> Dict[str, str]:
        """프롬프트 포맷팅"""
        formatted_user = self.user_template.format(
            news_text=news_text,
            evidence_blocks=evidence_blocks,
            **kwargs
        )
        return {
            "system": self.system_prompt,
            "user": formatted_user
        }


TEMPLATES: Dict[PromptStyle, PromptTemplate] = {
    PromptStyle.CLAUDE: PromptTemplate(
        style=PromptStyle.CLAUDE,
        system_prompt=CLAUDE_SYSTEM_PROMPT,
        user_template=CLAUDE_COT_TEMPLATE
    ),
    PromptStyle.GEMINI: PromptTemplate(
        style=PromptStyle.GEMINI,
        system_prompt=GEMINI_SYSTEM_PROMPT,
        user_template=GEMINI_COT_TEMPLATE
    ),
    PromptStyle.GPT: PromptTemplate(
        style=PromptStyle.GPT,
        system_prompt=GPT_SYSTEM_PROMPT,
        user_template=GPT_COT_TEMPLATE
    )
}


def get_prompt_template(style: str = "claude") -> PromptTemplate:
    """프롬프트 템플릿 가져오기"""
    try:
        prompt_style = PromptStyle(style.lower())
    except ValueError:
        prompt_style = PromptStyle.CLAUDE
    
    return TEMPLATES[prompt_style]


def format_evidence_blocks(
    relationships: list,
    search_results: Optional[str] = None
) -> str:
    """증거 블록 포맷팅"""
    blocks = []
    
    # Knowledge Graph 관계
    if relationships:
        blocks.append("=== KNOWLEDGE GRAPH EVIDENCE ===")
        for i, rel in enumerate(relationships, 1):
            blocks.append(
                f"[E{i}] {rel.get('subject', '')} --[{rel.get('relation', '')}]--> "
                f"{rel.get('object', '')}"
            )
            if rel.get('evidence_text'):
                blocks.append(f"     Evidence: {rel['evidence_text'][:150]}")
            if rel.get('source'):
                blocks.append(f"     Source: {rel['source']}")
            blocks.append("")
    
    # 검색 결과
    if search_results:
        blocks.append("=== LIVE SEARCH RESULTS ===")
        blocks.append(search_results)
        blocks.append("")
    
    return "\n".join(blocks) if blocks else "No evidence provided."


# ============================================
# Demo
# ============================================

def demo():
    """템플릿 데모"""
    print("=== CoT Prompt Templates Demo ===\n")
    
    test_news = "Google announced Gemini 3.0 trained entirely on TPUs."
    
    test_relationships = [
        {"subject": "Google", "relation": "partner", "object": "Broadcom", 
         "evidence_text": "Broadcom designs TPU interconnects"},
        {"subject": "Google", "relation": "competitor", "object": "Nvidia",
         "evidence_text": "TPU competes with Nvidia GPUs"}
    ]
    
    evidence = format_evidence_blocks(
        relationships=test_relationships,
        search_results="Recent: Anthropic signs 1M TPU contract with Google"
    )
    
    for style in PromptStyle:
        print(f"\n{'='*60}")
        print(f"Template: {style.value.upper()}")
        print(f"{'='*60}")
        
        template = get_prompt_template(style.value)
        prompt = template.format(
            news_text=test_news,
            evidence_blocks=evidence
        )
        
        print(f"\n[System Prompt ({len(prompt['system'])} chars)]")
        print(prompt['system'][:200] + "...")
        
        print(f"\n[User Prompt ({len(prompt['user'])} chars)]")
        print(prompt['user'][:500] + "...")


if __name__ == "__main__":
    demo()
