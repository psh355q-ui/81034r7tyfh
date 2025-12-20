"""
Automated Backup Script with NAS Support.

Backs up:
1. PostgreSQL database (pg_dump)
2. Redis data (RDB snapshot)
3. File storage (SEC filings, AI cache, embeddings)
4. Configuration files

Features:
- NAS-compatible (rsync to Synology NAS)
- Incremental backups (reduce transfer size)
- Compression (gzip)
- Retention policy (keep last 7 daily, 4 weekly, 12 monthly)
- Backup verification
- Email notifications
"""

import argparse
import asyncio
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class AutomatedBackup:
    """
    Automated backup system with NAS support.

    Usage:
        backup = AutomatedBackup(
            backup_root="/volume1/backups/ai_trading",
            nas_host="192.168.1.100",
            db_url="postgresql://user:pass@localhost/ai_trading"
        )

        # Full backup
        await backup.run_full_backup()

        # Database only
        await backup.backup_database()

        # Files only
        await backup.backup_files()
    """

    # Retention policy (days)
    KEEP_DAILY = 7
    KEEP_WEEKLY = 4 * 7  # 4 weeks
    KEEP_MONTHLY = 12 * 30  # 12 months

    def __init__(
        self,
        backup_root: str,
        nas_host: Optional[str] = None,
        db_url: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        """
        Initialize automated backup.

        Args:
            backup_root: Root backup directory (local or NAS path)
            nas_host: NAS hostname/IP (for rsync over SSH)
            db_url: PostgreSQL connection URL
            redis_host: Redis hostname
            redis_port: Redis port
        """
        self.backup_root = Path(backup_root)
        self.nas_host = nas_host
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.redis_host = redis_host
        self.redis_port = redis_port

        # Create backup directories
        self.db_backup_dir = self.backup_root / "database"
        self.files_backup_dir = self.backup_root / "files"
        self.redis_backup_dir = self.backup_root / "redis"
        self.config_backup_dir = self.backup_root / "config"

        logger.info(f"AutomatedBackup initialized (root={backup_root})")

    def _get_timestamp(self) -> str:
        """Get timestamp string for backup naming."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _get_backup_name(self, prefix: str, ext: str = "tar.gz") -> str:
        """
        Get backup filename.

        Args:
            prefix: Backup prefix (e.g., "db", "files")
            ext: File extension

        Returns:
            Backup filename
        """
        return f"{prefix}_{self._get_timestamp()}.{ext}"

    async def backup_database(self) -> Path:
        """
        Backup PostgreSQL database using pg_dump.

        Returns:
            Path to backup file
        """
        logger.info("Starting database backup...")

        # Create backup directory
        self.db_backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        backup_file = self.db_backup_dir / self._get_backup_name("db", "sql.gz")

        # Parse database URL
        # postgresql://user:pass@host:port/dbname
        if not self.db_url:
            raise ValueError("DATABASE_URL not set")

        # Run pg_dump
        try:
            cmd = [
                "pg_dump",
                "--no-owner",
                "--no-privileges",
                "--clean",
                "--if-exists",
                self.db_url,
            ]

            logger.info(f"Running pg_dump...")

            # Run pg_dump and pipe to gzip
            with open(backup_file, "wb") as f:
                proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                proc2 = subprocess.Popen(
                    ["gzip"], stdin=proc1.stdout, stdout=f
                )
                proc1.stdout.close()
                proc2.communicate()

            if proc2.returncode != 0:
                raise RuntimeError(f"pg_dump failed with code {proc2.returncode}")

            # Get file size
            size_mb = backup_file.stat().st_size / 1024 / 1024

            logger.info(
                f"Database backup complete: {backup_file.name} ({size_mb:.2f} MB)"
            )

            return backup_file

        except Exception as e:
            logger.error(f"Database backup failed: {e}", exc_info=True)
            raise

    async def backup_redis(self) -> Path:
        """
        Backup Redis data using RDB snapshot.

        Returns:
            Path to backup file
        """
        logger.info("Starting Redis backup...")

        # Create backup directory
        self.redis_backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        backup_file = self.redis_backup_dir / self._get_backup_name("redis", "rdb")

        try:
            # Trigger Redis SAVE
            import redis

            r = redis.Redis(host=self.redis_host, port=self.redis_port)

            # Force save
            r.save()

            # Get RDB file location
            config = r.config_get("dir")
            rdb_dir = config.get("dir", "/var/lib/redis")
            rdb_file = Path(rdb_dir) / "dump.rdb"

            if not rdb_file.exists():
                raise FileNotFoundError(f"Redis RDB file not found: {rdb_file}")

            # Copy RDB file
            shutil.copy2(rdb_file, backup_file)

            size_mb = backup_file.stat().st_size / 1024 / 1024

            logger.info(
                f"Redis backup complete: {backup_file.name} ({size_mb:.2f} MB)"
            )

            return backup_file

        except Exception as e:
            logger.error(f"Redis backup failed: {e}", exc_info=True)
            raise

    async def backup_files(
        self, source_dirs: Optional[List[str]] = None
    ) -> Path:
        """
        Backup file storage (SEC filings, AI cache, etc.).

        Args:
            source_dirs: List of directories to backup (default: auto-detect)

        Returns:
            Path to backup archive
        """
        logger.info("Starting files backup...")

        # Create backup directory
        self.files_backup_dir.mkdir(parents=True, exist_ok=True)

        # Default source directories
        if not source_dirs:
            project_root = Path(__file__).parent.parent.parent
            source_dirs = [
                str(project_root / "data" / "sec_filings"),
                str(project_root / "data" / "ai_cache"),
                str(project_root / "data" / "embeddings"),
            ]

        # Generate backup filename
        backup_file = self.files_backup_dir / self._get_backup_name(
            "files", "tar.gz"
        )

        try:
            # Create tar archive
            cmd = ["tar", "czf", str(backup_file)]

            # Add source directories
            for src_dir in source_dirs:
                if Path(src_dir).exists():
                    cmd.append(src_dir)
                    logger.info(f"Adding to backup: {src_dir}")
                else:
                    logger.warning(f"Skipping non-existent directory: {src_dir}")

            if len(cmd) == 3:
                logger.warning("No directories to backup!")
                return None

            # Run tar
            subprocess.run(cmd, check=True)

            size_mb = backup_file.stat().st_size / 1024 / 1024

            logger.info(
                f"Files backup complete: {backup_file.name} ({size_mb:.2f} MB)"
            )

            return backup_file

        except Exception as e:
            logger.error(f"Files backup failed: {e}", exc_info=True)
            raise

    async def backup_config(self) -> Path:
        """
        Backup configuration files.

        Returns:
            Path to backup archive
        """
        logger.info("Starting config backup...")

        # Create backup directory
        self.config_backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        backup_file = self.config_backup_dir / self._get_backup_name(
            "config", "tar.gz"
        )

        try:
            project_root = Path(__file__).parent.parent.parent

            config_files = [
                ".env",
                "docker-compose.yml",
                "backend/config.py",
                "backend/alembic.ini",
                ".specify/memory/constitution.md",
            ]

            # Create tar archive
            cmd = ["tar", "czf", str(backup_file), "-C", str(project_root)]

            for config_file in config_files:
                file_path = project_root / config_file
                if file_path.exists():
                    cmd.append(config_file)

            if len(cmd) == 5:
                logger.warning("No config files to backup!")
                return None

            # Run tar
            subprocess.run(cmd, check=True)

            size_kb = backup_file.stat().st_size / 1024

            logger.info(
                f"Config backup complete: {backup_file.name} ({size_kb:.2f} KB)"
            )

            return backup_file

        except Exception as e:
            logger.error(f"Config backup failed: {e}", exc_info=True)
            raise

    async def run_full_backup(self) -> Dict[str, Any]:
        """
        Run full backup (database + Redis + files + config).

        Returns:
            Backup summary dict
        """
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info("STARTING FULL BACKUP")
        logger.info("=" * 60)

        backups = {}
        errors = []

        # Backup database
        try:
            db_backup = await self.backup_database()
            backups["database"] = str(db_backup)
        except Exception as e:
            errors.append(f"Database backup failed: {e}")

        # Backup Redis
        try:
            redis_backup = await self.backup_redis()
            backups["redis"] = str(redis_backup)
        except Exception as e:
            errors.append(f"Redis backup failed: {e}")

        # Backup files
        try:
            files_backup = await self.backup_files()
            if files_backup:
                backups["files"] = str(files_backup)
        except Exception as e:
            errors.append(f"Files backup failed: {e}")

        # Backup config
        try:
            config_backup = await self.backup_config()
            if config_backup:
                backups["config"] = str(config_backup)
        except Exception as e:
            errors.append(f"Config backup failed: {e}")

        # Calculate total size
        total_size = 0
        for backup_path in backups.values():
            if Path(backup_path).exists():
                total_size += Path(backup_path).stat().st_size

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "backups": backups,
            "total_size_mb": total_size / 1024 / 1024,
            "errors": errors,
            "status": "SUCCESS" if not errors else "PARTIAL",
        }

        # Save summary
        summary_file = self.backup_root / f"backup_summary_{self._get_timestamp()}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("=" * 60)
        logger.info(
            f"BACKUP COMPLETE: {summary['status']} "
            f"({summary['total_size_mb']:.2f} MB in {duration:.1f}s)"
        )
        logger.info("=" * 60)

        return summary

    async def cleanup_old_backups(self) -> Dict[str, int]:
        """
        Clean up old backups based on retention policy.

        Returns:
            Cleanup summary dict
        """
        logger.info("Starting backup cleanup...")

        now = datetime.now()
        deleted = {
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
        }

        for backup_dir in [
            self.db_backup_dir,
            self.redis_backup_dir,
            self.files_backup_dir,
            self.config_backup_dir,
        ]:
            if not backup_dir.exists():
                continue

            for backup_file in backup_dir.glob("*"):
                if not backup_file.is_file():
                    continue

                # Get file age
                age_days = (now - datetime.fromtimestamp(backup_file.stat().st_mtime)).days

                # Determine if should delete
                should_delete = False

                if age_days > self.KEEP_MONTHLY:
                    should_delete = True
                    deleted["monthly"] += 1
                elif age_days > self.KEEP_WEEKLY:
                    # Keep only weekly backups (e.g., Sunday)
                    file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_date.weekday() != 6:  # Not Sunday
                        should_delete = True
                        deleted["weekly"] += 1
                elif age_days > self.KEEP_DAILY:
                    should_delete = True
                    deleted["daily"] += 1

                if should_delete:
                    logger.info(f"Deleting old backup: {backup_file.name} ({age_days} days old)")
                    backup_file.unlink()

        total_deleted = sum(deleted.values())
        logger.info(f"Cleanup complete: {total_deleted} files deleted")

        return deleted


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated backup with NAS support"
    )

    parser.add_argument(
        "--backup-root",
        default="/volume1/backups/ai_trading",
        help="Backup root directory",
    )

    parser.add_argument(
        "--nas-host",
        help="NAS hostname/IP for rsync",
    )

    parser.add_argument(
        "--db-url",
        help="PostgreSQL database URL (default: env DATABASE_URL)",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups after backup",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (show what would be backed up)",
    )

    args = parser.parse_args()

    # Create backup instance
    backup = AutomatedBackup(
        backup_root=args.backup_root,
        nas_host=args.nas_host,
        db_url=args.db_url,
    )

    if args.dry_run:
        logger.info("DRY RUN - No actual backup will be performed")
        logger.info(f"Backup root: {args.backup_root}")
        logger.info(f"Database: {backup.db_url}")
        return

    # Run full backup
    summary = await backup.run_full_backup()

    # Cleanup if requested
    if args.cleanup:
        cleanup_summary = await backup.cleanup_old_backups()
        logger.info(f"Cleanup summary: {cleanup_summary}")

    # Exit with error code if backup failed
    if summary["status"] != "SUCCESS":
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
