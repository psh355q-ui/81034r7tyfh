"""
Shadow Trading MVP - Conditional Virtual Trading

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    조건부 Shadow Trading 시스템
    - 실제 돈 없이 가상으로 트레이딩 실행
    - MVP Agent 검증용 (3개월 최소)
    - 성과 추적 및 SPY 벤치마크 비교
    - 실패 조건 감지 및 경고

Shadow Trading Conditions (Claude's Insight):
    - "Always-on Shadow는 비용 낭비"
    - "조건부 Shadow만 실행"
    - Triggers:
      1. MVP 첫 출시 (3개월 필수)
      2. Agent 가중치 대폭 변경 (>10%)
      3. 새로운 Hard Rule 추가
      4. 시장 환경 급변 (VIX >30)

Success Criteria (3 months):
    1. Risk-Adjusted Alpha > 1.0
    2. Win Rate > 55%
    3. Profit Factor > 1.5
    4. Max Drawdown < -15%
    5. Sharpe Ratio > 1.0

Failure Conditions (System Failure):
    1. Risk-Adjusted Alpha < 0.5 (for 1 month)
    2. Win Rate < 45% (for 1 month)
    3. Max Drawdown > -25%
    4. 3 consecutive weeks of losses
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (DB 연결용)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class ShadowTradingStatus(Enum):
    """Shadow Trading 상태"""
    ACTIVE = "active"          # 실행 중
    PAUSED = "paused"          # 일시정지
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패


@dataclass
class ShadowTrade:
    """Shadow Trade 기록"""
    trade_id: str
    symbol: str
    action: str  # buy/sell
    quantity: int
    entry_price: float
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    stop_loss_price: float = 0.0
    reason: str = ""
    agent_decision: Optional[Dict[str, Any]] = None


class ShadowTradingMVP:
    """MVP Shadow Trading System - Conditional Virtual Trading"""

    def __init__(self, initial_capital: float = 100000.0, session_id: Optional[str] = None):
        """
        Initialize Shadow Trading System

        Args:
            initial_capital: 초기 자본금 (default: $100k)
            session_id: 기존 세션 ID (복원 시 사용)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_cash = initial_capital

        # Shadow Trading 상태
        self.status = ShadowTradingStatus.PAUSED
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.session_id = session_id or f"shadow_{datetime.utcnow().isoformat()}"

        # DB 연결
        self._db_engine = None

        # Trades
        self.open_positions: Dict[str, ShadowTrade] = {}
        self.closed_trades: List[ShadowTrade] = []

        # Performance tracking
        self.daily_returns: List[float] = []
        self.equity_curve: List[Dict[str, Any]] = []

        # Success criteria
        self.SUCCESS_CRITERIA = {
            'min_risk_adjusted_alpha': 1.0,
            'min_win_rate': 0.55,
            'min_profit_factor': 1.5,
            'max_drawdown': -0.15,
            'min_sharpe_ratio': 1.0
        }

        # Failure conditions
        self.FAILURE_CONDITIONS = {
            'max_alpha_threshold': 0.5,       # Alpha < 0.5 for 1 month
            'min_win_rate_threshold': 0.45,   # Win rate < 45% for 1 month
            'max_drawdown_threshold': -0.25,  # Drawdown > -25%
            'consecutive_loss_weeks': 3       # 3주 연속 손실
        }

        # Triggers for Shadow Trading
        self.SHADOW_TRIGGERS = {
            'mvp_first_release': True,        # MVP 첫 출시
            'agent_weight_change': 0.10,      # 가중치 10% 이상 변경
            'new_hard_rule': True,            # 새 Hard Rule 추가
            'market_volatility': 30.0         # VIX > 30
        }

    def start(self, reason: str = "MVP validation") -> Dict[str, Any]:
        """
        Shadow Trading 시작

        Args:
            reason: 시작 이유

        Returns:
            시작 결과
        """
        if self.status == ShadowTradingStatus.ACTIVE:
            return {
                'success': False,
                'message': 'Shadow Trading already active'
            }

        self.status = ShadowTradingStatus.ACTIVE
        self.start_date = datetime.utcnow()
        self.current_capital = self.initial_capital
        self.available_cash = self.initial_capital
        self.open_positions = {}
        self.closed_trades = []
        self.daily_returns = []
        self.equity_curve = []

        # DB에 세션 저장
        save_result = self.save_session_to_db()
        if not save_result['success']:
            print(f"⚠️  Warning: {save_result['message']}")

        return {
            'success': True,
            'message': f'Shadow Trading started: {reason}',
            'start_date': self.start_date.isoformat(),
            'initial_capital': self.initial_capital,
            'session_id': self.session_id
        }

    def execute_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        agent_decision: Optional[Dict[str, Any]] = None,
        stop_loss_pct: float = 0.02
    ) -> Dict[str, Any]:
        """
        Shadow Trade 실행

        Args:
            symbol: 종목 심볼
            action: buy/sell
            quantity: 수량
            price: 가격
            agent_decision: Agent 결정 (optional)
            stop_loss_pct: Stop Loss % (default: 2%)

        Returns:
            실행 결과
        """
        if self.status != ShadowTradingStatus.ACTIVE:
            return {
                'success': False,
                'message': 'Shadow Trading not active'
            }

        trade_id = f"{symbol}_{datetime.utcnow().isoformat()}"
        trade_value = quantity * price

        # BUY
        if action == 'buy':
            if trade_value > self.available_cash:
                return {
                    'success': False,
                    'message': f'Insufficient cash: ${trade_value:,.0f} required, ${self.available_cash:,.0f} available'
                }

            # Create shadow trade
            stop_loss_price = price * (1 - stop_loss_pct)
            trade = ShadowTrade(
                trade_id=trade_id,
                symbol=symbol,
                action='buy',
                quantity=quantity,
                entry_price=price,
                entry_date=datetime.utcnow(),
                stop_loss_price=stop_loss_price,
                reason='Shadow buy',
                agent_decision=agent_decision
            )

            self.open_positions[symbol] = trade
            self.available_cash -= trade_value

            # DB에 Trade 저장
            self.save_trade_to_db(trade)
            # 세션 상태 업데이트
            self.save_session_to_db()

            return {
                'success': True,
                'message': f'Shadow BUY: {symbol} x{quantity} @ ${price:.2f}',
                'trade_id': trade_id,
                'trade_value': trade_value,
                'available_cash': self.available_cash
            }

        # SELL
        elif action == 'sell':
            if symbol not in self.open_positions:
                return {
                    'success': False,
                    'message': f'No open position for {symbol}'
                }

            # Close position
            open_trade = self.open_positions[symbol]
            exit_value = quantity * price

            pnl = exit_value - (open_trade.entry_price * open_trade.quantity)
            pnl_pct = pnl / (open_trade.entry_price * open_trade.quantity)

            # Update trade
            open_trade.exit_price = price
            open_trade.exit_date = datetime.utcnow()
            open_trade.pnl = pnl
            open_trade.pnl_pct = pnl_pct

            # Move to closed trades
            self.closed_trades.append(open_trade)
            del self.open_positions[symbol]

            # Update cash
            self.available_cash += exit_value

            # DB에 Trade 업데이트 (exit 정보 저장)
            self.save_trade_to_db(open_trade)
            # 세션 상태 업데이트
            self.save_session_to_db()

            return {
                'success': True,
                'message': f'Shadow SELL: {symbol} x{quantity} @ ${price:.2f}',
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'available_cash': self.available_cash
            }

        return {
            'success': False,
            'message': f'Invalid action: {action}'
        }

    def update_positions(self, market_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        포지션 업데이트 (시장 가격 반영)

        Args:
            market_prices: {symbol: current_price}

        Returns:
            업데이트 결과
        """
        if self.status != ShadowTradingStatus.ACTIVE:
            return {
                'success': False,
                'message': 'Shadow Trading not active'
            }

        stop_loss_triggered = []

        # Update open positions
        for symbol, trade in list(self.open_positions.items()):
            if symbol in market_prices:
                current_price = market_prices[symbol]

                # Check stop loss
                if current_price <= trade.stop_loss_price:
                    # Trigger stop loss
                    result = self.execute_trade(
                        symbol=symbol,
                        action='sell',
                        quantity=trade.quantity,
                        price=current_price,
                        agent_decision={'reason': 'stop_loss_triggered'}
                    )
                    stop_loss_triggered.append({
                        'symbol': symbol,
                        'price': current_price,
                        'result': result
                    })

        # Calculate current equity
        position_value = sum(
            trade.quantity * market_prices.get(trade.symbol, trade.entry_price)
            for trade in self.open_positions.values()
        )
        total_equity = self.available_cash + position_value

        # Record equity curve
        self.equity_curve.append({
            'date': datetime.utcnow().isoformat(),
            'equity': total_equity,
            'cash': self.available_cash,
            'positions_value': position_value
        })

        return {
            'success': True,
            'total_equity': total_equity,
            'available_cash': self.available_cash,
            'positions_value': position_value,
            'stop_loss_triggered': stop_loss_triggered
        }

    def get_performance(self) -> Dict[str, Any]:
        """
        성과 측정

        Returns:
            Performance metrics
        """
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'risk_adjusted_alpha': 0.0,
                'current_capital': self.current_capital,
                'days_running': (datetime.utcnow() - self.start_date).days if self.start_date else 0
            }

        # Calculate metrics
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl and t.pnl <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0

        total_wins = sum(t.pnl for t in winning_trades if t.pnl)
        total_losses = abs(sum(t.pnl for t in losing_trades if t.pnl))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        total_pnl = sum(t.pnl for t in self.closed_trades if t.pnl)
        total_pnl_pct = (total_pnl / self.initial_capital) * 100

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio()

        # Calculate risk-adjusted alpha (simplified vs SPY benchmark)
        # Assuming SPY return ~10% annually
        spy_benchmark_return = 0.10 / 12  # Monthly
        excess_return = (total_pnl_pct / 100) - spy_benchmark_return
        risk_adjusted_alpha = excess_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'risk_adjusted_alpha': risk_adjusted_alpha,
            'current_capital': self.current_capital,
            'days_running': (datetime.utcnow() - self.start_date).days if self.start_date else 0
        }

    def check_success_criteria(self) -> Dict[str, Any]:
        """
        성공 기준 체크

        Returns:
            {
                'passed': bool,
                'criteria_met': Dict[str, bool],
                'recommendation': str
            }
        """
        perf = self.get_performance()

        criteria_met = {
            'risk_adjusted_alpha': perf['risk_adjusted_alpha'] >= self.SUCCESS_CRITERIA['min_risk_adjusted_alpha'],
            'win_rate': perf['win_rate'] >= self.SUCCESS_CRITERIA['min_win_rate'],
            'profit_factor': perf['profit_factor'] >= self.SUCCESS_CRITERIA['min_profit_factor'],
            'max_drawdown': perf['max_drawdown'] >= self.SUCCESS_CRITERIA['max_drawdown'],
            'sharpe_ratio': perf['sharpe_ratio'] >= self.SUCCESS_CRITERIA['min_sharpe_ratio']
        }

        passed = all(criteria_met.values())

        if passed:
            recommendation = "✅ READY FOR $100 REAL MONEY TEST"
        else:
            failed_criteria = [k for k, v in criteria_met.items() if not v]
            recommendation = f"❌ NOT READY - Failed: {', '.join(failed_criteria)}"

        return {
            'passed': passed,
            'criteria_met': criteria_met,
            'recommendation': recommendation,
            'performance': perf
        }

    def check_failure_conditions(self) -> Dict[str, Any]:
        """
        실패 조건 체크

        Returns:
            {
                'system_failure': bool,
                'failures': List[str],
                'action_required': str
            }
        """
        perf = self.get_performance()
        failures = []

        # Failure 1: Alpha < 0.5 for 1 month
        if perf['days_running'] >= 30 and perf['risk_adjusted_alpha'] < self.FAILURE_CONDITIONS['max_alpha_threshold']:
            failures.append(f"Alpha {perf['risk_adjusted_alpha']:.2f} < 0.5 for 1 month")

        # Failure 2: Win Rate < 45% for 1 month
        if perf['days_running'] >= 30 and perf['win_rate'] < self.FAILURE_CONDITIONS['min_win_rate_threshold']:
            failures.append(f"Win rate {perf['win_rate']*100:.1f}% < 45% for 1 month")

        # Failure 3: Max Drawdown > -25%
        if perf['max_drawdown'] < self.FAILURE_CONDITIONS['max_drawdown_threshold']:
            failures.append(f"Max drawdown {perf['max_drawdown']*100:.1f}% > -25%")

        # Failure 4: 3 consecutive loss weeks
        consecutive_losses = self._count_consecutive_loss_weeks()
        if consecutive_losses >= self.FAILURE_CONDITIONS['consecutive_loss_weeks']:
            failures.append(f"{consecutive_losses} consecutive loss weeks")

        system_failure = len(failures) > 0

        if system_failure:
            action_required = "🚨 SYSTEM FAILURE - STOP AND REDESIGN"
        else:
            action_required = "Continue monitoring"

        return {
            'system_failure': system_failure,
            'failures': failures,
            'action_required': action_required
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0

        equity_values = [e['equity'] for e in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0

        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = (equity - peak) / peak
            if dd < max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio (simplified)"""
        if not self.daily_returns or len(self.daily_returns) < 2:
            return 0.0

        import statistics
        mean_return = statistics.mean(self.daily_returns)
        std_return = statistics.stdev(self.daily_returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming 252 trading days)
        sharpe = (mean_return / std_return) * (252 ** 0.5)
        return sharpe

    def _count_consecutive_loss_weeks(self) -> int:
        """Count consecutive loss weeks"""
        # Simplified - would need weekly PnL tracking in production
        return 0  # Placeholder

    def get_shadow_info(self) -> Dict[str, Any]:
        """Get shadow trading information"""
        return {
            'status': self.status.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'days_running': (datetime.utcnow() - self.start_date).days if self.start_date else 0,
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'available_cash': self.available_cash,
            'open_positions_count': len(self.open_positions),
            'closed_trades_count': len(self.closed_trades),
            'success_criteria': self.SUCCESS_CRITERIA,
            'failure_conditions': self.FAILURE_CONDITIONS,
            'shadow_triggers': self.SHADOW_TRIGGERS
        }

    # ==================== DB Persistence Methods ====================

    def _get_db_engine(self):
        """DB 엔진 가져오기 (싱글톤 패턴)"""
        if self._db_engine is None:
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_trading')
            # Convert asyncpg to psycopg2 for sync operations
            if 'postgresql+asyncpg://' in db_url:
                db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
            self._db_engine = create_engine(db_url)
        return self._db_engine

    def save_session_to_db(self) -> Dict[str, Any]:
        """
        현재 Shadow Trading 세션을 DB에 저장

        Returns:
            {'success': bool, 'message': str}
        """
        try:
            engine = self._get_db_engine()
            with engine.connect() as conn:
                # Check if session exists
                result = conn.execute(text("""
                    SELECT id FROM shadow_trading_sessions WHERE session_id = :session_id
                """), {'session_id': self.session_id})

                existing = result.fetchone()

                if existing:
                    # Update existing session
                    conn.execute(text("""
                        UPDATE shadow_trading_sessions
                        SET status = :status,
                            end_date = :end_date,
                            current_capital = :current_capital,
                            available_cash = :available_cash,
                            updated_at = NOW()
                        WHERE session_id = :session_id
                    """), {
                        'session_id': self.session_id,
                        'status': self.status.value,
                        'end_date': self.end_date,
                        'current_capital': self.current_capital,
                        'available_cash': self.available_cash
                    })
                else:
                    # Insert new session
                    conn.execute(text("""
                        INSERT INTO shadow_trading_sessions
                        (session_id, status, start_date, end_date, initial_capital,
                         current_capital, available_cash, reason, created_at, updated_at)
                        VALUES (:session_id, :status, :start_date, :end_date, :initial_capital,
                                :current_capital, :available_cash, :reason, NOW(), NOW())
                    """), {
                        'session_id': self.session_id,
                        'status': self.status.value,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'initial_capital': self.initial_capital,
                        'current_capital': self.current_capital,
                        'available_cash': self.available_cash,
                        'reason': f'Shadow Trading Session - {self.status.value}'
                    })

                conn.commit()

            return {
                'success': True,
                'message': f'Session {self.session_id} saved to DB'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to save session: {str(e)}'
            }

    def save_trade_to_db(self, trade: ShadowTrade) -> Dict[str, Any]:
        """
        개별 Shadow Trade를 DB에 저장

        Args:
            trade: ShadowTrade 객체

        Returns:
            {'success': bool, 'message': str}
        """
        try:
            engine = self._get_db_engine()
            with engine.connect() as conn:
                # Check if trade exists
                result = conn.execute(text("""
                    SELECT id FROM shadow_trades WHERE trade_id = :trade_id
                """), {'trade_id': trade.trade_id})

                existing = result.fetchone()

                if existing:
                    # Update existing trade
                    conn.execute(text("""
                        UPDATE shadow_trades
                        SET exit_price = :exit_price,
                            exit_date = :exit_date,
                            pnl = :pnl,
                            pnl_pct = :pnl_pct
                        WHERE trade_id = :trade_id
                    """), {
                        'trade_id': trade.trade_id,
                        'exit_price': trade.exit_price,
                        'exit_date': trade.exit_date,
                        'pnl': trade.pnl,
                        'pnl_pct': trade.pnl_pct
                    })
                else:
                    # Insert new trade
                    conn.execute(text("""
                        INSERT INTO shadow_trades
                        (session_id, trade_id, symbol, action, quantity, entry_price, entry_date,
                         exit_price, exit_date, pnl, pnl_pct, stop_loss_price, reason,
                         agent_decision, created_at)
                        VALUES (:session_id, :trade_id, :symbol, :action, :quantity, :entry_price,
                                :entry_date, :exit_price, :exit_date, :pnl, :pnl_pct,
                                :stop_loss_price, :reason, :agent_decision, NOW())
                    """), {
                        'session_id': self.session_id,
                        'trade_id': trade.trade_id,
                        'symbol': trade.symbol,
                        'action': trade.action,
                        'quantity': trade.quantity,
                        'entry_price': trade.entry_price,
                        'entry_date': trade.entry_date,
                        'exit_price': trade.exit_price,
                        'exit_date': trade.exit_date,
                        'pnl': trade.pnl,
                        'pnl_pct': trade.pnl_pct,
                        'stop_loss_price': trade.stop_loss_price,
                        'reason': trade.reason,
                        'agent_decision': str(trade.agent_decision) if trade.agent_decision else None
                    })

                conn.commit()

            return {
                'success': True,
                'message': f'Trade {trade.trade_id} saved to DB'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to save trade: {str(e)}'
            }

    @classmethod
    def load_active_session_from_db(cls) -> Optional['ShadowTradingMVP']:
        """
        DB에서 활성 Shadow Trading 세션을 로드

        Returns:
            ShadowTradingMVP 인스턴스 또는 None
        """
        try:
            # DB 연결
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_trading')
            if 'postgresql+asyncpg://' in db_url:
                db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
            engine = create_engine(db_url)

            with engine.connect() as conn:
                # 활성 세션 조회
                result = conn.execute(text("""
                    SELECT session_id, status, start_date, end_date, initial_capital,
                           current_capital, available_cash, reason
                    FROM shadow_trading_sessions
                    WHERE status = 'active'
                    ORDER BY start_date DESC
                    LIMIT 1
                """))

                session = result.fetchone()

                if not session:
                    return None

                # ShadowTradingMVP 인스턴스 생성
                instance = cls(
                    initial_capital=session[4],  # initial_capital
                    session_id=session[0]  # session_id
                )

                # 세션 데이터 복원
                instance.status = ShadowTradingStatus(session[1])  # status
                instance.start_date = session[2]  # start_date
                instance.end_date = session[3]  # end_date
                instance.current_capital = session[5]  # current_capital
                instance.available_cash = session[6]  # available_cash

                # Trades 로드
                trades_result = conn.execute(text("""
                    SELECT trade_id, symbol, action, quantity, entry_price, entry_date,
                           exit_price, exit_date, pnl, pnl_pct, stop_loss_price, reason
                    FROM shadow_trades
                    WHERE session_id = :session_id
                    ORDER BY entry_date
                """), {'session_id': instance.session_id})

                for trade_row in trades_result:
                    trade = ShadowTrade(
                        trade_id=trade_row[0],
                        symbol=trade_row[1],
                        action=trade_row[2],
                        quantity=trade_row[3],
                        entry_price=trade_row[4],
                        entry_date=trade_row[5],
                        exit_price=trade_row[6],
                        exit_date=trade_row[7],
                        pnl=trade_row[8],
                        pnl_pct=trade_row[9],
                        stop_loss_price=trade_row[10],
                        reason=trade_row[11]
                    )

                    # Open vs Closed
                    if trade.exit_date is None:
                        instance.open_positions[trade.symbol] = trade
                    else:
                        instance.closed_trades.append(trade)

                print(f"✅ Loaded Shadow Trading session: {instance.session_id}")
                print(f"   Status: {instance.status.value}")
                print(f"   Capital: ${instance.current_capital:,.0f}")
                print(f"   Open Positions: {len(instance.open_positions)}")
                print(f"   Closed Trades: {len(instance.closed_trades)}")

                return instance

        except Exception as e:
            print(f"❌ Failed to load session from DB: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Initialize shadow trading
    shadow = ShadowTradingMVP(initial_capital=100000)

    # Start shadow trading
    result = shadow.start(reason="MVP validation - 3 months")
    print(f"Start: {result['message']}")

    # Execute shadow buy
    trade1 = shadow.execute_trade(
        symbol='AAPL',
        action='buy',
        quantity=100,
        price=150.0,
        stop_loss_pct=0.02
    )
    print(f"\n{trade1['message']}")
    print(f"Available Cash: ${trade1['available_cash']:,.0f}")

    # Update positions (simulate price movement)
    update = shadow.update_positions({'AAPL': 155.0})
    print(f"\nEquity: ${update['total_equity']:,.0f}")

    # Execute shadow sell
    trade2 = shadow.execute_trade(
        symbol='AAPL',
        action='sell',
        quantity=100,
        price=155.0
    )
    print(f"\n{trade2['message']}")
    print(f"PnL: ${trade2['pnl']:,.0f} ({trade2['pnl_pct']:.2f}%)")

    # Check performance
    perf = shadow.get_performance()
    print(f"\n=== Performance ===")
    print(f"Win Rate: {perf['win_rate']*100:.1f}%")
    print(f"Profit Factor: {perf['profit_factor']:.2f}")
    print(f"Total PnL: ${perf['total_pnl']:,.0f} ({perf['total_pnl_pct']:.2f}%)")

    # Check success criteria
    check = shadow.check_success_criteria()
    print(f"\n{check['recommendation']}")
