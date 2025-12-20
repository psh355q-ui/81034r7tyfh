
# Troubleshooting Guide - AI Trading System

**작성일**: 2025-12-10
**문서 버전**: 1.1
**옵션**: Option 5 - 문서화 보완

---

## 📋 목차

1. [서버 시작 문제](#서버-시작-문제)
2. [데이터베이스 연결 오류](#데이터베이스-연결-오류)
3. [Redis 캐시 오류](#redis-캐시-오류)
4. [API 응답 오류](#api-응답-오류)
5. [AI 모델 오류](#ai-모델-오류)
6. [KIS Broker 연결 오류](#kis-broker-연결-오류)
7. [프론트엔드 오류](#프론트엔드-오류)
8. [성능 문제](#성능-문제)
9. [배포 문제](#배포-문제)

---

## 서버 시작 문제

### 오류 1: `ModuleNotFoundError: No module named 'backend'`

**증상**:
```bash
$ python backend/main.py
ModuleNotFoundError: No module named 'backend'
```

**원인**: Python 경로 설정 문제

**해결 방법**:
```bash
# 방법 1: PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python backend/main.py

# 방법 2: 프로젝트 루트에서 실행
cd /path/to/ai-trading-system
python -m backend.main

# 방법 3: Docker 사용 (권장)
docker-compose up -d
```

### 오류 2: `Address already in use` (포트 충돌 및 좀비 프로세스)

**증상**:
```bash
ERROR: bind: address already in use
```
또는 서버는 켜졌는데 코드가 반영되지 않음 (Ghost Process).

**원인**: 포트(8000, 8001)가 죽지 않는 좀비 프로세스(Windows Service 등)에 의해 점유됨.

**해결 방법**:

1. **포트 변경 (권장)**:
   - `start_server.bat` 또는 `uvicorn` 실행 시 포트를 **8002**로 변경.
   ```bash
   uvicorn backend.api.main:app --port 8002 --reload
   ```

2. **프로세스 강제 종료**:
   ```powershell
   # 1. 포트 점유 PID 찾기
   netstat -ano | findstr :8001
   
   # 2. 강제 종료
   taskkill /PID <PID> /F
   ```
   *주의: 일부 시스템 프로세스나 권한 문제로 종료되지 않을 수 있음. 이 경우 포트 변경이 답입니다.*

### 오류 3: 환경 변수 누락

**증상**:
```bash
KeyError: 'OPENAI_API_KEY'
```

**원인**: `.env` 파일 누락 또는 로드 실패

**해결 방법**:
```bash
# 1. .env 파일 생성
cp .env.example .env

# 2. API 키 설정
vim .env
# OPENAI_API_KEY=sk-xxxxxxxx
# KIS_APP_KEY=PSxxxxxxxx
# DATABASE_URL=postgresql://...

# 3. 환경 변수 로드 확인
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

---

## 데이터베이스 연결 오류

### 오류 4: `could not connect to server: Connection refused`

**증상**:
```bash
psycopg2.OperationalError: could not connect to server: Connection refused
```

**원인**: PostgreSQL이 실행되지 않음

**해결 방법**:
```bash
# 방법 1: PostgreSQL 시작
# Ubuntu/Debian
sudo service postgresql start

# macOS
brew services start postgresql

# Docker
docker-compose up -d postgres

# 방법 2: 연결 확인
psql -h localhost -U postgres -d ai_trading

# 방법 3: 로그 확인
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 오류 5: `FATAL: password authentication failed`

**증상**:
```bash
FATAL: password authentication failed for user "postgres"
```

**원인**: 데이터베이스 비밀번호 불일치

**해결 방법**:
```bash
# 1. .env 파일 확인
cat .env | grep DATABASE_URL
# DATABASE_URL=postgresql://postgres:correct_password@localhost/ai_trading

# 2. PostgreSQL 비밀번호 재설정
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';

# 3. 연결 테스트
psql postgresql://postgres:new_password@localhost/ai_trading
```

### 오류 6: `database "ai_trading" does not exist`

**증상**:
```bash
psycopg2.OperationalError: FATAL: database "ai_trading" does not exist
```

**원인**: 데이터베이스 미생성

**해결 방법**:
```bash
# 데이터베이스 생성
sudo -u postgres psql
CREATE DATABASE ai_trading;
\q

# 또는 스크립트 실행
bash scripts/setup_database.sh

# 마이그레이션 실행
alembic upgrade head
```

---

## Redis 캐시 오류

### 오류 7: `ConnectionError: Error 111 connecting to localhost:6379`

**증상**:
```bash
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**원인**: Redis 서버가 실행되지 않음

**해결 방법**:
```bash
# 방법 1: Redis 시작
# Ubuntu/Debian
sudo service redis-server start

# macOS
brew services start redis

# Docker
docker-compose up -d redis

# 방법 2: 연결 확인
redis-cli ping
# 예상 응답: PONG

# 방법 3: 로그 확인
sudo tail -f /var/log/redis/redis-server.log
```

### 오류 8: `OOM command not allowed when used memory > 'maxmemory'`

**증상**:
```bash
redis.exceptions.ResponseError: OOM command not allowed
```

**원인**: Redis 메모리 한계 도달

**해결 방법**:
```bash
# 1. 캐시 초기화
redis-cli FLUSHALL

# 2. maxmemory 증가
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru

# 3. Redis 재시작
sudo service redis-server restart

# 4. 메모리 사용량 확인
redis-cli INFO memory
```

---

## API 응답 오류

### 오류 9: `404 Not Found` (API 엔드포인트)

**증상**:
```bash
GET /api/v1/stock/AAPL → 404 Not Found
```

**원인**: API 경로 불일치

**해결 방법**:
```bash
# 1. 정확한 엔드포인트 확인
curl http://localhost:8000/docs

# 2. API 라우터 등록 확인
# backend/main.py
app.include_router(stock_router, prefix="/api/v1")

# 3. URL 수정
curl http://localhost:8000/api/v1/stock/AAPL
```

### 오류 10: `500 Internal Server Error`

**증상**:
```bash
{
  "detail": "Internal Server Error"
}
```

**원인**: 서버 내부 오류

**해결 방법**:
```bash
# 1. 서버 로그 확인
docker-compose logs backend

# 2. 상세 오류 확인
# backend/main.py
app = FastAPI(debug=True)  # 개발 환경에서만

# 3. 예외 처리 추가
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
```

### 오류 11: `429 Too Many Requests` (Rate Limiting)

**증상**:
```bash
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**원인**: 속도 제한 초과

**해결 방법**:
```python
# 1. Rate Limit 확인
# backend/middleware/rate_limiter.py
@limiter.limit("10/minute")

# 2. 제한 완화 (개발 환경)
@limiter.limit("1000/minute")

# 3. IP 화이트리스트 추가
RATE_LIMIT_WHITELIST = ["127.0.0.1", "192.168.1.100"]
```

---

## AI 모델 오류

### 오류 12: `401 Unauthorized` / `invalid x-api-key`

**증상**:
```json
"detail": "Analysis failed: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}"
```

**원인**:
1. `.env` 파일에 API 키가 없거나 잘못됨 (예: `CLAUDE_API_KEY` 오타).
2. `settings.py` 로드 시점이 환경변수 로드보다 빨라 키가 반영되지 않음.

**해결 방법**:
1. **API 키 확인**: `.env` 파일에서 `CLAUDE_API_KEY=sk-ant-api...` 형식 확인 (`ssk-` 등 오타 주의).
2. **서버 재시작**: 환경 변수 변경 후 반드시 서버(`start_all.bat`)를 재시작해야 함.
3. **코드 확인**: `settings.py` 상단에 `load_dotenv()`가 명시적으로 호출되는지 확인.

### 오류 13: `No feature data available` / `Missing critical features`

**증상**:
API 분석 요청 시 "Missing critical features: ['vol_20d']" 등의 메시지와 함께 `conviction: 0.0` 반환.

**원인**:
1. **데이터 부족**: 요청일 기준으로 과거 데이터(Lookback Window)가 부족하여 지표 계산 실패 (예: 휴일 포함 시 30일치 데이터로는 20일 이동평균 계산 불가).
2. **DB 연결 실패**: Redis/TimescaleDB 연결 오류.

**해결 방법**:
1. **Lookback 기간 확대**: `features.py`에서 데이터 조회 기간을 30일 → **60일**로 수정.
2. **DB 예외 처리**: `store.py`가 DB 연결 실패 시에도 실시간 데이터(Yahoo Finance)로 계산하도록 폴백 로직 확인.
3. **JSON Import 확인**: `store.py`에 `import json`이 누락되면 데이터 저장이 실패하므로 import 추가 확인.

### 오류 14: `Timeout: Request timed out`

**증상**:
```bash
httpx.TimeoutException: Request timeout after 30 seconds
```

**원인**: AI 응답 지연

**해결 방법**:
```python
# 1. Timeout 증가
import httpx

client = httpx.AsyncClient(timeout=60.0)

# 2. 프롬프트 최적화 (토큰 감소)
prompt = prompt[:1000]  # 길이 제한

# 3. 스트리밍 사용
async for chunk in openai.ChatCompletion.acreate(stream=True, ...):
    yield chunk
```

---

## KIS Broker 연결 오류

### 오류 15: `Unauthorized: Invalid API Key`

**증상**:
```bash
{
  "msg_cd": "APBK0002",
  "msg1": "인증실패"
}
```

**원인**: KIS API 키 오류

**해결 방법**:
```bash
# 1. API 키 확인
cat .env | grep KIS_APP_KEY

# 2. 키 재발급
# https://apiportal.koreainvestment.com
# [API 관리] → [앱 키 재발급]

# 3. 모의투자 vs 실투자 확인
KIS_BASE_URL=https://openapi.koreainvestment.com:9443  # 실투자
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443  # 모의투자
```

### 오류 16: `주문가능수량부족`

**증상**:
```json
{
  "msg_cd": "APBK0123",
  "msg1": "주문가능수량부족"
}
```

**원인**: 계좌 잔고 부족

**해결 방법**:
```python
# 1. 잔고 조회
balance = await kis_broker.get_balance()
print(f"Available Cash: {balance['cash']}")

# 2. 주문 수량 조정
max_quantity = balance['cash'] / current_price
quantity = min(desired_quantity, max_quantity)

# 3. 모의투자 계좌 충전
# KIS 홈페이지 → 모의투자 → 계좌충전
```

---

## 프론트엔드 오류

### 오류 17: `CORS policy: No 'Access-Control-Allow-Origin' header`

**증상**:
```
Access to fetch at 'http://localhost:8000/api/v1/stock/AAPL' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**원인**: CORS 설정 누락

**해결 방법**:
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 오류 18: `React: Cannot find module './component'`

**증상**:
```bash
Module not found: Error: Can't resolve './component'
```

**원인**: 파일 경로 오류

**해결 방법**:
```bash
# 1. 파일 존재 확인
ls -la frontend/src/components/Component.tsx

# 2. 대소문자 확인 (Linux는 대소문자 구분)
# 잘못: import Component from './component'
# 올바름: import Component from './Component'

# 3. 경로 확인
# 잘못: import Component from '../Component'
# 올바름: import Component from './Component'
```

---

## 성능 문제

### 문제 19: API 응답 속도 느림 (> 1초)

**증상**:
```bash
curl -w "@curl-format.txt" http://localhost:8000/api/v1/stock/AAPL
time_total: 1.234s
```

**진단**:
```python
# 1. Profiling
import cProfile
cProfile.run('your_function()')

# 2. 로그 시간 측정
import time
start = time.time()
result = await slow_function()
logger.info(f"Function took {time.time() - start:.2f}s")
```

**해결 방법**:
```python
# 1. 캐싱 추가
@cache(expire=60)
async def get_stock_data(ticker):
    ...

# 2. 비동기 병렬 처리
results = await asyncio.gather(
    fetch_price(ticker),
    fetch_news(ticker),
    fetch_fundamentals(ticker)
)

# 3. 데이터베이스 쿼리 최적화
# 인덱스 추가, N+1 문제 해결
```

### 문제 20: 메모리 사용량 증가

**증상**:
```bash
$ docker stats
CONTAINER     MEM USAGE
backend       3.5GB / 4GB  (87%)
```

**진단**:
```python
# 1. Memory Profiler
from memory_profiler import profile

@profile
def memory_leak_function():
    ...

# 2. 메모리 사용량 확인
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**해결 방법**:
```python
# 1. 캐시 크기 제한
from cachetools import LRUCache

cache = LRUCache(maxsize=1000)

# 2. 리소스 정리
async def cleanup():
    await db.close()
    await redis.close()

# 3. 메모리 제한 설정
# docker-compose.yml
mem_limit: 2g
```

---

## 배포 문제

### 문제 21: Docker 이미지 빌드 실패

**증상**:
```bash
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**원인**: 의존성 설치 실패

**해결 방법**:
```bash
# 1. requirements.txt 확인
cat requirements.txt

# 2. 로컬에서 테스트
pip install -r requirements.txt

# 3. Docker 캐시 삭제 후 재빌드
docker-compose build --no-cache

# 4. Python 버전 확인
# Dockerfile
FROM python:3.11-slim
```

### 문제 22: Docker 컨테이너 바로 종료됨

**증상**:
```bash
$ docker-compose ps
backend    Exit 1
```

**진단**:
```bash
# 로그 확인
docker-compose logs backend
```

**해결 방법**:
```bash
# 1. 환경 변수 확인
docker-compose config

# 2. 명령어 확인
# docker-compose.yml
command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 3. 헬스체크 추가
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 긴급 상황 대응

### 상황 1: 프로덕션 서버 다운

```bash
# 1. 즉시 백업 서버 활성화
# 2. 로그 수집
docker-compose logs > emergency.log

# 3. 데이터베이스 백업
pg_dump ai_trading > backup_$(date +%Y%m%d_%H%M%S).sql

# 4. 서비스 재시작
docker-compose restart
```

### 상황 2: 데이터 손실

```bash
# 1. 최근 백업 복원
psql ai_trading < backup_20241210.sql

# 2. 트랜잭션 로그 확인
SELECT * FROM pg_stat_activity;

# 3. 데이터 무결성 검증
SELECT COUNT(*) FROM stocks;
```

---

## 도움 요청

문제가 해결되지 않으면:

1. **GitHub Issues**: https://github.com/your-repo/ai-trading-system/issues
2. **Discord**: https://discord.gg/your-server
3. **이메일**: support@example.com

**이슈 보고 시 포함할 정보**:
- 오류 메시지 (전체)
- 재현 단계
- 환경 정보 (OS, Python 버전, Docker 버전)
- 로그 파일

---

**문서 버전**: 1.1
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team
