"""
Storage Configuration for NAS Compatibility.

Supports both local development and Synology NAS deployment with unified path handling.

Key Design Decisions:
1. **Path Abstraction**: Use logical paths (tags) mapped to physical locations
2. **NAS Detection**: Auto-detect if running on Synology NAS
3. **Fallback Strategy**: Local paths when NAS unavailable
4. **Volume Mounting**: Support Docker volume mounts for NAS shares
"""

import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StorageLocation(Enum):
    """Storage location types with logical tags."""
    SEC_FILINGS = "sec_filings"           # SEC 10-Q/10-K files
    AI_ANALYSIS_CACHE = "ai_cache"        # AI analysis results
    STOCK_PRICES = "stock_prices"         # Yahoo Finance historical data
    NEWS_ARCHIVE = "news_archive"         # News articles
    EMBEDDINGS = "embeddings"             # RAG vector embeddings
    BACKTEST_RESULTS = "backtest"         # Backtest outputs
    LOGS = "logs"                         # Application logs


@dataclass
class StoragePath:
    """Storage path configuration with NAS support."""
    location_tag: StorageLocation
    local_path: Path
    nas_path: Optional[Path] = None
    docker_volume: Optional[str] = None
    max_size_gb: Optional[int] = None

    def get_active_path(self) -> Path:
        """
        Get currently active storage path (NAS or local).

        Priority:
        1. Docker volume mount (if exists)
        2. NAS path (if exists and accessible)
        3. Local path (fallback)
        """
        # Check Docker volume mount
        if self.docker_volume:
            docker_path = Path(f"/mnt/{self.docker_volume}")
            if docker_path.exists():
                logger.info(f"Using Docker volume: {docker_path}")
                return docker_path

        # Check NAS path
        if self.nas_path and self.nas_path.exists():
            logger.info(f"Using NAS path: {self.nas_path}")
            return self.nas_path

        # Fallback to local
        logger.info(f"Using local path: {self.local_path}")
        self.local_path.mkdir(parents=True, exist_ok=True)
        return self.local_path

    def ensure_exists(self) -> Path:
        """Create directory if not exists and return active path."""
        active = self.get_active_path()
        active.mkdir(parents=True, exist_ok=True)
        return active


class StorageConfig:
    """
    Centralized storage configuration with NAS compatibility.

    Environment Variables:
    - NAS_HOST: Synology NAS hostname/IP (e.g., "192.168.1.100")
    - NAS_VOLUME: NAS volume name (e.g., "volume1")
    - NAS_SHARE: NAS shared folder (e.g., "ai_trading")
    - DOCKER_STORAGE_PATH: Docker volume mount point (e.g., "/mnt/ai_trading_data")

    Usage:
        config = StorageConfig()
        sec_path = config.get_path(StorageLocation.SEC_FILINGS)
        # Returns: /volume1/ai_trading/sec_filings (NAS)
        #      or: D:/code/ai-trading-system/data/sec_filings (local)
    """

    def __init__(self):
        """Initialize storage configuration."""
        self.is_nas = self._detect_nas_environment()
        self.base_local = Path("d:/code/ai-trading-system/data")
        self.base_nas = self._get_nas_base_path()

        # Define storage locations with tags
        self.storage_paths: Dict[StorageLocation, StoragePath] = {
            StorageLocation.SEC_FILINGS: StoragePath(
                location_tag=StorageLocation.SEC_FILINGS,
                local_path=self.base_local / "sec_filings",
                nas_path=self.base_nas / "sec_filings" if self.base_nas else None,
                docker_volume="ai_trading_sec",
                max_size_gb=10  # 10GB limit
            ),
            StorageLocation.AI_ANALYSIS_CACHE: StoragePath(
                location_tag=StorageLocation.AI_ANALYSIS_CACHE,
                local_path=self.base_local / "ai_cache",
                nas_path=self.base_nas / "ai_cache" if self.base_nas else None,
                docker_volume="ai_trading_cache",
                max_size_gb=5
            ),
            StorageLocation.STOCK_PRICES: StoragePath(
                location_tag=StorageLocation.STOCK_PRICES,
                local_path=self.base_local / "stock_prices",
                nas_path=self.base_nas / "stock_prices" if self.base_nas else None,
                docker_volume="ai_trading_prices",
                max_size_gb=20  # Stock data can be large
            ),
            StorageLocation.NEWS_ARCHIVE: StoragePath(
                location_tag=StorageLocation.NEWS_ARCHIVE,
                local_path=self.base_local / "news",
                nas_path=self.base_nas / "news" if self.base_nas else None,
                docker_volume="ai_trading_news",
                max_size_gb=15
            ),
            StorageLocation.EMBEDDINGS: StoragePath(
                location_tag=StorageLocation.EMBEDDINGS,
                local_path=self.base_local / "embeddings",
                nas_path=self.base_nas / "embeddings" if self.base_nas else None,
                docker_volume="ai_trading_embeddings",
                max_size_gb=30  # Large for 10K+ documents
            ),
            StorageLocation.BACKTEST_RESULTS: StoragePath(
                location_tag=StorageLocation.BACKTEST_RESULTS,
                local_path=self.base_local / "backtest",
                nas_path=self.base_nas / "backtest" if self.base_nas else None,
                docker_volume="ai_trading_backtest",
                max_size_gb=5
            ),
            StorageLocation.LOGS: StoragePath(
                location_tag=StorageLocation.LOGS,
                local_path=self.base_local / "logs",
                nas_path=self.base_nas / "logs" if self.base_nas else None,
                docker_volume="ai_trading_logs",
                max_size_gb=2
            ),
        }

        logger.info(f"Storage initialized (NAS: {self.is_nas})")
        if self.base_nas:
            logger.info(f"NAS base path: {self.base_nas}")

    def _detect_nas_environment(self) -> bool:
        """
        Detect if running on Synology NAS.

        Checks:
        1. Environment variable NAS_HOST
        2. /volume1 directory exists (Synology standard)
        3. Docker environment with NAS mounts
        """
        # Check env var
        if os.getenv("NAS_HOST"):
            return True

        # Check Synology volume
        if Path("/volume1").exists():
            return True

        # Check Docker NAS mount
        if os.getenv("DOCKER_STORAGE_PATH"):
            return True

        return False

    def _get_nas_base_path(self) -> Optional[Path]:
        """
        Get NAS base path based on environment.

        Priority:
        1. DOCKER_STORAGE_PATH (Docker mount)
        2. /volume1/{NAS_SHARE} (Synology)
        3. None (local only)
        """
        # Docker mount
        docker_path = os.getenv("DOCKER_STORAGE_PATH")
        if docker_path:
            return Path(docker_path)

        # Synology NAS
        nas_volume = os.getenv("NAS_VOLUME", "volume1")
        nas_share = os.getenv("NAS_SHARE", "ai_trading")

        nas_path = Path(f"/{nas_volume}/{nas_share}")
        if nas_path.exists():
            return nas_path

        return None

    def get_path(self, location: StorageLocation) -> Path:
        """
        Get active storage path for a location.

        Args:
            location: Storage location tag

        Returns:
            Active path (NAS or local)
        """
        storage_path = self.storage_paths.get(location)
        if not storage_path:
            raise ValueError(f"Unknown storage location: {location}")

        return storage_path.ensure_exists()

    def get_file_path(
        self,
        location: StorageLocation,
        filename: str,
        create_dirs: bool = True
    ) -> Path:
        """
        Get full file path within a storage location.

        Args:
            location: Storage location tag
            filename: File name (can include subdirs)
            create_dirs: Create parent directories if needed

        Returns:
            Full file path

        Example:
            >>> config.get_file_path(
            ...     StorageLocation.SEC_FILINGS,
            ...     "AAPL/10-Q_2024-Q3.txt"
            ... )
            Path("/volume1/ai_trading/sec_filings/AAPL/10-Q_2024-Q3.txt")
        """
        base_path = self.get_path(location)
        file_path = base_path / filename

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        return file_path

    def get_storage_stats(self) -> Dict[str, Dict]:
        """
        Get storage usage statistics.

        Returns:
            Dict with location stats (size, file count, etc.)
        """
        stats = {}

        for location, storage_path in self.storage_paths.items():
            active_path = storage_path.get_active_path()

            if active_path.exists():
                total_size = sum(
                    f.stat().st_size
                    for f in active_path.rglob("*")
                    if f.is_file()
                )
                file_count = sum(1 for _ in active_path.rglob("*") if _.is_file())

                stats[location.value] = {
                    "path": str(active_path),
                    "size_mb": total_size / (1024 * 1024),
                    "file_count": file_count,
                    "max_size_gb": storage_path.max_size_gb,
                    "usage_pct": (total_size / (storage_path.max_size_gb * 1024**3) * 100)
                    if storage_path.max_size_gb
                    else 0,
                }
            else:
                stats[location.value] = {
                    "path": str(active_path),
                    "size_mb": 0,
                    "file_count": 0,
                    "max_size_gb": storage_path.max_size_gb,
                    "usage_pct": 0,
                }

        return stats


# Singleton instance
_storage_config: Optional[StorageConfig] = None


def get_storage_config() -> StorageConfig:
    """Get or create storage config singleton."""
    global _storage_config
    if _storage_config is None:
        _storage_config = StorageConfig()
    return _storage_config


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = get_storage_config()

    # Get SEC filings path
    sec_path = config.get_path(StorageLocation.SEC_FILINGS)
    print(f"SEC Filings: {sec_path}")

    # Get specific file path
    file_path = config.get_file_path(
        StorageLocation.SEC_FILINGS,
        "AAPL/10-Q_2024-Q3.txt"
    )
    print(f"File path: {file_path}")

    # Get storage stats
    stats = config.get_storage_stats()
    for location, stat in stats.items():
        print(f"\n{location}:")
        print(f"  Path: {stat['path']}")
        print(f"  Size: {stat['size_mb']:.2f} MB")
        print(f"  Files: {stat['file_count']}")
        print(f"  Usage: {stat['usage_pct']:.1f}%")
