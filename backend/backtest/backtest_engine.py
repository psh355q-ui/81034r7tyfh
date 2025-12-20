"""
Backtest Engine - 30일 백테스트 메인 엔진

과거 데이터로 AI 트레이딩 시스템 성능 검증

작성일: 2025-12-15
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from backend.backtest.portfolio_manager import Portfolio
from backend.backtest.performance_metrics import calculate_all_metrics
from backend.data.collectors.api_clients.yahoo_client import get_yahoo_client
from backend.ai.macro.macro_analyzer_agent import get_macro_analyzer_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    30일 백테스트 엔진
    
    과거 30일 데이터로 시스템 성능 검증
    
    Usage:
        engine = BacktestEngine(
            start_date=datetime(2024, 11, 15),
            end_date=datetime(2024, 12, 14),
            initial_capital=10_000_000
        )
        
        result = await engine.run()
        engine.print_report(result)
    """
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10_000_000,
        test_ticker: str = "SPY"  # S&P 500 ETF로 테스트
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.test_ticker = test_ticker
        
        # Components
        self.yahoo_client = get_yahoo_client()
        self.macro_analyzer = get_macro_analyzer_agent()
        
        logger.info(
            f"BacktestEngine initialized: "
            f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
        )
    
    def get_trading_days(self) -> List[datetime]:
        """
        거래일 생성 (주말 제외)
        
        Returns:
            거래일 리스트
        """
        days = []
        current = self.start_date
        
        while current <= self.end_date:
            # 주말 제외 (월-금만)
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        
        return days
    
    async def get_market_data(
        self,
        ticker: str,
        date: datetime
    ) -> Dict:
        """
        특정 날짜의 시장 데이터
        
        Args:
            ticker: 종목 코드
            date: 날짜
            
        Returns:
            {date, open, high, low, close, volume}
        """
        try:
            # Yahoo Finance에서 해당 날짜 전후 데이터 가져오기
            data = self.yahoo_client.get_etf_data(ticker, period="5d")
            
            if not data:
                return None
            
            # 해당 날짜에 가장 가까운 데이터 찾기
            for i, dt in enumerate(data['dates']):
                if dt.date() == date.date():
                    return {
                        'date': dt,
                        'close': data['price'][i],
                        'volume': data['volume'][i]
                    }
            
            # 정확한 날짜가 없으면 가장 최근 데이터
            return {
                'date': data['dates'][-1],
                'close': data['price'][-1],
                'volume': data['volume'][-1]
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data for {ticker} on {date}: {e}")
            return None
    
    async def generate_simple_signal(
        self,
        ticker: str,
        date: datetime,
        market_data: Dict
    ) -> str:
        """
        간단한 매매 신호 생성 (Macro Analyzer 기반)
        
        Args:
            ticker: 종목
            date: 날짜
            market_data: 시장 데이터
            
        Returns:
            "BUY", "SELL", "HOLD"
        """
        try:
            # Macro Analyzer로 시장 체제 판단
            analysis = await self.macro_analyzer.analyze_market_regime()
            
            # Risk On → 매수
            # Risk Off → 매도
            # Neutral → 보유
            
            if analysis.regime.value == "risk_on":
                if analysis.stock_allocation >= 0.8:
                    return "BUY"
                else:
                    return "HOLD"
            
            elif analysis.regime.value == "risk_off":
                if analysis.stock_allocation <= 0.3:
                    return "SELL"
                else:
                    return "HOLD"
            
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Failed to generate signal: {e}")
            return "HOLD"
    
    async def run(self) -> Dict:
        """
        백테스트 실행
        
        Returns:
            결과 딕셔너리
        """
        logger.info("Starting backtest simulation...")
        
        # 1. 포트폴리오 초기화
        portfolio = Portfolio(self.initial_capital)
        
        # 2. 거래일 확인
        trading_days = self.get_trading_days()
        logger.info(f"Trading days: {len(trading_days)}")
        
        # 3. 일별 시뮬레이션
        for i, date in enumerate(trading_days):
            logger.info(f"\n[Day {i+1}/{len(trading_days)}] {date.strftime('%Y-%m-%d')}")
            
            # 시장 데이터
            market_data = await self.get_market_data(self.test_ticker, date)
            
            if not market_data:
                logger.warning(f"No market data for {date}, skipping")
                continue
            
            price = market_data['close']
            
            # 매매 신호
            signal = await self.generate_simple_signal(
                self.test_ticker,
                date,
                market_data
            )
            
            logger.info(f"Signal: {signal}, Price: ${price:.2f}")
            
            # 거래 실행
            if signal == "BUY":
                # 현금의 90%로 매수
                shares = int(portfolio.cash * 0.9 / price)
                if shares > 0:
                    portfolio.buy(
                        self.test_ticker,
                        shares,
                        price,
                        date
                    )
            
            elif signal == "SELL":
                # 전량 매도
                if self.test_ticker in portfolio.positions:
                    shares = portfolio.positions[self.test_ticker]
                    portfolio.sell(
                        self.test_ticker,
                        shares,
                        price,
                        date
                    )
            
            # 일별 스냅샷
            portfolio.record_daily_snapshot(
                date,
                {self.test_ticker: price}
            )
        
        # 4. 성과 계산
        logger.info("\n" + "="*60)
        logger.info("Backtest completed, calculating metrics...")
        
        summary = portfolio.get_summary()
        
        if len(portfolio.history) == 0:
            logger.error("No trading history!")
            return {}
        
        portfolio_values = [s.total_value for s in portfolio.history]
        
        metrics = calculate_all_metrics(
            initial_capital=self.initial_capital,
            final_value=summary['final_value'],
            portfolio_values=portfolio_values,
            trades=portfolio.trades,
            days=len(trading_days)
        )
        
        # 5. 결과 패키징
        result = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'trading_days': len(trading_days),
            'ticker': self.test_ticker,
            'initial_capital': self.initial_capital,
            'final_value': summary['final_value'],
            'metrics': metrics,
            'portfolio': portfolio,
            'summary': summary
        }
        
        return result
    
    def print_report(self, result: Dict):
        """
        백테스트 리포트 출력
        
        Args:
            result: run() 결과
        """
        if not result:
            print("No results to display")
            return
        
        metrics = result['metrics']
        
        print("\n" + "="*70)
        print("30일 백테스트 결과")
        print("="*70)
        
        print(f"\n기간: {result['start_date'].strftime('%Y-%m-%d')} ~ {result['end_date'].strftime('%Y-%m-%d')}")
        print(f"거래일: {result['trading_days']}일")
        print(f"종목: {result['ticker']}")
        
        print(f"\n{'='*70}")
        print("수익률")
        print(f"{'='*70}")
        print(f"초기 자본: ₩{result['initial_capital']:,.0f}")
        print(f"최종 자산: ₩{result['final_value']:,.0f}")
        print(f"총 수익률: {metrics.total_return:+.2%}")
        print(f"연환산 수익률: {metrics.annualized_return:+.2%}")
        
        print(f"\n{'='*70}")
        print("리스크 지표")
        print(f"{'='*70}")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
        print(f"변동성 (연): {metrics.volatility:.2%}")
        
        print(f"\n{'='*70}")
        print("거래 통계")
        print(f"{'='*70}")
        print(f"총 거래: {metrics.total_trades}회")
        print(f"승리: {metrics.winning_trades}회")
        print(f"패배: {metrics.losing_trades}회")
        print(f"승률: {metrics.win_rate:.1%}")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        
        if metrics.average_win > 0:
            print(f"평균 승리: {metrics.average_win:+.2%}")
        if metrics.average_loss < 0:
            print(f"평균 손실: {metrics.average_loss:+.2%}")
        
        print("\n" + "="*70)


async def main():
    """메인 실행"""
    
    # 백테스트 기간 (최근 30일)
    end_date = datetime(2024, 12, 14)
    start_date = end_date - timedelta(days=45)  # 주말 포함해서 여유있게
    
    # 엔진 생성
    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        initial_capital=10_000_000,
        test_ticker="SPY"  # S&P 500
    )
    
    # 실행
    result = await engine.run()
    
    # 리포트
    engine.print_report(result)
    
    print("\n✅ Backtest completed!")


if __name__ == "__main__":
    asyncio.run(main())
