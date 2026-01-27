"""
Liquidity Guardian 테스트
"""

import pytest
from unittest.mock import Mock, patch
from backend.ai.liquidity_guardian import LiquidityGuardian


class TestLiquidityGuardian:
    """LiquidityGuardian 클래스 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.guardian = LiquidityGuardian()
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_large_order_rejection(self, mock_ticker):
        """대형주 소량 주문: AAPL 100주 → allow=True"""
        # Mock 설정: AAPL 일평균 거래량 1000만주
        mock_hist = Mock()
        mock_hist.tail.return_value = Mock()
        mock_hist.tail.return_value.mean.return_value = 10000000  # 1000만주
        
        mock_today = Mock()
        mock_today.iloc.return_value = {
            'Close': 150.0,
            'High': 151.0,
            'Low': 149.0
        }
        mock_hist.tail.side_effect = [
            Mock(mean=lambda: 10000000),  # volume 계산용
            mock_today  # spread 계산용
        ]
        
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = self.guardian.check_liquidity('AAPL', 100, 15000)
        
        assert result['allow'] is True
        assert result['volume_impact'] == 0.001  # 100 / 10000000 = 0.001%
        assert result['avg_volume'] == 10000000
        assert 'Order approved' in result['reason']
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_small_stock_large_order_rejection(self, mock_ticker):
        """소형주 대량 주문: SMCI 10,000주 (일평균 6%) → allow=False"""
        # Mock 설정: SMCI 일평균 거래량 15만주
        mock_hist = Mock()
        mock_hist.tail.return_value = Mock()
        mock_hist.tail.return_value.mean.return_value = 150000  # 15만주
        
        mock_today = Mock()
        mock_today.iloc.return_value = {
            'Close': 300.0,
            'High': 305.0,
            'Low': 295.0
        }
        mock_hist.tail.side_effect = [
            Mock(mean=lambda: 150000),  # volume 계산용
            mock_today  # spread 계산용
        ]
        
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = self.guardian.check_liquidity('SMCI', 10000, 3000000)
        
        assert result['allow'] is False
        assert result['volume_impact'] == 0.067  # 10000 / 150000 ≈ 6.7%
        assert result['avg_volume'] == 150000
        assert 'exceeds 5%' in result['reason']
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_high_spread_warning(self, mock_ticker):
        """높은 스프레드: COIN, spread 2.5% → allow=True, warning 메시지"""
        # Mock 설정: COIN 일평균 거래량 1000만주, 높은 스프레드
        mock_hist = Mock()
        mock_hist.tail.return_value = Mock()
        mock_hist.tail.return_value.mean.return_value = 10000000  # 1000만주
        
        mock_today = Mock()
        mock_today.iloc.return_value = {
            'Close': 100.0,
            'High': 105.0,  # 높은 스프레드: (105-95)/100 = 10%
            'Low': 95.0
        }
        mock_hist.tail.side_effect = [
            Mock(mean=lambda: 10000000),  # volume 계산용
            mock_today  # spread 계산용
        ]
        
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = self.guardian.check_liquidity('COIN', 1000, 100000)
        
        assert result['allow'] is True
        assert result['volume_impact'] == 0.0001  # 1000 / 10000000 = 0.01%
        assert result['spread'] == 0.1  # 10%
        assert result['warning'] is not None
        assert 'High bid-ask spread' in result['warning']
        assert 'warning' in result['reason']
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_insufficient_data(self, mock_ticker):
        """데이터 부족 시 처리"""
        # Mock 설정: 데이터가 5일 미만
        mock_hist = Mock()
        mock_hist.__len__ = Mock(return_value=3)  # 3일 데이터만 있음
        
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = self.guardian.check_liquidity('UNKNOWN', 100, 10000)
        
        assert result['allow'] is True  # 기본값은 허용
        assert result['avg_volume'] == 0
        assert result['spread'] == 0.0
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_api_error_handling(self, mock_ticker):
        """API 에러 핸들링"""
        # Mock 설정: API 호출 예외 발생
        mock_ticker.side_effect = Exception("API Error")
        
        result = self.guardian.check_liquidity('ERROR', 100, 10000)
        
        assert result['allow'] is True  # 에러 시 기본값은 허용
        assert 'Liquidity check failed' in result['reason']
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_order_value_impact(self, mock_ticker):
        """주문 가치 영향도 체크"""
        # Mock 설정: 시가총액 100억
        mock_info = {'marketCap': 10000000000}  # 100억
        mock_ticker.return_value.info = mock_info
        
        # 1% 미만 주문
        result1 = self.guardian.check_order_value_impact('TEST', 500000)  # 50만원
        
        assert result1['allow'] is True
        assert result1['impact_ratio'] == 0.05  # 50만 / 100억 = 0.5%
        assert 'acceptable' in result1['reason']
        
        # 1% 이상 주문
        result2 = self.guardian.check_order_value_impact('TEST', 2000000)  # 2000만원
        
        assert result2['allow'] is True
        assert result2['impact_ratio'] == 0.2  # 2000만 / 100억 = 2%
        assert result2['warning'] is not None
        assert 'Large order' in result2['warning']
    
    @patch('backend.ai.liquidity_guardian.yf.Ticker')
    def test_liquidity_summary(self, mock_ticker):
        """유동성 요약 정보 테스트"""
        # Mock 설정
        mock_hist = Mock()
        mock_hist.tail.return_value = Mock()
        mock_hist.tail.return_value.mean.return_value = 5000000  # 500만주
        
        mock_today = Mock()
        mock_today.iloc.return_value = {
            'Close': 100.0,
            'High': 101.0,
            'Low': 99.0
        }
        mock_hist.tail.side_effect = [
            Mock(mean=lambda: 5000000),  # volume 계산용
            mock_today  # spread 계산용
        ]
        
        mock_info = {'marketCap': 5000000000}  # 50억
        mock_ticker.return_value.history.return_value = mock_hist
        mock_ticker.return_value.info = mock_info
        
        summary = self.guardian.get_liquidity_summary('TEST')
        
        assert summary['symbol'] == 'TEST'
        assert summary['avg_daily_volume'] == 5000000
        assert summary['bid_ask_spread'] == 0.02  # (101-99)/100 = 2%
        assert summary['market_cap'] == 5000000000
        assert summary['liquidity_grade'] == 'HIGH'  # 100만주 이상
    
    def test_liquidity_grades(self):
        """유동성 등급 분류 테스트"""
        # Mock 설정
        with patch('backend.ai.liquidity_guardian.yf.Ticker') as mock_ticker:
            mock_hist = Mock()
            mock_hist.tail.return_value = Mock()
            mock_today = Mock()
            mock_today.iloc.return_value = {'Close': 100.0, 'High': 101.0, 'Low': 99.0}
            mock_hist.tail.side_effect = [
                Mock(mean=lambda: 2000000),  # HIGH 등급
                mock_today
            ]
            
            mock_info = {'marketCap': 1000000000}
            mock_ticker.return_value.history.return_value = mock_hist
            mock_ticker.return_value.info = mock_info
            
            # HIGH 등급 (100만주 이상)
            summary1 = self.guardian.get_liquidity_summary('HIGH')
            assert summary1['liquidity_grade'] == 'HIGH'
            
            # MEDIUM 등급 (10만주 이상)
            mock_hist.tail.side_effect = [
                Mock(mean=lambda: 500000),  # MEDIUM 등급
                mock_today
            ]
            summary2 = self.guardian.get_liquidity_summary('MEDIUM')
            assert summary2['liquidity_grade'] == 'MEDIUM'
            
            # LOW 등급 (10만주 미만)
            mock_hist.tail.side_effect = [
                Mock(mean=lambda: 50000),  # LOW 등급
                mock_today
            ]
            summary3 = self.guardian.get_liquidity_summary('LOW')
            assert summary3['liquidity_grade'] == 'LOW'
    
    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        # Mock 설정
        with patch('backend.ai.liquidity_guardian.yf.Ticker') as mock_ticker:
            mock_hist = Mock()
            mock_hist.tail.return_value = Mock()
            mock_hist.tail.return_value.mean.return_value = 1000000
            mock_today = Mock()
            mock_today.iloc.return_value = {'Close': 100.0, 'High': 101.0, 'Low': 99.0}
            mock_hist.tail.side_effect = [
                Mock(mean=lambda: 1000000),
                mock_today
            ]
            
            mock_info = {'marketCap': 1000000000}
            mock_ticker.return_value.history.return_value = mock_hist
            mock_ticker.return_value.info = mock_info
            
            # 첫 번째 호출 - API 호출
            result1 = self.guardian.check_liquidity('CACHE', 100, 10000)
            assert mock_ticker.return_value.history.call_count == 1
            
            # 두 번째 호출 - 캐시 사용
            result2 = self.guardian.check_liquidity('CACHE', 200, 20000)
            assert mock_ticker.return_value.history.call_count == 1  # 추가 호출 없음
            
            # 결과는 동일해야 함
            assert result1['avg_volume'] == result2['avg_volume']
            assert result1['spread'] == result2['spread']
    
    def test_custom_thresholds(self):
        """사용자 정의 임계값 테스트"""
        # 더 엄격한 임계값 설정
        strict_guardian = LiquidityGuardian(volume_threshold=0.01, spread_threshold=0.01)
        
        with patch('backend.ai.liquidity_guardian.yf.Ticker') as mock_ticker:
            mock_hist = Mock()
            mock_hist.tail.return_value = Mock()
            mock_hist.tail.return_value.mean.return_value = 1000000  # 100만주
            
            mock_today = Mock()
            mock_today.iloc.return_value = {
                'Close': 100.0,
                'High': 102.0,  # 2% 스프레드
                'Low': 98.0
            }
            mock_hist.tail.side_effect = [
                Mock(mean=lambda: 1000000),
                mock_today
            ]
            
            mock_ticker.return_value.history.return_value = mock_hist
            
            # 2% 주문 (기본 5% 임계값에서는 통과하지만 1% 임계값에서는 실패)
            result = strict_guardian.check_liquidity('TEST', 20000, 2000000)
            
            assert result['allow'] is False
            assert 'exceeds 1%' in result['reason']
            
            # 2% 스프레드 (기본 2% 임계값에서는 통과하지만 1% 임계값에서는 경고)
            result2 = strict_guardian.check_liquidity('TEST2', 5000, 500000)
            
            assert result2['allow'] is True
            assert result2['warning'] is not None
            assert 'High bid-ask spread' in result2['warning']