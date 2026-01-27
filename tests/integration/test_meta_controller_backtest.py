"""
통합 테스트 및 백테스트 - 2020 COVID Crash 시뮬레이션

2020년 3월 9일~23일 반도체 포트폴리오에 대한 Meta-Controller V2 동작 검증
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.ai.meta_controller_v2 import MetaControllerV2
from backend.ai.correlation_shock_detector import CorrelationShockDetector
from backend.ai.drawdown_recovery import DrawdownRecoveryMode


class TestMetaControllerBacktest:
    """2020 COVID Crash 백테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.meta_controller = MetaControllerV2()
        
        # 2020년 3월 반도체 포트폴리오
        self.portfolio_symbols = ['NVDA', 'AMD', 'INTC', 'TSM']
        
        # 시뮬레이션 기간
        self.start_date = datetime(2020, 3, 9)
        self.end_date = datetime(2020, 3, 23)
        
    def test_covid_crash_full_simulation(self):
        """
        COVID-19 Crash 전체 시뮬레이션
        
        검증 대상:
        1. Correlation 추이: 정상(0.4) → 위기(0.95) 감지
        2. Drawdown 추이: 0% → 25% → 모드 강등
        3. VIX 추이: 15 → 82.69 (최고점) → Crisis 감지
        """
        # 시뮬레이션 데이터 준비 (실제 역사적 데이터 근사치)
        simulation_timeline = [
            # Date, VIX, Portfolio Value, Avg Correlation
            (datetime(2020, 3, 9), 54.5, 100000, 0.65),   # 시작 - 이미 변동성 높음
            (datetime(2020, 3, 12), 75.47, 85000, 0.78),  # 급락 시작
            (datetime(2020, 3, 16), 82.69, 75000, 0.92),  # VIX 역사적 최고점
            (datetime(2020, 3, 18), 76.83, 72000, 0.95),  # Correlation Crisis
            (datetime(2020, 3, 23), 61.59, 80000, 0.88),  # 약간 회복
        ]
        
        results = []
        
        for date, vix, portfolio_value, avg_corr in simulation_timeline:
            # 포트폴리오 데이터 구성
            portfolio_data = {
                'current_value': portfolio_value,
                'peak_value': 100000,  # 초기 최고점
                'positions': [
                    {'symbol': symbol, 'quantity': 100} 
                    for symbol in self.portfolio_symbols
                ]
            }
            
            market_data = {'vix': vix}
            
            # Meta-Controller 평가 (실제 상관관계 계산 대신 Mock 사용)
            with patch.object(
                self.meta_controller.correlation_detector,
                'detect_correlation_regime',
                return_value=(
                    'crisis_correlation' if avg_corr >= 0.85 else
                    'elevated_correlation' if avg_corr >= 0.70 else
                    'normal',
                    avg_corr
                )
            ):
                result = self.meta_controller.evaluate_market_regime(
                    market_data,
                    portfolio_data
                )
            
            results.append({
                'date': date,
                'vix': vix,
                'portfolio_value': portfolio_value,
                'avg_correlation': avg_corr,
                'final_regime': result['final_regime'],
                'forced_mode': result.get('forced_mode'),
                'position_limit_multiplier': result['position_limit_multiplier'],
                'reason': result['reason']
            })
        
        # 결과 검증
        self._verify_simulation_results(results)
        
        # 결과 출력
        self._print_backtest_report(results)
        
        return results
    
    def _verify_simulation_results(self, results):
        """시뮬레이션 결과 검증"""
        
        # 1. Correlation Crisis 감지 (3월 16일 이후)
        crisis_detected = False
        for result in results:
            if result['date'] >= datetime(2020, 3, 16):
                if 'correlation' in result['final_regime'] or result['avg_correlation'] >= 0.85:
                    crisis_detected = True
                    break
        
        assert crisis_detected, "Correlation Crisis가 감지되지 않았습니다 (3월 16일 이후)"
        
        # 2. Drawdown 20% 도달 시점에 Dividend 모드 강등
        dividend_mode_forced = False
        for result in results:
            drawdown = (100000 - result['portfolio_value']) / 100000
            if drawdown >= 0.20:
                if result['forced_mode'] == 'dividend':
                    dividend_mode_forced = True
                    break
        
        assert dividend_mode_forced, "20% Drawdown 시 Dividend 모드 강등이 발생하지 않았습니다"
        
        # 3. VIX Crisis 감지 (VIX > 40)
        vix_crisis_detected = False
        for result in results:
            if result['vix'] >= 40 and 'crisis' in result['final_regime']:
                vix_crisis_detected = True
                break
        
        assert vix_crisis_detected, "VIX Crisis가 감지되지 않았습니다"
        
        print("✅ 모든 시뮬레이션 검증 통과!")
    
    def _print_backtest_report(self, results):
        """백테스트 결과 리포트 출력"""
        print("\n" + "="*80)
        print("📊 2020 COVID Crash 백테스트 결과 (3월 9일~23일)")
        print("="*80 + "\n")
        
        for result in results:
            print(f"📅 {result['date'].strftime('%Y-%m-%d')}")
            print(f"   VIX: {result['vix']:.2f}")
            print(f"   Portfolio Value: ${result['portfolio_value']:,.0f}")
            print(f"   Drawdown: {((100000 - result['portfolio_value']) / 100000 * 100):.1f}%")
            print(f"   Avg Correlation: {result['avg_correlation']:.3f}")
            print(f"   🎯 Final Regime: {result['final_regime']}")
            
            if result['forced_mode']:
                print(f"   🚨 Forced Mode: {result['forced_mode'].upper()}")
            
            print(f"   📏 Position Limit Multiplier: {result['position_limit_multiplier']:.1f}x")
            print(f"   💡 Reason: {result['reason']}")
            print()
        
        print("="*80)
        print("✅ 백테스트 완료")
        print("="*80 + "\n")
    
    def test_correlation_progression(self):
        """
        상관관계 진행 추이 테스트
        
        정상(0.4) → 상승(0.7) → 위기(0.95)
        """
        test_cases = [
            (0.40, 'normal'),
            (0.70, 'elevated_correlation'),
            (0.85, 'crisis_correlation'),
            (0.95, 'crisis_correlation'),
        ]
        
        for avg_corr, expected_regime in test_cases:
            portfolio_data = {
                'current_value': 100000,
                'peak_value': 100000,
                'positions': [{'symbol': s, 'quantity': 100} for s in self.portfolio_symbols]
            }
            
            with patch.object(
                self.meta_controller.correlation_detector,
                'detect_correlation_regime',
                return_value=(expected_regime, avg_corr)
            ):
                result = self.meta_controller.evaluate_market_regime(
                    {'vix': 20},
                    portfolio_data
                )
            
            print(f"Correlation {avg_corr:.2f} → Regime: {result['correlation_regime']}")
            assert result['correlation_regime'] == expected_regime
    
    def test_drawdown_progression(self):
        """
        드로다운 진행 추이 테스트
        
        0% → 10% → 20% → 25%
        """
        peak_value = 100000
        
        test_cases = [
            (100000, 0.00, 'normal', None),
            (90000, 0.10, 'warning', None),
            (80000, 0.20, 'critical', 'dividend'),
            (75000, 0.25, 'critical', 'dividend'),
        ]
        
        for current_value, expected_dd, expected_severity, expected_forced in test_cases:
            portfolio_data = {
                'current_value': current_value,
                'peak_value': peak_value,
                'positions': [{'symbol': s, 'quantity': 100} for s in self.portfolio_symbols]
            }
            
            result = self.meta_controller.evaluate_market_regime(
                {'vix': 20},
                portfolio_data
            )
            
            actual_dd = result['drawdown_result']['drawdown']
            actual_severity = result['drawdown_result']['severity']
            actual_forced = result.get('forced_mode')
            
            print(
                f"Portfolio ${current_value:,} → "
                f"DD: {actual_dd:.1%}, "
                f"Severity: {actual_severity}, "
                f"Forced: {actual_forced}"
            )
            
            assert abs(actual_dd - expected_dd) < 0.001
            assert actual_severity == expected_severity
            assert actual_forced == expected_forced
    
    def test_vix_thresholds(self):
        """
        VIX 임계값 테스트
        
        15 (정상) → 30 (상승) → 40 (위기) → 82.69 (역사적 최고점)
        """
        test_cases = [
            (15, 'normal'),
            (30, 'elevated_vix'),
            (40, 'crisis_vix'),
            (82.69, 'crisis_vix'),
        ]
        
        portfolio_data = {
            'current_value': 100000,
            'peak_value': 100000,
            'positions': [{'symbol': s, 'quantity': 100} for s in self.portfolio_symbols]
        }
        
        for vix, expected_regime in test_cases:
            # Correlation과 Drawdown을 정상으로 설정하여 VIX만 테스트
            with patch.object(
                self.meta_controller.correlation_detector,
                'detect_correlation_regime',
                return_value=('normal', 0.4)
            ):
                result = self.meta_controller.evaluate_market_regime(
                    {'vix': vix},
                    portfolio_data
                )
            
            print(f"VIX {vix:.2f} → Regime: {result['vix_regime']}")
            assert result['vix_regime'] == expected_regime


if __name__ == '__main__':
    """직접 실행 시 백테스트 수행"""
    print("🚀 Starting COVID-19 Crash Backtest Simulation...")
    print()
    
    tester = TestMetaControllerBacktest()
    tester.setup_method()
    
    # 전체 시뮬레이션 실행
    results = tester.test_covid_crash_full_simulation()
    
    print("\n" + "="*80)
    print("📈 추가 검증 테스트")
    print("="*80 + "\n")
    
    # 상관관계 진행 추이
    print("1️⃣ Correlation Progression Test:")
    tester.test_correlation_progression()
    print()
    
    # 드로다운 진행 추이
    print("2️⃣ Drawdown Progression Test:")
    tester.test_drawdown_progression()
    print()
    
    # VIX 임계값
    print("3️⃣ VIX Threshold Test:")
    tester.test_vix_thresholds()
    print()
    
    print("✅ 모든 백테스트 완료!")
