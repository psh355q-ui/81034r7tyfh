"""
SEC 공시 문서 관련 데이터 모델

Author: AI Trading System
Date: 2025-11-22
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class FilingType(str, Enum):
    """공시 문서 유형"""
    FORM_10K = "10-K"      # 연간 보고서
    FORM_10Q = "10-Q"      # 분기 보고서
    FORM_8K = "8-K"        # 긴급 공시
    FORM_20F = "20-F"      # 외국 기업 연간 보고서
    FORM_DEF14A = "DEF 14A"  # Proxy Statement


class SECSection(str, Enum):
    """10-K/10-Q 주요 섹션"""
    BUSINESS = "Item 1"              # 사업 개요
    RISK_FACTORS = "Item 1A"         # 리스크 요인
    LEGAL = "Item 3"                 # 법적 절차
    MDA = "Item 7"                   # MD&A (Management Discussion & Analysis)
    FINANCIAL_STATEMENTS = "Item 8"  # 재무제표
    CONTROLS = "Item 9A"             # 내부 통제


@dataclass
class FilingMetadata:
    """공시 문서 메타데이터"""
    ticker: str
    cik: str  # Central Index Key (SEC 고유 번호)
    company_name: str
    filing_type: FilingType
    filing_date: datetime
    fiscal_period: str  # "FY2024", "Q3 2024" 등
    accession_number: str  # SEC 문서 고유 번호
    filing_url: str
    document_url: str  # 실제 문서 URL
    file_size_bytes: Optional[int] = None


@dataclass
class ParsedSection:
    """파싱된 섹션"""
    section_type: SECSection
    title: str
    content: str
    word_count: int
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class ParsedFiling:
    """파싱된 공시 문서"""
    metadata: FilingMetadata
    sections: Dict[SECSection, ParsedSection]
    full_text: str
    total_words: int
    parsed_at: datetime = field(default_factory=datetime.now)
    
    def get_section(self, section_type: SECSection) -> Optional[ParsedSection]:
        """특정 섹션 가져오기"""
        return self.sections.get(section_type)
    
    def get_text_for_ai(self, max_words: int = 50000) -> str:
        """
        AI 분석용 텍스트 추출 (토큰 제한 고려)
        
        우선순위:
        1. Risk Factors (가장 중요)
        2. MD&A
        3. Business
        4. Legal
        """
        priority_sections = [
            SECSection.RISK_FACTORS,
            SECSection.MDA,
            SECSection.BUSINESS,
            SECSection.LEGAL
        ]
        
        result_parts = []
        current_words = 0
        
        for section_type in priority_sections:
            section = self.get_section(section_type)
            if not section:
                continue
            
            if current_words + section.word_count > max_words:
                # 남은 공간만큼만 추가
                remaining_words = max_words - current_words
                words = section.content.split()[:remaining_words]
                result_parts.append(
                    f"\n\n### {section.title}\n" + " ".join(words) + "..."
                )
                break
            
            result_parts.append(f"\n\n### {section.title}\n{section.content}")
            current_words += section.word_count
        
        return "".join(result_parts)


@dataclass
class SECCompanyInfo:
    """SEC 기업 정보"""
    cik: str
    ticker: str
    company_name: str
    sic_code: str  # Standard Industrial Classification
    sic_description: str
    state_of_incorporation: str
    fiscal_year_end: str  # "1231" (MMDD)
    recent_filings: List[FilingMetadata] = field(default_factory=list)


@dataclass
class SECFilingCache:
    """SEC 공시 캐시 정보"""
    ticker: str
    filing_type: FilingType
    fiscal_period: str
    cached_at: datetime
    cache_key: str
    ttl_days: int = 90  # 캐시 유효 기간
    
    @property
    def is_expired(self) -> bool:
        """캐시 만료 여부"""
        from datetime import timedelta
        expiry = self.cached_at + timedelta(days=self.ttl_days)
        return datetime.now() > expiry


# ============================================
# SEC API 응답 모델
# ============================================

@dataclass
class SECSubmission:
    """SEC submissions API 응답"""
    cik: str
    entity_type: str
    sic: str
    sic_description: str
    name: str
    tickers: List[str]
    filings: List[Dict]  # Recent filings raw data
    
    @classmethod
    def from_api_response(cls, data: Dict) -> 'SECSubmission':
        """API 응답에서 객체 생성"""
        return cls(
            cik=data.get('cik', ''),
            entity_type=data.get('entityType', ''),
            sic=data.get('sic', ''),
            sic_description=data.get('sicDescription', ''),
            name=data.get('name', ''),
            tickers=data.get('tickers', []),
            filings=data.get('filings', {}).get('recent', {})
        )


# ============================================
# 에러 클래스
# ============================================

class SECError(Exception):
    """SEC API 관련 기본 에러"""
    pass


class SECRateLimitError(SECError):
    """SEC API Rate Limit 에러"""
    pass


class SECFilingNotFoundError(SECError):
    """공시 문서를 찾을 수 없음"""
    pass


class SECParsingError(SECError):
    """문서 파싱 에러"""
    pass
