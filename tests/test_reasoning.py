"""
Tests for Deep Reasoning Intelligence Module (Phase G)

pytest -v tests/test_reasoning.py
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from backend.ai.reasoning.macro_consistency_checker import (
    MacroConsistencyChecker,
    MacroContradiction,
    AnomalyType,
    Severity,
)
from backend.ai.reasoning.skeptic_agent import (
    SkepticAgent,
    SkepticAnalysis,
    SkepticRecommendation,
)


class TestMacroConsistencyChecker:
    """MacroConsistencyChecker 테스트"""
    
    @pytest.fixture
    def checker(self):
        return MacroConsistencyChecker()
    
    @pytest.mark.asyncio
    async def test_detect_over_stimulus(self, checker):
        """과잉 부양 경고 탐지"""
        macro_data = {
            "gdp_growth": 3.0,  # 높은 GDP
            "fed_rate_change": -0.25,  # 금리 인하
        }
        
        contradictions = await checker.detect_contradictions(macro_data)
        
        # Over-Stimulus 탐지 확인
        types = [c.anomaly_type for c in contradictions]
        assert AnomalyType.OVER_STIMULUS in types
    
    @pytest.mark.asyncio
    async def test_detect_hidden_stress(self, checker):
        """숨겨진 스트레스 탐지"""
        macro_data = {
            "vix": 12,  # 낮은 VIX
            "credit_spread": 2.0,  # 높은 Credit Spread
        }
        
        contradictions = await checker.detect_contradictions(macro_data)
        
        types = [c.anomaly_type for c in contradictions]
        assert AnomalyType.HIDDEN_STRESS in types
    
    @pytest.mark.asyncio
    async def test_no_contradiction(self, checker):
        """모순 없을 때"""
        macro_data = {
            "gdp_growth": 2.0,
            "fed_rate_change": 0.0,  # 금리 동결
        }
        
        contradictions = await checker.detect_contradictions(macro_data)
        
        # Over-Stimulus는 탐지되지 않아야 함 (조건 미충족)
        types = [c.anomaly_type for c in contradictions]
        assert AnomalyType.OVER_STIMULUS not in types
    
    @pytest.mark.asyncio
    async def test_missing_data_handling(self, checker):
        """데이터 누락 처리"""
        macro_data = {
            "gdp_growth": 2.0,
            # fed_rate_change 없음
        }
        
        contradictions = await checker.detect_contradictions(macro_data)
        
        # 에러 없이 실행되어야 함
        assert isinstance(contradictions, list)
    
    def test_format_report_korean(self, checker):
        """한국어 리포트 포맷팅"""
        contradiction = MacroContradiction(
            anomaly_type=AnomalyType.HIDDEN_STRESS,
            severity=Severity.HIGH,
            severity_score=0.8,
            indicator_a="vix",
            indicator_a_value=12,
            indicator_a_trend="DOWN",
            indicator_b="credit_spread",
            indicator_b_value=2.0,
            indicator_b_trend="UP",
            contradiction_description="테스트 모순",
            possible_explanations=["설명1", "설명2"],
            market_implication="시장 영향",
        )
        
        report = checker.format_report_korean([contradiction])
        
        assert "매크로 정합성" in report
        assert "숨겨진 스트레스" in report
        assert "테스트 모순" in report


class TestSkepticAgent:
    """SkepticAgent 테스트"""
    
    @pytest.fixture
    def agent(self):
        return SkepticAgent()
    
    @pytest.mark.asyncio
    async def test_analyze_buy_consensus(self, agent):
        """BUY 합의에 대한 회의론적 분석"""
        consensus = {
            "action": "BUY",
            "confidence": 0.9,
            "reasoning": "성장 모멘텀이 강함",
        }
        
        result = await agent.analyze("TEST", consensus)
        
        assert result.ticker == "TEST"
        assert result.consensus_view == "BUY"
        assert len(result.counter_arguments) > 0
        assert result.recommendation in [
            SkepticRecommendation.PROCEED,
            SkepticRecommendation.CAUTION,
            SkepticRecommendation.AVOID,
        ]
    
    @pytest.mark.asyncio
    async def test_counter_arguments_generated(self, agent):
        """반대 논거 생성"""
        consensus = {
            "action": "BUY",
            "confidence": 0.8,
            "reasoning": "growth 성장 potential",
        }
        
        arguments = await agent._generate_counter_arguments("TEST", consensus)
        
        assert len(arguments) >= 1
    
    @pytest.mark.asyncio
    async def test_overlooked_risks_found(self, agent):
        """간과된 리스크 발굴"""
        market_data = {
            "pe_ratio": 50,  # 높은 PER
            "short_interest": 15,  # 높은 공매도
        }
        
        risks = await agent._find_overlooked_risks("TEST", market_data)
        
        assert len(risks) >= 2
    
    def test_historical_failures_search(self, agent):
        """역사적 실패 사례 검색"""
        consensus = {
            "reasoning": "tech growth infrastructure",
        }
        
        failures = agent._search_historical_failures("TEST", consensus)
        
        assert len(failures) >= 1
    
    def test_skeptic_score_calculation(self, agent):
        """회의론 점수 계산"""
        score = agent._calculate_skeptic_score(
            counter_arguments=["arg1", "arg2"],
            overlooked_risks=["risk1"],
            blind_spots=["spot1", "spot2"],
            historical_failures=["fail1"],
            worst_case_prob=0.2,
        )
        
        assert 0 <= score <= 100
    
    def test_recommendation_determination(self, agent):
        """권고 결정"""
        # 높은 회의론 점수 + 높은 합의 신뢰도
        rec = agent._determine_recommendation(
            skeptic_score=70,
            consensus_confidence=0.9,
        )
        
        assert rec == SkepticRecommendation.AVOID
        
        # 낮은 회의론 점수
        rec = agent._determine_recommendation(
            skeptic_score=30,
            consensus_confidence=0.5,
        )
        
        assert rec == SkepticRecommendation.PROCEED
    
    def test_format_report_korean(self, agent):
        """한국어 리포트 포맷팅"""
        analysis = SkepticAnalysis(
            ticker="TEST",
            consensus_view="BUY",
            consensus_confidence=0.8,
            counter_arguments=["반박1"],
            overlooked_risks=["리스크1"],
            blind_spots=["맹점1"],
            historical_failures=["실패1"],
            worst_case_scenario="최악 시나리오",
            worst_case_probability=0.15,
            skeptic_score=65,
            recommendation=SkepticRecommendation.CAUTION,
        )
        
        report = agent.format_report_korean(analysis)
        
        assert "악마의 변호인" in report
        assert "TEST" in report
        assert "주의 필요" in report


# 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
