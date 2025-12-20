# AI Trading System - Quick Start Guide

빠른 시작 가이드 - 5분 안에 시스템을 실행하세요!

---

## 전제 조건 (Prerequisites)

시스템 실행에 필요한 소프트웨어:

### 필수
- **Python 3.10+** - [다운로드](https://www.python.org/downloads/)
- **Node.js 18+** - [다운로드](https://nodejs.org/)
- **PostgreSQL 14+** - [다운로드](https://www.postgresql.org/download/)
- **Redis 6+** - [다운로드](https://redis.io/download/)

### 선택 (권장)
- **Docker Desktop** - [다운로드](https://www.docker.com/products/docker-desktop)
- **Git** - [다운로드](https://git-scm.com/)

---

## 방법 1: Docker로 실행 (가장 쉬움)

### 1단계: Docker Compose 실행

```bash
cd d:\code\ai-trading-system
docker-compose up -d
```

이 명령은 다음을 실행합니다:
- PostgreSQL (포트 5432)
- Redis (포트 6379)
- TimescaleDB (PostgreSQL 확장)
- Prometheus (포트 9090)
- Grafana (포트 3001)

### 2단계: 데이터베이스 초기화

```bash
# 백엔드 디렉토리로 이동
cd backend

# 데이터베이스 마이그레이션
alembic upgrade head

# 또는 Python으로
python -c "from data.news_models import init_db; init_db()"
```

### 3단계: 환경 변수 설정

`.env` 파일 생성:

```bash
# Backend root에 .env 파일 생성
cd d:\code\ai-trading-system\backend
```

`.env` 파일 내용:

```env
# Database
DATABASE_URL=postgresql://trading_user:trading_pass@localhost:5432/ai_trading_db

# Redis
REDIS_URL=redis://localhost:6379/0

# AI APIs
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here

# Authentication
API_MASTER_KEY=your_generated_master_key
API_TRADING_KEY=your_generated_trading_key
API_READONLY_KEY=your_generated_readonly_key
API_WEBHOOK_KEY=your_generated_webhook_key

# API Key 생성 (Python에서 실행)
# python -c "from auth import setup_env_template; setup_env_template()"

# Telegram (선택)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Slack (선택)
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

### 4단계: 백엔드 실행

```bash
cd d:\code\ai-trading-system
python start_backend.py
```

백엔드가 http://localhost:5000 에서 실행됩니다.

### 5단계: 프론트엔드 실행

새 터미널에서:

```bash
cd d:\code\ai-trading-system\frontend
npm install
npm run dev
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

### 6단계: 브라우저에서 접속

http://localhost:3000 열기

완료! 시스템이 실행 중입니다.

---

## 방법 2: 수동 설치 (개발용)

Docker 없이 로컬에서 각 서비스를 직접 실행합니다.

### 1단계: PostgreSQL 설치 및 설정

```bash
# Windows (관리자 권한으로)
# PostgreSQL 설치 후 서비스 시작

# Database 생성
psql -U postgres
CREATE DATABASE ai_trading_db;
CREATE USER trading_user WITH PASSWORD 'trading_pass';
GRANT ALL PRIVILEGES ON DATABASE ai_trading_db TO trading_user;

# TimescaleDB 확장 설치
\c ai_trading_db
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### 2단계: Redis 설치 및 실행

```bash
# Windows
# Redis 설치 후 redis-server 실행

# 또는 WSL에서
sudo service redis-server start
```

### 3단계: Python 의존성 설치

```bash
cd d:\code\ai-trading-system\backend

# 가상환경 생성 (권장)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 4단계: Node.js 의존성 설치

```bash
cd d:\code\ai-trading-system\frontend
npm install
```

### 5단계: 환경 변수 설정

위의 Docker 방법과 동일하게 `.env` 파일 생성

### 6단계: 데이터베이스 마이그레이션

```bash
cd d:\code\ai-trading-system\backend
alembic upgrade head
```

### 7단계: 서비스 실행

**터미널 1 - 백엔드:**
```bash
cd d:\code\ai-trading-system
python start_backend.py
```

**터미널 2 - 프론트엔드:**
```bash
cd d:\code\ai-trading-system\frontend
npm run dev
```

---

## 초기 설정

### 1. API 키 생성

```bash
cd d:\code\ai-trading-system\backend
python -c "from auth import setup_env_template; setup_env_template()"
```

생성된 키를 `.env` 파일에 복사합니다.

### 2. RSS 피드 추가

시스템이 처음 실행되면 기본 RSS 피드가 자동으로 추가됩니다:
- Bloomberg
- Reuters
- CNBC
- Wall Street Journal
- MarketWatch
- Yahoo Finance
- 연합뉴스
- 한국경제
- 매일경제

추가 피드는 프론트엔드 `/rss-management` 페이지에서 추가할 수 있습니다.

### 3. 첫 번째 뉴스 크롤링

```bash
# API를 통해
curl -X POST http://localhost:5000/news/crawl
```

또는 프론트엔드의 News 페이지에서 "Crawl Now" 버튼 클릭

### 4. AI 분석 실행

```bash
# 처음 10개 기사 분석
curl -X POST "http://localhost:5000/news/analyze?batch_size=10"
```

---

## 주요 기능 확인

### 1. 대시보드 확인
http://localhost:3000/dashboard

- 포트폴리오 현황
- 최근 신호
- 성과 차트

### 2. 뉴스 확인
http://localhost:3000/news

- 크롤링된 뉴스 목록
- AI 분석 결과
- 감정 점수

### 3. 거래 신호 확인
http://localhost:3000/analysis

- 생성된 거래 신호
- 신뢰도 점수
- 승인/거부

### 4. Advanced Analytics (New!)
http://localhost:3000/advanced-analytics

- **Performance Attribution**: 전략/섹터/AI 소스별 성과 분석
- **Risk Analytics**: VaR, Drawdown, 집중도 리스크
- **Trade Analytics**: 거래 패턴, 실행 품질 분석

### 5. CEO Analysis
http://localhost:3000/ceo-analysis

- SEC 공시 CEO 발언 분석
- 유사 발언 검색
- 감정 추적

### 6. 백테스트
http://localhost:3000/backtest

- 과거 신호 백테스트
- 성과 지표
- 최적화

---

## 시스템 상태 확인

### Health Check

```bash
curl http://localhost:5000/health
```

정상 응답:
```json
{
  "status": "healthy",
  "components": [
    {
      "name": "Disk Space",
      "status": "healthy"
    },
    {
      "name": "Memory",
      "status": "healthy"
    }
  ]
}
```

### 백엔드 로그 확인

```bash
# 터미널에서 실시간 로그 확인
# 또는
curl http://localhost:5000/logs?limit=10
```

### 데이터베이스 연결 확인

```bash
psql -U trading_user -d ai_trading_db -c "SELECT COUNT(*) FROM news_articles;"
```

---

## 문제 해결

### 백엔드가 시작되지 않음

1. **포트 충돌 확인**
```bash
# Windows
netstat -ano | findstr :5000
# 프로세스 종료
taskkill /PID <PID> /F
```

2. **데이터베이스 연결 오류**
```bash
# PostgreSQL 서비스 상태 확인
# Windows: services.msc에서 PostgreSQL 확인
# Linux: sudo systemctl status postgresql
```

3. **Redis 연결 오류**
```bash
# Redis 서비스 확인
redis-cli ping
# 응답: PONG
```

### 프론트엔드가 시작되지 않음

1. **Node.js 버전 확인**
```bash
node --version
# v18.0.0 이상이어야 함
```

2. **의존성 재설치**
```bash
cd d:\code\ai-trading-system\frontend
rm -rf node_modules package-lock.json
npm install
```

3. **포트 변경**
`vite.config.ts`에서 포트 변경:
```typescript
server: {
  port: 3002,  // 다른 포트로 변경
  ...
}
```

### API 키 오류

```bash
# API 키 재생성
cd backend
python -c "from auth import setup_env_template; setup_env_template()"
```

### 데이터베이스 마이그레이션 오류

```bash
# 마이그레이션 리셋
cd backend
alembic downgrade base
alembic upgrade head
```

---

## 다음 단계

### 1. 백테스팅 실행

```python
# Python에서
from backtesting.signal_backtest_engine import SignalBacktestEngine

engine = SignalBacktestEngine()
results = await engine.run_backtest(
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_capital=100000
)
```

### 2. 실시간 거래 설정

1. 브로커 API 연결 (Alpaca, Interactive Brokers 등)
2. Paper Trading 모드 활성화
3. 신호 자동 승인 설정

### 3. 알림 설정

**Telegram 봇 생성:**
1. Telegram에서 @BotFather 찾기
2. `/newbot` 명령으로 봇 생성
3. 토큰 받기
4. 봇과 대화 시작
5. Chat ID 얻기: https://api.telegram.org/bot<TOKEN>/getUpdates

**Slack 웹훅:**
1. Slack 워크스페이스 설정
2. Incoming Webhooks 앱 추가
3. Webhook URL 복사
4. `.env`에 추가

### 4. 모니터링 대시보드

Grafana 접속: http://localhost:3001

기본 로그인:
- Username: `admin`
- Password: `admin`

사전 구성된 대시보드:
- System Health
- Trading Performance
- API Usage
- Cost Tracking

---

## 개발 모드

### 백엔드 Hot Reload

```bash
# Uvicorn은 자동으로 파일 변경 감지
python start_backend.py
```

### 프론트엔드 Hot Reload

```bash
# Vite는 자동으로 HMR 지원
npm run dev
```

### 디버깅

**VSCode 설정 (.vscode/launch.json):**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "backend.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "5000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

---

## 프로덕션 배포

### 환경 변수 검증

```bash
# 모든 필수 변수 확인
python -c "from backend.config import settings; print(settings)"
```

### 데이터베이스 백업

```bash
pg_dump -U trading_user ai_trading_db > backup.sql
```

### Docker 프로덕션 빌드

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx 리버스 프록시 설정

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

---

## 추가 리소스

- **전체 문서**: [README.md](README.md)
- **API 문서**: [251210_API_DOCUMENTATION.md](251210_API_DOCUMENTATION.md)
- **아키텍처**: [ARCHITECTURE.md](ARCHITECTURE.md) (준비 중)
- **기여 가이드**: [CONTRIBUTING.md](CONTRIBUTING.md) (준비 중)

---

## 지원

문제가 발생하면:
1. [GitHub Issues](https://github.com/your-repo/issues)에 보고
2. 로그 파일 확인: `backend/logs/`
3. 데이터베이스 상태 확인
4. Docker 컨테이너 로그: `docker-compose logs`

---

**축하합니다! 🎉**

AI Trading System이 성공적으로 실행되었습니다!

다음 단계로 대시보드를 탐색하고, 첫 번째 거래 신호를 생성해보세요.

**Happy Trading! 📈**
