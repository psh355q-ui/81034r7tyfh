"""
Trading Terms Parser

MASTER_GUIDE.md에서 기술 용어를 추출하여 사전 생성
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


# ============================================================================
# Pre-defined Trading Terms Dictionary
# ============================================================================

# MASTER_GUIDE.md 기반으로 미리 정의된 용어들
# 실제 운영시 MASTER_GUIDE.md를 파싱하거나 별도 JSON 파일로 관리

TRADING_TERMS = [
    # Risk Management
    {
        "term": "Kill Switch",
        "term_kr": "킬 스위치",
        "definition": "일일 손실이 특정 임계값(예: -2%)을 초과하면 자동으로 모든 거래를 중단하는 안전 메커니즘. 급격한 시장 하락이나 시스템 오류로 인한 큰 손실을 방지합니다.",
        "example": "포트폴리오가 하루에 2% 이상 하락하면 Kill Switch가 작동하여 모든 신규 매매를 중단하고 기존 주문도 취소됩니다.",
        "category": "리스크 관리",
        "related_terms": ["Stop Loss", "Position Sizing", "Max Drawdown"]
    },
    {
        "term": "Stop Loss",
        "term_kr": "손절가",
        "definition": "사전에 설정한 가격에 도달하면 자동으로 포지션을 청산하여 손실을 제한하는 주문. 일반적으로 매입가 대비 일정 비율(예: -3%)로 설정됩니다.",
        "example": "AAPL을 $200에 매수하고 3% 손절을 설정하면, 가격이 $194에 도달 시 자동 매도됩니다.",
        "category": "리스크 관리",
        "related_terms": ["Target Price", "Risk-Reward Ratio", "Trailing Stop"]
    },
    {
        "term": "Position Sizing",
        "term_kr": "포지션 사이징",
        "definition": "전체 포트폴리오에서 개별 종목에 할당하는 비중을 결정하는 전략. 리스크 대비 수익을 최적화하고 과도한 집중을 방지합니다.",
        "example": "최대 포지션 크기를 포트폴리오의 5%로 제한하면, $100,000 포트폴리오에서 단일 종목에 최대 $5,000을 투자합니다.",
        "category": "리스크 관리",
        "related_terms": ["Kelly Criterion", "Risk Per Trade", "Portfolio Allocation"]
    },
    {
        "term": "Max Drawdown",
        "term_kr": "최대 낙폭",
        "definition": "특정 기간 동안 포트폴리오가 최고점에서 최저점까지 하락한 최대 비율. 전략의 위험성을 측정하는 중요한 지표입니다.",
        "example": "포트폴리오가 $100,000에서 $85,000으로 하락 후 회복했다면, 최대 낙폭은 15%입니다.",
        "category": "성과 측정",
        "related_terms": ["Sharpe Ratio", "Volatility", "Risk-Adjusted Return"]
    },
    
    # Technical Analysis
    {
        "term": "RSI (Relative Strength Index)",
        "term_kr": "상대강도지수",
        "definition": "주가의 상승/하락 모멘텀을 측정하는 기술적 지표. 0-100 사이의 값을 가지며, 70 이상은 과매수, 30 이하는 과매도를 나타냅니다.",
        "example": "TSLA의 RSI가 75라면 과매수 상태로, 단기 조정이 있을 수 있음을 의미합니다.",
        "category": "기술적 분석",
        "related_terms": ["MACD", "Bollinger Bands", "Moving Average"]
    },
    {
        "term": "Moving Average",
        "term_kr": "이동평균선",
        "definition": "일정 기간 동안의 평균 가격을 연결한 선. 추세를 파악하고 지지/저항 수준을 식별하는 데 사용됩니다. 20일(단기), 60일(중기), 120일(장기) 등이 일반적입니다.",
        "example": "주가가 20일 이동평균선 위에 있으면 단기 상승 추세, 아래에 있으면 하락 추세로 볼 수 있습니다.",
        "category": "기술적 분석",
        "related_terms": ["SMA", "EMA", "Golden Cross", "Death Cross"]
    },
    {
        "term": "Volatility",
        "term_kr": "변동성",
        "definition": "주가의 변동 폭을 나타내는 지표. 일반적으로 표준편차로 측정하며, 높은 변동성은 높은 위험과 기회를 의미합니다.",
        "example": "변동성이 50% 이상인 종목은 고위험으로 분류되어 헌법 규칙에 의해 자동 필터링됩니다.",
        "category": "기술적 분석",
        "related_terms": ["Standard Deviation", "ATR", "VIX", "Beta"]
    },
    {
        "term": "Momentum",
        "term_kr": "모멘텀",
        "definition": "가격 변화의 속도와 방향을 측정하는 지표. 양의 모멘텀은 상승 추세, 음의 모멘텀은 하락 추세를 나타냅니다.",
        "example": "20일 모멘텀이 -30% 미만이면 급격한 하락세로, Constitution 규칙에 의해 매수가 제한됩니다.",
        "category": "기술적 분석",
        "related_terms": ["RSI", "MACD", "Rate of Change", "Trend"]
    },
    
    # AI/ML Terms
    {
        "term": "Claude 3.5 Haiku",
        "term_kr": "클로드 3.5 하이쿠",
        "definition": "Anthropic이 개발한 빠르고 비용 효율적인 AI 모델. 주식 분석에서 기술적/펀더멘털 분석을 수행하고 매매 결정을 내립니다.",
        "example": "Claude Haiku는 종목당 $0.00095의 비용으로 실시간 분석을 제공하며, 약 2.5K 토큰을 사용합니다.",
        "category": "AI 모델",
        "related_terms": ["Claude Sonnet", "Gemini", "ChatGPT", "LLM"]
    },
    {
        "term": "Conviction",
        "term_kr": "확신도",
        "definition": "AI가 특정 투자 결정에 대해 갖는 신뢰 수준. 0-100% 사이의 값으로 표현되며, BUY는 70% 이상, SELL은 60% 이상이 필요합니다.",
        "example": "Claude가 NVDA에 대해 85% 확신도로 BUY를 추천했다면, 이는 강한 매수 신호입니다.",
        "category": "AI 분석",
        "related_terms": ["Action", "Reasoning", "Risk Factors"]
    },
    {
        "term": "Constitution Rules",
        "term_kr": "헌법 규칙",
        "definition": "AI의 매매 결정을 검증하고 제한하는 규칙 집합. Pre-check(사전 검증)와 Post-check(사후 검증)로 나뉘며, 과도한 리스크를 방지합니다.",
        "example": "Pre-check: 변동성 50% 초과 종목 필터링. Post-check: BUY 결정은 70% 이상 확신도 필요.",
        "category": "AI 분석",
        "related_terms": ["Pre-Check", "Post-Check", "Threshold", "Filter"]
    },
    {
        "term": "Token",
        "term_kr": "토큰",
        "definition": "AI 모델이 처리하는 텍스트의 기본 단위. 대략 4글자 또는 0.75단어에 해당하며, API 비용은 토큰 수에 비례합니다.",
        "example": "Claude Haiku는 입력 $1/M 토큰, 출력 $5/M 토큰을 사용하므로, 2500토큰 분석 시 약 $0.00095가 소요됩니다.",
        "category": "AI 모델",
        "related_terms": ["Context Window", "Input Token", "Output Token", "Cost"]
    },
    
    # Execution
    {
        "term": "TWAP (Time-Weighted Average Price)",
        "term_kr": "시간가중평균가격",
        "definition": "대량 주문을 일정 시간에 걸쳐 균등하게 분할 실행하는 알고리즘. 시장 충격을 최소화합니다.",
        "example": "10,000주를 2시간 동안 TWAP으로 실행하면, 매 5분마다 약 416주를 매수합니다.",
        "category": "주문 실행",
        "related_terms": ["VWAP", "Slippage", "Market Impact", "Execution Algorithm"]
    },
    {
        "term": "VWAP (Volume-Weighted Average Price)",
        "term_kr": "거래량가중평균가격",
        "definition": "거래량을 고려하여 평균 가격을 계산하는 방식. 기관 투자자들이 실행 품질을 측정하는 벤치마크로 사용합니다.",
        "example": "하루 동안 평균 가격이 $100이고 VWAP이 $99.50이라면, VWAP보다 높게 매수한 것이므로 실행 품질이 떨어집니다.",
        "category": "주문 실행",
        "related_terms": ["TWAP", "Implementation Shortfall", "Execution Quality"]
    },
    {
        "term": "Slippage",
        "term_kr": "슬리피지",
        "definition": "주문 예상 가격과 실제 체결 가격의 차이. 유동성 부족이나 시장 변동으로 발생하며, 일반적으로 1-5 basis points입니다.",
        "example": "$100에 매수 주문을 넣었지만 $100.05에 체결되었다면, 5 basis points (0.05%)의 슬리피지가 발생한 것입니다.",
        "category": "주문 실행",
        "related_terms": ["Market Impact", "Bid-Ask Spread", "Liquidity"]
    },
    
    # Feature Store
    {
        "term": "Feature Store",
        "term_kr": "피처 스토어",
        "definition": "머신러닝 모델이 사용하는 특성(feature)을 중앙에서 관리하고 제공하는 데이터 시스템. Redis(L1)와 TimescaleDB(L2)의 2계층 캐시로 구성됩니다.",
        "example": "AAPL의 ret_5d, vol_20d 등의 특성을 Feature Store에서 <5ms 내에 조회할 수 있습니다.",
        "category": "데이터 인프라",
        "related_terms": ["Redis", "TimescaleDB", "Cache Hit Rate", "Latency"]
    },
    {
        "term": "Rolling Features",
        "term_kr": "롤링 피처",
        "definition": "일정 기간(window)에 걸쳐 계산되는 특성. 5일, 20일, 60일, 120일 등의 기간으로 수익률, 변동성 등을 계산합니다.",
        "example": "ret_20d는 최근 20일 수익률, vol_60d는 최근 60일 변동성을 의미합니다.",
        "category": "데이터 인프라",
        "related_terms": ["Window", "Time Series", "Feature Engineering"]
    },
    {
        "term": "Cache Hit Rate",
        "term_kr": "캐시 적중률",
        "definition": "요청된 데이터가 캐시에서 찾아지는 비율. 높은 적중률(>90%)은 빠른 응답 시간을 의미합니다.",
        "example": "L1 Redis 캐시 적중률이 95%라면, 100번 요청 중 95번은 <5ms 내에 응답됩니다.",
        "category": "데이터 인프라",
        "related_terms": ["Redis", "Latency", "Cache Miss", "TTL"]
    },
    
    # AI Factors
    {
        "term": "Management Credibility Score",
        "term_kr": "경영진 신뢰도 점수",
        "definition": "CEO 재임 기간, 실적 발표 감성, 내부자 거래 패턴 등을 종합하여 경영진의 신뢰성을 평가하는 AI 팩터.",
        "example": "CEO가 5년 이상 재직하고, 최근 실적 발표가 긍정적이며, 내부자 매수가 많다면 높은 신뢰도 점수를 받습니다.",
        "category": "AI 팩터",
        "related_terms": ["Insider Trading", "Earnings Call", "CEO Tenure"]
    },
    {
        "term": "Supply Chain Risk",
        "term_kr": "공급망 리스크",
        "definition": "기업의 공급망에서 발생할 수 있는 위험을 분석하는 팩터. 주요 공급업체의 지정학적 위치, 재무 상태 등을 평가합니다.",
        "example": "Apple의 주요 부품이 대만에서 생산된다면, 지정학적 리스크가 높게 평가됩니다.",
        "category": "AI 팩터",
        "related_terms": ["Geopolitical Risk", "Supplier Concentration", "Operational Risk"]
    },
    {
        "term": "Non-Standard Risk",
        "term_kr": "비정형 리스크",
        "definition": "전통적인 재무 분석으로 포착하기 어려운 위험 요소. 법적 리스크, 규제 변화, 운영 이슈 등을 뉴스와 공시에서 추출합니다.",
        "example": "최근 뉴스에서 집단 소송, FDA 승인 거부, 공장 화재 등의 키워드가 발견되면 비정형 리스크가 높아집니다.",
        "category": "AI 팩터",
        "related_terms": ["Legal Risk", "Regulatory Risk", "Operational Risk", "Reputational Risk"]
    },
    
    # Performance Metrics
    {
        "term": "Sharpe Ratio",
        "term_kr": "샤프 비율",
        "definition": "위험 대비 초과 수익을 측정하는 지표. (수익률 - 무위험수익률) / 표준편차로 계산하며, 높을수록 위험 대비 수익이 좋습니다.",
        "example": "샤프 비율이 2.0이면 변동성 1단위당 2단위의 초과 수익을 얻는 것으로, 매우 우수한 성과입니다.",
        "category": "성과 측정",
        "related_terms": ["Risk-Adjusted Return", "Sortino Ratio", "Information Ratio"]
    },
    {
        "term": "Win Rate",
        "term_kr": "승률",
        "definition": "총 거래 중 수익을 낸 거래의 비율. 50% 이상이면 절반 이상의 거래에서 수익을 얻는 것입니다.",
        "example": "100번 거래 중 60번이 수익이면 승률 60%입니다. 높은 승률이 항상 좋은 것은 아니며, 손익비도 고려해야 합니다.",
        "category": "성과 측정",
        "related_terms": ["Risk-Reward Ratio", "Profit Factor", "Average Win/Loss"]
    },
    {
        "term": "Cost-Adjusted Sharpe",
        "term_kr": "비용 조정 샤프",
        "definition": "API 비용을 고려하여 조정한 샤프 비율. AI 모델의 실제 비용 대비 성과를 평가하는 데 사용됩니다.",
        "example": "Claude Haiku의 Cost-Adjusted Sharpe가 Sonnet보다 3.4배 높다면, Haiku가 비용 대비 더 효율적입니다.",
        "category": "성과 측정",
        "related_terms": ["Sharpe Ratio", "Cost Efficiency", "ROI"]
    },
    
    # Fundamental Analysis
    {
        "term": "P/E Ratio",
        "term_kr": "주가수익비율",
        "definition": "주가를 주당순이익(EPS)으로 나눈 값. 기업의 수익성 대비 주가가 얼마나 비싼지를 나타내는 가치평가 지표입니다.",
        "example": "AAPL의 P/E가 32.5배이고 산업 평균이 25배라면, 시장은 Apple의 성장성을 높게 평가하고 있는 것입니다.",
        "category": "펀더멘털 분석",
        "related_terms": ["EPS", "PEG Ratio", "P/B Ratio", "Valuation"]
    },
    {
        "term": "EPS (Earnings Per Share)",
        "term_kr": "주당순이익",
        "definition": "순이익을 발행주식수로 나눈 값. 주주 1주당 얼마의 이익이 귀속되는지를 나타냅니다.",
        "example": "순이익이 $10억이고 발행주식이 1억 주라면, EPS는 $10입니다.",
        "category": "펀더멘털 분석",
        "related_terms": ["P/E Ratio", "Diluted EPS", "EPS Growth"]
    },
    
    # Strategy
    {
        "term": "Core-Satellite Strategy",
        "term_kr": "코어-위성 전략",
        "definition": "포트폴리오의 핵심(Core)은 안정적인 장기 투자로, 위성(Satellite)은 적극적인 단기 기회로 구성하는 전략.",
        "example": "Core 70%는 우량주 장기 보유, Satellite 30%는 이벤트 드리븐 단기 매매로 구성합니다.",
        "category": "투자 전략",
        "related_terms": ["Asset Allocation", "Diversification", "Active/Passive"]
    },
    {
        "term": "Event-Driven Strategy",
        "term_kr": "이벤트 드리븐 전략",
        "definition": "기업 공시, 합병, 실적 발표 등 특정 이벤트에 기반한 투자 전략.",
        "example": "실적 발표 전 옵션 매수, M&A 발표 후 차익 거래 등이 이벤트 드리븐 전략의 예입니다.",
        "category": "투자 전략",
        "related_terms": ["Catalyst", "Alpha Generation", "Market Timing"]
    },
    {
        "term": "Kelly Criterion",
        "term_kr": "켈리 공식",
        "definition": "승률과 손익비를 기반으로 최적의 베팅 크기를 계산하는 수학적 공식. 장기 자본 성장을 최대화합니다.",
        "example": "승률 60%, 평균 손익비 2:1이면 켈리 공식은 포트폴리오의 40%를 베팅하라고 제안하지만, 일반적으로 절반(Half Kelly)을 사용합니다.",
        "category": "투자 전략",
        "related_terms": ["Position Sizing", "Risk Management", "Optimal f"]
    },
    {
        "term": "Mean-CVaR Optimization",
        "term_kr": "평균-CVaR 최적화",
        "definition": "기대 수익률과 조건부 가치위험(CVaR)을 최적화하는 포트폴리오 구성 방법. 극단적 손실을 방지합니다.",
        "example": "95% CVaR이 -5%라는 것은, 최악의 5% 상황에서 평균 손실이 -5%임을 의미합니다.",
        "category": "투자 전략",
        "related_terms": ["VaR", "Tail Risk", "Portfolio Optimization", "Modern Portfolio Theory"]
    },
]


# ============================================================================
# Trading Terms Parser Class
# ============================================================================

class TradingTermsParser:
    """
    Trading Terms Dictionary Parser
    
    MASTER_GUIDE.md에서 용어를 추출하거나 사전 정의된 용어를 제공합니다.
    """
    
    def __init__(self, master_guide_path: Optional[str] = None):
        """
        Args:
            master_guide_path: MASTER_GUIDE.md 파일 경로 (선택적)
        """
        self.master_guide_path = master_guide_path
        self.terms = TRADING_TERMS
        
        # 카테고리 추출
        self.categories = list(set(term["category"] for term in self.terms))
        self.categories.sort()
    
    def get_all_terms(self) -> List[Dict[str, Any]]:
        """모든 용어 반환"""
        return self.terms
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 반환"""
        return self.categories
    
    def search_terms(
        self,
        query: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        용어 검색
        
        Args:
            query: 검색어 (영문 또는 한글)
            category: 카테고리 필터 (선택적)
        """
        query_lower = query.lower()
        results = []
        
        for term in self.terms:
            # 카테고리 필터
            if category and term["category"] != category:
                continue
            
            # 검색어 매칭
            if (
                query_lower in term["term"].lower() or
                query in term["term_kr"] or
                query_lower in term["definition"].lower() or
                query in term["definition"]
            ):
                results.append(term)
        
        return results
    
    def get_term_by_name(self, term_name: str) -> Optional[Dict[str, Any]]:
        """용어명으로 검색"""
        for term in self.terms:
            if term["term"] == term_name or term["term_kr"] == term_name:
                return term
        return None
    
    def get_terms_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 용어 조회"""
        return [term for term in self.terms if term["category"] == category]
    
    def get_related_terms(self, term_name: str) -> List[Dict[str, Any]]:
        """연관 용어 조회"""
        term = self.get_term_by_name(term_name)
        if not term:
            return []
        
        related = []
        for related_name in term.get("related_terms", []):
            related_term = self.get_term_by_name(related_name)
            if related_term:
                related.append(related_term)
        
        return related
    
    @staticmethod
    def parse_master_guide(file_path: str) -> List[Dict[str, Any]]:
        """
        MASTER_GUIDE.md에서 용어 자동 추출 (고급 기능)
        
        실제 구현시에는 NLP를 사용하여 문서에서 용어를 자동으로 추출할 수 있습니다.
        현재는 사전 정의된 용어를 사용합니다.
        """
        # TODO: 실제 파싱 로직 구현
        # - 코드 블록 분석
        # - 헤더 구조 분석
        # - 정의 패턴 검색
        return TRADING_TERMS


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    parser = TradingTermsParser()
    
    print("📚 Trading Terms Dictionary")
    print(f"Total terms: {len(parser.get_all_terms())}")
    print(f"Categories: {parser.get_categories()}")
    
    # 검색 테스트
    print("\n🔍 Search 'Stop Loss':")
    results = parser.search_terms("Stop Loss")
    for r in results:
        print(f"  - {r['term_kr']} ({r['term']})")
    
    print("\n🔍 Search '확신' (Korean):")
    results = parser.search_terms("확신")
    for r in results:
        print(f"  - {r['term_kr']} ({r['term']})")
    
    print("\n📂 Category '리스크 관리':")
    terms = parser.get_terms_by_category("리스크 관리")
    for t in terms:
        print(f"  - {t['term_kr']}")
    
    print("\n🔗 Related terms for 'Kill Switch':")
    related = parser.get_related_terms("Kill Switch")
    for r in related:
        print(f"  - {r['term_kr']}")
