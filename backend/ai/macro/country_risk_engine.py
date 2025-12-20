"""
Country Risk Engine - 국가별 리스크 점수 엔진

Phase F2: 글로벌 매크로 확장

핵심 국가(US, JP, CN, EU)의 매크로 데이터를 수집하고 리스크 점수 산출

주요 기능:
- 국가별 매크로 데이터 스키마
- 리스크 점수 계산 (0-100)
- 크로스 컨트리 비교

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 국가 및 데이터 스키마
# ═══════════════════════════════════════════════════════════════

class Country(str, Enum):
    """핵심 국가"""
    US = "US"   # 미국
    JP = "JP"   # 일본
    CN = "CN"   # 중국
    EU = "EU"   # 유럽
    KR = "KR"   # 한국 (보조)
    

class RiskLevel(str, Enum):
    """리스크 레벨"""
    LOW = "low"           # 0-25
    MODERATE = "moderate" # 25-50
    ELEVATED = "elevated" # 50-75
    HIGH = "high"         # 75-100


@dataclass
class CountryMacroData:
    """국가별 매크로 데이터"""
    country: Country
    as_of_date: date
    
    # 금리
    base_rate: Optional[float] = None       # 기준금리 (%)
    rate_change_ytd: Optional[float] = None # 연초대비 변화
    
    # 채권
    bond_10y: Optional[float] = None        # 10년물 국채 수익률
    bond_2y: Optional[float] = None         # 2년물 국채 수익률
    yield_spread: Optional[float] = None    # 장단기 금리차
    
    # 인플레이션
    cpi_yoy: Optional[float] = None         # 소비자물가 YoY
    ppi_yoy: Optional[float] = None         # 생산자물가 YoY
    core_cpi: Optional[float] = None        # 근원 CPI
    
    # 통화
    currency_index: Optional[float] = None  # 통화 인덱스 (100 기준)
    currency_change_1m: Optional[float] = None  # 1개월 변화율
    
    # 경제 지표
    gdp_growth: Optional[float] = None      # GDP 성장률 YoY
    unemployment: Optional[float] = None    # 실업률
    pmi_manufacturing: Optional[float] = None  # 제조업 PMI
    pmi_services: Optional[float] = None    # 서비스업 PMI
    
    # 시장 지표
    equity_index_level: Optional[float] = None   # 대표 주가지수
    equity_pe_ratio: Optional[float] = None      # PE ratio
    equity_change_ytd: Optional[float] = None    # YTD 변화율
    
    # 메타
    updated_at: datetime = field(default_factory=datetime.now)
    source: str = "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country.value,
            "as_of_date": self.as_of_date.isoformat(),
            "rates": {
                "base_rate": self.base_rate,
                "rate_change_ytd": self.rate_change_ytd,
                "bond_10y": self.bond_10y,
                "bond_2y": self.bond_2y,
                "yield_spread": self.yield_spread
            },
            "inflation": {
                "cpi_yoy": self.cpi_yoy,
                "ppi_yoy": self.ppi_yoy,
                "core_cpi": self.core_cpi
            },
            "currency": {
                "index": self.currency_index,
                "change_1m": self.currency_change_1m
            },
            "economy": {
                "gdp_growth": self.gdp_growth,
                "unemployment": self.unemployment,
                "pmi_manufacturing": self.pmi_manufacturing,
                "pmi_services": self.pmi_services
            },
            "equity": {
                "index_level": self.equity_index_level,
                "pe_ratio": self.equity_pe_ratio,
                "change_ytd": self.equity_change_ytd
            }
        }


@dataclass
class CountryRiskScore:
    """국가별 리스크 점수"""
    country: Country
    as_of_date: date
    
    # 개별 리스크 점수 (0-100)
    interest_rate_risk: float = 50.0
    inflation_risk: float = 50.0
    currency_risk: float = 50.0
    growth_risk: float = 50.0
    equity_risk: float = 50.0
    
    # 종합 리스크
    composite_score: float = 50.0
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # 변화
    score_change_1w: Optional[float] = None
    score_change_1m: Optional[float] = None
    
    # 메타
    confidence: float = 0.8
    factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country.value,
            "as_of_date": self.as_of_date.isoformat(),
            "scores": {
                "interest_rate_risk": self.interest_rate_risk,
                "inflation_risk": self.inflation_risk,
                "currency_risk": self.currency_risk,
                "growth_risk": self.growth_risk,
                "equity_risk": self.equity_risk
            },
            "composite": {
                "score": self.composite_score,
                "level": self.risk_level.value
            },
            "changes": {
                "1w": self.score_change_1w,
                "1m": self.score_change_1m
            },
            "confidence": self.confidence,
            "factors": self.factors
        }


# ═══════════════════════════════════════════════════════════════
# Country Risk Engine 클래스
# ═══════════════════════════════════════════════════════════════

class CountryRiskEngine:
    """
    국가별 리스크 점수 엔진
    
    Usage:
        engine = CountryRiskEngine()
        
        # 매크로 데이터 업데이트
        engine.update_macro_data(Country.US, macro_data)
        
        # 리스크 점수 계산
        score = engine.calculate_risk_score(Country.US)
        
        # 크로스 컨트리 비교
        comparison = engine.compare_countries([Country.US, Country.JP])
    """
    
    # 리스크 계산 가중치
    RISK_WEIGHTS = {
        "interest_rate_risk": 0.25,
        "inflation_risk": 0.20,
        "currency_risk": 0.20,
        "growth_risk": 0.20,
        "equity_risk": 0.15
    }
    
    # 기준값 (정상 범위)
    BENCHMARKS = {
        Country.US: {
            "base_rate": (3.0, 5.5),     # 정상 범위
            "cpi_yoy": (1.5, 3.0),
            "gdp_growth": (2.0, 3.5),
            "unemployment": (3.5, 5.0),
            "bond_10y": (3.0, 5.0)
        },
        Country.JP: {
            "base_rate": (-0.1, 0.5),
            "cpi_yoy": (0.0, 2.5),
            "gdp_growth": (0.5, 2.0),
            "unemployment": (2.0, 3.5),
            "bond_10y": (0.0, 1.5)
        },
        Country.CN: {
            "base_rate": (3.0, 5.0),
            "cpi_yoy": (1.5, 3.5),
            "gdp_growth": (4.5, 6.5),
            "unemployment": (4.0, 6.0),
            "bond_10y": (2.5, 4.0)
        },
        Country.EU: {
            "base_rate": (2.0, 4.5),
            "cpi_yoy": (1.5, 3.0),
            "gdp_growth": (1.0, 2.5),
            "unemployment": (6.0, 8.0),
            "bond_10y": (2.0, 4.0)
        },
        Country.KR: {
            "base_rate": (2.5, 4.0),
            "cpi_yoy": (1.5, 3.0),
            "gdp_growth": (2.0, 3.5),
            "unemployment": (2.5, 4.0),
            "bond_10y": (3.0, 4.5)
        }
    }
    
    def __init__(self):
        """초기화"""
        self._macro_data: Dict[Country, CountryMacroData] = {}
        self._risk_scores: Dict[Country, CountryRiskScore] = {}
        self._history: Dict[Country, List[CountryRiskScore]] = {
            c: [] for c in Country
        }
        
        # 기본 데이터 로드 (샘플)
        self._load_sample_data()
        
        logger.info("CountryRiskEngine initialized")
    
    def _load_sample_data(self):
        """샘플 데이터 로드 (실제로는 API에서 가져옴)"""
        today = date.today()
        
        # 미국
        self._macro_data[Country.US] = CountryMacroData(
            country=Country.US,
            as_of_date=today,
            base_rate=5.25,
            bond_10y=4.25,
            bond_2y=4.60,
            yield_spread=-0.35,
            cpi_yoy=3.2,
            core_cpi=3.8,
            gdp_growth=2.5,
            unemployment=3.9,
            pmi_manufacturing=48.5,
            currency_index=104.5,
            equity_pe_ratio=21.5,
            source="sample"
        )
        
        # 일본
        self._macro_data[Country.JP] = CountryMacroData(
            country=Country.JP,
            as_of_date=today,
            base_rate=0.25,
            bond_10y=0.95,
            bond_2y=0.15,
            yield_spread=0.80,
            cpi_yoy=2.9,
            gdp_growth=1.8,
            unemployment=2.5,
            pmi_manufacturing=49.0,
            currency_index=85.0,  # 엔화 약세
            source="sample"
        )
        
        # 중국
        self._macro_data[Country.CN] = CountryMacroData(
            country=Country.CN,
            as_of_date=today,
            base_rate=3.45,
            bond_10y=2.65,
            cpi_yoy=0.1,  # 디플레이션 우려
            gdp_growth=5.2,
            unemployment=5.2,
            pmi_manufacturing=49.2,
            currency_index=92.0,
            source="sample"
        )
        
        # 유럽
        self._macro_data[Country.EU] = CountryMacroData(
            country=Country.EU,
            as_of_date=today,
            base_rate=4.0,
            bond_10y=2.30,  # 독일 10년물
            cpi_yoy=2.8,
            gdp_growth=0.6,
            unemployment=6.5,
            pmi_manufacturing=45.8,  # 제조업 약세
            currency_index=108.0,
            source="sample"
        )
        
        # 한국
        self._macro_data[Country.KR] = CountryMacroData(
            country=Country.KR,
            as_of_date=today,
            base_rate=3.5,
            bond_10y=3.80,
            cpi_yoy=2.7,
            gdp_growth=2.3,
            unemployment=2.8,
            pmi_manufacturing=50.5,
            currency_index=95.0,
            source="sample"
        )
    
    def update_macro_data(self, country: Country, data: CountryMacroData):
        """매크로 데이터 업데이트"""
        self._macro_data[country] = data
        logger.info(f"Updated macro data for {country.value}")
    
    def get_macro_data(self, country: Country) -> Optional[CountryMacroData]:
        """매크로 데이터 조회"""
        return self._macro_data.get(country)
    
    def calculate_risk_score(self, country: Country) -> CountryRiskScore:
        """
        리스크 점수 계산
        
        Args:
            country: 국가
            
        Returns:
            CountryRiskScore
        """
        data = self._macro_data.get(country)
        if not data:
            return CountryRiskScore(
                country=country,
                as_of_date=date.today(),
                factors=["No data available"]
            )
        
        benchmarks = self.BENCHMARKS.get(country, self.BENCHMARKS[Country.US])
        factors = []
        
        # 1. 금리 리스크
        interest_risk = 50.0
        if data.base_rate is not None:
            low, high = benchmarks.get("base_rate", (2.0, 5.0))
            if data.base_rate > high:
                interest_risk = min(100, 50 + (data.base_rate - high) * 15)
                factors.append(f"High rates ({data.base_rate}%)")
            elif data.base_rate < low:
                interest_risk = max(0, 50 - (low - data.base_rate) * 10)
        
        # 역전된 수익률 곡선
        if data.yield_spread is not None and data.yield_spread < 0:
            interest_risk = min(100, interest_risk + abs(data.yield_spread) * 20)
            factors.append(f"Inverted yield curve ({data.yield_spread:.2f})")
        
        # 2. 인플레이션 리스크
        inflation_risk = 50.0
        if data.cpi_yoy is not None:
            low, high = benchmarks.get("cpi_yoy", (1.5, 3.0))
            if data.cpi_yoy > high:
                inflation_risk = min(100, 50 + (data.cpi_yoy - high) * 12)
                factors.append(f"High inflation ({data.cpi_yoy}%)")
            elif data.cpi_yoy < low:
                if data.cpi_yoy < 0:  # 디플레이션
                    inflation_risk = min(100, 70 + abs(data.cpi_yoy) * 10)
                    factors.append(f"Deflation risk ({data.cpi_yoy}%)")
                else:
                    inflation_risk = max(20, 50 - (low - data.cpi_yoy) * 8)
        
        # 3. 통화 리스크
        currency_risk = 50.0
        if data.currency_index is not None:
            deviation = abs(100 - data.currency_index)
            if deviation > 15:
                currency_risk = min(100, 50 + deviation * 1.5)
                direction = "weak" if data.currency_index < 100 else "strong"
                factors.append(f"Currency {direction} ({data.currency_index})")
        
        if data.currency_change_1m is not None and abs(data.currency_change_1m) > 3:
            currency_risk = min(100, currency_risk + abs(data.currency_change_1m) * 3)
            factors.append(f"Currency volatility ({data.currency_change_1m:.1f}%)")
        
        # 4. 성장 리스크
        growth_risk = 50.0
        if data.gdp_growth is not None:
            low, high = benchmarks.get("gdp_growth", (1.5, 3.0))
            if data.gdp_growth < low:
                growth_risk = min(100, 50 + (low - data.gdp_growth) * 15)
                factors.append(f"Low growth ({data.gdp_growth}%)")
        
        if data.pmi_manufacturing is not None and data.pmi_manufacturing < 50:
            growth_risk = min(100, growth_risk + (50 - data.pmi_manufacturing) * 1.5)
            factors.append(f"Manufacturing contraction (PMI: {data.pmi_manufacturing})")
        
        # 5. 주식 리스크
        equity_risk = 50.0
        if data.equity_pe_ratio is not None:
            if data.equity_pe_ratio > 25:
                equity_risk = min(100, 50 + (data.equity_pe_ratio - 25) * 3)
                factors.append(f"High valuations (P/E: {data.equity_pe_ratio})")
            elif data.equity_pe_ratio < 12:
                equity_risk = max(20, 50 - (12 - data.equity_pe_ratio) * 3)
        
        # 종합 점수 계산
        composite = (
            interest_risk * self.RISK_WEIGHTS["interest_rate_risk"] +
            inflation_risk * self.RISK_WEIGHTS["inflation_risk"] +
            currency_risk * self.RISK_WEIGHTS["currency_risk"] +
            growth_risk * self.RISK_WEIGHTS["growth_risk"] +
            equity_risk * self.RISK_WEIGHTS["equity_risk"]
        )
        
        # 리스크 레벨 결정
        if composite < 25:
            risk_level = RiskLevel.LOW
        elif composite < 50:
            risk_level = RiskLevel.MODERATE
        elif composite < 75:
            risk_level = RiskLevel.ELEVATED
        else:
            risk_level = RiskLevel.HIGH
        
        score = CountryRiskScore(
            country=country,
            as_of_date=data.as_of_date,
            interest_rate_risk=interest_risk,
            inflation_risk=inflation_risk,
            currency_risk=currency_risk,
            growth_risk=growth_risk,
            equity_risk=equity_risk,
            composite_score=composite,
            risk_level=risk_level,
            factors=factors[:5]  # 상위 5개 요인
        )
        
        # 캐시 및 히스토리 저장
        self._risk_scores[country] = score
        self._history[country].append(score)
        
        return score
    
    def get_risk_score(self, country: Country) -> Optional[CountryRiskScore]:
        """캐시된 리스크 점수 조회"""
        return self._risk_scores.get(country)
    
    def calculate_all_scores(self) -> Dict[Country, CountryRiskScore]:
        """모든 국가 리스크 점수 계산"""
        return {
            country: self.calculate_risk_score(country)
            for country in Country
        }
    
    def compare_countries(
        self,
        countries: Optional[List[Country]] = None
    ) -> Dict[str, Any]:
        """
        국가 간 리스크 비교
        
        Args:
            countries: 비교할 국가 목록 (None이면 전체)
            
        Returns:
            비교 결과
        """
        if countries is None:
            countries = list(Country)
        
        scores = {c: self.calculate_risk_score(c) for c in countries}
        
        # 정렬 (낮은 리스크 순)
        sorted_countries = sorted(
            scores.items(),
            key=lambda x: x[1].composite_score
        )
        
        return {
            "ranking": [
                {
                    "rank": i + 1,
                    "country": c.value,
                    "score": s.composite_score,
                    "level": s.risk_level.value,
                    "top_factors": s.factors[:3]
                }
                for i, (c, s) in enumerate(sorted_countries)
            ],
            "lowest_risk": sorted_countries[0][0].value,
            "highest_risk": sorted_countries[-1][0].value,
            "average_score": sum(s.composite_score for s in scores.values()) / len(scores)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """요약 정보"""
        scores = self.calculate_all_scores()
        return {
            "countries_tracked": len(self._macro_data),
            "scores": {
                c.value: {
                    "score": s.composite_score,
                    "level": s.risk_level.value
                }
                for c, s in scores.items()
            },
            "global_average": sum(s.composite_score for s in scores.values()) / len(scores)
        }


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_country_risk_engine: Optional[CountryRiskEngine] = None


def get_country_risk_engine() -> CountryRiskEngine:
    """CountryRiskEngine 싱글톤 인스턴스"""
    global _country_risk_engine
    if _country_risk_engine is None:
        _country_risk_engine = CountryRiskEngine()
    return _country_risk_engine


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = CountryRiskEngine()
    
    print("=== Country Risk Engine Test ===\n")
    
    # 각 국가별 리스크 점수
    for country in Country:
        score = engine.calculate_risk_score(country)
        print(f"\n{country.value}:")
        print(f"  Composite Score: {score.composite_score:.1f}")
        print(f"  Risk Level: {score.risk_level.value}")
        print(f"  Key Factors: {score.factors}")
    
    # 국가 간 비교
    print("\n" + "="*60)
    print("Country Comparison:")
    print("="*60)
    comparison = engine.compare_countries()
    for item in comparison["ranking"]:
        emoji = "🟢" if item["level"] == "low" else "🟡" if item["level"] == "moderate" else "🟠" if item["level"] == "elevated" else "🔴"
        print(f"  {item['rank']}. {emoji} {item['country']}: {item['score']:.1f} ({item['level']})")
    
    print(f"\nLowest Risk: {comparison['lowest_risk']}")
    print(f"Highest Risk: {comparison['highest_risk']}")
    print(f"Global Average: {comparison['average_score']:.1f}")
