# Data Accumulation System

**Date**: 2025-12-27
**Purpose**: Automated data collection and validation for War Room debate system

## Overview

The Data Accumulation System coordinates automated data collection to validate and improve the War Room debate engine before transitioning to paper trading and live trading.

**Target Metrics**:
- **Duration**: 14+ days continuous operation
- **Debates**: 100+ War Room analysis sessions
- **Tickers**: 10+ unique tickers analyzed
- **Constitutional Compliance**: 95%+ pass rate

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            Data Accumulation Orchestrator                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ News         │  │ War Room     │  │ Constitutional│      │
│  │ Collection   │→ │ Debate       │→ │ Validation    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                 ↓                    ↓             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Database     │  │ Database     │  │ Database      │      │
│  │ (News)       │  │ (Analysis)   │  │ (Validation)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌──────────────────┐
                    │ Quality Metrics  │
                    │ & Monitoring     │
                    └──────────────────┘
```

---

## Components

### 1. **Data Accumulation Orchestrator**
**File**: [backend/orchestration/data_accumulation_orchestrator.py](backend/orchestration/data_accumulation_orchestrator.py)

Main coordinator that runs automated data collection cycles.

**Features**:
- News collection every 5 minutes (configurable)
- War Room debate execution on new articles
- Constitutional validation for every debate
- Dual logging (database + file)
- Progress tracking and reporting

**Pipeline**:
```
1. News Collection (RSS + Finviz) → Every 5 min
2. War Room Analysis → Triggered by news
3. Constitutional Validation → Every debate
4. Metrics Collection → Continuous
```

### 2. **News Collection**

#### RSS Crawler
**File**: [backend/news/rss_crawler_with_db.py](backend/news/rss_crawler_with_db.py)

Collects news from RSS feeds with Deep Reasoning analysis.

**Features**:
- Multi-source RSS feed monitoring
- Duplicate detection via content hash
- Database integration
- Prometheus metrics

#### Finviz Collector
**File**: [backend/data/collectors/finviz_collector.py](backend/data/collectors/finviz_collector.py)

Real-time US market news scraper from Finviz.

**Features**:
- 5-minute update cycle
- Anti-scraping protection (User-Agent rotation)
- Ticker extraction
- Duplicate prevention

### 3. **War Room Debate Engine**

#### Constitutional Debate Engine
**File**: [backend/ai/debate/constitutional_debate_engine.py](backend/ai/debate/constitutional_debate_engine.py)

Wrapper around AIDebateEngine with constitutional validation.

**Features**:
- Multi-agent debate (7 agents)
- Constitutional validation
- Shadow trade tracking
- Violation detection and logging

#### Improved Agents (Phase 2)
All agents enhanced with advanced metrics:

| Agent | File | Enhancement |
|-------|------|-------------|
| **Trader** | [trader_agent.py](backend/ai/debate/trader_agent.py) | Multi-timeframe analysis, Bollinger Bands |
| **Macro** | [macro_agent.py](backend/ai/debate/macro_agent.py) | Yield curve analysis (2Y-10Y) |
| **Analyst** | [analyst_agent.py](backend/ai/debate/analyst_agent.py) | PEG Ratio calculation |
| **News** | [news_agent.py](backend/ai/debate/news_agent.py) | Regulatory/litigation detection |
| **Risk** | [risk_agent.py](backend/ai/debate/risk_agent.py) | Sharpe Ratio, Kelly Criterion, CDS Premium |

### 4. **Constitutional Validation Logging**

#### Database Schema
**File**: [backend/database/schemas/constitutional_validation_schema.py](backend/database/schemas/constitutional_validation_schema.py)

Two tables for tracking validation results:

**`constitutional_validations`**:
- Debate metadata (ticker, action, confidence)
- Validation result (pass/fail)
- Violation summary
- Market context
- AI model votes

**`constitutional_violations`**:
- Specific violation details
- Article references (Constitution)
- Severity classification
- Auto-fix status

#### Migration
**File**: [backend/database/migrations/add_constitutional_validation_tables.sql](backend/database/migrations/add_constitutional_validation_tables.sql)

Run this to create the tables:
```bash
psql -U postgres -d ai_trading_system -f backend/database/migrations/add_constitutional_validation_tables.sql
```

### 5. **Data Quality Metrics**
**File**: [backend/monitoring/data_quality_metrics.py](backend/monitoring/data_quality_metrics.py)

Comprehensive quality tracking across all systems.

**Metrics Tracked**:
- **News Quality**: Article count, source diversity, coverage score
- **Debate Quality**: Confidence distribution, debate count
- **Constitutional Compliance**: Pass rate, violation types
- **Signal Quality**: Distribution balance, ticker coverage
- **System Health**: Error rate, uptime score

**Overall Quality Score**: Weighted average (0-100)

---

## Usage

### Quick Start (5-minute test)

```bash
cd D:\code\ai-trading-system

# Test mode (5 minutes, 5 debates)
python scripts/start_data_accumulation.py --test
```

### Production Mode (14-day accumulation)

```bash
# Standard 14-day, 100 debates
python scripts/start_data_accumulation.py --days 14 --debates 100

# Custom settings
python scripts/start_data_accumulation.py --days 7 --debates 50 --interval 10
```

**Options**:
- `--days`: Target duration (default: 14)
- `--debates`: Target number of debates (default: 100)
- `--interval`: News check interval in minutes (default: 5)
- `--test`: Run 5-minute test mode

### Monitoring

#### Real-time Monitor
```bash
python scripts/monitor_accumulation.py --refresh 5
```

Shows:
- Real-time progress
- Recent validations
- Constitutional compliance
- Database stats

Press `Ctrl+C` to exit.

#### Generate Quality Report
```bash
python backend/monitoring/data_quality_metrics.py --days 7 --save
```

Output:
- Console report with scores
- JSON file saved to `logs/quality_report_*.json`

---

## Output Files

### Logs Directory (`logs/`)

| File | Description |
|------|-------------|
| `data_accumulation.log` | Main orchestrator log |
| `constitutional_validations.jsonl` | Backup validation log (JSONL) |
| `accumulation_stats_*.json` | Final statistics (per session) |
| `quality_report_*.json` | Data quality reports |

### Database Tables

| Table | Records |
|-------|---------|
| `news_articles` | Collected news articles |
| `analysis_results` | Deep Reasoning analysis |
| `trading_signals` | Generated signals |
| `constitutional_validations` | Validation results |
| `constitutional_violations` | Specific violations |

---

## Quality Metrics

### Target Metrics (After 14 Days)

| Metric | Target | Weight |
|--------|--------|--------|
| **News Coverage** | 100+ articles, 5+ sources | 20% |
| **Avg Confidence** | 80%+ | 25% |
| **Constitutional Compliance** | 95%+ | 30% |
| **Signal Diversity** | 10+ tickers, balanced BUY/SELL/HOLD | 15% |
| **System Uptime** | 95%+ | 10% |
| **Overall Score** | **85+** | 100% |

### Quality Ratings

- **90-100**: 🟢 EXCELLENT
- **75-89**: 🟡 GOOD
- **60-74**: 🟠 FAIR
- **< 60**: 🔴 NEEDS IMPROVEMENT

---

## Database Queries

### Recent Validations
```sql
SELECT
    ticker,
    action,
    confidence,
    is_constitutional,
    validation_timestamp
FROM constitutional_validations
ORDER BY validation_timestamp DESC
LIMIT 100;
```

### Pass Rate by Ticker
```sql
SELECT
    ticker,
    COUNT(*) as total,
    SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END) as passed,
    ROUND(SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 1) as pass_rate
FROM constitutional_validations
GROUP BY ticker
ORDER BY total DESC;
```

### Most Common Violations
```sql
SELECT
    violation_type,
    severity,
    COUNT(*) as count
FROM constitutional_violations
GROUP BY violation_type, severity
ORDER BY count DESC
LIMIT 20;
```

### Daily Stats (Last 7 Days)
```sql
SELECT
    DATE(validation_timestamp) as date,
    COUNT(*) as total_validations,
    SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN NOT is_constitutional THEN 1 ELSE 0 END) as failed,
    ROUND(SUM(CASE WHEN is_constitutional THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 1) as pass_rate
FROM constitutional_validations
WHERE validation_timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(validation_timestamp)
ORDER BY date DESC;
```

---

## Troubleshooting

### No Articles Collected
**Problem**: `No new articles found` in logs

**Solutions**:
1. Check RSS feeds are accessible
2. Verify internet connection
3. Check Finviz is not blocking (User-Agent rotation)
4. Review `data_accumulation.log` for errors

### Database Errors
**Problem**: `constitutional_validations table does not exist`

**Solution**:
```bash
# Run migration
psql -U postgres -d ai_trading_system -f backend/database/migrations/add_constitutional_validation_tables.sql
```

### Low Quality Score
**Problem**: Overall quality score < 60

**Diagnosis**:
```bash
# Generate detailed report
python backend/monitoring/data_quality_metrics.py --days 7
```

Check each subscore:
- **News Coverage < 50**: Increase news sources or collection frequency
- **Confidence < 60%**: Review agent logic, improve data quality
- **Compliance < 90%**: Fix constitutional violations in agent code
- **Diversity < 50**: Collect more diverse news sources

---

## Next Steps

After successful data accumulation (14 days, 100+ debates):

1. **Analyze Results**
   - Review quality report
   - Identify top violations
   - Check confidence distribution

2. **Improve Agents (if needed)**
   - Fix common constitutional violations
   - Tune confidence thresholds
   - Enhance analysis logic

3. **Transition to Paper Trading**
   - Use validated agents
   - Test with real market data
   - Monitor performance

4. **Live Trading Preparation**
   - Final validation
   - Risk management review
   - Capital allocation strategy

---

## Files Created

### Core System
- [backend/orchestration/data_accumulation_orchestrator.py](backend/orchestration/data_accumulation_orchestrator.py) - Main orchestrator
- [backend/database/schemas/constitutional_validation_schema.py](backend/database/schemas/constitutional_validation_schema.py) - DB schema
- [backend/database/migrations/add_constitutional_validation_tables.sql](backend/database/migrations/add_constitutional_validation_tables.sql) - Migration
- [backend/monitoring/data_quality_metrics.py](backend/monitoring/data_quality_metrics.py) - Quality metrics

### Scripts
- [scripts/start_data_accumulation.py](scripts/start_data_accumulation.py) - Startup script
- [scripts/monitor_accumulation.py](scripts/monitor_accumulation.py) - Monitoring dashboard

### Documentation
- [DATA_ACCUMULATION.md](DATA_ACCUMULATION.md) - This file

---

## Contact

For issues or questions:
- Check logs in `logs/` directory
- Review database tables for data integrity
- Consult agent code for logic issues

**Author**: AI Trading System Team
**Last Updated**: 2025-12-27
