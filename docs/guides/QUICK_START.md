# Quick Start Guide - Data Accumulation

## 1. Setup Database (One-time)

```bash
# Create constitutional validation tables
psql -U postgres -d ai_trading_system -f backend/database/migrations/add_constitutional_validation_tables.sql
```

## 2. Start Data Accumulation

### Test Mode (5 minutes)
```bash
python scripts/start_data_accumulation.py --test
```

### Production Mode (14 days, 100 debates)
```bash
python scripts/start_data_accumulation.py --days 14 --debates 100
```

## 3. Monitor Progress

### Real-time Dashboard
```bash
python scripts/monitor_accumulation.py
```

### Quality Report
```bash
python backend/monitoring/data_quality_metrics.py --days 7 --save
```

## 4. Check Results

### View Logs
```bash
# Main log
tail -f logs/data_accumulation.log

# Constitutional validations
tail -f logs/constitutional_validations.jsonl
```

### Database Queries
```sql
-- Recent validations
SELECT * FROM constitutional_validations ORDER BY validation_timestamp DESC LIMIT 10;

-- Pass rate
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END) as passed,
    ROUND(100.0 * SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END) / COUNT(*), 1) as pass_rate
FROM constitutional_validations;
```

## Target Metrics

| Metric | Target |
|--------|--------|
| Duration | 14+ days |
| Debates | 100+ |
| Tickers | 10+ |
| Compliance Rate | 95%+ |
| Avg Confidence | 80%+ |
| Overall Quality Score | 85+ |

## Common Commands

```bash
# Start with custom settings
python scripts/start_data_accumulation.py --days 7 --debates 50 --interval 10

# Generate quality report
python backend/monitoring/data_quality_metrics.py --days 7

# Monitor with 10-second refresh
python scripts/monitor_accumulation.py --refresh 10

# View help
python scripts/start_data_accumulation.py --help
```

## Files to Check

- `logs/data_accumulation.log` - Main log
- `logs/accumulation_stats_*.json` - Session statistics
- `logs/quality_report_*.json` - Quality reports
- `logs/constitutional_validations.jsonl` - Validation backup

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No articles collected | Check internet, RSS feeds, Finviz access |
| DB table not found | Run migration SQL script |
| Low quality score | Review detailed report, check agent logic |
| High error rate | Check logs for specific errors |

For full documentation, see [DATA_ACCUMULATION.md](DATA_ACCUMULATION.md)
