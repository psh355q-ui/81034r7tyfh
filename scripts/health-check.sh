#!/bin/bash
################################################################################
# AI Trading System - Health Check Script
# Purpose: Monitor system health and send alerts if issues detected
# Usage: Run periodically via DSM Task Scheduler (every 5-10 minutes)
################################################################################

# Configuration
LOG_FILE="/var/log/ai-trading-health.log"
ALERT_EMAIL=""  # Set in .env if email alerts are enabled
SLACK_WEBHOOK=""  # Set in .env if Slack alerts are enabled

# Expected containers
EXPECTED_CONTAINERS=("ai-trading-redis" "ai-trading-timescaledb" "ai-trading-prometheus" "ai-trading-grafana")

# Health check results
ERRORS=()
WARNINGS=()

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to check container status
check_container() {
    local container_name=$1

    if ! docker ps | grep -q "$container_name"; then
        ERRORS+=("Container $container_name is not running")
        return 1
    fi

    # Check if container is healthy (for containers with healthcheck)
    if docker ps | grep "$container_name" | grep -q "healthy"; then
        log_message "✓ $container_name is healthy"
    elif docker ps | grep "$container_name" | grep -q "unhealthy"; then
        ERRORS+=("Container $container_name is unhealthy")
        return 1
    else
        log_message "✓ $container_name is running"
    fi

    return 0
}

# Function to check Redis
check_redis() {
    if docker exec ai-trading-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_message "✓ Redis responding to ping"

        # Check Redis memory usage
        USED_MEMORY=$(docker exec ai-trading-redis redis-cli INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log_message "  Redis memory usage: $USED_MEMORY"
    else
        ERRORS+=("Redis is not responding to ping")
    fi
}

# Function to check TimescaleDB
check_timescaledb() {
    if docker exec ai-trading-timescaledb psql -U postgres -d ai_trading -c "SELECT 1" &>/dev/null; then
        log_message "✓ TimescaleDB is accepting connections"

        # Check feature count
        FEATURE_COUNT=$(docker exec ai-trading-timescaledb psql -U postgres -d ai_trading -t -c "SELECT COUNT(*) FROM features;" 2>/dev/null | tr -d ' ')
        log_message "  Features stored: $FEATURE_COUNT"
    else
        ERRORS+=("TimescaleDB is not accepting connections")
    fi
}

# Function to check Prometheus
check_prometheus() {
    if curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Prometheus"; then
        log_message "✓ Prometheus is healthy"
    else
        WARNINGS+=("Prometheus health check failed")
    fi
}

# Function to check Grafana
check_grafana() {
    if curl -s http://localhost:3001/api/health 2>/dev/null | grep -q "ok"; then
        log_message "✓ Grafana is healthy"
    else
        WARNINGS+=("Grafana health check failed")
    fi
}

# Function to check disk space
check_disk_space() {
    DISK_USAGE=$(df -h /volume1/docker/ai-trading-system | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ $DISK_USAGE -gt 90 ]; then
        ERRORS+=("Disk usage is critical: ${DISK_USAGE}%")
    elif [ $DISK_USAGE -gt 80 ]; then
        WARNINGS+=("Disk usage is high: ${DISK_USAGE}%")
    else
        log_message "✓ Disk usage: ${DISK_USAGE}%"
    fi
}

# Function to check memory usage
check_memory() {
    TOTAL_MEMORY=$(docker stats --no-stream --format "{{.MemUsage}}" | awk -F'/' '{sum+=$1} END {print sum}')
    log_message "✓ Total Docker memory usage: ${TOTAL_MEMORY}MB"
}

# Main health check
log_message "=========================================="
log_message "Starting health check"
log_message "=========================================="

# Check all containers
for container in "${EXPECTED_CONTAINERS[@]}"; do
    check_container "$container"
done

# Check services
check_redis
check_timescaledb
check_prometheus
check_grafana

# Check system resources
check_disk_space
check_memory

# Report results
log_message "=========================================="
if [ ${#ERRORS[@]} -eq 0 ] && [ ${#WARNINGS[@]} -eq 0 ]; then
    log_message "✓ All health checks passed"
    exit 0
else
    if [ ${#ERRORS[@]} -gt 0 ]; then
        log_message "✗ ERRORS detected:"
        for error in "${ERRORS[@]}"; do
            log_message "  - $error"
        done
    fi

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        log_message "⚠ WARNINGS detected:"
        for warning in "${WARNINGS[@]}"; do
            log_message "  - $warning"
        done
    fi

    # TODO: Send alerts via email or Slack if configured

    exit 1
fi
