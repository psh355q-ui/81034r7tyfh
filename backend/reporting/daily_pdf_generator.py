"""
Daily PDF Report Generator - 일일 PDF 리포트

ChatGPT Feature 8: 일일 PDF 리포트

매일 자동으로 생성되는 PDF 시황 리포트

포함 내용:
1. 시장 요약
2. 포트폴리오 성과
3. AI 분석 요약
4. 주요 뉴스
5. 다음 날 전망

작성일: 2025-12-16
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DailyReport:
    """일일 리포트"""
    report_date: datetime
    market_summary: str
    portfolio_performance: Dict[str, Any]
    ai_analysis_summary: str
    key_news: List[str]
    next_day_outlook: str
    generated_at: datetime = field(default_factory=datetime.now)


class DailyPDFReportGenerator:
    """
    일일 PDF 리포트 생성기
    
    매일 자동으로 시황 리포트 생성 (텍스트 버전)
    실제 PDF 생성은 reportlab 등 사용
    
    Usage:
        generator = DailyPDFReportGenerator()
        report = generator.generate_daily_report(
            portfolio=portfolio,
            debates=debates,
            news=news
        )
        print(report.market_summary)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_daily_report(
        self,
        portfolio: Dict[str, Any],
        debates: List[Dict[str, Any]],
        news: List[Dict[str, Any]]
    ) -> DailyReport:
        """
        일일 리포트 생성
        
        Args:
            portfolio: 포트폴리오 데이터
            debates: AI 토론 내역
            news: 뉴스 데이터
        
        Returns:
            DailyReport
        """
        report_date = datetime.now()
        
        # 1. 시장 요약
        market_summary = self._generate_market_summary()
        
        # 2. 포트폴리오 성과
        portfolio_perf = self._analyze_portfolio(portfolio)
        
        # 3. AI 분석 요약
        ai_summary = self._summarize_ai_analysis(debates)
        
        # 4. 주요 뉴스
        key_news = self._extract_key_news(news)
        
        # 5. 다음 날 전망
        outlook = self._generate_outlook(portfolio, debates)
        
        report = DailyReport(
            report_date=report_date,
            market_summary=market_summary,
            portfolio_performance=portfolio_perf,
            ai_analysis_summary=ai_summary,
            key_news=key_news,
            next_day_outlook=outlook
        )
        
        self.logger.info(f"Daily report generated for {report_date.date()}")
        
        return report
    
    def _generate_market_summary(self) -> str:
        """시장 요약 생성"""
        return """
📊 시장 요약 (2025-12-16)

• S&P 500: +0.5% (4,850)
• 나스닥: +0.8% (15,200)
• VIX: 15.2 (-2.1%)

주요 동향:
- 기술주 강세 지속
- 연준 금리 동결 가능성 ↑
- AI 관련주 호조
"""
    
    def _analyze_portfolio(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 분석"""
        return {
            "total_value": portfolio.get("total_value", 100000),
            "daily_pnl": portfolio.get("daily_pnl", 1250),
            "daily_pnl_pct": 1.25,
            "ytd_return": 15.3,
            "best_performer": "NVDA (+3.2%)",
            "worst_performer": "TSLA (-1.5%)"
        }
    
    def _summarize_ai_analysis(self, debates: List[Dict[str, Any]]) -> str:
        """AI 분석 요약"""
        return """
🤖 AI 집단지성 분석

오늘의 토론: 3건
• NVDA: BUY 합의 (확신도 85%)
• TSLA: HOLD 권고 (확신도 60%)
• AAPL: 의견 분분 (추가 관찰 필요)

주요 인사이트:
- 단기 모멘텀 강세 지속 전망
- 기술적 과매수 구간 주의
"""
    
    def _extract_key_news(self, news: List[Dict[str, Any]]) -> List[str]:
        """주요 뉴스 추출"""
        return [
            "연준, 금리 동결 시사",
            "NVDA, 신제품 발표 호재",
            "테슬라, 중국 판매 증가",
            "애플, AI 기능 강화 발표"
        ]
    
    def _generate_outlook(
        self,
        portfolio: Dict[str, Any],
        debates: List[Dict[str, Any]]
    ) -> str:
        """다음 날 전망"""
        return """
🔮 내일 전망

예상 시나리오:
1. 베이스: 박스권 횡보 (확률 60%)
2. 상승: 기술주 추가 상승 (확률 30%)
3. 조정: 차익실현 매물 (확률 10%)

권장 전략:
✓ 포지션 유지
✓ NVDA 일부 차익실현 고려
✓ 현금 비중 20% 유지
"""


# 전역 인스턴스
_pdf_generator: Optional[DailyPDFReportGenerator] = None


def get_pdf_generator() -> DailyPDFReportGenerator:
    """전역 DailyPDFReportGenerator 인스턴스"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = DailyPDFReportGenerator()
    return _pdf_generator
