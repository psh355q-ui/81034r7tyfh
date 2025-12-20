#!/bin/bash
################################################################################
# AI Trading System - Auto Start Script
# Purpose: Automatically start Docker containers on NAS boot
# Usage: Add to DSM Task Scheduler (Boot-up trigger)
################################################################################

# Wait for NAS services to fully initialize
sleep 60

# Set working directory
cd /volume1/docker/ai-trading-system

# Start all containers
docker-compose -f docker-compose.nas.yml up -d

# Log startup
echo "[$(date '+%Y-%m-%d %H:%M:%S')] AI Trading System started successfully" >> /var/log/ai-trading-startup.log

# Verify containers are running
sleep 10
docker-compose -f docker-compose.nas.yml ps >> /var/log/ai-trading-startup.log

# Check health status
if docker ps | grep -q "ai-trading-redis.*healthy"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Redis is healthy" >> /var/log/ai-trading-startup.log
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Redis health check failed" >> /var/log/ai-trading-startup.log
fi

if docker ps | grep -q "ai-trading-timescaledb.*healthy"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ TimescaleDB is healthy" >> /var/log/ai-trading-startup.log
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ TimescaleDB health check failed" >> /var/log/ai-trading-startup.log
fi

exit 0
