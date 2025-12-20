# AI Trading System Troubleshooting Guide

**Date**: 2025-12-14
**Author**: Development Team
**Version**: 1.0

## Table of Contents

1. [System Startup Issues](#1-system-startup-issues)
2. [API Connectivity Problems](#2-api-connectivity-problems)
3. [Database Connection Issues](#3-database-connection-issues)
4. [ELK Stack Troubleshooting](#4-elk-stack-troubleshooting)
5. [KIS Integration Problems](#5-kis-integration-problems)
6. [Frontend Issues](#6-frontend-issues)
7. [Performance Problems](#7-performance-problems)
8. [Docker Issues](#8-docker-issues)
9. [Common Error Messages](#9-common-error-messages)
10. [Debugging Tools](#10-debugging-tools)

---

## 1. System Startup Issues

### Backend Won't Start

**Symptom**: Backend fails to start with module import errors

**Error Messages**:
```
ModuleNotFoundError: No module named 'backend'
ImportError: attempted relative import with no known parent package
```

**Solutions**:

1. **Use the startup script**:
```powershell
# Windows
.\start-backend.ps1

# Linux/Mac
./start-backend.sh
```

2. **Manual PYTHONPATH setup**:
```powershell
# Windows PowerShell
$env:PYTHONPATH = "d:\code\ai-trading-system"
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Linux/Mac
export PYTHONPATH=/path/to/ai-trading-system
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

3. **Check Python version**:
```bash
python --version
# Should be Python 3.11+
```

### Port Already in Use

**Symptom**: "Address already in use" error on startup

**Error Message**:
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8001)
OSError: [WinError 10048] 각 소켓 주소(프로토콜/네트워크 주소/포트)는 하나만 사용할 수 있습니다
```

**Solutions**:

1. **Find and kill the process** (Windows):
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

2. **Find and kill the process** (Linux/Mac):
```bash
# Find process
lsof -i :8001

# Kill process
kill -9 <PID>
```

3. **Change the port**:
```bash
# Use a different port
uvicorn main:app --port 8002
```

### Frontend Won't Start

**Symptom**: Next.js development server fails to start

**Solutions**:

1. **Clean install dependencies**:
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
```

2. **Clear Next.js cache**:
```bash
rm -rf .next
npm run dev
```

3. **Check Node version**:
```bash
node --version
# Should be 18.x or higher
```

---

## 2. API Connectivity Problems

### CORS Errors

**Symptom**: Browser console shows CORS errors

**Error Message**:
```
Access to fetch at 'http://localhost:8001/api/...' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solutions**:

1. **Check CORS configuration in backend/main.py**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3002",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Add your frontend URL to .env**:
```env
FRONTEND_URL=http://localhost:3002
```

3. **Restart backend after changes**

### API Returns 401 Unauthorized

**Symptom**: All API requests return 401 status

**Solutions**:

1. **Check KIS authentication**:
```bash
# Test KIS connection
curl http://localhost:8001/api/kis/status
```

2. **Verify .env credentials**:
```env
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NUMBER=your_account_number
KIS_ACCOUNT_CODE=01  # or 02 for virtual account
```

3. **Check token expiration**:
```python
# KIS tokens expire after 24 hours
# Restart backend to get new token
```

### API Returns 500 Internal Server Error

**Symptom**: Random 500 errors on API calls

**Solutions**:

1. **Check backend logs**:
```bash
# View recent logs
docker-compose logs backend --tail=100

# Follow logs in real-time
docker-compose logs -f backend
```

2. **Check for uncaught exceptions**:
```python
# Look for tracebacks in logs
# Common causes:
# - Missing environment variables
# - Database connection failures
# - External API timeouts
```

3. **Enable debug mode** (development only):
```python
# In main.py
app = FastAPI(debug=True)
```

---

## 3. Database Connection Issues

### PostgreSQL Connection Refused

**Symptom**: Cannot connect to PostgreSQL database

**Error Messages**:
```
psycopg2.OperationalError: could not connect to server: Connection refused
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server failed
```

**Solutions**:

1. **Check Docker container status**:
```bash
docker-compose ps postgres
# Should show "Up"
```

2. **Verify database credentials in .env**:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=your_secure_password
```

3. **Test database connection directly**:
```bash
# Using psql
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db

# Using Python
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='trading_db', user='trading_user', password='your_password'); print('Connected!')"
```

4. **Check PostgreSQL logs**:
```bash
docker-compose logs postgres --tail=50
```

### Database Migration Errors

**Symptom**: Alembic migration fails

**Error Messages**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxxx'
sqlalchemy.exc.ProgrammingError: relation "xxx" does not exist
```

**Solutions**:

1. **Check migration status**:
```bash
cd backend
alembic current
alembic history
```

2. **Reset database** (development only):
```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm ai-trading-system_postgres_data

# Restart and recreate
docker-compose up -d postgres
cd backend
alembic upgrade head
```

3. **Manually create tables**:
```python
# In backend directory
python
>>> from database import engine, Base
>>> Base.metadata.create_all(bind=engine)
```

### TimescaleDB Extension Not Available

**Symptom**: TimescaleDB functions not working

**Solutions**:

1. **Verify TimescaleDB is installed**:
```sql
-- Connect to database
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db

-- Check extension
SELECT * FROM pg_extension WHERE extname = 'timescaledb';

-- Enable if not present
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

2. **Use correct Docker image**:
```yaml
# In docker-compose.yml
postgres:
  image: timescale/timescaledb:latest-pg15
```

---

## 4. ELK Stack Troubleshooting

### Elasticsearch Won't Start

**Symptom**: Elasticsearch container exits immediately

**Solutions**:

1. **Check memory limits**:
```yaml
# In docker-compose.yml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"  # Reduce if low memory
```

2. **Check logs**:
```bash
docker-compose logs elasticsearch
```

3. **Increase vm.max_map_count** (Linux):
```bash
sudo sysctl -w vm.max_map_count=262144
# Make permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### Kibana Shows "Elasticsearch cluster did not respond"

**Symptom**: Kibana cannot connect to Elasticsearch

**Solutions**:

1. **Wait for Elasticsearch to be ready**:
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Should return: "status":"green" or "yellow"
```

2. **Verify Kibana configuration**:
```yaml
# In docker-compose.yml
kibana:
  environment:
    ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
  depends_on:
    - elasticsearch
```

3. **Check network connectivity**:
```bash
# From Kibana container
docker exec ai-trading-kibana curl http://elasticsearch:9200
```

### No Logs Appearing in Kibana

**Symptom**: Kibana shows no data or indices

**Solutions**:

1. **Check Logstash is receiving logs**:
```bash
docker-compose logs logstash | grep "Successfully started"
```

2. **Verify Filebeat is running**:
```bash
docker-compose ps filebeat
docker-compose logs filebeat
```

3. **Check index patterns**:
```bash
# List all indices
curl http://localhost:9200/_cat/indices?v

# Should show indices like:
# ai-trading-2025.12.14
# ai-trading-errors-2025.12.14
```

4. **Create index pattern in Kibana**:
   - Go to Kibana (http://localhost:5601)
   - Management → Stack Management → Index Patterns
   - Create pattern: `ai-trading-*`
   - Select timestamp field: `@timestamp`

5. **Test log generation**:
```bash
# Generate test log
curl http://localhost:8001/api/health

# Check logs immediately
docker-compose logs backend | tail -20
```

### Logstash Pipeline Errors

**Symptom**: Logstash shows pipeline errors

**Solutions**:

1. **Validate Logstash configuration**:
```bash
# Test configuration syntax
docker exec ai-trading-logstash /usr/share/logstash/bin/logstash --config.test_and_exit -f /usr/share/logstash/pipeline/logstash.conf
```

2. **Check pipeline logs**:
```bash
docker-compose logs logstash | grep -i error
```

3. **Verify JSON format**:
```bash
# Logs should be valid JSON
docker-compose logs backend | grep "timestamp"
```

---

## 5. KIS Integration Problems

### Authentication Fails

**Symptom**: KIS API returns authentication errors

**Error Messages**:
```
{"msg_cd":"EGW00201","msg1":"인증 실패"}
HTTP 401: Unauthorized
```

**Solutions**:

1. **Verify credentials in .env**:
```env
KIS_APP_KEY=PSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KIS_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KIS_ACCOUNT_NUMBER=12345678-01
KIS_ACCOUNT_CODE=01
```

2. **Check credential format**:
   - APP_KEY: Starts with "PS" (real) or "PS" (virtual)
   - APP_SECRET: 36 characters
   - ACCOUNT_NUMBER: Format XXXXXXXX-XX
   - ACCOUNT_CODE: 01 (real) or 02 (virtual)

3. **Regenerate API keys**:
   - Login to KIS Developers (https://apiportal.koreainvestment.com)
   - Go to My Applications
   - Regenerate APP_KEY and APP_SECRET
   - Update .env and restart

4. **Check API endpoint**:
```env
# Real trading
KIS_BASE_URL=https://openapi.koreainvestment.com:9443

# Virtual trading (paper trading)
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443
```

### Order Placement Fails

**Symptom**: Orders return errors or aren't placed

**Solutions**:

1. **Check market hours**:
```python
# Korean market hours (KST)
# Regular: 09:00 - 15:30
# After-hours: 15:40 - 16:00 (limited)
```

2. **Verify order parameters**:
```python
# Example correct order
{
    "ticker": "005930",      # 6-digit code
    "quantity": 10,          # Integer > 0
    "price": 70000,          # Positive number
    "order_type": "limit",   # or "market"
}
```

3. **Check account balance**:
```bash
curl http://localhost:8001/api/kis/balance
```

4. **Review order response**:
```bash
# Enable detailed logging
export APP_LOG_LEVEL=DEBUG
```

### Rate Limit Exceeded

**Symptom**: KIS API returns rate limit errors

**Error Messages**:
```
{"msg_cd":"EGW00119","msg1":"API 호출 한도 초과"}
```

**Solutions**:

1. **Check rate limits**:
   - Real account: 1초당 20건, 1분당 200건
   - Virtual account: 1초당 5건, 1분당 50건

2. **Implement request throttling**:
```python
# In KIS client
import asyncio
from asyncio import Semaphore

# Limit concurrent requests
semaphore = Semaphore(5)

async def rate_limited_request():
    async with semaphore:
        await asyncio.sleep(0.2)  # 200ms between requests
        # Make request
```

3. **Use caching for frequently accessed data**:
```python
# Cache market data for 1 minute
# Cache balance data for 5 minutes
```

### WebSocket Connection Drops

**Symptom**: Real-time price updates stop

**Solutions**:

1. **Check WebSocket connection**:
```bash
# View WebSocket logs
docker-compose logs backend | grep -i websocket
```

2. **Implement reconnection logic**:
```python
# Auto-reconnect on disconnect
max_retries = 3
retry_delay = 5  # seconds
```

3. **Verify subscription format**:
```python
# Correct subscription message
{
    "header": {
        "approval_key": "your_approval_key",
        "custtype": "P",
        "tr_type": "1",
        "content-type": "utf-8"
    },
    "body": {
        "input": {
            "tr_id": "H0STCNT0",
            "tr_key": "005930"
        }
    }
}
```

---

## 6. Frontend Issues

### Page Won't Load / White Screen

**Symptom**: Frontend shows blank page or loading forever

**Solutions**:

1. **Check browser console for errors**:
   - Press F12 → Console tab
   - Look for JavaScript errors

2. **Verify API connection**:
```javascript
// Check if backend is reachable
fetch('http://localhost:8001/api/health')
  .then(r => r.json())
  .then(console.log)
```

3. **Clear browser cache**:
   - Hard reload: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Clear cache: Ctrl+Shift+Delete

4. **Check Next.js errors**:
```bash
# View Next.js logs
docker-compose logs frontend --tail=50
```

### Real-time Updates Not Working

**Symptom**: Stock prices don't update in real-time

**Solutions**:

1. **Verify WebSocket connection**:
```javascript
// In browser console
console.log(window.websocket)
// Should show WebSocket object in OPEN state
```

2. **Check SSE (Server-Sent Events) connection**:
```bash
# Test SSE endpoint
curl http://localhost:8001/api/stream/prices
```

3. **Enable debug logging**:
```javascript
// In frontend code
console.log('WebSocket state:', ws.readyState);
// 0: CONNECTING, 1: OPEN, 2: CLOSING, 3: CLOSED
```

### Chart Not Displaying

**Symptom**: TradingView charts or custom charts don't render

**Solutions**:

1. **Check data format**:
```javascript
// Data should be array of objects with:
// { time: timestamp, open, high, low, close, volume }
```

2. **Verify chart library loaded**:
```javascript
// In browser console
console.log(window.TradingView)
// or
console.log(window.Plotly)
```

3. **Check container dimensions**:
```css
/* Chart container must have explicit dimensions */
.chart-container {
  width: 100%;
  height: 400px;
}
```

---

## 7. Performance Problems

### Slow API Response Times

**Symptom**: API requests take > 2 seconds

**Diagnostic**:

1. **Check API response times in logs**:
```bash
# View recent API calls with timing
docker-compose logs backend | grep "duration"
```

2. **Identify slow endpoints**:
```bash
# Sort by response time
grep "api_request" backend.log | jq -r '[.endpoint, .duration] | @tsv' | sort -k2 -n -r | head -20
```

**Solutions**:

1. **Enable Redis caching**:
```env
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

2. **Optimize database queries**:
```python
# Use eager loading to prevent N+1 queries
query = session.query(Order).options(joinedload(Order.user))

# Add indexes for frequently queried fields
Index('idx_order_created_at', Order.created_at)
```

3. **Reduce external API calls**:
```python
# Batch requests where possible
# Cache frequently accessed data
# Use async/await for concurrent requests
```

### High Memory Usage

**Symptom**: System uses > 8GB RAM

**Diagnostic**:

```bash
# Check container memory usage
docker stats

# Check Python memory usage
docker exec ai-trading-backend python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

**Solutions**:

1. **Limit container memory**:
```yaml
# In docker-compose.yml
backend:
  deploy:
    resources:
      limits:
        memory: 2G
```

2. **Optimize data structures**:
```python
# Use generators instead of lists
# Clear large objects after use
# Avoid global state accumulation
```

3. **Reduce log retention**:
```yaml
# In docker-compose.yml
logging:
  options:
    max-size: "10m"
    max-file: "3"
```

### Database Slow Queries

**Symptom**: Database queries taking > 1 second

**Diagnostic**:

1. **Enable query logging**:
```sql
-- In PostgreSQL
ALTER DATABASE trading_db SET log_statement = 'all';
ALTER DATABASE trading_db SET log_min_duration_statement = 1000;  -- Log queries > 1s
```

2. **Check slow query log**:
```bash
docker exec ai-trading-postgres tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

**Solutions**:

1. **Add indexes**:
```sql
-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

-- Add index based on analysis
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

2. **Optimize queries**:
```sql
-- Avoid SELECT *
SELECT id, ticker, quantity FROM orders;

-- Use LIMIT for large result sets
SELECT * FROM trades ORDER BY created_at DESC LIMIT 100;
```

3. **Use connection pooling**:
```python
# In database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
)
```

---

## 8. Docker Issues

### Container Keeps Restarting

**Symptom**: Container shows "Restarting" status

**Diagnostic**:

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs <service_name> --tail=100

# Check exit code
docker inspect <container_id> | grep "ExitCode"
```

**Solutions**:

1. **Fix application errors**:
```bash
# Common causes:
# - Missing environment variables
# - Database connection failures
# - Port conflicts
```

2. **Check health checks**:
```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

3. **Review resource limits**:
```yaml
# Ensure adequate resources
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

### Cannot Remove Container/Volume

**Symptom**: "Volume is in use" or "Container is running" errors

**Solutions**:

1. **Force remove container**:
```bash
# Stop all containers
docker-compose down

# Force remove specific container
docker rm -f <container_name>

# Remove all stopped containers
docker container prune
```

2. **Remove volume**:
```bash
# Stop containers using the volume
docker-compose down

# Remove volume
docker volume rm ai-trading-system_postgres_data

# Remove all unused volumes
docker volume prune
```

### Out of Disk Space

**Symptom**: Docker build fails with "no space left on device"

**Solutions**:

1. **Clean up Docker resources**:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused (be careful!)
docker system prune -a --volumes
```

2. **Check disk usage**:
```bash
# Docker disk usage
docker system df

# System disk usage
df -h
```

3. **Move Docker data directory** (if needed):
```json
// In Docker Desktop settings or /etc/docker/daemon.json
{
  "data-root": "/path/to/larger/disk"
}
```

---

## 9. Common Error Messages

### "Connection refused"

**Possible Causes**:
- Service not running
- Wrong port
- Firewall blocking connection

**Quick Fix**:
```bash
# Check if service is running
docker-compose ps

# Check if port is open
netstat -an | grep 8001

# Restart service
docker-compose restart backend
```

### "Permission denied"

**Possible Causes**:
- File ownership issues
- Docker socket permissions
- Volume mount permissions

**Quick Fix** (Linux):
```bash
# Fix file ownership
sudo chown -R $USER:$USER .

# Add user to docker group
sudo usermod -aG docker $USER

# Fix volume permissions
docker-compose down
sudo rm -rf volumes/*
docker-compose up -d
```

### "No module named 'xxx'"

**Possible Causes**:
- Missing package
- Wrong Python environment
- PYTHONPATH not set

**Quick Fix**:
```bash
# Install missing package
pip install <package_name>

# Reinstall all requirements
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### "Database does not exist"

**Possible Causes**:
- Database not initialized
- Wrong database name
- Database container not running

**Quick Fix**:
```bash
# Check database exists
docker exec -it ai-trading-postgres psql -U postgres -l

# Create database
docker exec -it ai-trading-postgres psql -U postgres -c "CREATE DATABASE trading_db;"

# Run migrations
cd backend
alembic upgrade head
```

### "SSL: CERTIFICATE_VERIFY_FAILED"

**Possible Causes**:
- SSL certificate issues
- Corporate proxy/firewall
- Outdated CA certificates

**Quick Fix** (development only):
```python
# Disable SSL verification (NOT FOR PRODUCTION)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Or update certificates
pip install --upgrade certifi
```

---

## 10. Debugging Tools

### Backend Debugging

**Enable Debug Mode**:
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# In .env
APP_LOG_LEVEL=DEBUG
```

**Interactive Debugging**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

**Request Logging**:
```python
# Log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### Database Debugging

**Query Logging**:
```python
# In database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries
)
```

**Manual Query Testing**:
```bash
# Connect to database
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db

# Run queries
SELECT * FROM users LIMIT 5;
SELECT COUNT(*) FROM orders;
\dt  # List tables
\d orders  # Describe table
```

### Frontend Debugging

**Browser DevTools**:
```javascript
// Add console logs
console.log('Component mounted', props);
console.table(data);  // Display array/object as table
console.time('fetch');  // Start timer
// ... code ...
console.timeEnd('fetch');  // End timer
```

**React DevTools**:
- Install React DevTools extension
- Inspect component props/state
- Profile performance

**Network Debugging**:
- F12 → Network tab
- Check request/response
- Verify headers and payload

### Log Analysis

**Search Logs**:
```bash
# Search for errors
docker-compose logs | grep -i error

# Search for specific ticker
docker-compose logs backend | grep "005930"

# Search with context (5 lines before/after)
docker-compose logs backend | grep -C 5 "exception"
```

**Follow Logs in Real-time**:
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend

# Follow multiple services
docker-compose logs -f backend postgres
```

**Export Logs**:
```bash
# Export to file
docker-compose logs > system-logs-$(date +%Y%m%d).log

# Export specific time range
docker-compose logs --since="2025-12-14T09:00:00" --until="2025-12-14T10:00:00" > logs.txt
```

### Health Checks

**System Health**:
```bash
# Backend health
curl http://localhost:8001/api/health

# Database health
docker exec ai-trading-postgres pg_isready

# Redis health
docker exec ai-trading-redis redis-cli ping

# Elasticsearch health
curl http://localhost:9200/_cluster/health
```

**Create Health Check Script**:
```bash
#!/bin/bash
# health-check.sh

echo "=== Backend Health ==="
curl -s http://localhost:8001/api/health | jq

echo "=== Database Health ==="
docker exec ai-trading-postgres pg_isready

echo "=== Redis Health ==="
docker exec ai-trading-redis redis-cli ping

echo "=== Container Status ==="
docker-compose ps
```

---

## Quick Reference

### Most Common Issues

1. **Backend won't start** → Use `start-backend.ps1` script
2. **Port in use** → `netstat -ano | findstr :8001` then `taskkill /PID <PID> /F`
3. **CORS errors** → Check CORS origins in main.py
4. **Database connection** → Verify .env DB_* variables
5. **No logs in Kibana** → Check Elasticsearch indices with `curl http://localhost:9200/_cat/indices`
6. **KIS auth fails** → Regenerate API keys and update .env
7. **Container restarts** → Check logs with `docker-compose logs <service>`

### Useful Commands

```bash
# Check all service status
docker-compose ps

# View recent logs
docker-compose logs --tail=100

# Restart specific service
docker-compose restart backend

# Reset everything (CAUTION: deletes data)
docker-compose down -v
docker-compose up -d

# Check resource usage
docker stats

# Clean up Docker
docker system prune -a
```

### Emergency Reset

```bash
# Complete system reset (CAUTION: all data will be lost)
docker-compose down -v
docker volume prune -f
docker network prune -f
docker-compose up -d
cd backend
alembic upgrade head
```

---

## Getting Help

If you cannot resolve an issue:

1. **Check logs thoroughly**: Most issues show clear error messages
2. **Search existing documentation**: This guide + other docs in `docs/` folder
3. **Review code changes**: Use `git diff` to see recent modifications
4. **Test in isolation**: Disable features one by one to identify the cause
5. **Create minimal reproduction**: Simplify to the smallest code that reproduces the issue

**Log Collection for Support**:
```bash
# Collect all relevant information
docker-compose ps > debug-info.txt
docker-compose logs >> debug-info.txt
cat .env >> debug-info.txt  # Remove sensitive data first!
python --version >> debug-info.txt
docker version >> debug-info.txt
```

---

**Last Updated**: 2025-12-14
**Version**: 1.0
