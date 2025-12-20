"""
Point-in-Time (PiT) Backtest Engine for News-Based Trading Signals

Features:
- Strict temporal ordering (no lookahead bias)
- News data gated by crawled_at timestamp
- Event-driven simulation
- Performance metrics calculation

This engine ensures that during backtesting, the system only has access
to information that would have been available at that point in time.

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class SignalAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradingSignal:
    """Trading signal generated from news analysis"""
    ticker: str
    action: SignalAction
    position_size: float  # 0.0 ~ 1.0
    confidence: float     # 0.0 ~ 1.0
    execution_type: str   # "MARKET" | "LIMIT"
    reason: str
    urgency: str
    created_at: datetime
    source_article_id: Optional[int] = None


@dataclass
class Trade:
    """Executed trade record"""
    timestamp: datetime
    ticker: str
    action: str  # BUY or SELL
    quantity: float
    price: float
    fees: float = 0.0
    slippage: float = 0.0
    signal_id: Optional[int] = None


@dataclass
class Position:
    """Current portfolio position"""
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float
    unrealized_pnl: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price


@dataclass
class BacktestResult:
    """Complete backtest results"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    losing_trades: int
    avg_profit_per_trade: float
    avg_loss_per_trade: float
    profit_factor: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "losing_trades": self.losing_trades,
            "avg_profit_per_trade": self.avg_profit_per_trade,
            "avg_loss_per_trade": self.avg_loss_per_trade,
            "profit_factor": self.profit_factor,
        }


# ============================================================================
# Point-in-Time News Data Provider
# ============================================================================

class PointInTimeNewsProvider:
    """
    Provides news data strictly gated by timestamp.
    
    CRITICAL: This prevents lookahead bias by ensuring that at any point
    in the simulation, only news that was actually crawled by that time
    is accessible.
    """
    
    def __init__(self, db_session):
        """
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self._cache: Dict[datetime, List[Any]] = {}
        logger.info("PointInTimeNewsProvider initialized")
    
    def get_available_news(
        self,
        as_of_timestamp: datetime,
        lookback_hours: int = 24,
        include_analysis: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get news articles available at a specific point in time.
        
        CRITICAL: Uses crawled_at, NOT published_at!
        The system can only know about news AFTER it was crawled.
        
        Args:
            as_of_timestamp: The simulation time
            lookback_hours: How far back to look
            include_analysis: Include AI analysis if available
            
        Returns:
            List of news articles with their analyses
        """
        from data.news_models import NewsArticle, NewsAnalysis
        
        cutoff_time = as_of_timestamp - timedelta(hours=lookback_hours)
        
        # CRITICAL: Filter by crawled_at <= as_of_timestamp
        # This ensures we only see news that was actually collected by this time
        query = (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.crawled_at <= as_of_timestamp,  # ← KEY LINE
                NewsArticle.crawled_at >= cutoff_time,
            )
            .order_by(NewsArticle.crawled_at.desc())
        )
        
        articles = query.all()
        
        result = []
        for article in articles:
            article_data = {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at,
                "crawled_at": article.crawled_at,
                "content_summary": article.content_summary,
                "keywords": article.keywords or [],
            }
            
            if include_analysis:
                # Also check that analysis was done by this time
                analysis = (
                    self.db.query(NewsAnalysis)
                    .filter(
                        NewsAnalysis.article_id == article.id,
                        NewsAnalysis.analyzed_at <= as_of_timestamp,  # ← KEY LINE
                    )
                    .first()
                )
                
                if analysis:
                    article_data["analysis"] = {
                        "sentiment_overall": analysis.sentiment_overall,
                        "sentiment_score": analysis.sentiment_score,
                        "sentiment_confidence": analysis.sentiment_confidence,
                        "urgency": analysis.urgency,
                        "impact_magnitude": analysis.impact_magnitude,
                        "risk_category": analysis.risk_category,
                        "trading_actionable": analysis.trading_actionable,
                        "affected_sectors": analysis.affected_sectors or [],
                        "key_facts": analysis.key_facts or [],
                        "key_warnings": analysis.key_warnings or [],
                    }
                else:
                    article_data["analysis"] = None
            
            result.append(article_data)
        
        logger.debug(
            f"PiT News Query: as_of={as_of_timestamp.isoformat()}, "
            f"found={len(result)} articles in last {lookback_hours}h"
        )
        
        return result
    
    def get_unprocessed_news_since(
        self,
        last_processed_time: datetime,
        current_time: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get news articles that were crawled between two timestamps.
        Useful for event-driven simulation.
        
        Args:
            last_processed_time: Last simulation time we processed
            current_time: Current simulation time
            
        Returns:
            New articles that became available
        """
        from data.news_models import NewsArticle, NewsAnalysis
        
        query = (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.crawled_at > last_processed_time,
                NewsArticle.crawled_at <= current_time,
            )
            .order_by(NewsArticle.crawled_at.asc())
        )
        
        articles = query.all()
        
        result = []
        for article in articles:
            # Get analysis if it was done by current_time
            analysis = (
                self.db.query(NewsAnalysis)
                .filter(
                    NewsAnalysis.article_id == article.id,
                    NewsAnalysis.analyzed_at <= current_time,
                )
                .first()
            )
            
            article_data = {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "crawled_at": article.crawled_at,
                "analysis": None,
            }
            
            if analysis:
                article_data["analysis"] = {
                    "sentiment_overall": analysis.sentiment_overall,
                    "sentiment_score": analysis.sentiment_score,
                    "impact_magnitude": analysis.impact_magnitude,
                    "risk_category": analysis.risk_category,
                    "trading_actionable": analysis.trading_actionable,
                    "affected_sectors": analysis.affected_sectors or [],
                }
            
            result.append(article_data)
        
        return result


# ============================================================================
# Market Data Provider (Mock for backtesting)
# ============================================================================

class HistoricalMarketDataProvider:
    """
    Provides historical market data for backtesting.
    In production, this would query TimescaleDB or Yahoo Finance cache.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._price_cache: Dict[str, Dict[datetime, float]] = {}
    
    def get_price(self, ticker: str, timestamp: datetime) -> Optional[float]:
        """
        Get the price of a ticker at a specific timestamp.
        
        Args:
            ticker: Stock symbol
            timestamp: Point in time
            
        Returns:
            Price at that time, or None if not available
        """
        # In production: query from TimescaleDB or cache
        # For now: return mock data or fetch from stored historical data
        
        if ticker not in self._price_cache:
            self._load_historical_prices(ticker)
        
        if ticker in self._price_cache:
            # Find closest price at or before timestamp
            prices = self._price_cache[ticker]
            valid_times = [t for t in prices.keys() if t <= timestamp]
            if valid_times:
                closest = max(valid_times)
                return prices[closest]
        
        logger.warning(f"No price data for {ticker} at {timestamp}")
        return None
    
    def _load_historical_prices(self, ticker: str):
        """Load historical prices from database"""
        # Placeholder: In production, load from TimescaleDB
        # For testing, you can inject mock data
        self._price_cache[ticker] = {}
    
    def load_mock_prices(self, ticker: str, prices: Dict[datetime, float]):
        """Load mock prices for testing"""
        self._price_cache[ticker] = prices


# ============================================================================
# Point-in-Time Backtest Engine
# ============================================================================

class PointInTimeBacktestEngine:
    """
    Backtest engine with strict point-in-time data access.
    
    Key Features:
    1. News data gated by crawled_at timestamp (no lookahead bias)
    2. Event-driven simulation
    3. Realistic execution modeling (slippage, fees)
    4. Comprehensive performance metrics
    """
    
    def __init__(
        self,
        db_session,
        initial_capital: float = 100_000.0,
        slippage_bps: float = 1.0,  # 1 basis point
        commission_pct: float = 0.015,  # 0.015%
        max_position_pct: float = 0.10,  # 10% max per position
    ):
        """
        Initialize backtest engine.
        
        Args:
            db_session: Database session for data access
            initial_capital: Starting capital
            slippage_bps: Slippage in basis points
            commission_pct: Commission percentage
            max_position_pct: Maximum position size as % of portfolio
        """
        self.db = db_session
        self.initial_capital = initial_capital
        self.slippage_bps = slippage_bps
        self.commission_pct = commission_pct
        self.max_position_pct = max_position_pct
        
        # Data providers
        self.news_provider = PointInTimeNewsProvider(db_session)
        self.market_data = HistoricalMarketDataProvider(db_session)
        
        # State
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        logger.info(
            f"PointInTimeBacktestEngine initialized: "
            f"capital=${initial_capital:,.2f}, "
            f"slippage={slippage_bps}bps, "
            f"commission={commission_pct}%"
        )
    
    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        signal_generator,
        time_step_hours: int = 1,
    ) -> BacktestResult:
        """
        Run backtest over a date range.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            signal_generator: Object with generate_signals(news_list) method
            time_step_hours: Simulation step size in hours
            
        Returns:
            BacktestResult with all metrics
        """
        logger.info(
            f"Starting backtest: {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        # Reset state
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        current_time = start_date
        last_processed_time = start_date
        
        # Main simulation loop
        while current_time <= end_date:
            # 1. Get new news articles (only those crawled since last step)
            new_news = self.news_provider.get_unprocessed_news_since(
                last_processed_time, current_time
            )
            
            if new_news:
                logger.debug(
                    f"Time: {current_time.isoformat()}, "
                    f"New articles: {len(new_news)}"
                )
            
            # 2. Generate signals from new news
            for news_item in new_news:
                if news_item.get("analysis") and news_item["analysis"].get("trading_actionable"):
                    signals = signal_generator.generate_signals(news_item)
                    
                    for signal in signals:
                        # 3. Validate and execute signal
                        self._process_signal(signal, current_time)
            
            # 4. Update positions with current prices
            self._update_positions(current_time)
            
            # 5. Record equity curve
            total_equity = self._calculate_total_equity()
            self.equity_curve.append({
                "timestamp": current_time.isoformat(),
                "cash": self.cash,
                "positions_value": total_equity - self.cash,
                "total_equity": total_equity,
            })
            
            # Move to next time step
            last_processed_time = current_time
            current_time += timedelta(hours=time_step_hours)
        
        # Calculate final metrics
        result = self._calculate_metrics(start_date, end_date)
        
        logger.info(
            f"Backtest complete: "
            f"Return={result.total_return:.2%}, "
            f"Sharpe={result.sharpe_ratio:.2f}, "
            f"MaxDD={result.max_drawdown:.2%}, "
            f"Trades={result.total_trades}"
        )
        
        return result
    
    def _process_signal(self, signal: TradingSignal, current_time: datetime):
        """Process and potentially execute a trading signal"""
        # Get current price
        price = self.market_data.get_price(signal.ticker, current_time)
        if not price:
            logger.warning(f"No price for {signal.ticker}, skipping signal")
            return
        
        # Calculate position size
        total_equity = self._calculate_total_equity()
        target_value = total_equity * signal.position_size
        target_value = min(target_value, total_equity * self.max_position_pct)
        
        if signal.action == SignalAction.BUY:
            # Check if we have enough cash
            quantity = target_value / price
            cost_with_fees = self._calculate_execution_cost(price, quantity, "BUY")
            
            if cost_with_fees <= self.cash:
                self._execute_buy(signal.ticker, quantity, price, current_time)
            else:
                logger.debug(
                    f"Insufficient cash for BUY {signal.ticker}: "
                    f"need ${cost_with_fees:.2f}, have ${self.cash:.2f}"
                )
        
        elif signal.action == SignalAction.SELL:
            if signal.ticker in self.positions:
                position = self.positions[signal.ticker]
                self._execute_sell(
                    signal.ticker, position.quantity, price, current_time
                )
    
    def _execute_buy(
        self, ticker: str, quantity: float, price: float, timestamp: datetime
    ):
        """Execute a buy order"""
        # Calculate costs
        slippage = price * (self.slippage_bps / 10000)
        exec_price = price + slippage
        total_cost = quantity * exec_price
        fees = total_cost * (self.commission_pct / 100)
        
        # Update cash
        self.cash -= (total_cost + fees)
        
        # Update or create position
        if ticker in self.positions:
            pos = self.positions[ticker]
            new_quantity = pos.quantity + quantity
            new_avg_cost = (
                (pos.quantity * pos.avg_cost + quantity * exec_price) / new_quantity
            )
            pos.quantity = new_quantity
            pos.avg_cost = new_avg_cost
        else:
            self.positions[ticker] = Position(
                ticker=ticker,
                quantity=quantity,
                avg_cost=exec_price,
                current_price=exec_price,
            )
        
        # Record trade
        trade = Trade(
            timestamp=timestamp,
            ticker=ticker,
            action="BUY",
            quantity=quantity,
            price=exec_price,
            fees=fees,
            slippage=slippage * quantity,
        )
        self.trades.append(trade)
        
        logger.info(
            f"BUY {quantity:.4f} {ticker} @ ${exec_price:.2f} "
            f"(fees: ${fees:.2f})"
        )
    
    def _execute_sell(
        self, ticker: str, quantity: float, price: float, timestamp: datetime
    ):
        """Execute a sell order"""
        if ticker not in self.positions:
            logger.warning(f"No position to sell: {ticker}")
            return
        
        position = self.positions[ticker]
        
        # Calculate proceeds
        slippage = price * (self.slippage_bps / 10000)
        exec_price = price - slippage  # Slippage works against us
        proceeds = quantity * exec_price
        fees = proceeds * (self.commission_pct / 100)
        
        # Update cash
        self.cash += (proceeds - fees)
        
        # Remove position
        del self.positions[ticker]
        
        # Record trade
        trade = Trade(
            timestamp=timestamp,
            ticker=ticker,
            action="SELL",
            quantity=quantity,
            price=exec_price,
            fees=fees,
            slippage=slippage * quantity,
        )
        self.trades.append(trade)
        
        # Calculate P&L
        pnl = (exec_price - position.avg_cost) * quantity - fees
        
        logger.info(
            f"SELL {quantity:.4f} {ticker} @ ${exec_price:.2f} "
            f"(fees: ${fees:.2f}, PnL: ${pnl:.2f})"
        )
    
    def _update_positions(self, current_time: datetime):
        """Update all positions with current market prices"""
        for ticker, position in self.positions.items():
            new_price = self.market_data.get_price(ticker, current_time)
            if new_price:
                position.current_price = new_price
                position.unrealized_pnl = (
                    (new_price - position.avg_cost) * position.quantity
                )
    
    def _calculate_execution_cost(
        self, price: float, quantity: float, action: str
    ) -> float:
        """Calculate total cost including slippage and fees"""
        slippage = price * (self.slippage_bps / 10000)
        if action == "BUY":
            exec_price = price + slippage
        else:
            exec_price = price - slippage
        
        total_value = quantity * exec_price
        fees = total_value * (self.commission_pct / 100)
        
        return total_value + fees
    
    def _calculate_total_equity(self) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    def _calculate_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        final_equity = self._calculate_total_equity()
        
        # Basic returns
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Annualized return
        days = (end_date - start_date).days
        if days > 0:
            annual_return = ((1 + total_return) ** (365 / days)) - 1
        else:
            annual_return = 0.0
        
        # Sharpe Ratio (assuming risk-free rate of 2%)
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_eq = self.equity_curve[i-1]["total_equity"]
                curr_eq = self.equity_curve[i]["total_equity"]
                returns.append((curr_eq - prev_eq) / prev_eq)
            
            import statistics
            if returns:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0.001
                risk_free_hourly = 0.02 / (365 * 24)  # 2% annual to hourly
                sharpe_ratio = (avg_return - risk_free_hourly) / std_return * (24 * 365) ** 0.5
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Max Drawdown
        max_equity = self.initial_capital
        max_drawdown = 0.0
        for point in self.equity_curve:
            eq = point["total_equity"]
            max_equity = max(max_equity, eq)
            drawdown = (max_equity - eq) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
        
        # Trade statistics
        profits = []
        losses = []
        for i in range(0, len(self.trades), 2):  # Pair BUY/SELL
            if i + 1 < len(self.trades):
                buy_trade = self.trades[i]
                sell_trade = self.trades[i + 1]
                if buy_trade.action == "BUY" and sell_trade.action == "SELL":
                    pnl = (
                        sell_trade.price - buy_trade.price
                    ) * buy_trade.quantity - buy_trade.fees - sell_trade.fees
                    if pnl > 0:
                        profits.append(pnl)
                    else:
                        losses.append(abs(pnl))
        
        total_trades = len(profits) + len(losses)
        profitable_trades = len(profits)
        losing_trades = len(losses)
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        profit_factor = sum(profits) / sum(losses) if losses and sum(losses) > 0 else 0.0
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_equity,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            losing_trades=losing_trades,
            avg_profit_per_trade=avg_profit,
            avg_loss_per_trade=avg_loss,
            profit_factor=profit_factor,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )


# ============================================================================
# Example Usage
# ============================================================================

"""
Example of how to use the Point-in-Time Backtest Engine:

from pit_backtest_engine import PointInTimeBacktestEngine, TradingSignal, SignalAction
from datetime import datetime, timedelta
from data.news_models import get_db

# Create a simple signal generator
class SimpleNewsSignalGenerator:
    def generate_signals(self, news_item):
        signals = []
        analysis = news_item.get("analysis")
        
        if not analysis:
            return signals
        
        # Simple logic: negative sentiment = SELL, positive = BUY
        sentiment = analysis.get("sentiment_overall", "NEUTRAL")
        impact = analysis.get("impact_magnitude", 0.0)
        
        # Only generate signals for high impact news
        if impact < 0.7:
            return signals
        
        # Extract ticker (in production, this would be more sophisticated)
        ticker = "AAPL"  # Placeholder
        
        if sentiment == "NEGATIVE" and impact > 0.8:
            signals.append(TradingSignal(
                ticker=ticker,
                action=SignalAction.SELL,
                position_size=0.05,  # 5% of portfolio
                confidence=analysis.get("sentiment_confidence", 0.5),
                execution_type="MARKET",
                reason=f"High impact negative news: {news_item['title'][:50]}",
                urgency=analysis.get("urgency", "MEDIUM"),
                created_at=datetime.fromisoformat(news_item["crawled_at"]),
            ))
        elif sentiment == "POSITIVE" and impact > 0.8:
            signals.append(TradingSignal(
                ticker=ticker,
                action=SignalAction.BUY,
                position_size=0.05,
                confidence=analysis.get("sentiment_confidence", 0.5),
                execution_type="MARKET",
                reason=f"High impact positive news: {news_item['title'][:50]}",
                urgency=analysis.get("urgency", "MEDIUM"),
                created_at=datetime.fromisoformat(news_item["crawled_at"]),
            ))
        
        return signals


# Run backtest
db = next(get_db())
engine = PointInTimeBacktestEngine(db, initial_capital=100000)

# Load mock market data (in production, load from TimescaleDB)
engine.market_data.load_mock_prices("AAPL", {
    datetime(2024, 10, 1, 9, 30): 180.0,
    datetime(2024, 10, 2, 9, 30): 182.0,
    # ... more prices
})

generator = SimpleNewsSignalGenerator()

result = engine.run(
    start_date=datetime(2024, 10, 1),
    end_date=datetime(2024, 10, 31),
    signal_generator=generator,
    time_step_hours=1,
)

print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Win Rate: {result.win_rate:.2%}")
print(f"Total Trades: {result.total_trades}")
"""
