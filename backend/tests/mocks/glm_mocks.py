"""
Mock objects for GLM-4.7 API tests

Phase 0, Task T0.5.1

Mock classes for testing GLM API integration:
- GLMAnalysisResult: Pydantic model for GLM analysis response
- MOCK_GLM_RESPONSE: Mock API response data
- Factory functions for creating test data

Usage:
    from backend.tests.mocks.glm_mocks import (
        create_mock_glm_response,
        create_glm_analysis_result
    )

    result = create_glm_analysis_result(
        tickers=["AAPL", "TSLA"],
        sectors=["Technology"]
    )
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Pydantic Models
# ============================================================================

class GLMAnalysisResult(BaseModel):
    """
    GLM-4.7 뉴스 분석 결과 모델

    뉴스 기사에서 추출한 종목(Tickers)와 섹터(Sectors) 정보
    """
    tickers: List[str] = Field(
        default_factory=list,
        description="관련 종목 심볼 리스트 (예: ['AAPL', 'TSLA'])"
    )
    sectors: List[str] = Field(
        default_factory=list,
        description="관련 섹터 리스트 (예: ['Technology', 'Consumer'])"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="분석 신뢰도 (0.0 ~ 1.0)"
    )
    reasoning: str = Field(
        default="",
        description="분석 근거 설명"
    )
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="분석 시간 (ISO 8601)"
    )
    model: str = Field(
        default="glm-4-flash",
        description="사용된 GLM 모델"
    )
    latency_ms: int = Field(
        default=0,
        ge=0,
        description="API 응답 시간 (밀리초)"
    )
    cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="API 호출 비용 (USD)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "TSLA"],
                "sectors": ["Technology"],
                "confidence": 0.87,
                "reasoning": "애플과 테슬라가 AI 칩 개발에 협력",
                "analyzed_at": "2026-01-15T10:30:00Z",
                "model": "glm-4-flash",
                "latency_ms": 150,
                "cost_usd": 0.001
            }
        }


# ============================================================================
# Mock API Responses
# ============================================================================

# Mock GLM API 응답 - 성공 케이스
MOCK_GLM_RESPONSE_SUCCESS = {
    "tickers": ["AAPL", "TSLA"],
    "sectors": ["Technology", "Semiconductors"],
    "confidence": 0.87,
    "reasoning": "애플과 테슬라가 차세대 AI 칩 개발을 위해 협력한다는 뉴스입니다. " +
                 "두 회사는 반도체 산업의 핵심 플레이어로, AI 칩 수요 증가로 " +
                 "반도체 섹터 전반에 긍정적 영향을 미칠 것으로 예상됩니다.",
    "analyzed_at": "2026-01-15T10:30:00Z",
    "model": "glm-4-flash",
    "latency_ms": 150,
    "cost_usd": 0.001
}

# Mock GLM API 응답 - 단일 종목
MOCK_GLM_RESPONSE_SINGLE_TICKER = {
    "tickers": ["NVDA"],
    "sectors": ["Technology", "Semiconductors"],
    "confidence": 0.92,
    "reasoning": "엔비디아의 새로운 H200 GPU가 데이터센터 시장을 선점할 것으로 예상됩니다.",
    "analyzed_at": "2026-01-15T11:00:00Z",
    "model": "glm-4-flash",
    "latency_ms": 120,
    "cost_usd": 0.0008
}

# Mock GLM API 응답 - 관련 종목 없음
MOCK_GLM_RESPONSE_NO_TICKERS = {
    "tickers": [],
    "sectors": ["Economy"],
    "confidence": 0.65,
    "reasoning": "일반적인 경제 뉴스로 특정 종목과 직접적인 연관이 없습니다.",
    "analyzed_at": "2026-01-15T12:00:00Z",
    "model": "glm-4-flash",
    "latency_ms": 100,
    "cost_usd": 0.0005
}

# Mock GLM API 응답 - 복수 섹터
MOCK_GLM_RESPONSE_MULTIPLE_SECTORS = {
    "tickers": ["JPM", "BAC"],
    "sectors": ["Financials", "Banking"],
    "confidence": 0.85,
    "reasoning": "연준의 금리 인하로 금융 주 전반이 상승했습니다.",
    "analyzed_at": "2026-01-15T13:00:00Z",
    "model": "glm-4-flash",
    "latency_ms": 130,
    "cost_usd": 0.001
}

# Mock GLM API 응답 - 저신뢰도
MOCK_GLM_RESPONSE_LOW_CONFIDENCE = {
    "tickers": ["MSFT"],
    "sectors": ["Technology"],
    "confidence": 0.45,
    "reasoning": "뉴스 내용이 모호하여 MSFT와의 연관성 확신이 낮습니다.",
    "analyzed_at": "2026-01-15T14:00:00Z",
    "model": "glm-4-flash",
    "latency_ms": 110,
    "cost_usd": 0.0007
}


# ============================================================================
# Factory Functions
# ============================================================================

def create_glm_analysis_result(
    tickers: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    confidence: float = 0.8,
    reasoning: str = "테스트용 분석 결과",
    model: str = "glm-4-flash",
    latency_ms: int = 100,
    cost_usd: float = 0.001
) -> GLMAnalysisResult:
    """
    GLM 분석 결과 모델 생성

    Args:
        tickers: 종목 리스트 (기본: ["AAPL"])
        sectors: 섹터 리스트 (기본: ["Technology"])
        confidence: 신뢰도 0~1 (기본: 0.8)
        reasoning: 분석 근거 (기본: "테스트용 분석 결과")
        model: 모델명 (기본: "glm-4-flash")
        latency_ms: 응답 시간 ms (기본: 100)
        cost_usd: 비용 USD (기본: 0.001)

    Returns:
        GLMAnalysisResult 인스턴스

    Example:
        >>> result = create_glm_analysis_result(
        ...     tickers=["TSLA", "RIVN"],
        ...     sectors=["Automotive", "Technology"],
        ...     confidence=0.9
        ... )
        >>> assert "TSLA" in result.tickers
        >>> assert result.confidence == 0.9
    """
    return GLMAnalysisResult(
        tickers=tickers or ["AAPL"],
        sectors=sectors or ["Technology"],
        confidence=confidence,
        reasoning=reasoning,
        analyzed_at=datetime.now().isoformat(),
        model=model,
        latency_ms=latency_ms,
        cost_usd=cost_usd
    )


def create_mock_glm_response(
    scenario: str = "success"
) -> Dict[str, Any]:
    """
    Mock GLM API 응답 생성

    Args:
        scenario: 시나리오 타입
            - "success": 성공 (2개 종목)
            - "single": 단일 종목
            - "no_tickers": 종목 없음
            - "multiple_sectors": 복수 섹터
            - "low_confidence": 저신뢰도

    Returns:
        Mock 응답 딕셔너리

    Example:
        >>> response = create_mock_glm_response(scenario="single")
        >>> assert len(response["tickers"]) == 1
        >>> assert response["tickers"][0] == "NVDA"
    """
    scenarios = {
        "success": MOCK_GLM_RESPONSE_SUCCESS,
        "single": MOCK_GLM_RESPONSE_SINGLE_TICKER,
        "no_tickers": MOCK_GLM_RESPONSE_NO_TICKERS,
        "multiple_sectors": MOCK_GLM_RESPONSE_MULTIPLE_SECTORS,
        "low_confidence": MOCK_GLM_RESPONSE_LOW_CONFIDENCE
    }

    if scenario not in scenarios:
        raise ValueError(
            f"Unknown scenario: {scenario}. "
            f"Available: {list(scenarios.keys())}"
        )

    return scenarios[scenario].copy()


# ============================================================================
# Preset Test Scenarios
# ============================================================================

def get_preset_news_scenarios() -> Dict[str, Dict[str, Any]]:
    """
    뉴스 분석 테스트용 프리셋 시나리오

    Returns:
        뉴스 텍스트와 예상 GLM 응답 매핑

    Example:
        >>> scenarios = get_preset_news_scenarios()
        >>> apple_news = scenarios["apple_tesla_ai"]
        >>> assert "AAPL" in apple_news["expected_response"]["tickers"]
    """
    return {
        "apple_tesla_ai": {
            "news_text": (
                "애플과 테슬라가 차세대 AI 칩 개발을 위한 전략적 파트너십을 "
                "발표했습니다. 두 회사는 각각의 강점을 결합하여 2027년까지 "
                "새로운 AI 가속기를 출시할 계획입니다."
            ),
            "expected_response": create_mock_glm_response("success")
        },
        "nvidia_gpu": {
            "news_text": (
                "엔비디아의 새로운 H200 GPU가 클라우드 데이터센터 시장에서 "
                "압도적인 점유율을 기록하고 있습니다. 아마존 AWS와 구글 클라우드가 "
                "이 칩을 대규모로 도입한다고 밝혔습니다."
            ),
            "expected_response": create_mock_glm_response("single")
        },
        "fed_rate_cut": {
            "news_text": (
                "연준이 금리 인하를 시사하자 금융 주 전반이 급등했습니다. "
                "시장은 9월 FOMC 회의에서 0.25% 포인트 인하를 기대하고 있습니다."
            ),
            "expected_response": create_mock_glm_response("multiple_sectors")
        },
        "general_economy": {
            "news_text": (
                "미국 경제가 둔화 조짐을 보이고 있습니다. 소매 판매가 예상보다 "
                "부진했고, 제조업 지수도 하락세입니다."
            ),
            "expected_response": create_mock_glm_response("no_tickers")
        }
    }


def get_ticker_sector_mapping() -> Dict[str, List[str]]:
    """
    테스트용 종목-섹터 매핑

    Returns:
        종목별 섹터 매핑 딕셔너리

    Example:
        >>> mapping = get_ticker_sector_mapping()
        >>> assert "Technology" in mapping["AAPL"]
        >>> assert "Financials" in mapping["JPM"]
    """
    return {
        "AAPL": ["Technology", "Consumer Electronics"],
        "TSLA": ["Technology", "Automotive"],
        "NVDA": ["Technology", "Semiconductors"],
        "MSFT": ["Technology", "Software"],
        "GOOGL": ["Technology", "Software"],
        "AMZN": ["Technology", "E-Commerce", "Cloud"],
        "META": ["Technology", "Social Media"],
        "JPM": ["Financials", "Banking"],
        "BAC": ["Financials", "Banking"],
        "XOM": ["Energy", "Oil & Gas"],
        "CVX": ["Energy", "Oil & Gas"],
        "PFE": ["Healthcare", "Pharmaceuticals"],
        "JNJ": ["Healthcare", "Pharmaceuticals"]
    }
