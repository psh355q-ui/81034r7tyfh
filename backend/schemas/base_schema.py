"""
Base Schema - 모든 AI 모듈의 공통 데이터 구조

Phase 0: Foundation
GPT 권장사항: 모듈 간 데이터 구조 통일 선행 필수

작성일: 2025-12-03
참조: MASTER_INTEGRATION_ROADMAP_v5.md
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# [1] AI 칩 관련 스키마
# ═══════════════════════════════════════════════════════════════

class ChipInfo(BaseModel):
    """
    AI 칩 정보 (GPU/TPU/ASIC)

    Usage:
        unit_economics_engine, chip_efficiency_comparator에서 사용
    """
    model: Optional[str] = Field(None, description="칩 모델명 (예: NVIDIA H100, Google TPU v5p)")
    vendor: Optional[str] = Field(None, description="제조사 (예: NVIDIA, Google, AMD)")
    process_node: Optional[str] = Field(None, description="공정 (예: 5nm, 3nm, 4nm)")
    perf_tflops: Optional[float] = Field(None, description="성능 (TFLOPS)")
    mem_bw_gbps: Optional[float] = Field(None, description="메모리 대역폭 (GB/s)")
    tdp_watts: Optional[float] = Field(None, description="소비 전력 (W)")
    cost_usd: Optional[float] = Field(None, description="하드웨어 가격 ($)")
    efficiency_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="종합 효율 점수 (0~1)")
    tokens_per_sec: Optional[float] = Field(None, description="초당 토큰 생성량")
    segment: Optional[str] = Field(None, description="시장 세그먼트 (training/inference/both)")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "NVIDIA H100",
                "vendor": "NVIDIA",
                "process_node": "4nm",
                "perf_tflops": 1979.0,
                "mem_bw_gbps": 3350.0,
                "tdp_watts": 700.0,
                "cost_usd": 30000.0,
                "efficiency_score": 0.92,
                "tokens_per_sec": 15000.0,
                "segment": "training"
            }
        }


# ═══════════════════════════════════════════════════════════════
# [2] 공급망 관계 스키마
# ═══════════════════════════════════════════════════════════════

class RelationType(str, Enum):
    """공급망 관계 유형"""
    SUPPLIER = "supplier"              # 공급 (TSM → NVDA)
    COMPETITOR = "competitor"          # 경쟁 (NVDA ↔ AMD)
    CUSTOMER = "customer"              # 고객 (MSFT ← NVDA)
    PARTNER = "partner"                # 파트너 (GOOGL ↔ AVGO)
    DESIGNER = "designer"              # 설계사 (AVGO → TPU)
    MANUFACTURER = "manufacturer"      # 제조사 (TSM)


class SupplyChainEdge(BaseModel):
    """
    공급망 관계 엣지

    Usage:
        ai_value_chain_graph에서 사용
    """
    source: str = Field(..., description="출발 노드 (Ticker)")
    target: str = Field(..., description="도착 노드 (Ticker)")
    relation: RelationType = Field(..., description="관계 유형")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="신뢰도 (0~1)")
    context: Optional[str] = Field(None, description="관계 설명")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "TSM",
                "target": "NVDA",
                "relation": "supplier",
                "confidence": 0.98,
                "context": "TSMC manufactures NVIDIA GPUs using 4nm process"
            }
        }


# ═══════════════════════════════════════════════════════════════
# [3] 단위 경제학 스키마
# ═══════════════════════════════════════════════════════════════

class UnitEconomics(BaseModel):
    """
    단위 경제학 메트릭

    Usage:
        unit_economics_engine 출력 결과
    """
    token_cost: Optional[float] = Field(None, description="토큰당 비용 ($)")
    energy_cost: Optional[float] = Field(None, description="에너지당 비용 ($/kWh)")
    capex_cost: Optional[float] = Field(None, description="자본 지출 ($)")
    tco_monthly: Optional[float] = Field(None, description="월간 TCO ($)")
    lifetime_tokens: Optional[float] = Field(None, description="생애 전체 토큰 수")
    cost_per_watt: Optional[float] = Field(None, description="와트당 비용 ($/W)")

    class Config:
        json_schema_extra = {
            "example": {
                "token_cost": 1.2e-8,
                "energy_cost": 0.12,
                "capex_cost": 30000.0,
                "tco_monthly": 1250.0,
                "lifetime_tokens": 2.5e12,
                "cost_per_watt": 42.86
            }
        }


# ═══════════════════════════════════════════════════════════════
# [4] 뉴스 특성 스키마
# ═══════════════════════════════════════════════════════════════

class MarketSegment(str, Enum):
    """AI 칩 시장 세그먼트"""
    TRAINING = "training"              # 학습 시장
    INFERENCE = "inference"            # 추론 시장
    EDGE = "edge"                      # 엣지 시장
    HYPERSCALE = "hyperscale"          # 하이퍼스케일 데이터센터
    CONSUMER = "consumer"              # 소비자 시장
    MIXED = "mixed"                    # 복합
    OTHER = "other"                    # 기타


class NewsFeatures(BaseModel):
    """
    뉴스 특성 및 분류 결과

    Usage:
        news_segment_classifier 출력 결과
    """
    headline: str = Field(..., description="뉴스 헤드라인")
    body: str = Field("", description="뉴스 본문")
    segment: Optional[MarketSegment] = Field(None, description="시장 세그먼트")
    sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0, description="감성 점수 (-1~1)")
    keywords: List[str] = Field(default_factory=list, description="매칭된 키워드")
    tickers_mentioned: List[str] = Field(default_factory=list, description="언급된 티커")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="분류 신뢰도")
    published_at: Optional[datetime] = Field(None, description="뉴스 발행 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "headline": "NVIDIA Blackwell B200 breaks training records",
                "body": "NVIDIA announced new Blackwell B200 GPU...",
                "segment": "training",
                "sentiment": 0.85,
                "keywords": ["blackwell", "b200", "training"],
                "tickers_mentioned": ["NVDA", "TSM"],
                "confidence": 0.92,
                "published_at": "2025-12-03T00:00:00Z"
            }
        }


# ═══════════════════════════════════════════════════════════════
# [5] 정책 리스크 스키마 (PERI)
# ═══════════════════════════════════════════════════════════════

class PolicyRisk(BaseModel):
    """
    정책 이벤트 리스크 지수 (PERI: Policy Event Risk Index)

    Phase B4에서 구현 예정
    0~100 스케일로 정책 리스크 수치화

    Usage:
        peri_calculator 출력 결과
    """
    fed_conflict_score: float = Field(0.0, ge=0.0, le=1.0, description="연준 내부 의견 충돌도 (0~1)")
    successor_signal_score: float = Field(0.0, ge=0.0, le=1.0, description="차기 의장 후보 노출도 (0~1)")
    gov_fed_tension_score: float = Field(0.0, ge=0.0, le=1.0, description="재무부·백악관·연준 발언 온도차 (0~1)")
    election_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="대선/의회 리스크 (0~1)")
    bond_volatility_score: float = Field(0.0, ge=0.0, le=1.0, description="채권 변동성 (0~1)")
    policy_uncertainty_score: float = Field(0.0, ge=0.0, le=1.0, description="정책 불확실성 지수 (0~1)")
    peri: float = Field(0.0, ge=0.0, le=100.0, description="최종 PERI 점수 (0~100)")
    risk_level: Optional[str] = Field(None, description="리스크 레벨 (STABLE/CAUTION/WARNING/DANGER/CRITICAL)")
    adjustment_factor: Optional[float] = Field(None, ge=0.0, le=1.0, description="포지션 조정 계수 (0~1)")

    @validator('peri', pre=False, always=True)
    def calculate_peri(cls, v, values):
        """PERI 자동 계산"""
        if v == 0.0:  # 명시적으로 설정되지 않은 경우만 계산
            peri = (
                values.get('fed_conflict_score', 0.0) * 0.25 +
                values.get('successor_signal_score', 0.0) * 0.20 +
                values.get('gov_fed_tension_score', 0.0) * 0.20 +
                values.get('election_risk_score', 0.0) * 0.15 +
                values.get('bond_volatility_score', 0.0) * 0.10 +
                values.get('policy_uncertainty_score', 0.0) * 0.10
            ) * 100
            return peri
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "fed_conflict_score": 0.45,
                "successor_signal_score": 0.30,
                "gov_fed_tension_score": 0.60,
                "election_risk_score": 0.25,
                "bond_volatility_score": 0.35,
                "policy_uncertainty_score": 0.40,
                "peri": 41.75,
                "risk_level": "CAUTION",
                "adjustment_factor": 0.9
            }
        }


# ═══════════════════════════════════════════════════════════════
# [6] 통합 마켓 컨텍스트
# ═══════════════════════════════════════════════════════════════

class MarketRegime(str, Enum):
    """시장 국면"""
    BULL = "bull"                      # 상승장
    BEAR = "bear"                      # 하락장
    SIDEWAYS = "sideways"              # 횡보장
    CRASH = "crash"                    # 폭락장
    RECOVERY = "recovery"              # 회복장
    UNKNOWN = "unknown"                # 불명


class MarketContext(BaseModel):
    """
    모든 AI 모듈의 공통 입출력 구조

    Phase A5 DeepReasoningStrategy의 핵심 데이터 구조

    Usage:
        - Ingestion Layer: 원시 데이터 → MarketContext 변환
        - Reasoning Layer: MarketContext 기반 분석
        - Signal Layer: MarketContext → 매매 신호 변환
    """
    # 기본 정보
    ticker: Optional[str] = Field(None, description="종목 티커")
    company_name: Optional[str] = Field(None, description="회사명")
    timestamp: datetime = Field(default_factory=datetime.now, description="분석 시각")

    # AI 칩 정보
    chip_info: List[ChipInfo] = Field(default_factory=list, description="관련 칩 정보 리스트")

    # 공급망 관계
    supply_chain: List[SupplyChainEdge] = Field(default_factory=list, description="공급망 관계 그래프")

    # 경제성 분석
    unit_economics: Optional[UnitEconomics] = Field(None, description="단위 경제학 메트릭")

    # 뉴스 분석
    news: Optional[NewsFeatures] = Field(None, description="뉴스 특성 및 분류")

    # 리스크 팩터
    risk_factors: Dict[str, float] = Field(default_factory=dict, description="리스크 팩터 (키: 이름, 값: 점수)")
    policy_risk: Optional[PolicyRisk] = Field(None, description="정책 리스크 (PERI)")

    # 시장 국면
    market_regime: Optional[MarketRegime] = Field(None, description="시장 국면")

    # 추가 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "timestamp": "2025-12-03T00:00:00Z",
                "chip_info": [
                    {
                        "model": "H100",
                        "vendor": "NVIDIA",
                        "segment": "training"
                    }
                ],
                "supply_chain": [
                    {
                        "source": "TSM",
                        "target": "NVDA",
                        "relation": "supplier",
                        "confidence": 0.98
                    }
                ],
                "unit_economics": {
                    "token_cost": 1.2e-8,
                    "tco_monthly": 1250.0
                },
                "news": {
                    "headline": "NVIDIA announces new Blackwell GPU",
                    "segment": "training",
                    "sentiment": 0.85
                },
                "risk_factors": {
                    "geopolitical": 0.3,
                    "supply_chain": 0.2
                },
                "market_regime": "bull"
            }
        }


# ═══════════════════════════════════════════════════════════════
# [7] Multi-AI 입력 스키마
# ═══════════════════════════════════════════════════════════════

class MultimodelInput(BaseModel):
    """
    3개 AI 모델의 동일 스키마 기반 입력

    Phase A5 Ensemble 전략에서 사용
    각 AI 모델이 동일한 MarketContext를 받아 분석

    Usage:
        - Claude: Final Decision Maker
        - ChatGPT: Regime Detector & Macro Analysis
        - Gemini: Risk Screener
    """
    claude_context: MarketContext = Field(..., description="Claude 분석용 컨텍스트")
    chatgpt_context: MarketContext = Field(..., description="ChatGPT 분석용 컨텍스트")
    gemini_context: MarketContext = Field(..., description="Gemini 분석용 컨텍스트")

    # 앙상블 메타데이터
    ensemble_weights: Optional[Dict[str, float]] = Field(
        None,
        description="AI 모델별 가중치 (claude/chatgpt/gemini → 0~1)"
    )
    debate_mode: bool = Field(False, description="토론 모드 활성화 여부 (Phase C3)")

    class Config:
        json_schema_extra = {
            "example": {
                "claude_context": {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA",
                    "market_regime": "bull"
                },
                "chatgpt_context": {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA",
                    "market_regime": "bull"
                },
                "gemini_context": {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA",
                    "market_regime": "bull"
                },
                "ensemble_weights": {
                    "claude": 0.5,
                    "chatgpt": 0.3,
                    "gemini": 0.2
                },
                "debate_mode": False
            }
        }


# ═══════════════════════════════════════════════════════════════
# [8] 투자 시그널 스키마 (추가)
# ═══════════════════════════════════════════════════════════════

class SignalAction(str, Enum):
    """매매 액션"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"           # 비중 축소
    INCREASE = "INCREASE"       # 비중 확대


class InvestmentSignal(BaseModel):
    """
    투자 시그널

    DeepReasoningStrategy 최종 출력
    """
    ticker: str = Field(..., description="종목 티커")
    action: SignalAction = Field(..., description="매매 액션")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0~1)")
    reasoning: str = Field("", description="추론 근거")
    position_size: Optional[float] = Field(None, ge=0.0, le=1.0, description="포지션 크기 (0~1)")
    stop_loss: Optional[float] = Field(None, description="손절가")
    take_profit: Optional[float] = Field(None, description="익절가")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="리스크 점수 (0~1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "action": "BUY",
                "confidence": 0.85,
                "reasoning": "Blackwell B200 training efficiency leads market",
                "position_size": 0.15,
                "stop_loss": 120.0,
                "take_profit": 160.0,
                "risk_score": 0.25,
                "metadata": {
                    "segment": "training",
                    "hidden_beneficiaries": ["TSM", "AVGO"]
                }
            }
        }
