"""
AI Portfolio Package - Account Partitioning & Portfolio Management

Contains:
- AccountPartitionManager: 가상 지갑 시스템 (Core/Income/Satellite)
"""

from backend.ai.portfolio.account_partitioning import (
    AccountPartitionManager,
    WalletType,
    WalletConfig,
    WalletPosition,
    WalletSummary,
    get_partition_manager,
    DEFAULT_WALLET_CONFIGS,
)

__all__ = [
    "AccountPartitionManager",
    "WalletType",
    "WalletConfig",
    "WalletPosition",
    "WalletSummary",
    "get_partition_manager",
    "DEFAULT_WALLET_CONFIGS",
]
