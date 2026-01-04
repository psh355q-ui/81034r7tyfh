"""
Kill Switch System - Emergency Trading Stop

실거래 중 비정상적인 손실 방지를 위한 자동 정지 시스템

Features:
- Daily loss limits (5%)
- Max drawdown monitoring (-10%)
- API error detection (3회 연속)
- Position concentration limits (30%)
- Price data staleness check (5분)
- Emergency manual override

Author: AI Trading System Team
Date: 2026-01-02
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Kill Switch 트리거 유형"""
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    API_ERROR = "api_error"
    POSITION_CONCENTRATION = "position_concentration"
    STALE_DATA = "stale_data"
    MANUAL = "manual"
    DAILY_TRADE_LIMIT = "daily_trade_limit"


class KillSwitchStatus(Enum):
    """Kill Switch 상태"""
    ACTIVE = "active"          # 정상 동작
    TRIGGERED = "triggered"    # 트리거 발동
    PAUSED = "paused"         # 수동 일시정지
    DISABLED = "disabled"      # 비활성화 (개발 전용)


class KillSwitch:
    """
    Kill Switch - 긴급 거래 정지 시스템
    
    실거래 중 다음 조건 발생 시 자동으로 모든 신규 거래 차단:
    - 일일 손실 5% 초과
    - 총 손실 10% 초과 (Max Drawdown)
    - API 오류 3회 연속
    - 단일 종목 집중도 30% 초과
    - 가격 데이터 5분 이상 지연
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: Kill Switch 설정
                {
                    "max_daily_loss_pct": 5.0,
                    "max_drawdown_pct": 10.0,
                    "api_error_threshold": 3,
                    "max_position_concentration": 0.3,
                    "price_stale_minutes": 5,
                    "enabled": True
                }
        """
        self.config = config or self._default_config()
        self.status = KillSwitchStatus.ACTIVE if self.config['enabled'] else KillSwitchStatus.DISABLED
        self.triggered_at = None
        self.trigger_reason = None
        self.trigger_details = {}
        
        # Monitoring state
        self.consecutive_api_errors = 0
        self.daily_start_capital = None
        self.daily_trades_count = 0
        self.last_price_update = datetime.now()
        
        logger.info(f"Kill Switch initialized: {self.status.value}")
    
    def _default_config(self) -> Dict:
        """기본 Kill Switch 설정"""
        return {
            "enabled": True,
            "max_daily_loss_pct": 5.0,        # 일일 5% 손실
            "max_drawdown_pct": 10.0,         # 총 10% 손실
            "api_error_threshold": 3,         # API 오류 3회
            "max_position_concentration": 0.3, # 단일 종목 30%
            "price_stale_minutes": 5,         # 가격 데이터 5분
            "max_daily_trades": 20,           # 일일 최대 거래 20회
        }
    
    def check_triggers(self, trading_state: Dict) -> Dict[str, Any]:
        """
        모든 Kill Switch 조건 체크
        
        Args:
            trading_state: 현재 거래 상태
                {
                    "current_capital": float,
                    "initial_capital": float,
                    "open_positions": List[Dict],
                    "daily_pnl": float,
                    "daily_trades": int,
                    "last_api_error": Optional[datetime],
                }
        
        Returns:
            {
                "should_trigger": bool,
                "triggers": List[TriggerType],
                "details": Dict
            }
        """
        if self.status == KillSwitchStatus.DISABLED:
            return {"should_trigger": False, "triggers": [], "details": {}}
        
        if self.status == KillSwitchStatus.TRIGGERED:
            return {
                "should_trigger": True,
                "triggers": [self.trigger_reason],
                "details": {"already_triggered": True, "triggered_at": self.triggered_at}
            }
        
        triggers = []
        details = {}
        
        # 1. Daily Loss Check
        daily_loss_pct = self._check_daily_loss(trading_state)
        if daily_loss_pct is not None and daily_loss_pct >= self.config['max_daily_loss_pct']:
            triggers.append(TriggerType.DAILY_LOSS)
            details['daily_loss_pct'] = daily_loss_pct
        
        # 2. Max Drawdown Check
        drawdown_pct = self._check_max_drawdown(trading_state)
        if drawdown_pct is not None and abs(drawdown_pct) >= self.config['max_drawdown_pct']:
            triggers.append(TriggerType.MAX_DRAWDOWN)
            details['drawdown_pct'] = drawdown_pct
        
        # 3. API Error Check
        if self.consecutive_api_errors >= self.config['api_error_threshold']:
            triggers.append(TriggerType.API_ERROR)
            details['consecutive_errors'] = self.consecutive_api_errors
        
        # 4. Position Concentration Check
        concentration = self._check_position_concentration(trading_state)
        if concentration > self.config['max_position_concentration']:
            triggers.append(TriggerType.POSITION_CONCENTRATION)
            details['max_concentration'] = concentration
        
        # 5. Stale Price Data Check
        if self._is_price_data_stale():
            triggers.append(TriggerType.STALE_DATA)
            details['minutes_since_update'] = (datetime.now() - self.last_price_update).total_seconds() / 60
        
        # 6. Daily Trade Limit Check
        if trading_state.get('daily_trades', 0) >= self.config['max_daily_trades']:
            triggers.append(TriggerType.DAILY_TRADE_LIMIT)
            details['daily_trades'] = trading_state['daily_trades']
        
        return {
            "should_trigger": len(triggers) > 0,
            "triggers": triggers,
            "details": details
        }
    
    def _check_daily_loss(self, state: Dict) -> Optional[float]:
        """일일 손실률 체크"""
        daily_pnl = state.get('daily_pnl')
        if daily_pnl is None:
            return None
        
        if self.daily_start_capital is None:
            self.daily_start_capital = state.get('current_capital', 0)
        
        if self.daily_start_capital == 0:
            return None
        
        daily_loss_pct = abs(daily_pnl / self.daily_start_capital * 100)
        return daily_loss_pct if daily_pnl < 0 else 0.0
    
    def _check_max_drawdown(self, state: Dict) -> Optional[float]:
        """최대 낙폭 체크"""
        current = state.get('current_capital')
        initial = state.get('initial_capital')
        
        if current is None or initial is None or initial == 0:
            return None
        
        drawdown_pct = (current / initial - 1) * 100
        return drawdown_pct
    
    def _check_position_concentration(self, state: Dict) -> float:
        """포지션 집중도 체크"""
        positions = state.get('open_positions', [])
        if not positions:
            return 0.0
        
        total_value = state.get('current_capital', 0)
        if total_value == 0:
            return 0.0
        
        # 가장 큰 포지션의 비율
        max_position_value = max([
            pos.get('quantity', 0) * pos.get('current_price', 0)
            for pos in positions
        ], default=0)
        
        return max_position_value / total_value
    
    def _is_price_data_stale(self) -> bool:
        """가격 데이터 신선도 체크"""
        minutes_elapsed = (datetime.now() - self.last_price_update).total_seconds() / 60
        return minutes_elapsed >= self.config['price_stale_minutes']
    
    
    def trigger(self, reason: TriggerType, details: Dict):
        """
        Kill Switch 발동
        
        Args:
            reason: 트리거 사유
            details: 상세 정보
        """
        if self.status == KillSwitchStatus.TRIGGERED:
            logger.warning(f"Kill Switch already triggered at {self.triggered_at}")
            return
        
        self.status = KillSwitchStatus.TRIGGERED
        self.triggered_at = datetime.now()
        self.trigger_reason = reason
        self.trigger_details = details
        
        logger.critical(f"🚨 KILL SWITCH TRIGGERED: {reason.value}")
        logger.critical(f"   Details: {details}")
        logger.critical(f"   Timestamp: {self.triggered_at}")
        
        
        # Send Telegram alert
        try:
            import asyncio
            from backend.notifications.telegram_notifier import create_telegram_notifier
            
            telegram = create_telegram_notifier()
            if telegram:
                # Run async function in sync context
                asyncio.run(telegram.send_kill_switch_alert(
                    reason=reason.value,
                    daily_loss_pct=details.get('daily_loss_pct', 0),
                    threshold_pct=self.config.get('max_daily_loss_pct', 5.0)
                ))
                logger.info("✅ Telegram alert sent")
            else:
                logger.warning("⚠️ Telegram not configured, skipping alert")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alert: {e}")


    
    def reset(self, manual_override: bool = False) -> bool:
        """
        Kill Switch 해제
        
        Args:
            manual_override: 수동 승인 필요
        
        Returns:
            성공 여부
        """
        if self.status != KillSwitchStatus.TRIGGERED:
            logger.warning(f"Cannot reset: Kill Switch not triggered (status={self.status.value})")
            return False
        
        if not manual_override:
            logger.error("Kill Switch reset requires manual_override=True")
            return False
        
        logger.warning(f"🔓 Kill Switch RESET by manual override")
        logger.warning(f"   Previous trigger: {self.trigger_reason.value}")
        logger.warning(f"   Triggered at: {self.triggered_at}")
        
        self.status = KillSwitchStatus.ACTIVE
        self.triggered_at = None
        self.trigger_reason = None
        self.trigger_details = {}
        self.consecutive_api_errors = 0
        
        return True
    
    def record_api_error(self):
        """API 오류 기록"""
        self.consecutive_api_errors += 1
        logger.warning(f"API error recorded: {self.consecutive_api_errors} consecutive")
    
    def record_api_success(self):
        """API 성공 기록 - 오류 카운터 리셋"""
        if self.consecutive_api_errors > 0:
            logger.info(f"API success - resetting error count from {self.consecutive_api_errors}")
            self.consecutive_api_errors = 0
    
    def update_price_timestamp(self):
        """가격 데이터 업데이트 타임스탬프 갱신"""
        self.last_price_update = datetime.now()
    
    def can_trade(self) -> bool:
        """거래 가능 여부 - TRIGGERED 상태가 아니어야 거래 가능"""
        return self.status != KillSwitchStatus.TRIGGERED
    
    def get_status(self) -> Dict:
        """현재 상태 조회"""
        return {
            "status": self.status.value,
            "enabled": self.config['enabled'],
            "can_trade": self.can_trade(),
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "trigger_reason": self.trigger_reason.value if self.trigger_reason else None,
            "trigger_details": self.trigger_details,
            "consecutive_api_errors": self.consecutive_api_errors,
            "last_price_update": self.last_price_update.isoformat(),
            "config": self.config
        }


# Singleton instance
_kill_switch_instance = None

def get_kill_switch() -> KillSwitch:
    """Kill Switch singleton 반환"""
    global _kill_switch_instance
    if _kill_switch_instance is None:
        _kill_switch_instance = KillSwitch()
    return _kill_switch_instance
