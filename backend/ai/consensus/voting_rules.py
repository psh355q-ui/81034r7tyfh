"""
Voting Rules - 비대칭 의사결정 규칙

방어적 투자 전략을 위한 비대칭 투표 규칙:
- 손절은 빠르게 (1명 경고면 실행)
- 매수는 신중하게 (2명 찬성 필요)
- DCA는 매우 신중하게 (3명 전원 동의 필요)

작성일: 2025-12-06
"""

from typing import Dict
from enum import Enum


class VoteRequirement(str, Enum):
    """투표 요구사항"""
    ONE_OF_THREE = "1/3"      # 1명 이상 (손절)
    TWO_OF_THREE = "2/3"      # 2명 이상 (일반 매수)
    THREE_OF_THREE = "3/3"    # 3명 전원 (DCA)


class VotingRules:
    """
    비대칭 의사결정 규칙

    액션별로 다른 투표 요구사항 적용
    """

    # 액션별 투표 요구사항 매핑
    ACTION_REQUIREMENTS: Dict[str, VoteRequirement] = {
        # 방어적 액션 - 1명이라도 경고하면 즉시 실행
        "STOP_LOSS": VoteRequirement.ONE_OF_THREE,

        # 일반 매수 - 2명 찬성 필요
        "BUY": VoteRequirement.TWO_OF_THREE,
        "INCREASE": VoteRequirement.TWO_OF_THREE,

        # 매도 - 2명 찬성 필요
        "SELL": VoteRequirement.TWO_OF_THREE,
        "REDUCE": VoteRequirement.TWO_OF_THREE,

        # DCA (물타기) - 3명 전원 동의 필요 (매우 신중)
        "DCA": VoteRequirement.THREE_OF_THREE,

        # HOLD - 기본 과반수
        "HOLD": VoteRequirement.TWO_OF_THREE,
    }

    @classmethod
    def get_requirement(cls, action: str) -> VoteRequirement:
        """
        액션에 대한 투표 요구사항 조회

        Args:
            action: 투표 대상 액션 (BUY/SELL/DCA/STOP_LOSS 등)

        Returns:
            VoteRequirement (1/3, 2/3, 3/3)
        """
        # 기본값: 2/3 (과반수)
        return cls.ACTION_REQUIREMENTS.get(action, VoteRequirement.TWO_OF_THREE)

    @classmethod
    def get_required_votes(cls, action: str) -> int:
        """
        액션에 필요한 최소 찬성 수

        Args:
            action: 투표 대상 액션

        Returns:
            필요한 최소 찬성 수 (1, 2, 3)
        """
        requirement = cls.get_requirement(action)

        if requirement == VoteRequirement.ONE_OF_THREE:
            return 1
        elif requirement == VoteRequirement.TWO_OF_THREE:
            return 2
        elif requirement == VoteRequirement.THREE_OF_THREE:
            return 3
        else:
            return 2  # 기본값

    @classmethod
    def is_approved(cls, action: str, approve_count: int) -> bool:
        """
        투표 결과가 승인 조건을 만족하는지 확인

        Args:
            action: 투표 대상 액션
            approve_count: 찬성 수 (0~3)

        Returns:
            승인 여부 (True/False)
        """
        required = cls.get_required_votes(action)
        return approve_count >= required

    @classmethod
    def get_all_requirements(cls) -> Dict[str, str]:
        """
        모든 액션의 투표 요구사항 조회

        Returns:
            액션별 요구사항 딕셔너리
        """
        return {action: req.value for action, req in cls.ACTION_REQUIREMENTS.items()}

    @classmethod
    def explain_rule(cls, action: str) -> str:
        """
        액션의 투표 규칙 설명

        Args:
            action: 투표 대상 액션

        Returns:
            규칙 설명 문자열
        """
        requirement = cls.get_requirement(action)
        required_votes = cls.get_required_votes(action)

        explanations = {
            VoteRequirement.ONE_OF_THREE: (
                f"{action}: 1명 이상 찬성 필요 (방어적 - 빠른 대응)"
            ),
            VoteRequirement.TWO_OF_THREE: (
                f"{action}: 2명 이상 찬성 필요 (과반수 - 신중한 결정)"
            ),
            VoteRequirement.THREE_OF_THREE: (
                f"{action}: 3명 전원 찬성 필요 (만장일치 - 매우 신중한 결정)"
            ),
        }

        return explanations.get(requirement, f"{action}: {required_votes}명 찬성 필요")


# ============================================================================
# 규칙 검증 및 테스트
# ============================================================================

def validate_voting_rules():
    """투표 규칙 검증"""
    print("=" * 70)
    print("Voting Rules Validation")
    print("=" * 70)

    # 모든 액션 테스트
    test_actions = ["STOP_LOSS", "BUY", "SELL", "DCA", "HOLD", "INCREASE", "REDUCE"]

    for action in test_actions:
        requirement = VotingRules.get_requirement(action)
        required_votes = VotingRules.get_required_votes(action)
        explanation = VotingRules.explain_rule(action)

        print(f"\n{action}:")
        print(f"  Requirement: {requirement.value}")
        print(f"  Required Votes: {required_votes}")
        print(f"  Explanation: {explanation}")

        # 투표 시뮬레이션
        for approve_count in range(4):
            approved = VotingRules.is_approved(action, approve_count)
            status = "✅ APPROVED" if approved else "❌ REJECTED"
            print(f"    {approve_count}/3 votes: {status}")

    print("\n" + "=" * 70)
    print("Validation Complete")
    print("=" * 70)


if __name__ == "__main__":
    validate_voting_rules()
