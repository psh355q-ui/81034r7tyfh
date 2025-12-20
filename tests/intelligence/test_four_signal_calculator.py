"""
Four Signal Calculator 테스트
"""
import unittest
from datetime import datetime, timedelta
from backend.intelligence.four_signal_calculator import FourSignalCalculator, FourSignals


class TestFourSignalCalculator(unittest.TestCase):
    """Four Signal Calculator 단위 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.calculator = FourSignalCalculator()
    
    def test_diversity_integrity_single_source(self):
        """DI - 단일 출처"""
        articles = [
            {'title': 'Article 1', 'source': 'Bloomberg', 'published_at': datetime.now()},
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 단일 출처는 0.0
        self.assertEqual(signals.DI, 0.0)
    
    def test_diversity_integrity_multiple_sources(self):
        """DI - 복수 출처"""
        articles = [
            {'title': 'Article 1', 'source': 'Bloomberg', 'published_at': datetime.now()},
            {'title': 'Article 2', 'source': 'Reuters', 'published_at': datetime.now()},
            {'title': 'Article 3', 'source': 'CNBC', 'published_at': datetime.now()},
            {'title': 'Article 4', 'source': 'Yahoo Finance', 'published_at': datetime.now()},
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 4개 출처 -> 높은 점수
        self.assertGreater(signals.DI, 0.7)
    
    def test_temporal_naturalness_embargo(self):
        """TN - 엠바고 해제 (CPI 발표)"""
        now = datetime.now()
        
        articles = [
            {'title': 'CPI Article 1', 'source': 'Bloomberg', 'published_at': now},
            {'title': 'CPI Article 2', 'source': 'Reuters', 'published_at': now + timedelta(seconds=10)},
        ]
        
        calendar_event = {
            'event_type': 'CPI',
            'scheduled_at': now
        }
        
        signals = self.calculator.calculate(articles, calendar_event)
        
        # 엠바고 해제는 1.0
        self.assertEqual(signals.TN, 1.0)
    
    def test_temporal_naturalness_suspicious_velocity(self):
        """TN - 의심스러운 속도 (1분 내 30개)"""
        now = datetime.now()
        
        # 1분 내 30개 기사
        articles = [
            {
                'title': f'Article {i}',
                'source': f'Source {i}',
                'published_at': now + timedelta(seconds=i)
            }
            for i in range(30)
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 비정상적 속도 -> 낮은 점수
        self.assertLess(signals.TN, 0.5)
    
    def test_narrative_independence_copy_paste(self):
        """NI - 복붙 기사"""
        same_content = "Apple reports record earnings with $100B revenue."
        
        articles = [
            {
                'title': 'Apple Earnings',
                'content': same_content,
                'source': 'Source 1',
                'published_at': datetime.now()
            },
            {
                'title': 'Apple Earnings',
                'content': same_content,  # 동일한 내용
                'source': 'Source 2',
                'published_at': datetime.now()
            },
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 복붙 -> 낮은 점수
        self.assertLess(signals.NI, 0.5)
    
    def test_narrative_independence_unique(self):
        """NI - 독립적 기사"""
        articles = [
            {
                'title': 'Apple Earnings Beat',
                'content': 'Apple Inc reported quarterly earnings that exceeded analyst expectations.',
                'source': 'Bloomberg',
                'published_at': datetime.now()
            },
            {
                'title': 'AAPL Revenue Growth',
                'content': 'The tech giant saw significant revenue growth in its services division.',
                'source': 'Reuters',
                'published_at': datetime.now()
            },
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 독립적 취재 -> 높은 점수
        self.assertGreater(signals.NI, 0.5)
    
    def test_event_legitimacy_matched(self):
        """EL - 경제 캘린더 매칭"""
        now = datetime.now()
        
        articles = [
            {
                'title': 'CPI rises 3.2%',
                'source': 'Bloomberg',
                'published_at': now + timedelta(minutes=5)  # 5분 후 발표
            }
        ]
        
        calendar_event = {
            'event_name': 'CPI',
            'scheduled_at': now,
            'event_type': 'CPI'
        }
        
        signals = self.calculator.calculate(articles, calendar_event)
        
        # 30분 내 매칭 -> 1.0
        self.assertEqual(signals.EL, 1.0)
    
    def test_event_legitimacy_no_match(self):
        """EL - 매칭 없음"""
        articles = [
            {
                'title': 'General news',
                'source': 'News Site',
                'published_at': datetime.now()
            }
        ]
        
        signals = self.calculator.calculate(articles)
        
        # 일반 뉴스 -> 0.5
        self.assertEqual(signals.EL, 0.5)
    
    def test_overall_score(self):
        """전체 점수 계산"""
        now = datetime.now()
        
        # 좋은 클러스터: 여러 출처, 자연스러운 시간, 독립적 내용, 캘린더 매칭
        articles = [
            {
                'title': 'CPI Article 1',
                'content': 'Consumer prices rose 3.2% in October, exceeding forecasts.',
                'source': 'Bloomberg',
                'published_at': now
            },
            {
                'title': 'Inflation Data Released',
                'content': 'Latest inflation figures show prices increasing at annual rate.',
                'source': 'Reuters',
                'published_at': now + timedelta(minutes=1)
            },
            {
                'title': 'CPI Report Analysis',
                'content': 'Economic analysts review the consumer price index numbers.',
                'source': 'WSJ',
                'published_at': now + timedelta(minutes=3)
            },
        ]
        
        calendar_event = {
            'event_type': 'CPI',
            'scheduled_at': now
        }
        
        signals = self.calculator.calculate(articles, calendar_event)
        
        # 전체 점수 확인
        self.assertGreater(signals.overall_score, 0.7)
        
        # 개별 신호 확인
        print(f"\nTest Overall Score:")
        print(f"  DI: {signals.DI:.2f}")
        print(f"  TN: {signals.TN:.2f}")
        print(f"  NI: {signals.NI:.2f}")
        print(f"  EL: {signals.EL:.2f}")
        print(f"  Overall: {signals.overall_score:.2f}")


if __name__ == '__main__':
    unittest.main()
