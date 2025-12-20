# ELK Stack Configuration

This directory contains the configuration files for the ELK Stack (Elasticsearch, Logstash, Kibana) log centralization system.

## 📁 Directory Structure

```
elk/
├── elasticsearch/          # Elasticsearch configuration (auto-generated)
├── logstash/
│   ├── config/
│   │   └── logstash.yml   # Logstash service config
│   └── pipeline/
│       └── logstash.conf  # Log processing pipeline
├── filebeat/
│   └── filebeat.yml       # Filebeat configuration
└── kibana/
    └── dashboards/
        └── ai-trading-dashboard.ndjson  # Pre-built dashboards
```

## 🚀 Quick Start

### 1. Start ELK Stack

```bash
# Option 1: Use the quick start script
chmod +x scripts/start-elk.sh
./scripts/start-elk.sh

# Option 2: Manual start
docker-compose -f docker-compose.elk.yml up -d
```

### 2. Verify Installation

```bash
# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Check Kibana (in browser)
open http://localhost:5601
```

### 3. View Logs

1. Open Kibana: http://localhost:5601
2. Go to **Discover**
3. Select index pattern: `ai-trading-*`
4. Start exploring your logs!

## 📊 Available Dashboards

After importing the dashboard file, you'll have access to:

1. **Overview Dashboard**: General system health and metrics
2. **Error Monitoring**: All errors and exceptions
3. **Trading Activity**: Buy/sell orders and trades
4. **AI Cost Tracking**: OpenAI API usage and costs
5. **Performance Metrics**: API response times, DB queries

## 🔧 Configuration Details

### Logstash Pipeline

The pipeline (`logstash/pipeline/logstash.conf`) performs:

1. **Input**: Receives logs from Filebeat and direct TCP connections
2. **Filtering**:
   - Parse JSON logs
   - Extract structured fields (ticker, price, duration, etc.)
   - Classify by type (api_request, trading, ai_request, etc.)
   - Tag errors, warnings, and special events
3. **Output**: Send to Elasticsearch with daily indices

### Index Strategy

| Index Pattern | Purpose | Retention |
|--------------|---------|-----------|
| `ai-trading-YYYY.MM.DD` | All logs | 30 days |
| `ai-trading-errors-YYYY.MM.DD` | Errors only | 90 days |
| `ai-trading-trades-YYYY.MM.DD` | Trades only | 365 days |
| `ai-trading-ai-YYYY.MM.DD` | AI requests | 30 days |

### Resource Limits

Default configuration:

- **Elasticsearch**: 512MB RAM
- **Logstash**: 256MB RAM
- **Kibana**: Default (usually ~500MB)
- **Filebeat**: Minimal (~50MB)

Total: ~1.3GB RAM

## 📈 Usage Examples

### Python Integration

```python
from backend.utils.elk_logger import get_elk_logger

# Initialize
logger = get_elk_logger()

# Log API request
logger.log_api_request(
    endpoint="/stock/AAPL",
    method="GET",
    status_code=200,
    duration_ms=12.5
)

# Log trading activity
logger.log_trading_activity(
    action="BUY",
    ticker="AAPL",
    quantity=10,
    price=150.25
)

# Log AI request
logger.log_ai_request(
    model="gpt-4",
    prompt_tokens=1500,
    completion_tokens=500,
    cost=0.105
)
```

### Kibana Queries

```
# Find all errors for AAPL
tags:error AND ticker:"AAPL"

# Find slow API calls (>1s)
type:api_request AND response_time_ms > 1000

# Find expensive AI requests
type:ai_request AND cost_usd > 0.1

# Find trades in last hour
tags:trading AND @timestamp >= now-1h
```

## 🛠️ Maintenance

### Clean Old Indices

```bash
# Delete indices older than 30 days
curl -X DELETE "http://localhost:9200/ai-trading-2024.11.*"
```

### Backup

```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}
'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

### Restore

```bash
# Restore from snapshot
curl -X POST "http://localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

## 🔍 Troubleshooting

### Elasticsearch won't start

```bash
# Check logs
docker logs elasticsearch

# Common issue: vm.max_map_count too low
sudo sysctl -w vm.max_map_count=262144
```

### No logs appearing

```bash
# Check Logstash logs
docker logs logstash

# Check Filebeat logs
docker logs filebeat

# Test manual log send
echo '{"message":"test"}' | nc localhost 5000
```

### Kibana "Index pattern does not match any indices"

```bash
# Check if indices exist
curl http://localhost:9200/_cat/indices?v

# Create test log
python -c "
from backend.utils.elk_logger import get_elk_logger
logger = get_elk_logger()
logger.info('Test log', test=True)
"
```

## 📚 Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)

## 📞 Support

For issues or questions:
1. Check the [ELK Stack Guide](../docs/08_Monitoring/ELK_Stack_Guide.md)
2. Review [Troubleshooting Guide](../docs/09_Troubleshooting/Troubleshooting_Guide.md)
3. Open an issue on GitHub

---

**Last Updated**: 2025-12-10
**Version**: 1.0
