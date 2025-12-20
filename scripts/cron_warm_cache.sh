#!/bin/bash
# 
# Cache Warming Cron Job
# 
# Schedule this to run 30 minutes before US market open (9:30 AM ET)
# 
# Cron example (run at 8:30 AM ET = 1:30 PM UTC on weekdays):
# 30 13 * * 1-5 /volume1/docker/ai-trading-system/scripts/cron_warm_cache.sh
#
# Installation:
# 1. Copy this file to: /volume1/docker/ai-trading-system/scripts/
# 2. Make executable: chmod +x cron_warm_cache.sh
# 3. Add to cron: crontab -e
#

# Exit on error
set -e

# Logging
LOG_DIR="/volume1/docker/ai-trading-system/logs"
LOG_FILE="${LOG_DIR}/cache_warming_$(date +%Y%m%d).log"

mkdir -p "${LOG_DIR}"

echo "========================================" >> "${LOG_FILE}"
echo "Cache Warming Started: $(date)" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"

# Navigate to project directory
cd /volume1/docker/ai-trading-system/backend

# Activate virtual environment (if using one)
# source venv/bin/activate

# Run cache warming script
python3 scripts/warm_cache.py \
    --portfolio "${PORTFOLIO_TICKERS:-AAPL,MSFT,GOOGL}" \
    --watchlist "${WATCHLIST_TICKERS:-TSLA,NVDA,AMD,META,NFLX}" \
    --top-market-cap 30 \
    --max-workers 10 \
    >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Cache warming completed successfully" >> "${LOG_FILE}"
else
    echo "❌ Cache warming failed with exit code ${EXIT_CODE}" >> "${LOG_FILE}"
fi

echo "========================================" >> "${LOG_FILE}"
echo "Cache Warming Ended: $(date)" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"
echo "" >> "${LOG_FILE}"

# Clean up old logs (keep last 7 days)
find "${LOG_DIR}" -name "cache_warming_*.log" -mtime +7 -delete

exit ${EXIT_CODE}