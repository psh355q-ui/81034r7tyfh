"""
SEC 공시 문서 파서

10-K/10-Q HTML 문서에서 주요 섹션을 추출하고 텍스트로 변환

Author: AI Trading System
Date: 2025-11-22
"""

import re
from typing import Dict, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from backend.core.models.sec_models import (
    FilingMetadata,
    ParsedFiling,
    ParsedSection,
    SECSection,
    SECParsingError
)

logger = logging.getLogger(__name__)


class SECParser:
    """
    SEC 공시 문서 파서
    
    Features:
    - HTML 정제
    - 섹션별 추출 (Item 1, 1A, 7, 8 등)
    - 텍스트 정규화
    - 표/이미지 제거
    """
    
    # 10-K/10-Q 주요 섹션 패턴
    SECTION_PATTERNS = {
        SECSection.BUSINESS: [
            r"ITEM\s+1\.?\s+BUSINESS",
            r"ITEM\s+1\.?\s+Description of Business"
        ],
        SECSection.RISK_FACTORS: [
            r"ITEM\s+1A\.?\s+RISK FACTORS",
            r"ITEM\s+1A\.?\s+Risk Factors"
        ],
        SECSection.LEGAL: [
            r"ITEM\s+3\.?\s+LEGAL PROCEEDINGS",
            r"ITEM\s+3\.?\s+Legal Proceedings"
        ],
        SECSection.MDA: [
            r"ITEM\s+7\.?\s+MANAGEMENT'?S DISCUSSION",
            r"ITEM\s+7\.?\s+MD&A"
        ],
        SECSection.FINANCIAL_STATEMENTS: [
            r"ITEM\s+8\.?\s+FINANCIAL STATEMENTS",
            r"ITEM\s+8\.?\s+Consolidated Financial Statements"
        ],
        SECSection.CONTROLS: [
            r"ITEM\s+9A\.?\s+CONTROLS AND PROCEDURES",
            r"ITEM\s+9A\.?\s+Controls and Procedures"
        ]
    }
    
    def __init__(self):
        """파서 초기화"""
        self.soup = None
    
    def parse(
        self,
        filing: FilingMetadata,
        content: str
    ) -> ParsedFiling:
        """
        공시 문서 파싱
        
        Args:
            filing: 공시 메타데이터
            content: HTML 또는 텍스트 내용
            
        Returns:
            ParsedFiling
            
        Raises:
            SECParsingError: 파싱 실패
        """
        try:
            # HTML 정제
            clean_text = self._clean_html(content)
            
            # 섹션 추출
            sections = self._extract_sections(clean_text)
            
            # 전체 단어 수
            total_words = len(clean_text.split())
            
            parsed = ParsedFiling(
                metadata=filing,
                sections=sections,
                full_text=clean_text,
                total_words=total_words,
                parsed_at=datetime.now()
            )
            
            logger.info(
                f"Parsed {filing.ticker} {filing.filing_type.value}: "
                f"{len(sections)} sections, {total_words:,} words"
            )
            
            return parsed
            
        except Exception as e:
            raise SECParsingError(f"Failed to parse filing: {e}")
    
    def _clean_html(self, content: str) -> str:
        """
        HTML 정제 및 텍스트 추출
        
        제거 대상:
        - HTML 태그
        - JavaScript/CSS
        - 표 (재무제표는 너무 복잡)
        - XBRL 태그
        - 과도한 공백
        """
        # BeautifulSoup으로 파싱
        self.soup = BeautifulSoup(content, 'html.parser')
        
        # 불필요한 태그 제거
        for tag in self.soup(['script', 'style', 'table', 'img']):
            tag.decompose()
        
        # 텍스트 추출
        text = self.soup.get_text(separator='\n')
        
        # XBRL 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 과도한 공백 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 연속된 빈 줄 → 2줄로
        text = re.sub(r'[ \t]+', ' ', text)      # 연속된 공백 → 1칸
        
        # 특수 문자 정리
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')  # Zero-width space
        
        return text.strip()
    
    def _extract_sections(self, text: str) -> Dict[SECSection, ParsedSection]:
        """
        주요 섹션 추출
        
        Args:
            text: 정제된 텍스트
            
        Returns:
            섹션 딕셔너리
        """
        sections = {}
        
        for section_type, patterns in self.SECTION_PATTERNS.items():
            section = self._extract_section(text, section_type, patterns)
            if section:
                sections[section_type] = section
        
        return sections
    
    def _extract_section(
        self,
        text: str,
        section_type: SECSection,
        patterns: List[str]
    ) -> Optional[ParsedSection]:
        """
        특정 섹션 추출
        
        Args:
            text: 전체 텍스트
            section_type: 섹션 타입
            patterns: 검색 패턴 (정규식)
            
        Returns:
            ParsedSection 또는 None
        """
        # 여러 패턴 시도
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            if match:
                start_pos = match.start()
                
                # 다음 섹션 찾기 (Item 2, Item 1B 등)
                next_section_match = re.search(
                    r'\n\s*ITEM\s+\d+[A-Z]?\.?\s+',
                    text[start_pos + 100:],  # 100자 이후부터 검색 (현재 섹션 제목 스킵)
                    re.IGNORECASE
                )
                
                if next_section_match:
                    end_pos = start_pos + 100 + next_section_match.start()
                else:
                    # 다음 섹션 없으면 끝까지
                    end_pos = len(text)
                
                # 섹션 내용 추출
                content = text[start_pos:end_pos].strip()
                
                # 제목 추출 (첫 줄)
                title_match = re.search(r'^.*?$', content, re.MULTILINE)
                title = title_match.group(0) if title_match else section_type.value
                
                # 내용 (제목 제외)
                body = content[len(title):].strip()
                
                # 너무 짧으면 스킵 (실제 내용 아닐 가능성)
                if len(body.split()) < 50:
                    continue
                
                return ParsedSection(
                    section_type=section_type,
                    title=title,
                    content=body,
                    word_count=len(body.split()),
                    extracted_at=datetime.now()
                )
        
        logger.warning(f"Section not found: {section_type}")
        return None
    
    def extract_risk_factors(self, parsed: ParsedFiling) -> List[str]:
        """
        Risk Factors를 개별 리스크로 분리
        
        Args:
            parsed: 파싱된 문서
            
        Returns:
            리스크 목록
        """
        risk_section = parsed.get_section(SECSection.RISK_FACTORS)
        if not risk_section:
            return []
        
        content = risk_section.content
        
        # 리스크는 보통 "•", "-", 또는 번호로 시작
        # 또는 "Risk:" 같은 패턴
        
        # 패턴 1: 글머리 기호
        risks = re.split(r'\n\s*[•\-\*]\s+', content)
        
        # 패턴 2: 번호 (1., 2., 등)
        if len(risks) <= 1:
            risks = re.split(r'\n\s*\d+\.\s+', content)
        
        # 너무 짧거나 긴 항목 필터링
        filtered = []
        for risk in risks:
            words = len(risk.split())
            if 20 <= words <= 500:  # 적절한 길이
                filtered.append(risk.strip())
        
        return filtered[:20]  # 최대 20개
    
    def extract_key_metrics(self, parsed: ParsedFiling) -> Dict[str, str]:
        """
        주요 재무 지표 추출 (MD&A 섹션에서)
        
        간단한 패턴 매칭 사용 (정확도 제한적)
        향후 AI 분석으로 대체 예정
        
        Args:
            parsed: 파싱된 문서
            
        Returns:
            지표 딕셔너리
        """
        mda_section = parsed.get_section(SECSection.MDA)
        if not mda_section:
            return {}
        
        content = mda_section.content
        metrics = {}
        
        # 패턴 매칭 (매우 기본적)
        patterns = {
            'revenue': r'revenue[s]?\s+(?:of\s+)?\$?([\d,\.]+)\s*(?:million|billion)?',
            'net_income': r'net income\s+(?:of\s+)?\$?([\d,\.]+)\s*(?:million|billion)?',
            'eps': r'earnings per share\s+(?:of\s+)?\$?([\d\.]+)',
            'cash': r'cash and cash equivalents\s+(?:of\s+)?\$?([\d,\.]+)\s*(?:million|billion)?'
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metrics[metric] = match.group(1)
        
        return metrics
    
    def get_text_summary(self, parsed: ParsedFiling, max_words: int = 5000) -> str:
        """
        요약 텍스트 추출 (AI 분석용 미리보기)
        
        Args:
            parsed: 파싱된 문서
            max_words: 최대 단어 수
            
        Returns:
            요약 텍스트
        """
        # 우선순위 섹션
        priority_sections = [
            SECSection.RISK_FACTORS,
            SECSection.MDA
        ]
        
        summary_parts = []
        current_words = 0
        
        for section_type in priority_sections:
            section = parsed.get_section(section_type)
            if not section:
                continue
            
            # 섹션의 앞부분만 (첫 N 단어)
            words = section.content.split()[:1000]
            section_text = " ".join(words)
            
            summary_parts.append(f"\n### {section.title}\n{section_text}...")
            current_words += len(words)
            
            if current_words >= max_words:
                break
        
        return "".join(summary_parts)
    
    def extract_ceo_quotes(self, mda_text: str) -> List[Dict[str, any]]:
        """
        CEO 직접 발언 추출 (Phase 15)
        
        Args:
            mda_text: MD&A 섹션 텍스트
            
        Returns:
            CEO Quote 목록
        """
        quotes = []
        
        # CEO 발언 패턴
        patterns = [
            # "We believe/expect/anticipate..."
            (r'(?:We|I)\s+(?:believe|expect|anticipate|plan|intend|estimate)[^.]{20,200}\.', 'forward_looking'),
            # "Our strategy..."
            (r'(?:Our|My)\s+(?:strategy|approach|focus|goal|objective)[^.]{20,200}\.', 'strategy'),
            # "Looking ahead..."
            (r'Looking\s+(?:ahead|forward)[^.]{20,200}\.', 'forward_looking'),
            # Risk mentions
            (r'(?:We|I)\s+(?:face|encounter|recognize)\s+(?:risks?|challenges?)[^.]{20,200}\.', 'risk_mention'),
            # Opportunities
            (r'(?:We|I)\s+(?:see|identify|pursue)\s+(?:opportunities?|potential)[^.]{20,200}\.', 'opportunity'),
        ]
        
        for pattern, quote_type in patterns:
            matches = re.finditer(pattern, mda_text, re.IGNORECASE)
            for match in matches:
                quote_text = match.group(0).strip()
                
                # 너무 짧거나 긴 것 필터링
                word_count = len(quote_text.split())
                if word_count < 5 or word_count > 50:
                    continue
                
                quotes.append({
                    "text": quote_text,
                    "type": quote_type,
                    "position": match.start()
                })
        
        # 중복 제거 (같은 텍스트)
        seen = set()
        unique_quotes = []
        for quote in quotes:
            if quote["text"] not in seen:
                seen.add(quote["text"])
                unique_quotes.append(quote)
        
        return unique_quotes[:20]  # 최대 20개
    
    def count_forward_looking_statements(self, mda_text: str) -> int:
        """
        Forward-looking statement 개수 카운트
        
        Args:
            mda_text: MD&A 섹션 텍스트
            
        Returns:
            Forward-looking 키워드 출현 횟수
        """
        forward_keywords = [
            "expect", "anticipate", "believe", "plan", "intend",
            "estimate", "project", "forecast", "outlook", "guidance",
            "will", "should", "could", "may", "might"
        ]
        
        text_lower = mda_text.lower()
        count = sum(text_lower.count(keyword) for keyword in forward_keywords)
        
        return count


# ============================================
# 유틸리티 함수
# ============================================

def parse_filing(filing: FilingMetadata, content: str) -> ParsedFiling:
    """공시 문서 파싱 (편의 함수)"""
    parser = SECParser()
    return parser.parse(filing, content)


def extract_risks(parsed: ParsedFiling) -> List[str]:
    """리스크 목록 추출 (편의 함수)"""
    parser = SECParser()
    return parser.extract_risk_factors(parsed)


# ============================================
# 테스트/데모
# ============================================

def demo_parser():
    """파서 데모 (샘플 HTML)"""
    
    # 샘플 HTML
    sample_html = """
    <html>
    <head><title>10-K</title></head>
    <body>
        <h1>ITEM 1. BUSINESS</h1>
        <p>Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide...</p>
        
        <h1>ITEM 1A. RISK FACTORS</h1>
        <p>The following risk factors could materially adversely affect our business:</p>
        <ul>
            <li>Global economic conditions could adversely affect demand for our products</li>
            <li>Competition in mobile devices and personal computers is intense</li>
            <li>Supply chain disruptions could impact our ability to meet demand</li>
        </ul>
        
        <h1>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</h1>
        <p>Net sales for 2024 were $394.3 billion, an increase of 2% compared to 2023...</p>
        <p>Net income was $97.0 billion, compared to $96.9 billion in 2023...</p>
    </body>
    </html>
    """
    
    from backend.core.models.sec_models import FilingType
    from datetime import datetime
    
    # 샘플 메타데이터
    filing = FilingMetadata(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        filing_type=FilingType.FORM_10K,
        filing_date=datetime(2024, 11, 1),
        fiscal_period="FY2024",
        accession_number="0000320193-24-000123",
        filing_url="https://example.com",
        document_url="https://example.com/doc.html"
    )
    
    # 파싱
    parser = SECParser()
    parsed = parser.parse(filing, sample_html)
    
    print("=== Parsed Filing ===")
    print(f"Total words: {parsed.total_words:,}")
    print(f"Sections found: {len(parsed.sections)}")
    
    for section_type, section in parsed.sections.items():
        print(f"\n### {section.title}")
        print(f"Words: {section.word_count:,}")
        print(f"Preview: {section.content[:200]}...")
    
    # 리스크 추출
    risks = parser.extract_risk_factors(parsed)
    print(f"\n=== Risk Factors ({len(risks)}) ===")
    for i, risk in enumerate(risks[:3], 1):
        print(f"{i}. {risk[:100]}...")
    
    # AI용 텍스트
    ai_text = parsed.get_text_for_ai(max_words=1000)
    print(f"\n=== AI Text ({len(ai_text.split())} words) ===")
    print(ai_text[:500] + "...")


if __name__ == "__main__":
    demo_parser()
