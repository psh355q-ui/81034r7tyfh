"""
Claude 기반 SEC 공시 분석 엔진

Author: AI Trading System
Date: 2025-11-22
"""

import json
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import anthropic

from backend.data.sec_client import SECClient
from backend.data.sec_parser import SECParser
from backend.core.models.sec_models import FilingType, ParsedFiling
from backend.core.models.sec_analysis_models import (
    SECAnalysisResult,
    SECAnalysisRequest,
    RiskFactor,
    RedFlag,
    FinancialTrend,
    ManagementTone,
    RiskLevel,
    SentimentTone,
    RedFlagType,
    risk_level_from_score,
    sentiment_from_score,
    signal_from_risk
)
from backend.ai.sec_prompts import (
    build_analysis_prompt,
    build_quick_summary_prompt,
    estimate_tokens,
    estimate_analysis_cost
)
# Phase 1: Cost Optimization - Prompt Compression
from backend.ai.compression import IntelligentPromptCompressor

logger = logging.getLogger(__name__)


class SECAnalyzer:
    """
    SEC 공시 AI 분석 엔진
    
    Features:
    - Claude API를 사용한 종합 분석
    - Risk factors 추출 및 평가
    - Red flags 탐지
    - 재무 트렌드 분석
    - 경영진 어조 분석
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
        sec_client: Optional[SECClient] = None,
        sec_parser: Optional[SECParser] = None
    ):
        """
        Args:
            anthropic_api_key: Anthropic API 키
            model: 사용할 Claude 모델
            sec_client: SEC 클라이언트 (선택)
            sec_parser: SEC 파서 (선택)
        """
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.model = model
        self.sec_client = sec_client or SECClient()
        self.parser = sec_parser or SECParser()
        
        logger.info(f"SEC Analyzer initialized (model: {model})")
    
    async def analyze_ticker(
        self,
        request: SECAnalysisRequest
    ) -> SECAnalysisResult:
        """
        티커 기반 분석 (자동으로 최신 공시 다운로드)
        
        Args:
            request: 분석 요청
            
        Returns:
            SECAnalysisResult
        """
        logger.info(f"Analyzing {request.ticker} {request.filing_type}...")
        
        # 1. 최신 공시 조회
        filing_type_enum = FilingType(request.filing_type)
        filing = await self.sec_client.get_latest_filing(
            request.ticker,
            filing_type_enum
        )
        
        if not filing:
            raise ValueError(f"No {request.filing_type} found for {request.ticker}")
        
        # 2. 문서 다운로드
        content = await self.sec_client.download_filing(
            filing,
            force_refresh=request.force_refresh
        )
        
        # 3. 파싱
        parsed = self.parser.parse(filing, content)
        
        # 4. 분석
        return await self.analyze_filing(parsed, request)
    
    async def analyze_filing(
        self,
        parsed: ParsedFiling,
        request: SECAnalysisRequest
    ) -> SECAnalysisResult:
        """
        파싱된 공시 분석 (with LLMLingua-2 compression)
        
        Args:
            parsed: 파싱된 공시
            request: 분석 요청
            
        Returns:
            SECAnalysisResult
        """
        # AI용 텍스트 생성 (토큰 제한 고려)
        ai_text = parsed.get_text_for_ai(max_words=request.max_tokens // 4)
        
        # 섹션 딕셔너리
        sections_dict = {
            section.title: section.content
            for section in parsed.sections.values()
        }
        
        # === Phase 1: Compress SEC filing text before analysis ===
        try:
            compressor = IntelligentPromptCompressor()
            compression_result = compressor.compress_sec_filing(
                filing_text=ai_text,
                query=f"Analyze {parsed.metadata.filing_type.value} filing for {parsed.metadata.ticker}"
            )
            
            # Use compressed text instead of original
            compressed_text = compression_result['compressed_prompt']
            
            logger.info(
                f"📦 Compression: {compression_result['original_tokens']:,} → "
                f"{compression_result['compressed_tokens']:,} tokens "
                f"({compression_result['savings']:.1%} saved)"
            )
        except Exception as e:
            logger.warning(f"⚠️ Compression failed: {e}, using original text")
            compressed_text = ai_text
            compression_result = {'savings': 0.0}
        
        # 프롬프트 생성 (now with compressed text)
        prompt = build_analysis_prompt(
            ticker=parsed.metadata.ticker,
            company_name=parsed.metadata.company_name,
            filing_type=parsed.metadata.filing_type.value,
            fiscal_period=parsed.metadata.fiscal_period,
            filing_date=parsed.metadata.filing_date.strftime("%Y-%m-%d"),
            sections=sections_dict,
            document_content=compressed_text  # ✨ Using compressed text
        )
        
        # 토큰 추정
        estimated_input_tokens = estimate_tokens(prompt)
        estimated_cost = estimate_analysis_cost(estimated_input_tokens, model=self.model)
        
        logger.info(
            f"Sending to Claude: ~{estimated_input_tokens:,} tokens, "
            f"~${estimated_cost:.4f}"
        )
        
        # Claude API 호출
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,  # JSON 응답용
                temperature=0.0,  # 일관성을 위해 0
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 응답 파싱
            response_text = response.content[0].text
            
            # JSON 추출 (Claude가 마크다운으로 감쌀 수 있음)
            json_text = self._extract_json(response_text)
            analysis_data = json.loads(json_text)
            
            # 실제 사용 토큰
            actual_input_tokens = response.usage.input_tokens
            actual_output_tokens = response.usage.output_tokens
            actual_cost = estimate_analysis_cost(
                actual_input_tokens,
                actual_output_tokens,
                model=self.model
            )
            
            logger.info(
                f"Claude response: {actual_input_tokens:,} in, "
                f"{actual_output_tokens:,} out, ${actual_cost:.4f} "
                f"(💰 saved {compression_result['savings']:.1%} on input)"
            )
            
            # 결과 객체 생성
            result = self._parse_analysis_response(
                analysis_data,
                parsed.metadata.ticker,
                parsed.metadata.filing_type.value,
                parsed.metadata.fiscal_period,
                actual_input_tokens + actual_output_tokens,
                actual_cost
            )
            
            return result
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise
    
    async def analyze_management_discussion(
        self,
        parsed: ParsedFiling,
        prior_analysis: Optional['SECAnalysisResult'] = None
    ) -> 'ManagementAnalysis':
        """
        MD&A 섹션 집중 분석 (Phase 15)
        
        Args:
            parsed: 파싱된 공시
            prior_analysis: 이전 분기 분석 결과 (Tone Shift 비교용)
            
        Returns:
            ManagementAnalysis
        """
        from backend.core.models.sec_analysis_models import (
            ManagementAnalysis, Quote, ToneShift
        )
        
        # MD&A 섹션 추출
        mda_section = parsed.get_section(SECSection.MDA)
        if not mda_section:
            logger.warning(f"No MD&A section found for {parsed.metadata.ticker}")
            return ManagementAnalysis(
                ticker=parsed.metadata.ticker,
                fiscal_period=parsed.metadata.fiscal_period
            )
        
        # CEO Quotes 추출
        ceo_quotes_data = self.parser.extract_ceo_quotes(mda_section.content)
        ceo_quotes = [Quote(**q) for q in ceo_quotes_data]
        
        # Forward-looking statement 카운트
        forward_count = self.parser.count_forward_looking_statements(mda_section.content)
        
        # 현재 분석의 Tone 가져오기 (이미 analyze_filing에서 분석됨)
        # 여기서는 간단히 placeholder 사용
        current_tone = None
        
        # Tone Shift 분석 (이전 분기와 비교)
        tone_shift = None
        if prior_analysis and prior_analysis.management_tone and current_tone:
            tone_shift = self.detect_tone_shift(current_tone, prior_analysis.management_tone)
        
        # Risk 언급 빈도
        risk_keywords = ["risk", "challenge", "uncertainty", "concern", "threat"]
        risk_mentions = {
            kw: mda_section.content.lower().count(kw)
            for kw in risk_keywords
        }
        
        return ManagementAnalysis(
            ticker=parsed.metadata.ticker,
            fiscal_period=parsed.metadata.fiscal_period,
            ceo_quotes=ceo_quotes,
            forward_looking_count=forward_count,
            tone=current_tone,
            tone_shift=tone_shift,
            risk_mentions=risk_mentions
        )
    
    def detect_tone_shift(
        self,
        current_tone: 'ManagementTone',
        prior_tone: 'ManagementTone'
    ) -> 'ToneShift':
        """
        어조 변화 감지 (Phase 15)
        
        Args:
            current_tone: 현재 분기 어조
            prior_tone: 이전 분기 어조
            
        Returns:
            ToneShift
        """
        from backend.core.models.sec_analysis_models import (
            ToneShift, ToneShiftDirection
        )
        
        # 감정 점수 차이
        sentiment_delta = current_tone.sentiment_score - prior_tone.sentiment_score
        
        # 방향 결정
        if sentiment_delta > 0.2:
            direction = ToneShiftDirection.MORE_OPTIMISTIC
            signal = "POSITIVE"
        elif sentiment_delta < -0.2:
            direction = ToneShiftDirection.MORE_PESSIMISTIC
            signal = "NEGATIVE"
        else:
            direction = ToneShiftDirection.SIMILAR
            signal = "NEUTRAL"
        
        # 주요 변화 사항
        key_changes = []
        
        # Confidence 변화
        if current_tone.confidence_level != prior_tone.confidence_level:
            key_changes.append(
                f"Confidence: {prior_tone.confidence_level} → {current_tone.confidence_level}"
            )
        
        # 새로운 우려사항
        new_concerns = set(current_tone.concerns_mentioned) - set(prior_tone.concerns_mentioned)
        if new_concerns:
            key_changes.append(f"New concerns: {', '.join(list(new_concerns)[:3])}")
        
        # 새로운 기회
        new_opportunities = set(current_tone.opportunities_mentioned) - set(prior_tone.opportunities_mentioned)
        if new_opportunities:
            key_changes.append(f"New opportunities: {', '.join(list(new_opportunities)[:3])}")
        
        return ToneShift(
            direction=direction,
            magnitude=abs(sentiment_delta),
            key_changes=key_changes,
            signal=signal
        )
    
    def _extract_json(self, text: str) -> str:
        """
        텍스트에서 JSON 추출
        
        Claude가 ```json ... ``` 마크다운으로 감쌀 수 있음
        """
        # 마크다운 코드 블록 제거
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _parse_analysis_response(
        self,
        data: Dict[str, Any],
        ticker: str,
        filing_type: str,
        fiscal_period: str,
        tokens_used: int,
        cost: float
    ) -> SECAnalysisResult:
        """
        Claude 응답 JSON을 SECAnalysisResult로 변환
        """
        # Risk Factors
        risk_factors = []
        for rf_data in data.get("risk_factors", []):
            risk_factors.append(RiskFactor(
                category=rf_data["category"],
                title=rf_data["title"],
                description=rf_data["description"],
                severity=RiskLevel(rf_data["severity"]),
                impact_score=rf_data["impact_score"],
                likelihood_score=rf_data["likelihood_score"],
                is_new=rf_data.get("is_new", False)
            ))
        
        # Red Flags
        red_flags = []
        for rf_data in data.get("red_flags", []):
            red_flags.append(RedFlag(
                flag_type=RedFlagType(rf_data["flag_type"]),
                severity=RiskLevel(rf_data["severity"]),
                description=rf_data["description"],
                detected_in_section=rf_data["detected_in_section"],
                quotes=rf_data.get("quotes", []),
                action_required=rf_data.get("action_required", False)
            ))
        
        # Financial Trends
        financial_trends = []
        for ft_data in data.get("financial_trends", []):
            financial_trends.append(FinancialTrend(
                metric=ft_data["metric"],
                current_value=ft_data.get("current_value"),
                prior_value=ft_data.get("prior_value"),
                change_percent=ft_data.get("change_percent"),
                trend=ft_data["trend"],
                interpretation=ft_data["interpretation"]
            ))
        
        # Management Tone
        management_tone = None
        if "management_tone" in data and data["management_tone"]:
            mt_data = data["management_tone"]
            management_tone = ManagementTone(
                overall_sentiment=SentimentTone(mt_data["overall_sentiment"]),
                sentiment_score=mt_data["sentiment_score"],
                confidence_level=mt_data["confidence_level"],
                key_phrases=mt_data.get("key_phrases", []),
                tone_change_vs_prior=mt_data.get("tone_change_vs_prior"),
                concerns_mentioned=mt_data.get("concerns_mentioned", []),
                opportunities_mentioned=mt_data.get("opportunities_mentioned", [])
            )
        
        # Overall Assessment
        overall_risk_level = RiskLevel(data["overall_risk_level"])
        overall_risk_score = data["overall_risk_score"]
        investment_signal = data["investment_signal"]
        
        # 결과 생성
        result = SECAnalysisResult(
            ticker=ticker,
            filing_type=filing_type,
            fiscal_period=fiscal_period,
            analysis_date=datetime.now(),
            overall_risk_level=overall_risk_level,
            overall_risk_score=overall_risk_score,
            investment_signal=investment_signal,
            risk_factors=risk_factors,
            red_flags=red_flags,
            financial_trends=financial_trends,
            management_tone=management_tone,
            executive_summary=data["executive_summary"],
            key_takeaways=data["key_takeaways"],
            model_used=self.model,
            tokens_used=tokens_used,
            analysis_cost=cost,
            confidence_score=data.get("confidence_score", 0.8)
        )
        
        return result
    
    async def quick_summary(
        self,
        ticker: str,
        filing_type: str = "10-Q"
    ) -> Dict[str, Any]:
        """
        빠른 요약 (저비용, 토큰 최소화)
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형
            
        Returns:
            간단 요약 딕셔너리
        """
        # 최신 공시 조회
        filing = await self.sec_client.get_latest_filing(
            ticker,
            FilingType(filing_type)
        )
        
        if not filing:
            raise ValueError(f"No {filing_type} found for {ticker}")
        
        # 문서 다운로드
        content = await self.sec_client.download_filing(filing)
        
        # 파싱
        parsed = self.parser.parse(filing, content)
        
        # 짧은 발췌 (2000 단어)
        excerpt = parsed.get_text_for_ai(max_words=2000)
        
        # 간단 프롬프트
        prompt = build_quick_summary_prompt(ticker, filing_type, excerpt)
        
        # Claude 호출
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        json_text = self._extract_json(response_text)
        
        return json.loads(json_text)


# ============================================
# 편의 함수
# ============================================

async def analyze_10k(
    ticker: str,
    anthropic_api_key: str,
    force_refresh: bool = False
) -> SECAnalysisResult:
    """10-K 분석 (편의 함수)"""
    analyzer = SECAnalyzer(anthropic_api_key)
    request = SECAnalysisRequest(
        ticker=ticker,
        filing_type="10-K",
        force_refresh=force_refresh
    )
    return await analyzer.analyze_ticker(request)


async def analyze_10q(
    ticker: str,
    anthropic_api_key: str,
    force_refresh: bool = False
) -> SECAnalysisResult:
    """10-Q 분석 (편의 함수)"""
    analyzer = SECAnalyzer(anthropic_api_key)
    request = SECAnalysisRequest(
        ticker=ticker,
        filing_type="10-Q",
        force_refresh=force_refresh
    )
    return await analyzer.analyze_ticker(request)


# ============================================
# 데모
# ============================================

async def demo():
    """SEC Analyzer 데모"""
    import os
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return
    
    analyzer = SECAnalyzer(api_key)
    
    # 분석 요청
    request = SECAnalysisRequest(
        ticker="NVDA",
        filing_type="10-Q",
        force_refresh=False
    )
    
    print(f"\n{'='*60}")
    print(f"SEC ANALYZER DEMO: {request.ticker} {request.filing_type}")
    print(f"{'='*60}\n")
    
    # 분석 실행
    result = await analyzer.analyze_ticker(request)
    
    # 결과 출력
    print(f"📊 Analysis Complete")
    print(f"   Filing: {result.filing_type} {result.fiscal_period}")
    print(f"   Overall Risk: {result.overall_risk_level.value} ({result.overall_risk_score:.2f})")
    print(f"   Signal: {result.investment_signal}")
    print(f"   Tokens: {result.tokens_used:,}")
    print(f"   Cost: ${result.analysis_cost:.4f}")
    
    print(f"\n📝 Executive Summary:")
    print(f"   {result.executive_summary}")
    
    print(f"\n🔑 Key Takeaways:")
    for i, takeaway in enumerate(result.key_takeaways, 1):
        print(f"   {i}. {takeaway}")
    
    print(f"\n⚠️  Risk Factors ({len(result.risk_factors)}):")
    for rf in result.get_high_risks()[:3]:
        print(f"   - [{rf.severity.value}] {rf.title}")
        print(f"     Risk Score: {rf.risk_score:.2f}")
    
    if result.red_flags:
        print(f"\n🚨 Red Flags ({len(result.red_flags)}):")
        for rf in result.red_flags[:3]:
            print(f"   - [{rf.severity.value}] {rf.flag_type.value}")
            print(f"     {rf.description}")
    
    if result.management_tone:
        print(f"\n💬 Management Tone:")
        print(f"   Sentiment: {result.management_tone.overall_sentiment.value}")
        print(f"   Score: {result.management_tone.sentiment_score:.2f}")
        print(f"   Confidence: {result.management_tone.confidence_level}")
    
    print(f"\n{'='*60}")
    
    # 요약 딕셔너리
    summary = result.to_summary_dict()
    print(f"\n📋 Summary for Trading Agent:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
