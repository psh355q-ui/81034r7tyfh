"""
Base Intelligence Module

Market Intelligence v2.0의 모든 컴포넌트가 상속받는 기본 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class IntelligencePhase(Enum):
    """인텔리전스 컴포넌트 우선순위"""
    P0 = "P0"  # 핵심 (필수)
    P1 = "P1"  # 고급 (중요)
    P2 = "P2"  # 학습 (선택)


@dataclass
class IntelligenceResult:
    """
    인텔리전스 분석 결과 표준 데이터 클래스

    모든 인텔리전스 컴포넌트는 이 형식으로 결과를 반환해야 합니다.
    """
    success: bool
    component_name: str
    data: Dict[str, Any]
    confidence: float = 0.0  # 0.0 ~ 1.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """디셔너리로 변환 (JSON 직렬화용)"""
        return {
            "success": self.success,
            "component_name": self.component_name,
            "data": self.data,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "errors": self.errors,
        }

    def add_error(self, error: str) -> None:
        """에러 추가"""
        self.errors.append(error)
        self.success = False

    def has_errors(self) -> bool:
        """에러 존재 여부 확인"""
        return len(self.errors) > 0


class BaseIntelligence(ABC):
    """
    모든 인텔리전스 컴포넌트의 기본 클래스

    모든 컴포넌트는 이 클래스를 상속받아야 합니다.
    """

    def __init__(self, name: str, phase: IntelligencePhase):
        """
        초기화

        Args:
            name: 컴포넌트 이름
            phase: 우선순위 (P0, P1, P2)
        """
        self.name = name
        self.phase = phase
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """컴포넌트 활성화 여부"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """컴포넌트 활성화 설정"""
        self._enabled = value

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        분석 수행 (추상 메서드)

        Args:
            data: 입력 데이터

        Returns:
            IntelligenceResult: 분석 결과
        """
        pass

    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        입력 데이터 검증

        Args:
            data: 입력 데이터
            required_fields: 필수 필드 목록

        Raises:
            ValueError: 필수 필드 누락 시
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def create_result(
        self,
        success: bool,
        data: Dict[str, Any],
        confidence: float = 0.0,
        reasoning: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IntelligenceResult:
        """
        표준 결과 생성

        Args:
            success: 성공 여부
            data: 결과 데이터
            confidence: 신뢰도 (0.0 ~ 1.0)
            reasoning: 판단 근거
            metadata: 추가 메타데이터

        Returns:
            IntelligenceResult: 표준화된 결과
        """
        return IntelligenceResult(
            success=success,
            component_name=self.name,
            data=data,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', phase={self.phase.value}, enabled={self.enabled})>"


class IntelligencePipelineError(Exception):
    """인텔리전스 파이프라인 에러"""
    pass


class IntelligenceComponentError(Exception):
    """컴포넌트 실행 에러"""
    def __init__(self, component_name: str, message: str):
        self.component_name = component_name
        super().__init__(f"[{component_name}] {message}")


# Convenience Enums for common values

class NarrativePhase(Enum):
    """내러티브 단계"""
    EMERGING = "EMERGING"           # 새로운 내러티브 형성 중
    ACCELERATING = "ACCELERATING"     # 확산 및 가속
    CONSENSUS = "CONSENSUS"           # 시장 컨센서스 형성
    FATIGUED = "FATIGUED"             # 피로감/둔화
    REVERSING = "REVERSING"           # 반전 조짐


class FactVerificationStatus(Enum):
    """팩트 검증 상태"""
    VERIFIED = "VERIFIED"             # 검증 완료
    PARTIAL = "PARTIAL"               # 부분 검증
    MISMATCH = "MISMATCH"             # 불일치
    UNVERIFIED = "UNVERIFIED"         # 검증 불가


class MarketConfirmationStatus(Enum):
    """시장 확인 상태"""
    CONFIRMED = "CONFIRMED"           # 뉴스와 가격 일치
    DIVERGENT = "DIVERGENT"           # 뉴스와 가격 발산
    LEADING = "LEADING"               # 뉴스가 가격 선행
    NOISE = "NOISE"                   # 잡음


class FatigueSignal(Enum):
    """피로도 신호"""
    OVERHEATED = "OVERHEATED"         # 과열
    FATIGUED = "FATIGUED"             # 피로
    NORMAL = "NORMAL"                 # 정상
    EMERGING = "EMERGING"             # 싹 티움


class CrowdingLevel(Enum):
    """쏠림 수준"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class InvestmentHorizon(Enum):
    """투자 기간"""
    SHORT = "SHORT"      # 1~5일 (트레이더용)
    MEDIUM = "MEDIUM"    # 2~6주 (스윙용)
    LONG = "LONG"        # 6~18개월 (테마투자용)


# Type aliases for better readability
NarrativeStateData = Dict[str, Any]
MarketConfirmationData = Dict[str, Any]
FatigueAnalysisData = Dict[str, Any]
ContrarySignalData = Dict[str, Any]
HorizonTagData = Dict[str, Any]
