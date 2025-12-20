"""
Macro Consistency Checker (G1)

경제 지표 간의 논리적 모순을 탐지합니다.

탐지 규칙:
1. GDP ↑ + 금리 ↓ = Over-Stimulus Warning (과잉 부양 경고)
2. 실업률 ↓ + 인플레 ↑ = Sticky Inflation (고착 인플레이션)
3. VIX ↓ + Credit Spread ↑ = Hidden Stress (숨겨진 스트레스)
4. GDP 전망 ↑ + Rate Path ↓ = Policy Contradiction (정책 모순)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """이상 유형"""
    OVER_STIMULUS = "과잉 부양 경고"
    STICKY_INFLATION = "고착 인플레이션"
    HIDDEN_STRESS = "숨겨진 스트레스"
    POLICY_CONTRADICTION = "정책 모순"
    DIVERGENCE = "시장 괴리"
    COMPLACENCY = "시장 안일함"


class Severity(Enum):
    """심각도"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class MacroContradiction:
    """매크로 모순 감지 결과"""
    anomaly_type: AnomalyType
    severity: Severity
    severity_score: float  # 0-1
    
    indicator_a: str
    indicator_a_value: float
    indicator_a_trend: str  # UP, DOWN, STABLE
    
    indicator_b: str
    indicator_b_value: float
    indicator_b_trend: str
    
    contradiction_description: str
    possible_explanations: List[str] = field(default_factory=list)
    historical_precedents: List[str] = field(default_factory=list)
    market_implication: str = ""
    risk_level: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


# 모순 탐지 규칙 정의
CONTRADICTION_RULES = [
    {
        "name": "GDP vs Interest Rate",
        "indicators": ("gdp_growth", "fed_rate_change"),
        "condition": lambda gdp, rate: gdp > 2.0 and rate < 0,
        "type": AnomalyType.OVER_STIMULUS,
        "description": "경제 성장률이 높은데 금리를 인하하고 있습니다.",
        "explanations": [
            "정치적 압력으로 인한 완화 정책",
            "예상치 못한 유동성 위기 대응",
            "경기 선행 지표의 악화 징후",
        ],
        "implication": "단기 자산 가격 상승 후 인플레이션 위험",
    },
    {
        "name": "Unemployment vs Inflation",
        "indicators": ("unemployment_rate", "cpi_yoy"),
        "condition": lambda unemp, cpi: unemp < 4.0 and cpi > 3.5,
        "type": AnomalyType.STICKY_INFLATION,
        "description": "완전 고용 상태에서 인플레이션이 지속되고 있습니다.",
        "explanations": [
            "임금-물가 상승 스파이럴",
            "공급망 병목 지속",
            "통화정책 시차 효과",
        ],
        "implication": "금리 인상 장기화, 성장주 약세",
    },
    {
        "name": "VIX vs Credit Spread",
        "indicators": ("vix", "credit_spread"),
        "condition": lambda vix, spread: vix < 15 and spread > 1.5,
        "type": AnomalyType.HIDDEN_STRESS,
        "description": "주식 시장은 안정적이나 채권 시장에서 스트레스 징후가 있습니다.",
        "explanations": [
            "기관 투자자의 헤지 부족",
            "특정 섹터의 신용 악화",
            "시장 분열 (Risk-On 주식 / Risk-Off 채권)",
        ],
        "implication": "갑작스러운 조정 위험, 변동성 폭발 가능",
    },
    {
        "name": "GDP Forecast vs Rate Path",
        "indicators": ("gdp_forecast_change", "rate_path_change"),
        "condition": lambda gdp_fc, rate_fc: gdp_fc > 0.3 and rate_fc < -0.25,
        "type": AnomalyType.POLICY_CONTRADICTION,
        "description": "GDP 전망은 상향되었으나 금리 경로는 하향되었습니다.",
        "explanations": [
            "Fed의 정책 커뮤니케이션 혼란",
            "선거를 앞둔 정치적 압력",
            "글로벌 요인 (다른 중앙은행 완화)",
        ],
        "implication": "정책 불확실성 증가, 달러 약세",
    },
    {
        "name": "Stock Rally vs Bond Sell-off",
        "indicators": ("sp500_return_1m", "tnx_change_1m"),
        "condition": lambda stock, bond: stock > 5 and bond > 0.3,
        "type": AnomalyType.DIVERGENCE,
        "description": "주식은 급등하는데 국채 금리도 급등하고 있습니다.",
        "explanations": [
            "인플레이션 기대 상승",
            "재정 적자 확대 우려",
            "해외 중앙은행의 미국 국채 매도",
        ],
        "implication": "주식 밸류에이션 압박 예상, 성장주 주의",
    },
    {
        "name": "VIX vs Market Trend",
        "indicators": ("vix", "sp500_return_1m"),
        "condition": lambda vix, ret: vix < 12 and ret > 5,
        "type": AnomalyType.COMPLACENCY,
        "description": "시장이 급등했지만 VIX가 역사적 저점 수준입니다.",
        "explanations": [
            "옵션 시장의 과도한 낙관",
            "헤지 수요 감소",
            "변동성 매도 전략 과열",
        ],
        "implication": "갑작스러운 VIX 폭등 위험, 테일 리스크 증가",
    },
]


class MacroConsistencyChecker:
    """
    Macro Consistency Checker
    
    경제 지표 간의 논리적 모순을 탐지하여
    시장의 숨겨진 리스크를 발견합니다.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.rules = CONTRADICTION_RULES
    
    async def detect_contradictions(
        self,
        macro_data: Dict[str, float],
    ) -> List[MacroContradiction]:
        """
        모든 규칙을 검사하여 모순 탐지
        
        Args:
            macro_data: 매크로 데이터
                {
                    "gdp_growth": 2.5,
                    "fed_rate_change": -0.25,
                    "unemployment_rate": 3.7,
                    "cpi_yoy": 4.1,
                    "vix": 14.5,
                    "credit_spread": 1.8,
                    ...
                }
                
        Returns:
            List[MacroContradiction]: 감지된 모순 목록
        """
        contradictions = []
        
        for rule in self.rules:
            ind_a, ind_b = rule["indicators"]
            val_a = macro_data.get(ind_a)
            val_b = macro_data.get(ind_b)
            
            if val_a is None or val_b is None:
                continue
            
            try:
                if rule["condition"](val_a, val_b):
                    contradiction = await self._build_contradiction(
                        rule, val_a, val_b
                    )
                    contradictions.append(contradiction)
                    logger.warning(f"모순 감지: {rule['name']}")
            except Exception as e:
                logger.error(f"규칙 검사 실패 {rule['name']}: {e}")
        
        # 심각도 순으로 정렬
        contradictions.sort(key=lambda x: x.severity_score, reverse=True)
        
        return contradictions
    
    async def _build_contradiction(
        self,
        rule: Dict,
        val_a: float,
        val_b: float,
    ) -> MacroContradiction:
        """모순 객체 생성"""
        ind_a, ind_b = rule["indicators"]
        
        # 트렌드 결정
        trend_a = "UP" if val_a > 0 else "DOWN" if val_a < 0 else "STABLE"
        trend_b = "UP" if val_b > 0 else "DOWN" if val_b < 0 else "STABLE"
        
        # 심각도 계산 (규칙에 따라 다르게)
        severity_score = self._calculate_severity(rule, val_a, val_b)
        
        if severity_score >= 0.8:
            severity = Severity.CRITICAL
        elif severity_score >= 0.6:
            severity = Severity.HIGH
        elif severity_score >= 0.4:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        # AI로 추가 설명 생성 (있을 경우)
        explanations = rule.get("explanations", [])
        if self.ai_client:
            additional = await self._generate_explanations(rule, val_a, val_b)
            explanations.extend(additional)
        
        return MacroContradiction(
            anomaly_type=rule["type"],
            severity=severity,
            severity_score=severity_score,
            indicator_a=ind_a,
            indicator_a_value=val_a,
            indicator_a_trend=trend_a,
            indicator_b=ind_b,
            indicator_b_value=val_b,
            indicator_b_trend=trend_b,
            contradiction_description=rule["description"],
            possible_explanations=explanations,
            historical_precedents=self._get_historical_precedents(rule["type"]),
            market_implication=rule.get("implication", ""),
            risk_level=severity.value,
        )
    
    def _calculate_severity(
        self,
        rule: Dict,
        val_a: float,
        val_b: float,
    ) -> float:
        """심각도 점수 계산 (0-1)"""
        # 기본 심각도
        base_severity = {
            AnomalyType.OVER_STIMULUS: 0.7,
            AnomalyType.STICKY_INFLATION: 0.8,
            AnomalyType.HIDDEN_STRESS: 0.9,
            AnomalyType.POLICY_CONTRADICTION: 0.6,
            AnomalyType.DIVERGENCE: 0.5,
            AnomalyType.COMPLACENCY: 0.7,
        }
        
        score = base_severity.get(rule["type"], 0.5)
        
        # 값의 극단성에 따라 조정
        # (실제 구현에서는 더 정교한 로직 필요)
        
        return min(1.0, score)
    
    def _get_historical_precedents(
        self,
        anomaly_type: AnomalyType,
    ) -> List[str]:
        """역사적 선례 반환"""
        precedents = {
            AnomalyType.OVER_STIMULUS: [
                "2019년 Fed 금리 인하 사이클: 경기 호조에도 시장 압력으로 인하",
            ],
            AnomalyType.STICKY_INFLATION: [
                "1970년대 스태그플레이션: 높은 인플레와 경기 침체 동시 발생",
            ],
            AnomalyType.HIDDEN_STRESS: [
                "2007년 서브프라임: 주식 고점에서 신용 스프레드 확대",
            ],
            AnomalyType.POLICY_CONTRADICTION: [
                "2023년 SVB 사태: 긴축과 유동성 공급 동시 진행",
            ],
            AnomalyType.COMPLACENCY: [
                "2017년 저변동성 환경: VIX 9까지 하락 후 2018년 볼마게돈",
            ],
        }
        return precedents.get(anomaly_type, [])
    
    async def _generate_explanations(
        self,
        rule: Dict,
        val_a: float,
        val_b: float,
    ) -> List[str]:
        """AI로 추가 설명 생성"""
        if not self.ai_client:
            return []
        
        try:
            prompt = f"""
다음 매크로 경제 모순을 분석하세요:

모순: {rule['name']}
데이터: {rule['indicators'][0]}={val_a}, {rule['indicators'][1]}={val_b}

이 모순이 발생한 추가 가능한 이유 2가지를 간결하게 제시하세요.
"""
            response = await self.ai_client.generate(prompt)
            # 파싱 로직 필요
            return []
        except Exception as e:
            logger.error(f"AI 설명 생성 실패: {e}")
            return []
    
    def format_report_korean(
        self,
        contradictions: List[MacroContradiction],
    ) -> str:
        """모순 리포트를 한국어로 포맷팅"""
        if not contradictions:
            return "✅ 현재 감지된 매크로 모순이 없습니다."
        
        report = "# 📊 매크로 정합성 체크 리포트\n\n"
        
        for i, c in enumerate(contradictions, 1):
            severity_emoji = {
                Severity.CRITICAL: "🔴",
                Severity.HIGH: "🟠",
                Severity.MEDIUM: "🟡",
                Severity.LOW: "🟢",
            }
            
            report += f"""## {i}. {severity_emoji.get(c.severity, '⚪')} {c.anomaly_type.value}

**심각도**: {c.severity.value} (점수: {c.severity_score:.0%})

**모순 설명**: {c.contradiction_description}

**데이터**:
- {c.indicator_a}: {c.indicator_a_value} ({c.indicator_a_trend})
- {c.indicator_b}: {c.indicator_b_value} ({c.indicator_b_trend})

**가능한 설명**:
"""
            for exp in c.possible_explanations[:3]:
                report += f"- {exp}\n"
            
            if c.historical_precedents:
                report += f"\n**역사적 선례**:\n"
                for prec in c.historical_precedents:
                    report += f"- {prec}\n"
            
            report += f"\n**시장 영향**: {c.market_implication}\n\n---\n\n"
        
        return report
