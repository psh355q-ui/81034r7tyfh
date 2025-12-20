"""
Phase 15 CEO Speech Analysis - Enhanced SEC Analyzer Tests

Tests for:
- CEO Quote extraction
- Tone Shift detection
- Management Analysis
"""

import pytest
import asyncio
from datetime import datetime
from backend.data.sec_parser import SECParser
from backend.ai.sec_analyzer import SECAnalyzer
from backend.core.models.sec_analysis_models import (
    ManagementTone, SentimentTone, Quote, ToneShift, ToneShiftDirection
)


class TestCEOQuoteExtraction:
    """Test CEO quote extraction from MD&A sections"""
    
    def test_extract_forward_looking_quotes(self):
        """Test extraction of forward-looking statements"""
        parser = SECParser()
        
        sample_text = """
        We believe that our AI strategy will drive significant growth in the coming quarters.
        Looking ahead, we expect revenue to increase by 15-20% year-over-year.
        We anticipate strong demand for our data center products.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        assert len(quotes) >= 2
        assert any("believe" in q["text"].lower() for q in quotes)
        assert any("expect" in q["text"].lower() for q in quotes)
        assert all(q["type"] == "forward_looking" for q in quotes)
    
    def test_extract_strategy_quotes(self):
        """Test extraction of strategy statements"""
        parser = SECParser()
        
        sample_text = """
        Our strategy focuses on expanding our AI capabilities and market reach.
        Our approach emphasizes innovation and customer satisfaction.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        assert len(quotes) >= 1
        assert any(q["type"] == "strategy" for q in quotes)
    
    def test_extract_risk_mentions(self):
        """Test extraction of risk mentions"""
        parser = SECParser()
        
        sample_text = """
        We face significant risks related to supply chain disruptions.
        We recognize challenges in the competitive landscape.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        assert len(quotes) >= 1
        assert any(q["type"] == "risk_mention" for q in quotes)
    
    def test_extract_opportunity_quotes(self):
        """Test extraction of opportunity mentions"""
        parser = SECParser()
        
        sample_text = """
        We see tremendous opportunities in the AI market.
        We identify potential for growth in emerging markets.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        assert len(quotes) >= 1
        assert any(q["type"] == "opportunity" for q in quotes)
    
    def test_quote_deduplication(self):
        """Test that duplicate quotes are removed"""
        parser = SECParser()
        
        sample_text = """
        We believe in our strategy. We believe in our strategy.
        We expect growth. We expect growth.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        # Should have only unique quotes
        unique_texts = set(q["text"] for q in quotes)
        assert len(quotes) == len(unique_texts)
    
    def test_quote_length_filtering(self):
        """Test that too short or too long quotes are filtered"""
        parser = SECParser()
        
        sample_text = """
        We believe.
        We believe that our comprehensive strategy for artificial intelligence development and deployment will drive significant growth.
        We expect strong results in the coming quarters.
        """
        
        quotes = parser.extract_ceo_quotes(sample_text)
        
        # First quote too short, second too long, third should pass
        for quote in quotes:
            word_count = len(quote["text"].split())
            assert 5 <= word_count <= 50


class TestForwardLookingCounter:
    """Test forward-looking statement counter"""
    
    def test_count_forward_keywords(self):
        """Test counting of forward-looking keywords"""
        parser = SECParser()
        
        sample_text = """
        We expect revenue to grow. We anticipate strong demand.
        We believe our strategy will succeed. We plan to expand.
        """
        
        count = parser.count_forward_looking_statements(sample_text)
        
        # Should count: expect, anticipate, believe, plan, will
        assert count >= 5
    
    def test_case_insensitive_counting(self):
        """Test that counting is case-insensitive"""
        parser = SECParser()
        
        sample_text = "We EXPECT growth. We expect success."
        
        count = parser.count_forward_looking_statements(sample_text)
        
        assert count >= 2


class TestToneShiftDetection:
    """Test tone shift detection"""
    
    def test_detect_optimistic_shift(self):
        """Test detection of more optimistic tone"""
        analyzer = SECAnalyzer(api_key="test_key")
        
        prior_tone = ManagementTone(
            overall_sentiment=SentimentTone.NEUTRAL,
            sentiment_score=0.0,
            confidence_level="MEDIUM",
            key_phrases=[],
            concerns_mentioned=["market uncertainty"],
            opportunities_mentioned=[]
        )
        
        current_tone = ManagementTone(
            overall_sentiment=SentimentTone.POSITIVE,
            sentiment_score=0.5,
            confidence_level="HIGH",
            key_phrases=[],
            concerns_mentioned=[],
            opportunities_mentioned=["AI growth"]
        )
        
        shift = analyzer.detect_tone_shift(current_tone, prior_tone)
        
        assert shift.direction == ToneShiftDirection.MORE_OPTIMISTIC
        assert shift.magnitude == 0.5
        assert shift.signal == "POSITIVE"
        assert shift.is_significant  # magnitude > 0.3
    
    def test_detect_pessimistic_shift(self):
        """Test detection of more pessimistic tone"""
        analyzer = SECAnalyzer(api_key="test_key")
        
        prior_tone = ManagementTone(
            overall_sentiment=SentimentTone.POSITIVE,
            sentiment_score=0.4,
            confidence_level="HIGH",
            key_phrases=[],
            concerns_mentioned=[],
            opportunities_mentioned=["growth"]
        )
        
        current_tone = ManagementTone(
            overall_sentiment=SentimentTone.NEGATIVE,
            sentiment_score=-0.3,
            confidence_level="MEDIUM",
            key_phrases=[],
            concerns_mentioned=["supply chain", "competition"],
            opportunities_mentioned=[]
        )
        
        shift = analyzer.detect_tone_shift(current_tone, prior_tone)
        
        assert shift.direction == ToneShiftDirection.MORE_PESSIMISTIC
        assert shift.magnitude == 0.7
        assert shift.signal == "NEGATIVE"
        assert shift.is_significant
    
    def test_detect_similar_tone(self):
        """Test detection of similar tone"""
        analyzer = SECAnalyzer(api_key="test_key")
        
        prior_tone = ManagementTone(
            overall_sentiment=SentimentTone.NEUTRAL,
            sentiment_score=0.1,
            confidence_level="MEDIUM",
            key_phrases=[],
            concerns_mentioned=[],
            opportunities_mentioned=[]
        )
        
        current_tone = ManagementTone(
            overall_sentiment=SentimentTone.NEUTRAL,
            sentiment_score=0.15,
            confidence_level="MEDIUM",
            key_phrases=[],
            concerns_mentioned=[],
            opportunities_mentioned=[]
        )
        
        shift = analyzer.detect_tone_shift(current_tone, prior_tone)
        
        assert shift.direction == ToneShiftDirection.SIMILAR
        assert shift.magnitude == 0.05
        assert shift.signal == "NEUTRAL"
        assert not shift.is_significant  # magnitude < 0.3
    
    def test_key_changes_tracking(self):
        """Test tracking of key changes"""
        analyzer = SECAnalyzer(api_key="test_key")
        
        prior_tone = ManagementTone(
            overall_sentiment=SentimentTone.NEUTRAL,
            sentiment_score=0.0,
            confidence_level="LOW",
            key_phrases=[],
            concerns_mentioned=["old concern"],
            opportunities_mentioned=["old opportunity"]
        )
        
        current_tone = ManagementTone(
            overall_sentiment=SentimentTone.POSITIVE,
            sentiment_score=0.3,
            confidence_level="HIGH",
            key_phrases=[],
            concerns_mentioned=["new concern"],
            opportunities_mentioned=["new opportunity"]
        )
        
        shift = analyzer.detect_tone_shift(current_tone, prior_tone)
        
        assert len(shift.key_changes) > 0
        assert any("Confidence" in change for change in shift.key_changes)
        assert any("concerns" in change.lower() for change in shift.key_changes)


class TestManagementAnalysisModels:
    """Test Management Analysis data models"""
    
    def test_quote_model(self):
        """Test Quote model"""
        quote = Quote(
            text="We expect strong growth",
            quote_type="forward_looking",
            position=100,
            section="MD&A",
            sentiment=0.7
        )
        
        assert quote.text == "We expect strong growth"
        assert quote.quote_type == "forward_looking"
        assert quote.sentiment == 0.7
    
    def test_tone_shift_is_significant(self):
        """Test ToneShift.is_significant property"""
        # Significant shift
        shift1 = ToneShift(
            direction=ToneShiftDirection.MORE_OPTIMISTIC,
            magnitude=0.5,
            key_changes=[],
            signal="POSITIVE"
        )
        assert shift1.is_significant
        
        # Not significant shift
        shift2 = ToneShift(
            direction=ToneShiftDirection.SIMILAR,
            magnitude=0.1,
            key_changes=[],
            signal="NEUTRAL"
        )
        assert not shift2.is_significant


# Integration test (requires API key)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_management_analysis():
    """
    Integration test for full management analysis pipeline
    
    Requires ANTHROPIC_API_KEY environment variable
    """
    import os
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    # This would require actual SEC filing data
    # Placeholder for future implementation
    pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
