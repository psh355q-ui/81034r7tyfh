"""
Multi-Asset Models

Phase 30: Multi-Asset Support
Date: 2025-12-30

Models for supporting multiple asset classes:
- STOCK: Equities
- BOND: Fixed income securities
- CRYPTO: Cryptocurrencies
- COMMODITY: Precious metals, energy, agriculture
- ETF: Exchange-traded funds
- REIT: Real estate investment trusts
"""

from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from backend.database.models import Base


class Asset(Base):
    """Multi-asset support - 모든 자산 클래스 통합 모델"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, unique=True)  # AAPL, BTC-USD, GLD, TLT
    asset_class = Column(String(20), nullable=False)  # STOCK, BOND, CRYPTO, COMMODITY, ETF, REIT
    name = Column(String(200), nullable=False)  # Bitcoin, Apple Inc., Gold
    exchange = Column(String(50), nullable=True)  # NYSE, NASDAQ, BINANCE, COMEX
    currency = Column(String(10), nullable=False, default="USD")  # USD, KRW, EUR

    # Asset-specific fields
    sector = Column(String(50), nullable=True)  # For stocks
    bond_type = Column(String(30), nullable=True)  # TREASURY, CORPORATE, MUNICIPAL, JUNK
    maturity_date = Column(Date, nullable=True)  # For bonds
    coupon_rate = Column(Numeric(6, 4), nullable=True)  # For bonds (%)
    crypto_type = Column(String(30), nullable=True)  # LAYER1, LAYER2, DEFI, STABLECOIN, MEME
    commodity_type = Column(String(30), nullable=True)  # PRECIOUS_METAL, ENERGY, AGRICULTURE

    # Risk & correlation
    risk_level = Column(String(20), nullable=False, default="MEDIUM")  # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    correlation_to_sp500 = Column(Numeric(4, 2), nullable=True)  # -1.0 ~ 1.0

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Additional data (renamed from metadata to avoid SQLAlchemy conflict)
    extra_data = Column(JSONB, nullable=True)  # Additional asset-specific data

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_assets_symbol', 'symbol', unique=True),
        Index('idx_assets_class', 'asset_class'),
        Index('idx_assets_risk', 'risk_level'),
        Index('idx_assets_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, symbol='{self.symbol}', class='{self.asset_class}')>"


class MultiAssetPosition(Base):
    """Multi-asset 포트폴리오 포지션"""
    __tablename__ = "multi_asset_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, nullable=False)  # FK to assets.id
    quantity = Column(Numeric(18, 8), nullable=False)  # 수량 (코인은 소수점 8자리)
    average_cost = Column(Numeric(12, 2), nullable=False)  # 평균 단가
    current_price = Column(Numeric(12, 2), nullable=True)  # 현재가
    market_value = Column(Numeric(18, 2), nullable=True)  # 평가액
    unrealized_pnl = Column(Numeric(18, 2), nullable=True)  # 미실현 손익
    unrealized_pnl_percent = Column(Numeric(8, 4), nullable=True)  # 미실현 손익률 (%)
    portfolio_weight = Column(Numeric(6, 4), nullable=True)  # 포트폴리오 비중 (%)
    opened_at = Column(DateTime, nullable=False, default=datetime.now)  # 포지션 오픈 시각
    last_updated = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_multi_positions_asset', 'asset_id'),
        Index('idx_multi_positions_updated', 'last_updated'),
    )

    def __repr__(self):
        return f"<MultiAssetPosition(id={self.id}, asset_id={self.asset_id}, qty={self.quantity})>"


class AssetCorrelation(Base):
    """자산 간 상관관계 매트릭스"""
    __tablename__ = "asset_correlations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset1_id = Column(Integer, nullable=False)  # FK to assets.id
    asset2_id = Column(Integer, nullable=False)  # FK to assets.id
    correlation_30d = Column(Numeric(4, 2), nullable=True)  # 30일 상관계수
    correlation_90d = Column(Numeric(4, 2), nullable=True)  # 90일 상관계수
    correlation_1y = Column(Numeric(4, 2), nullable=True)  # 1년 상관계수
    calculated_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_correlations_assets', 'asset1_id', 'asset2_id', unique=True),
        Index('idx_correlations_calculated', 'calculated_at'),
    )

    def __repr__(self):
        return f"<AssetCorrelation(asset1={self.asset1_id}, asset2={self.asset2_id}, corr_30d={self.correlation_30d})>"


class AssetAllocation(Base):
    """자산 배분 전략 및 리밸런싱 기록"""
    __tablename__ = "asset_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False)  # "60/40", "All Weather", "Risk Parity"
    target_allocations = Column(JSONB, nullable=False)  # {"STOCK": 0.60, "BOND": 0.40}
    current_allocations = Column(JSONB, nullable=True)  # Current actual allocations
    deviation = Column(Numeric(6, 4), nullable=True)  # Max deviation from target (%)
    rebalance_threshold = Column(Numeric(6, 4), nullable=False, default=0.05)  # 5% threshold
    last_rebalanced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_allocations_strategy', 'strategy_name'),
        Index('idx_allocations_rebalanced', 'last_rebalanced'),
    )

    def __repr__(self):
        return f"<AssetAllocation(id={self.id}, strategy='{self.strategy_name}')>"
