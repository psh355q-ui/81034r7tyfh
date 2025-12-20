from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class ReasoningStep:
    """추론 단계 결과"""
    step_name: str
    input_context: str
    reasoning: str
    entities_identified: List[str] = field(default_factory=list)
    relationships_found: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DeepReasoningResult:
    """심층 추론 최종 결과"""
    # 메타데이터
    news_text: str
    analyzed_at: datetime
    model_used: str
    
    # 추론 단계
    step1_direct: ReasoningStep
    step2_secondary: ReasoningStep
    step3_strategy: ReasoningStep
    
    # 최종 결론
    theme: str
    primary_beneficiary: Dict  # {"ticker": "GOOGL", "action": "BUY", "confidence": 0.85}
    hidden_beneficiary: Optional[Dict] = None  # 숨은 수혜자
    loser: Optional[Dict] = None  # 피해자
    
    # Bull/Bear 시나리오
    bull_case: str = ""
    bear_case: str = ""
    
    # 추론 흔적
    reasoning_trace: List[str] = field(default_factory=list)
    verified_relationships: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['analyzed_at'] = self.analyzed_at.isoformat()
        return result
    
    def get_action_items(self) -> List[Dict]:
        """실행 가능한 액션 리스트"""
        actions = []
        if self.primary_beneficiary:
            actions.append(self.primary_beneficiary)
        if self.hidden_beneficiary:
            actions.append(self.hidden_beneficiary)
        if self.loser:
            actions.append(self.loser)
        return actions
