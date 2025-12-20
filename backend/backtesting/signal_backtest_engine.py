"""
Phase 10: Signal Backtest Engine
뉴스 기반 거래 시그널의 과거 성과를 검증하는 백테스트 엔진

주요 기능:
1. 과거 뉴스 분석 데이터 로드
2. Point-in-Time 시그널 생성 (Lookahead Bias 방지)
3. 가상 거래 실행 (슬리피지 + 수수료)
4. 성과 지표 계산 (Sharpe, Win Rate, Max Drawdown)
5. 파라미터 최적화

비용: $0 (시뮬레이션)
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class NewsAnalysis:
    """뉴스 분석 결과 (Phase 8에서 생성된 데이터)"""
    id: str
    article_id: str
    crawled_at: datetime
    analyzed_at: datetime
    
    # Sentiment
    sentiment_overall: str  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score: float  # -1.0 to 1.0
    sentiment_confidence: float  # 0.0 to 1.0
    
    # Impact
    urgency: str  # IMMEDIATE, SHORT_TERM, LONG_TERM
    impact_magnitude: float  # 0.0 to 1.0
    
    # Risk
    risk_category: str  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    
    # Content
    key_facts: List[str]
    related_tickers: List[Dict]  # [{ticker_symbol, relevance_score}]


@dataclass
class TradingSignal:
    """거래 시그널"""
    id: str
    timestamp: datetime
    ticker: str
    action: SignalAction
    position_size: float  # 0.0 to 1.0 (portfolio percentage)
    confidence: float  # 0.0 to 1.0
    execution_type: str  # MARKET, LIMIT
    reason: str
    urgency: str
    news_analysis_id: str


@dataclass
class Trade:
    """실행된 거래"""
    id: str
    timestamp: datetime
    ticker: str
    action: str  # BUY, SELL
    quantity: int
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    signal_id: str = ""
    is_open: bool = True


@dataclass
class BacktestResult:
    """백테스트 결과"""
    # 기본 정보
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    
    # 성과 지표
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    
    # 거래 통계
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    
    # 시그널 통계
    total_signals: int
    executed_signals: int
    rejected_signals: int
    
    # 일별 통계
    best_day_pct: float
    worst_day_pct: float
    avg_daily_return_pct: float
    
    # 추가 정보
    parameters: Dict
    daily_values: List[Dict]
    trades: List[Dict]


# =============================================================================
# NEWS SIGNAL GENERATOR (Phase 9 로직 재사용)
# =============================================================================

class NewsSignalGenerator:
    """뉴스 분석을 거래 시그널로 변환"""
    
    def __init__(
        self,
        base_position_size: float = 0.05,  # 5% of portfolio
        max_position_size: float = 0.10,   # 10% max
        min_sentiment_threshold: float = 0.7,
        min_relevance_score: int = 70
    ):
        self.base_position_size = base_position_size
        self.max_position_size = max_position_size
        self.min_sentiment_threshold = min_sentiment_threshold
        self.min_relevance_score = min_relevance_score
    
    def generate_signal(self, analysis: NewsAnalysis) -> Optional[TradingSignal]:
        """뉴스 분석 결과를 거래 시그널로 변환"""
        
        # 1. 액션 결정 (감정 기반)
        action = self._determine_action(analysis)
        if action == SignalAction.HOLD:
            return None
        
        # 2. 티커 추출
        ticker = self._extract_primary_ticker(analysis)
        if not ticker:
            return None
        
        # 3. 포지션 크기 계산
        position_size = self._calculate_position_size(analysis)
        
        # 4. 신뢰도 계산
        confidence = self._calculate_confidence(analysis)
        
        # 5. 실행 타입 결정
        execution_type = "MARKET" if analysis.urgency == "IMMEDIATE" else "LIMIT"
        
        return TradingSignal(
            id=f"sig_{analysis.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=analysis.analyzed_at,
            ticker=ticker,
            action=action,
            position_size=position_size,
            confidence=confidence,
            execution_type=execution_type,
            reason="; ".join(analysis.key_facts[:3]) if analysis.key_facts else "News-based signal",
            urgency=analysis.urgency,
            news_analysis_id=analysis.id
        )
    
    def _determine_action(self, analysis: NewsAnalysis) -> SignalAction:
        """감정 분석 기반 액션 결정"""
        sentiment = analysis.sentiment_overall
        score = abs(analysis.sentiment_score)
        
        # 강한 긍정 → 매수
        if sentiment == "POSITIVE" and score >= self.min_sentiment_threshold:
            return SignalAction.BUY
        
        # 강한 부정 → 매도
        elif sentiment == "NEGATIVE" and score >= self.min_sentiment_threshold:
            return SignalAction.SELL
        
        # 중립 또는 약한 신호 → 보류
        else:
            return SignalAction.HOLD
    
    def _extract_primary_ticker(self, analysis: NewsAnalysis) -> Optional[str]:
        """가장 관련성 높은 티커 추출"""
        if not analysis.related_tickers:
            return None
        
        # 관련성 점수로 정렬
        sorted_tickers = sorted(
            analysis.related_tickers,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        # 최소 관련성 임계값 확인
        if sorted_tickers and sorted_tickers[0].get("relevance_score", 0) >= self.min_relevance_score:
            return sorted_tickers[0].get("ticker_symbol")
        
        return None
    
    def _calculate_position_size(self, analysis: NewsAnalysis) -> float:
        """영향도 및 리스크 기반 포지션 크기 계산"""
        base_size = self.base_position_size
        
        # 영향도로 스케일링
        impact_multiplier = analysis.impact_magnitude
        size = base_size * impact_multiplier
        
        # 리스크 레벨로 조정
        if analysis.risk_category == "HIGH":
            size *= 0.5
        elif analysis.risk_category == "CRITICAL":
            size *= 0.25
        elif analysis.risk_category == "LOW":
            size *= 1.2
        
        # 최대값 제한
        return min(size, self.max_position_size)
    
    def _calculate_confidence(self, analysis: NewsAnalysis) -> float:
        """신뢰도 계산"""
        sentiment_conf = analysis.sentiment_confidence
        impact_conf = analysis.impact_magnitude
        
        # 가중 평균 (감정 70%, 영향도 30%)
        confidence = sentiment_conf * 0.7 + impact_conf * 0.3
        return confidence


# =============================================================================
# SIGNAL VALIDATOR (Phase 9 로직 재사용)
# =============================================================================

class SignalValidator:
    """시그널 유효성 검증"""
    
    def __init__(
        self,
        min_confidence: float = 0.7,
        max_position_size: float = 0.10,
        max_daily_trades: int = 10,
        max_sector_trades: int = 3,
        daily_loss_limit_pct: float = 2.0
    ):
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.max_daily_trades = max_daily_trades
        self.max_sector_trades = max_sector_trades
        self.daily_loss_limit_pct = daily_loss_limit_pct
        
        # 상태 추적
        self.daily_trade_count = 0
        self.sector_trade_count: Dict[str, int] = {}
        self.current_daily_loss_pct = 0.0
        self.kill_switch_active = False
    
    def validate(self, signal: TradingSignal) -> Tuple[bool, str]:
        """시그널 유효성 검증"""
        
        # 1. Kill Switch 체크
        if self.kill_switch_active:
            return False, "Kill switch is active"
        
        # 2. 신뢰도 체크
        if signal.confidence < self.min_confidence:
            return False, f"Confidence too low: {signal.confidence:.2%}"
        
        # 3. 포지션 크기 체크
        if signal.position_size > self.max_position_size:
            return False, f"Position size too large: {signal.position_size:.2%}"
        
        # 4. 일일 거래 횟수 체크
        if self.daily_trade_count >= self.max_daily_trades:
            return False, f"Daily trade limit reached: {self.max_daily_trades}"
        
        # 5. 일일 손실 제한 체크
        if self.current_daily_loss_pct <= -self.daily_loss_limit_pct:
            self.kill_switch_active = True
            return False, f"Daily loss limit exceeded: {self.current_daily_loss_pct:.2%}"
        
        return True, "Signal validated"
    
    def reset_daily_counters(self):
        """일일 카운터 초기화"""
        self.daily_trade_count = 0
        self.sector_trade_count = {}
        self.current_daily_loss_pct = 0.0
    
    def record_trade(self, sector: str = "UNKNOWN"):
        """거래 기록"""
        self.daily_trade_count += 1
        self.sector_trade_count[sector] = self.sector_trade_count.get(sector, 0) + 1
    
    def update_daily_pnl(self, pnl_pct: float):
        """일일 손익 업데이트"""
        self.current_daily_loss_pct += pnl_pct


# =============================================================================
# MAIN BACKTEST ENGINE
# =============================================================================

class SignalBacktestEngine:
    """시그널 백테스트 엔진"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00015,  # 0.015% (KRX standard)
        slippage_bps: float = 1.0,  # 1 basis point
        max_holding_days: int = 5,  # 최대 보유 기간
        stop_loss_pct: float = 2.0,  # 손절 %
        take_profit_pct: float = 5.0,  # 익절 %
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps / 10000  # Convert to decimal
        self.max_holding_days = max_holding_days
        self.stop_loss_pct = stop_loss_pct / 100
        self.take_profit_pct = take_profit_pct / 100
        
        # 포트폴리오 상태
        self.cash = initial_capital
        self.positions: Dict[str, Trade] = {}  # ticker -> open trade
        self.closed_trades: List[Trade] = []
        
        # 성과 추적
        self.daily_values: List[Dict] = []
        self.equity_curve: List[float] = [initial_capital]
        
        # 시그널 통계
        self.total_signals = 0
        self.executed_signals = 0
        self.rejected_signals = 0
        self.rejection_reasons: Dict[str, int] = {}
        
        # 컴포넌트
        self.signal_generator = NewsSignalGenerator()
        self.signal_validator = SignalValidator()
    
    async def run(
        self,
        news_analyses: List[NewsAnalysis],
        price_data: Dict[str, Dict[str, float]],  # {date: {ticker: price}}
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """백테스트 실행"""
        
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        logger.info(f"Initial capital: ${self.initial_capital:,.2f}")
        logger.info(f"Total news analyses: {len(news_analyses)}")
        
        # 날짜별로 시뮬레이션
        current_date = start_date
        last_daily_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 1. 해당 날짜의 가격 데이터 확인
            if date_str not in price_data:
                current_date += timedelta(days=1)
                continue
            
            # 2. 날짜가 변경되면 일일 카운터 초기화
            if current_date.date() != last_daily_date.date():
                self.signal_validator.reset_daily_counters()
                last_daily_date = current_date
            
            # 3. 기존 포지션 업데이트 (손절/익절/기간 만료 체크)
            await self._update_positions(current_date, price_data[date_str])
            
            # 4. 해당 시점까지 수집된 뉴스 분석 가져오기 (Point-in-Time)
            available_analyses = self._get_available_analyses(news_analyses, current_date)
            
            # 5. 각 분석에 대해 시그널 생성 및 검증
            for analysis in available_analyses:
                await self._process_analysis(analysis, current_date, price_data[date_str])
            
            # 6. 일일 포트폴리오 가치 기록
            portfolio_value = self._calculate_portfolio_value(price_data[date_str])
            self.daily_values.append({
                "date": date_str,
                "value": portfolio_value,
                "cash": self.cash,
                "positions": len(self.positions),
                "daily_pnl_pct": (portfolio_value / self.equity_curve[-1] - 1) * 100 if self.equity_curve else 0
            })
            self.equity_curve.append(portfolio_value)
            
            current_date += timedelta(days=1)
        
        # 7. 모든 포지션 청산
        final_prices = price_data.get(end_date.strftime("%Y-%m-%d"), {})
        await self._close_all_positions(end_date, final_prices)
        
        # 8. 결과 계산
        return self._calculate_results(start_date, end_date)
    
    def _get_available_analyses(
        self,
        all_analyses: List[NewsAnalysis],
        current_time: datetime
    ) -> List[NewsAnalysis]:
        """Point-in-Time: 현재 시점까지 수집된 분석만 반환 (Lookahead Bias 방지)"""
        available = [
            analysis for analysis in all_analyses
            if analysis.crawled_at <= current_time
            and analysis.analyzed_at <= current_time
        ]
        return available
    
    async def _process_analysis(
        self,
        analysis: NewsAnalysis,
        current_time: datetime,
        current_prices: Dict[str, float]
    ):
        """뉴스 분석 처리: 시그널 생성 → 검증 → 실행"""
        
        # 1. 시그널 생성
        signal = self.signal_generator.generate_signal(analysis)
        
        if not signal:
            return
        
        self.total_signals += 1
        
        # 2. 시그널 검증
        is_valid, reason = self.signal_validator.validate(signal)
        
        if not is_valid:
            self.rejected_signals += 1
            self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1
            logger.debug(f"Signal rejected: {reason}")
            return
        
        # 3. 가격 확인
        if signal.ticker not in current_prices:
            self.rejected_signals += 1
            reason = f"No price data for {signal.ticker}"
            self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1
            logger.debug(f"Signal rejected: {reason}")
            return
        
        # 4. 거래 실행
        await self._execute_signal(signal, current_time, current_prices)
        self.executed_signals += 1
        self.signal_validator.record_trade()
    
    async def _execute_signal(
        self,
        signal: TradingSignal,
        current_time: datetime,
        current_prices: Dict[str, float]
    ):
        """시그널 실행"""
        
        ticker = signal.ticker
        price = current_prices[ticker]
        
        if signal.action == SignalAction.BUY:
            # 이미 포지션이 있으면 스킵
            if ticker in self.positions:
                logger.debug(f"Already have position in {ticker}")
                return
            
            # 포지션 크기 계산
            position_value = self.cash * signal.position_size
            
            # 슬리피지 적용 (매수 시 높게)
            execution_price = price * (1 + self.slippage_bps)
            
            # 수수료 계산
            commission = position_value * self.commission_rate
            
            # 구매 가능 수량
            quantity = int((position_value - commission) / execution_price)
            
            if quantity <= 0:
                logger.debug(f"Insufficient funds for {ticker}")
                return
            
            # 실제 비용
            actual_cost = quantity * execution_price + commission
            
            if actual_cost > self.cash:
                logger.debug(f"Not enough cash: need ${actual_cost:.2f}, have ${self.cash:.2f}")
                return
            
            # 거래 생성
            trade = Trade(
                id=f"trade_{ticker}_{current_time.strftime('%Y%m%d%H%M%S')}",
                timestamp=current_time,
                ticker=ticker,
                action="BUY",
                quantity=quantity,
                entry_price=execution_price,
                commission=commission,
                slippage=quantity * price * self.slippage_bps,
                signal_id=signal.id
            )
            
            # 포트폴리오 업데이트
            self.cash -= actual_cost
            self.positions[ticker] = trade
            
            logger.info(f"BUY {quantity} {ticker} @ ${execution_price:.2f} (signal confidence: {signal.confidence:.2%})")
        
        elif signal.action == SignalAction.SELL:
            # 포지션이 없으면 스킵 (숏 셀링 미지원)
            if ticker not in self.positions:
                logger.debug(f"No position to sell for {ticker}")
                return
            
            # 포지션 청산
            await self._close_position(ticker, current_time, price, "SELL_SIGNAL")
    
    async def _update_positions(
        self,
        current_time: datetime,
        current_prices: Dict[str, float]
    ):
        """기존 포지션 업데이트 (손절/익절/기간 만료)"""
        
        tickers_to_close = []
        
        for ticker, trade in self.positions.items():
            if ticker not in current_prices:
                continue
            
            current_price = current_prices[ticker]
            pnl_pct = (current_price / trade.entry_price - 1)
            
            # 손절 체크
            if pnl_pct <= -self.stop_loss_pct:
                tickers_to_close.append((ticker, "STOP_LOSS"))
                logger.info(f"Stop loss triggered for {ticker}: {pnl_pct:.2%}")
            
            # 익절 체크
            elif pnl_pct >= self.take_profit_pct:
                tickers_to_close.append((ticker, "TAKE_PROFIT"))
                logger.info(f"Take profit triggered for {ticker}: {pnl_pct:.2%}")
            
            # 보유 기간 체크
            elif (current_time - trade.timestamp).days >= self.max_holding_days:
                tickers_to_close.append((ticker, "MAX_HOLDING"))
                logger.info(f"Max holding period reached for {ticker}")
        
        # 포지션 청산
        for ticker, reason in tickers_to_close:
            await self._close_position(ticker, current_time, current_prices[ticker], reason)
    
    async def _close_position(
        self,
        ticker: str,
        current_time: datetime,
        current_price: float,
        reason: str
    ):
        """포지션 청산"""
        
        if ticker not in self.positions:
            return
        
        trade = self.positions[ticker]
        
        # 슬리피지 적용 (매도 시 낮게)
        execution_price = current_price * (1 - self.slippage_bps)
        
        # 수수료 계산
        sell_value = trade.quantity * execution_price
        commission = sell_value * self.commission_rate
        
        # 순수익 계산
        net_proceeds = sell_value - commission
        total_cost = trade.quantity * trade.entry_price + trade.commission
        pnl = net_proceeds - total_cost
        pnl_pct = (execution_price / trade.entry_price - 1) * 100  # 진입가 대비 청산가 수익률
        
        # 거래 업데이트
        trade.exit_price = execution_price
        trade.exit_timestamp = current_time
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.commission += commission
        trade.slippage += trade.quantity * current_price * self.slippage_bps
        trade.is_open = False
        
        # 포트폴리오 업데이트
        self.cash += net_proceeds
        self.closed_trades.append(trade)
        del self.positions[ticker]
        
        # 일일 손익 업데이트
        self.signal_validator.update_daily_pnl(pnl_pct)
        
        logger.info(f"SELL {trade.quantity} {ticker} @ ${execution_price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:.2%}) | Reason: {reason}")
    
    async def _close_all_positions(
        self,
        current_time: datetime,
        current_prices: Dict[str, float]
    ):
        """모든 포지션 청산"""
        
        tickers = list(self.positions.keys())
        for ticker in tickers:
            if ticker in current_prices:
                await self._close_position(ticker, current_time, current_prices[ticker], "END_OF_BACKTEST")
    
    def _calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """포트폴리오 총 가치 계산"""
        
        total_value = self.cash
        
        for ticker, trade in self.positions.items():
            if ticker in current_prices:
                total_value += trade.quantity * current_prices[ticker]
            else:
                # 가격 없으면 진입가 사용
                total_value += trade.quantity * trade.entry_price
        
        return total_value
    
    def _calculate_results(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """백테스트 결과 계산"""
        
        final_value = self.equity_curve[-1] if self.equity_curve else self.initial_capital
        total_return_pct = (final_value / self.initial_capital - 1) * 100
        
        # 거래 통계
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.closed_trades) if self.closed_trades else 0
        
        avg_win_pct = sum(t.pnl_pct for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss_pct = sum(t.pnl_pct for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit Factor
        total_profits = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_profits / total_losses if total_losses > 0 else float('inf')
        
        # Sharpe Ratio (연율화)
        if len(self.daily_values) > 1:
            daily_returns = [d["daily_pnl_pct"] for d in self.daily_values]
            avg_daily_return = sum(daily_returns) / len(daily_returns)
            std_daily_return = math.sqrt(sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns))
            
            # 연율화 (252 거래일)
            if std_daily_return > 0:
                sharpe_ratio = (avg_daily_return / std_daily_return) * math.sqrt(252)
            else:
                sharpe_ratio = 0.0
        else:
            avg_daily_return = 0.0
            sharpe_ratio = 0.0
        
        # Max Drawdown
        max_drawdown_pct = self._calculate_max_drawdown()
        
        # 일별 통계
        daily_pnls = [d["daily_pnl_pct"] for d in self.daily_values]
        best_day_pct = max(daily_pnls) if daily_pnls else 0
        worst_day_pct = min(daily_pnls) if daily_pnls else 0
        
        return BacktestResult(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            initial_capital=self.initial_capital,
            final_value=final_value,
            
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            
            total_trades=len(self.closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            profit_factor=profit_factor,
            
            total_signals=self.total_signals,
            executed_signals=self.executed_signals,
            rejected_signals=self.rejected_signals,
            
            best_day_pct=best_day_pct,
            worst_day_pct=worst_day_pct,
            avg_daily_return_pct=avg_daily_return,
            
            parameters={
                "initial_capital": self.initial_capital,
                "commission_rate": self.commission_rate,
                "slippage_bps": self.slippage_bps * 10000,
                "max_holding_days": self.max_holding_days,
                "stop_loss_pct": self.stop_loss_pct * 100,
                "take_profit_pct": self.take_profit_pct * 100,
                "min_confidence": self.signal_validator.min_confidence,
                "max_position_size": self.signal_generator.max_position_size,
                "min_sentiment_threshold": self.signal_generator.min_sentiment_threshold,
            },
            daily_values=self.daily_values,
            trades=[asdict(t) for t in self.closed_trades]
        )
    
    def _calculate_max_drawdown(self) -> float:
        """최대 낙폭 계산"""
        
        if len(self.equity_curve) < 2:
            return 0.0
        
        peak = self.equity_curve[0]
        max_drawdown = 0.0
        
        for value in self.equity_curve[1:]:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return -max_drawdown


# =============================================================================
# DEMO / TEST
# =============================================================================

async def run_demo():
    """데모 백테스트 실행"""
    
    print("\n" + "=" * 70)
    print("📊 Phase 10: Signal Backtest Engine - DEMO")
    print("=" * 70)
    
    # 1. 샘플 뉴스 분석 데이터 생성
    sample_analyses = []
    
    # 긍정적 뉴스 (매수 신호)
    sample_analyses.append(NewsAnalysis(
        id="analysis_001",
        article_id="article_001",
        crawled_at=datetime(2024, 1, 2, 9, 0),
        analyzed_at=datetime(2024, 1, 2, 9, 5),
        sentiment_overall="POSITIVE",
        sentiment_score=0.85,
        sentiment_confidence=0.90,
        urgency="IMMEDIATE",
        impact_magnitude=0.8,
        risk_category="LOW",
        key_facts=["Apple reports record iPhone sales", "Revenue beats expectations"],
        related_tickers=[{"ticker_symbol": "AAPL", "relevance_score": 95}]
    ))
    
    # 부정적 뉴스 (매도 신호)
    sample_analyses.append(NewsAnalysis(
        id="analysis_002",
        article_id="article_002",
        crawled_at=datetime(2024, 1, 5, 10, 0),
        analyzed_at=datetime(2024, 1, 5, 10, 10),
        sentiment_overall="NEGATIVE",
        sentiment_score=-0.75,
        sentiment_confidence=0.85,
        urgency="SHORT_TERM",
        impact_magnitude=0.7,
        risk_category="HIGH",
        key_facts=["Tesla recalls vehicles", "Production delays reported"],
        related_tickers=[{"ticker_symbol": "TSLA", "relevance_score": 90}]
    ))
    
    # 중립적 뉴스 (시그널 없음)
    sample_analyses.append(NewsAnalysis(
        id="analysis_003",
        article_id="article_003",
        crawled_at=datetime(2024, 1, 8, 11, 0),
        analyzed_at=datetime(2024, 1, 8, 11, 15),
        sentiment_overall="NEUTRAL",
        sentiment_score=0.1,
        sentiment_confidence=0.60,
        urgency="LONG_TERM",
        impact_magnitude=0.3,
        risk_category="MEDIUM",
        key_facts=["Microsoft announces new partnership"],
        related_tickers=[{"ticker_symbol": "MSFT", "relevance_score": 80}]
    ))
    
    # 강한 긍정 뉴스
    sample_analyses.append(NewsAnalysis(
        id="analysis_004",
        article_id="article_004",
        crawled_at=datetime(2024, 1, 10, 9, 30),
        analyzed_at=datetime(2024, 1, 10, 9, 35),
        sentiment_overall="POSITIVE",
        sentiment_score=0.92,
        sentiment_confidence=0.95,
        urgency="IMMEDIATE",
        impact_magnitude=0.9,
        risk_category="LOW",
        key_facts=["NVIDIA AI chip demand surges", "Data center revenue triples"],
        related_tickers=[{"ticker_symbol": "NVDA", "relevance_score": 98}]
    ))
    
    # 2. 샘플 가격 데이터 생성
    price_data = {}
    
    # 30일 가격 데이터
    base_prices = {
        "AAPL": 180.0,
        "TSLA": 250.0,
        "MSFT": 350.0,
        "NVDA": 500.0
    }
    
    # 시뮬레이션 가격 변동 (약간의 상승 추세 + 노이즈)
    import random
    random.seed(42)
    
    start_date = datetime(2024, 1, 1)
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        price_data[date_str] = {}
        
        for ticker, base_price in base_prices.items():
            # 랜덤 변동 + 약간의 상승 추세
            noise = random.gauss(0, 0.02)  # 2% 표준편차
            trend = 0.001 * day  # 일일 0.1% 상승 추세
            
            # 특별 이벤트 (뉴스 반영)
            if ticker == "AAPL" and day >= 2:
                trend += 0.02  # 긍정 뉴스 후 상승
            if ticker == "NVDA" and day >= 10:
                trend += 0.05  # 강한 긍정 뉴스 후 급등
            
            price = base_price * (1 + trend + noise)
            price_data[date_str][ticker] = round(price, 2)
    
    # 3. 백테스트 실행
    engine = SignalBacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.00015,  # 0.015%
        slippage_bps=1.0,
        max_holding_days=5,
        stop_loss_pct=2.0,
        take_profit_pct=5.0
    )
    
    result = await engine.run(
        news_analyses=sample_analyses,
        price_data=price_data,
        start_date=start_date,
        end_date=start_date + timedelta(days=29)
    )
    
    # 4. 결과 출력
    print("\n📈 BACKTEST RESULTS")
    print("-" * 70)
    print(f"Period: {result.start_date} ~ {result.end_date}")
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Value: ${result.final_value:,.2f}")
    print()
    
    print("🎯 PERFORMANCE METRICS")
    print("-" * 70)
    print(f"Total Return: {result.total_return_pct:.2f}%")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Profit Factor: {result.profit_factor:.2f}")
    print()
    
    print("📊 TRADE STATISTICS")
    print("-" * 70)
    print(f"Total Trades: {result.total_trades}")
    print(f"Winning Trades: {result.winning_trades}")
    print(f"Losing Trades: {result.losing_trades}")
    print(f"Average Win: {result.avg_win_pct:.2f}%")
    print(f"Average Loss: {result.avg_loss_pct:.2f}%")
    print()
    
    print("🔔 SIGNAL STATISTICS")
    print("-" * 70)
    print(f"Total Signals Generated: {result.total_signals}")
    print(f"Executed Signals: {result.executed_signals}")
    print(f"Rejected Signals: {result.rejected_signals}")
    print()
    
    print("📅 DAILY PERFORMANCE")
    print("-" * 70)
    print(f"Best Day: {result.best_day_pct:.2f}%")
    print(f"Worst Day: {result.worst_day_pct:.2f}%")
    print(f"Avg Daily Return: {result.avg_daily_return_pct:.4f}%")
    print()
    
    print("⚙️ PARAMETERS USED")
    print("-" * 70)
    for key, value in result.parameters.items():
        print(f"  {key}: {value}")
    print()
    
    print("💰 INDIVIDUAL TRADES")
    print("-" * 70)
    for trade in result.trades:
        print(f"  {trade['ticker']}: {trade['action']} | "
              f"Entry: ${trade['entry_price']:.2f} | "
              f"Exit: ${trade['exit_price']:.2f} | "
              f"PnL: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")
    
    print("\n" + "=" * 70)
    print("✅ Demo completed!")
    print("=" * 70)
    
    # JSON 결과 저장
    return result


if __name__ == "__main__":
    result = asyncio.run(run_demo())
    
    # 결과를 JSON으로 저장
    with open("backtest_result.json", "w") as f:
        json.dump(asdict(result), f, indent=2, default=str)
    
    print(f"\n📁 Results saved to backtest_result.json")
