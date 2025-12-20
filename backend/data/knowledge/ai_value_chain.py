"""
AIValueChainGraph - AI 반도체 밸류체인 Knowledge Graph

AI 칩 시장의 회사 관계, 시장 세그먼트, 공급망을 그래프로 표현하여
뉴스 분석 시 숨겨진 수혜자를 찾는다.

핵심 인사이트:
"Google TPU 발표 → Broadcom이 숨겨진 승자 (TPU 설계 파트너)"

사용 예시:
- Google TPU 뉴스 → "GOOGL + AVGO Long" 시그널
- NVIDIA H200 발표 → "NVDA Long, AMD 영향 분석" 시그널
- AMD MI300 출시 → "AMD Long, NVDA Training 유지" 시그널

비용: $0/월 (룰 기반 그래프)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

# Import BaseSchema
from backend.schemas.base_schema import (
    SupplyChainEdge,
    RelationType,
    MarketSegment
)

logger = logging.getLogger(__name__)


@dataclass
class Company:
    """회사 노드"""
    ticker: str
    name: str
    segments: List[MarketSegment] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    market_share: Dict[str, float] = field(default_factory=dict)  # segment -> share
    strength_score: float = 0.5  # 0.0 ~ 1.0
    notes: str = ""


@dataclass
class Relationship:
    """회사 간 관계 엣지 (내부 사용)"""
    from_ticker: str
    to_ticker: str
    relation_type: RelationType
    strength: float = 0.5  # 0.0 ~ 1.0
    context: str = ""

    def to_supply_chain_edge(self) -> SupplyChainEdge:
        """BaseSchema SupplyChainEdge로 변환"""
        return SupplyChainEdge(
            source=self.from_ticker,
            target=self.to_ticker,
            relation=self.relation_type,
            confidence=self.strength
        )


class AIValueChainGraph:
    """
    AI 반도체 밸류체인 Knowledge Graph

    주요 기능:
    1. 회사 간 관계 그래프 관리
    2. 뉴스에서 수혜 회사 추론
    3. Training vs Inference 시장 세그먼트 분석

    Phase 0 통합:
    - SupplyChainEdge 출력
    - MarketSegment Enum 사용
    """

    def __init__(self):
        """그래프 초기화"""
        self.companies: Dict[str, Company] = {}
        self.relationships: List[Relationship] = []
        self._build_default_graph()

    def _build_default_graph(self):
        """기본 AI 밸류체인 그래프 구축"""

        # =====================================================================
        # 회사 노드 정의
        # =====================================================================

        # NVIDIA
        self.add_company(Company(
            ticker="NVDA",
            name="NVIDIA",
            segments=[MarketSegment.TRAINING, MarketSegment.TRAINING],  # Dominant in training
            products=["H100", "H200", "B200", "Blackwell", "CUDA"],
            market_share={"training": 0.85, "inference": 0.60},
            strength_score=0.95,
            notes="AI 칩 시장 지배자, CUDA 생태계 lock-in"
        ))

        # Google (Alphabet)
        self.add_company(Company(
            ticker="GOOGL",
            name="Google/Alphabet",
            segments=[MarketSegment.INFERENCE, MarketSegment.TRAINING],
            products=["TPU v5p", "TPU v6e", "Gemini"],
            market_share={"training": 0.08, "inference": 0.35},
            strength_score=0.80,
            notes="자체 TPU로 Inference 시장 강세, Google Cloud 전용"
        ))

        # Broadcom (TPU 설계 파트너)
        self.add_company(Company(
            ticker="AVGO",
            name="Broadcom",
            segments=[MarketSegment.INFERENCE],
            products=["TPU ASIC Design", "Custom Silicon"],
            market_share={"inference": 0.20},
            strength_score=0.75,
            notes="Google TPU 설계 파트너, 숨겨진 수혜자"
        ))

        # AMD
        self.add_company(Company(
            ticker="AMD",
            name="AMD",
            segments=[MarketSegment.INFERENCE, MarketSegment.TRAINING],
            products=["MI300X", "MI325X", "CDNA3", "ROCm"],
            market_share={"training": 0.05, "inference": 0.15},
            strength_score=0.65,
            notes="NVIDIA 대항마, ROCm 생태계 성장 중"
        ))

        # Intel
        self.add_company(Company(
            ticker="INTC",
            name="Intel",
            segments=[MarketSegment.INFERENCE],
            products=["Gaudi 3", "Habana"],
            market_share={"training": 0.02, "inference": 0.05},
            strength_score=0.40,
            notes="AI 칩 후발주자, 소프트웨어 생태계 약점"
        ))

        # TSMC (파운드리)
        self.add_company(Company(
            ticker="TSM",
            name="TSMC",
            segments=[MarketSegment.TRAINING, MarketSegment.INFERENCE],  # Both
            products=["N3", "N4", "CoWoS"],
            market_share={"manufacturing": 0.90},
            strength_score=0.90,
            notes="NVIDIA/AMD/Apple 칩 제조, AI 칩 공급 병목"
        ))

        # Microsoft (클라우드 고객)
        self.add_company(Company(
            ticker="MSFT",
            name="Microsoft",
            segments=[MarketSegment.TRAINING, MarketSegment.INFERENCE],
            products=["Azure", "Copilot", "Maia"],
            market_share={"cloud_ai": 0.25},
            strength_score=0.85,
            notes="NVIDIA 최대 고객, 자체 칩(Maia) 개발 중"
        ))

        # Amazon (클라우드 고객)
        self.add_company(Company(
            ticker="AMZN",
            name="Amazon",
            segments=[MarketSegment.INFERENCE],
            products=["AWS", "Trainium", "Inferentia"],
            market_share={"cloud_ai": 0.30},
            strength_score=0.80,
            notes="자체 칩 개발로 NVIDIA 의존도 감소 시도"
        ))

        # =====================================================================
        # 관계 엣지 정의
        # =====================================================================

        # 경쟁 관계
        self.add_relationship(Relationship(
            "NVDA", "AMD", RelationType.COMPETITOR, 0.8, "GPU 시장 경쟁"
        ))
        self.add_relationship(Relationship(
            "NVDA", "GOOGL", RelationType.COMPETITOR, 0.6, "Training 시장 경쟁"
        ))
        self.add_relationship(Relationship(
            "AMD", "INTC", RelationType.COMPETITOR, 0.7, "x86 및 AI 칩 경쟁"
        ))

        # 공급 관계
        self.add_relationship(Relationship(
            "TSM", "NVDA", RelationType.SUPPLIER, 0.95, "H100/H200/B200 제조"
        ))
        self.add_relationship(Relationship(
            "TSM", "AMD", RelationType.SUPPLIER, 0.90, "MI300X/MI325X 제조"
        ))
        self.add_relationship(Relationship(
            "TSM", "GOOGL", RelationType.SUPPLIER, 0.85, "TPU 제조"
        ))

        # 설계 파트너
        self.add_relationship(Relationship(
            "AVGO", "GOOGL", RelationType.PARTNER, 0.90, "TPU ASIC 설계"
        ))

        # 고객 관계
        self.add_relationship(Relationship(
            "MSFT", "NVDA", RelationType.CUSTOMER, 0.90, "Azure GPU 클러스터"
        ))
        self.add_relationship(Relationship(
            "AMZN", "NVDA", RelationType.CUSTOMER, 0.80, "AWS GPU 인스턴스"
        ))
        self.add_relationship(Relationship(
            "GOOGL", "NVDA", RelationType.CUSTOMER, 0.60, "GCP 일부 서비스"
        ))

    def add_company(self, company: Company):
        """회사 노드 추가"""
        self.companies[company.ticker] = company

    def add_relationship(self, relationship: Relationship):
        """관계 엣지 추가"""
        self.relationships.append(relationship)

    def get_company(self, ticker: str) -> Optional[Company]:
        """티커로 회사 조회"""
        return self.companies.get(ticker)

    def get_supply_chain_edges(self, ticker: Optional[str] = None) -> List[SupplyChainEdge]:
        """
        공급망 엣지를 BaseSchema 형식으로 반환

        Args:
            ticker: 특정 티커만 필터 (None이면 전체)

        Returns:
            SupplyChainEdge 리스트
        """
        edges = []

        for rel in self.relationships:
            if ticker and rel.from_ticker != ticker and rel.to_ticker != ticker:
                continue

            edges.append(rel.to_supply_chain_edge())

        return edges

    def get_related_companies(
        self,
        ticker: str,
        relation_types: Optional[List[RelationType]] = None
    ) -> List[Tuple[str, Relationship]]:
        """
        특정 회사와 관련된 모든 회사 조회

        Args:
            ticker: 기준 회사 티커
            relation_types: 필터링할 관계 유형 (None이면 모두)

        Returns:
            [(관련 티커, Relationship), ...]
        """
        related = []

        for rel in self.relationships:
            if relation_types and rel.relation_type not in relation_types:
                continue

            if rel.from_ticker == ticker:
                related.append((rel.to_ticker, rel))
            elif rel.to_ticker == ticker:
                related.append((rel.from_ticker, rel))

        return related

    def find_beneficiaries(
        self,
        news_ticker: str,
        news_sentiment: str = "positive"
    ) -> Dict[str, Any]:
        """
        뉴스 티커에서 수혜/피해 회사 추론

        Args:
            news_ticker: 뉴스 주인공 티커
            news_sentiment: "positive" | "negative"

        Returns:
            {
                "direct_beneficiaries": ["NVDA"],
                "indirect_beneficiaries": ["TSM", "AVGO"],
                "negatively_affected": ["AMD"],
                "rationale": "..."
            }
        """
        company = self.get_company(news_ticker)
        if not company:
            return {
                "error": f"Unknown ticker: {news_ticker}",
                "direct_beneficiaries": [],
                "indirect_beneficiaries": [],
                "negatively_affected": []
            }

        direct_beneficiaries = []
        indirect_beneficiaries = []
        negatively_affected = []
        rationales = []

        # 긍정적 뉴스의 경우
        if news_sentiment == "positive":
            # 본인 수혜
            direct_beneficiaries.append(news_ticker)
            rationales.append(f"{news_ticker} directly benefits from positive news")

            # 공급자 수혜 (TSMC 등)
            suppliers = self.get_related_companies(
                news_ticker,
                [RelationType.SUPPLIER]
            )
            for supplier_ticker, rel in suppliers:
                if rel.to_ticker == news_ticker:  # 공급받는 관계
                    indirect_beneficiaries.append(supplier_ticker)
                    rationales.append(f"{supplier_ticker} benefits as supplier to {news_ticker}")

            # 설계 파트너 수혜 (Broadcom-Google 등)
            design_partners = self.get_related_companies(
                news_ticker,
                [RelationType.PARTNER]
            )
            for partner_ticker, rel in design_partners:
                if rel.to_ticker == news_ticker:  # 설계해주는 관계
                    indirect_beneficiaries.append(partner_ticker)
                    rationales.append(f"{partner_ticker} benefits as design partner of {news_ticker}")

            # 경쟁자 피해
            competitors = self.get_related_companies(
                news_ticker,
                [RelationType.COMPETITOR]
            )
            for competitor_ticker, rel in competitors:
                negatively_affected.append(competitor_ticker)
                rationales.append(f"{competitor_ticker} may be negatively affected as competitor")

        # 부정적 뉴스의 경우
        elif news_sentiment == "negative":
            # 본인 피해
            negatively_affected.append(news_ticker)
            rationales.append(f"{news_ticker} directly affected by negative news")

            # 경쟁자 수혜
            competitors = self.get_related_companies(
                news_ticker,
                [RelationType.COMPETITOR]
            )
            for competitor_ticker, rel in competitors:
                direct_beneficiaries.append(competitor_ticker)
                rationales.append(f"{competitor_ticker} may benefit as competitor of struggling {news_ticker}")

            # 고객 영향 (공급 문제면 피해)
            customers = self.get_related_companies(
                news_ticker,
                [RelationType.CUSTOMER]
            )
            for customer_ticker, rel in customers:
                if rel.to_ticker == news_ticker:  # 고객인 관계
                    negatively_affected.append(customer_ticker)
                    rationales.append(f"{customer_ticker} may be affected as customer")

        # 중복 제거
        direct_beneficiaries = list(set(direct_beneficiaries))
        indirect_beneficiaries = list(set(indirect_beneficiaries) - set(direct_beneficiaries))
        negatively_affected = list(set(negatively_affected))

        return {
            "news_ticker": news_ticker,
            "news_sentiment": news_sentiment,
            "direct_beneficiaries": direct_beneficiaries,
            "indirect_beneficiaries": indirect_beneficiaries,
            "negatively_affected": negatively_affected,
            "rationale": "; ".join(rationales),
            "analyzed_at": datetime.now().isoformat()
        }

    def get_segment_leaders(self, segment: MarketSegment) -> List[Tuple[str, float]]:
        """
        특정 시장 세그먼트의 리더 순위

        Returns:
            [(티커, market_share), ...] 내림차순
        """
        leaders = []
        segment_key = segment.value

        for ticker, company in self.companies.items():
            if segment in company.segments:
                share = company.market_share.get(segment_key, 0)
                leaders.append((ticker, share))

        return sorted(leaders, key=lambda x: -x[1])

    def get_supply_chain(self, ticker: str) -> Dict[str, List[str]]:
        """
        특정 회사의 공급망 분석

        Returns:
            {
                "suppliers": ["TSM"],
                "customers": ["MSFT", "AMZN"],
                "design_partners": [],
                "competitors": ["AMD"]
            }
        """
        supply_chain = {
            "suppliers": [],
            "customers": [],
            "design_partners": [],
            "competitors": []
        }

        for rel in self.relationships:
            if rel.from_ticker == ticker:
                if rel.relation_type == RelationType.COMPETITOR:
                    supply_chain["competitors"].append(rel.to_ticker)
            elif rel.to_ticker == ticker:
                if rel.relation_type == RelationType.SUPPLIER:
                    supply_chain["suppliers"].append(rel.from_ticker)
                elif rel.relation_type == RelationType.CUSTOMER:
                    supply_chain["customers"].append(rel.from_ticker)
                elif rel.relation_type == RelationType.PARTNER:
                    supply_chain["design_partners"].append(rel.from_ticker)

        return supply_chain


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    graph = AIValueChainGraph()

    print("=" * 70)
    print("AI Value Chain Knowledge Graph Demo")
    print("=" * 70)

    # 1. 회사 정보 조회
    print("\n### Company Information ###")
    for ticker in ["NVDA", "GOOGL", "AVGO"]:
        company = graph.get_company(ticker)
        if company:
            print(f"\n{company.name} ({company.ticker})")
            print(f"  Products: {', '.join(company.products[:3])}")
            print(f"  Strength Score: {company.strength_score:.2f}")
            print(f"  Notes: {company.notes}")

    # 2. 뉴스 수혜 분석
    print("\n### News Beneficiary Analysis ###")

    # 시나리오 1: Google TPU 긍정 뉴스
    result = graph.find_beneficiaries("GOOGL", "positive")
    print(f"\n[Scenario] Google TPU v6e Launch - 50% Performance Boost")
    print(f"  Direct Beneficiaries: {result['direct_beneficiaries']}")
    print(f"  Indirect Beneficiaries: {result['indirect_beneficiaries']}")
    print(f"  Negatively Affected: {result['negatively_affected']}")

    # 시나리오 2: NVIDIA 부정 뉴스
    result = graph.find_beneficiaries("NVDA", "negative")
    print(f"\n[Scenario] NVIDIA B200 Launch Delayed")
    print(f"  Direct Beneficiaries: {result['direct_beneficiaries']}")
    print(f"  Indirect Beneficiaries: {result['indirect_beneficiaries']}")
    print(f"  Negatively Affected: {result['negatively_affected']}")

    # 3. 시장 세그먼트 리더
    print("\n### Market Segment Leaders ###")

    training_leaders = graph.get_segment_leaders(MarketSegment.TRAINING)
    print(f"\n[Training Market]")
    for ticker, share in training_leaders[:3]:
        print(f"  {ticker}: {share:.0%}")

    inference_leaders = graph.get_segment_leaders(MarketSegment.INFERENCE)
    print(f"\n[Inference Market]")
    for ticker, share in inference_leaders[:3]:
        print(f"  {ticker}: {share:.0%}")

    # 4. 공급망 분석
    print("\n### NVIDIA Supply Chain ###")
    supply_chain = graph.get_supply_chain("NVDA")
    print(f"  Suppliers: {supply_chain['suppliers']}")
    print(f"  Customers: {supply_chain['customers']}")
    print(f"  Competitors: {supply_chain['competitors']}")

    # 5. BaseSchema 통합 테스트
    print("\n### BaseSchema Integration Test ###")
    edges = graph.get_supply_chain_edges("NVDA")
    print(f"\nSupply Chain Edges for NVDA: {len(edges)}")
    for edge in edges[:3]:
        print(f"  {edge.source} --[{edge.relation}]--> {edge.target} (confidence: {edge.confidence:.2f})")
