"""
Dividend Analyzer - 배당 분석 및 시뮬레이션

Phase 21: Dividend Intelligence Module - Step 1.3
Date: 2025-12-25

Features:
- 포트

폴리오 월별/연별 배당금 계산 (세후)
- DRIP (Dividend Reinvestment Plan) 복리 시뮬레이션
- 예수금 추가 시뮬레이션
- YOC (Yield on Cost) 계산
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class DividendAnalyzer:
    """배당 분석 및 시뮬레이션"""
    
    # 환율 (KRW/USD) - 실제로는 API에서 가져와야 함
    DEFAULT_EXCHANGE_RATE = 1300.0
    
    # 세율
    US_WITHHOLDING_TAX = 0.15  # 미국 원천징수 15%
    KR_FINANCIAL_INCOME_TAX = 0.154  # 한국 금융소득세 15.4% (14% + 1.4% 지방세)
    
    async def calculate_portfolio_income(self, positions: List[Dict], exchange_rate: Optional[float] = None) -> Dict:
        """
        포트폴리오 월별/연별 예상 배당금 (세후)
        
        Args:
            positions: [
                {"ticker": "JNJ", "shares": 100, "avg_price": 150},
                {"ticker": "PG", "shares": 50, "avg_price": 145},
                ...
            ]
            exchange_rate: 환율 (KRW/USD), None이면 DEFAULT 사용
        
        Returns:
            {
                "annual_gross_usd": 5000,  # 연간 총배당 (세전, USD)
                "annual_gross_krw": 6500000,  # 연간 총배당 (세전, KRW)
                "annual_net_usd": 4000,  # 연간 순배당 (세후, USD)
                "annual_net_krw": 5200000,  # 연간 순배당 (세후, KRW)
                "monthly_avg_usd": 333,  # 월평균 (세후, USD)
                "monthly_avg_krw": 433333,  # 월평균 (세후, KRW)
                "by_month": {
                    "2025-01": {"usd": 400, "krw": 520000},
                    "2025-02": {"usd": 300, "krw": 390000},
                    ...
                },
                "yoc": 5.2,  # Yield on Cost (%)
                "effective_tax_rate": 27.6  # 실효 세율 (%)
            }
        """
        
        if exchange_rate is None:
            exchange_rate = self.DEFAULT_EXCHANGE_RATE
        
        total_gross_usd = 0.0
        total_investment_usd = 0.0
        monthly_dividends = {f"2025-{m:02d}": {"usd": 0.0, "krw": 0.0} for m in range(1, 13)}
        
        for position in positions:
            ticker = position['ticker']
            shares = position['shares']
            avg_price = position['avg_price']
            
            try:
                # yfinance에서 배당 데이터 가져오기
                stock = yf.Ticker(ticker)
                dividends = stock.dividends
                
                if dividends.empty:
                    logger.warning(f"No dividend data for {ticker}")
                    continue
                
                # 최근 12개월 배당금 (연간 배당금 추정)
                # yfinance는 timezone-aware datetime을 반환하므로 비교를 위해 timezone-aware로 변환
                one_year_ago = datetime.now(dividends.index.tz) - timedelta(days=365)
                recent_dividends = dividends[dividends.index >= one_year_ago]
                annual_dividend_per_share = float(recent_dividends.sum())
                
                # 포지션 배당금
                position_dividend_usd = annual_dividend_per_share * shares
                total_gross_usd += position_dividend_usd
                
                # 투자금
                total_investment_usd += avg_price * shares
                
                # 월별 배당금 배분 (간단히 12개월로 나눔)
                # 실제로는 배당 지급 일정에 맞춰야 함
                monthly_dividend = position_dividend_usd / 12
                for month in monthly_dividends:
                    monthly_dividends[month]["usd"] += monthly_dividend
                
            except Exception as e:
                logger.error(f"Failed to get dividend for {ticker}: {e}")
        
        # 세후 계산
        # 1단계: 미국 원천징수 (15%)
        after_us_tax_usd = total_gross_usd * (1 - self.US_WITHHOLDING_TAX)
        
        # 2단계: 한국 금융소득세 (15.4%)
        after_all_tax_usd = after_us_tax_usd * (1 - self.KR_FINANCIAL_INCOME_TAX)
        
        # 실효 세율
        effective_tax_rate = ((total_gross_usd - after_all_tax_usd) / total_gross_usd) * 100 if total_gross_usd > 0 else 0
        
        # YOC (Yield on Cost)
        yoc = (after_all_tax_usd / total_investment_usd) * 100 if total_investment_usd > 0 else 0
        
        # 월별 배당금 세후 계산
        tax_multiplier = (1 - self.US_WITHHOLDING_TAX) * (1 - self.KR_FINANCIAL_INCOME_TAX)
        for month in monthly_dividends:
            gross_usd = monthly_dividends[month]["usd"]
            net_usd = gross_usd * tax_multiplier
            monthly_dividends[month] = {
                "usd": round(net_usd, 2),
                "krw": round(net_usd * exchange_rate)
            }
        
        return {
            "annual_gross_usd": round(total_gross_usd, 2),
            "annual_gross_krw": round(total_gross_usd * exchange_rate),
            "annual_net_usd": round(after_all_tax_usd, 2),
            "annual_net_krw": round(after_all_tax_usd * exchange_rate),
            "monthly_avg_usd": round(after_all_tax_usd / 12, 2),
            "monthly_avg_krw": round((after_all_tax_usd * exchange_rate) / 12),
            "by_month": monthly_dividends,
            "yoc": round(yoc, 2),
            "effective_tax_rate": round(effective_tax_rate, 2),
            "total_investment_usd": round(total_investment_usd, 2),
            "total_investment_krw": round(total_investment_usd * exchange_rate)
        }
    
    async def simulate_drip(
        self,
        initial: float,
        monthly_contribution: float,
        years: int,
        cagr: float,
        dividend_yield: float,
        reinvest: bool = True,
        exchange_rate: Optional[float] = None
    ) -> List[Dict]:
        """
        배당 복리 시뮬레이션 (DRIP: Dividend Reinvestment Plan)
        
        Args:
            initial: 초기 투자금 (USD)
            monthly_contribution: 월 적립금 (USD)
            years: 투auto 기간 (년)
            cagr: 연평균 성장률 (%, 예: 7.0)
            dividend_yield: 배당률 (%, 예: 4.0)
            reinvest: 배당 재투자 여부
            exchange_rate: 환율 (KRW/USD)
        
        Returns:
            [
                {
                    "year": 1,
                    "portfolio_value_usd": 105000,
                    "portfolio_value_krw": 136500000,
                    "annual_dividends_usd": 5000,
                    "annual_dividends_krw": 6500000,
                    "cumulative_dividends_usd": 5000,
                    "cumulative_dividends_krw": 6500000,
                    "total_contribution_usd": 100000,
                    "profit_usd": 10000
                },
                ...
            ]
        """
        
        if exchange_rate is None:
            exchange_rate = self.DEFAULT_EXCHANGE_RATE
        
        results = []
        portfolio_value = initial
        cumulative_dividends = 0
        total_contribution = initial
        
        for year in range(1, years + 1):
            # 월적립 반영
            yearly_contribution = monthly_contribution * 12
            portfolio_value += yearly_contribution
            total_contribution += yearly_contribution
            
            # 배당금 계산 (세후)
            gross_dividends = portfolio_value * (dividend_yield / 100)
            net_dividends = gross_dividends * (1 - self.US_WITHHOLDING_TAX) * (1 - self.KR_FINANCIAL_INCOME_TAX)
            cumulative_dividends += net_dividends
            
            # 배당 재투자 여부
            if reinvest:
                portfolio_value += net_dividends
            
            # 자본 이득 (CAGR 적용)
            portfolio_value *= (1 + cagr / 100)
            
            # 수익
            profit = portfolio_value - total_contribution + (cumulative_dividends if not reinvest else 0)
            
            results.append({
                "year": year,
                "portfolio_value_usd": round(portfolio_value, 2),
                "portfolio_value_krw": round(portfolio_value * exchange_rate),
                "annual_dividends_usd": round(net_dividends, 2),
                "annual_dividends_krw": round(net_dividends * exchange_rate),
                "cumulative_dividends_usd": round(cumulative_dividends, 2),
                "cumulative_dividends_krw": round(cumulative_dividends * exchange_rate),
                "total_contribution_usd": round(total_contribution, 2),
                "total_contribution_krw": round(total_contribution * exchange_rate),
                "profit_usd": round(profit, 2),
                "profit_krw": round(profit * exchange_rate)
            })
        
        return results
    
    async def simulate_cash_injection(
        self,
        current_positions: List[Dict],
        inject_amount_usd: float,
        exchange_rate: Optional[float] = None
    ) -> Dict:
        """
        예수금 추가 시뮬레이션
        
        현재 포트폴리오 비율대로 종목별 추가 매수
        세후 배당금 변화 계산
        
        Args:
            current_positions: 현재 포지션 리스트
            inject_amount_usd: 추가 투자금 (USD)
            exchange_rate: 환율
        
        Returns:
            {
                "before": {
                    "annual_net_usd": 4000,
                    "monthly_avg_usd": 333,
                    ...
                },
                "after": {
                    "annual_net_usd": 4800,
                    "monthly_avg_usd": 400,
                    ...
                },
                "increase": {
                    "annual_usd": 800,
                    "monthly_usd": 67,
                    "percentage": 20.0
                },
                "new_positions": [
                    {"ticker": "JNJ", "additional_shares": 5, "cost": 750},
                    ...
                ]
            }
        """
        
        if exchange_rate is None:
            exchange_rate = self.DEFAULT_EXCHANGE_RATE
        
        # 현재 배당 수입
        before_income = await self.calculate_portfolio_income(current_positions, exchange_rate)
        
        # 현재 포트폴리오 비율 계산
        total_value = sum(p['shares'] * p['avg_price'] for p in current_positions)
        
        new_positions = []
        for pos in current_positions:
            weight = (pos['shares'] * pos['avg_price']) / total_value
            allocation = inject_amount_usd * weight
            
            # 현재 주가 (간단히 avg_price 사용)
            current_price = pos['avg_price']
            additional_shares = int(allocation / current_price)
            
            if additional_shares > 0:
                new_positions.append({
                    **pos,
                    'shares': pos['shares'] + additional_shares
                })
                
                logger.info(f"Added {additional_shares} shares of {pos['ticker']} at ${current_price}")
        
        # 추가 후 배당 수입
        after_income = await self.calculate_portfolio_income(new_positions, exchange_rate)
        
        # 증가량
        increase_annual_usd = after_income['annual_net_usd'] - before_income['annual_net_usd']
        increase_monthly_usd = after_income['monthly_avg_usd'] - before_income['monthly_avg_usd']
        increase_percentage = (increase_annual_usd / before_income['annual_net_usd']) * 100 if before_income['annual_net_usd'] > 0 else 0
        
        return {
            "before": before_income,
            "after": after_income,
            "increase": {
                "annual_usd": round(increase_annual_usd, 2),
                "annual_krw": round(increase_annual_usd * exchange_rate),
                "monthly_usd": round(increase_monthly_usd, 2),
                "monthly_krw": round(increase_monthly_usd * exchange_rate),
                "percentage": round(increase_percentage, 2)
            },
            "injection_amount_usd": inject_amount_usd,
            "injection_amount_krw": round(inject_amount_usd * exchange_rate)
        }


# CLI 실행
async def main():
    """테스트 실행"""
    
    analyzer = DividendAnalyzer()
    
    print("=" * 60)
    print("Dividend Analyzer Test")
    print("=" * 60)
    print()
    
    # 테스트 포트폴리오
    test_portfolio = [
        {"ticker": "JNJ", "shares": 100, "avg_price": 150},
        {"ticker": "PG", "shares": 50, "avg_price": 145},
        {"ticker": "KO", "shares": 150, "avg_price": 60}
    ]
    
    # 1. 포트폴리오 배당 수입 계산
    print("\n1️⃣ Portfolio Income Calculation")
    print("-" * 60)
    income = await analyzer.calculate_portfolio_income(test_portfolio)
    print(f"Annual Dividend (Net): ${income['annual_net_usd']:,.2f} (₩{income['annual_net_krw']:,})")
    print(f"Monthly Average: ${income['monthly_avg_usd']:,.2f} (₩{income['monthly_avg_krw']:,})")
    print(f"YOC: {income['yoc']}%")
    print(f"Effective Tax Rate: {income['effective_tax_rate']}%")
    
    # 2. DRIP 시뮬레이션
    print("\n2️⃣ DRIP Simulation (10 years)")
    print("-" * 60)
    drip_results = await analyzer.simulate_drip(
        initial=100000,  # $100k
        monthly_contribution=1000,  # $1k/month
        years=10,
        cagr=7.0,
        dividend_yield=4.0,
        reinvest=True
    )
    
    print(f"Year 1: ${drip_results[0]['portfolio_value_usd']:,.2f} (₩{drip_results[0]['portfolio_value_krw']:,})")
    print(f"Year 5: ${drip_results[4]['portfolio_value_usd']:,.2f} (₩{drip_results[4]['portfolio_value_krw']:,})")
    print(f"Year 10: ${drip_results[9]['portfolio_value_usd']:,.2f} (₩{drip_results[9]['portfolio_value_krw']:,})")
    print(f"Total Dividends: ${drip_results[9]['cumulative_dividends_usd']:,.2f}")
    print(f"Total Profit: ${drip_results[9]['profit_usd']:,.2f}")
    
    # 3. 예수금 추가 시뮬레이션
    print("\n3️⃣ Cash Injection Simulation")
    print("-" * 60)
    injection_result = await analyzer.simulate_cash_injection(
        current_positions=test_portfolio,
        inject_amount_usd=10000  # $10k 추가
    )
    
    print(f"Before: ${injection_result['before']['annual_net_usd']:,.2f}/year")
    print(f"After: ${injection_result['after']['annual_net_usd']:,.2f}/year")
    print(f"Increase: ${injection_result['increase']['annual_usd']:,.2f}/year (+{injection_result['increase']['percentage']:.1f}%)")
    print(f"Monthly Increase: ${injection_result['increase']['monthly_usd']:,.2f}/month")
    
    print("\n" + "=" * 60)
    print("✅ Test completed")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
