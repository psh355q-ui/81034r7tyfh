"""
AI War Priority System - 우선순위 점수 계산 모듈

ChatGPT Integration Feature 1:
- 의견이 많고, 충돌이 많고, 토론이 길수록 우선순위 상승
- 기관 신호가 있으면 추가 가중치

공식:
priority = opinion_count * 0.4 + avg_confidence * 0.3 + debate_rounds * 0.2 + institutional_signal * 0.1

작성일: 2025-12-16
"""

def calculate_priority_score(debate_result, has_institutional_signal: bool = False) -> float:
    """
    AI War 우선순위 점수 계산
    
    Args:
        debate_result: DebateResult 객체
        has_institutional_signal: 기관 매수 신호 있는지
    
    Returns:
        우선순위 점수 (0.0 ~ 1.0+)
    
    Example:
        >>> score = calculate_priority_score(result, has_institutional_signal=True)
        >>> if score > 0.7:
        >>>     print("고우선순위 제안")
    """
    # 1. Opinion Count (정규화: 5개 agents 기준)
    opinion_count = len(debate_result.model_votes)
    opinion_score = min(opinion_count / 5.0, 1.0)
    
    # 2. Average Confidence
    confidence_score = debate_result.consensus_confidence
    
    # 3. Debate Rounds (정규화: 3 rounds 기준)
    rounds_count = len(debate_result.debate_rounds)
    rounds_score = min(rounds_count / 3.0, 1.0)
    
    # 4. Institutional Signal (0 or 1)
    institutional_score = 1.0 if has_institutional_signal else 0.0
    
    # 가중 합계
    priority = (
        opinion_score * 0.4 +
        confidence_score * 0.3 +
        rounds_score * 0.2 +
        institutional_score * 0.1
    )
    
    return round(priority, 3)
