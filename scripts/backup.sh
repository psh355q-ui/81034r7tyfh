#!/bin/bash
################################################################################
# AI Trading System - Automated Backup Script
# Purpose: Daily backup of PostgreSQL database and Redis data
# Schedule: Run daily at midnight via DSM Task Scheduler
################################################################################

# Configuration
BACKUP_DIR="/volume1/backup/ai-trading"
DATE=$(date +%Y%m%d_%H%M%S)
DATE_SIMPLE=$(date +%Y%m%d)
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR
mkdir -p $BACKUP_DIR/db
mkdir -p $BACKUP_DIR/redis

# Log file
LOG_FILE="$BACKUP_DIR/backup.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log_message "=========================================="
log_message "Starting AI Trading System Backup"
log_message "=========================================="

# Check if containers are running
if ! docker ps | grep -q "ai-trading-timescaledb"; then
    log_message "ERROR: TimescaleDB container is not running"
    exit 1
fi

if ! docker ps | grep -q "ai-trading-redis"; then
    log_message "ERROR: Redis container is not running"
    exit 1
fi

# Backup PostgreSQL database
log_message "Backing up PostgreSQL database..."
docker exec ai-trading-timescaledb pg_dump -U postgres ai_trading | \
    gzip > $BACKUP_DIR/db/ai_trading_$DATE.sql.gz

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h $BACKUP_DIR/db/ai_trading_$DATE.sql.gz | cut -f1)
    log_message "✓ PostgreSQL backup completed: ai_trading_$DATE.sql.gz ($BACKUP_SIZE)"
else
    log_message "✗ PostgreSQL backup failed"
    exit 1
fi

# Backup Redis data
log_message "Backing up Redis data..."

# Trigger Redis save
docker exec ai-trading-redis redis-cli SAVE > /dev/null 2>&1
sleep 2

# Copy Redis dump file
if [ -f "/volume1/@docker/volumes/ai-trading-system_redis-data/_data/dump.rdb" ]; then
    cp /volume1/@docker/volumes/ai-trading-system_redis-data/_data/dump.rdb \
       $BACKUP_DIR/redis/redis_$DATE.rdb

    REDIS_SIZE=$(du -h $BACKUP_DIR/redis/redis_$DATE.rdb | cut -f1)
    log_message "✓ Redis backup completed: redis_$DATE.rdb ($REDIS_SIZE)"
else
    log_message "✗ Redis dump.rdb file not found"
fi

# Backup docker-compose and .env (excluding sensitive data)
log_message "Backing up configuration files..."
cp /volume1/docker/ai-trading-system/docker-compose.nas.yml \
   $BACKUP_DIR/docker-compose_$DATE_SIMPLE.yml
log_message "✓ docker-compose.nas.yml backed up"

# Backup .env (without sensitive data)
grep -v -E "(PASSWORD|SECRET|API_KEY)" /volume1/docker/ai-trading-system/.env \
    > $BACKUP_DIR/.env.template_$DATE_SIMPLE

log_message "✓ Configuration files backed up"

# Delete old backups (older than RETENTION_DAYS)
log_message "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

# Count files before cleanup
DB_BEFORE=$(find $BACKUP_DIR/db -name "*.sql.gz" | wc -l)
REDIS_BEFORE=$(find $BACKUP_DIR/redis -name "*.rdb" | wc -l)

# Delete old files
find $BACKUP_DIR/db -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/redis -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "docker-compose_*.yml" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name ".env.template_*" -mtime +$RETENTION_DAYS -delete

# Count files after cleanup
DB_AFTER=$(find $BACKUP_DIR/db -name "*.sql.gz" | wc -l)
REDIS_AFTER=$(find $BACKUP_DIR/redis -name "*.rdb" | wc -l)

log_message "✓ Cleanup completed:"
log_message "  - PostgreSQL backups: $DB_BEFORE → $DB_AFTER"
log_message "  - Redis backups: $REDIS_BEFORE → $REDIS_AFTER"

# Calculate total backup size
TOTAL_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
log_message "Total backup size: $TOTAL_SIZE"

# Verify latest backups
log_message "Verifying latest backups..."

# Test PostgreSQL backup integrity
if gzip -t $BACKUP_DIR/db/ai_trading_$DATE.sql.gz 2>/dev/null; then
    log_message "✓ PostgreSQL backup integrity verified"
else
    log_message "✗ PostgreSQL backup integrity check failed"
fi

log_message "=========================================="
log_message "Backup completed successfully"
log_message "=========================================="

exit 0
