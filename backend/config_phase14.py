"""
Phase 14: Deep Reasoning Configuration
========================================

AI 모델 역할 배정 및 Deep Reasoning 설정

핵심 원칙:
1. Model-Agnostic: 어떤 AI든 교체 가능
2. Cost-Efficient: Free API 우선 사용
3. Dynamic: 실시간 지식 검증 지원
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, List
from enum import Enum


class AIRole(str, Enum):
    """AI 역할 정의"""
    SCREENER = "screener"           # 빠른 스크리닝 (Gemini Flash)
    REASONING = "reasoning"         # 심층 추론 (Claude/Gemini Pro)
    REGIME = "regime"               # 시장 체제 감지 (ChatGPT)
    RISK = "risk"                   # 리스크 평가 (Gemini)
    FINAL_DECISION = "decision"     # 최종 결정 (Claude Haiku)


class AIProvider(str, Enum):
    """AI 공급자"""
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"


class Phase14Settings(BaseSettings):
    """Phase 14: Deep Reasoning 설정"""
    
    # ============================================
    # AI Model Configuration (역할별 모델 지정)
    # ============================================
    
    # 심층 추론 담당 모델 (꼬리에 꼬리를 무는 분석)
    REASONING_MODEL_NAME: str = "gemini-2.5-pro"
    REASONING_MODEL_PROVIDER: AIProvider = AIProvider.GEMINI

    # 빠른 스크리닝 모델
    SCREENER_MODEL_NAME: str = "gemini-2.5-flash"
    SCREENER_MODEL_PROVIDER: AIProvider = AIProvider.GEMINI
    
    # 시장 체제 감지 모델
    REGIME_MODEL_NAME: str = "gpt-4o-mini"
    REGIME_MODEL_PROVIDER: AIProvider = AIProvider.OPENAI
    
    # 최종 결정 모델
    DECISION_MODEL_NAME: str = "claude-3-haiku-20240307"
    DECISION_MODEL_PROVIDER: AIProvider = AIProvider.CLAUDE
    
    # ============================================
    # Knowledge Graph Settings
    # ============================================
    
    # 지식 그래프 DB (pgvector 사용)
    KNOWLEDGE_GRAPH_ENABLED: bool = True
    KNOWLEDGE_EMBEDDING_MODEL: str = "text-embedding-3-small"
    KNOWLEDGE_EMBEDDING_DIM: int = 1536
    
    # 관계 타입 정의
    RELATIONSHIP_TYPES: List[str] = [
        "partner",          # 파트너십 (Google-Broadcom TPU)
        "competitor",       # 경쟁관계 (Nvidia-AMD)
        "supplier",         # 공급자 (TSMC-Apple)
        "customer",         # 고객 (OpenAI-Microsoft)
        "investor",         # 투자자 (Microsoft-OpenAI)
        "subsidiary",       # 자회사
        "chip_designer",    # 칩 설계 (Broadcom-Google TPU)
        "chip_manufacturer" # 칩 제조 (TSMC)
    ]
    
    # ============================================
    # Dynamic Knowledge Verification
    # ============================================
    
    # 실시간 지식 검증 활성화
    ENABLE_LIVE_KNOWLEDGE_CHECK: bool = True
    
    # 검증 간격 (시간)
    KNOWLEDGE_VERIFY_INTERVAL_HOURS: int = 24
    
    # 검증에 사용할 검색 소스
    VERIFICATION_SOURCES: List[str] = [
        "web_search",       # 웹 검색
        "news_api",         # 뉴스 API
        "sec_filings"       # SEC 공시
    ]
    
    # ============================================
    # Deep Reasoning Settings
    # ============================================
    
    # 추론 단계 수 (3단계 권장)
    REASONING_STEPS: int = 3
    
    # 최대 추론 깊이 (꼬리 물기 단계)
    MAX_REASONING_DEPTH: int = 3
    
    # 시나리오 분석 활성화 (Bull/Bear Case)
    ENABLE_SCENARIO_ANALYSIS: bool = True
    
    # Hidden Beneficiary 탐색 활성화
    ENABLE_HIDDEN_BENEFICIARY: bool = True
    
    # 신뢰도 임계값
    CONFIDENCE_THRESHOLD: float = 0.6
    
    # 가설 라벨링 (증거 없는 추론)
    REQUIRE_HYPOTHESIS_LABELING: bool = True
    
    # ============================================
    # Cost Control
    # ============================================
    
    # 일일 Deep Reasoning 호출 제한
    DAILY_REASONING_LIMIT: int = 10
    
    # 토큰 제한 (비용 관리)
    MAX_REASONING_TOKENS: int = 4000
    MAX_VERIFICATION_TOKENS: int = 1000
    
    # Reasoning 결과 캐싱 (시간)
    REASONING_CACHE_TTL_HOURS: int = 12
    
    # ============================================
    # Output Settings
    # ============================================
    
    # 추론 흔적 저장
    SAVE_REASONING_TRACE: bool = True
    
    # 상세 로그
    VERBOSE_REASONING: bool = True
    
    class Config:
        env_prefix = "PHASE14_"
        env_file = ".env"
        extra = "ignore"  # .env의 다른 설정들 무시


# 기본 설정 인스턴스
settings = Phase14Settings()


# ============================================
# AI Model Registry (역할 → 모델 매핑)
# ============================================

AI_MODEL_REGISTRY: Dict[AIRole, Dict] = {
    AIRole.REASONING: {
        "provider": settings.REASONING_MODEL_PROVIDER,
        "model": settings.REASONING_MODEL_NAME,
        "description": "심층 추론 (3단계 CoT, 꼬리 물기 분석)",
        "max_tokens": settings.MAX_REASONING_TOKENS,
        "temperature": 0.3  # 낮은 온도 = 일관된 추론
    },
    AIRole.SCREENER: {
        "provider": settings.SCREENER_MODEL_PROVIDER,
        "model": settings.SCREENER_MODEL_NAME,
        "description": "빠른 리스크 스크리닝",
        "max_tokens": 1000,
        "temperature": 0.1
    },
    AIRole.REGIME: {
        "provider": settings.REGIME_MODEL_PROVIDER,
        "model": settings.REGIME_MODEL_NAME,
        "description": "시장 체제 감지 (Bull/Bear/Sideways)",
        "max_tokens": 1500,
        "temperature": 0.2
    },
    AIRole.FINAL_DECISION: {
        "provider": settings.DECISION_MODEL_PROVIDER,
        "model": settings.DECISION_MODEL_NAME,
        "description": "최종 매매 결정",
        "max_tokens": 2000,
        "temperature": 0.1
    }
}


# ============================================
# Seed Knowledge (초기 지식 그래프 시드)
# ============================================

SEED_KNOWLEDGE = {
    # AI 칩 생태계
    "Google": {
        "partners": ["Broadcom"],
        "products": ["TPU v5", "TPU v6", "Gemini"],
        "competitors": ["OpenAI", "Microsoft", "Meta"],
        "chip_dependency": "low",  # 자체 TPU
        "notes": "Full-stack AI (Chip + Model + Service)"
    },
    "Broadcom": {
        "partners": ["Google", "Meta", "Apple"],
        "role": "ASIC/TPU chip designer",
        "customers": ["Google TPU", "Meta MTIA"],
        "competitors": ["Marvell"],
        "notes": "AI 시대의 숨은 수혜자"
    },
    "Nvidia": {
        "products": ["H100", "H200", "Blackwell B200"],
        "competitors": ["AMD", "Intel", "Google TPU"],
        "moat": "CUDA ecosystem",
        "risk": "빅테크 자체 칩 개발",
        "notes": "현재 AI 칩 지배자, 장기 리스크 존재"
    },
    "OpenAI": {
        "partners": ["Microsoft"],
        "investors": ["Microsoft", "SoftBank"],
        "projects": ["Stargate"],
        "chip_dependency": "high",  # Nvidia 의존
        "notes": "자체 칩 개발 추진 중 (Broadcom 협력 가능성)"
    },
    "Microsoft": {
        "partners": ["OpenAI"],
        "products": ["Azure AI", "Maia (자체 칩)"],
        "chip_dependency": "medium",
        "notes": "클라우드 3사 중 하나"
    },
    "Amazon": {
        "products": ["AWS", "Trainium", "Inferentia"],
        "chip_dependency": "medium",
        "notes": "자체 AI 칩 개발 (Trainium)"
    },
    # 메모리 반도체
    "Samsung": {
        "products": ["HBM", "NAND", "Foundry 2nm"],
        "competitors": ["SK Hynix", "Micron", "TSMC"],
        "risk": "파운드리 수율 이슈",
        "opportunity": "SF2 2nm 성공 시 턴어라운드"
    },
    "SK Hynix": {
        "products": ["HBM3", "HBM3E"],
        "customers": ["Nvidia"],
        "notes": "HBM 시장 선두"
    },
    # 전력 인프라 (AI 데이터센터)
    "Vistra": {
        "sector": "Power/Utility",
        "relevance": "AI 데이터센터 전력 수요 수혜",
        "notes": "스타게이트 등 대형 프로젝트 수혜 가능"
    },
    "Constellation Energy": {
        "sector": "Nuclear/SMR",
        "relevance": "AI 전력 수요 → 원자력 르네상스",
        "notes": "SMR(소형모듈원전) 테마"
    }
}


def get_model_config(role: AIRole) -> Dict:
    """역할에 따른 모델 설정 반환"""
    return AI_MODEL_REGISTRY.get(role, AI_MODEL_REGISTRY[AIRole.REASONING])


def get_seed_knowledge(entity: str) -> Optional[Dict]:
    """초기 지식 조회 (검색 키워드용)"""
    return SEED_KNOWLEDGE.get(entity)


if __name__ == "__main__":
    print("=== Phase 14 Configuration ===")
    print(f"Reasoning Model: {settings.REASONING_MODEL_NAME}")
    print(f"Live Knowledge Check: {settings.ENABLE_LIVE_KNOWLEDGE_CHECK}")
    print(f"Reasoning Steps: {settings.REASONING_STEPS}")
    print(f"Daily Limit: {settings.DAILY_REASONING_LIMIT}")
    print(f"\n=== AI Model Registry ===")
    for role, config in AI_MODEL_REGISTRY.items():
        print(f"  {role.value}: {config['model']} ({config['description']})")
