#!/bin/bash
################################################################################
# AI Trading System - Database Restore Script
# Purpose: Restore PostgreSQL database from backup
# Usage: ./restore.sh <backup_file.sql.gz>
################################################################################

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /volume1/backup/ai-trading/db/*.sql.gz
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "AI Trading System - Database Restore"
echo "=========================================="
echo "Backup file: $BACKUP_FILE"
echo ""

# Warning
read -p "⚠️  WARNING: This will replace the current database. Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if container is running
if ! docker ps | grep -q "ai-trading-timescaledb"; then
    echo "ERROR: TimescaleDB container is not running"
    exit 1
fi

echo ""
echo "Step 1: Creating database backup before restore..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec ai-trading-timescaledb pg_dump -U postgres ai_trading | \
    gzip > /volume1/backup/ai-trading/db/pre_restore_backup_$TIMESTAMP.sql.gz
echo "✓ Pre-restore backup created: pre_restore_backup_$TIMESTAMP.sql.gz"

echo ""
echo "Step 2: Dropping existing database..."
docker exec ai-trading-timescaledb psql -U postgres -c "DROP DATABASE IF EXISTS ai_trading;"
echo "✓ Database dropped"

echo ""
echo "Step 3: Creating new database..."
docker exec ai-trading-timescaledb psql -U postgres -c "CREATE DATABASE ai_trading;"
echo "✓ Database created"

echo ""
echo "Step 4: Restoring from backup..."
gunzip -c $BACKUP_FILE | docker exec -i ai-trading-timescaledb psql -U postgres -d ai_trading

if [ $? -eq 0 ]; then
    echo "✓ Database restored successfully"
else
    echo "✗ Database restore failed"
    echo ""
    echo "Attempting to restore from pre-restore backup..."
    gunzip -c /volume1/backup/ai-trading/db/pre_restore_backup_$TIMESTAMP.sql.gz | \
        docker exec -i ai-trading-timescaledb psql -U postgres -d ai_trading
    exit 1
fi

echo ""
echo "Step 5: Verifying restore..."
ROW_COUNT=$(docker exec ai-trading-timescaledb psql -U postgres -d ai_trading -t -c "SELECT COUNT(*) FROM features;")
echo "✓ Features table has $ROW_COUNT rows"

HYPERTABLE_COUNT=$(docker exec ai-trading-timescaledb psql -U postgres -d ai_trading -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables;")
echo "✓ Hypertables: $HYPERTABLE_COUNT"

echo ""
echo "=========================================="
echo "Restore completed successfully!"
echo "=========================================="

exit 0
