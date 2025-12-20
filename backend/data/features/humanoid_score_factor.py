"""
Humanoid Robot Score Factor

전기차 기업의 휴머노이드 로봇 사업 진출 평가

핵심 인사이트 (사용자 제공 이미지 기반):
"휴머노이드 로봇 개발 경쟁의 본질은 '전기차 대량생산 역량'과 동일하다"

평가 기준:
1. AI 학습 데이터 재활용 (자율주행 → 로봇)
2. 핵심 부품 내재화 (배터리, 모터, SoC)
3. 대량 생산 노하우 (설비, 공급망, 인력)

대상 기업:
- Tesla (Optimus)
- BYD (중국 대학 협력)
- Xpeng (자체 AI칩 3개)
- Figure AI, Boston Dynamics 등 스타트업

비용: $0/월 (룰 기반) 또는 $0.0013/분석 (Claude API)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# 휴머노이드 생태계 구성 요소 (이미지 기반)
# =============================================================================

HUMANOID_ECOSYSTEM = {
    "ai_computation": {
        "name": "AI 연산 능력",
        "description": "수많은 센서(카메라, LiDAR등)를 실시간으로 처리하는 AI 연산 능력",
        "weight": 0.25,
        "key_technologies": ["SoC", "AI칩", "엣지 컴퓨팅", "신경망 처리"],
    },
    "control_system": {
        "name": "실시간 제어 시스템",
        "description": "관절 구동/모터 제어/전력관리 등 실시간 제어 시스템",
        "weight": 0.20,
        "key_technologies": ["모션 제어", "관절 구동", "전력 관리", "센서 융합"],
    },
    "battery_design": {
        "name": "저전력 설계",
        "description": "배터리 기반으로 작동하므로 저전력 설계 필수",
        "weight": 0.20,
        "key_technologies": ["배터리 셀", "전력 효율", "열 관리", "충전 시스템"],
    },
    "soc_integration": {
        "name": "고집적 SoC",
        "description": "공간 제약과 발열 제약이 크므로 고집적 SoC(System on Chip)",
        "weight": 0.20,
        "key_technologies": ["SoC 설계", "칩 내재화", "ASIC", "NPU"],
    },
    "software_ecosystem": {
        "name": "소프트웨어 생태계",
        "description": "소프트웨어 알고리즘(AI, 모션플래닝, 비전 등)을 구현 가능한 생태계",
        "weight": 0.15,
        "key_technologies": ["AI 프레임워크", "모션 플래닝", "컴퓨터 비전", "시뮬레이션"],
    },
}


# =============================================================================
# 휴머노이드 기업 프로파일
# =============================================================================

HUMANOID_COMPANIES = {
    # ========== 전기차 기업 (높은 점수) ==========
    "TSLA": {
        "name": "Tesla (Optimus)",
        "category": "ev_manufacturer",
        "humanoid_project": "Optimus Gen 2",
        
        # 이미지 기반 데이터
        "ai_data_reuse": 0.95,  # 자율주행 학습 데이터 = 휴머노이드 시각, 행동 학습 재활용
        "component_internalization": 0.90,  # 배터리 셀, 모터, 인버터, SoC까지 자체 설계
        "mass_production_capability": 0.95,  # 설비라인, 공급망, 인력 그대로 이용
        
        "key_strengths": [
            "FSD 자율주행 데이터 재활용",
            "배터리 셀/모터/인버터/SoC 자체 설계",
            "기존 EV 생산라인 활용",
            "로봇 스타트업보다 70% 저렴한 생산 단가",
        ],
        "weaknesses": [
            "아직 대량 생산 미실현",
            "소프트웨어 안정성 검증 필요",
        ],
        "estimated_production_cost": 0.30,  # 스타트업 대비 70% 절감
        "market_readiness": 0.70,
    },
    
    "BYD": {
        "name": "BYD (중국 대학 협력)",
        "category": "ev_manufacturer",
        "humanoid_project": "University Partnership",
        
        "ai_data_reuse": 0.60,  # 자율주행 데이터 있지만 Tesla보다 적음
        "component_internalization": 0.95,  # 셀, 모듈, 차체까지 95% 내재화
        "mass_production_capability": 0.90,
        
        "key_strengths": [
            "95% 부품 내재화율 (업계 최고)",
            "중국 대학 및 연구기관과 촉각 인식 기술 협력",
            "저가 대량생산 노하우",
        ],
        "weaknesses": [
            "서방 시장 진출 규제 리스크",
            "AI 소프트웨어 역량 Tesla 대비 부족",
        ],
        "estimated_production_cost": 0.35,
        "market_readiness": 0.55,
    },
    
    "XPEV": {
        "name": "Xpeng",
        "category": "ev_manufacturer",
        "humanoid_project": "Iron Robot",
        
        "ai_data_reuse": 0.75,  # 영상 입력 → 행동 명령으로 직접 연결 + 자체 AI칩 3개 탑재
        "component_internalization": 0.70,
        "mass_production_capability": 0.65,
        
        "key_strengths": [
            "자체 AI칩 3개 탑재",
            "영상 입력 → 행동 명령 직접 연결",
            "자율주행 데이터로 로봇 학습",
        ],
        "weaknesses": [
            "생산 규모 BYD/Tesla 대비 작음",
            "글로벌 공급망 제한",
        ],
        "estimated_production_cost": 0.45,
        "market_readiness": 0.50,
    },
    
    # ========== 로봇 스타트업 (낮은 점수) ==========
    "FIGURE": {
        "name": "Figure AI",
        "category": "startup",
        "humanoid_project": "Figure 01",
        
        "ai_data_reuse": 0.40,  # 자체 데이터만
        "component_internalization": 0.20,  # OEM/ODM 의존
        "mass_production_capability": 0.15,
        
        "key_strengths": [
            "순수 휴머노이드 전문",
            "OpenAI 파트너십",
        ],
        "weaknesses": [
            "OEM/ODM 의존 → 가격 경쟁 불리",
            "대량생산 인프라 부재",
            "높은 생산 단가",
        ],
        "estimated_production_cost": 1.00,  # 기준 (가장 비쌈)
        "market_readiness": 0.30,
    },
    
    "BOSTON_DYNAMICS": {
        "name": "Boston Dynamics (Hyundai)",
        "category": "robotics",
        "humanoid_project": "Atlas",
        
        "ai_data_reuse": 0.30,
        "component_internalization": 0.50,  # 현대차 인수 후 개선
        "mass_production_capability": 0.40,
        
        "key_strengths": [
            "세계 최고 수준 로봇 역학",
            "현대차 생산 역량 활용 가능",
        ],
        "weaknesses": [
            "상업화 실적 부족",
            "높은 R&D 비용",
        ],
        "estimated_production_cost": 0.80,
        "market_readiness": 0.45,
    },
}


# =============================================================================
# 휴머노이드 스코어 계산기
# =============================================================================

class HumanoidScoreCalculator:
    """
    휴머노이드 로봇 사업 진출 점수 계산기
    
    평가 요소:
    1. AI 데이터 재활용 (25%)
    2. 부품 내재화율 (35%)
    3. 대량생산 역량 (25%)
    4. 시장 준비도 (15%)
    
    비용: $0/월 (룰 기반)
    """
    
    def __init__(self):
        self.companies = HUMANOID_COMPANIES
        self.ecosystem = HUMANOID_ECOSYSTEM
    
    def calculate_humanoid_score(
        self,
        ticker: str,
    ) -> Dict[str, Any]:
        """
        특정 기업의 휴머노이드 스코어 계산
        
        Args:
            ticker: 종목 티커
            
        Returns:
            {
                "score": 0.0 ~ 1.0,
                "components": {...},
                "strengths": [...],
                "weaknesses": [...],
                "investment_recommendation": str,
            }
        """
        if ticker not in self.companies:
            return self._handle_unknown_ticker(ticker)
        
        company = self.companies[ticker]
        
        # 구성 요소별 점수
        ai_score = company["ai_data_reuse"]
        internalization_score = company["component_internalization"]
        production_score = company["mass_production_capability"]
        readiness_score = company["market_readiness"]
        
        # 비용 효율성 (낮을수록 좋음)
        cost_efficiency = 1.0 - company["estimated_production_cost"]
        
        # 가중 평균
        # 부품 내재화가 가장 중요 (이미지 핵심 인사이트)
        weighted_score = (
            ai_score * 0.25 +
            internalization_score * 0.35 +
            production_score * 0.25 +
            readiness_score * 0.10 +
            cost_efficiency * 0.05
        )
        
        # 투자 권고
        recommendation = self._generate_recommendation(weighted_score, company)
        
        return {
            "ticker": ticker,
            "company_name": company["name"],
            "category": company["category"],
            "project": company["humanoid_project"],
            "score": weighted_score,
            "components": {
                "ai_data_reuse": ai_score,
                "component_internalization": internalization_score,
                "mass_production_capability": production_score,
                "market_readiness": readiness_score,
                "cost_efficiency": cost_efficiency,
            },
            "strengths": company["key_strengths"],
            "weaknesses": company["weaknesses"],
            "estimated_production_cost": company["estimated_production_cost"],
            "investment_recommendation": recommendation,
            "calculated_at": datetime.now().isoformat(),
        }
    
    def _handle_unknown_ticker(self, ticker: str) -> Dict[str, Any]:
        """알려지지 않은 종목 처리"""
        return {
            "ticker": ticker,
            "company_name": f"Unknown ({ticker})",
            "category": "unknown",
            "score": 0.0,
            "components": {},
            "strengths": [],
            "weaknesses": ["Not in humanoid database"],
            "investment_recommendation": "NO_DATA",
            "calculated_at": datetime.now().isoformat(),
        }
    
    def _generate_recommendation(
        self,
        score: float,
        company: Dict
    ) -> str:
        """투자 권고 생성"""
        category = company["category"]
        
        if score >= 0.80:
            if category == "ev_manufacturer":
                return "STRONG_BUY: 전기차 DNA + 대량생산 역량으로 휴머노이드 시장 선도 예상"
            else:
                return "BUY: 높은 기술력과 시장 준비도"
        
        elif score >= 0.60:
            if category == "ev_manufacturer":
                return "BUY: 부품 내재화와 생산 역량 우위, 장기 성장 기대"
            else:
                return "HOLD: 기술력은 있으나 생산 확장성 검증 필요"
        
        elif score >= 0.40:
            return "HOLD: 잠재력 있으나 OEM 의존도 높음, 가격 경쟁 불리"
        
        else:
            if category == "startup":
                return "AVOID: 대량생산 인프라 부재, 가격 경쟁에서 뒤처질 위험"
            else:
                return "WEAK: 휴머노이드 사업 준비도 낮음"
    
    def get_top_humanoid_plays(
        self,
        min_score: float = 0.60
    ) -> List[Dict]:
        """
        Top 휴머노이드 투자 종목
        
        Returns:
            고득점 종목 리스트 (점수순)
        """
        results = []
        
        for ticker in self.companies.keys():
            score_data = self.calculate_humanoid_score(ticker)
            if score_data["score"] >= min_score:
                results.append(score_data)
        
        # 점수순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def compare_ev_vs_startup(self) -> Dict[str, Any]:
        """
        전기차 기업 vs 스타트업 비교
        
        핵심 인사이트: "로봇 스타트업보다 70% 저렴하게 생산"
        
        Returns:
            비교 분석 결과
        """
        ev_companies = []
        startups = []
        
        for ticker, company in self.companies.items():
            score_data = self.calculate_humanoid_score(ticker)
            
            if company["category"] == "ev_manufacturer":
                ev_companies.append(score_data)
            elif company["category"] == "startup":
                startups.append(score_data)
        
        # 평균 점수
        ev_avg_score = sum(c["score"] for c in ev_companies) / len(ev_companies) if ev_companies else 0
        startup_avg_score = sum(c["score"] for c in startups) / len(startups) if startups else 0
        
        # 평균 생산 비용
        ev_avg_cost = sum(c["estimated_production_cost"] for c in ev_companies) / len(ev_companies) if ev_companies else 1
        startup_avg_cost = sum(c["estimated_production_cost"] for c in startups) / len(startups) if startups else 1
        
        # 비용 우위
        cost_advantage = (startup_avg_cost - ev_avg_cost) / startup_avg_cost * 100
        
        return {
            "ev_companies": {
                "count": len(ev_companies),
                "avg_score": ev_avg_score,
                "avg_production_cost": ev_avg_cost,
                "top_player": ev_companies[0]["ticker"] if ev_companies else None,
            },
            "startups": {
                "count": len(startups),
                "avg_score": startup_avg_score,
                "avg_production_cost": startup_avg_cost,
                "top_player": startups[0]["ticker"] if startups else None,
            },
            "ev_cost_advantage": f"{cost_advantage:.1f}%",
            "conclusion": (
                f"전기차 기업이 스타트업 대비 평균 {cost_advantage:.0f}% 저렴한 생산 단가를 가짐. "
                f"부품 내재화와 대량생산 역량이 핵심 경쟁력."
            ),
        }
    
    def get_supply_chain_analysis(self, ticker: str) -> Dict[str, Any]:
        """
        공급망 분석 (이미지 기반)
        
        전기차 vs 휴머노이드 로봇 구성 요소:
        - 파워트레인: 전기 모터, 배터리 → 전기 모터(관절 구동), 배터리
        - 제어 시스템: ECU/MCU, 센서 융합 → AI 제어 칩, 모션 제어 보드
        - 센서 네트워크: LiDAR, 카메라, 레이더 → 3D 카메라, 토크 센서, IMU
        - 소프트웨어: 자율주행 알고리즘 → 보행/작업/AI 비전 알고리즘
        - 생산라인 구조: 모듈 조립 + 로봇팔 자동화 → 동일
        """
        if ticker not in self.companies:
            return {"error": f"Unknown ticker: {ticker}"}
        
        company = self.companies[ticker]
        
        # 구성 요소별 재활용 가능성
        supply_chain = {
            "powertrain": {
                "ev_component": "전기 모터, 배터리",
                "humanoid_component": "전기 모터(관절 구동), 배터리",
                "reuse_potential": 0.95,
                "status": "HIGH",
            },
            "control_system": {
                "ev_component": "ECU/MCU, 센서 융합",
                "humanoid_component": "AI 제어 칩, 모션 제어 보드",
                "reuse_potential": 0.80,
                "status": "HIGH",
            },
            "sensor_network": {
                "ev_component": "LiDAR, 카메라, 레이더",
                "humanoid_component": "3D 카메라, 토크 센서, IMU",
                "reuse_potential": 0.70,
                "status": "MEDIUM",
            },
            "software": {
                "ev_component": "자율주행 알고리즘",
                "humanoid_component": "보행/작업/AI 비전 알고리즘",
                "reuse_potential": company["ai_data_reuse"],
                "status": "HIGH" if company["ai_data_reuse"] > 0.7 else "MEDIUM",
            },
            "production_line": {
                "ev_component": "모듈 조립 + 로봇팔 자동화",
                "humanoid_component": "모듈 조립 + 로봇팔 자동화",
                "reuse_potential": 0.90,
                "status": "HIGH",
            },
        }
        
        return {
            "ticker": ticker,
            "company": company["name"],
            "supply_chain_analysis": supply_chain,
            "overall_reuse_potential": sum(
                v["reuse_potential"] for v in supply_chain.values()
            ) / len(supply_chain),
            "key_insight": "전기차 생산라인과 부품의 90% 이상을 휴머노이드 생산에 재활용 가능",
        }


# =============================================================================
# Feature Store 통합
# =============================================================================

HUMANOID_SCORE_FEATURE_DEFINITION = {
    "name": "Humanoid Robot Score",
    "description": "전기차 기업의 휴머노이드 로봇 사업 진출 평가 점수",
    "category": "thematic_factor",
    "data_source": "RULE_BASED",
    "calculation": "weighted_sum(ai_reuse:25%, internalization:35%, production:25%, readiness:10%, cost:5%)",
    "unit": "score",
    "range": (0.0, 1.0),
    "ttl_days": 30,  # 월 1회 업데이트
    "cost_usd": 0.0,
    "priority": 2,
}


class HumanoidScoreFeature:
    """Feature Store 통합용 래퍼"""
    
    def __init__(self):
        self.calculator = HumanoidScoreCalculator()
    
    async def calculate(
        self,
        ticker: str,
        as_of_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Feature Store 호환 인터페이스
        
        Args:
            ticker: 종목 티커
            as_of_date: 기준 날짜 (현재는 무시)
            
        Returns:
            Feature Store 형식의 결과
        """
        result = self.calculator.calculate_humanoid_score(ticker)
        
        return {
            "value": result["score"],
            "factor_name": "humanoid_score",
            "category": "thematic_factor",
            "company_type": result.get("category", "unknown"),
            "recommendation": result.get("investment_recommendation", "NO_DATA"),
            "metadata": {
                "calculated_at": result["calculated_at"],
                "ttl_days": 30,
                "cost_usd": 0.0,
                "data_source": "RULE_BASED",
                "components": result.get("components", {}),
            }
        }
    
    def get_feature_definition(self) -> Dict:
        """Feature Store 등록용 정의"""
        return HUMANOID_SCORE_FEATURE_DEFINITION


# =============================================================================
# 지정학적 리스크 분석
# =============================================================================

class GeopoliticalRiskAnalyzer:
    """
    지정학적 리스크 분석기
    
    미국 vs 중국 휴머노이드 경쟁:
    - 미국: Tesla 보조금, 중국산 로봇 관세
    - 중국: 정부 주도 핵심 기술 투자
    """
    
    def __init__(self):
        pass
    
    def analyze_geopolitical_risk(
        self,
        ticker: str,
        news_headlines: List[str] = None,
    ) -> Dict[str, Any]:
        """
        지정학적 리스크 분석
        
        Args:
            ticker: 종목 티커
            news_headlines: 최근 뉴스
            
        Returns:
            리스크 분석 결과
        """
        if ticker not in HUMANOID_COMPANIES:
            return {"ticker": ticker, "risk_score": 0.5, "risk_level": "UNKNOWN"}
        
        company = HUMANOID_COMPANIES[ticker]
        
        # 국적별 리스크
        if ticker in ["TSLA"]:
            # 미국 기업
            risk_factors = [
                "미국 보조금 수혜 가능",
                "중국 시장 접근 제한 리스크",
                "국내 생산 우대 정책",
            ]
            risk_score = 0.20  # 낮은 리스크
            risk_level = "LOW"
            
        elif ticker in ["BYD", "XPEV"]:
            # 중국 기업
            risk_factors = [
                "미국/EU 관세 리스크",
                "수출 규제 가능성",
                "AI 칩 수출 통제",
                "데이터 안보 이슈",
            ]
            risk_score = 0.60  # 높은 리스크
            risk_level = "HIGH"
            
        else:
            risk_factors = ["표준 시장 리스크"]
            risk_score = 0.40
            risk_level = "MEDIUM"
        
        # 뉴스 기반 리스크 조정
        if news_headlines:
            risk_keywords = ["tariff", "sanction", "ban", "restrict", "관세", "제재"]
            risk_count = sum(
                1 for h in news_headlines
                if any(kw in h.lower() for kw in risk_keywords)
            )
            risk_score = min(risk_score + (risk_count * 0.05), 1.0)
        
        return {
            "ticker": ticker,
            "company": company["name"],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level, ticker),
        }
    
    def _get_risk_recommendation(self, risk_level: str, ticker: str) -> str:
        """리스크 기반 권고"""
        if risk_level == "LOW":
            return f"{ticker}는 지정학적 리스크 낮음. 미국 정책 수혜 가능."
        elif risk_level == "HIGH":
            return f"{ticker}는 지정학적 리스크 높음. 관세/규제 뉴스 모니터링 필요."
        else:
            return f"{ticker}는 중간 수준의 지정학적 리스크."


# =============================================================================
# Demo
# =============================================================================

async def demo_humanoid_analysis():
    """휴머노이드 스코어 분석 데모"""
    print("=" * 80)
    print("Humanoid Robot Score Analysis Demo")
    print("(전기차 기업의 제2의 도약 = 휴머노이드)")
    print("=" * 80)
    
    calculator = HumanoidScoreCalculator()
    geo_analyzer = GeopoliticalRiskAnalyzer()
    
    # 1. 개별 기업 분석
    print("\n[1] Individual Company Analysis")
    print("-" * 60)
    
    for ticker in ["TSLA", "BYD", "XPEV", "FIGURE"]:
        result = calculator.calculate_humanoid_score(ticker)
        print(f"\n{result['company_name']}")
        print(f"  Humanoid Score: {result['score']:.2f}")
        print(f"  Category: {result['category']}")
        print(f"  AI Data Reuse: {result['components']['ai_data_reuse']:.0%}")
        print(f"  Component Internalization: {result['components']['component_internalization']:.0%}")
        print(f"  Mass Production: {result['components']['mass_production_capability']:.0%}")
        print(f"  Cost Efficiency: {result['components']['cost_efficiency']:.0%}")
        print(f"  Recommendation: {result['investment_recommendation']}")
    
    # 2. 전기차 vs 스타트업 비교
    print("\n[2] EV Manufacturers vs Startups")
    print("-" * 60)
    
    comparison = calculator.compare_ev_vs_startup()
    print(f"EV Companies:")
    print(f"  Count: {comparison['ev_companies']['count']}")
    print(f"  Avg Score: {comparison['ev_companies']['avg_score']:.2f}")
    print(f"  Avg Production Cost: {comparison['ev_companies']['avg_production_cost']:.2f}")
    
    print(f"\nStartups:")
    print(f"  Count: {comparison['startups']['count']}")
    print(f"  Avg Score: {comparison['startups']['avg_score']:.2f}")
    print(f"  Avg Production Cost: {comparison['startups']['avg_production_cost']:.2f}")
    
    print(f"\n🎯 EV Cost Advantage: {comparison['ev_cost_advantage']}")
    print(f"Conclusion: {comparison['conclusion']}")
    
    # 3. 공급망 분석
    print("\n[3] Supply Chain Analysis (Tesla)")
    print("-" * 60)
    
    supply_chain = calculator.get_supply_chain_analysis("TSLA")
    print(f"Overall Reuse Potential: {supply_chain['overall_reuse_potential']:.0%}")
    
    for component, data in supply_chain["supply_chain_analysis"].items():
        print(f"\n{component}:")
        print(f"  EV: {data['ev_component']}")
        print(f"  Humanoid: {data['humanoid_component']}")
        print(f"  Reuse: {data['reuse_potential']:.0%} ({data['status']})")
    
    # 4. 지정학적 리스크
    print("\n[4] Geopolitical Risk Analysis")
    print("-" * 60)
    
    for ticker in ["TSLA", "BYD"]:
        risk = geo_analyzer.analyze_geopolitical_risk(ticker)
        print(f"\n{ticker}:")
        print(f"  Risk Level: {risk['risk_level']}")
        print(f"  Risk Score: {risk['risk_score']:.2f}")
        print(f"  Recommendation: {risk['recommendation']}")
    
    # 5. Top Humanoid Plays
    print("\n[5] Top Humanoid Investment Plays")
    print("-" * 60)
    
    top_plays = calculator.get_top_humanoid_plays(min_score=0.50)
    for i, play in enumerate(top_plays, 1):
        print(f"{i}. {play['ticker']} ({play['company_name']})")
        print(f"   Score: {play['score']:.2f}")
        print(f"   Key Strength: {play['strengths'][0] if play['strengths'] else 'N/A'}")
    
    # 6. Feature Store 통합
    print("\n[6] Feature Store Integration")
    print("-" * 60)
    
    feature = HumanoidScoreFeature()
    tsla_feature = await feature.calculate("TSLA")
    
    print(f"TSLA Humanoid Score Feature:")
    print(f"  Value: {tsla_feature['value']:.2f}")
    print(f"  Category: {tsla_feature['category']}")
    print(f"  Recommendation: {tsla_feature['recommendation']}")
    print(f"  Cost: ${tsla_feature['metadata']['cost_usd']}")
    
    print("\n" + "=" * 80)
    print("Demo complete!")
    print("핵심: 전기차 DNA(AI 데이터 + 부품 내재화 + 대량생산)가 휴머노이드 승자 결정")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_humanoid_analysis())