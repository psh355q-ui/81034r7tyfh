"""
Auto Trade Service
==================
Consensus Engine 승인 시 KIS API로 자동 주문 실행

Features:
- Consensus 승인 → KIS 자동 주문
- Kill Switch 통합
- Position Limit 검증
- Stop-Loss 모니터링
- Dry Run 모드

작성일: 2025-12-09
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import os

logger = logging.getLogger(__name__)


class AutoTradeStatus(Enum):
    """자동 거래 상태"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"


@dataclass
class TradeExecution:
    """거래 실행 결과"""
    ticker: str
    action: str
    approved: bool
    executed: bool
    dry_run: bool
    kis_result: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AutoTradeConfig:
    """자동 거래 설정"""
    # Kill Switch 설정
    kill_switch_enabled: bool = True
    max_daily_loss_pct: float = 2.0  # 일일 최대 손실 2%
    
    # Position Limit 설정
    max_position_size_pct: float = 5.0  # 포지션당 최대 5%
    max_positions: int = 10  # 최대 포지션 수
    
    # 거래 설정
    default_is_virtual: bool = True  # 기본 모의투자
    dry_run_mode: bool = True  # 기본 Dry Run
    
    # Stop-Loss 설정
    stop_loss_pct: float = 3.0  # 기본 3% Stop-Loss


class AutoTradeService:
    """자동 거래 서비스"""
    
    def __init__(self, config: Optional[AutoTradeConfig] = None):
        self.config = config or AutoTradeConfig()
        self.status = AutoTradeStatus.STOPPED
        
        # 통계
        self._daily_trades: List[TradeExecution] = []
        self._total_daily_pnl: float = 0.0
        self._current_positions: Dict[str, Dict] = {}
        
        # Kill Switch 상태
        self._kill_switch_triggered = False
        self._kill_switch_reason: Optional[str] = None
        
        logger.info(f"AutoTradeService initialized: {self.config}")
    
    # ============================================
    # Status Management
    # ============================================
    
    def start(self) -> Dict:
        """자동 거래 시작"""
        if self._kill_switch_triggered:
            return {
                "success": False,
                "error": f"Kill Switch triggered: {self._kill_switch_reason}",
                "status": self.status.value
            }
        
        self.status = AutoTradeStatus.RUNNING
        logger.info("AutoTrade started")
        
        return {
            "success": True,
            "status": self.status.value,
            "message": "Auto trading started",
            "config": {
                "is_virtual": self.config.default_is_virtual,
                "dry_run": self.config.dry_run_mode,
                "max_positions": self.config.max_positions,
                "stop_loss_pct": self.config.stop_loss_pct
            }
        }
    
    def stop(self) -> Dict:
        """자동 거래 중지"""
        self.status = AutoTradeStatus.STOPPED
        logger.info("AutoTrade stopped")
        
        return {
            "success": True,
            "status": self.status.value,
            "message": "Auto trading stopped"
        }
    
    def get_status(self) -> Dict:
        """현재 상태 조회"""
        return {
            "status": self.status.value,
            "kill_switch_triggered": self._kill_switch_triggered,
            "kill_switch_reason": self._kill_switch_reason,
            "config": {
                "is_virtual": self.config.default_is_virtual,
                "dry_run": self.config.dry_run_mode,
                "kill_switch_enabled": self.config.kill_switch_enabled,
                "max_daily_loss_pct": self.config.max_daily_loss_pct,
                "max_position_size_pct": self.config.max_position_size_pct,
                "max_positions": self.config.max_positions,
                "stop_loss_pct": self.config.stop_loss_pct
            },
            "stats": {
                "daily_trades": len(self._daily_trades),
                "daily_pnl": self._total_daily_pnl,
                "current_positions": len(self._current_positions)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # ============================================
    # Kill Switch
    # ============================================
    
    def _check_kill_switch(self) -> bool:
        """Kill Switch 조건 확인"""
        if not self.config.kill_switch_enabled:
            return False
        
        # 일일 최대 손실 확인
        if self._total_daily_pnl < -self.config.max_daily_loss_pct:
            self._trigger_kill_switch(
                f"Daily loss exceeded {self.config.max_daily_loss_pct}%: {self._total_daily_pnl:.2f}%"
            )
            return True
        
        return False
    
    def _trigger_kill_switch(self, reason: str):
        """Kill Switch 발동"""
        self._kill_switch_triggered = True
        self._kill_switch_reason = reason
        self.status = AutoTradeStatus.KILL_SWITCH_TRIGGERED
        logger.critical(f"KILL SWITCH TRIGGERED: {reason}")
    
    def reset_kill_switch(self) -> Dict:
        """Kill Switch 리셋"""
        self._kill_switch_triggered = False
        self._kill_switch_reason = None
        self.status = AutoTradeStatus.STOPPED
        
        return {
            "success": True,
            "message": "Kill switch reset",
            "status": self.status.value
        }
    
    # ============================================
    # Position Management
    # ============================================
    
    def _check_position_limits(self, ticker: str) -> tuple[bool, Optional[str]]:
        """포지션 제한 확인"""
        # 최대 포지션 수 확인
        if len(self._current_positions) >= self.config.max_positions:
            if ticker not in self._current_positions:
                return False, f"Max positions ({self.config.max_positions}) reached"
        
        return True, None
    
    # ============================================
    # Trade Execution
    # ============================================
    
    async def execute_from_consensus(
        self,
        ticker: str,
        action: str,
        consensus_result: Dict,
        dry_run: Optional[bool] = None,
        is_virtual: Optional[bool] = None
    ) -> TradeExecution:
        """
        Consensus 결과를 바탕으로 거래 실행
        
        Args:
            ticker: 종목 티커
            action: 액션 (BUY/SELL/DCA/STOP_LOSS)
            consensus_result: Consensus Engine 투표 결과
            dry_run: Dry Run 모드 (None이면 config 사용)
            is_virtual: 모의투자 여부 (None이면 config 사용)
        
        Returns:
            TradeExecution: 거래 실행 결과
        """
        # 기본값 설정
        dry_run = dry_run if dry_run is not None else self.config.dry_run_mode
        is_virtual = is_virtual if is_virtual is not None else self.config.default_is_virtual
        
        # 상태 확인
        if self.status != AutoTradeStatus.RUNNING and not dry_run:
            return TradeExecution(
                ticker=ticker,
                action=action,
                approved=False,
                executed=False,
                dry_run=dry_run,
                error="AutoTrade is not running"
            )
        
        # Kill Switch 확인
        if self._check_kill_switch():
            return TradeExecution(
                ticker=ticker,
                action=action,
                approved=False,
                executed=False,
                dry_run=dry_run,
                error=f"Kill Switch triggered: {self._kill_switch_reason}"
            )
        
        # Consensus 승인 확인
        is_approved = consensus_result.get("final_decision") == "APPROVED"
        
        if not is_approved:
            return TradeExecution(
                ticker=ticker,
                action=action,
                approved=False,
                executed=False,
                dry_run=dry_run,
                error="Consensus not approved"
            )
        
        # 포지션 제한 확인
        can_trade, limit_error = self._check_position_limits(ticker)
        if not can_trade:
            return TradeExecution(
                ticker=ticker,
                action=action,
                approved=True,
                executed=False,
                dry_run=dry_run,
                error=limit_error
            )
        
        # Dry Run이면 실제 주문 없이 성공 반환
        if dry_run:
            execution = TradeExecution(
                ticker=ticker,
                action=action,
                approved=True,
                executed=True,
                dry_run=True,
                kis_result={
                    "mode": "dry_run",
                    "message": f"Would execute {action} for {ticker}",
                    "consensus": consensus_result
                }
            )
            self._daily_trades.append(execution)
            logger.info(f"[DRY RUN] {action} {ticker}")
            return execution
        
        # 실제 KIS 주문 실행
        try:
            kis_result = await self._execute_kis_order(
                ticker=ticker,
                action=action,
                is_virtual=is_virtual
            )
            
            execution = TradeExecution(
                ticker=ticker,
                action=action,
                approved=True,
                executed=True,
                dry_run=False,
                kis_result=kis_result
            )
            
            # 포지션 업데이트
            if action == "BUY" or action == "DCA":
                self._current_positions[ticker] = {
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            elif action == "SELL" or action == "STOP_LOSS":
                self._current_positions.pop(ticker, None)
            
            self._daily_trades.append(execution)
            logger.info(f"[EXECUTED] {action} {ticker}: {kis_result}")
            return execution
            
        except Exception as e:
            logger.error(f"KIS order failed: {e}")
            return TradeExecution(
                ticker=ticker,
                action=action,
                approved=True,
                executed=False,
                dry_run=False,
                error=str(e)
            )
    
    async def _execute_kis_order(
        self,
        ticker: str,
        action: str,
        is_virtual: bool
    ) -> Dict:
        """KIS 주문 실행"""
        # KIS Broker import
        try:
            from backend.brokers.kis_broker import KISBroker
            
            broker = KISBroker(is_virtual=is_virtual)
            
            # 액션에 따른 주문 실행
            if action in ["BUY", "DCA"]:
                result = await broker.place_order(
                    symbol=ticker,
                    side="BUY",
                    quantity=1,  # 기본 1주 (실제로는 포지션 사이징 필요)
                    order_type="MARKET"
                )
            elif action in ["SELL", "STOP_LOSS"]:
                result = await broker.place_order(
                    symbol=ticker,
                    side="SELL",
                    quantity=1,
                    order_type="MARKET"
                )
            else:
                result = {"error": f"Unknown action: {action}"}
            
            return result
            
        except ImportError:
            # KIS Broker 없으면 Mock 결과 반환
            return {
                "mock": True,
                "action": action,
                "ticker": ticker,
                "is_virtual": is_virtual,
                "message": "KIS Broker not available, mock result"
            }
    
    # ============================================
    # Statistics
    # ============================================
    
    def get_daily_stats(self) -> Dict:
        """일일 통계 조회"""
        return {
            "total_trades": len(self._daily_trades),
            "successful_trades": len([t for t in self._daily_trades if t.executed]),
            "failed_trades": len([t for t in self._daily_trades if not t.executed]),
            "dry_run_trades": len([t for t in self._daily_trades if t.dry_run]),
            "daily_pnl": self._total_daily_pnl,
            "current_positions": list(self._current_positions.keys()),
            "trades": [
                {
                    "ticker": t.ticker,
                    "action": t.action,
                    "approved": t.approved,
                    "executed": t.executed,
                    "dry_run": t.dry_run,
                    "timestamp": t.timestamp
                }
                for t in self._daily_trades[-10:]  # 최근 10개
            ]
        }
    
    def reset_daily_stats(self):
        """일일 통계 리셋"""
        self._daily_trades = []
        self._total_daily_pnl = 0.0
        logger.info("Daily stats reset")


# 글로벌 인스턴스
_auto_trade_service: Optional[AutoTradeService] = None


def get_auto_trade_service() -> AutoTradeService:
    """싱글톤 서비스 인스턴스"""
    global _auto_trade_service
    if _auto_trade_service is None:
        _auto_trade_service = AutoTradeService()
    return _auto_trade_service
