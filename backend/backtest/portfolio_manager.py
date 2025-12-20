"""
Portfolio Manager - 백테스트용 포트폴리오 관리

백테스트 시뮬레이션에서 포지션 및 현금 관리

작성일: 2025-12-15
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradeAction(Enum):
    """거래 액션"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Trade:
    """거래 기록"""
    date: datetime
    action: TradeAction
    ticker: str
    shares: int
    price: float
    commission: float
    total_cost: float


@dataclass
class PortfolioSnapshot:
    """포트폴리오 스냅샷"""
    date: datetime
    cash: float
    positions: Dict[str, int]  # {ticker: shares}
    position_values: Dict[str, float]  # {ticker: value}
    total_value: float
    daily_return: float = 0.0


class Portfolio:
    """
    백테스트 포트폴리오 관리자
    
    현금 및 포지션을 관리하고 거래를 실행합니다.
    
    Usage:
        portfolio = Portfolio(initial_capital=10_000_000)
        
        # 매수
        portfolio.buy("AAPL", shares=100, price=175.0, date=today)
        
        # 매도
        portfolio.sell("AAPL", shares=50, price=180.0, date=today)
        
        # 포트폴리오 가치
        value = portfolio.get_total_value(market_prices)
    """
    
    # 거래 비용
    COMMISSION_RATE = 0.001  # 0.1%
    SLIPPAGE_RATE = 0.0005   # 0.05%
    
    def __init__(self, initial_capital: float):
        """
        Args:
            initial_capital: 초기 자본
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, int] = {}  # {ticker: shares}
        
        # 거래 및 히스토리
        self.trades: List[Trade] = []
        self.history: List[PortfolioSnapshot] = []
        
        logger.info(f"Portfolio initialized with ₩{initial_capital:,.0f}")
    
    def buy(
        self,
        ticker: str,
        shares: int,
        price: float,
        date: datetime
    ) -> bool:
        """
        매수
        
        Args:
            ticker: 종목 코드
            shares: 주식 수
            price: 가격
            date: 날짜
            
        Returns:
            성공 여부
        """
        if shares <= 0:
            return False
        
        # 비용 계산 (수수료 + 슬리피지)
        gross_cost = shares * price
        commission = gross_cost * self.COMMISSION_RATE
        slippage = gross_cost * self.SLIPPAGE_RATE
        total_cost = gross_cost + commission + slippage
        
        # 현금 확인
        if total_cost > self.cash:
            logger.warning(
                f"Insufficient cash for {ticker}: "
                f"need ₩{total_cost:,.0f}, have ₩{self.cash:,.0f}"
            )
            return False
        
        # 거래 실행
        self.cash -= total_cost
        self.positions[ticker] = self.positions.get(ticker, 0) + shares
        
        # 기록
        trade = Trade(
            date=date,
            action=TradeAction.BUY,
            ticker=ticker,
            shares=shares,
            price=price,
            commission=commission + slippage,
            total_cost=total_cost
        )
        self.trades.append(trade)
        
        logger.info(
            f"BUY {shares} {ticker} @ ₩{price:,.0f} = ₩{total_cost:,.0f}"
        )
        
        return True
    
    def sell(
        self,
        ticker: str,
        shares: int,
        price: float,
        date: datetime
    ) -> bool:
        """
        매도
        
        Args:
            ticker: 종목 코드
            shares: 주식 수
            price: 가격
            date: 날짜
            
        Returns:
            성공 여부
        """
        if shares <= 0:
            return False
        
        # 보유 확인
        if ticker not in self.positions or self.positions[ticker] < shares:
            logger.warning(
                f"Insufficient shares for {ticker}: "
                f"need {shares}, have {self.positions.get(ticker, 0)}"
            )
            return False
        
        # 수익 계산 (수수료 + 슬리피지 차감)
        gross_revenue = shares * price
        commission = gross_revenue * self.COMMISSION_RATE
        slippage = gross_revenue * self.SLIPPAGE_RATE
        net_revenue = gross_revenue - commission - slippage
        
        # 거래 실행
        self.cash += net_revenue
        self.positions[ticker] -= shares
        
        if self.positions[ticker] == 0:
            del self.positions[ticker]
        
        # 기록
        trade = Trade(
            date=date,
            action=TradeAction.SELL,
            ticker=ticker,
            shares=shares,
            price=price,
            commission=commission + slippage,
            total_cost=-net_revenue  # 음수 (수익)
        )
        self.trades.append(trade)
        
        logger.info(
            f"SELL {shares} {ticker} @ ₩{price:,.0f} = ₩{net_revenue:,.0f}"
        )
        
        return True
    
    def get_total_value(self, market_prices: Dict[str, float]) -> float:
        """
        총 포트폴리오 가치
        
        Args:
            market_prices: {ticker: price}
            
        Returns:
            총 가치
        """
        stock_value = 0.0
        
        for ticker, shares in self.positions.items():
            if ticker in market_prices:
                stock_value += shares * market_prices[ticker]
            else:
                logger.warning(f"No price data for {ticker}")
        
        return self.cash + stock_value
    
    def get_position_values(
        self,
        market_prices: Dict[str, float]
    ) -> Dict[str, float]:
        """
        개별 포지션 가치
        
        Args:
            market_prices: {ticker: price}
            
        Returns:
            {ticker: value}
        """
        values = {}
        
        for ticker, shares in self.positions.items():
            if ticker in market_prices:
                values[ticker] = shares * market_prices[ticker]
        
        return values
    
    def record_daily_snapshot(
        self,
        date: datetime,
        market_prices: Dict[str, float]
    ):
        """
        일일 스냅샷 기록
        
        Args:
            date: 날짜
            market_prices: 시장 가격
        """
        total_value = self.get_total_value(market_prices)
        position_values = self.get_position_values(market_prices)
        
        # 일별 수익률 계산
        if len(self.history) > 0:
            prev_value = self.history[-1].total_value
            daily_return = (total_value - prev_value) / prev_value
        else:
            daily_return = 0.0
        
        snapshot = PortfolioSnapshot(
            date=date,
            cash=self.cash,
            positions=self.positions.copy(),
            position_values=position_values,
            total_value=total_value,
            daily_return=daily_return
        )
        
        self.history.append(snapshot)
        
        logger.debug(
            f"Snapshot [{date.strftime('%Y-%m-%d')}]: "
            f"₩{total_value:,.0f} ({daily_return:+.2%})"
        )
    
    def get_summary(self) -> Dict:
        """
        포트폴리오 요약
        
        Returns:
            요약 딕셔너리
        """
        if len(self.history) == 0:
            return {}
        
        final_value = self.history[-1].total_value
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'positions': len(self.positions),
            'cash_remaining': self.cash
        }


if __name__ == "__main__":
    # 간단한 테스트
    print("=== Portfolio Test ===\n")
    
    portfolio = Portfolio(initial_capital=10_000_000)
    
    # 매수
    portfolio.buy("AAPL", shares=100, price=175_000, date=datetime.now())
    
    print(f"Cash: ₩{portfolio.cash:,.0f}")
    print(f"Positions: {portfolio.positions}")
    print()
    
    # 포트폴리오 가치
    market_prices = {"AAPL": 180_000}
    total_value = portfolio.get_total_value(market_prices)
    
    print(f"Total Value: ₩{total_value:,.0f}")
    print(f"Profit: ₩{total_value - 10_000_000:,.0f}")
    
    # 매도
    portfolio.sell("AAPL", shares=100, price=180_000, date=datetime.now())
    
    print(f"\nFinal Cash: ₩{portfolio.cash:,.0f}")
    print(f"Trades: {len(portfolio.trades)}")
    
    print("\n✅ Portfolio test completed!")
