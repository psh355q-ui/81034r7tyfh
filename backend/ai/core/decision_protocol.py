"""
Decision Protocol - AI 응답 품질 검증 시스템

Phase F1: AI 집단지성 고도화

AI 응답의 품질을 다각도로 검증하여 신뢰할 수 있는 의사결정만 허용

검증 항목:
1. JSON Schema 검증 - 필수 필드 존재 여부
2. Reasoning Depth Check - 논리적 깊이 (최소 50단어)
3. 논리 키워드 검증 - because, therefore, however 등 사용
4. 숫자/티커 근거 확인 - 구체적 데이터 인용
5. 신뢰도 범위 검증 - 0.0 ~ 1.0 사이

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 검증 결과 구조
# ═══════════════════════════════════════════════════════════════

class ValidationSeverity(str, Enum):
    """검증 실패 심각도"""
    ERROR = "error"        # 치명적: 응답 거부
    WARNING = "warning"    # 경고: 가중치 감소
    INFO = "info"          # 정보: 로깅만


@dataclass
class ValidationIssue:
    """개별 검증 이슈"""
    check_name: str
    severity: ValidationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    quality_score: float  # 0.0 ~ 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def has_errors(self) -> bool:
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(i.severity == ValidationSeverity.WARNING for i in self.issues)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)


# ═══════════════════════════════════════════════════════════════
# AI 응답 스키마
# ═══════════════════════════════════════════════════════════════

@dataclass
class AIDecisionSchema:
    """AI 의사결정 응답 표준 스키마"""
    action: str  # BUY, SELL, HOLD, DCA, STOP_LOSS
    confidence: float  # 0.0 ~ 1.0
    reasoning: str  # 논리적 근거
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: Optional[str] = None  # short, medium, long
    risk_level: Optional[str] = None  # low, medium, high
    key_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "time_horizon": self.time_horizon,
            "risk_level": self.risk_level,
            "key_factors": self.key_factors
        }


# ═══════════════════════════════════════════════════════════════
# Decision Protocol 클래스
# ═══════════════════════════════════════════════════════════════

class DecisionProtocol:
    """
    AI 응답 품질 검증 프로토콜
    
    Usage:
        protocol = DecisionProtocol()
        
        # 응답 검증
        result = protocol.validate(ai_response)
        
        if result.is_valid:
            # 검증 통과
            process_decision(ai_response)
        else:
            # 검증 실패
            log_issues(result.issues)
    """
    
    # 필수 필드
    REQUIRED_FIELDS = ["action", "confidence", "reasoning"]
    
    # 유효한 액션
    VALID_ACTIONS = ["BUY", "SELL", "HOLD", "DCA", "STOP_LOSS", "WAIT"]
    
    # 논리 키워드 (영어/한국어)
    LOGIC_KEYWORDS_EN = [
        "because", "therefore", "however", "although", "since", 
        "thus", "hence", "consequently", "furthermore", "moreover",
        "despite", "unless", "whether", "if", "when", "assuming"
    ]
    LOGIC_KEYWORDS_KR = [
        "왜냐하면", "따라서", "그러나", "비록", "때문에",
        "그러므로", "결과적으로", "또한", "게다가", "더욱이",
        "그럼에도", "만약", "가정할 때", "반면", "하지만"
    ]
    
    # 숫자 패턴 (가격, 퍼센트, 배수 등)
    NUMBER_PATTERNS = [
        r'\$[\d,]+\.?\d*',           # $1,234.56
        r'[\d,]+\.?\d*%',             # 12.5%
        r'[\d,]+\.?\d*x',             # 2.5x
        r'[\d,]+\.?\d*배',            # 2.5배
        r'P/E\s*[\d.]+',              # P/E 15.3
        r'EPS\s*\$?[\d.]+',           # EPS 3.50
        r'\d{1,3}(,\d{3})*\.?\d*\s*(원|달러|억|조)',  # 1,000억
    ]
    
    # 티커 패턴
    TICKER_PATTERN = r'\b[A-Z]{1,5}\b'  # NVDA, AAPL, TSM
    
    def __init__(
        self,
        min_reasoning_words: int = 50,
        min_logic_keywords: int = 2,
        min_number_refs: int = 1,
        strict_mode: bool = False
    ):
        """
        Args:
            min_reasoning_words: 최소 논리 근거 단어 수
            min_logic_keywords: 최소 논리 키워드 수
            min_number_refs: 최소 숫자 참조 수
            strict_mode: 엄격 모드 (WARNING도 ERROR로 처리)
        """
        self.min_reasoning_words = min_reasoning_words
        self.min_logic_keywords = min_logic_keywords
        self.min_number_refs = min_number_refs
        self.strict_mode = strict_mode
        
        # 검증 통계
        self._stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "errors_by_check": {}
        }
        
        logger.info(
            f"DecisionProtocol initialized: "
            f"min_words={min_reasoning_words}, "
            f"min_logic={min_logic_keywords}, "
            f"strict={strict_mode}"
        )
    
    def validate(
        self, 
        response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        AI 응답 검증
        
        Args:
            response: AI 응답 딕셔너리
            context: 추가 컨텍스트 (선택)
            
        Returns:
            ValidationResult: 검증 결과
        """
        issues: List[ValidationIssue] = []
        checks_passed = 0
        total_checks = 7  # 총 검증 항목 수
        
        # 1. 필수 필드 검증
        field_result = self._check_required_fields(response)
        issues.extend(field_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in field_result):
            checks_passed += 1
        
        # 2. 액션 유효성 검증
        action_result = self._check_valid_action(response.get("action", ""))
        issues.extend(action_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in action_result):
            checks_passed += 1
        
        # 3. 신뢰도 범위 검증
        conf_result = self._check_confidence_range(response.get("confidence"))
        issues.extend(conf_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in conf_result):
            checks_passed += 1
        
        # 4. 논리 깊이 검증
        reasoning = response.get("reasoning", "")
        depth_result = self._check_reasoning_depth(reasoning)
        issues.extend(depth_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in depth_result):
            checks_passed += 1
        
        # 5. 논리 키워드 검증
        keyword_result = self._check_logic_keywords(reasoning)
        issues.extend(keyword_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in keyword_result):
            checks_passed += 1
        
        # 6. 숫자 근거 검증
        number_result = self._check_number_references(reasoning)
        issues.extend(number_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in number_result):
            checks_passed += 1
        
        # 7. 일관성 검증 (액션과 신뢰도)
        consistency_result = self._check_consistency(response)
        issues.extend(consistency_result)
        if not any(i.severity == ValidationSeverity.ERROR for i in consistency_result):
            checks_passed += 1
        
        # 품질 점수 계산
        quality_score = checks_passed / total_checks
        
        # 경고가 있으면 점수 감소
        warning_penalty = sum(
            0.05 for i in issues if i.severity == ValidationSeverity.WARNING
        )
        quality_score = max(0.0, quality_score - warning_penalty)
        
        # 최종 유효성 판정
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        has_critical_warnings = self.strict_mode and any(
            i.severity == ValidationSeverity.WARNING for i in issues
        )
        is_valid = not has_errors and not has_critical_warnings
        
        # 통계 업데이트
        self._update_stats(is_valid, issues)
        
        result = ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            metadata={
                "checks_passed": checks_passed,
                "total_checks": total_checks,
                "response_action": response.get("action"),
                "response_confidence": response.get("confidence")
            }
        )
        
        if not is_valid:
            logger.warning(
                f"Validation failed: {result.error_count} errors, "
                f"{result.warning_count} warnings"
            )
        
        return result
    
    def _check_required_fields(
        self, response: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """필수 필드 검증"""
        issues = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in response:
                issues.append(ValidationIssue(
                    check_name="required_fields",
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required field: {field}",
                    details={"missing_field": field}
                ))
            elif response[field] is None or response[field] == "":
                issues.append(ValidationIssue(
                    check_name="required_fields",
                    severity=ValidationSeverity.ERROR,
                    message=f"Empty required field: {field}",
                    details={"empty_field": field}
                ))
        
        return issues
    
    def _check_valid_action(self, action: str) -> List[ValidationIssue]:
        """액션 유효성 검증"""
        issues = []
        
        if not action:
            return issues  # 이미 필수 필드 검증에서 처리
        
        action_upper = action.upper()
        if action_upper not in self.VALID_ACTIONS:
            issues.append(ValidationIssue(
                check_name="valid_action",
                severity=ValidationSeverity.ERROR,
                message=f"Invalid action: {action}",
                details={
                    "provided": action,
                    "valid_actions": self.VALID_ACTIONS
                }
            ))
        
        return issues
    
    def _check_confidence_range(
        self, confidence: Optional[float]
    ) -> List[ValidationIssue]:
        """신뢰도 범위 검증"""
        issues = []
        
        if confidence is None:
            return issues  # 이미 필수 필드 검증에서 처리
        
        try:
            conf_float = float(confidence)
            if not (0.0 <= conf_float <= 1.0):
                issues.append(ValidationIssue(
                    check_name="confidence_range",
                    severity=ValidationSeverity.ERROR,
                    message=f"Confidence must be between 0.0 and 1.0, got: {confidence}",
                    details={"provided": confidence}
                ))
            elif conf_float == 0.0 or conf_float == 1.0:
                issues.append(ValidationIssue(
                    check_name="confidence_range",
                    severity=ValidationSeverity.WARNING,
                    message=f"Extreme confidence value: {confidence}",
                    details={"provided": confidence}
                ))
        except (ValueError, TypeError):
            issues.append(ValidationIssue(
                check_name="confidence_range",
                severity=ValidationSeverity.ERROR,
                message=f"Confidence must be a number, got: {type(confidence).__name__}",
                details={"provided": confidence}
            ))
        
        return issues
    
    def _check_reasoning_depth(self, reasoning: str) -> List[ValidationIssue]:
        """논리 깊이 검증"""
        issues = []
        
        if not reasoning:
            return issues  # 이미 필수 필드 검증에서 처리
        
        # 단어 수 계산 (영어 + 한국어)
        words = reasoning.split()
        word_count = len(words)
        
        if word_count < self.min_reasoning_words:
            severity = (
                ValidationSeverity.ERROR 
                if word_count < self.min_reasoning_words // 2 
                else ValidationSeverity.WARNING
            )
            issues.append(ValidationIssue(
                check_name="reasoning_depth",
                severity=severity,
                message=(
                    f"Reasoning too short: {word_count} words "
                    f"(minimum: {self.min_reasoning_words})"
                ),
                details={
                    "word_count": word_count,
                    "minimum": self.min_reasoning_words
                }
            ))
        
        return issues
    
    def _check_logic_keywords(self, reasoning: str) -> List[ValidationIssue]:
        """논리 키워드 검증"""
        issues = []
        
        if not reasoning:
            return issues
        
        reasoning_lower = reasoning.lower()
        
        # 영어 키워드 검색
        found_keywords_en = [
            kw for kw in self.LOGIC_KEYWORDS_EN 
            if kw in reasoning_lower
        ]
        
        # 한국어 키워드 검색
        found_keywords_kr = [
            kw for kw in self.LOGIC_KEYWORDS_KR 
            if kw in reasoning
        ]
        
        total_found = len(found_keywords_en) + len(found_keywords_kr)
        
        if total_found < self.min_logic_keywords:
            issues.append(ValidationIssue(
                check_name="logic_keywords",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Insufficient logical connectors: {total_found} "
                    f"(minimum: {self.min_logic_keywords})"
                ),
                details={
                    "found_count": total_found,
                    "found_keywords": found_keywords_en + found_keywords_kr,
                    "minimum": self.min_logic_keywords
                }
            ))
        
        return issues
    
    def _check_number_references(self, reasoning: str) -> List[ValidationIssue]:
        """숫자 근거 검증"""
        issues = []
        
        if not reasoning:
            return issues
        
        found_numbers = []
        for pattern in self.NUMBER_PATTERNS:
            matches = re.findall(pattern, reasoning)
            found_numbers.extend(matches)
        
        if len(found_numbers) < self.min_number_refs:
            issues.append(ValidationIssue(
                check_name="number_references",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Insufficient numeric references: {len(found_numbers)} "
                    f"(minimum: {self.min_number_refs})"
                ),
                details={
                    "found_count": len(found_numbers),
                    "examples": found_numbers[:5],
                    "minimum": self.min_number_refs
                }
            ))
        
        return issues
    
    def _check_consistency(self, response: Dict[str, Any]) -> List[ValidationIssue]:
        """일관성 검증 (액션과 신뢰도)"""
        issues = []
        
        action = response.get("action", "").upper()
        confidence = response.get("confidence", 0.5)
        
        try:
            conf_float = float(confidence)
        except (ValueError, TypeError):
            return issues
        
        # 공격적 액션인데 신뢰도가 너무 낮은 경우
        aggressive_actions = ["BUY", "SELL"]
        if action in aggressive_actions and conf_float < 0.5:
            issues.append(ValidationIssue(
                check_name="consistency",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Low confidence ({conf_float:.2f}) for aggressive action ({action})"
                ),
                details={
                    "action": action,
                    "confidence": conf_float
                }
            ))
        
        # HOLD인데 신뢰도가 너무 높은 경우
        if action == "HOLD" and conf_float > 0.9:
            issues.append(ValidationIssue(
                check_name="consistency",
                severity=ValidationSeverity.INFO,
                message=(
                    f"High confidence ({conf_float:.2f}) for HOLD action "
                    f"(consider stronger position)"
                ),
                details={
                    "action": action,
                    "confidence": conf_float
                }
            ))
        
        return issues
    
    def _update_stats(
        self, is_valid: bool, issues: List[ValidationIssue]
    ):
        """통계 업데이트"""
        self._stats["total_validations"] += 1
        
        if is_valid:
            self._stats["passed"] += 1
        else:
            self._stats["failed"] += 1
        
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                check_name = issue.check_name
                if check_name not in self._stats["errors_by_check"]:
                    self._stats["errors_by_check"][check_name] = 0
                self._stats["errors_by_check"][check_name] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """검증 통계 조회"""
        total = self._stats["total_validations"]
        return {
            **self._stats,
            "pass_rate": self._stats["passed"] / total if total > 0 else 0.0
        }
    
    def parse_and_validate(
        self, 
        raw_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[AIDecisionSchema], ValidationResult]:
        """
        원시 응답을 파싱하고 검증
        
        JSON 형식의 AI 응답을 파싱하여 스키마로 변환하고 검증
        
        Args:
            raw_response: 원시 AI 응답 문자열
            context: 추가 컨텍스트
            
        Returns:
            Tuple[Optional[AIDecisionSchema], ValidationResult]:
                검증 통과 시 스키마와 결과, 실패 시 None과 결과
        """
        # JSON 파싱 시도
        try:
            # JSON 블록 추출 시도
            json_match = re.search(r'\{[^{}]*\}', raw_response, re.DOTALL)
            if json_match:
                response_dict = json.loads(json_match.group())
            else:
                response_dict = json.loads(raw_response)
        except json.JSONDecodeError as e:
            return None, ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=[ValidationIssue(
                    check_name="json_parse",
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to parse JSON: {str(e)}",
                    details={"raw_response": raw_response[:500]}
                )]
            )
        
        # 검증
        validation_result = self.validate(response_dict, context)
        
        if not validation_result.is_valid:
            return None, validation_result
        
        # 스키마로 변환
        try:
            schema = AIDecisionSchema(
                action=response_dict.get("action", "HOLD").upper(),
                confidence=float(response_dict.get("confidence", 0.5)),
                reasoning=response_dict.get("reasoning", ""),
                target_price=response_dict.get("target_price"),
                stop_loss=response_dict.get("stop_loss"),
                time_horizon=response_dict.get("time_horizon"),
                risk_level=response_dict.get("risk_level"),
                key_factors=response_dict.get("key_factors", [])
            )
            return schema, validation_result
        except Exception as e:
            return None, ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=[ValidationIssue(
                    check_name="schema_conversion",
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to convert to schema: {str(e)}"
                )]
            )


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_decision_protocol: Optional[DecisionProtocol] = None


def get_decision_protocol() -> DecisionProtocol:
    """DecisionProtocol 싱글톤 인스턴스"""
    global _decision_protocol
    if _decision_protocol is None:
        _decision_protocol = DecisionProtocol()
    return _decision_protocol


# ═══════════════════════════════════════════════════════════════
# 편의 함수
# ═══════════════════════════════════════════════════════════════

def validate_decision(response: Dict[str, Any]) -> ValidationResult:
    """AI 응답 검증 편의 함수"""
    return get_decision_protocol().validate(response)


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    protocol = DecisionProtocol()
    
    print("=== Decision Protocol Test ===\n")
    
    # 테스트 1: 유효한 응답
    valid_response = {
        "action": "BUY",
        "confidence": 0.75,
        "reasoning": """
        Based on the recent earnings report, NVDA shows strong momentum. 
        Because the AI data center revenue increased by 150% YoY, and 
        therefore the stock has significant upside potential. The P/E ratio 
        of 65x is justified given the 40% revenue CAGR. However, we should 
        consider the valuation risk. Target price is $580 with 15% upside.
        """,
        "target_price": 580,
        "stop_loss": 450,
        "time_horizon": "medium",
        "risk_level": "medium",
        "key_factors": ["AI data center growth", "GPU demand", "Competition"]
    }
    
    print("Test 1: Valid Response")
    result = protocol.validate(valid_response)
    print(f"  Valid: {result.is_valid}")
    print(f"  Quality Score: {result.quality_score:.2f}")
    print(f"  Issues: {len(result.issues)}")
    
    # 테스트 2: 불완전한 응답
    incomplete_response = {
        "action": "BUY",
        "confidence": 0.8,
        "reasoning": "Buy because good."  # 너무 짧음
    }
    
    print("\nTest 2: Incomplete Response")
    result = protocol.validate(incomplete_response)
    print(f"  Valid: {result.is_valid}")
    print(f"  Quality Score: {result.quality_score:.2f}")
    print(f"  Issues:")
    for issue in result.issues:
        print(f"    - [{issue.severity.value}] {issue.message}")
    
    # 테스트 3: 잘못된 응답
    invalid_response = {
        "action": "MOONSHOT",  # 잘못된 액션
        "confidence": 1.5,     # 범위 초과
    }
    
    print("\nTest 3: Invalid Response")
    result = protocol.validate(invalid_response)
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {result.error_count}")
    for issue in result.issues:
        if issue.severity == ValidationSeverity.ERROR:
            print(f"    - {issue.message}")
    
    # 통계
    print("\n" + "="*50)
    print("Validation Statistics:")
    stats = protocol.get_stats()
    print(f"  Total: {stats['total_validations']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Pass Rate: {stats['pass_rate']:.1%}")
