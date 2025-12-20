#!/bin/bash

# ELK Stack Quick Start Script
# Starts Elasticsearch, Logstash, Kibana, and Filebeat

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

log_info "Starting ELK Stack..."

# Check vm.max_map_count (required for Elasticsearch)
log_info "Checking system requirements..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURRENT_MAX_MAP=$(sysctl -n vm.max_map_count)
    if [ "$CURRENT_MAX_MAP" -lt 262144 ]; then
        log_warning "vm.max_map_count is too low ($CURRENT_MAX_MAP)"
        log_info "Setting vm.max_map_count=262144..."
        sudo sysctl -w vm.max_map_count=262144
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "macOS detected - vm.max_map_count is handled by Docker Desktop"
fi

# Start ELK Stack
log_info "Starting Elasticsearch, Logstash, Kibana, Filebeat..."
docker-compose -f docker-compose.elk.yml up -d

# Wait for Elasticsearch to be ready
log_info "Waiting for Elasticsearch to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30

while ! curl -s http://localhost:9200/_cluster/health > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
        log_error "Elasticsearch failed to start after $MAX_RETRIES attempts"
        docker logs elasticsearch
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
log_info "Elasticsearch is ready!"

# Wait for Kibana to be ready
log_info "Waiting for Kibana to be ready..."
RETRY_COUNT=0

while ! curl -s http://localhost:5601/api/status > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
        log_error "Kibana failed to start after $MAX_RETRIES attempts"
        docker logs kibana
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
log_info "Kibana is ready!"

# Check cluster health
log_info "Checking Elasticsearch cluster health..."
HEALTH=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$HEALTH" == "green" ] || [ "$HEALTH" == "yellow" ]; then
    log_info "Cluster health: $HEALTH ✓"
else
    log_error "Cluster health: $HEALTH ✗"
fi

# Display status
echo ""
log_info "ELK Stack started successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Service URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Elasticsearch: http://localhost:9200"
echo "  Kibana:        http://localhost:5601"
echo "  Logstash:      localhost:5000 (TCP)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create index patterns (if not exists)
log_info "Setting up Kibana index patterns..."

# Wait a bit for Kibana to fully initialize
sleep 5

# Create index pattern via Kibana API
curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/ai-trading-*" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "ai-trading-*",
      "timeFieldName": "@timestamp"
    }
  }' > /dev/null 2>&1 || log_warning "Index pattern may already exist"

log_info "Index patterns configured!"

# Import dashboards
log_info "Importing Kibana dashboards..."

if [ -f "elk/kibana/dashboards/ai-trading-dashboard.ndjson" ]; then
    curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
      -H 'kbn-xsrf: true' \
      --form file=@elk/kibana/dashboards/ai-trading-dashboard.ndjson > /dev/null 2>&1 \
      && log_info "Dashboards imported successfully!" \
      || log_warning "Failed to import dashboards"
else
    log_warning "Dashboard file not found: elk/kibana/dashboards/ai-trading-dashboard.ndjson"
fi

# Test log sending
log_info "Testing log sending..."

python3 -c "
import socket
import json
import time

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5000))

    log_entry = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'level': 'INFO',
        'service': 'elk-setup',
        'message': 'ELK Stack test log',
        'test': True
    }

    sock.sendall((json.dumps(log_entry) + '\n').encode('utf-8'))
    sock.close()

    print('✓ Test log sent successfully')
except Exception as e:
    print(f'✗ Failed to send test log: {e}')
" 2>/dev/null || log_warning "Python test failed (Python 3 may not be installed)"

echo ""
log_info "Next steps:"
echo "  1. Open Kibana: http://localhost:5601"
echo "  2. Go to 'Discover' to view logs"
echo "  3. Go to 'Dashboard' to view visualizations"
echo "  4. Integrate ELKLogger in your application"
echo ""
log_info "To stop ELK Stack:"
echo "  docker-compose -f docker-compose.elk.yml down"
echo ""
