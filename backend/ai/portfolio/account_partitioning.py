"""
Account Partitioning - Virtual Wallet System

Phase: Phase 6 - Grand Unified Strategy (Account Partitioning)
Date: 2026-01-05

Purpose:
    하나의 증권 계좌 내에서 가상 지갑(Wallet)을 분리하여
    서로 다른 전략을 독립적으로 관리합니다.

Wallets:
    - CORE (60%): 장기 투자, 우량주, 인덱스 ETF
    - INCOME (30%): 배당주, 채권, 현금흐름 목적
    - SATELLITE (10%): 공격적 투자, 레버리지, 모멘텀 (Leverage Guardian 적용)

Key Features:
    1. 가상 잔액 관리: 각 Wallet별 독립 잔액 추적
    2. 자동 리밸런싱: 목표 비율 벗어나면 경고/자동 조정
    3. 전략별 성과 분리: Wallet별 수익률 추적
    4. 위험 격리: SATELLITE에서 큰 손실이 나도 CORE는 보호

Usage:
    manager = AccountPartitionManager(total_capital=100000)
    manager.allocate_to_wallet("SATELLITE", ticker="TQQQ", value=5000)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WalletType(str, Enum):
    """지갑 유형"""
    CORE = "core"           # 60% - 장기 투자
    INCOME = "income"       # 30% - 배당/현금흐름
    SATELLITE = "satellite" # 10% - 공격적 투자


@dataclass
class WalletConfig:
    """지갑 설정"""
    wallet_type: WalletType
    target_pct: float              # 목표 비율 (0.0 ~ 1.0)
    min_pct: float = 0.0           # 최소 비율
    max_pct: float = 1.0           # 최대 비율
    description: str = ""
    allowed_leverage: bool = False # 레버리지 허용 여부


# 기본 지갑 설정
DEFAULT_WALLET_CONFIGS = {
    WalletType.CORE: WalletConfig(
        wallet_type=WalletType.CORE,
        target_pct=0.60,
        min_pct=0.50,
        max_pct=0.70,
        description="장기 투자: 우량주, 인덱스 ETF, 성장주",
        allowed_leverage=False
    ),
    WalletType.INCOME: WalletConfig(
        wallet_type=WalletType.INCOME,
        target_pct=0.30,
        min_pct=0.20,
        max_pct=0.40,
        description="현금흐름: 배당주, 채권ETF, 리츠",
        allowed_leverage=False
    ),
    WalletType.SATELLITE: WalletConfig(
        wallet_type=WalletType.SATELLITE,
        target_pct=0.10,
        min_pct=0.00,
        max_pct=0.15,
        description="공격적 투자: 레버리지 ETF, 모멘텀, 단기 트레이딩",
        allowed_leverage=True  # Leverage Guardian으로 제한
    ),
}


@dataclass
class WalletPosition:
    """지갑 내 포지션"""
    ticker: str
    quantity: int
    avg_price: float
    current_price: float
    wallet_type: WalletType
    added_at: datetime = field(default_factory=datetime.now)
    
    @property
    def value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_price
    
    @property
    def unrealized_pnl(self) -> float:
        return self.value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis > 0:
            return (self.unrealized_pnl / self.cost_basis) * 100
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "current_price": self.current_price,
            "wallet": self.wallet_type.value,
            "value": self.value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "added_at": self.added_at.isoformat()
        }


@dataclass
class WalletSummary:
    """지갑 요약"""
    wallet_type: WalletType
    current_value: float
    current_pct: float
    target_pct: float
    deviation: float            # 목표 대비 편차
    positions_count: int
    unrealized_pnl: float
    unrealized_pnl_pct: float
    needs_rebalance: bool


class AccountPartitionManager:
    """
    Account Partition Manager - 가상 지갑 관리 시스템
    
    하나의 증권 계좌를 여러 가상 지갑으로 분리하여
    서로 다른 전략을 독립적으로 관리합니다.
    """
    
    def __init__(
        self, 
        total_capital: float = 100000.0,
        wallet_configs: Optional[Dict[WalletType, WalletConfig]] = None
    ):
        """
        Args:
            total_capital: 총 자본금
            wallet_configs: 커스텀 지갑 설정 (None이면 기본값)
        """
        self.total_capital = total_capital
        self.configs = wallet_configs or DEFAULT_WALLET_CONFIGS.copy()
        
        # 각 지갑별 현금
        self.wallet_cash: Dict[WalletType, float] = {
            WalletType.CORE: total_capital * self.configs[WalletType.CORE].target_pct,
            WalletType.INCOME: total_capital * self.configs[WalletType.INCOME].target_pct,
            WalletType.SATELLITE: total_capital * self.configs[WalletType.SATELLITE].target_pct,
        }
        
        # 각 지갑별 포지션
        self.positions: Dict[WalletType, List[WalletPosition]] = {
            WalletType.CORE: [],
            WalletType.INCOME: [],
            WalletType.SATELLITE: [],
        }
        
        logger.info(f"💼 AccountPartitionManager initialized: ${total_capital:,.0f}")
        for wallet, cash in self.wallet_cash.items():
            logger.info(f"   {wallet.value}: ${cash:,.0f} ({self.configs[wallet].target_pct*100:.0f}%)")
    
    def allocate_to_wallet(
        self,
        wallet: str,
        ticker: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        지갑에 포지션 할당
        
        Args:
            wallet: 지갑 유형 (core, income, satellite)
            ticker: 종목 티커
            quantity: 수량
            price: 가격
        
        Returns:
            할당 결과
        """
        wallet_type = WalletType(wallet.lower())
        config = self.configs[wallet_type]
        order_value = quantity * price
        
        # 1. 현금 체크
        available_cash = self.wallet_cash[wallet_type]
        if order_value > available_cash:
            return {
                "success": False,
                "error": f"{wallet_type.value} 지갑 잔액 부족: 필요 ${order_value:,.0f} > 가용 ${available_cash:,.0f}",
                "available_cash": available_cash
            }
        
        # 2. 레버리지 상품 체크
        from backend.ai.safety.leverage_guardian import get_leverage_guardian
        guardian = get_leverage_guardian()
        
        if guardian.is_leveraged(ticker) and not config.allowed_leverage:
            return {
                "success": False,
                "error": f"레버리지 상품 {ticker}은(는) {wallet_type.value} 지갑에 허용되지 않습니다. SATELLITE 지갑을 사용하세요.",
                "suggestion": "satellite"
            }
        
        # 3. SATELLITE 레버리지 한도 체크 (10% of total)
        if wallet_type == WalletType.SATELLITE and guardian.is_leveraged(ticker):
            current_satellite_value = sum(p.value for p in self.positions[WalletType.SATELLITE])
            max_satellite_value = self.total_capital * config.max_pct
            
            if current_satellite_value + order_value > max_satellite_value:
                return {
                    "success": False,
                    "error": f"SATELLITE 지갑 한도 초과: 현재 ${current_satellite_value:,.0f} + ${order_value:,.0f} > 최대 ${max_satellite_value:,.0f}",
                    "max_allowed": max_satellite_value - current_satellite_value
                }
        
        # 4. 포지션 생성/업데이트
        existing = next((p for p in self.positions[wallet_type] if p.ticker == ticker), None)
        
        if existing:
            # 평균 단가 계산
            total_cost = existing.cost_basis + order_value
            total_qty = existing.quantity + quantity
            existing.avg_price = total_cost / total_qty
            existing.quantity = total_qty
            existing.current_price = price
        else:
            position = WalletPosition(
                ticker=ticker,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                wallet_type=wallet_type
            )
            self.positions[wallet_type].append(position)
        
        # 5. 현금 차감
        self.wallet_cash[wallet_type] -= order_value
        
        logger.info(f"✅ {ticker} {quantity}주 @ ${price:.2f} → {wallet_type.value} 지갑 할당")
        
        return {
            "success": True,
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
            "wallet": wallet_type.value,
            "order_value": order_value,
            "remaining_cash": self.wallet_cash[wallet_type]
        }
    
    def sell_from_wallet(
        self,
        wallet: str,
        ticker: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        지갑에서 포지션 매도
        
        Args:
            wallet: 지갑 유형
            ticker: 종목 티커
            quantity: 매도 수량
            price: 매도 가격
        
        Returns:
            매도 결과
        """
        wallet_type = WalletType(wallet.lower())
        
        # 포지션 찾기
        position = next((p for p in self.positions[wallet_type] if p.ticker == ticker), None)
        
        if not position:
            return {
                "success": False,
                "error": f"{wallet_type.value} 지갑에 {ticker} 포지션이 없습니다."
            }
        
        if quantity > position.quantity:
            return {
                "success": False,
                "error": f"매도 수량 {quantity}주 > 보유 수량 {position.quantity}주"
            }
        
        # 매도 처리
        sell_value = quantity * price
        realized_pnl = (price - position.avg_price) * quantity
        
        position.quantity -= quantity
        position.current_price = price
        
        # 전량 매도 시 포지션 제거
        if position.quantity == 0:
            self.positions[wallet_type].remove(position)
        
        # 현금 추가
        self.wallet_cash[wallet_type] += sell_value
        
        logger.info(f"💰 {ticker} {quantity}주 @ ${price:.2f} 매도 → 실현손익 ${realized_pnl:,.2f}")
        
        return {
            "success": True,
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
            "wallet": wallet_type.value,
            "sell_value": sell_value,
            "realized_pnl": realized_pnl,
            "remaining_cash": self.wallet_cash[wallet_type]
        }
    
    def get_wallet_summary(self, wallet: str) -> WalletSummary:
        """
        지갑 요약 조회
        
        Args:
            wallet: 지갑 유형
        
        Returns:
            WalletSummary: 지갑 요약 정보
        """
        wallet_type = WalletType(wallet.lower())
        config = self.configs[wallet_type]
        
        # 포지션 가치 계산
        positions = self.positions[wallet_type]
        positions_value = sum(p.value for p in positions)
        cash = self.wallet_cash[wallet_type]
        total_value = positions_value + cash
        
        # 전체 대비 비율
        total_account_value = self.get_total_value()
        current_pct = total_value / total_account_value if total_account_value > 0 else 0
        
        # 편차
        deviation = current_pct - config.target_pct
        needs_rebalance = abs(deviation) > 0.05  # 5% 이상 편차
        
        # 미실현 손익
        unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        cost_basis = sum(p.cost_basis for p in positions)
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        return WalletSummary(
            wallet_type=wallet_type,
            current_value=total_value,
            current_pct=current_pct,
            target_pct=config.target_pct,
            deviation=deviation,
            positions_count=len(positions),
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            needs_rebalance=needs_rebalance
        )
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """
        전체 지갑 요약 조회
        
        Returns:
            모든 지갑의 요약 정보
        """
        total_value = self.get_total_value()
        
        summaries = {}
        for wallet_type in WalletType:
            summary = self.get_wallet_summary(wallet_type.value)
            summaries[wallet_type.value] = {
                "value": summary.current_value,
                "pct": summary.current_pct,
                "target_pct": summary.target_pct,
                "deviation": summary.deviation,
                "positions_count": summary.positions_count,
                "unrealized_pnl": summary.unrealized_pnl,
                "unrealized_pnl_pct": summary.unrealized_pnl_pct,
                "needs_rebalance": summary.needs_rebalance
            }
        
        return {
            "total_value": total_value,
            "wallets": summaries,
            "rebalance_needed": any(
                summaries[w]["needs_rebalance"] for w in summaries
            )
        }
    
    def get_total_value(self) -> float:
        """전체 계좌 가치 계산"""
        total = sum(self.wallet_cash.values())
        for positions in self.positions.values():
            total += sum(p.value for p in positions)
        return total
    
    def get_rebalance_recommendations(self) -> List[Dict[str, Any]]:
        """
        리밸런싱 추천 생성
        
        Returns:
            리밸런싱이 필요한 지갑 및 권장 조정액
        """
        recommendations = []
        total_value = self.get_total_value()
        
        for wallet_type in WalletType:
            summary = self.get_wallet_summary(wallet_type.value)
            config = self.configs[wallet_type]
            
            if summary.needs_rebalance:
                target_value = total_value * config.target_pct
                adjustment = target_value - summary.current_value
                
                recommendations.append({
                    "wallet": wallet_type.value,
                    "current_value": summary.current_value,
                    "current_pct": summary.current_pct,
                    "target_value": target_value,
                    "target_pct": config.target_pct,
                    "adjustment": adjustment,
                    "action": "add_funds" if adjustment > 0 else "reduce_funds"
                })
        
        return recommendations
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """전체 포지션 조회"""
        all_positions = []
        for wallet_type in WalletType:
            for pos in self.positions[wallet_type]:
                all_positions.append(pos.to_dict())
        return all_positions


# 사용자별 Partition Manager 캐시
_user_managers: Dict[str, AccountPartitionManager] = {}


def get_partition_manager(user_id: str, total_capital: float = 100000.0) -> AccountPartitionManager:
    """사용자별 AccountPartitionManager 인스턴스 반환"""
    if user_id not in _user_managers:
        _user_managers[user_id] = AccountPartitionManager(total_capital=total_capital)
    return _user_managers[user_id]


# 테스트용
if __name__ == "__main__":
    manager = AccountPartitionManager(total_capital=100000)
    
    print("=== Account Partitioning Test ===\n")
    
    # 초기 상태
    summaries = manager.get_all_summaries()
    print(f"Total Value: ${summaries['total_value']:,.0f}")
    for wallet, data in summaries['wallets'].items():
        print(f"  {wallet}: ${data['value']:,.0f} ({data['pct']*100:.0f}%)")
    
    # CORE에 AAPL 할당
    result = manager.allocate_to_wallet("core", "AAPL", 10, 175.0)
    print(f"\n{result}")
    
    # SATELLITE에 TQQQ 할당
    result = manager.allocate_to_wallet("satellite", "TQQQ", 20, 50.0)
    print(f"\n{result}")
    
    # CORE에 TQQQ 시도 (거부됨)
    result = manager.allocate_to_wallet("core", "TQQQ", 10, 50.0)
    print(f"\nCORE에 TQQQ 할당 시도: {result}")
    
    # 최종 상태
    print("\n=== Final State ===")
    summaries = manager.get_all_summaries()
    for wallet, data in summaries['wallets'].items():
        print(f"  {wallet}: ${data['value']:,.0f} ({data['pct']*100:.1f}%)")
