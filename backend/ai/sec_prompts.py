"""
SEC 공시 분석용 Claude 프롬프트

Author: AI Trading System
Date: 2025-11-22
"""

from typing import Dict, Any


# ============================================
# 메인 분석 프롬프트
# ============================================

SEC_ANALYSIS_PROMPT = """You are a professional financial analyst specializing in SEC filings analysis. Your task is to analyze the provided 10-K or 10-Q filing and provide a comprehensive investment risk assessment.

## FILING INFORMATION
- Company: {ticker} - {company_name}
- Filing Type: {filing_type}
- Fiscal Period: {fiscal_period}
- Filing Date: {filing_date}

## DOCUMENT SECTIONS PROVIDED
{sections_summary}

## YOUR ANALYSIS TASKS

### 1. RISK FACTORS ANALYSIS
Analyze the Risk Factors section and identify:
- **Top 5-10 most material risks** with severity assessment
- **New risks** not mentioned in prior filings (if context available)
- **Categorize risks** into: Market, Operational, Financial, Regulatory, Legal, Technology, Competitive
- **Impact score** (0.0-1.0) and **Likelihood score** (0.0-1.0) for each

### 2. RED FLAGS DETECTION
Scan ALL sections for critical warning signs:
- Accounting method changes
- Auditor changes or qualified opinions
- Going concern warnings
- Financial restatements
- Material weaknesses in internal controls
- Large lawsuits or regulatory actions
- Unusual insider trading patterns
- Debt covenant breaches
- Revenue recognition issues

For each red flag, provide:
- Type and severity (CRITICAL/HIGH/MEDIUM/LOW)
- Description and location in filing
- Relevant quotes from the document

### 3. FINANCIAL TRENDS
From the MD&A section, extract and analyze:
- Revenue trend (improving/stable/declining)
- Profitability trend
- Cash flow situation
- Debt levels and leverage changes
- Key metric changes vs prior period

### 4. MANAGEMENT TONE ANALYSIS
Assess the overall tone and sentiment:
- Sentiment score: -1.0 (very negative) to +1.0 (very positive)
- Confidence level: HIGH/MEDIUM/LOW
- Key positive phrases/opportunities mentioned
- Key concerns/challenges mentioned
- Tone change vs prior filing (if applicable)

### 5. EXECUTIVE SUMMARY
Provide a 3-5 sentence summary covering:
- Overall financial health assessment
- Most critical risks or issues
- Investment outlook

### 6. OVERALL ASSESSMENT
- Overall Risk Level: CRITICAL/HIGH/MEDIUM/LOW/MINIMAL
- Overall Risk Score: 0.0-1.0
- Investment Signal: BUY/HOLD/SELL/AVOID
- Confidence in this analysis: 0.0-1.0

## OUTPUT FORMAT

You MUST respond with a valid JSON object in this exact structure:

```json
{{
  "risk_factors": [
    {{
      "category": "Market|Operational|Financial|Regulatory|Legal|Technology|Competitive",
      "title": "Brief risk title",
      "description": "2-3 sentence summary of the risk",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|MINIMAL",
      "impact_score": 0.0-1.0,
      "likelihood_score": 0.0-1.0,
      "is_new": true|false
    }}
  ],
  "red_flags": [
    {{
      "flag_type": "ACCOUNTING_CHANGE|AUDITOR_CHANGE|GOING_CONCERN|RESTATEMENT|LAWSUIT|REGULATORY_ACTION|INSIDER_TRADING|DEBT_COVENANT|MATERIAL_WEAKNESS|REVENUE_RECOGNITION",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "What was found",
      "detected_in_section": "Section name",
      "quotes": ["Relevant quote from filing"],
      "action_required": true|false
    }}
  ],
  "financial_trends": [
    {{
      "metric": "revenue|net_income|eps|debt|cash_flow",
      "current_value": "Value with units",
      "prior_value": "Value with units",
      "change_percent": -100.0 to +100.0,
      "trend": "IMPROVING|STABLE|DECLINING",
      "interpretation": "Brief explanation"
    }}
  ],
  "management_tone": {{
    "overall_sentiment": "VERY_POSITIVE|POSITIVE|NEUTRAL|NEGATIVE|VERY_NEGATIVE",
    "sentiment_score": -1.0 to +1.0,
    "confidence_level": "HIGH|MEDIUM|LOW",
    "key_phrases": ["Notable positive phrases"],
    "tone_change_vs_prior": "More optimistic|Similar|More pessimistic|Unknown",
    "concerns_mentioned": ["Key concerns"],
    "opportunities_mentioned": ["Key opportunities"]
  }},
  "overall_risk_level": "CRITICAL|HIGH|MEDIUM|LOW|MINIMAL",
  "overall_risk_score": 0.0-1.0,
  "investment_signal": "BUY|HOLD|SELL|AVOID",
  "executive_summary": "3-5 sentence summary",
  "key_takeaways": [
    "Takeaway 1",
    "Takeaway 2",
    "Takeaway 3",
    "Takeaway 4",
    "Takeaway 5"
  ],
  "confidence_score": 0.0-1.0
}}
```

## IMPORTANT GUIDELINES

1. **BE OBJECTIVE**: Base analysis on facts in the filing, not market sentiment
2. **BE CONSERVATIVE**: When uncertain, assign higher risk scores
3. **PRIORITIZE MATERIAL ISSUES**: Focus on items that could significantly impact investment value
4. **CITE EVIDENCE**: When possible, reference specific sections or quotes
5. **AVOID SPECULATION**: Only analyze what's explicitly stated in the filing
6. **BE CONSISTENT**: Use the exact enum values specified in the JSON structure
7. **BE COMPLETE**: Fill all required fields; use null/empty arrays if no data available

## DOCUMENT CONTENT

{document_content}

---

PROVIDE YOUR ANALYSIS AS A VALID JSON OBJECT. DO NOT include any text outside the JSON structure, including backticks or markdown formatting.
"""


# ============================================
# 간단 요약 프롬프트 (저비용)
# ============================================

SEC_QUICK_SUMMARY_PROMPT = """You are analyzing a {filing_type} filing for {ticker}.

Provide a BRIEF analysis focusing on:
1. Top 3 risks
2. Any critical red flags
3. Overall risk level (CRITICAL/HIGH/MEDIUM/LOW/MINIMAL)
4. Investment signal (BUY/HOLD/SELL/AVOID)
5. 2-sentence summary

Document excerpt (Risk Factors & MD&A):
{document_excerpt}

Respond with JSON:
{{
  "top_risks": ["Risk 1", "Risk 2", "Risk 3"],
  "red_flags": ["Flag 1", "Flag 2"],
  "overall_risk_level": "MEDIUM",
  "investment_signal": "HOLD",
  "summary": "Brief summary"
}}

DO NOT output anything other than valid JSON.
"""


# ============================================
# Red Flag 전문 탐지 프롬프트
# ============================================

RED_FLAG_DETECTION_PROMPT = """You are a forensic accounting expert analyzing SEC filings for warning signs.

Company: {ticker}
Filing: {filing_type} {fiscal_period}

Your ONLY task is to detect RED FLAGS in these categories:
1. Accounting changes or irregularities
2. Auditor issues
3. Going concern warnings
4. Restatements
5. Material weaknesses
6. Legal/regulatory actions
7. Insider trading anomalies
8. Debt covenant issues
9. Revenue recognition problems

Sections to analyze:
{sections_content}

For EACH red flag found, provide:
- Type (use exact enum value)
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Description
- Section where found
- Relevant quote (if available)
- Action required? (true/false)

Output JSON array:
```json
[
  {{
    "flag_type": "ACCOUNTING_CHANGE",
    "severity": "HIGH",
    "description": "What was found",
    "detected_in_section": "Item 8",
    "quotes": ["Quote from filing"],
    "action_required": true
  }}
]
```

If NO red flags found, return empty array: []

DO NOT output anything other than valid JSON array.
"""


# ============================================
# 경영진 어조 분석 프롬프트
# ============================================

MANAGEMENT_TONE_PROMPT = """Analyze the management's tone and sentiment in this MD&A section.

Company: {ticker}
Filing: {filing_type} {fiscal_period}

MD&A Content:
{mda_content}

Assess:
1. Overall sentiment (-1.0 to +1.0)
2. Confidence level (HIGH/MEDIUM/LOW)
3. Key positive phrases
4. Key concerns/challenges
5. Opportunities mentioned

Output JSON:
{{
  "overall_sentiment": "POSITIVE|NEUTRAL|NEGATIVE",
  "sentiment_score": 0.0,
  "confidence_level": "MEDIUM",
  "key_phrases": ["phrase 1", "phrase 2"],
  "concerns_mentioned": ["concern 1"],
  "opportunities_mentioned": ["opportunity 1"]
}}

DO NOT output anything other than valid JSON.
"""


# ============================================
# 프롬프트 빌더 함수
# ============================================

def build_analysis_prompt(
    ticker: str,
    company_name: str,
    filing_type: str,
    fiscal_period: str,
    filing_date: str,
    sections: Dict[str, str],
    document_content: str
) -> str:
    """
    메인 분석 프롬프트 생성
    
    Args:
        ticker: 주식 티커
        company_name: 회사명
        filing_type: 공시 유형 (10-K, 10-Q)
        fiscal_period: 회계 기간
        filing_date: 공시 날짜
        sections: 섹션 딕셔너리 {섹션명: 내용}
        document_content: 전체 문서 내용
        
    Returns:
        포맷된 프롬프트
    """
    # 섹션 요약
    sections_summary = "\n".join([
        f"- {name}: {len(content.split())} words"
        for name, content in sections.items()
    ])
    
    return SEC_ANALYSIS_PROMPT.format(
        ticker=ticker,
        company_name=company_name,
        filing_type=filing_type,
        fiscal_period=fiscal_period,
        filing_date=filing_date,
        sections_summary=sections_summary,
        document_content=document_content
    )


def build_quick_summary_prompt(
    ticker: str,
    filing_type: str,
    document_excerpt: str
) -> str:
    """간단 요약 프롬프트 생성"""
    return SEC_QUICK_SUMMARY_PROMPT.format(
        ticker=ticker,
        filing_type=filing_type,
        document_excerpt=document_excerpt
    )


def build_red_flag_prompt(
    ticker: str,
    filing_type: str,
    fiscal_period: str,
    sections_content: str
) -> str:
    """Red Flag 탐지 프롬프트 생성"""
    return RED_FLAG_DETECTION_PROMPT.format(
        ticker=ticker,
        filing_type=filing_type,
        fiscal_period=fiscal_period,
        sections_content=sections_content
    )


def build_tone_analysis_prompt(
    ticker: str,
    filing_type: str,
    fiscal_period: str,
    mda_content: str
) -> str:
    """어조 분석 프롬프트 생성"""
    return MANAGEMENT_TONE_PROMPT.format(
        ticker=ticker,
        filing_type=filing_type,
        fiscal_period=fiscal_period,
        mda_content=mda_content
    )


# ============================================
# 토큰 추정
# ============================================

def estimate_tokens(text: str) -> int:
    """
    텍스트 토큰 수 추정 (대략 1 token = 4 characters)
    
    Claude의 정확한 토큰 카운트는 API 응답에서 확인
    """
    return len(text) // 4


def estimate_analysis_cost(
    input_tokens: int,
    output_tokens: int = 2000,  # JSON 응답 평균
    model: str = "claude-sonnet-4.5"
) -> float:
    """
    분석 비용 추정
    
    Sonnet 4.5 요금 (2025-11):
    - Input: $3 / 1M tokens
    - Output: $15 / 1M tokens
    """
    if "haiku" in model.lower():
        # Haiku 요금
        input_cost = input_tokens * 0.25 / 1_000_000
        output_cost = output_tokens * 1.25 / 1_000_000
    else:
        # Sonnet 요금
        input_cost = input_tokens * 3.0 / 1_000_000
        output_cost = output_tokens * 15.0 / 1_000_000
    
    return input_cost + output_cost


# ============================================
# 프롬프트 테스트
# ============================================

if __name__ == "__main__":
    # 샘플 프롬프트 생성
    sample_sections = {
        "Item 1A. Risk Factors": "Various risks including market risks, operational risks...",
        "Item 7. MD&A": "Revenue increased 10% to $100M..."
    }
    
    prompt = build_analysis_prompt(
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        fiscal_period="FY2024",
        filing_date="2024-11-01",
        sections=sample_sections,
        document_content="[Full document content here]"
    )
    
    print("=== Sample Prompt ===")
    print(prompt[:1000] + "...")
    print(f"\nEstimated tokens: {estimate_tokens(prompt):,}")
    print(f"Estimated cost: ${estimate_analysis_cost(estimate_tokens(prompt)):.4f}")
