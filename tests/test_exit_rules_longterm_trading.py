"""
Exit Rules Tests - Long-Term & Trading Modes

TDD: Long-Term Thesis Violation + Trading Stop-Loss/Take-Profit
"""

import pytest
from backend.ai.exit_rules import LongTermExitRule, TradingExitRule, ExitRuleEngine


class TestLongTermExitRule:
    """Test Long-Term Exit Rule"""
    
    def setup_method(self):
        """Setup before each test"""
        self.exit_rule = LongTermExitRule()
    
    def test_thesis_intact_no_exit(self):
        """Test: Thesis intact, no exit triggered"""
        position = {
            'ticker': 'AAPL',
            'mode': 'long_term',
            'entry_price': 150.0,
            'current_price': 155.0
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'thesis_intact'
    
    def test_non_longterm_mode_ignored(self):
        """Test: Non-long_term mode ignored"""
        position = {
            'ticker': 'NVDA',
            'mode': 'aggressive',
            'entry_price': 500.0,
            'current_price': 600.0
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'mode_not_applicable'


class TestTradingExitRule:
    """Test Trading Exit Rule"""
    
    def setup_method(self):
        """Setup before each test"""
        self.exit_rule = TradingExitRule(stop_loss_pct=0.03, take_profit_pct=0.07)
    
    def test_stop_loss_triggered(self):
        """Test: Stop-Loss at -3% triggers exit"""
        position = {
            'ticker': 'TSLA',
            'mode': 'trading',
            'entry_price': 100.0,
            'current_price': 96.5  # -3.5% loss
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'stop_loss'
        assert result['action'] == 'force_liquidate'
        assert result['priority'] == 'immediate'
        assert result['details']['pnl_pct'] < -3.0
    
    def test_take_profit_triggered(self):
        """Test: Take-Profit at +7% triggers exit"""
        position = {
            'ticker': 'NVDA',
            'mode': 'trading',
            'entry_price': 500.0,
            'current_price': 537.0  # +7.4% profit
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'take_profit'
        assert result['action'] == 'liquidate'
        assert result['priority'] == 'normal'
        assert result['details']['pnl_pct'] > 7.0
    
    def test_within_range_no_exit(self):
        """Test: P&L within range, no exit"""
        position = {
            'ticker': 'AAPL',
            'mode': 'trading',
            'entry_price': 150.0,
            'current_price': 153.0  # +2% profit
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'within_range'
        assert -3.0 < result['details']['pnl_pct'] < 7.0
    
    def test_macd_dead_cross_triggers_exit(self):
        """Test: MACD dead cross triggers exit"""
        position = {
            'ticker': 'GOOGL',
            'mode': 'trading',
            'entry_price': 100.0,
            'current_price': 102.0  # +2%, within range
        }
        
        price_data = {
            'macd': {
                'macd': 1.5,
                'signal': 1.8,
                'previous_macd': 2.0,  # Was above
                'previous_signal': 1.7  # Now below (dead cross!)
            }
        }
        
        result = self.exit_rule.check_exit(position, price_data)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'macd_dead_cross'
        assert result['details']['dead_cross'] is True
    
    def test_macd_golden_cross_no_exit(self):
        """Test: MACD golden cross (bullish) no exit"""
        position = {
            'ticker': 'MSFT',
            'mode': 'trading',
            'entry_price': 300.0,
            'current_price': 305.0
        }
        
        price_data = {
            'macd': {
                'macd': 2.0,
                'signal': 1.8,
                'previous_macd': 1.7,  # Was below
                'previous_signal': 1.9  # Now above (golden cross)
            }
        }
        
        result = self.exit_rule.check_exit(position, price_data)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'within_range'
    
    def test_non_trading_mode_ignored(self):
        """Test: Non-trading mode ignored"""
        position = {
            'ticker': 'KO',
            'mode': 'dividend',
            'entry_price': 50.0,
            'current_price': 45.0  # Would trigger stop-loss if trading
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'mode_not_applicable'
    
    def test_boundary_stop_loss(self):
        """Test: Exactly -3% triggers stop-loss"""
        position = {
            'ticker': 'TEST',
            'mode': 'trading',
            'entry_price': 100.0,
            'current_price': 97.0  # Exactly -3%
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'stop_loss'
    
    def test_boundary_take_profit(self):
        """Test: Exactly +7% triggers take-profit"""
        position = {
            'ticker': 'TEST',
            'mode': 'trading',
            'entry_price': 100.0,
            'current_price': 107.0  # Exactly +7%
        }
        
        result = self.exit_rule.check_exit(position)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'take_profit'


class TestExitRuleEngine:
    """Test Exit Rule Engine Integration"""
    
    def setup_method(self):
        """Setup before each test"""
        self.engine = ExitRuleEngine()
    
    def test_dividend_mode_routing(self):
        """Test: Dividend mode routes to DividendExitRule"""
        position = {'ticker': 'JNJ', 'mode': 'dividend'}
        
        # Will return 'insufficient_dividend_history' since we don't have data
        result = self.engine.check_all_exits(position)
        
        # Just check it doesn't crash
        assert 'exit_triggered' in result
    
    def test_longterm_mode_routing(self):
        """Test: Long-term mode routes to LongTermExitRule"""
        position = {'ticker': 'AAPL', 'mode': 'long_term', 'entry_price': 150.0, 'current_price': 155.0}
        
        result = self.engine.check_all_exits(position)
        
        assert result['reason'] == 'thesis_intact'
    
    def test_trading_mode_routing(self):
        """Test: Trading mode routes to TradingExitRule"""
        position = {'ticker': 'NVDA', 'mode': 'trading', 'entry_price': 500.0, 'current_price': 550.0}
        
        result = self.engine.check_all_exits(position)
        
        assert result['exit_triggered'] is True
        assert result['reason'] == 'take_profit'


if __name__ == '__main__':
    """직접 실행 시 테스트 수행"""
    pytest.main([__file__, '-v', '--tb=short'])
